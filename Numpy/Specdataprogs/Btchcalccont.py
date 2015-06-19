#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse

import numpy as np

import miscutils
import specdatactrl
import datarange
import specinfo
import simbad
import doppler

parsearg = argparse.ArgumentParser(description='Batch mode calculate continue')
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)
parsearg.add_argument('--include', type=str, help='Comma-separated ranges to take points from (otherwise whole)')
parsearg.add_argument('--exclude', type=str, default='halpha', help='Comma-separated ranges to exclude (default halpha)')
parsearg.add_argument('--individual', action='store_true', help='Calculate individual continua')
parsearg.add_argument('--degree', type=int, default=3, help='Degree of polynomial fit')
parsearg.add_argument('--maxiter', type=int, default=5000, help='Maximum number of iterations')
parsearg.add_argument('--refwl', type=float, default=6562.8, help='Reference wavelength of polynomial')
parsearg.add_argument('--upper', type=float, default=3.0, help='Upper mult of SD to exclude above')
parsearg.add_argument('--lower', type=float, default=2.0, help='Lower mult of SD to exclude below')

res = vars(parsearg.parse_args())

infofile = res['infofile'][0]
inclranges = res['include']
exclranges = res['exclude']
indiv = res['individual']
degree = res['degree']
maxiter = res['maxiter']
refwl = res['refwl']
uppersd = res['upper']
lowersd = res['lower']

if not os.path.isfile(infofile):
    infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infofile)
    ctrllist = inf.get_ctrlfile()
    rangl = inf.get_rangelist()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", infofile
    print "Error was:", e.args[0]
    sys.exit(100)

try:
    ctrllist.loadfiles()
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Problem loading files via", infofile
    print "Error was:", e.args[0]
    sys.exit(101)

inclrange = None
exclrange = None

try:
    if inclranges is not None and len(inclranges) != 0:
        inclrange = datarange.Rangeset(rangl)
        inclrange.parseset(inclranges)
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print "Problem seting include ranges"
    print "Error was:", e.args[0]
    sys.exit(102)
try:
    if exclranges is not None and len(exclranges) != 0:
        exclrange = datarange.Rangeset(rangl)
        exclrange.parseset(exclranges)
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print "Problem seting exclude ranges"
    print "Error was:", e.args[0]
    sys.exit(103)
    
totremovals = 0
stuffed = False

if indiv:
    ctrllist.reset_indiv_y()
    
    for dataset in ctrllist.datalist:

            # Grab each spectrum we're not excluding

            if dataset.tmpxvals is None:
                try:
                    xvalues, yvalues = rangeapply.get_selected_specdata(dataset, exclist, inclist)
                except specdatactrl.SpecDataError:
                    continue
            else:
                xvalues = dataset.tmpxvals
                yvalues = dataset.tmpyvals

            # We iterate each spectrum in turn, using the
            # tmpcoeffs entry in each to remember the result of
            # the last iteration.

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
                tries += 1

            # Out of iterations loop, break to previous loop if
            # we hit an error otherwise save the last lot of coeffs

            if stuffed: break

            dataset.tmpcoeffs = coeffs
            dataset.tmpxvals = xvalues
            dataset.tmpyvals = yvalues
            dataset.stddev = stddeviation

        # Finished iteration over datasets, now display results

        resdlg = ContCalcResDlg(dlg, True)

        resdlg.exclpoints.setText("%d" % totremovals)
        if prevexcl is None: resdlg.pexclpoints.setText("N/a")
        else: resdlg.pexclpoints.setText(str(prevexcl))
        prevexcl = totremovals
        resdlg.afterits.setText("%d/%d" % (itn+1, iterations))

        # Now add all the stuff for plotting with

        resdlg.init_data(copy_ctrlfile)
        resdlg.lowstd = lwrstd
        resdlg.upstd = uprstd
        resdlg.settingup = False
        resdlg.datafiles.setCurrentRow(0)

        # False return from result dialog means we pressed cancel

        if not resdlg.exec_():
            plt.close()
            return None

        plt.close()

        # Otherwise look at "applied" to see if user pressed "Apply changes"

        if resdlg.applied:
            changes = 0
            copy_ctrlfile.copy_coeffs()
            return copy_ctrlfile

        # Turn off restart which disables things we can't change unless we restart

        dlg.restart.setEnabled(True)
        dlg.restart.setChecked(False)

        # Now we should be ready to loop again

    # Cancel pressed, return None to say we're not doing anything



else:               # global one
    
    ctrllist.reset_indiv_y()
    ctrllist.reset_y()
    ctrllist.set_yscale(1.0)
    
    allyvalues = np.empty((0,),dtype=np.float64)
    allxvalues = np.empty((0,),dtype=np.float64)
    
    for dataset in ctrllist.datalist:
        try:
            xvalues = dataset.get_xvalues(False)
            yvalues = dataset.get_yvalues(False)
        except specdatactrl.SpecDataError:
            continue
        
        if inclrange is not None:
            xvalues, yvalues = inclrange.include(xvalues, yvalues)
        
        if exclrange is not None:
            xvalues, yvalues = exclrange.exclude(xvalues, yvalues)
        
        allyvalues = np.concatenate((allyvalues, yvalues))
        allxvalues = np.concatenate((allxvalues, xvalues))
    
    # Sort that lot
    
    sortind = allxvalues.argsort()
    allxvalues = allxvalues[sortind]
    allyvalues = allyvalues[sortind]     
 
    iterations = 0
    
    while 1:
        
        if iterations >= maxiter:
            sys.stdout = sys.stderr
            print "Too many iterations"
            sys.exit(10)
        
        iterations += 1
        relxvalues = allxvalues - refwl      
        coeffs = np.polyfit(relxvalues, allyvalues, degree)

        # Get the Y values corresponding to the polynomial we've fitted

        polyyvalues = np.polyval(coeffs, relxvalues)

        # Get std devs

        diffs = allyvalues - polyyvalues
        meandiff = diffs.mean()
        stddeviation = diffs.std()
        mindiff = meandiff - (lowersd * stddeviation)
        maxdiff = meandiff + uppersd * stddeviation

        removing = (diffs < mindiff) | (diffs > maxdiff)

        # If that didn't do anything, we're done however many iterations we've got to go

        nrem = np.count_nonzero(removing)
        if nrem == 0:
            break

        notremoving = ~ removing
        if np.count_nonzero(notremoving) == 0:
            sys.stdout = sys.stderr
            print "Run out of data after", iterations, "iterations"
            sys.exit(11)
 
        # Prune away the ones we are removing.
        
        totremovals += nrem
          
        allxvalues = allxvalues[notremoving]
        allyvalues = allyvalues[notremoving]
    
    #  All done now, report results
    
    ctrllist.set_refwavelength(refwl)
    ctrllist.set_yoffset(coeffs)
    
    print "Finished calculating ceoffs after %d iterations and %d removed, coeff values are:" % (iterations, totremovals)
    
    for n, c in zip(range(degree, -1, -1), coeffs)
        print "%2d: %#.8g" % (n, c)
 
 # Now save result
 
try:
    inf.savefile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot re-save", infofile
    print "Error was", e.args[0]
    sys.exit(150)

sys.exit(0)
