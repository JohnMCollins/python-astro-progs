# Peak compare dialog stuff

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path

import datafile
import datarange
import xyvalue
import doppler
import integration

import ui_peakcompdlg

class Peakcompdlg(QDialog, ui_peakcompdlg.Ui_peakcompdlg):

    """Class to run batch integration stuff from"""

    def __init__(self, parent = None):
        super(Peakcompdlg, self).__init__(parent)
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
        fname = QFileDialog.getSaveFileName(self, self.tr("Select results file"), dir, self.tr("Results file (*.pkr)"))
        if len(fname) == 0:
            return
        suff = '.pkr'
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

        # Get ranges from options

        try:
            lowerpeak = self.opts.ranges.getrange("lpeak").checkvalid()
            upperpeak = self.opts.ranges.getrange("upeak").checkvalid()
            bglower = self.opts.ranges.getrange("bglower").checkvalid()
            bgupper = self.opts.ranges.getrange("bgupper").checkvalid()
        except datarange.DataRangeError as e:
            QMessageBox.warning(self, "Range problem", e.args[0])
            return

        bg1low = bglower.lower
        bg1high = bglower.upper
        bg2low = bgupper.lower
        bg2high = bgupper.upper

        peak1low = lowerpeak.lower
        peak1high = lowerpeak.upper
        peak2low = upperpeak.lower
        peak2high = upperpeak.upper

        # Do it this way to minimise the subtractions
        
        bgwidth = (bg1high + bg2high) - (bg1low + bg2low)

        peak1width = peak1high - peak1low
        peak2width = peak2high - peak2low

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

                if self.opts.apply_doppler:   xyspecarray = doppler.apply_doppler_xy(xyspecarray, helioc)

                # Get lower background integration, both peaks, upper background

                bglower = integration.integrate(xyspecarray, bg1low, bg1high)
                bgupper = integration.integrate(xyspecarray, bg2low, bg2high)
                peak1 = integration.integrate(xyspecarray, peak1low, peak1high)
                peak2 = integration.integrate(xyspecarray, peak2low, peak2high)

                # Get average background

                averagebg = (bglower + bgupper) / bgwidth

                # Slice that off resulta

                peak1 -= averagebg * peak1width
                peak2 -= averagebg * peak2width

                # Get result as diffence over sum

                peakc = (peak1 - peak2) / (peak1 + peak2)

                # Construct result as jdate, modjdate, peakdata, averagebg

                results.append((jdate, modjdate, peakc, averagebg))

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

