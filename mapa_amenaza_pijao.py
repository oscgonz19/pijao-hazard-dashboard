#!/usr/bin/env python3
"""
MAPA DE AMENAZA POR MOVIMIENTOS EN MASA - CORREDOR VIAL PIJAO
=============================================================
Autor: Ozz - Geólogo/Data Scientist
Fecha: Noviembre 2025
Normas: INVÍAS, SGC (Servicio Geológico Colombiano)

Este script genera el mapa de amenaza continuo interpolando el índice
haz_num (1-5) a lo largo del corredor vial, cumpliendo con los requisitos
técnicos de las interventorías colombianas.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import Voronoi, voronoi_plot_2d, cKDTree
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import rasterio
from rasterio.transform import from_bounds
from rasterio.features import rasterize
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# FUNCIONES DE UTILIDAD PARA ROBUSTEZ
# ==============================================================================

def ensure_projected(corredor_gdf, puntos_gdf):
    """Asegura que ambos GDF estén en coordenadas proyectadas (UTM)"""
    def _utm_epsg(gdf):
        c = gdf.unary_union.centroid
        lon, lat = (c.x, c.y)
        zone = int((lon + 180) / 6) + 1
        return 32600 + zone if lat >= 0 else 32700 + zone

    # Si el corredor está en geográficas, pásalo a UTM
    if corredor_gdf.crs is None or corredor_gdf.crs.is_geographic:
        epsg = _utm_epsg(corredor_gdf if len(corredor_gdf) else puntos_gdf)
        corredor_gdf = corredor_gdf.to_crs(epsg=epsg)
    # Alinea puntos al CRS del corredor
    if puntos_gdf.crs != corredor_gdf.crs:
        puntos_gdf = puntos_gdf.to_crs(corredor_gdf.crs)
    return corredor_gdf, puntos_gdf

def ensure_id_column(gdf):
    """Asegura que exista una columna ID usando varios nombres candidatos"""
    cand = [c for c in ['ID','Sondeo','SONDEO','fid','FID'] if c in gdf.columns]
    if cand:
        gdf = gdf.copy()
        gdf['ID'] = gdf[cand[0]]
    else:
        gdf = gdf.copy()
        gdf['ID'] = np.arange(len(gdf))
    return gdf

def ensure_fs_min(gdf):
    """Calcula FS_min si no existe, usando todas las columnas FS_*"""
    if 'FS_min' in gdf.columns:
        return gdf
    g = gdf.copy()
    fs_cols = [c for c in g.columns if c.upper().startswith('FS_')]
    if not fs_cols:
        return g  # no hay de dónde calcular
    # fuerza numérico y toma el mínimo por fila
    for c in fs_cols:
        g[c] = pd.to_numeric(g[c], errors='coerce')
    g['FS_min'] = g[fs_cols].min(axis=1, skipna=True)
    return g

def ensure_haz_num(gdf):
    """Genera haz_num desde CLASIFICACION o FS_min si no existe"""
    if 'haz_num' in gdf.columns:
        return gdf
    g = gdf.copy()
    # 1) si existe CLASIFICACION textual -> mapea
    if 'CLASIFICACION' in g.columns:
        mapa = {'MUY BAJA':1,'BAJA':2,'MEDIA':3,'ALTA':4,'MUY ALTA':5}
        g['haz_num'] = (g['CLASIFICACION'].astype(str)
                        .str.upper().str.strip().map(mapa))
    # 2) si no, deriva de FS_min (ajusta umbrales a tu matriz INVÍAS)
    if 'haz_num' not in g or g['haz_num'].isna().all():
        g = ensure_fs_min(g)
        if 'FS_min' in g.columns:
            def fs_to_h(fs):
                if pd.isna(fs): return np.nan
                if fs >= 1.50: return 1   # muy baja
                if fs >= 1.30: return 2   # baja
                if fs >= 1.10: return 3   # media
                if fs >= 1.00: return 4   # alta
                return 5                  # muy alta
            g['haz_num'] = g['FS_min'].apply(fs_to_h).astype('Int64')
    return g

print("=" * 80)
print("GENERACIÓN DE MAPA DE AMENAZA - CORREDOR VIAL PIJAO")
print("Metodología: INVÍAS - SGC")
print("=" * 80)

# ==============================================================================
# 1. CONFIGURACIÓN Y PARÁMETROS
# ==============================================================================

# Archivos de entrada
CORREDOR_FILE = "corredor_pijao.gpkg"
PUNTOS_FILE = "puntos_pijao_joined.gpkg"

# Parámetros de interpolación
BUFFER_DISTANCE = 100  # metros - buffer alrededor del corredor para interpolación
RESOLUTION = 5  # metros - resolución del raster de salida
CAMPO_CONTINUO = "FS_min"  # campo continuo a interpolar (más técnicamente defendible)

# Umbrales INVÍAS para reclasificación FS_min -> haz_num
UMBRALES_FS = {
    'bins': [0, 1.0, 1.2, 1.5, 2.0, np.inf],
    'clases': [5, 4, 3, 2, 1],  # 5=Muy Alta, 4=Alta, 3=Media, 2=Baja, 1=Muy Baja
    'labels': ['≤1.0 (Muy Alta)', '≤1.2 (Alta)', '≤1.5 (Media)', '≤2.0 (Baja)', '>2.0 (Muy Baja)']
}

# Clasificación de amenaza según haz_num
AMENAZA_LABELS = {
    1: "MUY BAJA",
    2: "BAJA", 
    3: "MEDIA",
    4: "ALTA",
    5: "MUY ALTA"
}

# Colores para el mapa (según estándares SGC)
AMENAZA_COLORS = {
    1: '#1a9641',  # Verde oscuro - Muy Baja
    2: '#a6d96a',  # Verde claro - Baja
    3: '#ffffbf',  # Amarillo - Media
    4: '#fdae61',  # Naranja - Alta
    5: '#d7191c'   # Rojo - Muy Alta
}

# ==============================================================================
# 2. FUNCIONES DE PROCESAMIENTO
# ==============================================================================

def calcular_estadisticas_puntos(puntos_gdf):
    """
    Calcula estadísticas de los puntos críticos para el informe técnico
    """
    print("\n📊 ESTADÍSTICAS DE PUNTOS CRÍTICOS:")
    print("-" * 50)
    
    # Verificar campos necesarios
    campos_requeridos = ['FS_min', 'haz_num', 'cohesion', 'angulo_friccion', 
                         'peso_unitario', 'nivel_freatico']
    campos_disponibles = [col for col in campos_requeridos if col in puntos_gdf.columns]
    
    if 'haz_num' in puntos_gdf.columns:
        # Distribución de amenaza
        distribucion = puntos_gdf['haz_num'].value_counts().sort_index()
        print("\nDistribución de niveles de amenaza:")
        for nivel, count in distribucion.items():
            porcentaje = (count / len(puntos_gdf)) * 100
            print(f"  Nivel {nivel} ({AMENAZA_LABELS.get(nivel, 'N/A')}): "
                  f"{count} puntos ({porcentaje:.1f}%)")
    
    if 'FS_min' in puntos_gdf.columns:
        # Estadísticas de Factor de Seguridad
        print(f"\nFactor de Seguridad mínimo:")
        print(f"  Media: {puntos_gdf['FS_min'].mean():.3f}")
        print(f"  Mediana: {puntos_gdf['FS_min'].median():.3f}")
        print(f"  Mínimo: {puntos_gdf['FS_min'].min():.3f}")
        print(f"  Máximo: {puntos_gdf['FS_min'].max():.3f}")
        
        # Puntos críticos (FS < 1.0)
        puntos_criticos = puntos_gdf[puntos_gdf['FS_min'] < 1.0]
        if len(puntos_criticos) > 0:
            print(f"\n⚠️ ALERTA: {len(puntos_criticos)} puntos con FS < 1.0 (crítico)")
            if 'ID' in puntos_criticos.columns:
                print(f"  IDs críticos: {', '.join(puntos_criticos['ID'].astype(str).tolist())}")
    
    return campos_disponibles

def interpolar_idw(puntos, xi, yi, valores, power=2):
    """
    Interpolación IDW (Inverse Distance Weighting)
    Método recomendado por INVÍAS para mapas de amenaza
    """
    tree = cKDTree(puntos)
    distances, indices = tree.query(np.column_stack([xi.ravel(), yi.ravel()]), 
                                   k=min(10, len(puntos)))
    
    # Evitar división por cero
    distances = np.maximum(distances, 1e-10)
    
    # Calcular pesos IDW
    weights = 1.0 / (distances ** power)
    weights = weights / weights.sum(axis=1)[:, np.newaxis]
    
    # Interpolar valores
    interpolated = np.sum(weights * valores[indices], axis=1)
    
    return interpolated.reshape(xi.shape)

def crear_poligonos_voronoi(puntos_gdf, corredor_gdf, buffer_dist):
    """
    Crea polígonos de Voronoi limitados al área del corredor
    Versión robusta que evita celdas abiertas en el borde
    """
    print("\n🔷 Generando polígonos de Voronoi...")

    # coords reales
    coords = []
    for geom in puntos_gdf.geometry:
        if geom.geom_type == 'Point':
            coords.append([geom.x, geom.y])
        else:
            c = geom.centroid
            coords.append([c.x, c.y])
    coords = np.asarray(coords)
    n_real = len(coords)

    # buffer del corredor para recorte y caja para cerrar Voronoi
    corredor_buffer = corredor_gdf.unary_union.buffer(buffer_dist)
    xmin, ymin, xmax, ymax = corredor_buffer.bounds
    pad = buffer_dist * 3
    bbox_pts = np.array([
        [xmin - pad, ymin - pad],
        [xmin - pad, ymax + pad],
        [xmax + pad, ymin - pad],
        [xmax + pad, ymax + pad]
    ])

    # construye Voronoi con puntos "fantasma" para cerrar regiones
    all_pts = np.vstack([coords, bbox_pts])
    vor = Voronoi(all_pts)

    polys = []
    for point_idx in range(n_real):  # solo puntos reales
        region_idx = vor.point_region[point_idx]
        region = vor.regions[region_idx]
        if not region or -1 in region:
            continue
        poly = Polygon([vor.vertices[i] for i in region])
        poly = poly.intersection(corredor_buffer)
        if poly.is_empty:
            continue
        rec = {
            'geometry': poly,
            'haz_num': int(puntos_gdf.iloc[point_idx]['haz_num']),
            'FS_min': (puntos_gdf.iloc[point_idx]['FS_min']
                       if 'FS_min' in puntos_gdf.columns else None),
            'punto_id': puntos_gdf.iloc[point_idx]['ID']
        }
        polys.append(rec)

    out = gpd.GeoDataFrame(polys, crs=puntos_gdf.crs)
    print(f"  ✓ {len(out)} polígonos generados")
    return out

def reclasificar_fs_a_haz(fs_continuo, umbrales):
    """
    Reclasifica valores continuos de FS a categorías de amenaza (haz_num)
    usando umbrales INVÍAS
    """
    bins = umbrales['bins']
    clases = umbrales['clases']
    
    # Digitalizar usando los bins
    indices = np.digitize(fs_continuo, bins, right=True)
    
    # Mapear a clases de amenaza
    raster_clasificado = np.zeros_like(fs_continuo, dtype=np.uint8)
    for i, clase in enumerate(clases, 1):
        mask = (indices == i)
        raster_clasificado[mask] = clase
    
    return raster_clasificado

def generar_raster_amenaza(puntos_gdf, corredor_gdf, resolution, buffer_dist, method='idw'):
    """
    Genera raster de amenaza interpolando campo continuo (FS_min) y reclasificando
    Método técnicamente más defendible que interpolar categorías
    """
    print(f"\n🌐 Generando raster de amenaza (método: {method.upper()})...")
    print(f"  Campo interpolado: {CAMPO_CONTINUO}")
    
    # Verificar que existe el campo continuo
    if CAMPO_CONTINUO not in puntos_gdf.columns:
        print(f"  ⚠️ ERROR: Campo '{CAMPO_CONTINUO}' no encontrado")
        print(f"  Campos disponibles: {list(puntos_gdf.columns)}")
        return None, None, None
    
    area = corredor_gdf.unary_union.buffer(buffer_dist)
    xmin, ymin, xmax, ymax = area.bounds

    width  = max(1, int(np.ceil((xmax - xmin) / resolution)))
    height = max(1, int(np.ceil((ymax - ymin) / resolution)))

    print(f"  Dimensiones del raster: {width} x {height} píxeles")
    print(f"  Resolución: {resolution} m/píxel")

    x = np.linspace(xmin, xmax, width)
    y = np.linspace(ymin, ymax, height)
    xi, yi = np.meshgrid(x, y)

    # coords de puntos
    coords = np.array([
        (g.x, g.y) if g.geom_type == 'Point' else (g.centroid.x, g.centroid.y)
        for g in puntos_gdf.geometry
    ])
    
    # Usar campo continuo para interpolación
    vals_continuas = puntos_gdf[CAMPO_CONTINUO].astype(float).values
    
    # Verificar valores válidos
    mask_validos = ~np.isnan(vals_continuas)
    if not np.any(mask_validos):
        print(f"  ⚠️ ERROR: No hay valores válidos en {CAMPO_CONTINUO}")
        return None, None, None
    
    coords_validos = coords[mask_validos]
    vals_validas = vals_continuas[mask_validos]
    
    print(f"  Interpolando {len(vals_validas)} puntos válidos")
    print(f"  Rango de {CAMPO_CONTINUO}: {vals_validas.min():.3f} - {vals_validas.max():.3f}")

    # Interpolar campo continuo
    if method == 'idw':
        zi_continuo = interpolar_idw(coords_validos, xi, yi, vals_validas, power=2)
    else:
        zi_continuo = griddata(coords_validos, vals_validas, (xi, yi), method='nearest')

    from rasterio.features import geometry_mask
    transform = from_bounds(xmin, ymin, xmax, ymax, width, height)
    mask = geometry_mask([area], transform=transform, out_shape=(height, width), invert=True)
    zi_continuo[~mask] = np.nan

    # Reclasificar FS continuo a haz_num usando umbrales INVÍAS
    print(f"  Reclasificando usando umbrales INVÍAS:")
    for i, label in enumerate(UMBRALES_FS['labels']):
        print(f"    {UMBRALES_FS['clases'][i]}: {label}")
    
    # Aplicar reclasificación solo a valores válidos
    mask_validos_raster = ~np.isnan(zi_continuo)
    zi_clasificado = np.zeros_like(zi_continuo, dtype=np.uint8)
    
    if np.any(mask_validos_raster):
        zi_clasificado[mask_validos_raster] = reclasificar_fs_a_haz(
            zi_continuo[mask_validos_raster], UMBRALES_FS
        )

    print("  ✓ Raster generado y reclasificado exitosamente")
    return zi_clasificado, transform, (xmin, ymin, xmax, ymax)

def exportar_raster(raster_data, transform, crs, output_file):
    """
    Exporta el raster de amenaza a GeoTIFF con nodata
    """
    print(f"\n💾 Exportando raster a: {output_file}")
    with rasterio.open(
        output_file, 'w', driver='GTiff',
        height=raster_data.shape[0], width=raster_data.shape[1],
        count=1, dtype=raster_data.dtype, crs=crs, transform=transform,
        compress='deflate', nodata=0
    ) as dst:
        dst.write(raster_data, 1)
        dst.set_band_description(1, 'Indice_Amenaza_haz_num')
    print("  ✓ Raster exportado exitosamente")

def crear_mapa_amenaza(puntos_gdf, corredor_gdf, voronoi_gdf, raster_data, bounds):
    """
    Crea visualización completa del mapa de amenaza
    """
    print("\n🗺️ Generando mapa de amenaza...")
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))
    
    # Configurar colormaps
    colors = [AMENAZA_COLORS[i] for i in range(1, 6)]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(boundaries=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5], ncolors=5)
    
    # Convertir geometrías a puntos si es necesario
    puntos_plot = puntos_gdf.copy()
    if puntos_gdf.geometry.iloc[0].geom_type != 'Point':
        puntos_plot['geometry'] = puntos_gdf.geometry.centroid
    
    # MAPA 1: Polígonos de Voronoi
    ax1 = axes[0]
    if voronoi_gdf is not None and len(voronoi_gdf) > 0:
        voronoi_gdf.plot(column='haz_num', ax=ax1, cmap=cmap, norm=norm, 
                         edgecolor='gray', linewidth=0.5, alpha=0.8)
    
    corredor_gdf.plot(ax=ax1, color='none', edgecolor='black', linewidth=2)
    puntos_plot.plot(ax=ax1, color='black', markersize=30, zorder=5)
    
    # Agregar etiquetas a puntos
    if 'ID' in puntos_gdf.columns:
        for idx, row in puntos_gdf.iterrows():
            # Obtener coordenadas del centroide
            if row.geometry.geom_type == 'Point':
                x, y = row.geometry.x, row.geometry.y
            else:
                centroid = row.geometry.centroid
                x, y = centroid.x, centroid.y
            
            ax1.annotate(str(row.get('ID', idx)), 
                        xy=(x, y),
                        xytext=(3, 3), textcoords='offset points',
                        fontsize=8, fontweight='bold')
    
    ax1.set_title('MAPA DE AMENAZA - Polígonos de Voronoi\nCorredor Vial Pijao', 
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('Coordenada Este (m)')
    ax1.set_ylabel('Coordenada Norte (m)')
    ax1.grid(True, alpha=0.3)
    
    # MAPA 2: Interpolación IDW (Raster)
    ax2 = axes[1]
    if raster_data is not None:
        extent = [bounds[0], bounds[2], bounds[1], bounds[3]]
        im = ax2.imshow(raster_data, extent=extent, cmap=cmap, norm=norm, 
                       alpha=0.8, origin='lower')
    
    corredor_gdf.plot(ax=ax2, color='none', edgecolor='black', linewidth=2)
    puntos_plot.plot(ax=ax2, color='black', markersize=30, zorder=5)
    
    # Agregar etiquetas a puntos
    if 'ID' in puntos_gdf.columns:
        for idx, row in puntos_gdf.iterrows():
            # Obtener coordenadas del centroide
            if row.geometry.geom_type == 'Point':
                x, y = row.geometry.x, row.geometry.y
            else:
                centroid = row.geometry.centroid
                x, y = centroid.x, centroid.y
                
            ax2.annotate(str(row.get('ID', idx)), 
                        xy=(x, y),
                        xytext=(3, 3), textcoords='offset points',
                        fontsize=8, fontweight='bold')
    
    ax2.set_title('MAPA DE AMENAZA - Interpolación IDW\nCorredor Vial Pijao', 
                  fontsize=14, fontweight='bold')
    ax2.set_xlabel('Coordenada Este (m)')
    ax2.set_ylabel('Coordenada Norte (m)')
    ax2.grid(True, alpha=0.3)
    
    # Leyenda común
    legend_elements = [mpatches.Patch(facecolor=AMENAZA_COLORS[i], 
                                     edgecolor='black', 
                                     label=f'{i} - {AMENAZA_LABELS[i]}')
                      for i in range(1, 6)]
    
    fig.legend(handles=legend_elements, loc='lower center', ncol=5, 
              title='NIVEL DE AMENAZA POR MOVIMIENTO EN MASA',
              bbox_to_anchor=(0.5, -0.05), fontsize=11)
    
    plt.suptitle('ANÁLISIS DE AMENAZA GEOTÉCNICA - METODOLOGÍA INVÍAS/SGC', 
                fontsize=16, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    
    # Guardar mapa
    output_file = 'mapa_amenaza_pijao.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✓ Mapa guardado como: {output_file}")
    
    plt.show()
    
    return fig

def generar_informe_tecnico(puntos_gdf, voronoi_gdf, estadisticas):
    """
    Genera informe técnico para interventoría
    """
    print("\n📄 GENERANDO INFORME TÉCNICO...")
    print("=" * 80)
    
    informe = []
    informe.append("INFORME TÉCNICO - MAPA DE AMENAZA POR MOVIMIENTOS EN MASA")
    informe.append("=" * 80)
    informe.append(f"Corredor Vial: Pijao, Quindío")
    informe.append(f"Metodología: INVÍAS - Servicio Geológico Colombiano (SGC)")
    informe.append(f"Fecha: Noviembre 2025")
    informe.append("")
    
    # Resumen ejecutivo
    informe.append("1. RESUMEN EJECUTIVO")
    informe.append("-" * 40)
    informe.append(f"Total de puntos analizados: {len(puntos_gdf)}")
    
    if 'haz_num' in puntos_gdf.columns:
        distribucion = puntos_gdf['haz_num'].value_counts().sort_index()
        for nivel, count in distribucion.items():
            porcentaje = (count / len(puntos_gdf)) * 100
            informe.append(f"  • Amenaza {AMENAZA_LABELS.get(nivel, 'N/A')}: "
                          f"{count} puntos ({porcentaje:.1f}%)")
    
    # Puntos críticos
    if 'FS_min' in puntos_gdf.columns:
        puntos_criticos = puntos_gdf[puntos_gdf['FS_min'] < 1.0]
        if len(puntos_criticos) > 0:
            informe.append("")
            informe.append("2. PUNTOS CRÍTICOS (FS < 1.0)")
            informe.append("-" * 40)
            for idx, punto in puntos_criticos.iterrows():
                informe.append(f"  PC-{punto.get('ID', idx)}:")
                informe.append(f"    - FS mínimo: {punto['FS_min']:.3f}")
                if 'haz_num' in punto:
                    informe.append(f"    - Nivel amenaza: {punto['haz_num']} "
                                 f"({AMENAZA_LABELS.get(punto['haz_num'], 'N/A')})")
                informe.append(f"    - REQUIERE INTERVENCIÓN INMEDIATA")
    
    # Metodología
    informe.append("")
    informe.append("3. METODOLOGÍA APLICADA")
    informe.append("-" * 40)
    informe.append("  • Análisis de estabilidad de taludes (Método del talud infinito)")
    informe.append("  • Cálculo de Factor de Seguridad para múltiples escenarios")
    informe.append("  • Clasificación de amenaza según FS mínimo")
    informe.append("  • Interpolación espacial IDW para mapa continuo")
    informe.append("  • Generación de polígonos de Voronoi para zonificación")
    
    # Recomendaciones
    informe.append("")
    informe.append("4. RECOMENDACIONES")
    informe.append("-" * 40)
    
    if 'haz_num' in puntos_gdf.columns:
        puntos_alta_amenaza = puntos_gdf[puntos_gdf['haz_num'] >= 4]
        if len(puntos_alta_amenaza) > 0:
            informe.append(f"  ⚠️ {len(puntos_alta_amenaza)} puntos con amenaza ALTA o MUY ALTA")
            informe.append("     Implementar medidas de estabilización prioritarias:")
            informe.append("     - Obras de drenaje y subdrenaje")
            informe.append("     - Muros de contención o anclajes")
            informe.append("     - Reconformación de taludes")
            informe.append("     - Monitoreo instrumental continuo")
    
    # Guardar informe
    informe_texto = "\n".join(informe)
    with open('informe_tecnico_amenaza_pijao.txt', 'w', encoding='utf-8') as f:
        f.write(informe_texto)
    
    print(informe_texto)
    print("\n✓ Informe guardado como: informe_tecnico_amenaza_pijao.txt")
    
    return informe_texto

# ==============================================================================
# 3. PROCESO PRINCIPAL
# ==============================================================================

def verificar_y_convertir_geometrias(gdf, nombre=""):
    """
    Verifica el tipo de geometría y convierte a puntos si es necesario
    """
    tipo_geom = gdf.geometry.iloc[0].geom_type if len(gdf) > 0 else "Unknown"
    print(f"  Tipo de geometría en {nombre}: {tipo_geom}")
    
    if tipo_geom != 'Point':
        print(f"  ⚠️ Convirtiendo geometrías a puntos (centroides)...")
        gdf_puntos = gdf.copy()
        gdf_puntos['geometry'] = gdf.geometry.centroid
        return gdf_puntos
    
    return gdf

def main():
    """
    Proceso principal de generación del mapa de amenaza
    """
    try:
        # Cargar datos
        print("\n📂 Cargando archivos GeoPackage...")
        corredor_gdf = gpd.read_file(CORREDOR_FILE)
        puntos_gdf = gpd.read_file(PUNTOS_FILE)
        
        print(f"  ✓ Corredor cargado: {len(corredor_gdf)} geometrías")
        print(f"  ✓ Puntos cargados: {len(puntos_gdf)} puntos críticos")
        
        # Aplicar funciones de robustez
        corredor_gdf, puntos_gdf = ensure_projected(corredor_gdf, puntos_gdf)
        puntos_gdf = verificar_y_convertir_geometrias(puntos_gdf, "puntos_pijao_joined")
        puntos_gdf = ensure_id_column(puntos_gdf)
        puntos_gdf = ensure_fs_min(puntos_gdf)
        puntos_gdf = ensure_haz_num(puntos_gdf)
        
        print(f"  CRS del proyecto: {corredor_gdf.crs}")
        
        # Validar campos necesarios
        if 'haz_num' not in puntos_gdf.columns or puntos_gdf['haz_num'].isna().all():
            print("\n⚠️ ERROR: no pude derivar 'haz_num'. Revisa CLASIFICACION o FS_*.")
            print("Campos disponibles:", list(puntos_gdf.columns))
            return
        
        if CAMPO_CONTINUO not in puntos_gdf.columns:
            print(f"\n⚠️ ERROR: Campo continuo '{CAMPO_CONTINUO}' no encontrado.")
            print("Campos disponibles:", list(puntos_gdf.columns))
            return
        
        # Verificar valores válidos en campo continuo
        vals_validos = puntos_gdf[CAMPO_CONTINUO].notna().sum()
        print(f"  ✓ Campo continuo '{CAMPO_CONTINUO}': {vals_validos}/{len(puntos_gdf)} valores válidos")
        
        # Calcular estadísticas
        estadisticas = calcular_estadisticas_puntos(puntos_gdf)
        
        # Generar polígonos de Voronoi
        voronoi_gdf = crear_poligonos_voronoi(puntos_gdf, corredor_gdf, BUFFER_DISTANCE)
        
        # Guardar Voronoi
        voronoi_output = 'voronoi_amenaza_pijao.gpkg'
        voronoi_gdf.to_file(voronoi_output, driver='GPKG')
        print(f"  ✓ Polígonos Voronoi guardados: {voronoi_output}")
        
        # Generar raster IDW interpolando campo continuo
        raster_data, transform, bounds = generar_raster_amenaza(
            puntos_gdf, corredor_gdf, RESOLUTION, BUFFER_DISTANCE, method='idw'
        )
        
        # Verificar que el raster se generó correctamente
        if raster_data is None:
            print("\n❌ Error en la generación del raster. Abortando proceso.")
            return
        
        # Exportar raster
        exportar_raster(raster_data, transform, corredor_gdf.crs, 
                       'raster_amenaza_pijao.tif')
        
        # Crear mapa de visualización
        fig = crear_mapa_amenaza(puntos_gdf, corredor_gdf, voronoi_gdf, 
                                raster_data, bounds)
        
        # Generar informe técnico
        informe = generar_informe_tecnico(puntos_gdf, voronoi_gdf, estadisticas)
        
        # Resumen final
        print("\n" + "=" * 80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print("\nArchivos generados:")
        print("  1. voronoi_amenaza_pijao.gpkg - Polígonos de zonificación")
        print("  2. raster_amenaza_pijao.tif - Raster de amenaza continuo")
        print("  3. mapa_amenaza_pijao.png - Visualización cartográfica")
        print("  4. informe_tecnico_amenaza_pijao.txt - Informe para interventoría")
        print("\n📋 Estos productos cumplen con los requisitos INVÍAS/SGC")
        print("   para mapas de amenaza por movimientos en masa")
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: No se encontró el archivo: {e}")
        print("   Verifica que los archivos estén en el directorio actual:")
        print(f"   - {CORREDOR_FILE}")
        print(f"   - {PUNTOS_FILE}")
    
    except Exception as e:
        print(f"\n❌ ERROR inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
