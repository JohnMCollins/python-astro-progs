#! /usr/bin/env python

# Program to add nice spikes to spectra

import argparse
import os.path
import sys
import numpy as np
import string
import math
import jdate
import argmaxmin
import miscutils

parsearg = argparse.ArgumentParser(description='Add spikes to ew data copied from real life ones')
parsearg.add_argument('ewfiles', type=str, nargs='*', help='EW files to add adjustments to, possibly none to just display')
parsearg.add_argument('--inewfile', type=str, required=True, help='EW file to take from')
parsearg.add_argument('--number', type=int, default=1, help='Number of maxima to take')
parsearg.add_argument('--suffix', type=str, default='spk', help='Suffix to add to files')
parsearg.add_argument('--print', action='store_true', help='Print values of maxima and exponents even if doing something')

resargs = vars(parsearg.parse_args())

ewfiles = resargs['ewfiles']
infile = resargs['inewfile']
numb = resargs['number']
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

maxes = argmaxmin.maxmaxes(jdates, ews)

avew = ews.mean()
diffm = ews-avew

results = []

for mm in maxes:
    
    try:
        curr = diffm[mm]
        currd = jdates[mm]
        nxt = diffm[mm+1]
        nxtd = jdates[mm+1]
        n = math.log(curr/nxt) / (nxtd - currd)
    except IndexError:
        continue
    except ValueError:
        n = -1.0
    
    results.append((mm, currd, curr, n))
    if len(results) >= numb:
        break

if len(ewfiles) == 0 or pvals:
    for mm, currd, curr, n in results:    
        print "%d: %s %.3f %.3f" % (mm, jdate.display(currd), curr, n)

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
    
    jdates = newew[0]
    ews = newew[2]
    
    for mm, currd, curr, n in results:
        
        if n < 0.0:
            ews[mm] += curr
        else:
            datesrem = jdates[mm:] - jdates[mm]
            ews[mm:] += curr * np.exp(-n * datesrem)
    
    newew[2] = ews
    newfname = miscutils.replacesuffix(ewf, suff)
    np.savetxt(newfname, newew.transpose()) 

sys.exit(0)
