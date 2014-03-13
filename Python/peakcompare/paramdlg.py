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
        self.opts = None
        self.plotter = None
        self.rangesl = None
        self.xr = None
        self.yr = None
        self.currentrange = None
        self.setupUi(self)
        self.colourdisp.setScene(QGraphicsScene())
        self.colourdisp.show()

    def copyin_ranges(self):
        """Set up the dialog ranges from the ranges set in the options"""
        self.doppleradj.setChecked(self.opts.apply_doppler)
        ranges = self.opts.ranges
        self.xr = ranges.getrange("xrange")
        self.yr = ranges.getrange("yrange")
        self.xrangemin.setValue(self.xr.lower)
        self.xrangemax.setValue(self.xr.upper)
        self.yrangemin.setValue(self.yr.lower)
        self.yrangemax.setValue(self.yr.upper)
        self.rangesl = []

        for n, rnam in enumerate(("lpeak", "upeak", "bglower", "bgupper")):
            r = ranges.getrange(rnam)
            self.rangesl.append(r)
            self.editrange.addItem(r.description, QVariant(n))

        self.plotter = plotter.Plotter(self.opts.plotopts)
        for n,id in enumerate(self.indexdata):
            item = QListWidgetItem(id[0])
            item.setData(Qt.UserRole, QVariant(n))
            self.datafiles.addItem(item)


    def copyout_ranges(self):
        """Copy back the changed ranges to the options

        Actually we don't do much as we operate directly on the ranges"""

        self.opts.apply_doppler = self.doppleradj.isChecked()

    def updateplot(self):
        """Revise plot when anything changes"""

        # If we're just setting up, ignore attempts to reset
        
        if self.plotter is None:  return

        plotfiles = []
        try:
            self.plotter.reset()
            self.plotter.set_xrange(self.xr)
            self.plotter.set_yrange(self.yr)
            for r in self.rangesl:
                self.plotter.set_subrange(r)
            for n,pf in enumerate(self.selecteddata):
                tf = os.path.join(self.tempdir, "tf%d" % n)
                self.dfparser.writefile(tf, pf)
                plotfiles.append(tf)
            self.plotter.set_plot(plotfiles)
            self.warningmsg.setText("")
        except datafile.Datafile_error as e:
            self.warningmsg.setText(e.args[0])
            self.plotter.clear()
        except plotter.Plotter_error as e:
            self.warningmsg.setText(e.args[0])
            self.plotter.clear()

    def on_xrangemin_valueChanged(self, value):
        if isinstance(value, QString): return
        self.xr.lower = value
        self.updateplot()

    def on_xrangemax_valueChanged(self, value):
        if isinstance(value, QString): return
        self.xr.upper = value
        self.updateplot()

    def on_yrangemin_valueChanged(self, value):
        if isinstance(value, QString): return
        self.yr.lower = value
        self.updateplot()

    def on_yrangemax_valueChanged(self, value):
        if isinstance(value, QString): return
        self.yr.upper = value
        self.updateplot()

    def on_editrange_currentIndexChanged(self, ind):
        """After changing the current range selection.

        Reset range to current thing we are looking at"""

        if not isinstance(ind, int): return
        newrnum, ok = self.editrange.itemData(ind).toInt()
        sc = self.colourdisp.scene()
        sc.clear()
        if ok:
            self.currentrange = r = self.rangesl[newrnum]
            sc.setForegroundBrush(QColor(r.red, r.green, r.blue))
            self.srmin.setValue(r.lower)
            self.srmax.setValue(r.upper)
        else:
            self.currentrange = None
            sc.setForegroundBrush(QColor(255, 255, 255))

    def on_selcolour_clicked(self, b = None):
        if b is None: return
        if self.currentrange is None: return
        r = self.currentrange
        nc = QColorDialog.getColor(QColor(r.red, r.green, r.blue), self, "Select new colour")
        if not nc.isValid(): return
        r.red = nc.red()
        r.green = nc.green()
        r.blue = nc.blue()
        self.colourdisp.scene().setForegroundBrush(nc)

    def on_srmin_valueChanged(self, value):
        if self.currentrange is None: return
        self.currentrange.lower = value
        self.updateplot()

    def on_srmax_valueChanged(self, value):
        if self.currentrange is None: return
        self.currentrange.upper = value
        self.updateplot()

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
    def on_srlpp1_clicked(self, b = None): self.incdec_range(b, self.srmin, 0.1)
    def on_srlpp5_clicked(self, b = None): self.incdec_range(b, self.srmin, 0.5)
    def on_srlmp1_clicked(self, b = None): self.incdec_range(b, self.srmin, -0.1)
    def on_srlmp5_clicked(self, b = None): self.incdec_range(b, self.srmin, -0.5)
    def on_srupp1_clicked(self, b = None): self.incdec_range(b, self.srmax, 0.1)
    def on_srupp5_clicked(self, b = None): self.incdec_range(b, self.srmax, 0.5)
    def on_srump1_clicked(self, b = None): self.incdec_range(b, self.srmax, -0.1)
    def on_srump5_clicked(self, b = None): self.incdec_range(b, self.srmax, -0.5)
    def on_srbpp1_clicked(self, b = None): self.incdec_both(b, self.srmin, self.srmax, 0.1)
    def on_srbpp5_clicked(self, b = None): self.incdec_both(b, self.srmin, self.srmax, 0.5)
    def on_srbmp1_clicked(self, b = None): self.incdec_both(b, self.srmin, self.srmax, -0.1)
    def on_srbmp5_clicked(self, b = None): self.incdec_both(b, self.srmin, self.srmax, -0.5)


