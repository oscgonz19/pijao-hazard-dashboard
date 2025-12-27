"""
Funciones de estilo para capas de Folium
"""

import folium
from pathlib import Path
from typing import Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import COLORES_SGC, MAPA_CONFIG, UMBRALES_AMENAZA


def style_punto(row: Dict[str, Any], colormap: Dict[int, str] = COLORES_SGC) -> Dict:
    """
    Estilo para marcadores de puntos criticos (CircleMarker).

    Args:
        row: Fila de GeoDataFrame con columnas FS_min, haz_num, ID
        colormap: Dict {haz_num: color_hex}

    Returns:
        dict: Configuracion para folium.CircleMarker
    """
    haz_num = row.get('haz_num', 1)
    if haz_num is None or (isinstance(haz_num, float) and haz_num != haz_num):
        haz_num = 1

    return {
        'radius': MAPA_CONFIG['punto_radius'],
        'fill_color': colormap.get(int(haz_num), '#808080'),
        'color': 'black',
        'weight': MAPA_CONFIG['punto_weight'],
        'fill_opacity': 0.85
    }


def style_voronoi(feature: Dict) -> Dict:
    """
    Estilo para poligonos de Voronoi (GeoJSON style_function).

    Args:
        feature: Feature de GeoJSON con properties.haz_num

    Returns:
        dict: Configuracion de estilo
    """
    haz_num = feature.get('properties', {}).get('haz_num', 1)
    if haz_num is None:
        haz_num = 1

    return {
        'fillColor': COLORES_SGC.get(int(haz_num), '#808080'),
        'color': 'black',
        'weight': 1,
        'fillOpacity': MAPA_CONFIG['opacity_voronoi']
    }


def style_corredor(feature: Dict) -> Dict:
    """
    Estilo para el corredor vial (GeoJSON style_function).

    Args:
        feature: Feature de GeoJSON

    Returns:
        dict: Configuracion de estilo
    """
    return {
        'color': MAPA_CONFIG['corredor_color'],
        'weight': MAPA_CONFIG['corredor_weight'],
        'fillOpacity': 0
    }


def create_popup_html(row: Dict[str, Any]) -> str:
    """
    Crea contenido HTML para popup de punto critico.
    Muestra FS_min, haz_num, y el umbral aplicado.

    Args:
        row: Dict con datos del punto

    Returns:
        str: HTML para folium.Popup
    """
    fs_min = row.get('FS_min', None)
    haz_num = row.get('haz_num', None)
    punto_id = row.get('ID', 'N/A')

    # Formatear FS_min
    if fs_min is not None and not (isinstance(fs_min, float) and fs_min != fs_min):
        fs_display = f"{fs_min:.3f}"
    else:
        fs_display = "N/A"

    # Obtener label de amenaza
    if haz_num is not None and not (isinstance(haz_num, float) and haz_num != haz_num):
        haz_num = int(haz_num)
        umbral_label = UMBRALES_AMENAZA['labels'].get(haz_num, 'N/A')
        haz_label = UMBRALES_AMENAZA['labels_cortos'].get(haz_num, 'N/A')
        color = COLORES_SGC.get(haz_num, '#808080')
    else:
        umbral_label = "N/A"
        haz_label = "N/A"
        haz_num = "N/A"
        color = '#808080'

    html = f"""
    <div style='font-family: Arial, sans-serif; font-size: 12px; min-width: 200px;'>
        <div style='background-color: {color}; color: {'white' if haz_num in [4, 5] else 'black'};
                    padding: 8px; margin: -10px -10px 10px -10px; font-weight: bold;'>
            Punto ID: {punto_id}
        </div>
        <table style='width: 100%; border-collapse: collapse;'>
            <tr>
                <td style='padding: 4px; font-weight: bold;'>FS minimo:</td>
                <td style='padding: 4px;'>{fs_display}</td>
            </tr>
            <tr>
                <td style='padding: 4px; font-weight: bold;'>Clase amenaza:</td>
                <td style='padding: 4px;'>{haz_num} ({haz_label})</td>
            </tr>
        </table>
        <hr style='margin: 8px 0; border: none; border-top: 1px solid #ccc;'>
        <div style='font-size: 11px; color: #666;'>
            <b>Umbral aplicado:</b><br>
            {umbral_label}
        </div>
    </div>
    """
    return html


def create_legend_html() -> str:
    """
    Crea leyenda HTML para el mapa.

    Returns:
        str: HTML de la leyenda
    """
    items = []
    for haz_num in [1, 2, 3, 4, 5]:
        color = COLORES_SGC[haz_num]
        label = UMBRALES_AMENAZA['labels_cortos'][haz_num]
        items.append(
            f'<div style="display: flex; align-items: center; margin: 2px 0;">'
            f'<div style="width: 20px; height: 20px; background-color: {color}; '
            f'border: 1px solid black; margin-right: 8px;"></div>'
            f'<span style="color: black;">{haz_num} - {label}</span></div>'
        )

    html = f"""
    <div style='
        position: fixed;
        bottom: 50px;
        left: 10px;
        background-color: white;
        padding: 10px;
        border: 2px solid gray;
        border-radius: 5px;
        z-index: 9999;
        font-size: 12px;
        font-family: Arial, sans-serif;
        color: black;
    '>
        <b style="color: black;">Amenaza</b>
        <hr style='margin: 5px 0; border-color: gray;'>
        {''.join(items)}
    </div>
    """
    return html
