"""
Carga de archivos GeoPackage y rasters con validacion
"""

import geopandas as gpd
import rasterio
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import VALORES_DISCRETOS_VALIDOS, clasificar_fs_array, UMBRALES_AMENAZA


def load_gpkg(
    file_path: Path,
    layer_name: Optional[str] = None,
    to_4326: bool = True
) -> gpd.GeoDataFrame:
    """
    Carga GeoPackage con manejo de errores y reproyeccion opcional.

    Args:
        file_path: Path al archivo .gpkg
        layer_name: Nombre de capa (opcional)
        to_4326: Si True, reproyecta a EPSG:4326

    Returns:
        GeoDataFrame

    Raises:
        FileNotFoundError: Si el archivo no existe
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"No se encontro: {file_path}")

    gdf = gpd.read_file(file_path, layer=layer_name)

    # Reproyectar a EPSG:4326 para Folium
    if to_4326 and gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    return gdf


def prepare_puntos(puntos_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Prepara GeoDataFrame de puntos para visualizacion.
    - Convierte geometrias no-punto a centroides
    - Valida columnas requeridas (FS_min, haz_num)
    - Crea columna ID si no existe

    Args:
        puntos_gdf: GeoDataFrame con puntos criticos

    Returns:
        GeoDataFrame preparado
    """
    gdf = puntos_gdf.copy()

    # Convertir a Point si es necesario
    if len(gdf) > 0 and gdf.geometry.iloc[0].geom_type != 'Point':
        # Reproyectar a CRS proyectado para centroid correcto
        original_crs = gdf.crs
        if gdf.crs is not None and gdf.crs.is_geographic:
            gdf_proj = gdf.to_crs("EPSG:3116")  # MAGNA-SIRGAS Colombia Bogota
            gdf_proj['geometry'] = gdf_proj.geometry.centroid
            gdf = gdf_proj.to_crs(original_crs)
        else:
            gdf['geometry'] = gdf.geometry.centroid

    # Buscar columna ID
    id_candidates = ['ID', 'id', 'SONDEO', 'Sondeo', 'fid', 'FID', 'OBJECTID']
    id_col = None
    for col in id_candidates:
        if col in gdf.columns:
            id_col = col
            break

    if id_col and id_col != 'ID':
        gdf['ID'] = gdf[id_col]
    elif 'ID' not in gdf.columns:
        gdf['ID'] = range(1, len(gdf) + 1)

    # Validar columnas requeridas
    if 'FS_min' not in gdf.columns:
        # Intentar calcular de columnas FS_*
        fs_cols = [c for c in gdf.columns if c.startswith('FS_') and c != 'FS_min']
        if fs_cols:
            gdf['FS_min'] = gdf[fs_cols].min(axis=1)
        else:
            gdf['FS_min'] = np.nan

    if 'haz_num' not in gdf.columns:
        # Calcular de FS_min si existe
        if 'FS_min' in gdf.columns and not gdf['FS_min'].isna().all():
            from config import clasificar_fs
            gdf['haz_num'] = gdf['FS_min'].apply(clasificar_fs)
        else:
            gdf['haz_num'] = np.nan

    return gdf


def load_raster_with_validation(raster_path: Path) -> Dict[str, Any]:
    """
    Carga raster y valida si es discreto o continuo.

    Args:
        raster_path: Path al archivo .tif

    Returns:
        dict con:
            - data: numpy array con valores (reclasificado si era continuo)
            - transform: affine transform
            - crs: CRS del raster
            - bounds: bounds en CRS original
            - bounds_4326: bounds en EPSG:4326
            - is_discrete: bool
            - reclassified: bool
            - metadata: info adicional
    """
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs
        bounds = src.bounds

        # Calcular bounds en 4326
        if crs and crs.to_epsg() != 4326:
            from rasterio.warp import transform_bounds
            bounds_4326 = transform_bounds(crs, 'EPSG:4326', *bounds)
        else:
            bounds_4326 = bounds

        # Detectar si es discreto
        valid_mask = (data != 0) & ~np.isnan(data)
        valid_data = data[valid_mask]

        if len(valid_data) == 0:
            is_discrete = True
            unique_vals = []
        else:
            unique_vals = np.unique(valid_data)
            is_discrete = all(
                v in VALORES_DISCRETOS_VALIDOS or
                (isinstance(v, (float, np.floating)) and float(v).is_integer() and int(v) in VALORES_DISCRETOS_VALIDOS)
                for v in unique_vals
            )

        # Reclasificar si es continuo
        reclassified = False
        if not is_discrete:
            data = clasificar_fs_array(data.astype(np.float32))
            reclassified = True

        metadata = {
            'original_unique_values': unique_vals.tolist()[:10] if len(unique_vals) <= 10 else f'{len(unique_vals)} valores unicos',
            'min': float(np.nanmin(valid_data)) if len(valid_data) > 0 else None,
            'max': float(np.nanmax(valid_data)) if len(valid_data) > 0 else None,
            'dtype': str(src.dtypes[0]),
            'shape': data.shape,
            'crs': str(crs),
            'umbrales_aplicados': UMBRALES_AMENAZA['version'] if reclassified else 'N/A (ya discreto)'
        }

        return {
            'data': data,
            'transform': transform,
            'crs': crs,
            'bounds': bounds,
            'bounds_4326': bounds_4326,
            'is_discrete': is_discrete,
            'reclassified': reclassified,
            'metadata': metadata
        }


def get_estadisticas_puntos(puntos_gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
    """
    Calcula estadisticas de los puntos criticos.

    Args:
        puntos_gdf: GeoDataFrame con puntos

    Returns:
        dict con estadisticas
    """
    stats = {
        'total_puntos': len(puntos_gdf),
        'distribucion_amenaza': {},
        'fs_min_stats': {}
    }

    if 'haz_num' in puntos_gdf.columns:
        dist = puntos_gdf['haz_num'].value_counts().sort_index().to_dict()
        stats['distribucion_amenaza'] = {int(k): int(v) for k, v in dist.items()}

    if 'FS_min' in puntos_gdf.columns:
        fs_valid = puntos_gdf['FS_min'].dropna()
        if len(fs_valid) > 0:
            stats['fs_min_stats'] = {
                'min': float(fs_valid.min()),
                'max': float(fs_valid.max()),
                'mean': float(fs_valid.mean()),
                'std': float(fs_valid.std())
            }

    return stats
