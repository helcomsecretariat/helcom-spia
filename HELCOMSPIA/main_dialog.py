import csv
from PyQt5.QtWidgets import QDialog, QFileDialog, QCheckBox, QSpacerItem, QSizePolicy, QMessageBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from pathlib import Path
import os
from PyQt5 import uic
from qgis.core import QgsApplication
from osgeo import gdal, osr
from .processing_task import RasterProcessingTask
import webbrowser

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), "main_dialog_base.ui")
)

class HELCOMSPIADialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
         
                    
        self._init_step_visibility()
        
        # Storage for checkboxes
        self.ec_checkboxes = []
        self.p_checkboxes = []
        
        self.selected_ecs = []
        self.selected_ps = []
        
        self.available_ecs = []
        self.available_ps = []
                
        self.ec_folder = None
        self.p_folder = None
        
        self.selected_tools = []
        
        self.log = {
            "csvFilePath": "",
            "selectedEcP": ""
        }
        
        self.tool_labels = {
            "Tool1": "Impact index SUM tool",
            "Tool2": "Impact index AVERAGE tool",
            "Tool3": "Pressure index SUM tool",
            "Tool4": "Pressure index weighted SUM tool"
        }
        
        # Initial state: everything disabled except CSV loading & EC/P selection
        self.btnConfirmSelection.setEnabled(False)
        self.btnValidate.setEnabled(False)
        self.btnRunTools.setEnabled(False)

        # Disable tool checkboxes initially
        for cb in [self.tool1CheckBox, self.tool2CheckBox,
                   self.tool3CheckBox, self.tool4CheckBox]:
            cb.setEnabled(False)

        # Connect browse button
        self.btnBrowseCsv.clicked.connect(self.select_csv_file)

        # Connect search fields
        self.searchECLineEdit.textChanged.connect(self.filter_ec_list)
        self.searchPLineEdit.textChanged.connect(self.filter_p_list)
        
        # Connect Select/Deselect All buttons
        self.btnSelectAllECs.clicked.connect(self.select_all_ec)
        self.btnDeselectAllECs.clicked.connect(self.deselect_all_ec)
        self.btnSelectAllPs.clicked.connect(self.select_all_p)
        self.btnDeselectAllPs.clicked.connect(self.deselect_all_p)
       
        # Stretch left (EC/P) and right sides
        self.mainHorizontalLayout.setStretch(0, 1)
        self.mainHorizontalLayout.setStretch(1, 1)
        
        self.btnConfirmSelection.clicked.connect(self.confirm_selection)
               
        self.btnBrowseECFolder.clicked.connect(self.select_ec_folder)
        self.btnBrowsePFolder.clicked.connect(self.select_p_folder)
        
        self.btnValidate.clicked.connect(self.run_full_validation)
        
        self.btnRunTools.clicked.connect(self.run_selected_tools)
        
        self.btnReturnToSelection.clicked.connect(self.on_return_to_selection_clicked)
        self.btnReturnToFolders.clicked.connect(self.on_return_to_folders_clicked)
        self.btnCancelProcessing.clicked.connect(self._cancel_processing)
        self.btnStartOver.clicked.connect(self.on_return_to_selection_clicked)
        
        # Output folder selection
        self.btnBrowseOutputFolder.clicked.connect(self.select_output_folder)
        
        self.ecFolderLineEdit.textChanged.connect(self._update_validate_button_state)
        self.pFolderLineEdit.textChanged.connect(self._update_validate_button_state)
        
        
        for cb in [
            self.tool1CheckBox,
            self.tool2CheckBox,
            self.tool3CheckBox,
            self.tool4CheckBox,
        ]:
            cb.toggled.connect(self._update_run_tools_state)
            
        self.outputFolderLineEdit.textChanged.connect(self._update_run_tools_state)
            
        self.tool1CheckBox.setToolTip(
            "Compute weighted EC×P sum raster and EC/P summary CSV."
        )
        self.tool2CheckBox.setToolTip(
            "Compute weighted EC×P average raster and EC/P summary CSV."
        )
        self.tool3CheckBox.setToolTip(
            "Sum selected P rasters only."
        )
        self.tool4CheckBox.setToolTip(
            "Weighted sum of P rasters using average EC scores."
        )
        
        self._set_button_style(self.btnReturnToSelection)
        self._set_button_style(self.btnReturnToFolders)
        
        self.btnHelp.setIcon(QIcon.fromTheme("help-about"))
        self.btnHelp.clicked.connect(self.open_user_guide)
        
    def _set_button_style(self, button):
        button.setStyleSheet("""
            text-align: left; 
            padding: 0px 5px;
            min-height: 28px;
        """)
        button.setIcon(QIcon(":/images/themes/default/mActionArrowLeft.svg"))
        button.setIconSize(QSize(16, 16))
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.adjustSize()
        
    def _init_step_visibility(self):
        self.big_step1.show()
        self.big_step2.hide()
        self.big_step2_Layout.setAlignment(Qt.AlignTop)
        self.big_step3.hide()
        self.big_step3_Layout.setAlignment(Qt.AlignTop)
        self.btnStartOver.hide()
        self.big_step4.hide()
        self.big_step4_Layout.setAlignment(Qt.AlignTop)
        
    
    def on_return_to_selection_clicked(self):
        self.big_step1.show()
        self.big_step2.hide()
        self.big_step3.hide()
        self.big_step4.hide()
        self.selectionOutput.clear()
        self.show_status_message("")
        self.btnStartOver.hide()
        
    def on_return_to_folders_clicked(self):
        self.big_step1.hide()
        self.big_step2.show()
        self.big_step3.hide()
        self.big_step4.hide()
        self.selectionOutput.clear()
        self.show_status_message("")
    
    def _update_confirm_selection_state(self):
        has_ec = any(cb.isChecked() for cb in self.ec_checkboxes)
        has_p  = any(cb.isChecked() for cb in self.p_checkboxes)
        self.btnConfirmSelection.setEnabled(has_ec and has_p)
            
    def _update_validate_button_state(self):
        ec_ok = bool(self.ecFolderLineEdit.text().strip())
        p_ok = bool(self.pFolderLineEdit.text().strip())
        self.btnValidate.setEnabled(ec_ok and p_ok)
    
    def _update_run_tools_state(self):
        any_tool = any(cb.isChecked() for cb in
                       [self.tool1CheckBox, self.tool2CheckBox,
                        self.tool3CheckBox, self.tool4CheckBox])
        
        p = self.outputFolderLineEdit.text().strip()
        folder_path = Path(p)
                        
        self.btnRunTools.setEnabled(any_tool and folder_path.is_dir() and bool(p))
        
    def select_csv_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select sensitivity scores matrix CSV file",
            "",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        self.csvPathLineEdit.setText(path)
        self.load_ec_p_lists(path)
        
        self.log["csvFilePath"] = path


    def load_ec_p_lists(self, csv_path):
        """Reads EC and P names from CSV and populates the UI lists."""

        self.clear_lists()

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # First row (excluding first column) contains P names
        p_names = [name.strip() for name in rows[0][1:]]

        # First column (excluding header) contains EC names
        ec_names = [row[0].strip() for row in rows[1:]]

        # Populate EC list
        for ec in ec_names:
            cb = QCheckBox(ec)
            self.ecCheckboxLayout.addWidget(cb)
            self.ec_checkboxes.append(cb)
            cb.toggled.connect(self._update_confirm_selection_state)

        # Populate P list
        for p in p_names:
            cb = QCheckBox(p)
            self.pCheckboxLayout.addWidget(cb)
            self.p_checkboxes.append(cb)
            cb.toggled.connect(self._update_confirm_selection_state)
            
        # Bind checkbox state changes for live updates
        for cb in self.ec_checkboxes:
            cb.stateChanged.connect(self.update_selection_display)

        for cb in self.p_checkboxes:
            cb.stateChanged.connect(self.update_selection_display)


    def clear_lists(self):
        """Remove all existing checkboxes before loading new CSV."""
        for cb in self.ec_checkboxes:
            self.ecCheckboxLayout.removeWidget(cb)
            cb.deleteLater()
        self.ec_checkboxes.clear()

        for cb in self.p_checkboxes:
            self.pCheckboxLayout.removeWidget(cb)
            cb.deleteLater()
        self.p_checkboxes.clear()

    def filter_ec_list(self, text):
        text = text.lower()

        # Remove ALL spacers at the bottom
        for i in reversed(range(self.ecCheckboxLayout.count())):
            item = self.ecCheckboxLayout.itemAt(i)
            if isinstance(item, QSpacerItem):
                self.ecCheckboxLayout.removeItem(item)

        # Filter checkboxes
        for cb in self.ec_checkboxes:
            cb.setVisible(text in cb.text().lower())

        # Add a fresh bottom spacer
        self.ecCheckboxLayout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )


    def filter_p_list(self, text):
        text = text.lower()

        for i in reversed(range(self.pCheckboxLayout.count())):
            item = self.pCheckboxLayout.itemAt(i)
            if isinstance(item, QSpacerItem):
                self.pCheckboxLayout.removeItem(item)

        for cb in self.p_checkboxes:
            cb.setVisible(text in cb.text().lower())

        self.pCheckboxLayout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        
    def select_all_ec(self):
        for cb in self.ec_checkboxes:
            if cb.isVisible():  # only select items matching current search
                cb.setChecked(True)

    def deselect_all_ec(self):
        for cb in self.ec_checkboxes:
            if cb.isVisible():
                cb.setChecked(False)

    def select_all_p(self):
        for cb in self.p_checkboxes:
            if cb.isVisible():
                cb.setChecked(True)

    def deselect_all_p(self):
        for cb in self.p_checkboxes:
            if cb.isVisible():
                cb.setChecked(False)
                
    def confirm_selection(self):
        selected_ecs = [cb.text() for cb in self.ec_checkboxes if cb.isChecked()]
        selected_ps = [cb.text() for cb in self.p_checkboxes if cb.isChecked()]

        # Validation
        if not selected_ecs:
            self.show_status_message("⚠ Select at least one Ecosystem component.", "error")
            return

        if not selected_ps:
            self.show_status_message("⚠ Select at least one Pressure.", "error")
            return

        # Store selections for later
        self.selected_ecs = [label.strip() for label in selected_ecs]
        self.selected_ps  = [label.strip() for label in selected_ps]


        # Success message at the NEW top location
        self.show_status_message("✅ Ecosystem component and Pressure selection confirmed.", "success")

        # Continue to show details in the text output box
        self.selectionOutput.setPlainText(
            "Selected Ecosystem components:\n" +
            ", ".join(selected_ecs) +
            "\n\nSelected Pressures:\n" +
            ", ".join(selected_ps)
        )
                
        # Hide selection steps
        self.big_step1.hide()
        self.big_step2.show()
        self.big_step3.hide()
        self.big_step4.hide()
        
    def update_selection_display(self):
        # Count ECs
        selected_ecs = [cb.text() for cb in self.ec_checkboxes if cb.isChecked()]
        selected_ec_count = len(selected_ecs)
        total_ec_count = len(self.ec_checkboxes)

        # Count Ps
        selected_ps = [cb.text() for cb in self.p_checkboxes if cb.isChecked()]
        selected_p_count = len(selected_ps)
        total_p_count = len(self.p_checkboxes)

        # Build display text
        output = []
        output.append(f"Selected Ecosystem components: {selected_ec_count} / {total_ec_count}")
        if selected_ecs:
            output.append(", ".join(selected_ecs))

        output.append("")  # spacer line

        output.append(f"Selected Pressures: {selected_p_count} / {total_p_count}")
        if selected_ps:
            output.append(", ".join(selected_ps))

        # Update UI text box
        self.selectionOutput.setPlainText("\n".join(output))
                
    def show_status_message(self, message: str, message_type: str = "info"):
        """
        Shows a colored status message directly beneath the Confirm button.
        message_type: "info", "success", or "error"
        """

        if message_type == "success":
            color = "#0a7f00"  # green
        elif message_type == "error":
            color = "#b30000"  # red
        else:
            color = "#333333"  # default dark

        self.statusMessageLabel.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.statusMessageLabel.setText(message)
        
    def select_ec_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select EC Raster Folder")
        if folder:
            self.ecFolderLineEdit.setText(folder)
            self.ec_folder = folder

    def select_p_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select P Raster Folder")
        if folder:
            self.pFolderLineEdit.setText(folder)
            self.p_folder = folder
            
    def run_full_validation(self):
        """
        Combined validation pipeline:
          1. Validate EC & P folders contain rasters for selected labels.
          2. Ask user if missing rasters should be ignored.
          3. Run detailed GDAL sanity check on all available rasters.
          4. Print a detailed validation log in the summary panel.
        """

        log = []
        ec_folder = self.ecFolderLineEdit.text().strip()
        p_folder = self.pFolderLineEdit.text().strip()

        # Validate ECs
        available_ecs, missing_ecs = self.validate_single_group(
            ec_folder, self.selected_ecs, "EC"
        )
        
        # Validate Ps
        available_ps, missing_ps = self.validate_single_group(
            p_folder, self.selected_ps, "P"
        )
        
        if len(available_ecs) == 0 or len(available_ps) == 0:
            box_message = ""
            if len(available_ecs) == 0 and len(available_ps) == 0:
                box_message = "There no selected Ecosystem component and Pressure rasters in selected folders."
            elif len(available_ecs) == 0 and len(available_ps) > 0:
                box_message = "There no selected Ecosystem component rasters in selected folder."
            elif len(available_ecs) > 0 and len(available_ps) == 0:
                box_message = "There no selected Pressure rasters in selected folder."
            
            self.show_status_message("❌ No rasters in the folders.", "error")
            QMessageBox.critical(
                self,
                "No rasters error",
                f"{box_message}\n\nCheck if:\n  • selected folders contain raster files\n  • file names are same as titles in the CSV file.",
                QMessageBox.Ok
            )
            
            return
        
        # Save available rasters
        self.available_ecs = available_ecs
        self.available_ps = available_ps
        
        # Build file check log
        if missing_ecs or missing_ps:
            log.append("⚠ Some raster files are missing:\n")

            if missing_ecs:
                log.append(f"Missing {len(missing_ecs)} out of {len(self.selected_ecs)} selected Ecosystem component rasters:")
                log.extend(f"  • {m}" for m in missing_ecs)
                log.append("")

            if missing_ps:
                log.append(f"Missing {len(missing_ps)} out of {len(self.selected_ps)} selected Pressure rasters:")
                log.extend(f"  • {m}" for m in missing_ps)
                log.append("")

            # Show log so far
            self.selectionOutput.setPlainText("\n".join(log))
            self.show_status_message("⚠ Missing rasters detected.", "error")

            # Ask user
            proceed = QMessageBox.question(
                self,
                "Missing raster files",
                "\n".join(log) + "\n\nProceed with available rasters?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if proceed == QMessageBox.No:
                self.show_status_message("❌ Validation cancelled.", "error")
                return

            log.append(f"\n⚠ Proceeding with {len(self.available_ecs)} Ecosystem component and {len(self.available_ps)} Pressure available rasters.\n")
            
        else:
            log.append("✅ All raster files found.\n")


        # ===============================================================
        # Step 2 — Full raster metadata sanity check
        # ===============================================================
        log.append("\n=== Raster validation ===\n")

        sanity_report = self.run_raster_sanity_check(ec_folder, p_folder)
        log.append(sanity_report)

        # Critical error detection
        if "❌" in sanity_report:
            self.selectionOutput.setPlainText("\n".join(log))
            self.show_status_message(
                "❌ Critical raster mismatches — cannot proceed.", "error"
            )
            return

        # If passed
        self.selectionOutput.setPlainText("\n".join(log))
        self.show_status_message("✅ Validation complete!", "success")
        
        self.big_step1.hide()
        self.big_step2.hide()
        self.big_step3.show()
        self.big_step4.hide()
        
        for cb in [
            self.tool1CheckBox,
            self.tool2CheckBox,
            self.tool3CheckBox,
            self.tool4CheckBox,
        ]:
            cb.setEnabled(True)

        # After enabling tools, update Run button state
        self._update_run_tools_state()
        
    def validate_single_group(self, folder_path: str, selected_items: list, group_label: str):
        expected_files = [name.strip() + ".tif" for name in selected_items]

        if not folder_path or not os.path.isdir(folder_path):
            return [], expected_files  # everything missing

        files_in_folder = {
            f.lower() for f in os.listdir(folder_path)
            if f.lower().endswith(".tif")
        }

        available = []
        missing = []

        for fn in expected_files:
            if fn.lower() in files_in_folder:
                available.append(fn[:-4])
            else:
                missing.append(fn)

        return available, missing
        
    def run_raster_sanity_check(self, ec_folder: str, p_folder: str):
        
        log = []
        errors = 0
        warnings = 0

        # Collect all raster paths
        all_paths = []
        for name in self.available_ecs:
            all_paths.append(os.path.join(ec_folder, name + ".tif"))
        for name in self.available_ps:
            all_paths.append(os.path.join(p_folder, name + ".tif"))

        if not all_paths:
            return "⚠ No rasters available for validation.\n"

        ref = gdal.Open(all_paths[0])
        if ref is None:
            return "❌ Cannot open reference raster.\n"

        ref_gt = ref.GetGeoTransform()
        ref_proj = ref.GetProjection()
        ref_xsize = ref.RasterXSize
        ref_ysize = ref.RasterYSize
        ref_dtype = ref.GetRasterBand(1).DataType
        ref_block = ref.GetRasterBand(1).GetBlockSize()

        ref_res_x = ref_gt[1]
        ref_res_y = abs(ref_gt[5])

        ref_xmin = ref_gt[0]
        ref_xmax = ref_gt[0] + ref_xsize * ref_gt[1]
        ref_ymax = ref_gt[3]
        ref_ymin = ref_gt[3] + ref_ysize * ref_gt[5]

        log.append(f"First raster: {os.path.basename(all_paths[0])} is used as a reference raster.\n")
        log.append(f"--- Reference raster parameters:")
        info_text = f"CRS: {self.get_raster_crs_name(ref)}\nResolution: {self.get_raster_resolution(ref)}\nDimensions: {self.get_raster_dimensions(ref)}\nExtent: {self.get_raster_extent(ref)}\nBlock size: {self.get_raster_block_size(ref)}\nData type: {self.get_raster_data_type(ref)}\n"
        log.append(info_text)

        for path in all_paths:
            ds = gdal.Open(path)
            name = os.path.basename(path)

            if ds is None:
                errors += 1
                log.append(f"❌ Cannot open: {name}\n")
                continue

            gt = ds.GetGeoTransform()
            proj = ds.GetProjection()
            xsize = ds.RasterXSize
            ysize = ds.RasterYSize
            dtype = ds.GetRasterBand(1).DataType
            block = ds.GetRasterBand(1).GetBlockSize()

            res_x = gt[1]
            res_y = abs(gt[5])

            xmin = gt[0]
            xmax = gt[0] + xsize * gt[1]
            ymax = gt[3]
            ymin = gt[3] + ysize * gt[5]

            if proj != ref_proj:
                errors += 1
                log.append(f"❌ CRS mismatch for {name}: {self.get_raster_crs_name(ds)}\n")

            if (res_x != ref_res_x) or (res_y != ref_res_y):
                errors += 1
                log.append(f"❌ Resolution mismatch for {name}: {self.get_raster_resolution(ds)}\n")

            if xsize != ref_xsize or ysize != ref_ysize:
                errors += 1
                log.append(f"❌ Dimension mismatch for {name}: {self.get_raster_dimensions(ds)}\n")

            if (abs(xmin - ref_xmin) > 0.001 or
                abs(xmax - ref_xmax) > 0.001 or
                abs(ymin - ref_ymin) > 0.001 or
                abs(ymax - ref_ymax) > 0.001):
                errors += 1
                log.append(f"❌ Extent mismatch for {name}: {self.get_raster_extent(ds)}\n")

            if gt[2] != 0 or gt[4] != 0:
                warnings += 1
                log.append(f"⚠ Rotated raster: {name}\n")

            if block != ref_block:
                warnings += 1
                log.append(f"⚠ Block size mismatch for {name}: {self.get_raster_block_size(ds)}\n")

            if dtype != ref_dtype:
                warnings += 1
                log.append(f"⚠ Data type mismatch for {name}: {self.get_raster_data_type(ds)}\n")

        # Summary
        log.append("\n=== Raster validation summary ===\n")
        if errors == 0:
            log.append("✅ No critical errors.\n")
        else:
            log.append(f"❌ {errors} critical errors.\n")

        if warnings == 0:
            log.append("✅ No warnings.\n")
        else:
            log.append(f"⚠ {warnings} warnings.\n")

        if errors == 0:
            log.append("✅ Validation passed — rasters compatible.\n")
        else:
            log.append("❌ Validation failed — rasters incompatible.\n")

        return "\n".join(log)
        
    def get_raster_crs_name(self, ds):
        """
        Return CRS name in a user‑friendly form (e.g. 'EPSG:3035').
        """
        proj_wkt = ds.GetProjection()
        if not proj_wkt:
            return "Unknown"

        srs = osr.SpatialReference()
        srs.ImportFromWkt(proj_wkt)

        auth_name = srs.GetAuthorityName(None)
        auth_code = srs.GetAuthorityCode(None)

        if auth_name and auth_code:
            return f"{auth_name}:{auth_code}"

        return srs.GetName() or "Custom CRS"
        
    def get_raster_resolution(self, ds):
        """
        Return raster resolution as (pixel_width, pixel_height).
        """
        gt = ds.GetGeoTransform()
        pixel_width = abs(gt[1])
        pixel_height = abs(gt[5])
        
        return f"{pixel_width:.6g} × {pixel_height:.6g}"
        
    def get_raster_dimensions(self, ds):
        """
        Return raster dimensions as (cols, rows).
        """
        cols = ds.RasterXSize
        rows = ds.RasterYSize
        
        return f"{cols} × {rows} (cols × rows)"
        
    def get_raster_extent(self, ds):
        """
        Return raster extent as (xmin, ymin, xmax, ymax).
        """
        gt = ds.GetGeoTransform()
        cols = ds.RasterXSize
        rows = ds.RasterYSize

        xmin = gt[0]
        ymax = gt[3]
        xmax = xmin + cols * gt[1]
        ymin = ymax + rows * gt[5]
        
        return f"xmin={xmin:.6f}, ymin={ymin:.6f}, xmax={xmax:.6f}, ymax={ymax:.6f}"
        
    def get_raster_block_size(self, ds):
        """
        Return raster block size as (block_x, block_y).
        """
        band = ds.GetRasterBand(1)
        block_x, block_y = band.GetBlockSize()
        
        return f"{block_x} × {block_y}"

    def get_raster_data_type(self, ds):
        """
        Return raster data type name (e.g. 'Float32').
        """
        band = ds.GetRasterBand(1)
        
        return gdal.GetDataTypeName(band.DataType)
        
    def get_selected_tools(self):
        tools = []
        if self.tool1CheckBox.isChecked():
            tools.append("Tool1")
        if self.tool2CheckBox.isChecked():
            tools.append("Tool2")
        if self.tool3CheckBox.isChecked():
            tools.append("Tool3")
        if self.tool4CheckBox.isChecked():
            tools.append("Tool4")
        return tools

        
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.outputFolderLineEdit.setText(folder)
        
    def run_selected_tools(self):
        tools = self.get_selected_tools()
        if not tools:
            self.show_status_message("⚠ Select at least one tool.", "error")
            return

        output_folder = self.outputFolderLineEdit.text().strip()
        if not output_folder:
            self.show_status_message("⚠ Select an output folder.", "error")
            return

        # Clear summary display
        self.selectionOutput.clear()
        self.show_status_message("⏳ Running selected tools…", "info")
        
        #self.processingStatusLabel.setText("Running selected tools…")
        self.processingProgressBar.setValue(0)

        self.big_step1.hide()
        self.big_step2.hide()
        self.big_step3.hide()
        self.big_step4.show()

        # Start background task
        print("DEBUG: Creating task")
        self.current_task = RasterProcessingTask(
            description="Running raster tools",
            selected_tools=tools,
            ec_labels=self.available_ecs,
            p_labels=self.available_ps,
            ec_folder=self.ecFolderLineEdit.text().strip(),
            p_folder=self.pFolderLineEdit.text().strip(),
            score_matrix_path=self.csvPathLineEdit.text().strip(),
            output_folder=output_folder,
            callback_finished=self.on_tools_finished
        )
        
        
        self.current_task.progressChanged.connect(self._on_task_progress_changed)
        self.current_task.logMessage.connect(self._on_task_log_message)
        
        self._update_estimated_runtime()
        self.btnCancelProcessing.show()
        
        self.add_results_to_map = self.addResultsToMapCheckBox.isChecked()

        QgsApplication.taskManager().addTask(self.current_task)
        
    def on_tools_finished(self, success, outputs, logs):
        
        if self.current_task and self.current_task.isCanceled():
            self.show_status_message(
                "⚠ Processing cancelled by user.",
                "error"
            )

            # Show logs collected so far
            self.selectionOutput.setPlainText("\n".join(logs))

            self.btnStartOver.show()
            self.btnCancelProcessing.hide()
            return

        if success:
            from qgis.core import QgsRasterLayer, QgsProject
            
            # Add result rasters to QGIS map if requested
            if self.add_results_to_map and outputs:
                for tool, result in outputs.items():
                    for key, path in result.items():
                        if path.lower().endswith(".tif") and os.path.exists(path):
                            layer_name = f"{os.path.basename(path)}"
                            layer = QgsRasterLayer(path, layer_name)

                            if layer.isValid():
                                QgsProject.instance().addMapLayer(layer)
                            else:
                                self.selectionOutput.append(
                                    f"⚠ Failed to add raster to map: {path}"
                                )
            self.show_status_message("✅ Tools completed successfully!", "success")
        else:
            self.show_status_message("❌ Tool processing failed.", "error")

        # Show logs in summary output box
        self.selectionOutput.setPlainText("\n".join(logs))
        
        # Optionally list output files
        if success:
            self.selectionOutput.append("\nGenerated output files:")
            for tool, result in outputs.items():
                self.selectionOutput.append(f"\n{self.tool_labels[tool]}:")
                for key, path in result.items():
                    self.selectionOutput.append(f"  • {key}: {path}")
                    
        self.btnStartOver.show()
        self.btnCancelProcessing.hide()
        self.estimatedRuntimeLabel.hide()
        
    def _update_estimated_runtime(self):
        """
        Display a heuristic runtime estimate based on workload size.
        """

        ec_count = len(self.available_ecs)
        p_count = len(self.available_ps)
        tools = self.get_selected_tools()

        pairs = ec_count * p_count
        tool_count = len(tools)

        if pairs == 0 or tool_count == 0:
            self.estimatedRuntimeLabel.hide()
            return

        # Simple heuristic (conservative, non-committal)
        if pairs < 1_000:
            estimate = "Estimated runtime: seconds to a few minutes"
        elif pairs < 10_000:
            estimate = "Estimated runtime: several minutes"
        elif pairs < 50_000:
            estimate = "Estimated runtime: tens of minutes"
        else:
            estimate = "Estimated runtime: tens of minutes to hours"

        self.estimatedRuntimeLabel.setText(estimate)
        self.estimatedRuntimeLabel.show()
                
    def _on_task_progress_changed(self, progress):
        """
        Slot called by QgsTask whenever task progress changes.
        Progress is a float between 0 and 100.
        """
        self.processingProgressBar.setValue(int(progress))
        
    def _on_task_log_message(self, message):
        """
        Receive live log messages from RasterProcessingTask
        and append them to the output panel immediately.
        """
        self.selectionOutput.append(message)
        
    def _cancel_processing(self):
        """
        Cancel the currently running raster processing task.
        """
        if self.current_task and self.current_task.isActive():
            self.current_task.cancel()
            self.show_status_message("⚠ Processing cancelled by user.", "error")
            self.btnCancelProcessing.hide()
            self.estimatedRuntimeLabel.hide()
            
    
    def open_user_guide(self):
        """
        Open online user guide in browser.
        """

        url = "https://github.com/helcomsecretariat/helcom-spia/blob/main/USER_GUIDE.md"

        webbrowser.open(url)


