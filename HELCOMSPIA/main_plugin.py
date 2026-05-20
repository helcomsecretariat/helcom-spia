from qgis.PyQt.QtWidgets import QAction
from PyQt5.QtGui import QIcon
import os
from .main_dialog import HELCOMSPIADialog

class HELCOMSPIA:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dlg = HELCOMSPIADialog()

    def initGui(self):
        # Menu item
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))
        self.action = QAction(icon, "HELCOM SPIA", self.iface.mainWindow())
        self.action.triggered.connect(self.show_dialog)

        # Add to Plugins menu
        self.iface.addPluginToMenu("&HELCOM SPIA", self.action)

    def unload(self):
        self.iface.removePluginMenu("&HELCOM SPIA", self.action)

    def show_dialog(self):
        self.dlg.show()
