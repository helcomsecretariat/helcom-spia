# HELCOM SPIA (QGIS Plugin)

HELCOM SPIA is a QGIS plugin for raster-based analysis of relationships between **Ecosystem Components (EC)** and **Pressures (P)** using a user-defined sensitivity score matrix.

It enables users to combine raster datasets, validate inputs, and generate spatial outputs for environmental analysis.

---

## 🚀 Key Features

### SPIA Processing Tools

- **Impact index SUM tool** — EC×P weighted sum  
- **Impact index AVERAGE tool** — EC×P weighted average  
- **Pressure index SUM tool** — sum of selected Pressure rasters  
- **Pressure index weighted SUM tool** — weighted sum of Pressure rasters  

---

### Smart Processing

- Shared computation between tools (improves performance)
- NoData values handling - if any input rasters have NoData values in certains cells - final raster products get NoData values in those cells.
- Progress bar with runtime estimate
- Safe cancellation

---

### Validation

Checks raster datasets for:

- Missing files  
- CRS consistency  
- Resolution  
- Dimensions  
- Extent  
- Data type  

---

## ⚡ Quick Start

1. Load EC×P sensitivity scores matrix (CSV)
2. Select folders with Ecosystem Component and Pressure rasters
3. Validate raster datasets
4. Select processing tools
5. Run analysis

👉 For full step‑by‑step instructions:

**See the User Guide: USER_GUIDE.md**

---

## 📦 Installation

1. Download plugin ZIP from Releases (use latest release). 
2. Open QGIS
3. Go to:

   Plugins → Manage and Install Plugins → Install from ZIP

4. Select the plugin file

---

## 📁 Outputs

Results are saved in a timestamped folder: SPIA-results-YYYY-MM-DD-HH-MM-SS
Outputs include:

- Raster files (.tif)
- Contribution matrix (.csv)

---

## ⚙️ Requirements

- QGIS 3.28 or newer
- Recommended:
  - ≥ 8 CPU cores  
  - ≥ 16 GB RAM  

---

## 📘 Documentation

👉 Detailed usage instructions and examples are available in:

**USER_GUIDE.md**

---

## ⚠️ Notes

- Processing can take from minutes to hours depending on amount of datasets and their size
- Impact index SUM tool and Impact index AVERAGE tools share computation → faster when run together

---

## 📄 License

(Add your license here)

---

## 📧 Contact

data@helcom.fi
