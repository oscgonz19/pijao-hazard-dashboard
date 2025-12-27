"""
Pagina 3: Metodologia - Explicacion tecnica
Dashboard de Amenaza Geotecnica - Corredor Vial Pijao
"""

import streamlit as st
import sys
from pathlib import Path

# Agregar directorio padre al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import UMBRALES_AMENAZA, COLORES_SGC

st.set_page_config(page_title="Metodologia", page_icon="📚", layout="wide")

st.title("Metodologia Tecnica")
st.markdown("**Analisis de Amenaza por Movimientos en Masa - INVIAS/SGC**")

st.divider()

# Seccion 1: Umbrales INVIAS
st.header("1. Umbrales de Clasificacion INVIAS")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    La clasificacion de amenaza se basa en el **Factor de Seguridad (FS)**,
    calculado mediante el metodo del **talud infinito**:

    $$
    FS = \\frac{c' + (\\gamma z \\cos^2\\beta - u) \\tan\\phi'}{\\gamma z \\sin\\beta \\cos\\beta}
    $$

    Donde:
    - $c'$ = cohesion efectiva
    - $\\phi'$ = angulo de friccion interna
    - $\\gamma$ = peso unitario del suelo
    - $z$ = profundidad del plano de falla
    - $\\beta$ = angulo del talud
    - $u$ = presion de poros
    """)

with col2:
    st.markdown("**Clasificacion:**")

    # Mostrar tabla con colores
    for haz_num in [5, 4, 3, 2, 1]:
        color = COLORES_SGC[haz_num]
        label = UMBRALES_AMENAZA['labels'][haz_num]
        st.markdown(
            f'<div style="background-color:{color}; padding: 8px 12px; '
            f'color: {"white" if haz_num >= 4 else "black"}; border-radius: 4px; '
            f'margin-bottom: 4px; font-weight: bold;">'
            f'{haz_num} - {label}</div>',
            unsafe_allow_html=True
        )

    st.markdown("""
    **Umbral critico**: FS < 1.0
    *(Talud inestable, intervencion urgente)*
    """)

st.divider()

# Seccion 2: Pipeline de Analisis
st.header("2. Pipeline de Analisis")

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Calculo FS",
    "2. Interpolacion",
    "3. Zonificacion",
    "4. Outputs"
])

with tab1:
    st.subheader("Calculo de Factor de Seguridad")
    st.markdown("""
    **Paso 1**: Analisis de estabilidad de taludes

    Para cada punto critico se calculan multiples escenarios de FS:
    - `FS_1`: Escenario seco (sin agua)
    - `FS_2`: Nivel freatico a 0.5 m
    - `FS_3`: Nivel freatico a 1.0 m
    - `FS_4`: Nivel freatico a 1.5 m
    - ... (N escenarios)

    **Paso 2**: Calculo de FS_min

    $$
    FS_{min} = \\min(FS_1, FS_2, ..., FS_N)
    $$

    El `FS_min` representa el **escenario mas desfavorable** (worst-case).

    **Paso 3**: Clasificacion inicial

    Se aplica la tabla INVIAS para asignar nivel de amenaza (1-5).
    """)

with tab2:
    st.subheader("Interpolacion Espacial IDW")
    st.markdown("""
    **Metodo**: Inverse Distance Weighting (IDW)

    **Filosofia clave** (diferenciador tecnico):

    **CORRECTO** (lo que hace este motor):
    1. Interpolar **valores continuos de FS_min**
    2. Reclasificar el raster continuo a categorias de amenaza

    **INCORRECTO** (comun en scripts basicos):
    1. Interpolar directamente niveles de amenaza (1-5)
    → Genera artefactos, no es defendible

    ---

    **Formula IDW**:

    $$
    FS(x,y) = \\frac{\\sum_{i=1}^{n} w_i \\cdot FS_i}{\\sum_{i=1}^{n} w_i}
    $$

    $$
    w_i = \\frac{1}{d_i^p}
    $$

    Donde:
    - $FS_i$ = Factor de Seguridad del punto $i$
    - $d_i$ = distancia al punto $i$
    - $p$ = exponente (tipicamente 2)
    - $n$ = numero de vecinos (k=10)

    **Parametros**:
    - Resolucion: 5 m/pixel
    - Buffer: 100 m alrededor del corredor
    - Potencia: p=2
    """)

with tab3:
    st.subheader("Zonificacion Voronoi")
    st.markdown("""
    **Poligonos de Voronoi** (Thiessen polygons):

    Cada punto critico genera una celda donde todos los puntos dentro
    estan mas cerca de ese punto que de cualquier otro.

    **Implementacion robusta**:

    Para evitar celdas infinitas en los bordes, se usan **phantom points**
    (puntos fantasma) en las esquinas del bounding box. Estos se descartan
    despues del clipping.

    ```python
    # Phantom points para cerrar Voronoi
    bbox_pts = np.array([
        [xmin - pad, ymin - pad],
        [xmin - pad, ymax + pad],
        [xmax + pad, ymin - pad],
        [xmax + pad, ymax + pad]
    ])
    all_pts = np.vstack([coords_reales, bbox_pts])
    vor = Voronoi(all_pts)  # Voronoi cerrado
    ```

    **Ventaja**: Zonificacion discreta, util para delimitacion administrativa.

    **Desventaja**: Transiciones bruscas en bordes de celdas.
    """)

with tab4:
    st.subheader("Generacion de Outputs")
    st.markdown("""
    **Outputs por corredor**:

    1. **Raster GeoTIFF** (`raster_amenaza_pijao.tif`)
       - Valores: 1-5 (niveles de amenaza)
       - Resolucion: 5 m/pixel
       - CRS: EPSG:9377 (MAGNA-SIRGAS Colombia)
       - Formato: GeoTIFF con compresion DEFLATE

    2. **Poligonos Voronoi** (`voronoi_amenaza_pijao.gpkg`)
       - Formato: GeoPackage (OGC estandar)
       - Atributos: `haz_num`, `FS_min`, `punto_id`

    3. **Mapa PNG** (`mapa_amenaza_pijao.png`)
       - Resolucion: 300 DPI (alta calidad)
       - Visualizacion lado a lado: Voronoi + IDW

    4. **Informe tecnico** (`informe_tecnico_amenaza_pijao.txt`)
       - Resumen ejecutivo
       - Puntos criticos (FS<1.0)
       - Distribucion de amenaza
       - Recomendaciones
    """)

st.divider()

# Seccion 3: Limitaciones y QA
st.header("3. Limitaciones y Control de Calidad")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Limitaciones")
    st.markdown("""
    **Interpolacion espacial**:
    - IDW asume isotropia (mismas propiedades en todas direcciones)
    - No considera barreras geologicas o estructurales
    - Precision limitada por densidad de puntos

    **Talud infinito**:
    - Asume plano de falla paralelo al talud
    - No modela fallas circulares o complejas
    - Valido para taludes con L/H > 10

    **Datos de entrada**:
    - Parametros geotecnicos puntuales (no distribuciones espaciales)
    - Nivel freatico estimado, no medido continuamente
    - No considera variabilidad temporal (lluvias)

    **Zonificacion**:
    - Voronoi sensible a ubicacion de puntos
    - IDW suaviza extremos (puede subestimar picos)
    """)

with col2:
    st.subheader("Control de Calidad")
    st.markdown("""
    **Validaciones implementadas**:

    1. **Robustez de datos**:
       - Auto-deteccion y reproyeccion de CRS
       - Manejo de geometrias no-Point (centroides)
       - Derivacion de campos faltantes (FS_min, haz_num)

    2. **Verificaciones geometricas**:
       - Puntos dentro del buffer del corredor
       - Voronoi clipped correctamente
       - Raster mask aplicada al area de interes

    3. **Validacion de outputs**:
       - Valores de amenaza en rango [1-5]
       - No-data manejado correctamente (0)
       - CRS consistente en todos los outputs

    4. **Trazabilidad**:
       - Outputs con nombre de region
       - Parametros registrados en metadatos
       - Reproducibilidad garantizada
    """)

st.divider()

# Seccion 4: Amenaza vs Riesgo
st.header("4. Amenaza vs Riesgo")

st.warning("""
**Distincion importante:**

Este sistema genera mapas de **AMENAZA** (hazard), no de **RIESGO** (risk).
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Amenaza (H)**:
    - Probabilidad de ocurrencia de un fenomeno
    - Basada en condiciones geotecnicas
    - Lo que calcula este motor

    **Formula de Riesgo**:
    $$
    R = H \\times V \\times E
    $$
    """)

with col2:
    st.markdown("""
    **Componentes adicionales para Riesgo**:
    - **Vulnerabilidad (V)**: Fragilidad de elementos expuestos
    - **Exposicion (E)**: Infraestructura/poblacion en el area

    Los mapas de amenaza son **insumos** para el analisis de riesgo posterior.
    """)

st.divider()

# Seccion 5: Referencias
st.header("5. Referencias Tecnicas")

st.markdown("""
**Normas y estandares**:

1. **INVIAS** (2016). *Manual de diseno geometrico de carreteras*.
   Instituto Nacional de Vias, Colombia.

2. **SGC** (2017). *Guia metodologica para zonificacion de amenaza por movimientos en masa*.
   Servicio Geologico Colombiano.

3. **Duncan, J.M. & Wright, S.G.** (2005). *Soil Strength and Slope Stability*.
   John Wiley & Sons.

4. **Varnes, D.J.** (1984). *Landslide Hazard Zonation: A Review of Principles and Practice*.
   UNESCO Natural Hazards Series.

**Metodologia de interpolacion**:

5. **Shepard, D.** (1968). *A two-dimensional interpolation function for irregularly-spaced data*.
   Proceedings of the 1968 23rd ACM national conference.

6. **Watson, D.F.** (1992). *Contouring: A Guide to the Analysis and Display of Spatial Data*.
   Pergamon Press.

**Sistema de coordenadas**:

- **EPSG:9377**: MAGNA-SIRGAS / Colombia Origen Unico
- Proyeccion: Transverse Mercator
- Datum: SIRGAS 2000
""")

st.divider()

# Footer
st.info("""
**Sobre esta metodologia**

Este motor implementa las mejores practicas de analisis geotecnico combinadas
con procesamiento geoespacial moderno. Los outputs cumplen con requisitos INVIAS/SGC
para proyectos de infraestructura vial.

Para preguntas tecnicas o validaciones especificas, consultar la documentacion
completa en el repositorio.
""")

st.caption("v0.1.0 - Pijao Landslide Hazard Engine | Metodologia INVIAS/SGC")
