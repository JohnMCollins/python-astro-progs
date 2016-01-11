#! /usr/bin/env python

# Produce a Latex table of equivalent width data

import argparse
import os.path
import sys
import string
import numpy as np
import datetime
import jdate
import splittime
import periodarg

# According to type of display select column, xlabel  for hist, ylabel for plot

optdict = dict(ew = (2, 'Equivalent width ($\AA$)'),
               ps = (4, 'Peak size'),
               pr = (6, 'Peak ratio'))

parsearg = argparse.ArgumentParser(description='Plot equivalent width results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file')
parsearg.add_argument('--type', help='ew/ps/pr/lpr to select display', type=str, default="ew")
parsearg.add_argument('--sepdays', type=str, default='1000d', help='Separate items if this number of days apart')
parsearg.add_argument('--outfile', type=str, help='Output file name if not stdout')

resargs = vars(parsearg.parse_args())
rf = resargs['integ'][0]
sepdays = periodarg.periodarg(resargs['sepdays'])
outf = resargs['outfile']
typeplot = resargs['type']

ofil = sys.stdout

if outf is not None:
    try:
        ofil = open(outf, 'w')
    except IOError as e:
        sys.stdout = sys.stderr
        print "Error creating output file", outf, "error was", e.args[1]
        sys.exit(100)

sys.stdout = ofil

if typeplot not in optdict:
    sys.stdout = sys.stderr
    print "Unknown type", typeplot, "specified"
    sys.exit(2)

ycolumn, title = optdict[typeplot]

# Load up file of integration results

try:
    inp = np.loadtxt(rf, unpack=True)
except IOError as e:
    sys.stdout = sys.stderr
    print "Error loading EW file", rf, "error was", e.args[1]
    sys.exit(100)
    
dates = inp[0]
vals = inp[ycolumn]

dt_dates = [jdate.jdate_to_datetime(d) for d in dates]

timesegs = splittime.splittime(sepdays, dt_dates, dates, vals)

print "\\begin{center}"
print "\\begin{tabular}{ |l l r r r r| }"
print "\\hline"
print "\\multicolumn{6}{|c|}{%s}" % title, "\\\\\\hline"
print "Start & End & Min & Max & Mean & Std \\\\\\hline"
fmt = "%s & %s & %#.6g & %#.6g & %#.6g & %#.6g \\\\"
for day_dt, day_date, day_vals in timesegs:
    sdate = day_date[0]
    edate = day_date[-1]
    mn = np.min(day_vals)
    mx = np.max(day_vals)
    av = np.mean(day_vals)
    st = np.std(day_vals)
    print fmt % (jdate.display(sdate), jdate.display(edate), mn, mx, av, st)

print "\\hline"
print fmt % ('All', '', np.min(vals), np.max(vals), np.mean(vals), np.std(vals))
print "\\hline"
print "\\end{tabular}"
print "\\end{center}"
