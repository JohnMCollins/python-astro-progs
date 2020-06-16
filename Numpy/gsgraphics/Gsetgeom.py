#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import copy
import argparse
import xml.etree.ElementTree as ET

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QWidget, QPushButton, QFrame, QApplication)

import miscutils
import xmlutil
import remgeom
import remdefaults

import ui_gsetgeom
import ui_geomabout

import geomoptdlg
import trimeditdlg
import radecdlg


class AboutDlg(QtWidgets.QDialog, ui_geomabout.Ui_aboutdlg):

    def __init__(self, parent=None):
        super(AboutDlg, self).__init__(parent)
        self.setupUi(self)


class GsetgeomMain(QtWidgets.QMainWindow, ui_gsetgeom.Ui_setgeommain):

    def __init__(self):
        super(QtWidgets.QMainWindow, self).__init__()
        self.unsaved = False
        self.currentconfig = None
        self.cfname = None
        self.set_title()
        self.setupUi(self)
        self.updateUI()
        self.geomlist.itemDoubleClicked.connect(self.on_action_Edit_Geometry_triggered)

    def updateUI(self):
        hasconfig = self.currentconfig is not None
        self.action_Save_working_config.setEnabled(hasconfig)
        self.action_Save_config.setEnabled(hasconfig and self.unsaved)
        self.action_Save_config_as.setEnabled(hasconfig)
        self.action_Create_Geometry.setEnabled(hasconfig)
        self.action_Clone_Geometry.setEnabled(hasconfig)
        self.action_Edit_Geometry.setEnabled(hasconfig)
        self.action_Delete_Geometry.setEnabled(hasconfig)

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
        self.geomlist.clear()
        if self.currentconfig is not None:
            self.geomlist.addItem("(Default)")
            for g in self.currentconfig.list_altfmts():
                self.geomlist.addItem(g)

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

    def check_geom_name(self, name):
        """Check new name for greyscale doesn't clash with old one. Returns true if it clashes"""
        if name in self.currentconfig.list_altfmts():
            QtWidgets.QMessageBox.warning(self, "Name error", "Geometry name" + name + " clashes with existing one")
            return True
        return False

    def on_action_Create_Geometry_triggered(self, checked=None):
        if checked is None: return
        dlg = geomoptdlg.GeomOptDlg(self)
        newgeom = remgeom.Winfmt()
        dlg.copyin("NewGeomEditMe", newgeom)
        while dlg.exec_():
            newname = dlg.get_geom_name()
            if newname is None:
                continue
            if self.check_geom_name(newname):
                continue
            dlg.copyout(newgeom)
            self.currentconfig.altfmts[newname] = newgeom
            self.unsaved = True
            self.redisp_config()
            self.updateUI()
            break

    def on_action_Clone_Geometry_triggered(self, checked=None):
        if checked is None: return
        cur = self.geomlist.currentItem()
        if cur is None:
            return
        origname = str(cur.text())
        if origname.isalnum():
            fromgeom = self.currentconfig.altfmts[origname]
        else:
            fromgeom = self.currentconfig.defwinfmt
        newgeom = copy.deepcopy(fromgeom)
        dlg = geomoptdlg.GeomOptDlg(self)
        dlg.copyin('CloneEdutNe', newgeom)
        while  dlg.exec_():
            newname = dlg.get_geom_name()
            if newname is None:
                continue
            if self.check_geom_name(newname):
                continue
            dlg.copyout(newgeom)
            self.currentconfig.altfmts[newname] = newgeom
            self.unsaved = True
            self.redisp_config()
            self.updateUI()
            break

    def on_action_Edit_Geometry_triggered(self, checked=None):
        if checked is None: return
        cur = self.geomlist.currentItem()
        if cur is None:
            return
        origname = str(cur.text())
        if origname.isalnum():
            isdef = False
            fromgeom = self.currentconfig.altfmts[origname]
        else:
            fromgeom = self.currentconfig.defwinfmt
            isdef = True
        newgeom = copy.deepcopy(fromgeom)
        dlg = geomoptdlg.GeomOptDlg(self)
        dlg.copyin(origname, newgeom)
        while  dlg.exec_():
            dlg.copyout(newgeom)
            if isdef:
                self.currentconfig.defwinfmt = newgeom
            else:
                newname = dlg.get_geom_name()
                if newname is None:
                    continue
                if newname != origname:
                    if self.check_geom_name(newname):
                        continue
                    del self.currentconfig.altfmts[origname]
                    self.currentconfig.altfmts[newname] = newgeom
                    self.redisp_config()
                else:
                    self.currentconfig.altfmts[newname] = newgeom
                    ######### NB no redisp_config whilst we're just listing names!!!!
            self.unsaved = True
            self.updateUI()
            break

    def on_action_Delete_Geometry_triggered(self, checked=None):
        if checked is None: return
        cur = self.geomlist.currentItem()
        if cur is None:
            return
        geomname = str(cur.text())
        if not geomname.isalnum():
            QtWidgets.QMessageBox.warning(self, "Cannot delete", "Cannot delete default")
            return
        if QtWidgets.QMessageBox.question(self, "Are you sure", "Delete geometry '" + geomname + "' are you sure?",
            QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No) != QtWidgets.QMessageBox.Yes:
            return
        del self.currentconfig.altfmts[geomname]
        self.unsaved = True
        self.redisp_config()
        self.updateUI()

    def on_action_Edit_Trims_triggered(self, checked=None):
        if checked is None: return
        dlg = trimeditdlg.TrimEditDlg(self)
        copy_current = copy.deepcopy(self.currentconfig)
        dlg.copyin(copy_current)
        if dlg.exec_():
            self.currentconfig = copy_current
            self.unsaved = True
            self.updateUI()

    def on_action_Edit_Limits_triggered(self, checked=None):
        if checked is None: return
        dlg = trimeditdlg.ImLimDlg(self)
        copy_current = copy.deepcopy(self.currentconfig)
        dlg.copyin(copy_current)
        if dlg.exec_():
            self.currentconfig = copy_current
            self.unsaved = True
            self.updateUI()

    def on_action_Set_RA_and_Dec_Colours_triggered(self, checked=None):
        if checked is None: return
        dlg = radecdlg.RaDecDlg()
        copy_current = copy.deepcopy(self.currentconfig)
        dlg.copyin(copy_current)
        if dlg.exec_():
            dlg.copyout()
            self.currentconfig = copy_current
            self.unsaved = True
            self.updateUI()

    def on_action_about_GSetgeom_triggered(self, checked=None):
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
mw = GsetgeomMain()
mw.init_load_working_config()
parsearg = argparse.ArgumentParser(description='Set up config', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

mw.show()
app.exec_()
