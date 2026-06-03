import os
import numpy as np
from datetime import datetime
from .raster_utils import RasterUtils


class ToolsEngine:
    """
    Tools 1–4 using hybrid float32/float64 computation:

      - EC/P rasters loaded as float32 arrays + boolean masks (from Module 1e)
      - EC*P*score temporary arrays computed in float32
      - CSV sums computed in float64 (np.nansum)
      - Strict NoData propagation (if ANY invalid → result = NaN)
      - Final GeoTIFF saved as float32 with NaN preserved

    This module is fully synchronized with raster_utils Module 1e.
    """

    def __init__(self,
                 ec_labels,
                 p_labels,
                 ec_folder,
                 p_folder,
                 score_matrix_path,
                 save_intermediate,
                 output_folder):

        # Trim labels (safe for score matrix indexing)
        self.ec_labels = [e.strip() for e in ec_labels]
        self.p_labels = [p.strip() for p in p_labels]

        self.ec_folder = ec_folder
        self.p_folder = p_folder

        # Raster utilities (float32 + NaN safe)
        self.utils = RasterUtils()
        self.utils.load_score_matrix(score_matrix_path)
        
        self.save_intermediate = save_intermediate
        
        self.run_timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self.output_folder = os.path.join(output_folder, f"SPIA-results-{self.run_timestamp}")
        os.makedirs(self.output_folder, exist_ok=True)
             
        self.intermediate_count = 0
        self.intermediate_folder = None

        
        
    def compute_ec_p_core(self, progress_callback=None, cancel_callback=None):
        """
        Shared EC × P computation for Tool 1 and Tool 2.
        Computes:
            - csv_matrix
            - sum_array
            - sum_mask
            - total_pairs
        """

        total_pairs = len(self.ec_labels) * len(self.p_labels)
        if total_pairs == 0:
            raise RuntimeError("No EC/P combinations selected.")

        csv_matrix = np.zeros(
            (len(self.ec_labels), len(self.p_labels)),
            dtype=np.float64
        )

        sum_array = None
        sum_mask = None

        pair = 0

        for ei, ec in enumerate(self.ec_labels):

            if cancel_callback and cancel_callback():
                return None

            ec_arr, ec_mask = self.utils.get_ec_array(ec, self.ec_folder)

            for pj, p in enumerate(self.p_labels):

                if cancel_callback and cancel_callback():
                    return None

                p_arr, p_mask = self.utils.get_p_array(p, self.p_folder)
                score = self.utils.get_score(ec, p)

                tmp, tmp_mask = self.utils.compute_tmp_array(
                    ec_arr, ec_mask,
                    p_arr, p_mask,
                    score
                )                
                
                if self.save_intermediate:
                                        
                    if self.intermediate_folder is None:
                        self.intermediate_folder = os.path.join(self.output_folder, "intermediate")
                        os.makedirs(self.intermediate_folder, exist_ok=True)

                    # Create safe file name
                    ec_name = ec.replace(" ", "_").replace("/", "_")
                    p_name = p.replace(" ", "_").replace("/", "_")

                    filename = f"EC_{ec_name}__P_{p_name}_{self.run_timestamp}.tif"
                    intermediate_folder = os.path.join(self.output_folder, "intermediate")
                    os.makedirs(intermediate_folder, exist_ok=True)
                    filepath = os.path.join(intermediate_folder, filename)

                    self.utils.write_tif(tmp, filepath)
                    
                    self.intermediate_count += 1

                # CSV
                csv_matrix[ei, pj] = np.nansum(tmp, dtype=np.float64)

                # Sum accumulation
                if sum_array is None:
                    sum_array = tmp.copy()
                    sum_mask = tmp_mask.copy()
                else:
                    valid = sum_mask & tmp_mask
                    sum_array = np.where(
                        valid,
                        np.nan_to_num(sum_array) + np.nan_to_num(tmp),
                        np.nan
                    ).astype(np.float32)
                    sum_mask = valid

                pair += 1

                if progress_callback:
                    progress_callback(100 * pair / total_pairs)

        return {
            "csv_matrix": csv_matrix,
            "sum_array": sum_array,
            "sum_mask": sum_mask,
            "total_pairs": total_pairs,
            "intermediate_count": self.intermediate_count,
            "intermediate_folder": self.intermediate_folder
        }
        
    def write_common_csv(self, core_result):
        csv_path = os.path.join(self.output_folder, f"Contribution-matrix-{self.run_timestamp}.csv")
        self.utils.write_csv_matrix(
            csv_path,
            self.ec_labels,
            self.p_labels,
            core_result["csv_matrix"]
        )

        return csv_path

    def run_tool1(self, core_result):
        """
        Tool 1: write sum raster only (no recalculation)
        """

        sum_array = core_result["sum_array"]
        tif_path = os.path.join(self.output_folder, f"Impact-index-SUM-{self.run_timestamp}.tif")
        self.utils.write_tif(sum_array, tif_path)

        return {"tif": tif_path}
        
    def run_tool2(self, core_result):
        """
        Tool 2: average = sum / total_pairs
        """

        sum_array = core_result["sum_array"]
        total_pairs = core_result["total_pairs"]

        avg_array = np.where(
            np.isnan(sum_array),
            np.nan,
            sum_array / float(total_pairs)
        ).astype(np.float32)

        tif_path = os.path.join(self.output_folder, f"Impact-index-AVERAGE-{self.run_timestamp}.tif")
        self.utils.write_tif(avg_array, tif_path)

        return {"tif": tif_path}

    def run_tool3(self, progress_callback=None, cancel_callback=None):
        if len(self.p_labels) == 0:
            raise RuntimeError("No Pressures selected for Pressure index SUM tool.")

        sum_array = None
        sum_mask  = None

        for i, p in enumerate(self.p_labels):
            if cancel_callback and cancel_callback():
                return None
            p_arr, p_mask = self.utils.get_p_array(p, self.p_folder)

            if sum_array is None:
                sum_array = p_arr.copy()
                sum_mask  = p_mask.copy()
            else:
                valid = sum_mask & p_mask
                sum_array = np.where(
                    valid,
                    np.nan_to_num(sum_array) + np.nan_to_num(p_arr),
                    np.nan
                ).astype(np.float32)
                sum_mask = valid

            if progress_callback:
                progress_callback(100 * (i + 1) / len(self.p_labels))

        tif_path = os.path.join(self.output_folder, f"Pressure-index-SUM-{self.run_timestamp}.tif")
        self.utils.write_tif(sum_array, tif_path)
        
        if cancel_callback and cancel_callback():
            return None
        if sum_array is None:
            return None

        return {"tif": tif_path}

    def run_tool4(self, progress_callback=None, cancel_callback=None):
        if len(self.p_labels) == 0:
            raise RuntimeError("No Pressures selected for Pressure index weighted SUM tool.")
        if len(self.ec_labels) == 0:
            raise RuntimeError("Pressure index weighted SUM tool requires Ecosystem components to compute average scores.")

        sum_array = None
        sum_mask  = None

        for i, p in enumerate(self.p_labels):
            if cancel_callback and cancel_callback():
                return None
            # average score for this P
            scores = [self.utils.get_score(ec, p) for ec in self.ec_labels]
            avg_score = float(np.mean(scores))

            p_arr, p_mask = self.utils.get_p_array(p, self.p_folder)

            weighted = (p_arr * avg_score).astype(np.float32)

            if sum_array is None:
                sum_array = weighted.copy()
                sum_mask  = p_mask.copy()
            else:
                valid = sum_mask & p_mask
                sum_array = np.where(
                    valid,
                    np.nan_to_num(sum_array) + np.nan_to_num(weighted),
                    np.nan
                ).astype(np.float32)
                sum_mask = valid

            if progress_callback:
                progress_callback(100 * (i + 1) / len(self.p_labels))

        tif_path = os.path.join(self.output_folder, f"Pressure-index-weighted-SUM-{self.run_timestamp}.tif")
        self.utils.write_tif(sum_array, tif_path)
        
        if cancel_callback and cancel_callback():
            return None
        if sum_array is None:
            return None

        return {"tif": tif_path}