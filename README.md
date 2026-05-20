# HELCOM SPIA (QGIS Plugin)

HELCOM SPIA is a QGIS plugin for raster-based analysis of relationships between **Ecosystem Components (EC)** and **Pressures (P)** using a user-provided sensitivity score matrix.

It allows users to combine raster datasets, validate datasets, and generate interpretable spatial outputs for environmental analysis.

---

## Key Features

### SPIA Processing Tools

- **Impact index SUM tool — EC×P Weighted Sum**  
  Computes the weighted sum of selected EC×P combinations using sensitivity scores.

- **Impact index AVERAGE tool — EC×P Weighted Average**  
  Computes the average of selected EC×P combinations using sensitivity scores.

- **Pressure index SUM tool — Pressure Sum**  
  Sums selected Pressure rasters.

- **Pressure index weighted SUM tool — Weighted Pressure Sum**  
  Computes the weighted sum of selected Pressure rasters using sensitivity scores.

---

### Smart Processing

- Shared computation between tools (if more than pone tool is selected).
- NoData handling - if any input rasters have NoData values in certains cells - final raster products get NoData values in those cells.
- Progress bar and processing estimation time.
- Safe cancellation support.

---

### Validation

- Checks raster availability.
- Detects missing EC / P raster datasets.
- Verifies:
  - CRS
  - Resolution
  - Dimensions
  - Extent
  - Data type

---

## Workflow

The plugin guides users through a simple step-by-step process:

1. Load EC×P score matrix (CSV)
2. Select Ecosystem Components and Pressures
3. Validate raster datasets
4. Choose processing tools
5. Run analysis
6. Review outputs

---

## Installation

### Install from ZIP

1. Download plugin archive
2. Open QGIS
3. Go to: Plugins → Manage and Install → Install from ZIP
4. Select the plugin file

---

## Input Data

### CSV Sensitivity scores matrix

- First row → Pressure names  
- First column → Ecosystem Component names  
- Values → EC×P sensitivity scores  

Example:

|     | P1  | P2  |
|-----|-----|-----|
| EC1 | 0.7 | 1.5 |
| EC2 | 0   | 2   |

---

### Raster Datasets

- One dataset per EC and P
- Filename must match CSV labels
- Format: .tif

All rasters must share:

- same CRS  
- same resolution  
- same extent  

---

## Outputs

All outputs are grouped into a timestamped result folder: SPIA-results-YYYY-MM-DD-HH-MM-SS

### Output files

- **Raster outputs (.tif)**
  - Impact index SUM tool → Impact-index-SUM-YYYY-MM-DD-HH-MM-SS.tif
  - Impact index AVERAGE tool → Impact-index-AVERAGE-YYYY-MM-DD-HH-MM-SS.tif
  - Pressure index SUM tool → Pressure-index-SUM-YYYY-MM-DD-HH-MM-SS.tif
  - Pressure index weighted SUM tool → Pressure-index-weighted-SUM-YYYY-MM-DD-HH-MM-SS.tif

- **CSV output (.csv)**
  - Shared between Impact index SUM tool and Impact index AVERAGE tool → Contribution-matrix-YYYY-MM-DD-HH-MM-SS.csv

---

## Requirements

- QGIS **3.28 or newer**
- Recommended:
  - ≥ 8 CPU cores  
  - ≥ 16 GB RAM  

---

## Performance Notes

- Shared computation between tools (if more than pone tool is selected).
- Runtime depends on:
  - number of EC×P combinations
  - raster size
  - system performance

---

## Limitations

- CPU-based processing (no GPU)
- Very large rasters may require significant RAM
- Cancellation is safe but may not be instant

---

## Project Structure

SPIA/
main_dialog.py
processing_task.py
tools_engine.py
raster_utils.py

- **ToolsEngine** → raster computation logic  
- **RasterProcessingTask** → background processing  
- **MainDialog** → UI workflow  
- **RasterUtils** → GDAL operations  

---

## License

(Add your license here — MIT, GPL, etc.)

---

## Contact

(Add your contact information)