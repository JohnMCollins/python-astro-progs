#! /usr/bin/env python

# Produce a Latex table of equivalent width data

import argparse
import os.path
import sys
import string
import numpy as np
import exclusions
import jdate

# According to type of display select column, xlabel  for hist, ylabel for plot

optdict = dict(ew = (1, 'Equivalent width ($\AA$)'),
               ps = (2, 'Peak size (rel to EW)'),
               pr = (3, 'Peak ratio'),
               lpr = (4, 'Log Peak Ratio'))

parsearg = argparse.ArgumentParser(description='Plot equivalent width results')
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--type', help='ew/ps/pr/lpr to select display', type=str, default="ew")
parsearg.add_argument('--sepdays', type=int, default=10000, help='Separate items if this number of days apart')
parsearg.add_argument('--outfile', type=str, help='Output file name if not stdout')

res = vars(parsearg.parse_args())
rf = res['integ'][0]
sepdays = res['sepdays']
outf = res['outfile']
typeplot = res['type']

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
 
rxarray = []
ryarray = []
rxvalues = []
ryvalues = []

lastdate = 1e12

for d, v in zip(dates,vals):
    if d - lastdate > sepdays and len(rxvalues) != 0:
        rxarray.append(rxvalues)
        ryarray.append(ryvalues)
        rxvalues = []
        ryvalues = []
    rxvalues.append(d)
    ryvalues.append(v)
    lastdate = d

if len(rxvalues) != 0:
   rxarray.append(rxvalues)
   ryarray.append(ryvalues)

print "\\begin{center}"
print "\\begin{tabular}{ |l l r r r r| }"
print "\\hline"
print "\\multicolumn{6}{|c|}{%s}" % title, "\\\\\\hline"
print "Start & End & Min & Max & Mean & Std \\\\\\hline"
fmt = "%s & %s & %#.6g & %#.6g & %#.6g & %#.6g \\\\"
for d, vl in zip(rxarray, ryarray):
    sdate = d[0]
    edate = d[-1]
    mn = np.min(vl)
    mx = np.max(vl)
    av = np.mean(vl)
    st = np.std(vl)
    print fmt % (jdate.display(sdate), jdate.display(edate), mn, mx, av, st)

print "\\hline"
print fmt % ('All', '', np.min(vals), np.max(vals), np.mean(vals), np.std(vals))
print "\\hline"
print "\\end{tabular}"
print "\\end{center}"
