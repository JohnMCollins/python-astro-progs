#! /usr/bin/python

# Integrate all of a spectrum starting from obs times file
# Obs times file is of form <spec file name> <obs time>

import argparse
import os
import os.path
import sys
import numpy as np
import re
import string
import rangearg

parsearg = argparse.ArgumentParser(description='Integration file',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--timings', type=str, help='Timings data file')
parsearg.add_argument('--outinteg', type=str, help='Output integration file')
parsearg.add_argument('--resdir', type=str, help='Input directory if not same as timings data')
parsearg.add_argument('--range', type=str, help='Range as nnn.nnn pair')
parsearg.add_argument('--lower', type=float, default=0.0, help='Lower integration limit, default none')
parsearg.add_argument('--upper', type=float, default=0.0, help='Upper integration limit, default none')

resargs = vars(parsearg.parse_args())

timefile = resargs['timings']
outinteg = resargs['outinteg']
resdir = resargs['resdir']
try:
    llim, ulim = rangearg.getrangearg(resargs)
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
    sel = None
    if llim > 0.0:
        if ulim > 0.0:
            sel1 = wl >= llim
            sel2 = wl <= ulim
            sel = sel1 & sel2
        else:
            sel = wl >= llim
    elif ulim > 0.0:
        sel = wl <= ulim
    if sel is not None:
        inten = inten[sel]
        wl = wl[sel]
    if len(wl) == 0:
        print "No data after selection"
        sys.exit(13)
    integ = np.trapz(inten, wl) / (np.max(wl) - np.min(wl)) - 1
    fout.write("%#.16g %#.16g\n" % (tim, integ))

fout.close()


