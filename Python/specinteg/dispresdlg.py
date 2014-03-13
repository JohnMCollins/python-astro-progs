# Display results dialog

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path

import datafile
import plotter

import ui_dispresdlg

class Dispresdlg(QDialog, ui_dispresdlg.Ui_dispresdlg):

    def __init__(self, parent = None):
        super(Dispresdlg, self).__init__(parent)
        if  parent:
            self.opts = parent.opts
        self.setupUi(self)

    def on_selresfile_clicked(self, b = None):
        if b is None: return
        workdir = str(self.resfile.text())
        if len(workdir) == 0:
            workdir = os.getcwd()
        else:
            workdir = os.path.dirname(workdir)
        fname = QFileDialog.getOpenFileName(self, self.tr("Select result file"), workdir, self.tr("Results file (*.spr)"))
        if  len(fname) == 0: return
        self.resfile.setText(fname)

    def on_display_clicked(self, b = None):
        if b is None: return
        fname = str(self.resfile.text())
        if len(fname) == 0:
            QMessageBox.warning(self, "No results file", "Results file not specified")
            return
        if not os.path.isfile(fname):
            QMessageBox.warning(self, "Cannot open results file", "Results file does not exist")
            return

        # Load up the results file

        parser = datafile.IntResult()
        try:
            resultdata = parser.parsefile(fname)
        except datafile.Datafile_error as e:
            QMessageBox.warning(self, "Results file error", "Results file parse reported error " + e.args[0])
            return

        # Now split the data into days

        sepdays = self.sepdays.value()
        resetting = self.resetx.isChecked()

        dayparts = []
        cpart = []
        previous_time = starting_time = resultdata[0][1]
        for line in resultdata:
            jdate, modjdate, integvalue, bg = line
            basedate = modjdate
            if int(modjdate - previous_time) >= sepdays:
                dayparts.append((starting_time, cpart))
                cpart = []
                starting_time = modjdate
            if resetting: basedate -= starting_time
            cpart.append((basedate, integvalue))
            previous_time = modjdate

        # Remember to slap on any pending stuff

        if len(cpart) != 0:
            dayparts.append((starting_time, cpart))

        # Create an output file for each part based on the starting time

        tdir = self.opts.tempdir
        prefix = os.path.join(tdir, "df")
        output_files = []
        output_parser = datafile.DispResult()
        try:
            for n, part in enumerate(dayparts):
                starting_time, rdata = part
                fname = "%s:%.3d" % (prefix, n)
                output_parser.writefile(fname, rdata)
                output_files.append((fname, starting_time))
        except datafile.Datafile_error as e:
            QMessageBox.warning(self, "Display file error", "Display result reported error " + e.args[0])
            return            
        pl = plotter.Resultplot(self.opts)
        pl.display(output_files)
        QMessageBox.information(self, "Results ready", "Results should now be displayed")

