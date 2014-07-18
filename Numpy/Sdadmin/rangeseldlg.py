# Manage parameters dialog

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path
import math
import copy

import mpplotter
import datarange

import ui_rangeseldlg
import ui_newrangedlg

import scaleoffdlg

def rangeadj(lobox, hibox, loadj, hiadj):
    """Adjust range limit spin boxes by given adjustments

    Don't do anything if the result would make the low value >= high value or either below minimum
    or maximum"""

    lomin = lobox.minimum()
    himax = hibox.maximum()
    loval = lobox.value()
    hival = hibox.value()
    nlo = loval + loadj
    nhi = hival + hiadj
    if  nlo < lomin or nhi > himax or nlo >= nhi: return
    if  nlo != loval: lobox.setValue(nlo)
    if  nhi != hival: hibox.setValue(nhi)

def dlg_rangeadj(box):
    """Adjust range in a dialog box, used for new ranges and ranges in main dlg"""
    # Get amount to adjust from Combo Box
    amt = float(box.radjby.currentText())
    lamt = amt
    ramt = -amt
    if box.rzoomout.isChecked():
        lamt = -amt
        ramt = amt
    if box.rzleft.isChecked():
        ramt = 0.0
    elif box.rzright.isChecked():
        lamt = 0.0
    rangeadj(box.srmin, box.srmax, lamt, ramt)

def make_listitem(spectra, colourlist, num):
    """Make a list item widget out of a spectrum structure for display"""
    spectrum = spectra[num]
    jd = "%.4f" % spectrum.modbjdate
    rems = spectrum.remarks
    if rems is not None:
        if spectrum.discount:
           jd += " (" + rems + ")"
        else:
           jd += " " + rems
    jd += " : " + colourlist[num]
    item = QListWidgetItem(jd)
    item.setData(Qt.UserRole, QVariant(num))
    return  item

class NewRangeDlg(QDialog, ui_newrangedlg.Ui_newrangedlg):

    def __init__(self, parent = None):
        super(NewRangeDlg, self).__init__(parent)
        self.setupUi(self)
        self.colourdisp.setScene(QGraphicsScene())
        self.colourdisp.show()

    def on_selcolour_clicked(self, b = None):
        if b is None: return
        nc = QColorDialog.getColor(self.colourdisp.scene().foregroundBrush().color(), self, "Select new colour")
        if not nc.isValid(): return
        self.colourdisp.scene().setForegroundBrush(nc)

    def on_adjrange_clicked(self, b = None):
        if b is None: return
        dlg_rangeadj(self)

colourlist = ('black', 'brown', 'red', 'orange', 'yellow', 'green', 'blue', 'magenta', 'cyan', 'lightgrey')

class Rangeseldlg(QDialog, ui_rangeseldlg.Ui_rangeseldlg):

    def __init__(self, parent = None):
        super(Rangeseldlg, self).__init__(parent)
        self.rangelist = None
        self.specctl = None
        self.colourlist = None
        self.plotter = None
        self.currentrange = None
        self.hangon = False
        self.setupUi(self)
        self.colourdisp.setScene(QGraphicsScene())
        self.colourdisp.show()

    def set_range_limits(self, lowerspin, upperspin, maxmin):
        """Set range spin boxes according to given maximum and minimum range"""

        lowerspin.setMinimum(maxmin.lower)
        upperspin.setMaximum(maxmin.upper)
        lowerspin.setMaximum(maxmin.upper)
        upperspin.setMinimum(maxmin.lower)
        lowerspin.setValue(maxmin.lower)
        upperspin.setValue(maxmin.upper)
        # Set decimals so that 6th sig figure is adjusted
        dec = 5 - math.trunc(math.log10(math.fabs(maxmin.upper)))
        if dec < 0: dec = 0
        ss = 10**-dec
        lowerspin.setDecimals(dec)
        upperspin.setDecimals(dec)
        lowerspin.setSingleStep(ss)
        upperspin.setSingleStep(ss)

    def copyin_ranges(self, rl, spcl):
        """Set up the dialog ranges"""

        self.rangelist = copy.deepcopy(rl)
        self.specctl = spcl
        maxminx, maxminy = self.specctl.getmaxmin()
        self.set_range_limits(self.xrangemin, self.xrangemax, maxminx)
        self.set_range_limits(self.yrangemin, self.yrangemax, maxminy)
        try:
            xr = self.rangelist.getrange("xrange")
            if maxminx.inrange(xr.lower): self.xrangemin.setValue(xr.lower)
            if maxminx.inrange(xr.upper): self.xrangemax.setValue(xr.upper)
            self.selectx.setChecked(not xr.notused)
        except datarange.DataRangeError:
            pass
        try:
            yr = self.rangelist.getrange("yrange")
            if maxminx.inrange(yr.lower): self.yrangemin.setValue(yr.lower)
            if maxminx.inrange(yr.upper): self.yrangemax.setValue(yr.upper)
            self.selecty.setChecked(not yr.notused)
        except datarange.DataRangeError:
            pass

        rlist = self.rangelist.listranges()
        rlist.sort()
        for rnam in rlist:
            if rnam == "xrange" or rnam == "yrange": continue
            r = self.rangelist.getrange(rnam)
            self.editrange.addItem(r.description, QVariant(rnam))

        self.plotter = mpplotter.Plotter(mpplotter.Plotter_options())
        
        self.colourlist = colourlist * ((len(self.specctl.datalist) + len(colourlist) - 1) / len(colourlist))

        for n in xrange(0, len(self.specctl.datalist)):
            self.datafiles.addItem(make_listitem(self.specctl.datalist, self.colourlist, n))

    def make_xrange(self):
        """Generate range structure from X selection fields"""
        return datarange.DataRange(lbound = self.xrangemin.value(), ubound = self.xrangemax.value(), descr = "X axis display range", shortname = "xrange", notused=not self.selectx.isChecked())

    def make_yrange(self):
        """Generate range structure from y selection fields"""
        return datarange.DataRange(lbound = self.yrangemin.value(), ubound = self.yrangemax.value(), descr = "y axis display range", shortname = "yrange", notused=not self.selecty.isChecked())

    def copyout_ranges(self):
        """Copy back the changed ranges to the options

        Actually we don't do much as we operate directly on the ranges
        We just reset X and Y ranges"""

        self.rangelist.setrange(self.make_xrange())
        self.rangelist.setrange(self.make_yrange())
        return self.rangelist

    def on_addnew_clicked(self, b = None):
        if b is None: return
        dlg = NewRangeDlg()
        if self.currentrange is not None:
            dlg.shortname.setText(self.shortname.text() + '_new')
            dlg.rangename.setText(self.currentrange.description + ' new')
            dlg.rinuse.setChecked(self.rinuse.isChecked())
            dlg.srmin.setValue(self.srmin.value())
            dlg.srmax.setValue(self.srmax.value())
            dlg.colourdisp.scene().setForegroundBrush(self.colourdisp.scene().foregroundBrush().color())
        else:
            dlg.shortname.setText("newrange")
            dlg.rangename.setText("New Range")
        while dlg.exec_():
            sname = str(dlg.shortname.text())
            if len(sname) == 0:
                QMessageBox.warning(self, "Range name null", "No short name for range")
                continue
            try:
                r = self.rangelist.getrange(sname)
                QMessageBox.warning(self, "Range name error", "Short name clashes with existing")
                continue
            except datarange.DataRangeError:
                pass
            fname = string.strip(str(dlg.rangename.text()))
            if len(fname) == 0:
                QMessageBox.warning(self, "Range name null", "No name for range")
                continue
            col = dlg.colourdisp.scene().foregroundBrush().color()
            nrange = datarange.DataRange(dlg.srmin.value(), dlg.srmax.value(), fname, sname, col.red(), col.green(), col.blue(), not dlg.rinuse.isChecked())
            try:
                nrange.checkvalid()
            except datarange.DataRangeError as e:
                QMessageBox.warning(self, "Data range error", e.args[0])
                continue
            self.rangelist.setrange(nrange)
            self.editrange.addItem(fname, QVariant(sname))
            self.editrange.setCurrentIndex(self.editrange.count()-1)
            return

    def on_delrange_clicked(self, b = None):
        if b is None or self.currentrange is None: return
        if QMessageBox.question(self, "OK to delete", "Are you sure you mean to delete range '" + self.currentrange.description + "'") != QMessageBox.Ok: return
        self.rangelist.removerange(self.currentrange)
        self.editrange.removeItem(self.editrange.currentIndex())
        self.updateplot()

    def updateplot(self):
        """Revise plot when anything changes"""

        # If we're just setting up, ignore it all
        
        if self.plotter is None:  return

        selected = [ p.data(Qt.UserRole).toInt()[0] for p in self.datafiles.selectedItems() ]
        nsel = len(selected)
        self.editx.setEnabled(nsel == 1)
        self.edity.setEnabled(nsel == 1)
        if nsel == 0: return

        plotlist = [self.specctl.datalist[n] for n in selected]
        clist = [self.colourlist[n] for n in selected]
        try:
            self.plotter.set_xrange(self.make_xrange())
            self.plotter.set_yrange(self.make_yrange())
            for r in self.rangelist.listranges():
                if r == "xrange" or r == "yrange": continue
                self.plotter.set_subrange(self.rangelist.getrange(r))
            self.specctl.loadfiles(plotlist)
            self.plotter.set_plot(plotlist, clist)
            self.warningmsg.setText("")
        except mpplotter.Plotter_error as e:
            self.warningmsg.setText(e.args[0])

    def on_xrangemin_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_xrangemax_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_selectx_stateChanged(self, b = None):
        if b is None: return
        self.updateplot()

    def on_yrangemin_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_yrangemax_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_selecty_stateChanged(self, b = None):
        if b is None: return
        self.updateplot()

    def on_editrange_currentIndexChanged(self, ind):
        """After changing the current range selection.

        Reset range to current thing we are looking at"""

        if not isinstance(ind, int): return
        newr = str(self.editrange.itemData(ind).toString())
        sc = self.colourdisp.scene()
        sc.clear()
        if len(newr) != 0:
            self.currentrange = r = self.rangelist.getrange(newr)
            sc.setForegroundBrush(QColor(r.red, r.green, r.blue))
            self.srmin.setValue(r.lower)
            self.srmax.setValue(r.upper)
            self.rinuse.setChecked(not r.notused)
            self.shortname.setText(r.shortname)
        else:
            self.currentrange = None
            sc.setForegroundBrush(QColor(255, 255, 255))
            self.shortname.setText("")

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
        self.updateplot()

    def on_srmin_valueChanged(self, value):
        if self.currentrange is None: return
        self.currentrange.lower = value
        self.updateplot()

    def on_srmax_valueChanged(self, value):
        if self.currentrange is None: return
        self.currentrange.upper = value
        self.updateplot()

    def on_rinuse_stateChanged(self, b = None):
        if b is None: return
        if self.currentrange is None: return
        self.currentrange.notused = not self.rinuse.isChecked()
        self.updateplot()

    def getxyamounts(self):
        """Get adjustments for X or Y ranges"""
        amt = float(self.adjby.currentText())
        lamt = amt
        ramt = -amt
        if self.zoomout.isChecked():
            lamt = -amt
            ramt = amt
        if self.zleft.isChecked():
            ramt = 0.0
        elif self.zright.isChecked():
            lamt = 0.0
        return (lamt, ramt)      

    def on_adjustx_clicked(self, b = None):
        if b is None: return
        lamt, ramt = self.getxyamounts()
        rangeadj(self.xrangemin, self.xrangemax, lamt, ramt)

    def on_adjusty_clicked(self, b = None):
        if b is None: return
        lamt, ramt = self.getxyamounts()
        rangeadj(self.yrangemin, self.yrangemax, lamt, ramt)

    def on_adjrange_clicked(self, b = None):
        if b is None: return
        dlg_rangeadj(self)

    def on_datafiles_itemSelectionChanged(self):
        if self.hangon: return
        self.updateplot()

    def on_select_all_clicked(self, b = None):
        if b is None: return
        self.hangon = True
        for row in xrange(0, self.datafiles.count()):
            self.datafiles.item(row).setSelected(True)
        self.hangon = False
        self.updateplot()

    def on_select_unmarked_clicked(self, b = None):
        if b is None: return
        self.hangon = True
        for row in xrange(0, self.datafiles.count()):
            item = self.datafiles.item(row)
            specnum = item.data(Qt.UserRole).toInt()[0]
            spec = self.specctl.datalist[specnum]
            item.setSelected(spec.remarks is None or len(spec.remarks) == 0)
        self.hangon = False
        self.updateplot()

    def on_select_unexcluded_clicked(self, b = None):
        if b is None: return
        for row in xrange(0, self.datafiles.count()):
            item = self.datafiles.item(row)
            specnum = item.data(Qt.UserRole).toInt()[0]
            spec = self.specctl.datalist[specnum]
            item.setSelected(not spec.discount)
        self.hangon = False
        self.updateplot()

    def on_editx_clicked(self, b = None):
        if b is None: return
        selected = [ p.data(Qt.UserRole).toInt()[0] for p in self.datafiles.selectedItems() ]
        if len(selected) != 1: return
        spectrum = self.specctl.datalist[selected[0]]
        dlg = scaleoffdlg.XIndScaleOffDlg(self)
        dlg.initdata(copy.deepcopy(spectrum))
        if dlg.exec_():
            spectrum.xscale = dlg.spectrum.xscale
            spectrum.xoffset = dlg.spectrum.xoffset
            # Possibly redisplay line if different

    def on_edity_clicked(self, b = None):
        if b is None: return
        selected = [ p.data(Qt.UserRole).toInt()[0] for p in self.datafiles.selectedItems() ]
        if len(selected) != 1: return
        nsel = selected[0]
        spectrum = self.specctl.datalist[selected[0]]
        dlg = scaleoffdlg.YIndScaleOffDlg(self)
        dlg.initdata(spectrum)
        if dlg.exec_():
            spectrum.yscale = dlg.spectrum.yscale
            spectrum.yoffset = dlg.spectrum.yoffset
            rems = string.strip(str(dlg.remarks.text()))
            disc = dlg.exclude.isChecked()
            if len(rems) == 0:
                rems = None
                disc = False
            if rems != spectrum.remarks or disc != spectrum.discount:
                spectrum.remarks = rems
                spectrum.discount = disc
                self.datafiles.takeItem(nsel)
                self.datafiles.insertItem(nsel, make_listitem(self.specctl.datalist, self.colourlist, nsel))
                self.datafiles.setCurrentRow(nsel)
 
    def closefigure(self):
        if self.plotter is not None:
            self.plotter.close()

