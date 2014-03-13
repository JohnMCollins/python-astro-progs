# Manage parameters dialog

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path

import datafile
import doppler
import plotter

import ui_paramdlg

class Paramdlg(QDialog, ui_paramdlg.Ui_paramdlg):

    def __init__(self, parent = None):
        super(Paramdlg, self).__init__(parent)
        self.indexdata = None
        self.indexdir = os.getcwd()
        self.tempdir = os.getcwd()
        self.selected = []
        self.selecteddata = []
        self.dfparser = datafile.SpecDataFile()
        self.plotter = None
        self.setupUi(self)

    def copyin_options(self, mw):
        """Copy options from options structure and parsed index data"""
        opts = mw.opts
        self.plotter = plotter.Plotter(opts)
        self.xrangemin.setValue(opts.xrange.lower)
        self.xrangemax.setValue(opts.xrange.upper)
        self.yrangemin.setValue(opts.yrange.lower)
        self.yrangemax.setValue(opts.yrange.upper)
        self.bgintmin.setValue(opts.intparams.background.lower)
        self.bgintmax.setValue(opts.intparams.background.upper)
        self.halphamin.setValue(opts.intparams.peak.lower)
        self.halphamax.setValue(opts.intparams.peak.upper)
        self.doppleradj.setChecked(opts.intparams.apply_doppler)
        if len(opts.indexfile) != 0:
            self.indexdir = os.path.dirname(opts.indexfile)
        self.indexdata = mw.indexdata
        if len(opts.tempdir) != 0:  self.tempdir = opts.tempdir
        if mw.indexdata is None: return
        for n,id in enumerate(mw.indexdata):
            item = QListWidgetItem(id[0])
            item.setData(Qt.UserRole, QVariant(n))
            self.datafiles.addItem(item)

    def copyout_options(self, mw):
        """Copy back set parameters to options"""
        opts = mw.opts
        opts.xrange.lower = self.xrangemin.value()
        opts.xrange.upper = self.xrangemax.value()
        opts.yrange.lower = self.yrangemin.value()
        opts.yrange.upper = self.yrangemax.value()
        opts.intparams.background.lower = self.bgintmin.value()
        opts.intparams.background.upper = self.bgintmax.value()
        opts.intparams.peak.lower = self.halphamin.value()
        opts.intparams.peak.upper = self.halphamax.value()
        opts.intparams.apply_doppler = self.doppleradj.isChecked()

    def updateplot(self):
        """Revise plot when anything changes"""
        plotfiles = []
        try:
            self.plotter.reset()
            self.plotter.set_xrange(self.xrangemin.value(), self.xrangemax.value())
            self.plotter.set_yrange(self.yrangemin.value(), self.yrangemax.value())
            self.plotter.set_bgirange(self.bgintmin.value(), self.bgintmax.value())
            self.plotter.set_pkrange(self.halphamin.value(), self.halphamax.value())
            for n,pf in enumerate(self.selecteddata):
                tf = os.path.join(self.tempdir, "tf%d" % n)
                self.dfparser.writefile(tf, pf)
                plotfiles.append(tf)
            self.plotter.set_plot(plotfiles)
        except datafile.Datafile_error as e:
            self.warningmsg.setText(e.args[0])
            self.plotter.clear()
        except plotter.Plotter_error as e:
            self.warningmsg.setText(e.args[0])
            self.plotter.clear()

    def on_xrangemin_valueChanged(self, value): self.updateplot()
    def on_xrangemax_valueChanged(self, value): self.updateplot()
    def on_yrangemin_valueChanged(self, value): self.updateplot()
    def on_yrangemax_valueChanged(self, value): self.updateplot()
    def on_bgintmin_valueChanged(self, value): self.updateplot()
    def on_bgintmax_valueChanged(self, value): self.updateplot()
    def on_halphamin_valueChanged(self, value): self.updateplot()
    def on_halphamax_valueChanged(self, value): self.updateplot()

    def read_files(self):
        """Read and build selected data 3-D matrix of data points.

        Apply Doppler adjustment if set.
        We have to do this if we change the Doppler adjust state"""

        self.selecteddata = []
        try:
            for itemnum in self.selected:
                dfileent = self.indexdata[itemnum]
                fname = dfileent[0]
                if not os.path.isabs(fname): fname = os.path.join(self.indexdir, fname)
                ddata = self.dfparser.parsefile(fname)
                if self.doppleradj.isChecked(): ddata = doppler.apply_doppler_array(ddata, dfileent[3])
                self.selecteddata.append(ddata)
            self.warningmsg.setText("")
        except datafile.Datafile_error as e:
            self.warningmsg.setText(e.args[0] + " file " + e.filename + " line " + e.linenumber + " col " + e.colnumber)
            self.selected = []
            self.selecteddata = []

    def on_doppleradj_stateChanged(self, b = None):
        if b is None: return
        self.read_files()
        self.updateplot()

    def incdec_range(self, b, fld, amt):
        if b is None: return
        cval = fld.value()
        nval = cval + amt
        if nval > fld.maximum(): nval = fld.maximum()
        elif nval < fld.minimum(): nval = fld.minimum()
        if nval != cval: fld.setValue(nval)

    def incdec_both(self, b, lfld, ufld, amt):
        self.incdec_range(b, lfld, -amt)
        self.incdec_range(b, ufld, amt)

    def on_datafiles_itemSelectionChanged(self, b = None):
        self.selected = [ p.data(Qt.UserRole).toInt()[0] for p in self.datafiles.selectedItems() ]
        self.read_files()        
        self.updateplot()
 
    def on_rlpp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, 0.1)
    def on_rlpp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, 0.5)
    def on_rlmp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, -0.1)
    def on_rlmp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, -0.5)
    def on_rupp1_clicked(self, b = None): self.incdec_range(b, self.xrangemax, 0.1)
    def on_rupp5_clicked(self, b = None): self.incdec_range(b, self.xrangemax, 0.5)
    def on_rump1_clicked(self, b = None): self.incdec_range(b, self.xrangemax, -0.1)
    def on_rump5_clicked(self, b = None): self.incdec_range(b, self.xrangemax, -0.5)
    def on_rbpp1_clicked(self, b = None): self.incdec_both(b, self.xrangemin, self.xrangemax, 0.1)
    def on_rbpp5_clicked(self, b = None): self.incdec_both(b, self.xrangemin, self.xrangemax, 0.5)
    def on_rbmp1_clicked(self, b = None): self.incdec_both(b, self.xrangemin, self.xrangemax, -0.1)
    def on_rbmp5_clicked(self, b = None): self.incdec_both(b, self.xrangemin, self.xrangemax, -0.5)
    def on_bgilpp1_clicked(self, b = None): self.incdec_range(b, self.bgintmin, 0.1)
    def on_bgilpp5_clicked(self, b = None): self.incdec_range(b, self.bgintmin, 0.5)
    def on_bgilmp1_clicked(self, b = None): self.incdec_range(b, self.bgintmin, -0.1)
    def on_bgilmp5_clicked(self, b = None): self.incdec_range(b, self.bgintmin, -0.5)
    def on_bgiupp1_clicked(self, b = None): self.incdec_range(b, self.bgintmax, 0.1)
    def on_bgiupp5_clicked(self, b = None): self.incdec_range(b, self.bgintmax, 0.5)
    def on_bgiump1_clicked(self, b = None): self.incdec_range(b, self.bgintmax, -0.1)
    def on_bgiump5_clicked(self, b = None): self.incdec_range(b, self.bgintmax, -0.5)
    def on_bgibpp1_clicked(self, b = None): self.incdec_both(b, self.bgintmin, self.bgintmax, 0.1)
    def on_bgibpp5_clicked(self, b = None): self.incdec_both(b, self.bgintmin, self.bgintmax, 0.5)
    def on_bgibmp1_clicked(self, b = None): self.incdec_both(b, self.bgintmin, self.bgintmax, -0.1)
    def on_bgibmp5_clicked(self, b = None): self.incdec_both(b, self.bgintmin, self.bgintmax, -0.5)
    def on_halpp1_clicked(self, b = None): self.incdec_range(b, self.halphamin, 0.1)
    def on_halpp5_clicked(self, b = None): self.incdec_range(b, self.halphamin, 0.5)
    def on_halmp1_clicked(self, b = None): self.incdec_range(b, self.halphamin, -0.1)
    def on_halmp5_clicked(self, b = None): self.incdec_range(b, self.halphamin, -0.5)
    def on_haupp1_clicked(self, b = None): self.incdec_range(b, self.halphamax, 0.1)
    def on_haupp5_clicked(self, b = None): self.incdec_range(b, self.halphamax, 0.5)
    def on_haump1_clicked(self, b = None): self.incdec_range(b, self.halphamax, -0.1)
    def on_haump5_clicked(self, b = None): self.incdec_range(b, self.halphamax, -0.5)
    def on_habpp1_clicked(self, b = None): self.incdec_both(b, self.halphamin, self.halphamax, 0.1)
    def on_habpp5_clicked(self, b = None): self.incdec_both(b, self.halphamin, self.halphamax, 0.5)
    def on_habmp1_clicked(self, b = None): self.incdec_both(b, self.halphamin, self.halphamax, -0.1)
    def on_habmp5_clicked(self, b = None): self.incdec_both(b, self.halphamin, self.halphamax, -0.5)

