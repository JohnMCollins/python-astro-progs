#! /usr/bin/env python3

"""QT mark objects dialog"""

import sys
import os.path
import argparse
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import astroquery.utils as autils
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QWidget, QFrame, QApplication)
import miscutils
import find_results
import remdefaults
import objdata
import objedits
import remfits
import ui_markobj
import logs

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
            self.latexname.setText(obj.obj.latexname)
        self.radeg.setValue(obj.radeg)
        self.decdeg.setValue(obj.decdeg)
        self.apsize.setValue(obj.apsize)
        self.curradus.setText("{:.2f}".format(obj.adus))
        magname = None
        magmin = 1e60
        for f in 'griz':
            m = getattr(obj.obj, f+'mag', None)
            if m is not None and m < magmin:
                magname = f
                magmin = m
        if magname is not None:
            self.magname.setText(magname)
            self.magvalue.setText("{:.6g}".format(magmin))
        if obj.istarget:
            self.hide.setEnabled(False)
        self.setname.setEnabled(False)
        self.setnamecalc.setEnabled(False)
        self.frlab.setText(obj.label)
        self.cdiff.setText(str(round(obj.cdiff,4)))
        self.rdiff.setText(str(round(obj.rdiff, 4)))
        self.tcdiff.setText(str(round(findres[0].cdiff, 4)))
        self.trdiff.setText(str(round(findres[0].rdiff, 4)))

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


def record_exit(edit):
    """Record operaion and exit"""
    # Reload in case changed by another instance
    newelist = objedits.ObjEdit_List()
    newelist.loaddb(mycurs, notdone=False)
    if fitsfilename.isdigit():
        edit.obsfile = fitsfilename
    else:
        edit.obsfile = os.path.abspath(fitsfilename)
    if  edit.objind != 0:
        for ed in newelist.editlist:
            if not ed.done:
                if ed.objind == edit.objind:
                    if QtWidgets.QMessageBox.question(None,
                                                  "Already got edit " + ed.op + " for object - replace?",
                                                  QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No) \
                                                  != QtWidgets.QMessageBox.Yes:
                        return
                ed.done = True
                newelist.add_edit(ed)
    newelist.add_edit(edit)
    newelist.savedb(mycurs)
    sys.exit(0)

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
#autils.suppress_vo_warnings()

app = QApplication(sys.argv)

parsearg = argparse.ArgumentParser(description='Interactively mark objects in display', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('args', type=str, nargs='+', help='Label or coords if creating')
remdefaults.parseargs(parsearg, inlib=False, tempdir=False)
parsearg.add_argument('--create', action='store_true', help='Create label at coords')
parsearg.add_argument('--newname', type=str, default='newobj', help='Initial name of new objects')
logs.parseargs(parsearg)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
args = resargs['args']
creating = resargs['create']
newobjname = resargs['newname']
logging = logs.getargs(resargs)

mydb, mycurs = remdefaults.opendb()

fitsfilename = args.pop(0)

try:
    fitsfile = remfits.parse_filearg(fitsfilename, mycurs)
except remfits.RemFitsErr as e:
    QtWidgets.QMessageBox.warning(None, "Could not load FITSfile " + fitsfilename, e.args[0])
    sys.exit(40)

findres = find_results.FindResults(fitsfile)
findres.loaddb(mycurs)

if findres.num_results() == 0:
    QtWidgets.QMessageBox.warning(None, "No results in file ", "No results for file " + fitsfilename)
    sys.exit(41)

elist = objedits.ObjEdit_List()
elist.loaddb(mycurs)

dlg = markobjdlg()

if creating:
    try:
        xcoord, ycoord, raparam, decparam = args
        xcoord = float(xcoord)
        ycoord = float(ycoord)
        raparam = float(raparam)
        decparam = float(decparam)
    except (ValueError, TypeError):
        QtWidgets.QMessageBox.warning(None, "Wrong arguments", "Expecting coordinates for create")
        sys.exit(20)

    dlg.setupplace(os.path.basename(fitsfilename), newobjname, raparam, decparam)
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

    dlg.setupobj(os.path.basename(fitsfilename), robj)

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

        elif objdata.nameused(mycurs, oname, True) or oname in elist.namelist:
            QtWidgets.QMessageBox.warning(dlg, "Duplicated name", "Name clashed with existing name")
            continue

        dispname = str(dlg.dispname.text())
        if len(dispname) == 0:
            dispname = oname
        latexname = str(dlg.latexname.text())
        if len(latexname) == 0:
            latexname = dispname

        apsize = dlg.apsize.value()
        if sn and apsize < 1.0:
            QtWidgets.QMessageBox.warning(dlg, "Invalid aperture", "Aperture must be at least 1")
            continue

        if sn:
            ed = objedits.ObjEdit(op='NEW',
                                  objname=oname,
                                  dispname=dispname,
                                  latexname=latexname,
                                  nrow=ycoord,
                                  ncol=xcoord,
                                  radeg=raparam,
                                  decdeg=decparam,
                                  apsize=apsize)
        else:
            ed = objedits.ObjEdit(op='NEWAP',
                                  objname=oname,
                                  dispname=dispname,
                                  latexname=latexname,
                                  nrow=ycoord,
                                  ncol=xcoord,
                                  radeg=raparam,
                                  decdeg=decparam)
        record_exit(ed)

    else:
   
        oid = robj.obj.objind

        if oid in {e.objind for e in elist.editlist if e.objind is not None and not e.done}:
            QtWidgets.QMessageBox.warning(dlg, "Edit already made", "This has existing edit set up")
            continue

        if dlg.setdispname.isChecked():

            dispname = str(dlg.dispname.text())
            latexname = str(dlg.latexname.text())

            if len(dispname) == 0 or len(latexname) == 0:
                record_exit(objedits.ObjEdit(op='DELDISP', objind=oid))
            else:
                record_exit(objedits.ObjEdit(op="NEWDISP", objind=oid, dispname=dispname, latexname=latexname))

        elif dlg.hide.isChecked():
            record_exit(objedits.ObjEdit(op='HIDE', objind=oid))

        elif dlg.apadj.isChecked():
            apsize = dlg.apsize.value()
            if apsize < 1.0:
                QtWidgets.QMessageBox.warning(dlg, "Invalid aperture", "Aperture must be at least 1")
                continue
            record_exit(objedits.ObjEdit(op='SETAP', objind=oid, apsize=apsize))

        elif dlg.calcaperture.isChecked():
            record_exit(objedits.ObjEdit(op='CALCAP', objind=oid))
        else:
            QtWidgets.QMessageBox.warning(dlg, "No operation selected", "Please choose an operation")
            continue

sys.exit(0)
