#! /usr/bin/env python3

"""QT mark objects dialog"""

import sys
import os.path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QWidget, QFrame, QApplication)
import miscutils
import find_results
import ui_markobj


class markobjdlg(QtWidgets.QDialog, ui_markobj.Ui_markobj):
    
    def __init__(self, parent=None):
        super(markobjdlg, self).__init__(parent)
        self.setupUi(self)

    def setupobj(self, pref, obj):
        """Set up details of object in dialog"""
        self.filename.setText(pref)
        if len(obj.name) != 0:
            self.objectname.setText(obj.name)
            self.objectname.setReadOnly(True)
            self.label.setEnabled(False)
        if len(obj.dispname) != 0:
            self.dispname.setText(obj.dispname)
            self.dispname.setReadOnly(True)
        self.radeg.setValue(obj.radeg)
        self.decdeg.setValue(obj.decdeg)
        self.apsize.setValue(obj.apsize)
        if obj.istarget:
            self.hide.setEnabled(False)


def record_exit(prefix, op, param=None):
    """Record operaion and exit"""
    try:
        outfn = miscutils.addsuffix(prefix, "edits")
        outf = open(outfn, "at")
    except OSError as e:
        QtWidgets.QMessageBox.warning(None, "File error", "Cannot write " + outfn + " " + e.args[1])
        sys.exit(60)
    if param:
        print(op, param, sep='\t', file=outf)
    else:
        print(op, file=outf)
    outf.close()
    sys.exit(0)


app = QApplication(sys.argv)
try:
    prog, prefix, label = sys.argv
except ValueError:
    QtWidgets.QMessageBox.warning(None, "Wrong arguments", "Expecting file prefix and label arguments")
    sys.exit(20)

try:
    findres = find_results.load_results_from_file(prefix)
except find_results.FindResultErr as e:
    QtWidgets.QMessageBox.warning(None, "Could not load file " + prefix, e.args[0])
    sys.exit(40)

try:
    robj = findres[label]
except find_results.FindResultErr as e:
    QtWidgets.QMessageBox.warning(None, "Could not locate object " + label, e.args[0])
    sys.exit(60)

dlg = markobjdlg()

nosuff = miscutils.removesuffix(prefix, 'findres')

dlg.setupobj(os.path.basename(nosuff), robj)
while dlg.exec_():
    if dlg.label.isChecked():
        newname = str(self.objectname.text())
        if len(newname) < 4:
            QtWidgets.QMessageBox.warning(dlg, "Bad name", "Name must be 4 characters or more")
            continue
        record_exit(nosuff, label, "newName", newname)
    if dlg.hide.isChecked():
        record_exit(nosuff, label, "hide")
    if dlg.apadj.isChecked():
        record_exit(nosuff, label, "apadj", self.apsize.value())
    if dlg.calcaperture.isChecked():
        record_exit(nosuff, label, "calcap")
    QtWidgets.QMessageBox.warning(dlg, "No action", "No action given")
sys.exit(0)
