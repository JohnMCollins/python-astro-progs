#! /usr/bin/python

# Calculate equivalent widths
# Obs times file is of form <spec file name> <obs time>

import argparse
import os
import os.path
import sys
import numpy as np
import re
import string
import rangearg

parsearg = argparse.ArgumentParser(description='Equivalent width calculation')
parsearg.add_argument('--timings', type=str, help='Timings data file')
parsearg.add_argument('--outinteg', type=str, help='Output EW file')
parsearg.add_argument('--resdir', type=str, help='Input directory if not same as timings data')
parsearg.add_argument('--range', type=str, help='Range as nnn.nnn pair')
parsearg.add_argument('--lower', type=float, default=0.0, help='Lower integration limit')
parsearg.add_argument('--upper', type=float, default=0.0, help='Upper integration limit')

resargs = vars(parsearg.parse_args())

timefile = resargs['timings']
outinteg = resargs['outinteg']
resdir = resargs['resdir']
try:
    llim, ulim = rangearg.getrangearg(resargs)
    if llim == 0.0: raise ValueError("Cannot omit lower range limit")
    if ulim == 0.0: raise ValueError("Cannot omit upper range limit")
except ValueError as e:
    print e.args[0]
    sys.exit(9)

errors = 0

if timefile is None or not os.path.isfile(timefile):
    print "No timings file"
    errors += 1
    timefile = "none"
if outinteg is None:
    print "No output file"
    errors += 1
if resdir is None:
    resdir = os.path.dirname(timefile)
if len(resdir) == 0:
    resdir = os.getcwd()
elif not os.path.isdir(resdir):
    print "No results directory", resdir
    errors += 1

if errors > 0:
    sys.exit(10)

try:
    fin = open(timefile, 'r')
except IOError as e:
    print "Could not open", timefile, "error was", e.args[1]
    sys.exit(11)

if not os.path.isabs(outinteg):
    outinteg = os.path.join(resdir, outinteg)

try:
    fout = open(outinteg, 'w')
except IOError as e:
    print "Could not write", outinteg, "error was", e.args[1]
    sys.exit(12)

reparser = re.compile("\s+")

# Now do the business

for lin in fin:
    filen, tim = reparser.split(string.strip(lin))
    tim = float(tim)
    wl,inten = np.loadtxt(os.path.join(resdir, filen), unpack=True)
    sel1 = wl >= llim
    sel2 = wl <= ulim
    # Lower continuum
    wlcont = wl[~sel1]
    ilcont = inten[~sel1]
    if len(wlcont) == 0:
        print "Empty lower continuum file", filen
        continue
    # Upper continuum
    wucont = wl[~sel2]
    iucont = wl[~sel2]
    if len(wucont) == 0:
        print "Empty upper continuum file", filen
        continue
    # Thing itself
    sel = sel1 & sel2
    wvals = wl[sel]
    ivals = inten[sel]
    if len(wvals) == 0:
        print "Empty data set file", filen
        continue;
    # Get continuum
    contheight = (np.trapz(ilcont, wlcont) + np.trapz(iucont, wucont)) / ((np.max(wlcont)-np.min(wlcont)) + (np.max(wucont)-np.min(wucont)))
    # Now get equiv width
    integ = np.trapz(inten, wl) / contheight
    fout.write("%#.16g %#.16g\n" % (tim, integ))

fout.close()


