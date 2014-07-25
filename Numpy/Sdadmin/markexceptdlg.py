# Mark exceptional data dialog and processing

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

import ui_markexceptdlg
import ui_markexresdlg

class Markexresdlg(QDialog, ui_markexresdlg.Ui_markexresdlg):

    def __init__(self, parent = None):
        super(Markexresdlg, self).__init__(parent)
        self.setupUi(self)
        self.applied = False

    def on_applychanges_clicked(self, b = None):
        if b is None: return
        # Run "accept" to exit dialog box but set applied so caller knows it's "apply changes" not OK
        self.applied = True
        self.accept()

    def on_inclrange_currentIndexChanged(self, ind):
        if not isinstance(ind, int): return
        # Set corresponding value in box
        self.rngav.setText(self.inclrange.itemData(ind).toString())

class Markexceptdlg(QDialog, ui_markexceptdlg.Ui_markexceptdlg):

    def __init__(self, parent = None):
        super(Markexceptdlg, self).__init__(parent)
        self.setupUi(self)

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

class intresult(object):
    """Record integration results indexed by date

    dataarray contains the specdatactrl.SpecDataArray structure with the spectrum we are looking at
    contlist contains the calculated continuum for each of the ranges we are worried about
    (or none if we're looking at the whole range
    totcont gives the total continuum - either the whole range or the total of the ranges we look at
    note gives the generated message for adding in"""

    def __init__(self, da):
        self.dataarray = da
        self.contlist = None
        self.totcont = 0.0
        self.note = None

def list_spec_ranges(dlg, rangefile, *boxes):
    """List specified distinct ranges specified in boxes"""

    bl = set()              # Done as a set to eliminate dups
    for b in boxes:
        rn = dlg.getrangename(b)
        if rn is not None:
            bl.add(rn)
    rl = []
    for b in bl:
        try:
            rl.append(rangefile.getrange(b))
        except datarange.DataRangeError as e:
            QMessageBox.warning(dlg, "Problem loading range", "Could not load range " + b + " error was " + e.args[0])

    rl.sort(lambda a,b: cmp(a.description, b.description))
    return rl

def apply_included_ranges(rangelist, xvalues, yvalues):
    """Apply list of included ranges to xvalues and yvalues.

    Return list of tuples (Xvals,Yvals) for each range"""

    return  [ r.select(xvalues,yvalues) for r in rangelist ]

def apply_excluded_ranges(rangelist, xvalues, yvalues):
    """Apply list of excluded ranges to xvalues and yvalues.

    Return revised list of xvalues and yvalues"""

    for r in rangelist:
        xvalues, yvalues = r.selectnot(xvalues, yvalues)
    return (xvalues, yvalues)

def run_exception_marks(ctrlfile, rangefile):
    """Do the business for marking exceptions

    Return None if we decided not to do anything, otherwise
    a new version of the control file list"""

    dlg = Markexceptdlg()
    dlg.initranges(rangefile)

    doneonce = False

    while dlg.exec_():
        if not dlg.entirespec.isChecked() and dlg.inclrange1.currentIndex() <= 0 and dlg.inclrange2.currentIndex() <= 0 and dlg.inclrange3.currentIndex() <= 0:
            QMessageBox.warning(dlg, "No range selected", "No range to include selected")
            continue

        # Count of pre-existing discounted markers for display at the end

        pre_existing = ctrlfile.count_markers()

        # Make a copy in case we decide not to do anything

        copy_ctrlfile = copy.deepcopy(ctrlfile)

        # Load up all the data (if not already)

        try:
            copy_ctrlfile.loadfiles()
        except specdatactrl.SpecDataError as e:
            QMessageBox.warning(dlg, "Error loading files", e.args[0])
            continue

        # Do any resetting we are doing, remember how many we reset in "ndone".

        ndone = 0
        if dlg.resetmarks.isChecked():
            ndone = copy_ctrlfile.reset_markers()
        elif dlg.clearmarks.isChecked():
            ndone = copy_ctrlfile.clear_remarks()

        # Accumulate Y values to get median

        allyvalues = np.empty((0,),dtype=np.float64)
        resultdict = dict()
        total = 0.0

        # Get ourselves any excluded ranges

        exclist = list_spec_ranges(dlg, rangefile, dlg.exclrange1, dlg.exclrange2)

        # If we are doing the whole list....

        entire = dlg.entirespec.isChecked()
        
        if entire:

            for dataset in copy_ctrlfile.datalist:
                try:
                    xvalues = dataset.get_xvalues(False)
                    yvalues = dataset.get_yvalues(False)
                except specdatactrl.SpecDataError:
                    continue

                # Apply exclusions

                if len(exclist) != 0:
                    xvalues, yvalues = apply_excluded_ranges(exclist, xvalues, yvalues)
            
                # Remember all Y values for median

                allyvalues = np.concatenate((allyvalues, yvalues))

                # Do the sum to get continuum level. We only bother with "totcont"
                # Index by "modbjdate"

                area = si.trapz(yvalues, xvalues)
                width = np.max(xvalues) - np.min(xvalues)
                mv = area / width
                resitem = intresult(dataset)
                resitem.totcont = mv
                resultdict[dataset.modbjdate] = resitem
                total += mv

        else:

            # Applying ranges to include

            inclist = list_spec_ranges(dlg, rangefile, dlg.inclrange1, dlg.inclrange2, dlg.inclrange3)
            if len(inclist) == 0:
                QMessageBox.warning(dlg, "No valid input range", "No range was valid (probably a bug)")
                continue
            
            # Build total of each continuum in "rtotals" corresponding to range

            rtotals = np.zeros(len(inclist))
            
            for dataset in copy_ctrlfile.datalist:      # Each spectrum
                
                try:
                    xvalues = dataset.get_xvalues(False)
                    yvalues = dataset.get_yvalues(False)
                except specdatactrl.SpecDataError:
                    # We just ignore spectra we are already ignoring
                    continue

                # Apply exclusions

                if len(exclist) != 0:
                    xvalues, yvalues = apply_excluded_ranges(exclist, xvalues, yvalues)

                # Extract the continuum ranges from the data to get a list of x values and y values
                # corresponding to each range
                # NB this doesn't worry about possibly overlapping ranges!

                xypairs = apply_included_ranges(inclist, xvalues, yvalues)

                # Keep track of the total area and width we are dealing with and do the division at the end

                totarea = 0.0
                totwidth = 0.0

                contc = []                  # This will be the continum for each of the ranges in "inclist"

                for x, y in xypairs:

                    # Accumulate all Y values for later median calculation

                    allyvalues = np.concatenate((allyvalues, y))

                    # Acculmulate total area and width and remember the continuum calc for each included range

                    area = si.trapz(y, x)
                    width = np.max(x) - np.min(x)
                    mv = area / width
                    totarea += area
                    totwidth += width
                    contc.append(mv)

                # Record result in "intresult" structure

                resitem = intresult(dataset)
                resitem.contlist = contc
                resitem.totcont = totarea / totwidth
       
                resultdict[dataset.modbjdate] = resitem

                # Remember totals for each included range plus overall

                rtotals += contc
                total += resitem.totcont

        # Do the overall sums.

        dates = resultdict.keys()
        dates.sort()
        numdates = len(dates)

        meancont = total / numdates
        mediancont = np.median(allyvalues)

        # Display the mean and median

        normto = meancont
        normcol = "magenta"

        if dlg.median.isChecked():
            normto = mediancont
            normcol = "g"

        # Get me the totals by date for display

        totconts = [resultdict[rd].totcont for rd in dates]

        # Lets have a catchy title

        if doneonce:    plt.clf()
        fig = plt.gcf()

        if entire:
            fig.canvas.set_window_title('Continuum level')
            plt.plot(dates, totconts, color='black', label='Overall level')
        else:
            fig.canvas.set_window_title('Continuum levels')
            plt.plot(dates, totconts, color='black', label='Overall')

            # Do a plot for each range using the specified colour for the range

            for n, r in enumerate(inclist):
                contc = [resultdict[rd].contlist[n] for rd in dates]
                plt.plot(dates, contc, color=r.rgbcolour(), label=r.description)

        # Put lines in for mean and median
                  
        plt.axhline(y=mediancont, label="Median", color="g")
        plt.axhline(y=meancont, label="Mean", color="magenta")

        # Figure out the RMSes of each difference from mean or median

        rms = totconts - normto
        rms = np.sqrt(sum(rms * rms) / numdates)

        # Get upper and lower number of RMSes from dialog

        ulim = normto + rms * dlg.upperlim.value()
        llim = normto - rms * dlg.lowerlim.value()

        # Add in dashed lines for those

        plt.axhline(y=ulim, color=normcol, ls='--', label='Stddev+')
        plt.axhline(y=llim, color=normcol, ls='--', label='Stddev-')

        # Label axes and display

        plt.xlabel('Dates')
        plt.ylabel('Continuum level')
        plt.legend()
        plt.show()

        # Now actually compare each spectrum and generate the result dialog box

        notechanges = []        # Vector of intresult structures with marks to be added

        if entire:
            for rd in resultdict.values():
                totc = rd.totcont
                if not (llim < totc < ulim):
                    rd.node = "Continuum outside range"
                    notechanges.append(rd)
        else:
            rtotals /= numdates
            for rd in resultdict.values():
                contc = rd.contlist
                for c, r in zip(rtotals, inclist):        # Each continuum calc versus each range used
                    if not (llim < c < ulim):
                        nt = "Outside range for " + r.description
                        if rd.note is None: rd.note = nt
                        else: rd.note += ", " + nt
                if rd.note is not None:
                    notechanges.append(rd)

        # Mark up what we changed

        for nt in notechanges:
            nt.dataarray.skip(nt.note)

        numch = len(notechanges)

        # Now let's create the result dialog

        resdlg = Markexresdlg(dlg)

        # Set up combo box for displaying each average

        if entire:
            resdlg.inclrange.setEnabled(False)
            resdlg.rngav.setText("(n/a)")
        else:
            for r, c in zip(inclist, rtotals):
                resdlg.inclrange.addItem(r.description, QVariant("%#.10g" % c))
            resdlg.inclrange.setCurrentIndex(0)

        resdlg.avoverall.setText("%#.10g" % meancont)
        resdlg.median.setText("%#.10g" % mediancont)
        resdlg.prevmarked.setText(str(pre_existing))
        resdlg.cleared.setText(str(ndone))
        resdlg.newmarked.setText(str(numch))

        # If OK pressed or Apply pressed in result dialog box, exec_() will return True
        # applied will be set if we pressed Apply
        # Otherwise go round again with the main dialog
        # If cancel pressed we drop out and return None

        if resdlg.exec_():
            if resdlg.applied:
                plt.close()
                return copy_ctrlfile
            continue
        plt.close()
        return None

