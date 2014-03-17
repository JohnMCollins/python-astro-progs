# Scale and offsets dialog

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path
import math
import copy

import ui_scaleoffdlg

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

class ScaleOffDlg(QDialog, ui_scaleoffdlg.Ui_scaleoffdlg):

    def __init__(self, parent = None):
        super(ScaleOffDlg, self).__init__(parent)
        self.setupUi(self)
        self.xminv = 0.0
        self.xmaxv = 1e9
        self.yminv = 0.0
        self.ymaxv = 1e9
        self.prevxscale = self.prevyscale = 1.0

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
        
   def set_yoffset(self):
        """Reset spin box parameters to something sensible after we've fiddled"""
        lower, upper, step, postdigs = calcscale(self.yminv, self.ymaxv)
        v = self.yoffset.value()
        self.yoffset.setDecimals(postdigs)
        self.yoffset.setRange(lower, upper)
        self.yoffset.setMaximum(upper)
        if not (lower <= v <= upper):
            if lower <= 0.0 <= upper:
                v = 0.0
            else:
                v = lower
            self.yoffset.setValue(v)
        
    def on_xscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xscale.hasFocus(): return
        self.xlogscale.setValue(math.log10(v))
        rescale = v / self.prevxscale
        self.xminv *= rescale
        self.xmaxv *= rescale
        self.set_xoffset()
        self.xmin.setText(str(self.xminv))
        self.xmax.setText(str(self.xmaxv))
        self.prevxscale = v

    def on_yscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.yscale.hasFocus(): return
        self.ylogscale.setValue(math.log10(v))
        rescale = v / self.prevyscale
        self.yminv *= rescale
        self.ymaxv *= rescale
        self.set_yoffset()
        self.ymin.setText(str(self.yminv))
        self.ymax.setText(str(self.ymaxv))
        self.prevyscale = v

    def on_xlogscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.xlogscale.hasFocus(): return
        actscale = 10.0**v
        self.xscale.setValue(actscale)
        rescale = actscale / self.prevxscale
        self.xminv *= rescale
        self.xmaxv *= rescale
        self.set_xoffset()
        self.xmin.setText(str(self.xminv))
        self.xmax.setText(str(self.xmaxv))
        self.prevxscale = actscale

    def on_ylogscale_valueChanged(self, v):
        if not isinstance(v, float): return
        if not self.yscale.hasFocus(): return
        actscale = 10.0**v
        self.yscale.setValue(actscale)
        rescale = actscale / self.prevyscale
        self.yminv *= rescale
        self.ymaxv *= rescale
        self.set_yoffset()
        self.ymin.setText(str(self.yminv))
        self.ymax.setText(str(self.ymaxv))
        self.prevyscale = actscale


