# Pijao Landslide Hazard Dashboard

Dashboard interactivo para visualización y análisis de amenaza por movimientos en masa en corredores viales. Desarrollado para el corredor Pijao, Quindío, Colombia.
<img width="1895" height="905" alt="image" src="https://github.com/user-attachments/assets/13a7c604-297f-440d-9614-47e975ae2367" />


## Características

- **Mapa interactivo** con capas toggleables (Raster IDW, Voronoi, Corredor, Puntos críticos)
- **Detección automática** de tipo de raster (discreto vs continuo) con reclasificación en caliente
- **Soporte multi-región**: estructura `data/<region>/` para múltiples corredores
- **Estadísticas y KPIs**: distribución de amenaza, puntos críticos, FS mínimo/máximo
- **Filtros dinámicos**: amenaza mínima, Top N puntos, opacidad de capas
- **Popups informativos**: FS, clase de amenaza, umbral aplicado
<img width="1592" height="726" alt="image" src="https://github.com/user-attachments/assets/341162be-8229-4427-9d81-4e85d53486d1" />

## Clasificación de Amenaza
<img width="1904" height="859" alt="image" src="https://github.com/user-attachments/assets/c870562f-3801-4746-a91c-23b6994d607c" />

Basada en el Factor de Seguridad (FS) según metodología INVÍAS/SGC:

| Rango FS | Clase | Amenaza | Color |
|----------|-------|---------|-------|
| FS < 1.0 | 5 | MUY ALTA | 🔴 Rojo |
| 1.0 ≤ FS < 1.2 | 4 | ALTA | 🟠 Naranja |
| 1.2 ≤ FS < 1.5 | 3 | MEDIA | 🟡 Amarillo |
| 1.5 ≤ FS < 2.0 | 2 | BAJA | 🟢 Verde claro |
| FS ≥ 2.0 | 1 | MUY BAJA | 🟢 Verde oscuro |

> **Umbral crítico**: FS < 1.0 indica talud inestable que requiere intervención inmediata.
<img width="1899" height="906" alt="image" src="https://github.com/user-attachments/assets/a5f370e1-d793-47d7-9e39-5685a6935c91" />

## Instalación

### 1. Crear ambiente conda

```bash
conda create -n pijao_dashboard python=3.11 -y
conda activate pijao_dashboard
```

### 2. Instalar dependencias geoespaciales (recomendado vía conda)

```bash
conda install -c conda-forge geopandas rasterio -y
```

### 3. Instalar Streamlit y Folium

```bash
pip install streamlit streamlit-folium folium pillow
```

### 4. Verificar instalación

```bash
python -c "import streamlit; import folium; import geopandas; import rasterio; print('OK')"
```

## Estructura del Proyecto

```
pijao/
├── Home.py                     # Página principal (overview)
├── config.py                   # Fuente única de verdad (umbrales, colores)
├── requirements.txt            # Dependencias Python
├── mapa_amenaza_pijao.py       # Motor de cálculo offline
│
├── pages/
│   ├── 1_Estadisticas.py       # KPIs y estadísticas
│   ├── 2_Mapa.py               # Mapa interactivo Folium
│   └── 3_Metodologia.py        # Documentación técnica
│
├── utils/
│   ├── __init__.py
│   ├── data_loader.py          # Carga de GeoPackages + detección raster
│   ├── geotiff_overlay.py      # Conversión GeoTIFF → PNG RGBA para Folium
│   └── styles.py               # Estilos de capas y popups
│
└── data/
    └── pijao/                  # Datos por región
        ├── puntos.gpkg         # Puntos críticos con FS_min, haz_num
        ├── corredor.gpkg       # Geometría del corredor vial
        ├── voronoi.gpkg        # Polígonos de zonificación
        └── raster_amenaza.tif  # Raster de amenaza (clases 1-5)
```

## Uso

### Ejecutar el dashboard

```bash
conda activate pijao_dashboard
cd /path/to/pijao
streamlit run Home.py
```

El dashboard se abrirá en `http://localhost:8501`

### Agregar una nueva región

1. Crear directorio con el nombre de la región:
```bash
mkdir -p data/nueva_region
```

2. Copiar los 4 archivos requeridos:
```bash
cp puntos.gpkg data/nueva_region/
cp corredor.gpkg data/nueva_region/
cp voronoi.gpkg data/nueva_region/
cp raster_amenaza.tif data/nueva_region/
```

3. La región aparecerá automáticamente en el selector del sidebar.

### Regenerar outputs (motor offline)

```bash
python3 mapa_amenaza_pijao.py
```

Genera:
- `voronoi_amenaza_pijao.gpkg` - Polígonos de zonificación
- `raster_amenaza_pijao.tif` - Raster de amenaza
- `mapa_amenaza_pijao.png` - Mapa estático
- `informe_tecnico_amenaza_pijao.txt` - Reporte técnico

## Configuración

### Umbrales de clasificación

Editar `config.py` para ajustar umbrales:

```python
UMBRALES_AMENAZA = {
    'version': 'matriz_proyecto_v1',
    'bins': np.array([0.0, 1.0, 1.2, 1.5, 2.0, np.inf]),
    'clases': [5, 4, 3, 2, 1],
    # ...
}
```

### Colores SGC

```python
COLORES_SGC = {
    1: '#1a9641',  # Verde oscuro - Muy Baja
    2: '#a6d96a',  # Verde claro - Baja
    3: '#ffffbf',  # Amarillo - Media
    4: '#fdae61',  # Naranja - Alta
    5: '#d7191c'   # Rojo - Muy Alta
}
```

## Detección Automática de Raster

El dashboard detecta automáticamente si el raster contiene:

- **Valores discretos (1-5)**: Usa directamente como clases de amenaza
- **Valores continuos (FS)**: Reclasifica en caliente usando los umbrales de `config.py`

Esto permite flexibilidad en los inputs sin requerir preprocesamiento manual.

## Notas Técnicas

### Interpolación

- **Método**: IDW (Inverse Distance Weighting) con power=2
- **Campo interpolado**: `FS_min` (valor continuo, más defendible que interpolar categorías)
- **Reclasificación**: Post-interpolación a clases discretas

### Voronoi

- Generación con puntos fantasma en esquinas del bbox para cerrar celdas de borde
- Clipping al buffer del corredor (100m por defecto)

### CRS

- Datos internos: EPSG:3116 (MAGNA-SIRGAS Colombia Bogotá) para cálculos
- Visualización: EPSG:4326 (WGS84) para Folium/Leaflet

## Limitaciones

1. **Resolución vs precisión**: El raster de 5m/pixel no implica precisión de 5m; depende de la densidad de puntos de muestreo
2. **Interpolación**: IDW asume variación espacial suave; puede no capturar discontinuidades geológicas
3. **Amenaza ≠ Riesgo**: Este sistema genera mapas de **amenaza** (H). El riesgo requiere: R = H × V × E

## Dependencias

| Paquete | Versión | Uso |
|---------|---------|-----|
| streamlit | ≥1.31.0 | Framework web |
| streamlit-folium | ≥0.19.0 | Integración Folium |
| folium | ≥0.15.0 | Mapas interactivos |
| geopandas | ≥0.14.0 | Datos vectoriales |
| rasterio | ≥1.3.9 | Datos raster |
| pandas | ≥2.1.0 | Tablas |
| numpy | ≥1.25.0 | Cálculos |
| Pillow | ≥10.0.0 | Procesamiento de imágenes |

## Licencia

Proyecto desarrollado para el Consorcio Puntos Críticos - Análisis de riesgo vial, Quindío, Colombia.

## Contacto

Para soporte técnico o preguntas sobre la metodología, contactar al equipo de geotecnia del proyecto.
