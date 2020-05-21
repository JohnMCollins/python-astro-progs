# Scale and offsets dialog

from PyQt5 import QtCore, QtGui, QtWidgets

import ui_geomoptdlg


class GeomOptDlg(QtWidgets.QDialog, ui_geomoptdlg.Ui_geomoptdlg):

    def __init__(self, parent=None):
        super(GeomOptDlg, self).__init__(parent)
        self.setupUi(self)
    
    def copyin(self, name, geom):
        """Copy in and set up parameters"""
        self.geomname.setText(name)
        if not name.isalnum():
            self.geomname.setReadOnly(True)
        self.width.setValue(geom.width)
        self.height.setValue(geom.height)
        self.labsize.setValue(geom.labsize)
        self.ticksize.setValue(geom.ticksize)

    def get_geom_name(self):
        """Get greyscale name, checking it's OK"""
        name = str(self.geomname.text())
        if len(name) == 0:
            QtWidgets.QMessageBox.warning(self, "Name error", "Geometry name cannot be zero length")
            return None
        if not name.isalnum():
            QtWidgets.QMessageBox.warning(self, "Name error", "Geometry name '" + name + "' should be alphanumeric")
            return None
        return name

    def copyout(self, geom):
        """Return greyscale instance based on current dialog"""

        geom.width = self.width.value()
        geom.height = self.height.value()
        geom.labsize = self.labsize.value()
        geom.ticksize = self.ticksize.value()

