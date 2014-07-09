# Scale and offsets dialog

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path
import math
import copy

import ui_xscaleoffdlg
import ui_yscaleoffdlg
import ui_xindscaleoffdlg
import ui_yindscaleoffdlg

def test_eps(x):
    """Return true if value is close to zero"""
    return  abs(x) < 1e-10

def nearly_one(x):
    """Return true if value is close to one"""
    return  abs(x - 1.0) < 1e-10

def set_offset_box(box, cvalue, minv, maxv):
    """Set up x offset box

    cvalue is the value to set (use 0.0) if none
    minv and maxv are the current minimum and maximum"""

    predigs = int(math.floor(math.log10(abs(minv-maxv))))
    postdigs = 7 - predigs
    step = 10**(2-postdigs)
    scrange = 10.0**predigs
    mval = max(abs(minv),abs(maxv))
    upper = (math.ceil(mval / scrange) + 1.0) * scrange
    if postdigs < 0: postdigs = 0
    box.setDecimals(postdigs)
    box.setRange(-upper, upper)
    if cvalue is None: cvalue = 0.0
    if not (-upper <= cvalue <= upper):  cvalue = 0.0
    box.setValue(cvalue)

def setup_y_offsets(box, offlist):
    """Set up y offset combo box"""
    # Clear anything that was there before
    while box.count() != 0:
        box.removeItem(box.count() - 1)
    if offlist is None: return
    for off in offlist:
        box.addItem(str(off))
    box.setCurrentIndex(0)

class XScaleOffDlg(QDialog, ui_xscaleoffdlg.Ui_xscaleoffdlg):

    def __init__(self, parent = None):
        super(XScaleOffDlg, self).__init__(parent)
        self.setupUi(self)
        self.specctrl = None

    def initdata(self, slist):
        """Copy in and set up parameters"""
        self.specctrl = slist
        self.dispmaxmin()
        self.setup_xoffset()
        self.setup_xscale()
        nindivs = self.specctrl.count_indiv_x()
        self.xindivnum.setText(str(nindivs))
        if nindivs == 0:
            self.resetindivx.setEnabled(False)

    def dispmaxmin(self):
        """Set up display of maximum and minimum"""
        minv, maxv = self.specctrl.getmaxminx()
        self.xmin.setText(str(minv))
        self.xmax.setText(str(maxv))

    def setup_xoffset(self):
        """Set up x offset box"""
        minv, maxv = self.specctrl.getmaxminx()
        set_offset_box(self.xoffset, self.specctrl.xoffset, minv, maxv)

    def setup_xscale(self):
        """Set up scale boxes

        Note that the value changed routines check for focus so we don't have a cascade"""
        v = self.specctrl.xscale
        if nearly_one(v):
            self.xscale.setValue(1.0)
            self.xscalequot.setValue(1.0)
            self.xlogscale.setValue(0.0)
        else:
            self.xscale.setValue(v)
            self.xscalequot.setValue(1.0/v)
            self.xlogscale.setValue(math.log10(v))
            
    def on_xscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xscale.hasFocus(): return
        self.specctrl.set_xscale(v)
        self.setup_xscale()
        self.dispmaxmin()

    def on_xscalequot_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xscalequot.hasFocus(): return
        self.specctrl.set_xscale(1.0/v)
        self.setup_xscale()
        self.dispmaxmin()

    def on_xlogscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xlogscale.hasFocus(): return
        self.specctrl.set_xscale(10.0**v)
        self.setup_xscale()
        self.dispmaxmin()

    def on_xoffset_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xoffset.hasFocus(): return
        self.specctrl.set_xoffset(v)
        self.dispmaxmin()

    def on_resetx_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel X scaling and offsets, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.specctrl.reset_x()
        self.dispmaxmin()
        self.setup_xoffset()
        self.setup_xscale()        

    def on_resetindivx_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel previous X scaling and offsets, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.specctrl.reset_indiv_x()
        self.xindivnum.setText("0")
        self.resetindivx.setEnabled(False)

class XIndScaleOffDlg(QDialog, ui_xindscaleoffdlg.Ui_xindscaleoffdlg):

    def __init__(self, parent = None):
        super(XIndScaleOffDlg, self).__init__(parent)
        self.setupUi(self)
        self.spectrum = None

    def initdata(self, spec):
        """Copy in and set up parameters"""
        self.spectrum = spec
        self.jdate.setText(str(spec.modbjdate))
        self.dispmaxmin()
        self.setup_xoffset()
        self.setup_xscale()

    def dispmaxmin(self):
        """Set up display of maximum and minimum"""
        minv, maxv = self.spectrum.getmaxminx()
        self.xmin.setText(str(minv))
        self.xmax.setText(str(maxv))

    def setup_xoffset(self):
        """Set up x offset box"""
        minv, maxv = self.spectrum.getmaxminx()
        set_offset_box(self.xoffset, self.spectrum.xoffset, minv, maxv)

    def setup_xscale(self):
        """Set up scale boxes

        Note that the value changed routines check for focus so we don't have a cascade"""
        v = self.spectrum.xscale
        if nearly_one(v):
            self.xscale.setValue(1.0)
            self.xscalequot.setValue(1.0)
            self.xlogscale.setValue(0.0)
        else:
            self.xscale.setValue(v)
            self.xscalequot.setValue(1.0/v)
            self.xlogscale.setValue(math.log10(v))
            
    def on_xscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xscale.hasFocus(): return
        self.spectrum.xscale = v
        self.setup_xscale()
        self.dispmaxmin()

    def on_xscalequot_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xscalequot.hasFocus(): return
        self.spectrum.xscale = 1.0 / v
        self.setup_xscale()
        self.dispmaxmin()

    def on_xlogscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xlogscale.hasFocus(): return
        self.spectrum.xscale = 10.0 ** v
        self.setup_xscale()
        self.dispmaxmin()

    def on_xoffset_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xoffset.hasFocus(): return
        self.spectrum.xoffset = v
        self.dispmaxmin()

    def on_resetx_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel X scaling and offset, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.spectrum.xscale = 1.0
        self.spectrum.xoffset = 0.0
        self.dispmaxmin()
        self.setup_xoffset()
        self.setup_xscale()

class YScaleOffDlg(QDialog, ui_yscaleoffdlg.Ui_yscaleoffdlg):

    def __init__(self, parent = None):
        super(YScaleOffDlg, self).__init__(parent)
        self.setupUi(self)
        self.specctrl = None

    def initdata(self, slist):
        """Copy in and set up parameters"""
        self.specctrl = slist
        self.dispmaxmin()
        self.setup_yoffset()
        self.setup_yscale()
        nindivs = self.specctrl.count_indiv_y()
        self.yindivnum.setText(str(nindivs))
        if nindivs == 0:
            self.resetindivy.setEnabled(False)

    def dispmaxmin(self):
        """Set up display of maximum and minimum"""
        minv, maxv = self.specctrl.getmaxminy()
        self.ymin.setText(str(minv))
        self.ymax.setText(str(maxv))

    def setup_yoffset(self):
        """Set up y offset box"""
        setup_y_offsets(self.offsets, self.specctrl.yoffset)

    def setup_yscale(self):
        """Set up scale boxes

        Note that the value changed routines check for focus so we don't have a cascade"""
        v = self.specctrl.yscale
        if nearly_one(v):
            self.yscale.setValue(1.0)
            self.yscalequot.setValue(1.0)
            self.ylogscale.setValue(0.0)
        else:
            self.yscale.setValue(v)
            self.yscalequot.setValue(1.0/v)
            self.ylogscale.setValue(math.log10(v))
            
    def on_yscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.yscale.hasFocus(): return
        self.specctrl.set_yscale(v)
        self.setup_yscale()
        self.dispmaxmin()

    def on_yscalequot_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.yscalequot.hasFocus(): return
        self.specctrl.set_yscale(1.0/v)
        self.setup_yscale()
        self.dispmaxmin()

    def on_ylogscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.ylogscale.hasFocus(): return
        self.specctrl.set_yscale(10.0**v)
        self.setup_yscale()
        self.dispmaxmin()

    def on_resety_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel y scaling and offsets, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.specctrl.reset_y()
        self.dispmaxmin()
        self.setup_yoffset()
        self.setup_yscale()        

    def on_resetindivy_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel previous y scaling and offsets, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.specctrl.reset_indiv_y()
        self.yindivnum.setText("0")
        self.resetindivy.setEnabled(False)

class YIndScaleOffDlg(QDialog, ui_yindscaleoffdlg.Ui_yindscaleoffdlg):

    def __init__(self, parent = None):
        super(YIndScaleOffDlg, self).__init__(parent)
        self.setupUi(self)
        self.spectrum = None

    def initdata(self, spec):
        """Copy in and set up parameters"""
        self.spectrum = spec
        self.jdate.setText(str(spec.modbjdate))
        if spec.remarks is not None:
            self.remarks.setText(spec.remarks)
        if spec.discount: self.exclude.setChecked(True)
        self.dispmaxmin()
        self.setup_yoffset()
        self.setup_yscale()

    def dispmaxmin(self):
        """Set up display of maximum and minimum"""
        minv, maxv = self.spectrum.getmaxminy()
        self.ymin.setText(str(minv))
        self.ymax.setText(str(maxv))

    def setup_yoffset(self):
        """Set up y offset box"""
        setup_y_offsets(self.offsets, self.spectrum.yoffset)

    def setup_yscale(self):
        """Set up scale boxes

        Note that the value changed routines check for focus so we don't have a cascade"""
        v = self.spectrum.yscale
        if nearly_one(v):
            self.yscale.setValue(1.0)
            self.yscalequot.setValue(1.0)
            self.ylogscale.setValue(0.0)
        else:
            self.yscale.setValue(v)
            self.yscalequot.setValue(1.0/v)
            self.ylogscale.setValue(math.log10(v))
            
    def on_yscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.yscale.hasFocus(): return
        self.spectrum.yscale = v
        self.setup_yscale()
        self.dispmaxmin()

    def on_yscalequot_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.yscalequot.hasFocus(): return
        self.spectrum.yscale = 1.0 / v
        self.setup_yscale()
        self.dispmaxmin()

    def on_ylogscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.ylogscale.hasFocus(): return
        self.spectrum.yscale = 10.0 ** v
        self.setup_yscale()
        self.dispmaxmin()

    def on_resety_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel y scaling and offsets, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.spectrum.yscale = 1.0
        self.spectrum.yoffset = None
        self.dispmaxmin()
        self.setup_yoffset()
        self.setup_yscale()        

