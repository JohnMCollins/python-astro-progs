#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse
import xml.etree.ElementTree as ET

sys.ps1 = 'FRED'            # Mystery stuff to make interactive work
import matplotlib
matplotlib.use('Qt4agg')
matplotlib.interactive(True)
import matplotlib.pyplot as plt
plt.ion()

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import miscutils
import xmlutil
import specdatactrl
import datarange
import specinfo
import mpplotter
import configfile

import obsfileseldlg
import rangeseldlg
import scaleoffdlg
import ui_sdadminmain
import ui_progoptsdlg

CONFIGFNAME = 'Sdadmin'
CONFIGROOT = 'SDADMIN'

class SdaminConfig(object):
    """Bits and pieces of program options"""

    def __init__(self):
        self.swidth = 15.0
        self.sheight = 10.0

    def load(self, node):
        """Load from XML DOM node"""
        for child in node:
            tagn = child.tag
            if tagn == "geom":
                self.load_geom(child)

    def load_geom(self, node):
        """Load geom parameters"""
        for child in node:
            tagn = child.tag
            if tagn == "width":
                self.swidth = xmlutil.getfloat(child)
            elif tagn == "height":
                self.sheight = xmlutil.getfloat(child)

    def save_geom(self, doc, pnode, name):
        """Save geom parameters"""
        node = ET.SubElement(pnode, name)
        xmlutil.savedata(doc, node, "width", self.swidth)
        xmlutil.savedata(doc, node, "height", self.sheight)

    def save(self, doc, pnode):
        """Save to XML DOM node"""
        self.save_geom(doc, pnode, "geom")

class ProgoptsDlg(QDialog, ui_progoptsdlg.Ui_progoptsdlg):
    def __init__(self, parent = None):
        super(ProgoptsDlg, self).__init__(parent)
        self.setupUi(self)

class SadminMain(QMainWindow, ui_sdadminmain.Ui_sdadminmain):

    def __init__(self):
        super(SadminMain, self).__init__(None)
        self.sinf = None
        self.currentlist = None
        self.rangelist = datarange.init_default_ranges()
        self.unsavedc = False
        self.unsavedr = False
        self.setupUi(self)
        self.updateUI()
        self.origtitle = str(self.windowTitle())

    def resetTitle(self, filename = None):
        """Reset the window title according to the file name being processed"""
        if filename is None or len(filename) == 0:
            self.setWindowTitle(self.origtitle)
        else:
            filename = string.upper(miscutils.removesuffix(os.path.basename(filename)))
            self.setWindowTitle("Processing - " + filename)

    def updateUI(self):
        hascl = self.currentlist is not None
        saveable = hascl and self.currentlist.is_complete()
        needssaving = saveable and self.dirty_either()
        reloadable = hascl and self.sinf is not None and self.sinf.is_complete()
        self.action_select_observation_directory.setEnabled(hascl)
        self.action_select_observation_times_file.setEnabled(hascl)
        self.action_save_info.setEnabled(needssaving)
        self.action_save_info_as.setEnabled(saveable)
        self.action_reload_control.setEnabled(reloadable)
        self.action_reload_ranges.setEnabled(reloadable)
        self.action_X_scaling_and_offsets.setEnabled(saveable)
        self.action_Y_scaling_and_offsets.setEnabled(saveable)
        self.action_tune_ranges.setEnabled(saveable)

    def dirty_either(self):
        """True if anything needs saving"""
        return self.dirty_ctrlfile() or self.dirty_rangefile()

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
        if QMessageBox.question(self, "Are you sure", "There are unsaved changes in the control data, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes:
            return False
        return True

    def dirty_rangefile(self):
        """Report if range file needs saving."""
        return self.unsavedr

    def ask_dirty_rangefile(self):
        """If range file is dirty, ask before zapping"""
        if not self.dirty_ctrlfile(): return True
        if QMessageBox.question(self, "Are you sure", "There are unsaved changes in the range data, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes:
            return False
        return True

    def ask_dirty(self):
        """Ask before proceeding if anything is unsaved"""
        return self.ask_dirty_ctrlfile() and self.ask_dirty_ctrlfile()

    def set_info_file(self, filename):
        """Set control file up to given file name, possibly from argument or from dialog"""
        try:
            newsinf = specinfo.SpecInfo()
            newsinf.loadfile(filename)
            clist = newsinf.get_ctrlfile()
            rlist = newsinf.get_rangelist()
        except specinfo.SpecInfoError as e:
            QMessageBox.warning(self, "Load file data error", e.args[0])
            return
        self.sinf = newsinf
        self.currentlist = clist
        self.rangelist = rlist
        self.unsavedc = False
        self.unsavedr = False
        self.resetTitle(self.currentlist.dirname)
        self.updateUI()

    def on_action_new_info_file_triggered(self, checked = None):
        if checked is None: return
        if not self.ask_dirty(): return
        self.sinf = None
        self.currentlist = specdatactrl.SpecDataList()
        self.rangelist = datarange.init_default_ranges()
        self.unsavedc = False
        self.unsavedr = False
        self.resetTitle()
        self.updateUI()

    def on_action_select_info_file_triggered(self, checked = None):
        if checked is None: return
        if not self.ask_dirty(): return
        existing = ""
        if self.sinf is not None and self.sinf.filename is not None: existing = self.sinf.filename
        newfile = QFileDialog.getOpenFileName(self, self.tr("Select spectrum info file"), existing, self.tr("Spectrum info files (*." + specinfo.SUFFIX + ")"))
        if len(newfile) == 0: return
        self.set_info_file(str(newfile))

    def on_action_select_observation_directory_triggered(self, checked = None):
        if checked is None: return
        olddir = ""
        if self.currentlist is not None:
            olddir = self.currentlist.dirname
        newdir = QFileDialog.getExistingDirectory(self, self.tr("Select observations directory"), olddir)
        if len(newdir) == 0: return
        newdir = str(newdir)
        if newdir == olddir: return
        if self.currentlist is None:
            self.currentlist = specdatactrl.SpecDataList(newdir)
        else:
            self.currentlist.set_dirname(newdir)
        self.resetTitle((newdir))

    def on_action_select_observation_times_file_triggered(self, checked = None):
        if checked is None: return
        dlg = obsfileseldlg.ObsFileDlg(self)
        if self.currentlist is None:
            dlg.default_fields()
        else:
            if len(self.currentlist.obsfname) > 0 and len(self.currentlist.dirname) > 0:
                dlg.obsfile.setText(os.path.join(self.currentlist.dirname, self.currentlist.obsfname))
            dlg.copyin_specfields(self.currentlist.cols, self.currentlist.spdcols)
        while dlg.exec_():
            obslist, speclist = dlg.extract_fields()
            fname = str(dlg.obsfile.text())
            if len(fname) == 0:
                QMessageBox.warning(self, "No obs file", "No observation file given")
                continue
            if self.currentlist is None:
                fname = os.path.abspath(fname)
            elif not os.path.isabs(fname):
                if len(self.currentlist.dirname) > 0:
                    fname = os.path.join(self.currentlist.dirname, fname)
                else:
                    fname = os.path.abspath(fname)
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

    def on_action_reinit_ranges_triggered(self, checked = None):
        if checked is None: return
        if not self.ask_dirty_rangefile(): return
        self.rangelist = datarange.init_default_ranges()
        self.unsavedr = True
        self.updateUI()

    def on_action_reload_control_triggered(self, checked = None):
        if checked is None: return
        if not self.ask_dirty_ctrlfile(): return
        if not self.sinf or not self.sinf.is_complete(): return
        self.currentlist = self.sinf.get_ctrlfile()
        self.unsavedc = False
        self.updateUI()

    def on_action_reload_ranges_triggered(self, checked = None):
        if checked is None: return
        if not self.ask_dirty_rangefile(): return
        if not self.sinf or not self.sinf.is_complete(): return
        self.rangelist = self.sint.get_rangelist()
        save.unsavedr = False
        self.updateUI()

    def on_action_X_scaling_and_offsets_triggered(self, checked = None):
        if checked is None: return
        if self.currentlist is None:
            QMessageBox.warning(self, "No current obs file", "Please set up an observation times file first")
            return
        dlg = scaleoffdlg.XScaleOffDlg(self)
        dlg.initdata(self.currentlist)
        dlg.exec_()
        self.unsavedc = True
        self.updateUI()

    def on_action_Y_scaling_and_offsets_triggered(self, checked = None):
        if checked is None: return
        if self.currentlist is None:
            QMessageBox.warning(self, "No current obs file", "Please set up an observation times file first")
            return
        dlg = scaleoffdlg.YScaleOffDlg(self)
        dlg.initdata(self.currentlist)
        dlg.exec_()
        self.unsavedc = True
        self.updateUI()

    def on_action_tune_ranges_triggered(self, checked = None):
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
            self.unsavedc = True
            self.unsavedr = True
            self.updateUI()
        dlg.closefigure()

    def ready_to_calc(self):
        if self.currentlist is None:
            QMessageBox.warning(self, "No current obs file", "Please set up an observation times file first")
            return False
        if self.rangelist is None:
            QMessageBox.warning(self, "No current ranges", "Please set up ranges first")
            return False
        return True

    def save_ops(self, filename = None):
        try:
            if self.sinf is None:
                self.sinf = specinfo.SpecInfo()
            self.sinf.set_ctrlfile(self.currentlist)
            self.sinf.set_rangelist(self.rangelist)
            self.sinf.savefile(filename)
            self.unsavedc = False
            self.unsavedr = False
            self.updateUI()
        except specinfo.SpecInfoError as e:
            QMessageBox.warning(self, "File save error", "Cannot save file, error was " + e.args[0])

    def on_action_save_info_triggered(self, checked = None):
        if checked is None: return
        if not self.dirty_either(): return
        if self.sinf is None or not self.sinf.has_file():
            self.on_action_save_info_as_triggered(True)
            return
        self.save_ops()

    def on_action_save_info_as_triggered(self, checked = None):
        if checked is None: return
        if self.currentlist is None or not self.currentlist.is_complete():
            QMessageBox.warning(self, "No observation list", "No observation list set up yet")
            return
        existing = ""
        if self.sinf is not None and self.sinf.filename is not None:
            existing = self.sinf.filename
        fname = QFileDialog.getSaveFileName(self, self.tr("Select save file"), existing, self.tr("Spectral info files (*." + specinfo.SUFFIX + ")"))
        if len(fname) == 0: return
        self.save_ops(miscutils.replacesuffix(str(fname), specinfo.SUFFIX))

    def on_action_options_triggered(self, checked = None):
        global cfg
        if checked is None: return
        dlg = ProgoptsDlg(self)
        dlg.pwidth.setValue(cfg.swidth)
        dlg.pheight.setValue(cfg.sheight)
        if dlg.exec_():
            cfg.swidth = dlg.pwidth.value()
            cfg.sheight = dlg.pheight.value()
            mpplotter.Setdims(width = cfg.swidth, height = cfg.sheight)

    def on_action_quit_triggered(self, checked = None):
        global cfg
        if checked is None: return
        if self.dirty_either() and \
            QMessageBox.question(self, "Unsaved data", "There are unsaved changes, sure you want to quit",
                                 QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes:
            return
        try:
            cdoc, croot = configfile.init_save(CONFIGROOT)
            cfg.save(cdoc, croot)
            configfile.complete_save(cdoc, CONFIGFNAME)
        except configfile.ConfigError as e:
            QMessageBox.warning(self, "Configuration file error", e.args[0])
        QApplication.exit(0)

    def closeEvent(self, event):
        self.on_action_quit_triggered(True)

app = QApplication(sys.argv)
mw = SadminMain()
cfg = SdaminConfig()

# Load up last times config parameters

try:
    dp = configfile.load(fname = CONFIGFNAME, rootname = CONFIGROOT)
    if dp is not None:
        cdoc, croot = dp
        cfg.load(croot)
except configfile.ConfigError as e:
    QMessageBox.warning(mw, "Configuration file error", e.args[0])
except xmlutil.XMLError as e:
    QMessageBox.warning(mw, "Config file XML error", e.args[0])

# Parse arguments

parsearg = argparse.ArgumentParser(description='Spectrum data files admin')
parsearg.add_argument('--infofile', type=str, help='Existing spectrum info file')
parsearg.add_argument('--width', type=float, default=0.0, help='Plotting width display')
parsearg.add_argument('--height', type=float, default=0.0, help='Plotting height display')
res = vars(parsearg.parse_args())
infofile = res['infofile']
if res['width'] >= 2.0:
    cfg.swidth = res['width']
if res['height'] >= 2.0:
    cfg.sheight = res['height']
mpplotter.Setdims(width = cfg.swidth, height = cfg.sheight)

if infofile is not None:
    if not os.path.isfile(infofile):
        infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)
    mw.set_info_file(infofile)
else:
    mw.on_action_new_info_file_triggered(True)
mw.show()
app.exec_()
