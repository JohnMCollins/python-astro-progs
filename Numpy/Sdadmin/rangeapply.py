# Routines to list/apply excluded ranges to Numpy arrays.
# Assumes dialog box names in "markexceptdlg" and "contcalcdlg"

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as np
import datarange
import specdatactrl

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

    # If rangelist is None, use entire range but pretend we did it

    try:
        return  [ r.select(xvalues,yvalues) for r in rangelist ]
    except TypeError:
        return  [ (xvalues, yvalues) ]

def apply_excluded_ranges(rangelist, xvalues, yvalues):
    """Apply list of excluded ranges to xvalues and yvalues.

    Return revised list of xvalues and yvalues"""

    try:
        for r in rangelist:
            xvalues, yvalues = r.selectnot(xvalues, yvalues)
    except TypeError:
        pass
    return (xvalues, yvalues)

def get_selected_specdata(dataset, exclist, inclist):
    """Return (unsorted) pair of X and Y data array from dataset
    after applying excluded and included lists"""

    # NB The following might raise a data error exception
    # if we are discounting the given spectral data
    # Containing code should handle this!

    xvalues = dataset.get_xvalues(False)
    yvalues = dataset.get_yvalues(False)
    
    # Apply exclusions

    xvalues, yvalues = apply_excluded_ranges(exclist, xvalues, yvalues)
    
    xypairs = apply_included_ranges(inclist, xvalues, yvalues)
    yvalues = np.empty((0,),dtype=np.float64)
    xvalues = np.empty((0,),dtype=np.float64)
    for x, y in xypairs:
        yvalues = np.concatenate((yvalues, y))
        xvalues = np.concatenate((xvalues, x))
    return (xvalues,  yvalues)

def get_all_selected_specdata(ctrlfile, exclist, inclist):
    """Return (unsorted) list of X and Y arrays from all data"""

    allyvalues = np.empty((0,),dtype=np.float64)
    allxvalues = np.empty((0,),dtype=np.float64)

    for dataset in ctrlfile.datalist:
        try:
            xvalues, yvalues = get_selected_specdata(dataset, exclist, inclist)
        except specdatactrl.SpecDataError:
            continue
        allyvalues = np.concatenate((allyvalues, yvalues))
        allxvalues = np.concatenate((allxvalues, xvalues))
    return (allxvalues, allyvalues)

