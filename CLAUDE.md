# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a geotechnical hazard assessment project for the Pijao road corridor in Quindío, Colombia. The code generates mass movement (landslide) hazard maps following Colombian standards (INVÍAS and SGC - Servicio Geológico Colombiano).

**Main outputs:**
- Continuous hazard raster (IDW interpolation)
- Voronoi-based hazard polygons
- Technical reports for engineering oversight
- Cartographic visualizations

## Commands

### Running the Analysis

**Main script (recommended):**
```bash
python3 mapa_amenaza_pijao.py
```

**Jupyter notebook (interactive):**
```bash
jupyter notebook amenaza_pijao.ipynb
```

### Required Input Files

The script expects these GeoPackage files in the current directory:
- `corredor_pijao.gpkg` - Road corridor geometry (line/polygon)
- `puntos_pijao_joined.gpkg` - Critical point locations with geotechnical attributes

## Code Architecture

### Hazard Classification System

The core of this analysis is the `haz_num` index (1-5 scale):
- **1**: MUY BAJA (Very Low) - FS_min >= 1.50
- **2**: BAJA (Low) - 1.30 <= FS_min < 1.50
- **3**: MEDIA (Medium) - 1.10 <= FS_min < 1.30
- **4**: ALTA (High) - 1.00 <= FS_min < 1.10
- **5**: MUY ALTA (Very High) - FS_min < 1.00

Where `FS_min` is the minimum Factor of Safety across all geotechnical scenarios.

### Processing Pipeline

The code follows this workflow:

1. **Data Ingestion & Validation** (`ensure_*` functions):
   - `ensure_projected()` - Converts to UTM if needed
   - `ensure_id_column()` - Creates ID field from various candidates
   - `ensure_fs_min()` - Calculates minimum FS from FS_* columns
   - `ensure_haz_num()` - Derives hazard index from classification or FS_min

2. **Spatial Analysis**:
   - `crear_poligonos_voronoi()` - Generates Voronoi tessellation clipped to corridor buffer
   - `interpolar_idw()` - Inverse Distance Weighting interpolation (power=2)
   - `generar_raster_amenaza()` - Creates continuous hazard raster

3. **Reclassification**:
   - `reclasificar_fs_a_haz()` - Converts continuous FS values to discrete hazard classes using INVÍAS thresholds

4. **Output Generation**:
   - `exportar_raster()` - GeoTIFF export with proper nodata handling
   - `crear_mapa_amenaza()` - Dual-view cartographic visualization (Voronoi + IDW)
   - `generar_informe_tecnico()` - Technical report for interventoría

### Key Parameters

Defined at top of script (lines 108-141):
- `BUFFER_DISTANCE = 100` - Buffer around corridor for interpolation (meters)
- `RESOLUTION = 5` - Raster cell size (meters)
- `CAMPO_CONTINUO = "FS_min"` - Field to interpolate (more defensible than interpolating categories)
- `UMBRALES_FS` - INVÍAS thresholds for FS-to-hazard reclassification

### Robustness Features

The code handles various data quality issues:

- **Multiple geometry types**: Converts non-point geometries to centroids
- **Flexible field names**: Searches for ID fields using candidates: `['ID','Sondeo','SONDEO','fid','FID']`
- **FS_min derivation**: Automatically calculates from all `FS_*` columns if not present
- **haz_num fallback**: Can derive from `CLASIFICACION` text field or calculate from FS thresholds
- **Voronoi edge handling**: Uses phantom points to close boundary cells properly
- **CRS alignment**: Automatically reprojects to matching coordinate systems

### Color Scheme (SGC Standards)

Hazard visualization uses Colombian Geological Service colors:
```python
1: '#1a9641'  # Dark green - Very Low
2: '#a6d96a'  # Light green - Low
3: '#ffffbf'  # Yellow - Medium
4: '#fdae61'  # Orange - High
5: '#d7191c'  # Red - Very High
```

## Important Distinctions

**Hazard vs Risk:**
- This code generates **amenaza** (hazard) maps only
- **Riesgo** (risk) requires additional factors:
  - Exposición (E): Infrastructure/population in the area
  - Vulnerabilidad (V): Fragility of exposed elements
  - Risk formula: R = H × V × E

The output hazard maps are inputs for downstream risk analysis, not final risk assessments.

## File Structure

```
.
├── mapa_amenaza_pijao.py          # Main standalone script (665 lines)
├── amenaza_pijao.ipynb            # Interactive notebook version
├── corredor_pijao.gpkg            # Input: corridor geometry
├── puntos_pijao_joined.gpkg       # Input: critical points with attributes
├── voronoi_amenaza_pijao.gpkg     # Output: Voronoi hazard zones
├── raster_amenaza_pijao.tif       # Output: continuous hazard raster
├── mapa_amenaza_pijao.png         # Output: visualization map
└── informe_tecnico_amenaza_pijao.txt  # Output: technical report
```

## Dependencies

Required Python packages (inferred from imports):
- geopandas
- pandas
- numpy
- scipy
- shapely
- rasterio
- matplotlib

Install with: `pip install geopandas pandas numpy scipy shapely rasterio matplotlib`

## QGIS Integration

To use outputs in QGIS:
1. Load `voronoi_amenaza_pijao.gpkg` and `raster_amenaza_pijao.tif`
2. Apply categorical symbology to raster using the 5-class color scheme
3. Optional: Polygonize raster and dissolve by category for clean vector zones
4. Overlay corridor with black border for context
