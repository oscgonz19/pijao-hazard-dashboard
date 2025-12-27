"""
Dashboard de Amenaza Geotecnica - Corredor Vial
Streamlit + Folium

Ejecutar con:
    conda activate pijao_dashboard
    streamlit run app.py
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from pathlib import Path

from config import (
    DATA_DIR, ARCHIVOS_REGION, UMBRALES_AMENAZA,
    COLORES_SGC, COLORES_RGBA, MAPA_CONFIG,
    get_regiones_disponibles, get_archivos_region
)
from utils.data_loader import load_gpkg, prepare_puntos, get_estadisticas_puntos
from utils.geotiff_overlay import raster_to_folium_overlay
from utils.styles import style_punto, style_voronoi, style_corredor, create_popup_html, create_legend_html


# ==============================================================================
# CONFIGURACION DE PAGINA
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Amenaza Geotecnica",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==============================================================================
# CACHE DE DATOS
# ==============================================================================
@st.cache_data
def load_region_data(region: str):
    """Carga todos los datos de una region con cache."""
    archivos = get_archivos_region(region)
    data = {'region': region, 'archivos': archivos}

    # Cargar puntos
    if archivos['puntos']:
        puntos = load_gpkg(archivos['puntos'])
        puntos = prepare_puntos(puntos)
        data['puntos'] = puntos
        data['stats'] = get_estadisticas_puntos(puntos)
    else:
        data['puntos'] = None
        data['stats'] = None

    # Cargar corredor
    if archivos['corredor']:
        data['corredor'] = load_gpkg(archivos['corredor'])
    else:
        data['corredor'] = None

    # Cargar voronoi
    if archivos['voronoi']:
        data['voronoi'] = load_gpkg(archivos['voronoi'])
    else:
        data['voronoi'] = None

    # Cargar y procesar raster
    if archivos['raster']:
        data['raster_overlay'] = raster_to_folium_overlay(
            archivos['raster'],
            colormap=COLORES_RGBA,
            auto_detect=True
        )
    else:
        data['raster_overlay'] = None

    return data


# ==============================================================================
# SIDEBAR
# ==============================================================================
st.sidebar.title("⚙️ Configuracion")

# Selector de region
regiones = get_regiones_disponibles()

if not regiones:
    st.sidebar.error("No se encontraron regiones en data/")
    st.sidebar.info(
        "Estructura esperada:\n"
        "```\n"
        "data/\n"
        "  pijao/\n"
        "    puntos.gpkg\n"
        "    corredor.gpkg\n"
        "    voronoi.gpkg\n"
        "    raster_amenaza.tif\n"
        "```"
    )
    st.stop()

region_seleccionada = st.sidebar.selectbox(
    "Region",
    options=regiones,
    index=0,
    help="Selecciona la region a visualizar"
)

st.sidebar.markdown("---")

# Cargar datos de la region
with st.spinner(f"Cargando datos de {region_seleccionada}..."):
    data = load_region_data(region_seleccionada)

# Filtros
st.sidebar.subheader("Filtros")

amenaza_min = st.sidebar.slider(
    "Amenaza minima",
    min_value=1,
    max_value=5,
    value=1,
    help="Mostrar puntos con amenaza >= este valor"
)

n_puntos = len(data['puntos']) if data['puntos'] is not None else 0
top_n = st.sidebar.slider(
    "Top N puntos",
    min_value=1,
    max_value=max(n_puntos, 1),
    value=min(10, n_puntos) if n_puntos > 0 else 1,
    help="Numero de puntos a mostrar en tabla"
)

st.sidebar.markdown("---")

# Toggle de capas
st.sidebar.subheader("Capas")

show_raster = st.sidebar.checkbox(
    "Raster de amenaza",
    value=data['raster_overlay'] is not None,
    disabled=data['raster_overlay'] is None
)

show_voronoi = st.sidebar.checkbox(
    "Poligonos Voronoi",
    value=False,
    disabled=data['voronoi'] is None
)

show_corredor = st.sidebar.checkbox(
    "Corredor vial",
    value=data['corredor'] is not None,
    disabled=data['corredor'] is None
)

show_puntos = st.sidebar.checkbox(
    "Puntos criticos",
    value=True,
    disabled=data['puntos'] is None
)

# Opacidad del raster
if show_raster and data['raster_overlay']:
    raster_opacity = st.sidebar.slider(
        "Opacidad raster",
        min_value=0.0,
        max_value=1.0,
        value=MAPA_CONFIG['opacity_raster'],
        step=0.1
    )
else:
    raster_opacity = MAPA_CONFIG['opacity_raster']


# ==============================================================================
# CONTENIDO PRINCIPAL
# ==============================================================================
st.title(f"🗺️ Dashboard de Amenaza Geotecnica")
st.markdown(f"**Region:** {region_seleccionada.upper()}")

# Alertas sobre el raster
if data['raster_overlay'] and data['raster_overlay'].get('reclassified'):
    st.warning(
        "⚠️ El raster contiene valores continuos (FS). "
        f"Se reclasificó automaticamente usando umbrales: **{UMBRALES_AMENAZA['version']}**"
    )

# Filtrar puntos
if data['puntos'] is not None:
    puntos_gdf = data['puntos'].copy()
    puntos_filtrados = puntos_gdf[puntos_gdf['haz_num'] >= amenaza_min].copy()
    puntos_filtrados = puntos_filtrados.sort_values(
        by=['haz_num', 'FS_min'],
        ascending=[False, True]
    )
else:
    puntos_filtrados = None

# ==============================================================================
# MAPA
# ==============================================================================
st.subheader("Mapa Interactivo")

# Calcular centro del mapa
if puntos_filtrados is not None and len(puntos_filtrados) > 0:
    center = [
        puntos_filtrados.geometry.y.mean(),
        puntos_filtrados.geometry.x.mean()
    ]
elif data['corredor'] is not None:
    bounds = data['corredor'].total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
else:
    center = [4.32, -75.68]  # Default: Quindio

# Crear mapa base
m = folium.Map(
    location=center,
    zoom_start=MAPA_CONFIG['zoom_default'],
    tiles='OpenStreetMap'
)

# Agregar tile layers adicionales
folium.TileLayer('CartoDB positron', name='CartoDB Light').add_to(m)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri',
    name='Esri Satellite'
).add_to(m)

# Capa: Raster overlay
if show_raster and data['raster_overlay']:
    overlay = data['raster_overlay']
    folium.raster_layers.ImageOverlay(
        image=overlay['image'],
        bounds=overlay['bounds'],
        opacity=raster_opacity,
        name='Amenaza (IDW)',
        interactive=False
    ).add_to(m)

# Capa: Voronoi
if show_voronoi and data['voronoi'] is not None:
    folium.GeoJson(
        data['voronoi'].__geo_interface__,
        name='Voronoi',
        style_function=style_voronoi,
        tooltip=folium.GeoJsonTooltip(
            fields=['haz_num'],
            aliases=['Amenaza:'],
            localize=True
        )
    ).add_to(m)

# Capa: Corredor
if show_corredor and data['corredor'] is not None:
    folium.GeoJson(
        data['corredor'].__geo_interface__,
        name='Corredor',
        style_function=style_corredor
    ).add_to(m)

# Capa: Puntos
if show_puntos and puntos_filtrados is not None and len(puntos_filtrados) > 0:
    fg_puntos = folium.FeatureGroup(name='Puntos criticos')

    for idx, row in puntos_filtrados.iterrows():
        style = style_punto(row)
        popup_html = create_popup_html(row)

        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=style['radius'],
            color=style['color'],
            weight=style['weight'],
            fill=True,
            fill_color=style['fill_color'],
            fill_opacity=style['fill_opacity'],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Punto {row['ID']} - Amenaza {int(row['haz_num'])}"
        ).add_to(fg_puntos)

    fg_puntos.add_to(m)

# Control de capas
folium.LayerControl(collapsed=False).add_to(m)

# Agregar leyenda
legend_html = create_legend_html()
m.get_root().html.add_child(folium.Element(legend_html))

# Renderizar mapa
map_data = st_folium(
    m,
    width=None,
    height=550,
    returned_objects=["last_object_clicked"]
)

# ==============================================================================
# TABLA DE PUNTOS CRITICOS
# ==============================================================================
st.subheader(f"📊 Top {top_n} Puntos Criticos")

if puntos_filtrados is not None and len(puntos_filtrados) > 0:
    # Preparar tabla
    top_puntos = puntos_filtrados.head(top_n).copy()

    # Agregar columnas de display
    top_puntos['Clasificacion'] = top_puntos['haz_num'].apply(
        lambda x: UMBRALES_AMENAZA['labels_cortos'].get(int(x), 'N/A') if pd.notna(x) else 'N/A'
    )
    top_puntos['Accion'] = top_puntos['haz_num'].apply(
        lambda x: '⚠️ Inmediata' if x >= 4 else ('📋 Monitoreo' if x == 3 else '✅ Rutina')
    )

    # Seleccionar columnas para mostrar
    cols_display = ['ID', 'FS_min', 'haz_num', 'Clasificacion', 'Accion']
    cols_disponibles = [c for c in cols_display if c in top_puntos.columns]

    tabla = top_puntos[cols_disponibles].copy()
    tabla = tabla.reset_index(drop=True)

    # Formatear FS_min
    if 'FS_min' in tabla.columns:
        tabla['FS_min'] = tabla['FS_min'].apply(
            lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
        )

    # Mostrar tabla con estilo
    st.dataframe(
        tabla,
        width='stretch',
        hide_index=True,
        column_config={
            'ID': st.column_config.TextColumn('ID', width='small'),
            'FS_min': st.column_config.TextColumn('FS min', width='small'),
            'haz_num': st.column_config.NumberColumn('Clase', width='small'),
            'Clasificacion': st.column_config.TextColumn('Clasificacion', width='medium'),
            'Accion': st.column_config.TextColumn('Accion Requerida', width='medium')
        }
    )
else:
    st.info("No hay puntos que cumplan los criterios de filtro.")

# ==============================================================================
# METADATOS
# ==============================================================================
st.subheader("ℹ️ Metadatos")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total puntos",
        n_puntos
    )
    if puntos_filtrados is not None:
        st.metric(
            "Puntos filtrados",
            len(puntos_filtrados)
        )

with col2:
    if data['raster_overlay']:
        is_discrete = data['raster_overlay'].get('is_discrete', True)
        reclassified = data['raster_overlay'].get('metadata', {}).get('reclassified', False)
        st.metric(
            "Tipo raster",
            "Discreto" if is_discrete else "Continuo",
            delta="Reclasificado" if reclassified else None
        )
    else:
        st.metric("Raster", "No disponible")

with col3:
    st.metric(
        "Umbrales",
        UMBRALES_AMENAZA['version']
    )

# Expandir detalles tecnicos
with st.expander("Ver detalles tecnicos"):
    tabs = st.tabs(["Umbrales", "Raster", "Archivos"])

    with tabs[0]:
        st.markdown("**Umbrales de clasificacion:**")
        for haz_num, label in UMBRALES_AMENAZA['labels'].items():
            color = COLORES_SGC[haz_num]
            st.markdown(
                f'<span style="background-color:{color}; padding: 2px 8px; '
                f'color: {"white" if haz_num >= 4 else "black"}; border-radius: 3px;">'
                f'{haz_num}</span> {label}',
                unsafe_allow_html=True
            )

    with tabs[1]:
        if data['raster_overlay']:
            st.json(data['raster_overlay'].get('metadata', {}))
        else:
            st.info("Raster no disponible")

    with tabs[2]:
        archivos_info = {k: str(v) if v else "No encontrado" for k, v in data['archivos'].items()}
        st.json(archivos_info)

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
st.caption(
    f"Dashboard de Amenaza Geotecnica | Region: {region_seleccionada} | "
    f"Umbrales: {UMBRALES_AMENAZA['version']}"
)
