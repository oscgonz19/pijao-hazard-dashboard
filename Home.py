"""
Pijao Landslide Hazard Dashboard
Home page - Overview del proyecto
"""

import streamlit as st
from pathlib import Path

from config import UMBRALES_AMENAZA, COLORES_SGC, get_regiones_disponibles

# Configuración de la página
st.set_page_config(
    page_title="Pijao Hazard Dashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🗺️ Pijao Landslide Hazard Dashboard")
st.markdown("**Motor de análisis de amenaza por movimientos en masa**")
st.markdown("Metodología: INVÍAS / SGC (Servicio Geológico Colombiano)")

st.divider()

# Descripción del proyecto
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Sobre el Proyecto")
    st.markdown("""
    Sistema de análisis geotécnico para corredores viales en Pijao, Quindío.

    **Metodología**:
    1. Análisis de estabilidad de taludes (método del talud infinito)
    2. Cálculo de Factor de Seguridad (FS) para múltiples escenarios
    3. Clasificación de amenaza según umbrales INVÍAS
    4. Interpolación espacial IDW sobre FS continuo
    5. Zonificación mediante polígonos de Voronoi

    **Outputs generados**:
    - Mapas de amenaza (Voronoi + IDW)
    - Rasters GeoTIFF para SIG
    - Informes técnicos para interventoría
    - Polígonos de zonificación (GeoPackage)
    """)

with col2:
    st.header("Clasificación INVÍAS")
    st.markdown("""
    | FS Range | Amenaza |
    |----------|---------|
    | FS ≤ 1.0 | 🔴 MUY ALTA |
    | 1.0-1.2 | 🟠 ALTA |
    | 1.2-1.5 | 🟡 MEDIA |
    | 1.5-2.0 | 🟢 BAJA |
    | FS > 2.0 | 🟢 MUY BAJA |

    **Umbral crítico**: FS < 1.0
    (Requiere intervención inmediata)
    """)

st.divider()

# Instrucciones de uso
st.header("📋 Cómo usar este dashboard")

tab1, tab2, tab3 = st.tabs(["Estadísticas", "Mapa Interactivo", "Metodología"])

with tab1:
    st.markdown("""
    **Página: Estadísticas**
    - Selecciona una región del sidebar
    - Visualiza KPIs: puntos totales, críticos (FS<1), distribución de amenaza
    - Tabla de puntos críticos ordenados por severidad
    - Estadísticas de Factor de Seguridad
    """)

with tab2:
    st.markdown("""
    **Página: Mapa Interactivo**
    - Visualiza capas: Raster IDW, Voronoi, Corredor, Puntos
    - Cambia entre mapas base (OpenStreetMap, Satélite, CartoDB)
    - Filtra por nivel de amenaza
    - Haz clic en puntos para ver detalles
    """)

with tab3:
    st.markdown("""
    **Página: Metodología**
    - Umbrales INVÍAS detallados
    - Explicación de interpolación continua
    - Limitaciones y consideraciones
    - Referencias técnicas
    """)

st.divider()

# Footer con información técnica
st.info("""
**ℹ️ Sobre los datos**

Este dashboard consume outputs pre-generados por el motor de cálculo offline.
Los cálculos pesados (interpolación, Voronoi, rasters) se ejecutan mediante el script principal,
garantizando reproducibilidad y trazabilidad.

Para generar nuevos análisis:
```bash
python3 mapa_amenaza_pijao.py
```
""")

# Sidebar con configuración
st.sidebar.header("Configuración")

# Estado de datos
regiones = get_regiones_disponibles()

if regiones:
    st.sidebar.success(f"✓ {len(regiones)} región(es) disponible(s)")
    for region in regiones:
        st.sidebar.markdown(f"  • {region}")
else:
    st.sidebar.warning("⚠️ No hay datos en data/")

# Info del sistema
st.sidebar.divider()
st.sidebar.markdown("### Sistema")
st.sidebar.caption("v0.1.0 - Pijao Hazard Engine")
st.sidebar.caption("INVÍAS / SGC Standards")

# Leyenda de colores
st.sidebar.divider()
st.sidebar.markdown("### Leyenda de Amenaza")

for haz_num in [5, 4, 3, 2, 1]:
    color = COLORES_SGC[haz_num]
    label = UMBRALES_AMENAZA['labels_cortos'][haz_num]
    st.sidebar.markdown(
        f'<span style="background-color:{color}; padding: 2px 10px; '
        f'color: {"white" if haz_num >= 4 else "black"}; border-radius: 3px; '
        f'display: inline-block; width: 100px; text-align: center;">'
        f'{label}</span>',
        unsafe_allow_html=True
    )

# Enlaces
st.sidebar.divider()
st.sidebar.markdown("### Enlaces")
st.sidebar.markdown("[📖 Documentación](../CLAUDE.md)")
st.sidebar.markdown("[💻 Repositorio](#)")
st.sidebar.markdown("[📧 Contacto](#)")
