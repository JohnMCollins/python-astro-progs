#! /usr/bin/python

import sys
import os
import os.path
import locale
import cPickle
import argparse

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import plotter
import datarange
import specarray
import rangeseldlg

import ui_rpmain
import ui_configdlg

def hassuffix(st, suff):
    """Return whether string (usually file name) has given suffix"""
    try:
        if st[st.rindex(suff):] == suff: return True
    except ValueError:
        pass
    return False

def init_default_ranges():
    """Create default range set"""
    
    ret = datarange.RangeList()
    ret.setrange(datarange.DataRange(lbound = 6500.0, ubound = 6650.0, descr = "X axis display range", shortname = "xrange", notused=True))
    ret.setrange(datarange.DataRange(lbound = 0.0, ubound = 3.0, descr = "Y axis display range", shortname = "yrange", notused=True))
    ret.setrange(datarange.DataRange(lbound = 6560.3, ubound = 6561.0, descr = "Continuum blue", shortname = "contblue", blue=128))
    ret.setrange(datarange.DataRange(lbound = 6563.0, ubound = 6620.0, descr = "Continuum red", shortname = "contred", red=128))
    ret.setrange(datarange.DataRange(lbound = 6561.46, ubound = 6561.7, descr = "Integration section 1", shortname = "integ1", green=200, blue=200))
    ret.setrange(datarange.DataRange(lbound = 6562.06, ubound = 6562.3, descr = "Integration section 2", shortname = "integ2", red=200, green=200))
    return ret

class Configdlg(QDialog, ui_configdlg.Ui_configdlg):

    def __init__(self, parent = None):
        super(Configdlg, self).__init__(parent)
        self.setupUi(self)

    def on_selrange_clicked(self, b = None):
        if b is None: return
        lastd = os.getcwd()
        csel = str(self.rangefile.text())
        if len(csel) != 0  and  os.path.isabs(csel):
            lastd = os.path.dirname(csel)
        fname = str(QFileDialog.getOpenFileName(self, self.tr("Select range file"), lastd, self.tr("Range file (*.spcr)")))
        if  len(fname) == 0:
            return
        if not hassuffix(fname, ".spcr"):
            fname += ".spcr"
        self.rangefile.setText(fname)

    def on_selspec_clicked(self, b = None):
        if b is None: return
        lastd = os.getcwd()
        csel = str(self.specfile.text())
        if len(csel) != 0  and  os.path.isabs(csel):
            lastd = os.path.dirname(csel)
        fname = str(QFileDialog.getOpenFileName(self, self.tr("Select combined spectrum data file"), lastd, self.tr("Spectrum data file (*.xml *.pick)")))
        if  len(fname) == 0:    return
        self.specfile.setText(fname)

    def on_seltemp_clicked(self, b = None):
        if b is None: return
        lastd = os.getcwd()
        csel = str(self.tempdir.text())
        if len(csel) != 0  and  os.path.isabs(csel):
            lastd = csel
        dname = str(QFileDialog.getExistingDirectory(self, self.tr("Select temp directory"), lastd))
        if  len(dname) != 0:
            self.tempdir.setText(dname)

class RangePickMain(QMainWindow, ui_rpmain.Ui_rpmain):

    def __init__(self):
        super(RangePickMain, self).__init__(None)
        self.rangefile = None
        self.rangelist = None
        self.specfile = None
        self.specdata = None
        self.tempdir = os.getcwd()
        self.gpopts = plotter.Plotter_options()
        self.setupUi(self)

    def set_rangefile(self, fname):
        """Try to set up range file and load data"""
        if os.path.isfile(fname):
            try:
                rangeset = datarange.load_ranges(fname)
            except datarange.DataRangeError as e:
                QMessageBox.warning(self, "Range load error", e.args[0])
                return None
        else:
            if QMessageBox.question(self, "OK to create", "Range file " + fname + " does not exist - create it") != QMessageBox.Ok:
                return None
            rangeset = init_default_ranges()
        return rangeset

    def set_specfile(self, fname):
        """Try to set up spectra file and load data"""
        if hassuffix(fname, '.xml'):
            try:
                doc, root = xmlutil.load_file(fname, "specdata")
                specnode = xmlutil.find_child(root, "speclist")
                Sl = specarray.Specarraylist()
                app.setOverrideCursor(Qt.WaitCursor)
                Sl.load(specnode)
                app.restoreOverrideCursor()
            except xmlutil.XMLError as e:
                QMessageBox.warning(self, "Spectrum file error", e.args[0])
                return False
        else:
            inf = None
            try:
                app.setOverrideCursor(Qt.WaitCursor)
                inf = open(fname)
                Sl = cPickle.load(inf)
                app.restoreOverrideCursor()
            except IOError as e:
                QMessageBox.warning(self, "Spectrum file error", e.args[0])
                return False
            except EOFError:
                QMessageBox.warning(self, "Spectrum file error", "Spectrum file empty")
                return False
            except cPickle.UnpicklingError as e:
                QMessageBox.warning(self, "Spectrum file error", e.args[0])
                return False
            finally:
                if inf is not None:
                    inf.close()
               
        self.specfile = fname
        self.specdata = Sl
        return True
    
    def on_action_Select_files_triggered(self, checked = None):

        global app

        if checked is None: return
        dlg = Configdlg(self)
        if self.rangefile is not None:
            dlg.rangefile.setText(self.rangefile)
        if self.specfile is not None:
            dlg.specfile.setText(self.specfile)
        dlg.tempdir.setText(self.tempdir)
        
        while dlg.exec_():
            rngf = str(dlg.rangefile.text())
            specf = str(dlg.specfile.text())
            tdir = str(dlg.tempdir.text())
            
            if len(tdir) != 0 and not os.path.isdir(tdir):
                QMessageBox.warning(self, "Invalid temp dir", "Could not find temp dir")
                continue
            if len(rngf) == 0:
                QMessageBox.warning(self, "Invalid range file", "No range file given")
                continue
            if not hassuffix(specf, '.xml') and not hassuffix(specf, '.pick'):
                QMessageBox.warning(self, "Invalid spectrum file", "Spectrum file not XML or Pickle format")
                continue
            if not os.path.isfile(specf):
                QMessageBox.warning(self, "Invalid spectrum file", "Spectrum file does note exist")
                continue

            # Load up range first it's quicker if it goes wrong

            rangeset = self.set_rangefile(rngf)
            if  rangeset is None: continue

            # Now load up spectrum data file

            if not self.set_specfile(specf):
                continue
               
            self.rangefile = rngf
            self.tempdir = tdir
            self.rangelist = rangeset
            self.gpopts.setdims(dlg.gpwidth.value(), dlg.gpheight.value())
            return

    def on_action_Tune_Ranges_triggered(self, checked = None):
        if checked is None: return
        
        dlg = rangeseldlg.Rangeseldlg(self)
        dlg.rangefile = self.rangefile
        dlg.rangelist = self.rangelist
        dlg.specfile = self.specfile
        dlg.specdata = self.specdata
        dlg.tempdir = self.tempdir
        dlg.gpopts = self.gpopts
        dlg.copyin_ranges()
        if dlg.exec_():
            dlg.copyout_ranges()
            try:
                datarange.save_ranges(self.rangefile, self.rangelist)
            except datarange.DataRangeError as e:
                QMessageBox.warning(self, "Range file error", e.args[0])
            return

    def on_action_Quit_triggered(self, checked = None):
        if checked is None: return
        QApplication.exit(0)

    def closeEvent(self, event):
        self.on_action_Quit_triggered(True)

app = QApplication(sys.argv)
parsearg = argparse.ArgumentParser(description='Set up ranges directory')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data file')
parsearg.add_argument('--tempdir', type=str, help='Temporary directory')
res = vars(parsearg.parse_args())
rf = res['rangefile']
sf = res['specfile']
tf = res['tempdir']
if rf is None or not hassuffix(rf, ".spcr"):
    rf = None
if sf is None or (not hassuffix(sf, ".xml") and not hassuffix(sf, ".pick") or not os.path.isfile(sf)):
    sf = None
if tf is None or not os.path.isdir(tf):
    tf = None
mw = RangePickMain()
if sf is not None:
    mw.set_specfile(sf)
if rf is not None:
    mw.rangelist = mw.set_rangefile(rf)
    if mw.rangelist is not None:    mw.rangefile = rf
if tf is not None:
    mw.tempdir = tf
mw.show()
os._exit(app.exec_())

