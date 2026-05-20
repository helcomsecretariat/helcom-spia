import os
import numpy as np
import pandas as pd
from osgeo import gdal, gdalconst


class RasterUtils:
    """
    Raster utilities with CORRECT NoData handling for float64 rasters.

    Key features:
      • Load input rasters safely as float32
      • Detect NoData BEFORE float32 cast (fixes float64 → -inf issue)
      • Detect inf/-inf and treat as NoData
      • Produce a float32 array + boolean mask
      • Use NaN to represent NoData internally and in outputs
      • Use float64 ONLY for CSV nansum
      • Write final rasters as float32 with NaN preserved
    """

    def __init__(self):
        self.ec_arrays = {}   
        self.p_arrays = {}

        # Raster metadata (from first loaded raster)
        self.ref_gt = None
        self.ref_proj = None
        self.ref_xsize = None
        self.ref_ysize = None

        self.score_df = None

    # ----------------------------------------------------------------------
    # SCORE MATRIX
    # ----------------------------------------------------------------------
    def load_score_matrix(self, csv_path):
        df = pd.read_csv(csv_path, index_col=0)

        # Trim whitespace (critical!)
        df.index = df.index.str.strip()
        df.columns = df.columns.str.strip()

        self.score_df = df
        return df

    def get_score(self, ec_label, p_label):
        return float(self.score_df.loc[ec_label.strip(), p_label.strip()])

    # ----------------------------------------------------------------------
    # RASTER LOADING WITH SAFE NODATA HANDLING
    # ----------------------------------------------------------------------
    def load_raster(self, path):
        """
        Load raster safely:
          1. Read as float64
          2. Identify NoData BEFORE conversion
          3. Convert inf/-inf to NaN
          4. Convert NoData to NaN
          5. Cast to float32 (safe, no inf)
          6. Produce mask: True = valid, False = NoData
        """
        ds = gdal.Open(path, gdalconst.GA_ReadOnly)
        if ds is None:
            raise RuntimeError(f"Cannot open raster: {path}")

        band = ds.GetRasterBand(1)

        # --- STEP 1: Load as float64 to inspect NoData safely
        arr64 = band.ReadAsArray().astype(np.float64)

        nodata = band.GetNoDataValue()

        # --- STEP 2: Detect NoData BEFORE any float32 cast
        if nodata is not None:
            nd_mask = np.isclose(arr64, nodata, atol=1e-12, rtol=1e-12)
        else:
            nd_mask = np.isnan(arr64)

        # --- STEP 3: Detect inf / -inf from float64 → float32 overflow
        inf_mask = ~np.isfinite(arr64)

        # --- STEP 4: Final valid mask
        mask = ~(nd_mask | inf_mask)

        # --- STEP 5: Assign NaN to invalid pixels
        arr64[~mask] = np.nan

        # --- STEP 6: Convert clean array to float32
        arr = arr64.astype(np.float32)

        # Mask stays boolean
        mask = mask.astype(bool)

        # --- Save reference metadata once
        if self.ref_gt is None:
            self.ref_gt = ds.GetGeoTransform()
            self.ref_proj = ds.GetProjection()
            self.ref_xsize = ds.RasterXSize
            self.ref_ysize = ds.RasterYSize

        return arr, mask

    def get_ec_array(self, label, folder):
        key = label.strip()
        if key not in self.ec_arrays:
            path = os.path.join(folder, f"{key}.tif")
            self.ec_arrays[key] = self.load_raster(path)
        return self.ec_arrays[key]

    def get_p_array(self, label, folder):
        key = label.strip()
        if key not in self.p_arrays:
            path = os.path.join(folder, f"{key}.tif")
            self.p_arrays[key] = self.load_raster(path)
        return self.p_arrays[key]

    # ----------------------------------------------------------------------
    # TMP COMPUTATION (float32 + strict mask propagation)
    # ----------------------------------------------------------------------
    def compute_tmp_array(self, ec_arr, ec_mask, p_arr, p_mask, score):
        # EC * P * score in float32
        tmp_numeric = (ec_arr * p_arr * score).astype(np.float32)

        tmp_mask = ec_mask & p_mask

        # invalid → NaN
        tmp = np.where(tmp_mask, tmp_numeric, np.nan).astype(np.float32)

        return tmp, tmp_mask

    # ----------------------------------------------------------------------
    # OUTPUT WRITERS (float32 rasters + NaN)
    # ----------------------------------------------------------------------
    def write_tif(self, array_float32, output_path):
        """Write float32 GeoTIFF with NaN preserved as NoData."""
        driver = gdal.GetDriverByName("GTiff")
        ds = driver.Create(
            output_path,
            self.ref_xsize,
            self.ref_ysize,
            1,
            gdal.GDT_Float32,
            options=["COMPRESS=LZW", "TILED=YES"]
        )

        ds.SetGeoTransform(self.ref_gt)
        ds.SetProjection(self.ref_proj)

        band = ds.GetRasterBand(1)
        band.WriteArray(array_float32.astype(np.float32))
        band.SetNoDataValue(np.nan)
        band.FlushCache()
        ds = None

    def write_csv_matrix(self, csv_path, ec_labels, p_labels, matrix_2d):
        """Write CSV (float64-safe) with P SUM and EC SUM."""
        df = pd.DataFrame(matrix_2d, index=ec_labels, columns=p_labels)

        df["P SUM"] = df.sum(axis=1)

        ec_sum_row = df.sum(axis=0)
        ec_sum_row.name = "EC SUM"

        df = pd.concat([df, ec_sum_row.to_frame().T], axis=0)
        df.to_csv(csv_path)
