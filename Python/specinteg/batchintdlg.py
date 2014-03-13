# Batch Integration dialog stuff

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path

import datafile
import xyvalue
import doppler
import integration

import ui_batchintdlg

class Batchintdlg(QDialog, ui_batchintdlg.Ui_batchintdlg):

    """Class to run batch integration stuff from"""

    def __init__(self, parent = None):
        super(Batchintdlg, self).__init__(parent)
        self.indexdata = None
        self.opts = None
        self.setupUi(self)

    def on_seldestfile_clicked(self, b = None):
        if b is None: return
        rf = str(self.destfile.text())
        if len(rf) != 0 and os.path.isabs(rf):
            dir = os.path.dirname(rf)
        else:
            dir = os.getcwd()
        fname = QFileDialog.getSaveFileName(self, self.tr("Select results file"), dir, self.tr("Results file (*.spr)"))
        if len(fname) == 0:
            return
        suff = '.spr'
        if len(fname) < len(suff) or fname[-len(suff):] != suff:
            fname += suff
        self.destfile.setText(fname)

    def on_begin_clicked(self, b = None):
        if b is None: return
        if self.opts is None or self.indexdata is None:
            QMessageBox.warning(self, "No parameters", "No parameters set up yet")
            return
        outfile = str(self.destfile.text())
        if len(outfile) == 0:
            QMessageBox.warning(self, "No output file", "please set up a results file")
            return
        if self.opts is None or self.indexdata is None:
            QMessageBox.warning(self, "No parameters", "No parameters set up yet")
            return
        workdir = os.path.dirname(self.opts.indexfile)
        nfiles = len(self.indexdata)
        self.intprogress.setMaximum(len(self.indexdata))
        parser = datafile.SpecDataFile()
        errorfiles = []
        self.begin.setEnabled(False)

        bg1low = self.opts.intparams.background.lower
        rangelow = self.opts.intparams.peak.lower
        rangehigh = self.opts.intparams.peak.upper
        bg2high = self.opts.intparams.background.upper

        bgwidth = (rangelow - bg1low) + (bg2high - rangehigh)
        rangewidth = rangehigh - rangelow

        results = []

        for cfilenum, indentry in enumerate(self.indexdata):
            self.intprogress.setValue(cfilenum)
            try:
                dataf, jdate, modjdate, helioc = indentry
                if not os.path.isabs(dataf):
                    dataf = os.path.join(workdir, dataf)
                specarray = parser.parsefile(dataf)
            
                # Got array, convert to x,y pairs ready for integration

                xyspecarray = xyvalue.convert_to_xy(specarray, 0, 1)

                # Make adjustments for Doppler if required

                if self.opts.intparams.apply_doppler:   xyspecarray = doppler.apply_doppler_xy(xyspecarray, helioc)

                # Get lower background integration, thing itself, upper background

                bglower = integration.integrate(xyspecarray, bg1low, rangelow)
                peakdata = integration.integrate(xyspecarray, rangelow, rangehigh)
                bgupper = integration.integrate(xyspecarray, rangehigh, bg2high)

                # Get average background

                averagebg = (bglower + bgupper) / bgwidth

                # Slice that off result

                peakdata -= averagebg * rangewidth

                # Construct result as jdate, modjdate, peakdata, averagebg

                results.append((jdate, modjdate, peakdata, averagebg))

            except datafile.Datafile_error as e:

                # Cope with data file errors

                errorfiles.append((dataf, e.args[0]))
                results.append((jdate, modjdate, 0.0, 0.0))

            except integration.Integration_error as e:

                # Cope with integration errors

                errorfiles.append((dataf, e.args[0]))
                results.append((jdate, modjdate, 0.0, 0.0))

        # Set progress to 100%

        self.intprogress.setValue(nfiles)

        if len(errorfiles) != 0:
            QMessageBox.warning(self, "Errors in processing", str(len(errorfiles)) + " gave errors in processing")

        try:
            outparser = datafile.IntResult()
            outparser.writefile(outfile, results)
        except datafile.Datafile_error as e:
            QMessageBox.warning(self, "Error writing results", e.args[0])

