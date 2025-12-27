"""
Conversion de GeoTIFF a PNG RGBA para overlays en Folium
Similar al helper de Google Earth Engine usado en Buenavista

Flujo:
1. Leer GeoTIFF con rasterio
2. Aplicar colormap SGC segun valores 1-5
3. Generar PNG RGBA en memoria con transparencia
4. Calcular bounds en EPSG:4326 para ImageOverlay de Folium
"""

import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from PIL import Image
from io import BytesIO
import base64
from pathlib import Path
from typing import Tuple, Dict, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import COLORES_RGBA, VALORES_DISCRETOS_VALIDOS, clasificar_fs_array


def raster_to_png_base64(
    raster_path: Path,
    colormap: Dict[int, Tuple[int, int, int, int]] = COLORES_RGBA,
    nodata_value: int = 0,
    is_discrete: bool = True
) -> Tuple[str, list]:
    """
    Convierte un GeoTIFF a PNG base64 con colormap aplicado.

    Args:
        raster_path: Ruta al archivo .tif
        colormap: Dict {clase: (R,G,B,A)} en valores 0-255
        nodata_value: Valor que representa "sin datos"
        is_discrete: Si False, reclasifica valores continuos de FS

    Returns:
        tuple: (png_base64_string, bounds_folium)
               bounds_folium = [[south, west], [north, east]]
    """
    with rasterio.open(raster_path) as src:
        # Leer banda 1
        data = src.read(1)
        bounds = src.bounds
        crs = src.crs

        # Convertir bounds a EPSG:4326 si es necesario
        if crs and crs.to_epsg() != 4326:
            bounds_4326 = transform_bounds(crs, 'EPSG:4326', *bounds)
        else:
            bounds_4326 = bounds

        # Si no es discreto, reclasificar valores continuos de FS
        if not is_discrete:
            data = clasificar_fs_array(data.astype(np.float32))

        # Crear imagen RGBA
        height, width = data.shape
        rgba = np.zeros((height, width, 4), dtype=np.uint8)

        # Aplicar colormap
        for clase, color in colormap.items():
            mask = (data == clase)
            rgba[mask] = color

        # Transparencia total para nodata
        mask_nodata = (data == nodata_value)
        rgba[mask_nodata, 3] = 0

        # Convertir a PIL Image
        img = Image.fromarray(rgba, mode='RGBA')

        # Guardar en memoria como PNG
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        # Codificar en base64
        png_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        # Bounds para Folium: [[south, west], [north, east]]
        bounds_folium = [
            [bounds_4326[1], bounds_4326[0]],  # SW corner (lat, lon)
            [bounds_4326[3], bounds_4326[2]]   # NE corner (lat, lon)
        ]

        return png_base64, bounds_folium


def detect_raster_type(raster_path: Path) -> Tuple[bool, Dict]:
    """
    Detecta si un raster es discreto (clases 1-5) o continuo (valores FS).

    Args:
        raster_path: Ruta al archivo .tif

    Returns:
        tuple: (is_discrete, metadata)
            is_discrete: True si valores estan en {0,1,2,3,4,5}
            metadata: Dict con info adicional
    """
    with rasterio.open(raster_path) as src:
        data = src.read(1)

        # Excluir nodata (asumimos 0 o nan)
        valid_mask = (data != 0) & ~np.isnan(data)
        valid_data = data[valid_mask]

        if len(valid_data) == 0:
            return True, {'message': 'Raster vacio', 'unique_values': []}

        unique_vals = np.unique(valid_data)

        # Verificar si todos los valores estan en el set de discretos validos
        is_discrete = all(
            v in VALORES_DISCRETOS_VALIDOS or (isinstance(v, float) and v.is_integer() and int(v) in VALORES_DISCRETOS_VALIDOS)
            for v in unique_vals
        )

        metadata = {
            'unique_values': unique_vals.tolist()[:20],  # Limitar para display
            'n_unique': len(unique_vals),
            'min': float(np.nanmin(valid_data)),
            'max': float(np.nanmax(valid_data)),
            'dtype': str(data.dtype),
            'shape': data.shape,
            'crs': str(src.crs)
        }

        return is_discrete, metadata


def raster_to_folium_overlay(
    raster_path: Path,
    colormap: Dict[int, Tuple[int, int, int, int]] = COLORES_RGBA,
    auto_detect: bool = True
) -> Dict:
    """
    Crea overlay completo para Folium.ImageOverlay.

    Args:
        raster_path: Ruta al archivo .tif
        colormap: Dict {clase: (R,G,B,A)}
        auto_detect: Si True, detecta automaticamente si reclasificar

    Returns:
        dict: {
            'image': data_url (data:image/png;base64,...),
            'bounds': [[south, west], [north, east]],
            'is_discrete': bool,
            'metadata': dict con info del raster
        }
    """
    # Detectar tipo de raster
    is_discrete, metadata = detect_raster_type(raster_path)

    if auto_detect and not is_discrete:
        metadata['reclassified'] = True
        metadata['message'] = 'Raster continuo detectado. Reclasificando con umbrales de config.py'
    else:
        metadata['reclassified'] = False

    # Generar PNG
    png_b64, bounds = raster_to_png_base64(
        raster_path,
        colormap=colormap,
        is_discrete=is_discrete if auto_detect else True
    )

    return {
        'image': f'data:image/png;base64,{png_b64}',
        'bounds': bounds,
        'is_discrete': is_discrete,
        'metadata': metadata
    }
