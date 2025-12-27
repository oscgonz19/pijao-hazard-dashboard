"""
Configuracion global para el Dashboard de Amenaza Geotecnica
FUENTE UNICA DE VERDAD para umbrales, colores y parametros

NOTA SOBRE INCONSISTENCIA DE UMBRALES:
En mapa_amenaza_pijao.py existen DOS definiciones diferentes:

1) ensure_haz_num() [lineas 90-96]:
   FS >= 1.50 -> 1 (MUY BAJA)
   FS >= 1.30 -> 2 (BAJA)
   FS >= 1.10 -> 3 (MEDIA)
   FS >= 1.00 -> 4 (ALTA)
   FS <  1.00 -> 5 (MUY ALTA)

2) UMBRALES_FS [lineas 119-122]:
   bins = [0, 1.0, 1.2, 1.5, 2.0, inf]
   clases = [5, 4, 3, 2, 1]

Este archivo usa la version 2 (UMBRALES_FS) por defecto.
Si se requiere usar la version 1, ajustar UMBRALES_AMENAZA manualmente.
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

# ==============================================================================
# RUTAS BASE
# ==============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# ==============================================================================
# UMBRALES DE CLASIFICACION DE AMENAZA
# ==============================================================================
# Matriz por defecto (basada en UMBRALES_FS de mapa_amenaza_pijao.py)
# NO se asume como "estandar INVIAS" - ajustar segun normativa aplicable

UMBRALES_AMENAZA = {
    'version': 'matriz_proyecto_v1',
    'descripcion': 'Umbrales basados en UMBRALES_FS de mapa_amenaza_pijao.py',
    'bins': np.array([0.0, 1.0, 1.2, 1.5, 2.0, np.inf]),
    'clases': [5, 4, 3, 2, 1],  # Orden: MUY ALTA, ALTA, MEDIA, BAJA, MUY BAJA
    'labels': {
        5: 'MUY ALTA (FS < 1.0)',
        4: 'ALTA (1.0 <= FS < 1.2)',
        3: 'MEDIA (1.2 <= FS < 1.5)',
        2: 'BAJA (1.5 <= FS < 2.0)',
        1: 'MUY BAJA (FS >= 2.0)'
    },
    'labels_cortos': {
        5: 'MUY ALTA',
        4: 'ALTA',
        3: 'MEDIA',
        2: 'BAJA',
        1: 'MUY BAJA'
    }
}

# ==============================================================================
# COLORES SGC (Servicio Geologico Colombiano)
# ==============================================================================
COLORES_SGC = {
    1: '#1a9641',  # Verde oscuro - Muy Baja
    2: '#a6d96a',  # Verde claro - Baja
    3: '#ffffbf',  # Amarillo - Media
    4: '#fdae61',  # Naranja - Alta
    5: '#d7191c'   # Rojo - Muy Alta
}

# Version RGBA para PNG overlay (alpha=180 de 255 ~ 70% opacidad)
COLORES_RGBA = {
    1: (26, 150, 65, 180),    # Verde oscuro
    2: (166, 217, 106, 180),  # Verde claro
    3: (255, 255, 191, 180),  # Amarillo
    4: (253, 174, 97, 180),   # Naranja
    5: (215, 25, 28, 180)     # Rojo
}

# ==============================================================================
# CONFIGURACION DEL MAPA
# ==============================================================================
MAPA_CONFIG = {
    'zoom_default': 14,
    'opacity_raster': 0.7,
    'opacity_voronoi': 0.5,
    'corredor_color': '#2c3e50',
    'corredor_weight': 4,
    'punto_radius': 8,
    'punto_weight': 2
}

# ==============================================================================
# NOMBRES DE ARCHIVOS ESPERADOS POR REGION
# ==============================================================================
ARCHIVOS_REGION = {
    'raster': 'raster_amenaza.tif',
    'corredor': 'corredor.gpkg',
    'puntos': 'puntos.gpkg',
    'voronoi': 'voronoi.gpkg'
}

# ==============================================================================
# DETECCION DE RASTER DISCRETO
# ==============================================================================
VALORES_DISCRETOS_VALIDOS = {0, 1, 2, 3, 4, 5}


# ==============================================================================
# FUNCIONES DE UTILIDAD
# ==============================================================================

def get_regiones_disponibles() -> List[str]:
    """
    Detecta regiones disponibles buscando subdirectorios en DATA_DIR
    que contengan al menos el archivo de puntos.
    """
    regiones = []
    if not DATA_DIR.exists():
        return regiones

    for subdir in DATA_DIR.iterdir():
        if subdir.is_dir():
            # Verificar que exista al menos el archivo de puntos
            puntos_file = subdir / ARCHIVOS_REGION['puntos']
            if puntos_file.exists():
                regiones.append(subdir.name)

    return sorted(regiones)


def get_archivos_region(region: str) -> Dict[str, Optional[Path]]:
    """
    Retorna paths a los archivos de una region.
    Retorna None para archivos que no existen.
    """
    region_dir = DATA_DIR / region
    archivos = {}

    for key, filename in ARCHIVOS_REGION.items():
        filepath = region_dir / filename
        archivos[key] = filepath if filepath.exists() else None

    return archivos


def clasificar_fs(fs_value: float) -> int:
    """
    Clasifica un valor de Factor de Seguridad (FS) en clase de amenaza (1-5).
    Usa los umbrales definidos en UMBRALES_AMENAZA.
    """
    if np.isnan(fs_value):
        return 0  # nodata

    bins = UMBRALES_AMENAZA['bins']
    clases = UMBRALES_AMENAZA['clases']

    # np.digitize retorna indice del bin (1-based)
    idx = np.digitize(fs_value, bins, right=False) - 1
    idx = max(0, min(idx, len(clases) - 1))

    return clases[idx]


def clasificar_fs_array(fs_array: np.ndarray) -> np.ndarray:
    """
    Clasifica un array de valores FS a clases de amenaza.
    Preserva nodata (0 o nan).
    """
    bins = UMBRALES_AMENAZA['bins']
    clases = UMBRALES_AMENAZA['clases']

    # Crear array de salida
    result = np.zeros_like(fs_array, dtype=np.uint8)

    # Mascara de valores validos (no 0 y no nan)
    valid_mask = (fs_array != 0) & ~np.isnan(fs_array)

    if not np.any(valid_mask):
        return result

    # Clasificar valores validos
    indices = np.digitize(fs_array[valid_mask], bins, right=False) - 1
    indices = np.clip(indices, 0, len(clases) - 1)

    # Mapear indices a clases
    clases_array = np.array(clases)
    result[valid_mask] = clases_array[indices]

    return result
