#! /usr/bin/python

import sys
import os
import os.path
import locale
import argparse

import matplotlib
matplotlib.use('Qt4agg')

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import miscutils
import xmlutil
import specdatactrl
import datarange

import obsfileseldlg
import rangeseldlg
import scaleoffdlg
import ui_sdadminmain

SPC_DOC_NAME = "SPCCTRL"
SPC_DOC_ROOT = "spcctrl"

class SadminMain(QMainWindow, ui_sdadminmain.Ui_sdadminmain):

    def __init__(self):
        super(SadminMain, self).__init__(None)
        self.currentfile = ""
        self.rangefile = ""
        self.unsavedc = False
        self.unsavedr = False
        self.currentlist = None
        self.rangelist = None
        self.setupUi(self)
        self.updateUI()

    def updateUI(self):
        dcf = self.dirty_ctrlfile()
        self.action_Save_Control.setEnabled(dcf)
        nocl = self.currentlist is not None
        self.action_Save_Control_as.setEnabled(nocl)
        self.action_Tune_Ranges.setEnabled(nocl)
        drf = self.dirty_rangefile()
        self.action_Save_ranges.setEnabled(drf)
        norf = self.rangelist is not None
        self.action_Save_ranges_as.setEnabled(norf)

    def dirty_ctrlfile(self):
        """Report if ctrlfile needs saving.

        It will do if we have changed something or if the structure reports it needs
        saving (different X/Y offsets or scaling)"""
        if self.unsavedc: return True
        if self.currentlist is None: return False
        return self.currentlist.dirty

    def ask_dirty_ctrlfile(self):
        """If control file is dirty, ask before zapping"""
        if not self.dirty_ctrlfile(): return True
        if QMessageBox.question(self, "Are you sure", "There are unsaved changes in the control file, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes:
            return False
        return True

    def set_ctrl_file(self, filename):
        """Set control file up to given file name, possibly from argument or from dialog"""
        try:
            doc, root = xmlutil.load_file(filename, SPC_DOC_ROOT)
            newlist = specdatactrl.SpecDataList(filename)
            cnode = xmlutil.find_child(root, "cfile")
            newlist.load(cnode)
        except xmlutil.XMLError as e:
            QMessageBox.warning(self, "Load control file XML error", e.args[0])
            return
        except specdatactrl.SpecDataError as e:
            QMessageBox.warning(self, "Load control file data error", e.args[0])
            return
        self.unsavedc = False
        self.currentfile = filename
        self.currentlist = newlist
        self.updateUI()

    def on_action_New_Control_File_triggered(self, checked = None):
        if checked is None: return
        if not self.ask_dirty_ctrlfile(): return
        self.unsavedc = False
        self.currentfile = ""
        self.currentlist = None
        self.updateUI()
    
    def on_action_Select_Control_File_triggered(self, checked = None):
        if checked is None: return
        if not self.ask_dirty_ctrlfile(): return
        newfile = QFileDialog.getOpenFileName(self, self.tr("Select control file"), self.currentfile, self.tr("Sadmin control files (*.sac)"))
        if len(newfile) == 0: return
        self.set_ctrl_file(str(newfile))

    def on_action_Select_Observation_times_file_triggered(self, checked = None):
        if checked is None: return
        dlg = obsfileseldlg.ObsFileDlg(self)
        dlg.obsfile.setText(self.currentfile)
        if self.currentlist is None:
            dlg.default_fields()
        else:
            dlg.copyin_specfields(self.currentlist.cols, self.currentlist.spdcols)
        while dlg.exec_():
            obslist, speclist = dlg.extract_fields()
            fname = str(dlg.obsfile.text())
            if not os.path.isfile(fname):
                QMessageBox.warning(self, "No such file", "No such file as " + fname)
                continue
            try:
                newlist = specdatactrl.SpecDataList(fname, obslist, speclist)
                newlist.loadfile()
            except specdatactrl.SpecDataError as e:
                QMessageBox.warning(self, "Load file error", "File gave error " + e.args[0])
                continue
            self.currentlist = newlist
            self.unsavedc = True
            self.updateUI()
            return

    def dirty_rangefile(self):
        """Report if range file needs saving."""
        return self.unsavedr

    def ask_dirty_rangefile(self):
        """If range file is dirty, ask before zapping"""
        if not self.dirty_ctrlfile(): return True
        if QMessageBox.question(self, "Are you sure", "There are unsaved changes in the range data, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes:
            return False
        return True

    def set_rangefile(self, filename):
        """Set up range file"""
        try:
            self.rangelist = datarange.load_ranges(filename)
            self.rangefile = filename
            self.unsavedr = False
            self.updateUI()
        except datarange.DataRangeError as e:
            QMessageBox.warning(self, "Range load error", e.args[0])
            return

    def on_action_New_Range_file_triggered(self, checked = None):
        if checked is None: return
        if not self.ask_dirty_rangefile(): return
        self.unsavedr = False
        self.rangefile = ""
        self.rangelist = None
        self.updateUI()

    def on_action_Select_Range_file_triggered(self, checked = None):
        if checked is None: return
        if not self.ask_dirty_rangefile(): return
        newfile = QFileDialog.getOpenFileName(self, self.tr("Select range file"), self.rangefile, self.tr("Range file (*.spcr)"))
        if len(newfile) == 0: return
        newfile = str(newfile)
        if not miscutils.hassuffix(newfile, ".spcr"):
            newfile += ".spcr"
        self.set_rangefile(newfile)

    def on_action_X_Scaling_and_offsets_triggered(self, checked = None):
        if checked is None: return
        if self.currentlist is None:
            QMessageBox.warning(self, "No current obs file", "Please set up an observation times file first")
            return
        dlg = scaleoffdlg.XScaleOffDlg(self)
        dlg.initdata(self.currentlist)
        dlg.exec_()

    def on_action_Y_Scaling_and_offsets_triggered(self, checked = None):
        if checked is None: return
        if self.currentlist is None:
            QMessageBox.warning(self, "No current obs file", "Please set up an observation times file first")
            return
        dlg = scaleoffdlg.YScaleOffDlg(self)
        dlg.initdata(self.currentlist)
        dlg.exec_()
        
    def on_action_Tune_Ranges_triggered(self, checked = None):
        if checked is None: return
        if self.currentlist is None:
            QMessageBox.warning(self, "No current obs file", "Please set up an observation times file first")
            return
        dlg = rangeseldlg.Rangeseldlg(self)
        if self.rangelist is None:
            self.rangelist = datarange.init_default_ranges()
        dlg.copyin_ranges(self.rangelist, self.currentlist)
        if dlg.exec_():
            self.rangelist = dlg.copyout_ranges()
            self.unsavedr = True
            self.updateUI()
        dlg.closefigure()

    def save_cf_ops(self, fname):
        """Guts of saving control file"""
        try:
            doc, root = xmlutil.init_save(SPC_DOC_NAME, SPC_DOC_ROOT)
            self.currentlist.save(doc, root, "cfile")
            xmlutil.complete_save(fname, doc)
            return True
        except xmlutil.XMLError as e:
            QMessageBox.warning(self, "Save control file XML error", e.args[0])
            return False

    def on_action_Save_Control_triggered(self, checked = None):
        if checked is None: return
        if not self.dirty_ctrlfile(): return
        if len(self.currentfile) == 0:
            self.on_action_Save_Control_as_triggered(True)
            return
        if not self.save_cf_ops(self.currentfile): return
        self.unsavedc = False
        self.updateUI()

    def on_action_Save_Control_as_triggered(self, checked = None):
        if checked is None: return
        if self.currentlist is None:
            QMessageBox.warning(self, "No observation list", "No observation list set up yet")
            return
        fname = QFileDialog.getSaveFileName(self, self.tr("Select save file"), self.currentfile, self.tr("Sadmin control files (*.sac)"))
        if len(fname) == 0: return
        fname = str(fname)
        if not miscutils.hassuffix(fname, ".sac"):
            fname += ".sac"
        if not self.save_cf_ops(fname): return
        self.unsavedc = False
        self.currentfile = fname
        self.updateUI()

    def save_rf_ops(self, fname):
        """Guts of saving range file"""
        try:
            datarange.save_ranges(fname, self.rangelist)
            return True
        except datarange.DataRangeError as e:
            QMessageBox.warning(self, "Save range file error", e.args[0])
            return False

    def on_action_Save_ranges_triggered(self, checked = None):
        if checked is None: return
        if not self.unsavedr: return
        if len(self.rangefile) == 0:
            self.on_action_Save_ranges_as_triggered(True)
            return
        if not self.save_rf_ops(self.rangefile): return
        self.unsavedr = False
        self.updateUI()

    def on_action_Save_ranges_as_triggered(self, checked = None):
        if checked is None: return
        if self.rangelist is None:
            QMessageBox.warning(self, "No range list", "No range list set up yet")
            return
        fname = QFileDialog.getSaveFileName(self, self.tr("Select range file"), self.rangefile, self.tr("Range file (*.spcr)"))
        if len(fname) == 0: return
        fname = str(fname)
        if not miscutils.hassuffix(fname, ".spcr"):
            fname += ".spcr"
        if not self.save_rf_ops(fname): return
        self.unsavedr = False
        self.rangefile = fname
        self.updateUI()

    def on_action_Quit_triggered(self, checked = None):
        if checked is None: return
        if (self.dirty_ctrlfile() or self.dirty_rangefile()) and \
            QMessageBox.question(self, "Unsaved data", "There are unsaved changes, sure you want to quit", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes:
            return
        QApplication.exit(0)

    def closeEvent(self, event):
        self.on_action_Quit_triggered(True)

app = QApplication(sys.argv)
parsearg = argparse.ArgumentParser(description='Spectrum data files admin')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data controlfile')
res = vars(parsearg.parse_args())
rf = res['rangefile']
sf = res['specfile']

mw = SadminMain()
if sf is not None:
    mw.set_ctrl_file(sf)
if rf is not None:
    mw.set_rangefile(rf)
mw.show()
os._exit(app.exec_())

