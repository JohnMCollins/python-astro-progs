#! /usr/bin/env python3

"""QT mark objects dialog"""

import sys
import os.path
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QWidget, QFrame, QApplication)
import miscutils
import find_results
import remdefaults
import objdata
import objedits
import ui_markobj


class markobjdlg(QtWidgets.QDialog, ui_markobj.Ui_markobj):
    """Dialog box for mark object"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def setupobj(self, pref, obj):
        """Set up details of object in dialog"""
        self.filename.setText(pref)
        if obj.obj is not None:
            self.objectname.setText(obj.obj.objname)
            self.objectname.setReadOnly(True)
            self.setname.setEnabled(False)
            self.dispname.setText(obj.obj.dispname)
        self.radeg.setValue(obj.radeg)
        self.decdeg.setValue(obj.decdeg)
        self.apsize.setValue(obj.apsize)
        if obj.istarget:
            self.hide.setEnabled(False)
        self.setname.setEnabled(False)
        self.setnamecalc.setEnabled(False)
        self.frlab.setText(obj.label)
        self.cdiff.setText(str(obj.cdiff))
        self.rdiff.setText(str(obj.rdiff))
        self.tcdiff.setText(str(findres[0].cdiff))
        self.trdiff.setText(str(findres[0].rdiff))

    def setupplace(self, pref, defname, radeg, decdeg):
        """Set up for marking place"""
        self.filename.setText(pref)
        self.objectname.setText(defname)
        self.radeg.setValue(radeg)
        self.decdeg.setValue(decdeg)
        self.hide.setEnabled(False)
        self.setdispname.setEnabled(False)
        self.apadj.setEnabled(False)
        self.calcaperture.setEnabled(False)


def record_exit(pref, edit):
    """Record operaion and exit"""
    elist = objedits.load_edits_from_file(pref, vicinity=vicinity, create=True)
    elist.add_edit(edit)
    objedits.save_edits_to_file(elist, pref)
    sys.exit(0)


app = QApplication(sys.argv)

parsearg = argparse.ArgumentParser(description='Interactively mark objects in display', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('args', type=str, nargs='+', help='Label or coords if creating')
remdefaults.parseargs(parsearg, inlib=False, tempdir=False)
parsearg.add_argument('--create', action='store_true', help='Create label at coords')
parsearg.add_argument('--findres', type=str, required=True, help='Name of fild results file')
parsearg.add_argument('--newname', type=str, default='newobj', help='Initial name of new objects')
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
args = resargs['args']
creating = resargs['create']
prefix = resargs['findres']
newobjname = resargs['newname']

try:
    findres = find_results.load_results_from_file(prefix)
except find_results.FindResultErr as e:
    QtWidgets.QMessageBox.warning(None, "Could not load file " + prefix, e.args[0])
    sys.exit(40)

if findres.num_results() == 0:
    QtWidgets.QMessageBox.warning(None, "No results in file ", "No results in findres file " + prefix)
    sys.exit(41)

vicinity = findres[0].obj.vicinity

nosuff = miscutils.removesuffix(prefix, 'findres')
dlg = markobjdlg()

mydb, mycurs = remdefaults.opendb()

if creating:
    try:
        xcoord, ycoord, raparam, decparam = args
        xcoord = int(xcoord)
        ycoord = int(ycoord)
        raparam = float(raparam)
        decparam = float(decparam)
    except (ValueError, TypeError):
        QtWidgets.QMessageBox.warning(None, "Wrong arguments", "Expecting coordinates for create")
        sys.exit(20)

    dlg.setupplace(os.path.basename(nosuff), newobjname, raparam, decparam)
    dlg.setname.setChecked(True)
else:
    try:
        label, = args
    except ValueError:
        QtWidgets.QMessageBox.warning(None, "Wrong arguments", "Expecting label argument")
        sys.exit(20)
    try:
        robj = findres[label]
    except find_results.FindResultErr as e:
        QtWidgets.QMessageBox.warning(None, "Could not locate object " + label, e.args[0])
        sys.exit(60)

    dlg.setupobj(os.path.basename(nosuff), robj)

while dlg.exec_():

    if creating:
        sn = dlg.setname.isChecked()
        snc = dlg.setnamecalc.isChecked()

        if not (sn or snc):
            QtWidgets.QMessageBox.warning(dlg, "No action selected", "Need to select action - with or without aperture")
            continue

        oname = str(dlg.objectname.text())

        if len(oname) == 0:
            QtWidgets.QMessageBox.warning(dlg, "No object name", "Need to select object name")
            continue

        elif objdata.nameused(mycurs, oname, True):
            oname = objdata.nextname(mycurs, oname)
            QtWidgets.QMessageBox.information(dlg, "Name amended", "Name clashed and amended to " + oname)

        dispname = str(dlg.dispname.text())
        if len(dispname) == 0:
            dispname = oname
        elif  objdata.nameused(mycurs, dispname, True):
            QtWidgets.QMessageBox.information(dlg, "Display name amended", "Name clashed and reverted to " + oname)
            dispname = oname

        apsize = dlg.apsize.value()
        if sn and apsize < 3:
            QtWidgets.QMessageBox.warning(dlg, "Invalide aperture", "Aperture must be at least 3")
            continue

        if sn:
            ed = objedits.ObjEdit_Newobj_Ap(row=ycoord, col=xcoord, radeg=raparam, decdeg=decparam, apsize=apsize)
        else:
            ed = objedits.ObjEdit_Newobj_Calcap(row=ycoord, col=xcoord, radeg=raparam, decdeg=decparam)
        record_exit(prefix, ed)

    else:
        oid = robj.obj.objind

        if dlg.setdispname.isChecked():

            dispname = str(dlg.dispname.text())

            if len(dispname) == 0:
                record_exit(prefix, objedits.ObjEdit_Deldisp(oid=oid, label=label))

            else:
                if objdata.nameused(mycurs, dispname, True):
                    QtWidgets.QMessageBox.warning(dlg, "Display name not accepted", "Name clashed with existing name")
                    continue
                record_exit(prefix, "newdisp", objedits.ObjEdit_Newdisp(oid=oid, label=label, dname=dispname))

        elif dlg.hide.isChecked():
            record_exit(prefix, objedits.ObjEdit_Hide(oid=oid, label=label))

        elif dlg.apadj.isChecked():
            apsize = dlg.apsize.value()
            if apsize < 3:
                QtWidgets.QMessageBox.warning(dlg, "Invalid aperture", "Aperture must be at least 3")
                continue
            record_exit(prefix, objedits.ObjEdit_Adjap(oid=oid, label=label, apsize=apsize))

        elif dlg.calcaperture.isChecked():
            record_exit(prefix, objedits.ObjEdit_Calcap(oid=oid, label=label))

        else:
            QtWidgets.QMessageBox.warning(dlg, "No operation selected", "Please choose an operation")
            continue

sys.exit(0)
