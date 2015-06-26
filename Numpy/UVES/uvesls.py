#! /usr/bin/env python

# Apply X-ray file to UVES data to mark

import sys
import os
import string
import os.path
import locale
import argparse
import numpy as np
import miscutils
import jdate
import datetime
import splittime
import periodarg
import scipy.signal as ss

SECSPERDAY = 3600.0 * 24.0

coltype = dict(ew = 2, ps = 4, pr = 6)

parsearg = argparse.ArgumentParser(description='Process UVES EW data and generate periodograms')
parsearg.add_argument('ewfile', type=str, nargs=1, help='EW data produced by uvesew')
parsearg.add_argument('--xraylevel', type=float, required=True, help='X-ray level for cutoff')
parsearg.add_argument('--splittime', help='Split plot segs on value', type=float, default=1)
parsearg.add_argument('--outfile', help='Prefix for output file', type=str, required=True)
parsearg.add_argument('--start', help='Starting period to try', type=str, default='10m')
parsearg.add_argument('--step', help='Step in periods to try', type=str, default='10s')
parsearg.add_argument('--stop', help='Ending period to try', type=str, default='1d')
parsearg.add_argument('--type', type=str, default='ew', help='Type of feature to process, ew, ps or pr default ew')
parsearg.add_argument('--normalise', action='store_true', help='Apply normalisation to L-S result')

resargs = vars(parsearg.parse_args())

ewfile = resargs['ewfile'][0]
xraylevel = resargs['xraylevel']
splitem = resargs['splittime']
outfile = resargs['outfile']
typeplt = resargs['type']
norm = resargs['normalise']

try:
    typecol = coltype[typeplt]
except ValueError:
    print "Invalid column type", typeplt

try:
    startper = periodarg.periodarg(resargs['start'])
    stepper = periodarg.periodarg(resargs['step'])
    stopper = periodarg.periodarg(resargs['stop'])
except ValueError as e:
    print "Trouble with period argument set"
    print "Error was:", e.args[0]
    sys.exit(8)

if startper >= stopper:
    print "Sorry do not understand start period >= stop period"
    sys.exit(9)
    
perrange = np.arange(startper, stopper, stepper)
tfreqs = 2 * np.pi / perrange

if len(perrange) <= 10:
    print "Range of periods is unacceptably low"
    sys.exit(9)

# Now read the EW file we need the dates to marry with the xray and the barycentric dates for the calc.

try:
    filecontents = np.loadtxt(ewfile, unpack=True)
    
    jdates = filecontents[0]
    bjdates = filecontents[1]
    values = filecontents[typecol]
    xrayvs = filecontents[9]

except IOError as e:
    print "Cannot open info file, error was", e.args[1]
    sys.exit(12)
except IndexError as e:
    print "File does not seem to be correct format"
    sys.exit(13)

# Get date list and split up spectra by day

datelist = [jdate.jdate_to_datetime(jd) for jd in jdates]
dateparts = splittime.splittime(SECSPERDAY * splitem, datelist, jdates, bjdates, values, xrayvs)

# Produce individual files if number of days > 1

if len(dateparts) > 1:
    
    fnum = 1
    
    for day_dtdates, day_jdates, day_bjdates, day_values, day_xrayvs in dateparts:
        
        # Scale back to zero doesn't alter L-S result
        
        day_bjdates -= day_bjdates[0] 

        sel = day_xrayvs <= xraylevel
        bjd = day_bjdates[sel]
        dv = day_values[sel]
        dv -= dv.mean()                     # Need this for ss.lombscargle to work
        
        spectrum = ss.lombscargle(bjd, dv, tfreqs)
        if norm:
            spectrum = np.sqrt(spectrum * 4.0 / float(len(bjd)))
        
        np.savetxt(outfile + "_day_%d.ls" % fnum, np.transpose(np.array([perrange, spectrum])))
        fnum += 1

bjdates -= bjdates[0]
sel = xrayvs < xraylevel
bjd = bjdates[sel]
dv = values[sel]
dv -= dv.mean()

spectrum = ss.lombscargle(bjd, dv, tfreqs)
if norm:
    spectrum = np.sqrt(spectrum * 4.0 / float(len(bjd)))
np.savetxt(outfile + "_all.ls", np.transpose(np.array([perrange, spectrum])))
