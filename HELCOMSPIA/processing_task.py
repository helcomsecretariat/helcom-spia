from qgis.core import QgsTask, QgsMessageLog, Qgis
import traceback
import time
from PyQt5.QtCore import pyqtSignal

from .tools_engine import ToolsEngine


class RasterProcessingTask(QgsTask):
    """
    Background QGIS task for running selected raster-processing tools.
    Runs Tools 1–4 and reports progress + results back to UI safely.
    """
    logMessage = pyqtSignal(str)
    
    def __init__(self,
                 description,
                 selected_tools,
                 ec_labels,
                 p_labels,
                 ec_folder,
                 p_folder,
                 score_matrix_path,
                 output_folder,
                 csv_delimiter=',',
                 save_intermediate=False,
                 callback_finished=None):
        super().__init__(description, QgsTask.CanCancel)

        self.selected_tools = selected_tools
        self.ec_labels = ec_labels
        self.p_labels = p_labels
        self.ec_folder = ec_folder
        self.p_folder = p_folder
        self.score_matrix_path = score_matrix_path
        self.csv_delimiter = csv_delimiter
        self.output_folder = output_folder
        self.save_intermediate = save_intermediate
        self.callback_finished = callback_finished

        # To collect tool outputs (csv paths, tif paths)
        self.tool_outputs = {}
        self.log_messages = []

    # ------------------------------------------------------------------
    # PROGRESS HANDLING
    # ------------------------------------------------------------------
    def progress_for_tool(self, base_percent, tool_weight, pct):
        """
        Convert tool-local progress (0–100) to global task progress.

        base_percent → starting point for tool
        tool_weight  → how much portion of total progress this tool occupies
        pct          → tool's local progress
        """
        global_progress = base_percent + tool_weight * (pct / 100.0)
        self.setProgress(global_progress)

    # ------------------------------------------------------------------
    # MAIN PROCESSING
    # ------------------------------------------------------------------
    def run(self):
        """
        Runs inside background thread.
        Perform selected tools in order: Tool1 → Tool2 → Tool3 → Tool4
        """
        try:
            t0 = time.time()
            msg = "▶ Processing started..."
            self.log_messages.append(msg + "\n")
            self.logMessage.emit(msg)
            
            # Instantiate processing engine
            engine = ToolsEngine(
                self.ec_labels,
                self.p_labels,
                self.ec_folder,
                self.p_folder,
                self.score_matrix_path,
                self.csv_delimiter,
                self.save_intermediate,
                self.output_folder
            )

            # Calculate progress allocation per tool
            num_tools = len(self.selected_tools)
            tool_weight = 100.0 / num_tools if num_tools > 0 else 100.0
            base = 0.0

            # ----------------------------------------------------------
            # TOOL 1 + TOOL 2 (shared core)
            # ----------------------------------------------------------
            if "Tool1" in self.selected_tools or "Tool2" in self.selected_tools:

                def cb_core(pct):
                    self.progress_for_tool(base, tool_weight, pct)

                core_result = engine.compute_ec_p_core(
                    progress_callback=cb_core,
                    cancel_callback=self._is_cancelled
                )
                                
                intermediate_info = {
                    "count": core_result.get("intermediate_count", 0),
                    "folder": core_result.get("intermediate_folder", None)
                }

                if core_result is None:
                    self.logMessage.emit("⚠ Processing cancelled.")
                    return False

                # ✅ write CSV ONCE
                csv_path = engine.write_common_csv(core_result)

                # TOOL 1
                if "Tool1" in self.selected_tools:
                    out1 = engine.run_tool1(core_result)
                    out1["csv"] = csv_path
                    out1["intermediate"] = intermediate_info
                    self.tool_outputs["Tool1"] = out1

                # TOOL 2
                if "Tool2" in self.selected_tools:
                    out2 = engine.run_tool2(core_result)
                    out2["csv"] = csv_path
                    out2["intermediate"] = intermediate_info
                    self.tool_outputs["Tool2"] = out2

                base += tool_weight

            # ----------------------------------------------------------
            # TOOL 3
            # ----------------------------------------------------------
            if "Tool3" in self.selected_tools:

                def cb3(pct):
                    self.progress_for_tool(base, tool_weight, pct)

                outputs = engine.run_tool3(
                    progress_callback=cb3,
                    cancel_callback=self._is_cancelled
                )
                if outputs is None:
                    self.logMessage.emit("⚠ Pressure index SUM tool cancelled by user.")
                    return False
                    
                self.tool_outputs["Tool3"] = outputs

                base += tool_weight

            # ----------------------------------------------------------
            # TOOL 4
            # ----------------------------------------------------------
            if "Tool4" in self.selected_tools:

                def cb4(pct):
                    self.progress_for_tool(base, tool_weight, pct)

                outputs = engine.run_tool4(
                    progress_callback=cb4,
                    cancel_callback=self._is_cancelled
                )
                if outputs is None:
                    self.logMessage.emit("⚠ Pressure index weighted SUM tool cancelled by user.")
                    return False
                    
                self.tool_outputs["Tool4"] = outputs

                base += tool_weight

            elapsed = time.time() - t0
            elapsed_str = self._format_elapsed_time(elapsed)
            msg = f"✔ Processing finished in {elapsed_str}."
            self.log_messages.append(msg + "\n")
            self.logMessage.emit(msg)

            return True  # Task succeeded

        except Exception as e:
            self.log_messages.append("ERROR during processing:\n")
            self.log_messages.append(str(e) + "\n")
            self.log_messages.append(traceback.format_exc() + "\n")
            QgsMessageLog.logMessage(str(e), "DataPrepTools", level=Qgis.Critical)
            return False

    # ------------------------------------------------------------------
    # FINISHED HANDLER — this runs in main GUI thread
    # ------------------------------------------------------------------
            
    def finished(self, result):
        """
        Called by QGIS after 'run()' completes.
        Executes in the main GUI thread.
        """

        # User cancelled the task
        if self.isCanceled():
            msg = "⚠ Processing cancelled by user."
            QgsMessageLog.logMessage(msg, "DataPrepTools", level=Qgis.Warning)

            if self.callback_finished:
                self.callback_finished(
                    success=False,
                    outputs=None,
                    logs=self.log_messages + [msg]
                )
            return

        # Normal success
        if result:
            QgsMessageLog.logMessage(
                "Processing completed successfully.",
                "DataPrepTools",
                level=Qgis.Info
            )
            if self.callback_finished:
                self.callback_finished(True, self.tool_outputs, self.log_messages)

        # Real failure (exception, logic error)
        else:
            QgsMessageLog.logMessage(
                "Processing failed.",
                "DataPrepTools",
                level=Qgis.Critical
            )
            if self.callback_finished:
                self.callback_finished(False, self.tool_outputs, self.log_messages)
    
    def _is_cancelled(self):
        return self.isCanceled()
        
    def _format_elapsed_time(self, seconds):
        """
        Return human-readable elapsed time.
        """
        seconds = int(seconds)

        if seconds < 60:
            return f"{seconds} seconds"

        minutes, sec = divmod(seconds, 60)
        if minutes < 60:
            return f"{minutes} min {sec} sec"

        hours, minutes = divmod(minutes, 60)
        return f"{hours} h {minutes} min"
