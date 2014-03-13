#! /usr/bin/python

# GUI processing of spectral data

import sys
import os
import os.path
import locale

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import options
import datarange
import datafile
import paramdlg
import peakcompdlg
import dispresdlg

import ui_pkcmain
import ui_configdlg

CONFIG_NAME = "peakcomp"
ROOT_NAME = "peakcomp"

class Configdlg(QDialog, ui_configdlg.Ui_configdlg):

    def __init__(self, parent = None):
        super(Configdlg, self).__init__(parent)
        self.opts = None
        self.setupUi(self)

    def on_selindex_clicked(self, b = None):
        if b is None: return
        lastd = os.getcwd()
        csel = str(self.indexfile.text())
        if len(csel) != 0  and  os.path.isabs(csel):
            lastd = os.path.dirname(csel)
        fname = str(QFileDialog.getOpenFileName(self, self.tr("Select spectrum index file"), lastd, self.tr("Spectrum index file (*.asc)")))
        if  len(fname) != 0:
            self.indexfile.setText(fname)

    def on_seltemp_clicked(self, b = None):
        if b is None: return
        lastd = os.getcwd()
        csel = str(self.tempdir.text())
        if len(csel) != 0  and  os.path.isabs(csel):
            lastd = os.path.dirname(csel)
        dname = str(QFileDialog.getExistingDirectory(self, self.tr("Select temp directory"), lastd))
        if  len(dname) != 0:
            self.tempdir.setText(dname)

class PeakcompMain(QMainWindow, ui_pkcmain.Ui_pkcmain):

    def __init__(self):
        super(PeakcompMain, self).__init__(None)
        self.opts = options.Options()
        self.opts.loadfile(CONFIG_NAME, ROOT_NAME)
        self.indexdata = None
        self.indexparser = datafile.IndexDataFile()
        self.resultsfile = ""
        self.setupUi(self)

    def updateUI(self):
        valid = len(self.opts.indexfile) != 0
        self.action_Parameters.setEnabled(valid)
        self.action_Peak_Comparison.setEnabled(valid)
        self.action_Display_Results.setEnabled(valid)

    def parseindexfile(self, whatfile = None):
        """Parse the index file either when changed or when first loaded.

        If whatfile is None use the index file set otherwise that file"
        Display a message if incorrect.
        Return True if it worked"""

        if whatfile is None: whatfile = self.opts.indexfile
        if len(whatfile) == 0:
            self.indexdata = None
            return True
        try:
            self.indexdata = self.indexparser.parsefile(whatfile)
        except datafile.Datafile_error as e:
            QMessageBox.warning(self, "Datafile parse error", e.args[0] + "\nline " + str(e.linenumber) + "\ncolumn " + str(e.colnumber))
            return False
        return True

    def on_action_Configuration_triggered(self, checked = None):
        if checked is None: return
        dlg = Configdlg(self)
        dlg.indexfile.setText(self.opts.indexfile)
        dlg.tempdir.setText(self.opts.tempdir)
        dlg.gpwidth.setValue(self.opts.plotopts.width)
        dlg.gpheight.setValue(self.opts.plotopts.height)
        while dlg.exec_():
            indf = str(dlg.indexfile.text())
            tdir = str(dlg.tempdir.text())
            if len(tdir) != 0 and not os.path.isdir(tdir):
                QMessageBox.warning(self, "Invalid temp dir", "Could not find temp dir")
                continue
            if len(indf) != 0:
                if not os.path.isfile(indf):
                    QMessageBox.warning(self, "Invalid index file", "Could not find index file")
                    continue
                if not self.parseindexfile(indf): continue
            self.opts.indexfile = indf
            self.opts.tempdir = tdir
            self.opts.plotopts.setdims(dlg.gpwidth.value(), dlg.gpheight.value())
            self.updateUI()
            return

    def on_action_Parameters_triggered(self, checked = None):
        if checked is None: return
        dlg = paramdlg.Paramdlg(self)
        dlg.opts = self.opts
        dlg.indexdata = self.indexdata
        dlg.indexdir = os.path.dirname(self.opts.indexfile)
        dlg.tempdir = self.opts.tempdir
        try:
            dlg.copyin_ranges()
        except datarange.DataRangeError as e:
            QMessageBox.warning(self, "Range set error", e.args[0])
            return
        if dlg.exec_():
            dlg.copyout_ranges()

    def on_action_Peak_Comparison_triggered(self, checked = None):
        if checked is None: return
        dlg = peakcompdlg.Peakcompdlg(self)
        dlg.destfile.setText(self.resultsfile)
        dlg.opts = self.opts
        dlg.indexdata = self.indexdata
        if dlg.exec_():
            rf = str(dlg.destfile.text())
            if len(rf) != 0:
                self.resultsfile = rf

    def on_action_Display_Results_triggered(self, checked = None):
        if checked is None: return
        dlg = dispresdlg.Dispresdlg(self)
        dlg.opts = self.opts
        dlg.resfile.setText(self.resultsfile)
        if len(self.resultsfile) != 0 and os.path.isfile(self.resultsfile):
            dlg.resfile.setText(self.resultsfile)
        if dlg.exec_():
            self.resultsfile = str(dlg.resfile.text())

    def on_action_Quit_triggered(self, checked = None):
        if checked is None: return
        try:
            self.opts.savefile(CONFIG_NAME, ROOT_NAME)
        except options.OptError as e:
            QMessageBox.warning(self, "Save config error", "Could not save config file - " + e.args[0])
        QApplication.exit(0)

    def closeEvent(self, event):
        self.on_action_Quit_triggered(True)

app = QApplication(sys.argv)
mw = PeakcompMain()
if not mw.parseindexfile():
    mw.opts.indexfile = ""
mw.updateUI()
mw.show()
os._exit(app.exec_())

