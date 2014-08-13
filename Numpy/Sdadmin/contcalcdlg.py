# Calculate continuum dialog and processing

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path
import math
import copy

import numpy as np
import scipy.integrate as si
import scipy.optimize as so
import matplotlib.pyplot as plt

import specdatactrl

import ui_contcalcdlg
import ui_contcalcresdlg

import rangeapply

class intresult(object):
    """Record integration results"""

    def __init__(self, da):
        self.dataarray = da
        self.yoffsets = None
        self.yscale = 1.0

# Maybe put this in a file somewhere, it's the same as in rangseldlg

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

class ContCalcResDlg(QDialog, ui_contcalcresdlg.Ui_contcalcresdlg):

    def __init__(self, parent = None):
        super(ContCalcResDlg, self).__init__(parent)
        self.setupUi(self)
        self.settingup = True
        self.applied = False
        self.data = None
        self.calccoeffs = None
        self.lowstd = 0.0
        self.upstd = 0.0
        self.refwl = 0.0
        fig = plt.gcf()
        fig.canvas.set_window_title('X/Y values versus continuum polynomial')

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

    def init_data(self, ctrlfile):
        """Initialise data list in dlg"""
        self.data = ctrlfile.datalist
        self.refwl = ctrlfile.refwavelength
        xr, yr = ctrlfile.getmaxmin()
        self.set_range_limits(self.xrangemin, self.xrangemax, xr)
        self.set_range_limits(self.yrangemin, self.yrangemax, yr)
        for spectrum in self.data:
            jd = "%.4f" % spectrum.modbjdate
            rems = spectrum.remarks
            if rems is not None:
                if spectrum.discount:
                    jd += " (" + rems + ")"
                else:
                    jd += " " + rems
            self.datafiles.addItem(QListWidgetItem(jd))

    def on_applychanges_clicked(self, b = None):
        if b is None: return
        # Run "accept" to exit dialog box but set applied so caller knows it's "apply changes" not OK
        self.applied = True
        self.accept()

    def updateplot(self):
        """Revise plot when anything changes"""

        # If we're just setting up, ignore it all
        
        if self.settingup: return
        plt.clf()

        # Limit ranges or put dashed lines in where limit would go.

        minx = self.xrangemin.value()
        maxx = self.xrangemax.value()
        miny = self.yrangemin.value()
        maxy = self.yrangemax.value()
        if self.selectx.isChecked():
            plt.xlim(minx, maxx)
        else:
            plt.axvline(x=minx, color="black", ls="--")
            plt.axvline(x=maxx, color="black", ls="--")
            minx = self.xrangemin.minimum()
            maxx = self.xrangemax.maximum()
        if self.selecty.isChecked():
            plt.ylim(miny, maxy)
        else:
            plt.axhline(y=miny, color="black", ls="--")
            plt.axhline(y=maxy, color="black", ls="--")

        plt.xlabel('Wavelength (Ang)')
        plt.ylabel('Unnormalised intensity')

        # Plot the selected spectrum

        selected = self.data[self.datafiles.currentRow()]
        plt.plot(selected.get_xvalues(), selected.get_yvalues(), color='b', label='Selected spectrum')

        # Plot the fitted polynomial

        pxv = np.linspace(minx, maxx, 300)
        relpv = pxv - self.refwl
        pyv = np.polyval(self.calccoeffs, relpv)
        plt.plot(pxv, pyv, color='g', label='Fitted polynomial')
        
        # Put in std devs

        plt.plot(pxv, pyv + self.lowstd, color='g', ls=':', label='Lower lim')              # lowstd is -ve
        plt.plot(pxv, pyv + self.upstd, color='g', ls=':', label='Upper lim')
        plt.legend()
        plt.show()

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

    def on_adjustx_clicked(self, b = None):
        if b is None: return
        lamt, ramt = self.getxyamounts()
        rangeadj(self.xrangemin, self.xrangemax, lamt, ramt)

    def on_adjusty_clicked(self, b = None):
        if b is None: return
        lamt, ramt = self.getxyamounts()
        rangeadj(self.yrangemin, self.yrangemax, lamt, ramt)

    def on_datafiles_itemSelectionChanged(self):
        self.updateplot()

class ContCalcDlg(QDialog, ui_contcalcdlg.Ui_contcalcdlg):

    def __init__(self, parent = None):
        super(ContCalcDlg, self).__init__(parent)
        self.setupUi(self)
        self.ismain = True

    def on_entirespec_stateChanged(self, st):
        enab = st != Qt.Checked
        self.inclrange1.setEnabled(enab)
        self.inclrange2.setEnabled(enab)
        self.inclrange3.setEnabled(enab)

    def set_combos(self, name, descr):
        """Initialise all the combo boxes"""
        self.inclrange1.addItem(descr, QVariant(name))
        self.inclrange2.addItem(descr, QVariant(name))
        self.inclrange3.addItem(descr, QVariant(name))
        self.exclrange1.addItem(descr, QVariant(name))
        self.exclrange2.addItem(descr, QVariant(name))

    def initranges(self, rangefile):
        """Initialise range combo boxes"""
        rlist = rangefile.listranges()
        rlist.sort()
        self.set_combos("", "(None)")
        for rnam in rlist:
            if rnam == "yrange": continue
            r = rangefile.getrange(rnam)
            self.set_combos(rnam, r.description)

    def getrangename(self, box):
        """Get range name from given combo box"""
        selex = box.currentIndex()
        if selex <= 0: return None
        return str(box.itemData(selex).toString())

    def getrangelists(self, rangefile):
        """Get tuple (inclranges, exclranges) from completed dlg

        If error, display message and return None"""

        exclist = rangeapply.list_spec_ranges(self, rangefile, self.exclrange1, self.exclrange2)
        if self.entirespec.isChecked():
            inclist = None
        else:
            inclist = rangeapply.list_spec_ranges(self, rangefile, self.inclrange1, self.inclrange2, self.inclrange3)
            if len(inclist) == 0:
                QMessageBox.warning(self, "No valid input range", "No range was valid (probably a bug)")
                return None
        return (inclist, exclist)

    def on_restart_stateChanged(self, st):
        enab = st == Qt.Checked
        enabincl = enab and not self.entirespec.isChecked()
        self.entirespec.setEnabled(enab)
        self.refwavel.setEnabled(enab and self.ismain)
        self.exclrange1.setEnabled(enab)
        self.exclrange2.setEnabled(enab)
        self.inclrange1.setEnabled(enabincl)
        self.inclrange2.setEnabled(enabincl)
        self.inclrange3.setEnabled(enabincl)

def run_continuum_calc(ctrlfile, rangefile):
    """Do the business to calculate the continuum polynomial"""

    # Load up all the data (if not already)

    try:
        ctrlfile.loadfiles()
    except specdatactrl.SpecDataError as e:
        QMessageBox.warning(dlg, "Error loading files", e.args[0])
        return

    dlg = ContCalcDlg()
    dlg.initranges(rangefile)
    dlg.refwavel.setValue(ctrlfile.refwavelength)

    allxvalues = None
    allyvalues = None
    prevexc = None              # Previous values outside range

    while dlg.exec_():

        # First time round, if we've got no values or if the "restart" checkbox is checked, we start from
        # scratch by resetting everything.

        if allxvalues is None or dlg.restart.isChecked():
        
            if not dlg.entirespec.isChecked() and dlg.inclrange1.currentIndex() <= 0 and dlg.inclrange2.currentIndex() <= 0 and dlg.inclrange3.currentIndex() <= 0:
                QMessageBox.warning(dlg, "No range selected", "No range to include selected")
                continue

            # Make a copy of the stuff and obliterate anything we've got already

            copy_ctrlfile = copy.deepcopy(ctrlfile)
            copy_ctrlfile.reset_indiv_y()
            copy_ctrlfile.reset_y()
            copy_ctrlfile.set_yscale(1.0)

            # Get what we're including and excluding

            rls = dlg.getrangelists(rangefile)
            if rls is None: continue
            inclist, exclist = rls
            
            # Get ourselves the values
 
            copy_ctrlfile.refwavelength = dlg.refwavel.value()
            allxvalues, allyvalues = rangeapply.get_all_selected_specdata(copy_ctrlfile, exclist, inclist)
            origvals = len(allxvalues)

            # Sort them into ascending order of X values

            sortind = allxvalues.argsort()
            allxvalues = allxvalues[sortind]
            allyvalues = allyvalues[sortind]

            origxvalues = np.copy(allxvalues)
            origyvalues = np.copy(allyvalues)
 
        # Get rest of parameters from dlg
       
        degree = dlg.degree.value()
        iterations = dlg.iterations.value()
        uprstd = dlg.upperlim.value()
        lwrstd = dlg.lowerlim.value()

        # Repeat for each iteration..

        removals = 0
        stuffed = False

        for itn in xrange(0, iterations):
    
            # Get ourselves the master fitting polynomial
            # First get a revised set of X values as offsets from the ref value

            relx = allxvalues - copy_ctrlfile.refwavelength
            coeffs = np.polyfit(relx, allyvalues, degree)
        
            # Get the Y values corresponding to the polynomial we've fitted

            polyyvalues = np.polyval(coeffs, relx)

            # Get std devs

            diffs = allyvalues - polyyvalues
            stddeviation = diffs.std()
            
            mindiff = - (lwrstd * stddeviation)
            maxdiff = uprstd * stddeviation

            removing = (diffs < mindiff) | (diffs > maxdiff)
            
            # If that didn't do anything, we're done however many iterations we've got to go

            nrem = np.count_nonzero(removing)
            if nrem == 0:
                break

            notremoving = ~ removing
            if np.count_nonzero(notremoving) == 0:
                QMessageBox.warning(dlg, "No data left", "No data left after pruning")
                stuffed = True
                break

            # Prune away the ones we are removing.
            # NB revist to do the same for individual spectra

            allxvalues = allxvalues[notremoving]
            allyvalues = allyvalues[notremoving]

            removals += nrem
        
        if stuffed:
            dlg.restart.setChecked(True)
            continue

        resdlg = ContCalcResDlg(dlg)

        # Put coefficients and what we've done in box

        resdlg.exclpoints.setText("%d/%d" % (removals, origvals))
        if prevexc is None: resdlg.pexclpoints.setText("N/a")
        else: resdlg.pexclpoints.setText(str(prevexc))
        prevexc = removals      

        pwrs = len(coeffs)-1
        for c in coeffs:
            resdlg.coeffs.addItem("%d: %#.8g" % (pwrs, c))
            pwrs -= 1

        # Now add all the stuff for plotting with

        resdlg.init_data(copy_ctrlfile)
        resdlg.calccoeffs = coeffs
        resdlg.lowstd = mindiff
        resdlg.upstd = maxdiff
        resdlg.settingup = False
        resdlg.datafiles.setCurrentRow(0)

        # False return from result dialog means we pressed cancel

        if not resdlg.exec_():
            plt.close()
            return None

        plt.close()

        # Otherwise look at "applied" to see if user pressed "Apply changes"

        if resdlg.applied:
            copy_ctrlfile.set_yoffset(coeffs)
            return copy_ctrlfile

        # Turn off restart which disables things we can't change unless we restart

        dlg.restart.setChecked(False)

        # Now we should be ready to loop again

    # Cancel pressed, return None to say we're not doing anything

    return None

def run_indiv_continuum_calc(ctrlfile, rangefile):
    """Do the business to calculate the continuum polynomial for individual spectra"""

    # If no master polynomial ask the user if he/she didn't mean that first

    if ctrlfile.yoffset is None and QMessageBox.question(None, "Are you sure", "There is no Master Polynomial, are you sure", QMessageBox.Yes, QMessageBox.No|QMessageBox.Default|QMessageBox.Escape) != QMessageBox.Yes:
        return

    # Load up all the data (if not already)

    try:
        ctrlfile.loadfiles()
    except specdatactrl.SpecDataError as e:
        QMessageBox.warning(dlg, "Error loading files", e.args[0])
        return

    dlg = ContCalcDlg()
    dlg.initranges(rangefile)
    dlg.refwavel.setValue(ctrlfile.refwavelength)
    dlg.refwavel.setEnabled(False)
    dlg.ismain = False          # So ref wl doesn't get reenabled

    tries = 0

    while dlg.exec_():

        # First time round, if we've got no values or if the "restart" checkbox is checked, we start from
        # scratch by resetting everything.

        if tries <= 0 or dlg.restart.isChecked():
        
            if not dlg.entirespec.isChecked() and dlg.inclrange1.currentIndex() <= 0 and dlg.inclrange2.currentIndex() <= 0 and dlg.inclrange3.currentIndex() <= 0:
                QMessageBox.warning(dlg, "No range selected", "No range to include selected")
                continue

            # Make a copy of the stuff and obliterate what we've got already
            # We leave alone the master stuff

            copy_ctrlfile = copy.deepcopy(ctrlfile)
            copy_ctrlfile.reset_indiv_y()
            
            # Get what we're including and excluding

            rls = dlg.getrangelists(rangefile)
            if rls is None: continue
            inclist, exclist = rls
            
            prevexcl = None
            
        # Get rest of parameters from dlg
       
        degree = dlg.degree.value()
        iterations = dlg.iterations.value()
        uprstd = dlg.upperlim.value()
        lwrstd = dlg.lowerlim.value()

        # Repeat for each iteration..

        totremovals = 0
        stuffed = False
        
        for dataset in copy_ctrlfile.datalist:
            
            # Grab each spectrum we're not excluding
            
            try:
                xvalues, yvalues = rangeapply.get_selected_specdata(dataset, exclist, inclist)
            except specdatactrl.SpecDataError:
                continue
            
            origxvalues = np.copy(xvalues)
            origyvalues = np.copy(yvalues)
        
            for itn in xrange(0, iterations):
            
                relx = xvalues - copy_ctrlfile.refwavelength
                coeffs = np.polyfit(relx, yvalues, degree)
                
                # Get yvalues corresponding to fitted polynomial
                
                polyyvalues = np.polyval(coeffs, relx)
                diffs = yvalues - polyyvalues
                
                stddeviation = diffs.std()
                
                mindiff = - (lwrstd * stddeviation)
                maxdiff = uprstd * stddeviation

                removing = (diffs < mindiff) | (diffs > maxdiff)
                
                # If that didn't do anything, we're done however many iterations we've got to go

                nrem = np.count_nonzero(removing)
                if nrem == 0: break

                notremoving = ~ removing
                if np.count_nonzero(notremoving) == 0:
                    QMessageBox.warning(dlg, "No data left", "No data left after pruning")
                    stuffed = True
                    break

                # Prune away the ones we are removing.
            
                xvalues = xvalues[notremoving]
                yvalues = yvalues[notremoving]

                totremovals += nrem
            
            if stuffed: break
            

