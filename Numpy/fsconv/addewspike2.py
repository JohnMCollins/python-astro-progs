#! /usr/bin/env python

# Program to add nice spikes to spectra

import argparse
import os.path
import sys
import numpy as np
import string
import math
import jdate
import miscutils

parsearg = argparse.ArgumentParser(description='Add spikes to ew data copied from real life ones by level',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ewfiles', type=str, nargs='*', help='EW files to add adjustments to, possibly none to just display')
parsearg.add_argument('--inewfile', type=str, required=True, help='EW file to take from')
parsearg.add_argument('--upper', type=float, default=2.0, help='Numbers of std devs to continue to apply for')
parsearg.add_argument('--median', action='store_true', help='Use median not mean')
parsearg.add_argument('--byvalue', action='store_true', help='Apply by value rather than x * std')
parsearg.add_argument('--suffix', type=str, default='spk', help='Suffix to add to files')
parsearg.add_argument('--print', action='store_true', help='Print values of maxima and exponents even if doing something')

resargs = vars(parsearg.parse_args())

ewfiles = resargs['ewfiles']
infile = resargs['inewfile']
ulev = resargs['upper']
bymed = resargs['median']
byval = resargs['byvalue']
suff = resargs['suffix']
pvals = resargs['print']

try:
    ewdata = np.loadtxt(infile, unpack = True)
except IOError as e:
    print "Cannot open input ew file", infile, e.args[1]
    sys.exit(2)
except ValueError:
    print "Invalid format input ew file", infile
    sys.exit(3)

if ewdata.shape[0] != 8:
    print "Invalid shape EW file", infile
    eys.exit(4)

jdates = ewdata[0]
ews = ewdata[2]

mval = ews.mean()
if bymed:
    mval = np.median(ews)
if byval:
    cutoff = ulev
else:
    cutoff = mval + ews.std() * ulev

# Now forget everything below the lower limit

ews[ews < cutoff] = 0.0

if len(ewfiles) == 0 or pvals:
    for n, dv in enumerate(zip(jdates,ews)):
        d,v = dv
        if v <= 0.0: continue
        print "%d: %s %.3f" % (n, jdate.display(d), v)

ews /= mval

for ewf in ewfiles:  
    try:
        newew = np.loadtxt(ewf, unpack=True)
    except IOError as e:
        print "Cannot open", ewf, "Error was", e.args[1]
        continue
    except ValueError:
        print "Invalid format", ewf
        continue
    
    if newew.shape[0] != 8:
        print "Invalid shape file", ewf
        continue
    
    newews = newew[2]
    if bymed:
        mval = np.median(newews)
    else:
        mval = newews.mean()
    
    newews += ews * mval
    
    newew[2] = newews
    newfname = miscutils.replacesuffix(ewf, suff)
    np.savetxt(newfname, newew.transpose()) 

sys.exit(0)
