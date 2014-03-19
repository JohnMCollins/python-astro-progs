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

def calcscale(minv, maxv):
    """Calculate minimum and maximum values for offset fields.

    Return (min, max, stepsize, digits)"""

    predigs = int(math.floor(math.log10(abs(minv-maxv))))
    postdigs = 7 - predigs
    step = 10**(2-postdigs)
    scrange = 10.0**predigs
    lower = (math.floor(minv / scrange) - 1.0) * scrange
    upper = (math.ceil(maxv / scrange) + 1.0) * scrange
    if postdigs < 0: postdigs = 0
    return (lower, upper, step, postdigs)

class XScaleOffDlg(QDialog, ui_xscaleoffdlg.Ui_xscaleoffdlg):

    def __init__(self, parent = None):
        super(XScaleOffDlg, self).__init__(parent)
        self.setupUi(self)
        self.xminv = 0.0
        self.xmaxv = 1e9
        self.specctrl = None

    def initmaxmin(self):
        xr, yr = self.specctrl.getmaxmin()
        self.xminv = xr.lower
        self.xmaxv = xr.upper

    def initdata(self, slist):
        """Copy in and set up parameters"""
        self.specctrl = slist
        self.initmaxmin()
        self.set_xoffset()

    def set_xoffset(self):
        """Reset spin box parameters to something sensible after we've fiddled"""
        lower, upper, step, postdigs = calcscale(self.xminv, self.xmaxv)
        v = self.xoffset.value()
        self.xoffset.setDecimals(postdigs)
        self.xoffset.setRange(lower, upper)
        self.xoffset.setMaximum(upper)
        if not (lower <= v <= upper):
            if lower <= 0.0 <= upper:
                v = 0.0
            else:
                v = lower
            self.xoffset.setValue(v)   
        self.xmin.setText(str(self.xminv))
        self.xmax.setText(str(self.xmaxv))
              
    def on_xscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xscale.hasFocus(): return
        self.xscalequot.setValue(1.0/v)
        self.xlogscale.setValue(math.log10(v))
        rescale = v / self.prevxscale
        self.xminv *= rescale
        self.xmaxv *= rescale
        self.set_xoffset()
        self.prevxscale = v

    def on_xscalequot_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xscalequot.hasFocus(): return
        self.xlogscale.setValue(-math.log10(v))
        rescale = v / self.prevxscale
        self.xminv *= rescale
        self.xmaxv *= rescale
        self.set_xoffset()
        self.prevxscale = v

    def on_xlogscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xlogscale.hasFocus(): return
        actscale = 10.0**v
        self.xscale.setValue(actscale)
        self.xscalequot.setValue(1.0/actscale)
        rescale = actscale / self.prevxscale
        self.xminv *= rescale
        self.xmaxv *= rescale
        self.set_xoffset()
        self.prevxscale = actscale

    def on_resetx_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel X scaling and offsets, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.specctrl.reset_x()
        self.initmaxmin()
        self.set_xoffset()

    def on_resetindivx_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel previous X scaling and offsets, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.specctrl.reset_indiv_x()
        self.initmaxmin()
        self.set_xoffset()


