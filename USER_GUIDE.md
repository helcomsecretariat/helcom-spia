# HELCOM SPIA — User Guide

This guide provides step‑by‑step instructions for installing and using the HELCOM SPIA QGIS plugin.

👉 For general plugin information and features, see **README.md** in plugin Github repository https://github.com/helcomsecretariat/helcom-spia

---

# 📥 1. Getting the Plugin

1. Go to the plugin repository:  
   https://github.com/helcomsecretariat/helcom-spia

2. Download the plugin from **Releases**:
   Releases → HELCOMSPIA.zip
   
   ⚠️ Do NOT use *Code → Download ZIP* (it will not install properly in QGIS)

---

# ⚙️ 2. Installing the Plugin in QGIS

1. Open QGIS  
2. Go to:
   Plugins → Manage and Install Plugins → Install from ZIP
3. Select the downloaded `.zip` file  
4. Click **Install Plugin**  
5. Enable the plugin if needed  

---

# ▶️ 3. Starting the Plugin

1. Open QGIS  
2. Go to:
   Plugins → HELCOM SPIA
3. The plugin dialog will open  

![Plugin window](images/image1.png)

---

# 🧭 4. Workflow Overview

The plugin follows a structured workflow:

1. Load EC×P sensitivity matrix (CSV)
2. Select Ecosystem Component (EC) and Pressure (P) raster folders
3. Validate raster datasets
4. Select tools, options and output folder
5. Run analysis
6. Review outputs

---

# 📊 5. Step‑by‑Step Instructions

---

## ✅ Step 1 — Load sensitivity score matrix (CSV)

- Click **Browse…**
- Select a CSV file containing EC×P scores

### CSV structure

- First row → Pressure names  
- First column → Ecosystem Component names  
- Values → sensitivity scores  

Example:

|     | Pressure 1 | Pressure 2 |
|-----|------------|------------|
| EC1 | 0.7        | 1.5        |
| EC2 | 0          | 2          |

---

#### Delimiter

The plugin **automatically detects the delimiter** and supports following:
- comma `,`
- semicolon `;`
- or tab

---

#### Encoding

The plugin **automatically detects encoding** and supports following:
- UTF‑8
- UTF‑8 with BOM
- Windows‑1252 (Excel default)
- Latin‑1

---

#### Important notes

- The first cell (top-left) can be empty
- Names must match raster filenames (without `.tif`)
- Avoid duplicate EC or P names

## ✅ Step 2 — Select ECs and Ps

Select checkboxes for:
- Ecosystem Components
- Pressures

Optional:
- Use search fields to filter
- Use **Select All / Deselect All**

When at least one EC and one P are selected:
- **Confirm selection** button becomes available

![EC/P selection](images/image2.png)

---

## ✅ Step 3 — Confirm selection

Click:
   Confirm selection

- Selection summary appears on the right panel  
- Next step becomes available  

---

## ✅ Step 4 — Select raster folders

You must choose:
- Folder containing EC rasters  
- Folder containing P rasters  

Each folder must contain `.tif` files matching selected labels.

Example:
   Productive surface waters.tif
   Oxygenated deep waters.tif
   Physical loss.tif
   Physical disturbance.tif

---

## ✅ Step 5 — Validate raster inputs

Click:
   Validate rasters

Validation checks:

- File availability  
- CRS  
- Resolution  
- Dimensions  
- Extent  
- Data type  

---

### Possible outcomes

| Result | Meaning |
|------|--------|
| ✅ All good | Proceed |
| ⚠ Missing rasters | Can proceed with available |
| ❌ No matching rasters | Processing stops |
| ⚠ Warnings | Can proceed |
| ❌ Critical errors | Processing stops |

---

## ✅ Step 6 — Select tools and output folder

1. Select output folder  
2. Choose one or more tools  

### Available tools

- **Impact index SUM tool**  
- **Impact index AVERAGE tool**  
- **Pressure index SUM tool**  
- **Pressure index weighted SUM tool**

Each tool produces a different type of output raster.

---

#### Optional settings

✅ **Add result rasters to the QGIS map**
- Checked → rasters added automatically  
- Unchecked → saved only to disk  

✅ **Save intermediate impact rasters (EC × P × score)**

- Checked → all intermediate impact EC×P rasters will be saved  
- Unchecked → only final results are saved  

⚠️ Warning:
- This option can generate **a very large number of files**
- Processing time and disk usage may increase significantly  

---

![Tool selection](images/image3.png)

---

#### Output structure

The plugin creates a timestamped folder SPIA-results-YYYY-MM-DD-HH-MM-SS in the selected output folder

---

## ✅ Step 7 — Run processing

Click:
   Run selected tools

### During processing

- Progress bar shows progress  
- Estimated runtime is displayed  

---

### Cancel processing

Click:
   Cancel processing

- Processing stops safely  
- No incomplete outputs are written  

---

### After processing completes

- Output files are listed  
- Rasters are added to map (if enabled)  
- You can restart the workflow  

---

# 📁 6. Outputs

All outputs are saved in:
   SPIA-results-YYYY-MM-DD-HH-MM-SS

---

## Raster outputs

- Impact index SUM tool - Impact-index-SUM-YYYY-MM-DD-HH-MM-SS.tif
- Impact index AVERAGE tool - Impact-index-AVERAGE-YYYY-MM-DD-HH-MM-SS.tif 
- Pressure index SUM tool - Pressure-index-SUM-YYYY-MM-DD-HH-MM-SS.tif
- Weighted Pressure index - Pressure-index-weighted-SUM-YYYY-MM-DD-HH-MM-SS.tif

---

## CSV output

- Contribution matrix - Contribution-matrix-YYYY-MM-DD-HH-MM-SS.csv
- Shared between Impact index SUM and Impact index AVERAGE tools

---

## Intermediate rasters (optional, if enabled)

/intermediate/ foldercontains:
- raster for each EC × P × score combination - EC_name_P_name_YYYY-MM-DD-HH-MM-SS.tif

---

# ⏱ 7. Performance Tips

- Tools Impact index SUM and Impact index AVERAGE share computation → faster together  
- Many and large datasets may take hours
  Saving intermediate rasters increases runtime 
- Consider running long jobs overnight  

---

## ⚠️ 8. Errors and Warnings

This section describes common issues and how to resolve them.

---

### ❌ Could not read CSV file

**Cause:**
- Unsupported encoding  
- Corrupt CSV  

**Solution:**
- Open CSV in Excel or text editor  
- Save as **UTF‑8 CSV**  
- Try again  

---

### ❌ Invalid CSV structure

**Cause:**
- Missing header row or column  
- Empty or malformed file  

**Solution:**
- Ensure:
  - first row = Pressures  
  - first column = ECs  
  - data cells contain numbers  

---

### ⚠️ Missing raster files

**Cause:**
- Raster files not found in selected folder  

**Solution:**
- Check:
  - correct folder selected  
  - filenames match EC/P names  

---

### ❌ No matching rasters

**Cause:**
- None of selected EC/P rasters found  

**Solution:**
- Verify file names and paths  
- Ensure `.tif` format  

---

### ⚠️ Validation warnings

**Cause:**
- Minor differences in rasters  

Examples:
- slightly different resolution  
- metadata inconsistencies  

**Solution:**
- Recommended: fix rasters if possible  
- Otherwise: proceed with caution  

---

### ❌ Critical validation errors

**Cause:**
- Different CRS  
- Different raster extents  
- Different dimensions  

**Solution:**
- Reproject or align rasters  
- Use QGIS tools:
  - Warp (reproject)  
  - Align rasters  

---

### ⚠️ Very large number of intermediate rasters

**Cause:**
- Many EC × P combinations  

**Solution:**
- Disable "Save intermediate rasters"  
- Reduce number of EC/P selections  

---

### ⚠️ Processing is slow

**Cause:**
- Large rasters  
- Many EC/P combinations  

**Solution:**
- Reduce inputs  
- Use smaller test datasets  
- Run overnight  

---
# ✅ 9. Best Practices

- Start with small datasets  
- Validate inputs before running  
- Compare outputs using timestamps
- Enable intermediate rasters only when necessary
- Use consistent naming  

---

# 📘 10. Additional Resources

👉 For plugin overview:  
See **README.md**

👉 For updates and issues:  
https://github.com/helcomsecretariat/helcom-spia/issues

---

# ✅ End of Guide
