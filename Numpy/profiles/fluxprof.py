#! /usr/bin/env python

import sys
import math
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
import matplotlib.pyplot as plt
sys.ps1 = 'FRED'            # Mystery stuff to make interactive work
import matplotlib
matplotlib.use('Qt4agg')
matplotlib.interactive(True)
plt.ion()

import ui_fluxprofdlgui

Gaussdiv = 2.0 * math.sqrt(2.0 * math.log(2.0))
Lorentzdiv = 2.0 * math.sqrt(2.0)

def calcgauss(xvals, offset, scale, fhwm):
    """Calculate Gaussian profile"""
    sigma = fhwm / Gaussdiv
    return  scale * np.exp(-0.5 * ((xvals - offset) / sigma)**2)

def calclorentz(xvals, offset, scale, fhwm):
    """Calculate Lorentzian profile"""
    sigma = fhwm / Lorentzdiv
    return  scale / (1.0 + 0.5 * ((offset - xvals) / sigma) ** 2)

class fluxprofdlg(QDialog, ui_fluxprofdlgui.Ui_fluxprofdlg):

    def __init__(self, parent = None):
        super(fluxprofdlg, self).__init__(parent)
        self.xvals = None
        self.yvals = None
        self.setupUi(self)
    
    def updateplot(self):
        npoints = self.npoints.value()
        pixwidth = self.pixwidth.value()
        lims = pixwidth * npoints
        xvals = np.arange(-lims, lims+pixwidth, pixwidth)
        plt.clf()
        offset = self.offset1.value()
        scale = self.scale1.value()
        fhwm = self.fhwm1.value()
        if self.gauss1.isChecked():
            yvals1 = calcgauss(xvals, offset, scale, fhwm)
        elif self.igauss1.isChecked():
            yvals1 = 1.0 - calcgauss(xvals, offset, scale, fhwm)
        elif self.lorentz1.isChecked():
            yvals1 = calclorentz(xvals, offset, scale, fhwm)
        else:
            yvals1 = 1.0 - calclorentz(xvals, offset, scale, fhwm)
        if self.none2.isChecked():
            yvals = yvals1
        else:
            offset = self.offset2.value()
            scale = self.scale2.value()
            fhwm = self.fhwm2.value()
            if self.gauss2.isChecked():
                yvals2 = calcgauss(xvals, offset, scale, fhwm)
            elif self.igauss2.isChecked():
                yvals2 = 1.0 - calcgauss(xvals, offset, scale, fhwm)
            elif self.lorentz2.isChecked():
                yvals2 = calclorentz(xvals, offset, scale, fhwm)
            else:
                yvals2 = 1.0 - calclorentz(xvals, offset, scale, fhwm)
            yvals = yvals1 + yvals2 - 1.0
        if self.clipy.isChecked():
            yvals[yvals > 1.0] = 1.0
            yvals[yvals < 0.0] = 0.0
        elif self.scaley.isChecked():
            miny = np.min(yvals)
            if miny < 0.0:
                yvals -= miny
            yvals /= np.max(yvals)
        plt.xlabel('Wavelength offset')
        plt.ylabel("Relative Intensity")
        plt.plot(xvals, yvals)
        self.xvals = xvals
        self.yvals = yvals
    
    def on_npoints_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()
    
    def on_noadj_toggled(self, st):
        if st: self.updateplot(
                               )
    def on_clipy_toggled(self, st):
        if st: self.updateplot()
    
    def on_scaley_toggled(self, st):
        if st: self.updateplot()
    
    def on_pixwidth_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()
    
    def on_gauss1_toggled(self, st):
        if st: self.updateplot()
    
    def on_lorentz1_toggled(self, st):
        if st: self.updateplot()
    
    def on_igauss1_toggled(self, st):
        if st: self.updateplot()
    
    def on_ilorentz1_toggled(self, st):
        if st: self.updateplot()
    
    def on_none2_toggled(self, st):
        self.scale2.setEnabled(not st)
        self.offset2.setEnabled(not st)
        self.fhwm2.setEnabled(not st)
        if st: self.updateplot()

    def on_gauss2_toggled(self, st):
        if st: self.updateplot()
    
    def on_lorentz2_toggled(self, st):
        if st: self.updateplot()
    
    def on_igauss2_toggled(self, st):
        if st: self.updateplot()
    
    def on_ilorentz2_toggled(self, st):
        if st: self.updateplot()

    def on_scale1_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()
    
    def on_scale2_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_offset1_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()
    
    def on_offset2_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_fhwm1_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()
    
    def on_fhwm2_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()
    
    def on_chooserfile_clicked(self, b = None):
        if b is None: return
        fname = QFileDialog.getSaveFileName(self, self.tr("Select save file"), self.rfile.text())
        if len(fname) == 0: return
        self.rfile.setText(fname)

app = QApplication(sys.argv)

dlg = fluxprofdlg()
dlg.updateplot()

while dlg.exec_():
    outfile = str(dlg.rfile.text())
    if len(outfile) == 0:
        QMessageBox.warning(dlg, "No output file", "Please specify output file")
        continue
    yv = dlg.yvals
    mv = np.min(yv)
    if mv <= 0:
        adj = max(-mv, 1.0)
        yv += adj
    arr = np.array([dlg.xvals,yv])
    arr = np.transpose(arr)
    np.savetxt(outfile, arr, "%.2f %.6f")
    sys.exit(0)
sys.exit(100)
