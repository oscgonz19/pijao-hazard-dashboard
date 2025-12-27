"""
Pagina 1: Estadisticas - KPIs y metricas por region
Dashboard de Amenaza Geotecnica - Corredor Vial Pijao
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Agregar directorio padre al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    UMBRALES_AMENAZA, COLORES_SGC,
    get_regiones_disponibles, get_archivos_region
)
from utils.data_loader import load_gpkg, prepare_puntos, get_estadisticas_puntos

st.set_page_config(page_title="Estadisticas", page_icon="📊", layout="wide")

st.title("Estadisticas - Analisis por Region")

# Detectar regiones disponibles
regiones = get_regiones_disponibles()

if not regiones:
    st.error("No se encontraron regiones en data/")
    st.info("""
    **Estructura esperada**:
    ```
    data/
      pijao/
        puntos.gpkg
        corredor.gpkg
        voronoi.gpkg
        raster_amenaza.tif
    ```
    """)
    st.stop()

# Selector de region
region_seleccionada = st.selectbox(
    "Selecciona una region",
    regiones,
    help="Regiones con datos disponibles"
)

st.divider()

# Cargar datos
archivos = get_archivos_region(region_seleccionada)

if not archivos['puntos']:
    st.error(f"No se encontro archivo de puntos para {region_seleccionada}")
    st.stop()

# Cargar y preparar puntos
puntos = load_gpkg(archivos['puntos'])
puntos = prepare_puntos(puntos)
stats = get_estadisticas_puntos(puntos)

# KPIs principales
st.header(f"{region_seleccionada.upper()}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_puntos = len(puntos)
    st.metric(
        label="Total Puntos",
        value=total_puntos,
        help="Puntos criticos analizados en la region"
    )

with col2:
    # Puntos criticos (FS < 1.0 o haz_num == 5)
    criticos = len(puntos[puntos['haz_num'] >= 5]) if 'haz_num' in puntos.columns else 0
    if 'FS_min' in puntos.columns:
        criticos = len(puntos[puntos['FS_min'] < 1.0])

    delta_color = "inverse" if criticos > 0 else "normal"
    st.metric(
        label="Criticos (FS<1.0)",
        value=criticos,
        delta="Requiere intervencion" if criticos > 0 else "Estable",
        delta_color=delta_color,
        help="Puntos con Factor de Seguridad < 1.0"
    )

with col3:
    # Porcentaje alta/muy alta
    if 'haz_num' in puntos.columns:
        alta_muy_alta = len(puntos[puntos['haz_num'] >= 4])
        pct_alta = (alta_muy_alta / total_puntos * 100) if total_puntos > 0 else 0
    else:
        pct_alta = 0
    st.metric(
        label="% Alta/Muy Alta",
        value=f"{pct_alta:.1f}%",
        help="Porcentaje de puntos con amenaza alta o muy alta"
    )

with col4:
    # Nivel predominante
    if 'haz_num' in puntos.columns:
        nivel_predominante = int(puntos['haz_num'].mode().iloc[0]) if not puntos['haz_num'].mode().empty else 3
        label = UMBRALES_AMENAZA['labels_cortos'].get(nivel_predominante, 'N/A')
        color = COLORES_SGC.get(nivel_predominante, '#808080')
        st.markdown(f"""
        **Nivel Predominante**

        <span style="background-color: {color}; padding: 5px 10px; border-radius: 5px;
        color: {'white' if nivel_predominante >= 4 else 'black'}; font-weight: bold;">
        {label}
        </span>
        """, unsafe_allow_html=True)
    else:
        st.metric("Nivel Predominante", "N/A")

st.divider()

# Distribucion de amenaza
st.subheader("Distribucion de Niveles de Amenaza")

if 'haz_num' in puntos.columns:
    col1, col2 = st.columns([2, 1])

    # Calcular distribucion
    amenaza_counts = puntos['haz_num'].value_counts().sort_index()

    with col1:
        # Mostrar barras de progreso
        for nivel in [5, 4, 3, 2, 1]:
            count = amenaza_counts.get(nivel, 0)
            pct = (count / total_puntos * 100) if total_puntos > 0 else 0
            label = UMBRALES_AMENAZA['labels_cortos'].get(nivel, 'N/A')
            color = COLORES_SGC.get(nivel, '#808080')

            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div style="font-weight: bold; margin-bottom: 3px;">
                    {nivel} - {label}: {count} puntos ({pct:.1f}%)
                </div>
                <div style="background-color: #f0f0f0; border-radius: 5px; overflow: hidden;">
                    <div style="background-color: {color}; width: {max(pct, 2)}%; height: 25px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("**Resumen por nivel**")
        for nivel in [5, 4, 3, 2, 1]:
            count = amenaza_counts.get(nivel, 0)
            label = UMBRALES_AMENAZA['labels_cortos'].get(nivel, 'N/A')
            color = COLORES_SGC.get(nivel, '#808080')
            st.markdown(f"""
            <span style="background-color: {color}; padding: 2px 8px; border-radius: 3px;
            color: {'white' if nivel >= 4 else 'black'}; font-size: 12px;">
            {nivel}
            </span> {label}: **{count}**
            """, unsafe_allow_html=True)
else:
    st.info("No hay datos de clasificacion de amenaza disponibles")

st.divider()

# Puntos criticos
st.subheader("Puntos Criticos (FS < 1.0)")

if 'FS_min' in puntos.columns:
    criticos_df = puntos[puntos['FS_min'] < 1.0].copy()

    if len(criticos_df) > 0:
        st.error(f"**{len(criticos_df)} puntos requieren intervencion inmediata**")

        # Ordenar por FS_min
        criticos_df = criticos_df.sort_values('FS_min', ascending=True)

        # Preparar tabla
        cols_display = ['ID', 'FS_min', 'haz_num']
        cols_disponibles = [c for c in cols_display if c in criticos_df.columns]

        tabla = criticos_df[cols_disponibles].copy().reset_index(drop=True)
        if 'FS_min' in tabla.columns:
            tabla['FS_min'] = tabla['FS_min'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "N/A")

        st.dataframe(
            tabla,
            hide_index=True,
            column_config={
                'ID': st.column_config.TextColumn('ID Punto'),
                'FS_min': st.column_config.TextColumn('Factor de Seguridad'),
                'haz_num': st.column_config.NumberColumn('Nivel Amenaza')
            }
        )

        st.markdown("""
        **Recomendaciones para puntos criticos**:
        - Obras de drenaje y subdrenaje
        - Muros de contencion o anclajes
        - Reconformacion de taludes
        - Monitoreo instrumental continuo
        """)
    else:
        st.success("No hay puntos criticos (todos los FS >= 1.0)")
else:
    st.info("No hay datos de Factor de Seguridad disponibles")

st.divider()

# Estadisticas de FS
if 'FS_min' in puntos.columns:
    st.subheader("Estadisticas de Factor de Seguridad")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("FS Minimo", f"{puntos['FS_min'].min():.3f}")
    with col2:
        st.metric("FS Maximo", f"{puntos['FS_min'].max():.3f}")
    with col3:
        st.metric("FS Promedio", f"{puntos['FS_min'].mean():.3f}")
    with col4:
        st.metric("FS Mediana", f"{puntos['FS_min'].median():.3f}")

st.divider()

# Archivos disponibles
st.subheader("Archivos Disponibles")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if archivos['puntos']:
        st.success("Puntos")
    else:
        st.error("Puntos")

with col2:
    if archivos['corredor']:
        st.success("Corredor")
    else:
        st.warning("Corredor")

with col3:
    if archivos['voronoi']:
        st.success("Voronoi")
    else:
        st.warning("Voronoi")

with col4:
    if archivos['raster']:
        st.success("Raster")
    else:
        st.warning("Raster")

# Footer
st.divider()
st.caption(f"Region: **{region_seleccionada}** | Umbrales: {UMBRALES_AMENAZA['version']}")
