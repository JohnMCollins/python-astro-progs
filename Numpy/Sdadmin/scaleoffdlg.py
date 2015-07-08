# Scale and offsets dialog

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path
import math
import copy
import jdate
import simbad

import ui_xrvdlg
import ui_yscaleoffdlg
import ui_xindhvdlg
import ui_yindscaleoffdlg

def test_eps(x):
    """Return true if value is close to zero"""
    return  abs(x) < 1e-10

def nearly_one(x):
    """Return true if value is close to one"""
    return  abs(x - 1.0) < 1e-10

def setup_y_offsets(box, offlist):
    """Set up y offset combo box"""
    # Clear anything that was there before
    while box.count() != 0:
        box.removeItem(box.count() - 1)
    if offlist is None: return
    for off in offlist:
        box.addItem(str(off))
    box.setCurrentIndex(0)

class XRvDlg(QDialog, ui_xrvdlg.Ui_xrvdlg):

    def __init__(self, parent = None):
        super(XRvDlg, self).__init__(parent)
        self.setupUi(self)
        self.specctrl = None

    def initdata(self, slist):
        """Copy in and set up parameters"""
        self.specctrl = slist
        self.objname.setText(slist.objectname)
        nindivs = self.specctrl.count_indiv_x()
        self.xindivnum.setText(str(nindivs))
        if nindivs == 0:
            self.resetindivx.setEnabled(False)
        self.rvcorrect.setValue(slist.rvcorrect)    # Should trigger value changed
        self.dispmaxmin()

    def dispmaxmin(self):
        """Set up display of maximum and minimum"""
        minv, maxv = self.specctrl.getmaxminx()
        self.xmin.setText(str(minv))
        self.xmax.setText(str(maxv))

    def on_rvcorrect_valueChanged(self, v):
        if not isinstance(v, float): return
        self.dispmaxmin()
        self.resetx.setEnabled(v != 0.0)

    def on_resetx_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel wavelength RVs, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.specctrl.reset_x()
        self.rvcorrect.setValue(0.0)

    def on_resetindivx_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel previous X scaling and offsets, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.specctrl.reset_indiv_x()
        self.xindivnum.setText("0")
        self.resetindivx.setEnabled(False)
    
    def on_fetchsimbad_clicked(self, b = None):
        if b is None: return
        objn = string.strip(str(self.objname.text()))
        if len(objn) == 0:
            QMessageBox.warning(self, "No current object name", "Please set up an object name")
            return
        rv = simbad.getrv(objn)
        if rv is None:
            QMessageBox.warning(self, "Cannot locate object", "Cannot find object name " + objn + " RV value in SIMBAD")
            return
        self.rvcorrect.setValue(rv)

class XIndHvDlg(QDialog, ui_xindhvdlg.Ui_xindhvdlg):

    def __init__(self, parent = None):
        super(XIndHvDlg, self).__init__(parent)
        self.setupUi(self)
        self.spectrum = None
        self.clist = None

    def initdata(self, spec, clst):
        """Copy in and set up parameters"""
        self.spectrum = spec
        self.clist = clst
        self.jdate.setText(jdate.display(spec.modjdate))
        self.globalrv.setText("%.6g" % clst.rvcorrect)
        myrv = spec.hvcorrect
        self.hvcorrect.setValue(myrv)

    def dispmaxmin(self, newhv):
        """Set up display of maximum and minimum"""
        minv, maxv = self.spectrum.getmaxminx()
        self.xmin.setText(str(minv))
        self.xmax.setText(str(maxv))
        self.netrv.setText("%.6g" % (self.clist.rvcorrect + newhv/1000.0))

    def on_resetx_clicked(self, b = None):
        if b is None: return
        if QMessageBox.question(self, "Are you sure", "This will cancel HV, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes: return
        self.hvcorrect.setValue(0.0)

    def on_hvcorrect_valueChanged(self, v):
        if not isinstance(v, float): return
        self.spectrum.hvcorrect = v
        self.dispmaxmin(v)

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

