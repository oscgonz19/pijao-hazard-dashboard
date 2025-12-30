*[Read in English](README.md)*

# Evaluación de Amenaza Geotécnica en Vías de Montaña
## Corredor Andino, Colombia

**Geociencias aplicadas + evaluación de riesgo para infraestructura vial de montaña**
*Datos anonimizados — presentación de metodología y enfoque*

<img width="1895" alt="Vista General del Dashboard" src="https://github.com/user-attachments/assets/13a7c604-297f-440d-9614-47e975ae2367" />

---

## Contexto

Los corredores viales de montaña en los Andes colombianos enfrentan desafíos persistentes por fenómenos de remoción en masa. Pendientes pronunciadas que superan el 50%, suelos volcánicos altamente meteorizados y precipitaciones anuales superiores a 2,500 mm crean condiciones donde deslizamientos, erosión y fallas de taludes interrumpen regularmente la conectividad rural crítica.

Este proyecto abordó la evaluación de amenaza geotécnica para un corredor vial estratégico que sirve a comunidades montañosas aisladas. La vía representa la única ruta de acceso para la producción agrícola y servicios esenciales, haciendo de su estabilidad un asunto tanto de viabilidad económica como de seguridad pública.

El estudio integró análisis geológicos, hidrogeológicos y geotécnicos para identificar puntos críticos que requieren intervención, clasificar niveles de amenaza a lo largo del corredor y proporcionar recomendaciones de ingeniería para estabilización de taludes y diseño de drenajes. El trabajo siguió estándares técnicos colombianos (Manual de Estabilidad de Taludes INVÍAS, Guía Metodológica SGC para Estudios de Amenaza) y produjo resultados accionables para la toma de decisiones en infraestructura.

---

## Mi Rol

- Realicé **evaluación geológica e hidrogeológica** para un corredor vial de montaña, caracterizando unidades litológicas, rasgos estructurales y condiciones de aguas subterráneas
- Ejecuté **análisis satelital multitemporal** (Landsat 5/7/8, Sentinel-2) para rastrear dinámicas de vegetación e identificar cambios del terreno durante más de 30 años
- Construí un **marco de clasificación de amenaza** basado en cálculos de Factor de Seguridad (FS), integrando parámetros geotécnicos con análisis espacial
- Desarrollé **herramientas de evaluación de riesgo basadas en SIG** incluyendo interpolación IDW, teselación de Voronoi y pipelines automatizados de procesamiento raster
- Creé un **dashboard de visualización interactivo** para comunicación con stakeholders y soporte de decisiones técnicas
- Produje **informes técnicos** sintetizando observaciones de campo, análisis de teledetección y modelación geotécnica para supervisión de interventoría

---

## Alcance del Trabajo

### Geología
- Contexto geológico regional: basamento metamórfico, secuencias volcano-sedimentarias cretácicas, depósitos volcánicos plio-pleistocenos
- Análisis estructural: sistemas de fallas, patrones de foliación, controles tectónicos sobre estabilidad de taludes
- Reconocimiento de campo: documentación de afloramientos, caracterización de materiales, perfiles de meteorización
- Morfología de laderas: identificación de depósitos de deslizamiento, flujos de detritos, rasgos erosivos

### Hidrogeología
- Caracterización de unidades hidrogeológicas por capacidad de infiltración, almacenamiento y conductividad hidráulica
- Identificación de manantiales, rezumaderos y zonas de saturación que afectan la estabilidad de taludes
- Modelo conceptual de flujo de aguas subterráneas: zonas de recarga, tránsito y descarga
- Recomendaciones de drenaje para manejo de aguas superficiales y subterráneas

### Análisis de Amenaza
- Cálculo de Factor de Seguridad usando métodos de equilibrio límite
- Interpolación espacial de parámetros geotécnicos a lo largo del corredor
- Zonificación de amenaza siguiendo umbrales de clasificación estandarizados
- Integración de factores condicionantes: litología, pendiente, precipitación, sismicidad

### Vulnerabilidad y Riesgo
- Inventario de elementos expuestos: infraestructura vial, estructuras de drenaje, muros de contención
- Evaluación de vulnerabilidad usando metodología de matriz de fragilidad
- Clasificación de riesgo combinando probabilidad de amenaza con severidad de consecuencias
- Marco de priorización para planificación de intervenciones

---

## Metodología

### Enfoque de Integración de Datos

El análisis combinó múltiples fuentes de datos en un marco espacial unificado:

```
┌─────────────────────────────────────────────────────────────────┐
│              PIPELINE DE INTEGRACIÓN DE DATOS                    │
├─────────────────────────────────────────────────────────────────┤
│  DATOS DE CAMPO      TELEDETECCIÓN        FUENTES SECUNDARIAS   │
│  ──────────────      ─────────────        ──────────────────    │
│  • Registros de      • Archivo Landsat    • Mapas geológicos    │
│    afloramientos     • Sentinel-2 MSI     • Cartografía         │
│  • Puntos GPS        • DEM (12.5m)          hidrogeológica      │
│  • Parámetros        • Pendiente/aspecto  • Registros           │
│    geotécnicos       • Series NDVI          climáticos          │
│  • Registros foto    •                    • Zonificación        │
│                                             sísmica              │
│                          ↓                                       │
│              ┌─────────────────────────┐                        │
│              │   ANÁLISIS ESPACIAL SIG  │                        │
│              │   • Alineación CRS       │                        │
│              │   • Operaciones raster   │                        │
│              │   • Interpolación        │                        │
│              │   • Clasificación        │                        │
│              └─────────────────────────┘                        │
│                          ↓                                       │
│              ┌─────────────────────────┐                        │
│              │  MAPA DE ZONIFICACIÓN   │                        │
│              │      DE AMENAZA         │                        │
│              └─────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### Análisis Geotécnico

El Factor de Seguridad (FS) fue calculado para puntos críticos usando métodos de talud infinito y equilibrio límite. Los valores continuos de FS fueron luego interpolados espacialmente usando Ponderación por Distancia Inversa (IDW) para generar una superficie de amenaza a través de la zona buffer del corredor.

**Decisiones metodológicas clave:**
- Interpolar valores continuos de FS primero, luego reclasificar a clases discretas de amenaza (más defendible que interpolar categorías)
- Usar teselación de Voronoi con puntos fantasma en los límites para asegurar cobertura completa
- Aplicar buffer del corredor para enfocar el análisis en la zona de influencia

### Análisis Multitemporal

Imágenes satelitales abarcando 1990–2024 fueron procesadas para detectar cambios de vegetación indicativos de inestabilidad de taludes:

- **Índices espectrales**: NDVI (vigor de vegetación), NBR (detección de perturbación/quema)
- **Filtrado de calidad**: Enmascaramiento de nubes, compositos de época seca
- **Fusión de sensores**: Series temporales armonizadas Landsat-Sentinel
- **Detección de cambios**: Diferenciación período a período con clasificación por umbrales

El análisis monitoreó 24 puntos críticos a lo largo del corredor, rastreando dinámicas de vegetación durante más de 30 años:

<p align="center">
  <img src="assets/multitemporal/ndvi_time_series.png" alt="Serie Temporal NDVI" width="700"/>
  <br><em>Serie temporal NDVI para todos los puntos de monitoreo (1990s–Presente)</em>
</p>

<p align="center">
  <img src="assets/multitemporal/ndvi_change_total.png" alt="Cambio Total NDVI" width="700"/>
  <br><em>Mapa de cambio acumulado de vegetación (1990s vs Presente)</em>
</p>

**Hallazgos clave del análisis multitemporal:**
- 90-99% de los puntos de monitoreo muestran recuperación significativa de vegetación
- Patrones de regeneración post-perturbación detectados vía dNBR
- Magnitudes de cambio >1.0 NDVI indican transformaciones mayores del paisaje

> El análisis completo de Google Earth Engine está disponible en [`multitemporal_analysis.ipynb`](multitemporal_analysis.ipynb)

### Marco de Clasificación

Los niveles de amenaza siguen estándares nacionales colombianos con cinco clases basadas en umbrales de Factor de Seguridad:

| Rango FS | Clase | Nivel de Amenaza | Interpretación |
|----------|-------|------------------|----------------|
| FS < 1.0 | 5 | MUY ALTA | Inestable - intervención inmediata requerida |
| 1.0 ≤ FS < 1.2 | 4 | ALTA | Marginalmente estable - intervención prioritaria |
| 1.2 ≤ FS < 1.5 | 3 | MEDIA | Condicionalmente estable - monitoreo necesario |
| 1.5 ≤ FS < 2.0 | 2 | BAJA | Estable bajo condiciones normales |
| FS ≥ 2.0 | 1 | MUY BAJA | Estable - mantenimiento rutinario |

<img width="1904" alt="Clasificación de Amenaza" src="https://github.com/user-attachments/assets/c870562f-3801-4746-a91c-23b6994d607c" />

---

## Datos y Herramientas

### Stack de Software
- **QGIS**: Plataforma SIG principal para análisis espacial y producción cartográfica
- **Python**: Pipelines de procesamiento automatizado (geopandas, rasterio, scipy, numpy)
- **Google Earth Engine**: Procesamiento de imágenes satelitales multitemporales a escala
- **Streamlit**: Desarrollo de dashboard interactivo para visualización por stakeholders

### Técnicas de Análisis Espacial
- Parámetros de terreno derivados de DEM (pendiente, aspecto, curvatura)
- Interpolación IDW para generación de superficies continuas
- Teselación de Voronoi para delimitación de zonas
- Álgebra raster para reclasificación de amenaza
- Análisis de buffer para zona de influencia del corredor

### Productos de Datos Generados
- Raster de amenaza continuo (GeoTIFF)
- Polígonos de zonas de amenaza (GeoPackage)
- Mapas de cambio multitemporal
- Cartografía técnica
- Resúmenes estadísticos y KPIs

---

## Marco de Evaluación de Riesgo

### Amenaza → Vulnerabilidad → Riesgo

La evaluación sigue la ecuación estándar de riesgo:

```
Riesgo = Amenaza × Vulnerabilidad × Exposición
```

**Amenaza (A)**: Probabilidad de ocurrencia de movimiento en masa, derivada del análisis de Factor de Seguridad y precedentes históricos.

**Vulnerabilidad (V)**: Fragilidad de elementos expuestos, evaluada mediante:
- Condición estructural de infraestructura vial
- Presencia/ausencia de sistemas de drenaje
- Efectividad de muros de contención
- Historial de daños previos

**Exposición (E)**: Elementos en riesgo dentro de la zona de amenaza:
- Segmentos viales y pavimento
- Alcantarillas y estructuras de drenaje
- Muros de contención y protección de taludes
- Infraestructura adyacente

### Matriz de Priorización

La clasificación de riesgo permite la asignación de recursos:

| Nivel de Riesgo | Interpretación | Acción |
|-----------------|----------------|--------|
| ALTO | Riesgo inaceptable | Intervención estructural inmediata |
| MEDIO | Riesgo significativo | Intervención planificada + monitoreo |
| BAJO | Riesgo aceptable | Mantenimiento rutinario |

<img width="1899" alt="Análisis de Riesgo" src="https://github.com/user-attachments/assets/a5f370e1-d793-47d7-9e39-5685a6935c91" />

---

## Resultados

### Hallazgos Principales

- Identificados múltiples sectores con FS < 1.0 que requieren estabilización inmediata
- Correlacionadas condiciones hidrogeológicas (manantiales, zonas de rezumadero) con áreas de mayor amenaza
- Detectados patrones de pérdida de vegetación en registro satelital precediendo fallas de talud documentadas
- Mapeados controles estructurales (drenaje paralelo a fallas) que influyen en la distribución de inestabilidad

### Productos de Soporte a Decisiones

El análisis produjo entregables accionables:

1. **Lista priorizada de intervenciones** clasificando puntos críticos por nivel de riesgo y costo estimado de intervención
2. **Mapas de zonificación de amenaza** a escalas de corredor y sitio para diseño de ingeniería
3. **Recomendaciones de drenaje** basadas en caracterización hidrogeológica
4. **Protocolo de monitoreo** especificando ubicaciones, métodos y umbrales de activación

### Insights Técnicos

- Depósitos volcánicos meteorizados mostraron mayor susceptibilidad, particularmente donde ocurre descarga de aguas subterráneas en caras de talud
- Análisis multitemporal de NDVI demostró ser efectivo para identificar inestabilidad incipiente antes de que se desarrollen escarpes visibles
- Interpolación IDW de valores continuos de FS produjo superficies de amenaza más realistas que enfoques categóricos

---

## Por Qué Este Proyecto Importa

### Resiliencia de Infraestructura
Las vías de montaña en regiones en desarrollo frecuentemente representan la única conexión entre comunidades rurales y mercados, salud y educación. Entender y mitigar amenazas geotécnicas impacta directamente los medios de vida y el acceso a servicios esenciales.

### Geociencias Aplicadas
Este proyecto demuestra la integración de métodos clásicos de campo geológico con análisis moderno de teledetección y SIG. La combinación permite tanto comprensión a nivel de sitio como mapeo de amenaza a escala de corredor.

### Toma de Decisiones Informada por Riesgo
Al cuantificar amenaza y riesgo, estudios técnicos como este permiten asignación racional de recursos. Presupuestos limitados pueden dirigirse a intervenciones de mayor prioridad en lugar de respuesta de emergencia reactiva.

### Metodología Transferible
El marco analítico desarrollado aquí—reconocimiento de campo, series temporales satelitales, interpolación espacial, clasificación de amenaza—aplica a corredores viales de montaña a través de los Andes y ambientes de montaña tropical similares globalmente.

---

## Dashboard Interactivo

El proyecto incluye una herramienta de visualización basada en Streamlit para explorar datos de amenaza:

<img width="1592" alt="Características del Dashboard" src="https://github.com/user-attachments/assets/341162be-8229-4427-9d81-4e85d53486d1" />

### Características
- Mapa interactivo con capas activables (raster, zonas Voronoi, puntos críticos)
- Detección automática de tipo de raster (clases discretas vs FS continuo)
- Dashboard de estadísticas y KPIs
- Documentación de metodología

<img width="1916" alt="Estadísticas del Dashboard" src="https://github.com/user-attachments/assets/9f340b6e-f651-4bca-8874-4098c2fc231e" />

### Inicio Rápido

```bash
# Configurar ambiente
conda create -n hazard_dashboard python=3.11 -y
conda activate hazard_dashboard
conda install -c conda-forge geopandas rasterio -y
pip install streamlit streamlit-folium folium pillow

# Ejecutar
streamlit run Home.py
```

### Estructura del Proyecto

```
├── Home.py                 # Punto de entrada principal
├── config.py               # Umbrales, colores, parámetros
├── pages/
│   ├── 1_Estadisticas.py   # KPIs y estadísticas
│   ├── 2_Mapa.py           # Mapa interactivo Folium
│   └── 3_Metodologia.py    # Documentación técnica
├── utils/
│   ├── data_loader.py      # Carga de GeoPackage
│   ├── geotiff_overlay.py  # Conversión raster a Folium
│   └── styles.py           # Estilos de mapa
└── data/
    └── <region>/           # Datos por corredor
        ├── puntos.gpkg
        ├── corredor.gpkg
        ├── voronoi.gpkg
        └── raster_amenaza.tif
```

---

## Aviso de Confidencialidad

> **Nota**: Este caso de estudio está anonimizado. No se comparten nombres de clientes, detalles de contratos, coordenadas precisas ni documentos restringidos. Las visualizaciones y descripciones están generalizadas para propósitos de portafolio. La metodología y enfoque técnico se presentan para demostrar capacidades profesionales sin comprometer la confidencialidad del proyecto.

---

## Referencias Técnicas

- INVÍAS (2022). *Manual de Estabilidad de Taludes*. Instituto Nacional de Vías, Colombia.
- SGC (2017). *Guía Metodológica para Estudios de Amenaza, Vulnerabilidad y Riesgo por Movimientos en Masa*. Servicio Geológico Colombiano.
- Varnes, D.J. (1978). Slope Movement Types and Processes. *Transportation Research Board Special Report 176*.

---

## Licencia

Licencia MIT - Ver [LICENSE](LICENSE) para detalles.

---

*Este repositorio presenta metodología de geociencias aplicadas para evaluación de amenaza en infraestructura. El código y marco analítico se proporcionan como referencia profesional.*
