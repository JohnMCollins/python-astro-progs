#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import copy
import xml.etree.ElementTree as ET
import numpy as np
import argparse
import re
from astropy.io import fits

sys.ps1 = 'FRED'  # Mystery stuff to make interactive work
import matplotlib
# matplotlib.use('Qt4agg')
matplotlib.interactive(True)
import matplotlib.pyplot as plt
plt.ion()

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QWidget, QPushButton, QFrame, QApplication)

import miscutils
import xmlutil
import remgeom
import trimarrays
import remfitshdr

import ui_gsedit
import ui_geomdlg
import ui_about

import gseditdlg


class AboutDlg(QtWidgets.QDialog, ui_about.Ui_aboutdlg):

    def __init__(self, parent=None):
        super(AboutDlg, self).__init__(parent)
        self.setupUi(self)


class GeomDlg(QtWidgets.QDialog, ui_geomdlg.Ui_geomdlg):

    def __init__(self, parent=None):
        super(GeomDlg, self).__init__(parent)
        self.setupUi(self)
        self.figstyle.setEnabled(False)
        self.config = None

    def copyin_rg(self, cf, currw, currh):
        """Initialsse stuff from config"""
        if cf is not None:
            self.config = cf
            self.figstyle.setEnabled(True)
            self.figstyle.addItem("(default)", "")
            for k in cf.altfmts.keys():
                self.figstyle.addItem(k, k)
        self.width.setValue(currw)
        self.height.setValue(currh)

    def copyout(self):
        """Get width and height selected from dlg"""
        return  (self.width.value(), self.height.value())

    def on_figstyle_currentIndexChanged(self, value):
        if type(value) != int:
            return
        which = self.figstyle.currentData()
        if len(which) == 0:
            self.width.setValue(self.config.defwinfmt.width)
            self.height.setValue(self.config.defwinfmt.height)
        else:
            try:
                af = self.config.altfmts[which]
                self.width.setValue(af.width)
                self.height.setValue(af.height)
            except KeyError:
                pass


class GsEditorMain(QtWidgets.QMainWindow, ui_gsedit.Ui_gseditmain):

    def __init__(self):
        super(QtWidgets.QMainWindow, self).__init__()
        self.unsaved = False
        self.currentconfig = None
        self.cfname = None
        self.currentimage = None
        self.currentimage_fname = None
        self.currentImage_title = None
        self.imwidth = 8.00
        self.imheight = 6.00
        self.set_title()
        self.setupUi(self)
        self.updateUI()
        self.gslist.itemDoubleClicked.connect(self.on_action_Edit_Greyscale_triggered)

    def updateUI(self):
        hasconfig = self.currentconfig is not None
        self.action_Save_working_config.setEnabled(hasconfig)
        self.action_Save_config.setEnabled(hasconfig and self.unsaved)
        self.action_Save_config_as.setEnabled(hasconfig)
        self.action_Load_Image_file.setEnabled(hasconfig)
        self.action_Create_Greyscale.setEnabled(hasconfig)
        self.action_Clone_Greyscale.setEnabled(hasconfig)
        self.action_Edit_Greyscale.setEnabled(hasconfig)
        self.action_Delete_Greyscale.setEnabled(hasconfig)

    def load_image_file(self, fname):
        """Load up image file, possibly on startup"""
        global filtfn, fmtch, ftypes

        if miscutils.hassuffix(fname, ".npy"):
            try:
                self.currentimage = np.load(fname)
                self.currentimage_fname = fname
                self.currentimage_title = "Processed image file " + fname
            except OSError as e:
                QtWidgets.QMessageBox.warning(self, "Load image errorr", "Loading from: " + fname + " gave error " + e.strerror)
                return False
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Load image errorr", "Loading from: " + fname + "  wrong file type")
                return False
        elif miscutils.hassuffix(fname, ".fits.gz") or miscutils.hassuffix(fname, ".fits"):
            try:
                ffile = fits.open(fname)
            except OSError as e:
                QtWidgets.QMessageBox.warning(self, "FITS file errorr", "Loading from: " + fname + "  wrong file type")
                return False
            try:
                fhdr = remfitshdr.RemFitsHdr(ffile[0].header)
            except remfitshdr.RemFitsHdrErr as e:
                ffile.close()
                QtWidgets.QMessageBox.warning(self, "FITS file errorr", "Loading from: " + fname + " " + e.args[0])
                return False
            fdat = ffile[0].data.astype(np.float32)
            ffile.close()

            if self.currentconfig is None:
                fdat = trimarrays.trimzeros(trimarrays.trimnan(fdat))
            else:
                il = self.currentconfig.get_imlim(fhdr.filter)
                if il.rows == 1024 or il.cols == 1024:
                    fdat = trimarrays.trimzeros(trimarrays.trimnan(fdat))
                else:
                    fdat = il.apply(fdat)
            self.currentimage = fdat
            self.currentimage_fname = fname
            self.currentimage_title = fhdr.description
        else:
            QtWidgets.QMessageBox.warning(self, "Load imager", "Do not know what kind of file " + fname + " is")
            return False
        return True

    def ask_dirty(self):
        """If file is dirty, ask before zapping"""
        if not self.unsaved: return True
        if QtWidgets.QMessageBox.question(self, "Are you sure", "There are unsaved changes in the file you sure",
			QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No) != QtWidgets.QMessageBox.Yes:
            return False
        return True

    def set_title(self):
        """Reset title after doing something"""
        if self.currentconfig is None:
            self.setWindowTitle("(No config)")
        elif self.cfname is None:
            self.setWindowTitle("Working config")
        else:
            filename = miscutils.removesuffix(os.path.basename(self.cfname)).upper()
            self.setWindowTitle("Processing - " + filename)

    def redisp_config(self):
        """Reset list widget display after load"""
        self.gslist.clear()
        if self.currentconfig is not None:
            gsl = self.currentconfig.list_greyscales()
            for g in gsl:
                self.gslist.addItem(g)

    def on_action_New_config_triggered(self, checked=None):
        if checked is None: return
        if not self.ask_dirty(): return
        self.unsaved = True
        self.cfname = None
        self.currentconfig = remgeom.RemGeom()
        self.redisp_config()
        self.set_title()
        self.updateUI()

    def init_load_working_config(self):
        """Possibly load working config on startup"""
        try:
            self.currentconfig = remgeom.load(mustexist=True)
        except remgeom.RemGeomError:
            QtWidgets.QMessageBox.information(self, "No working config", "No working config, you may want to create one");
            return
        self.set_title()
        self.redisp_config()
        self.updateUI()

    def on_action_Load_working_config_triggered(self, checked=None):
        if checked is None: return
        if not self.ask_dirty(): return
        try:
            self.currentconfig = remgeom.load(mustexist=True)
        except remgeom.RemGeomError as e:
            QtWidgets.QMessageBox.warning(self, "Load file error", e.args[0])
            return
        self.cfname = None
        self.unsaved = False
        self.set_title()
        self.redisp_config()
        self.updateUI()

    def on_action_Load_config_triggered(self, checked=None):
        if checked is None: return
        if not self.ask_dirty(): return
        sfile, filt = QtWidgets.QFileDialog.getOpenFileName(self, self.tr("Select config file"), self.cfname, self.tr("Remgeom files (*.remgeom)"))
        if len(sfile) == 0:
            return
        try:
            self.currentconfig = remgeom.load(sfile, mustexist=True)
        except remgeom.RemGeomError as e:
            QtWidgets.QMessageBox.warning(self, "Load file error", sfile + " gave error: " + e.args[0])
            return
        self.cfname = sfile
        self.unsaved = False
        self.set_title()
        self.redisp_config()
        self.updateUI()

    def on_action_Save_working_config_triggered(self, checked=None):
        if checked is None: return
        if self.currentconfig is None: return
        try:
            remgeom.save(self.currentconfig)
        except remgeom.RemGeomError as e:
            QtWidgets.QMessageBox.warning(self, "Save file error", e.args[0])
            return
        if self.cfname is None:
            self.unsaved = False
        self.redisp_config()
        self.updateUI()

    def on_action_Save_config_triggered(self, checked=None):
        if checked is None: return
        if self.cfname is None:
            self.on_action_Save_config_as_triggered(checked)
            return
        try:
            remgeom.save(self.currentconfig, self.cfname)
        except remgeom.RemGeomError as e:
            QtWidgets.QMessageBox.warning(self, "Save file error", "Saving to: " + self.cfname + " gave error " + e.args[0])
            return
        self.unsaved = False
        self.updateUI()

    def on_action_Save_config_as_triggered(self, checked=None):
        if checked is None: return
        fname, suffix = QtWidgets.QFileDialog.getSaveFileName(self, self.tr("Select save file"), self.cfname, self.tr("Remgoem files (*.remgeom)"))
        if len(fname) == 0:
            return
        fname = miscutils.replacesuffix(fname, ".remgeom")
        try:
            remgeom.save(self.currentconfig, fname)
        except remgeom.RemGeomError as e:
            QtWidgets.QMessageBox.warning(self, "Save file error", "Saving to: " + fname + " gave error " + e.args[0])
            return
        self.cfname = fname
        self.set_title()
        self.unsaved = False
        self.updateUI()

    def on_action_Set_Geometry_triggered(self, checked=None):
        if checked is None: return
        dlg = GeomDlg(self)
        dlg.copyin_rg(self.currentconfig, self.imwidth, self.imheight)
        if dlg.exec_():
            self.imwidth, self.imheight = dlg.copyout()

    def on_action_Load_Image_file_triggered(self, checked=None):
        if checked is None: return
        ifile, filt = QtWidgets.QFileDialog.getOpenFileName(self, self.tr("Select image file"), self.currentimage_fname, self.tr("Numpy or FITS file (*.npy *.fits *.fits.gz)"))
        if len(ifile) == 0:
            return
        if not self.load_image_file(ifile):
            return
        self.updateUI()

    def check_gs_name(self, name):
        """Check new name for greyscale doesn't clash with old one. Returns true if it clashes"""
        if name in self.currentconfig.list_greyscales():
            QtWidgets.QMessageBox.warning(self, "Name error", "Greyscale name" + name + " clashes with existing one")
            return True
        return False

    def on_action_Create_Greyscale_triggered(self, checked=None):
        if checked is None: return
        dlg = gseditdlg.GsEditDlg(self)
        newgs = remgeom.greyscale()
        newgs.setname("NewGSEditMe")
        # Maybe make this configurable sometime
        newgs.setscale([25, 50, 75], [85, 170], isperc=True)
        dlg.copyin(newgs, self)
        while dlg.exec_():
            newname = dlg.get_gs_name()
            if newname is None:
                continue
            if self.check_gs_name(newname):
                continue
            newgs = dlg.copyout()
            self.currentconfig.set_greyscale(newgs)
            self.unsaved = True
            self.redisp_config()
            self.updateUI()
            break
        if dlg.plotfigure is not None:
            plt.close(dlg.plotfigure)

    def on_action_Clone_Greyscale_triggered(self, checked=None):
        if checked is None: return
        cur = self.gslist.currentItem()
        if cur is None:
            return
        origname = str(cur.text())
        fromgs = self.currentconfig.get_greyscale(origname)
        newgs = copy.deepcopy(fromgs)
        newgs.name += 'CloneEdutNe'
        dlg = gseditdlg.GsEditDlg(self)
        dlg.copyin(newgs, self)
        while  dlg.exec_():
            newname = dlg.get_gs_name()
            if newname is None:
                continue
            if newname != origname and self.check_gs_name(newname):
                continue
            newgs = dlg.copyout()
            self.currentconfig.set_greyscale(newgs)
            self.unsaved = True
            self.redisp_config()
            self.updateUI()
            break
        if dlg.plotfigure is not None:
            plt.close(dlg.plotfigure)

    def on_action_Edit_Greyscale_triggered(self, checked=None):
        if checked is None: return
        cur = self.gslist.currentItem()
        if cur is None:
            return
        origname = str(cur.text())
        gs = self.currentconfig.get_greyscale(origname)
        dlg = gseditdlg.GsEditDlg(self)
        dlg.copyin(copy.deepcopy(gs), self)
        while  dlg.exec_():
            newname = dlg.get_gs_name()
            if newname is None:
                continue
            if newname != origname:
                if self.check_gs_name(newname):
                    continue
                newgs = dlg.copyout()
                self.currentconfig.del_greyscale(origname)
                self.currentconfig.set_greyscale(newgs)
                self.redisp_config()
            else:
                newgs = dlg.copyout()
                self.currentconfig.set_greyscale(newgs)
                ######### NB no redisp_config whilst we're just listing names!!!!
            self.unsaved = True
            self.updateUI()
            break
        if dlg.plotfigure is not None:
            plt.close(dlg.plotfigure)

    def on_action_Delete_Greyscale_triggered(self, checked=None):
        if checked is None: return
        cur = self.gslist.currentItem()
        if cur is None:
            return
        gsname = str(cur.text())
        if QtWidgets.QMessageBox.question(self, "Are you sure", "Delete greyscale '" + gsname + "' are you sure?",
            QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No) != QtWidgets.QMessageBox.Yes:
            return
        self.currentconfig.del_greyscale(gsname)
        self.unsaved = True
        self.redisp_config()
        self.updateUI()

    def on_action_about_GS_Edit_triggered(self, checked=None):
        if checked is None: return
        dlg = AboutDlg(self)
        dlg.exec_()

    def on_action_Quit_triggered(self, checked=None):
        if checked is None: return
        if not self.ask_dirty(): return
        QApplication.exit(0)

    def closeEvent(self, event):
        self.on_action_quit_triggered(True)


app = QApplication(sys.argv)
mw = GsEditorMain()
mw.init_load_working_config()

parsearg = argparse.ArgumentParser(description='Greyscale Editorn', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--imagefile', type=str, help='Image file to use')
resargs = vars(parsearg.parse_args())

init_imagefile = resargs['imagefile']
if init_imagefile is not None:
    mw.load_image_file(init_imagefile)

mw.show()
app.exec_()
