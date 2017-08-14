#! /usr/bin/env python

import os
import os.path
import sys
import numpy as np
import argparse
import datetime
import string
import math
import glob
import re
import jdate
import threading

def makefname(seq, ordn, dat, formdets):
    """Construct filename from supplied info"""
    format, ms, pref, suff = formdets
    result = format
    if  string.find(result, "%DATE%") >= 0:
        adate = jdate.jdate_to_datetime(dat)
        datestr = adate.strftime("%Y-%m-%dT%H:%M:%S")
        if ms:
            datestr += ".%.3d" % (adate.microsecond / 1000)
        result = string.replace(result, "%DATE%", datestr)
    result = string.replace(result, "%ORD%", "%.3d" % ordn)
    result = string.replace(result, "%SEQ%", "%.6d" % seq)
    result = string.replace(result, "%PREFIX%", pref)
    return string.replace(result, "%SUFFIX%", suff)

class ordthread(threading.Thread):
    def __init__(self, threadID, whichord, subarray, dl, formatdets):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.whichord = whichord
      self.subarray = subarray
      self.datelist = dl
      self.formdets = formatdets
    def run(self):
        n = 1
        for dat, dn in zip(self.datelist, self.subarray):
            fname = makefname(n, self.whichord, dat, self.formdets)
            n += 1
            np.savetxt(fname, dn.transpose())

parsearg = argparse.ArgumentParser(description='Expand out a 4D array of spectral data', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infile', type=str, help='Input file', nargs=1)
parsearg.add_argument('--outdir', type=str, help='Output directory if not CWD')
parsearg.add_argument('--format', type=str, help='File name format if not default')
parsearg.add_argument('--ms', action='store_false', help='Save times with microseconds')
parsearg.add_argument('--prefix', type=str, default="", help='Prefix before time')
parsearg.add_argument('--suffix', type=str, default="", help='Suffix after time')
parsearg.add_argument('--firstord', type=int, default=0, help='First order number')

resargs = vars(parsearg.parse_args())

infile = resargs['infile'][0]
outdir = resargs['outdir']
format = resargs['format']
prefix = resargs['prefix']
suffix = resargs['suffix']
ms = resargs['ms']
firstord = resargs['firstord']

try:
    inputs = np.load(infile)
except IOError as e:
    sys.stdout = sys.stderr
    print "Cannot open", infile, "error was:", e.args[1]
    sys.exit(10)

if outdir is not None:
    try:
        os.chdir(outdir)
    except OSError as e:
        sys.stddout = sys.stderr
        print "Cannot select directory", outdir, "error was", e.args[1]
        sys.exit(12)
try:
    datelist = inputs['dates']
except:
    datelist = None

if format is None:
    if datelist is None:
        format = "%PREFIX%.%SEQ%.%SUFFIX%.%ORD%"
    else:
        format = "%PREFIX%.%DATE%.%SUFFIX%.%ORD%"
else:
    if datelist is None and string.find(format, "%DATE%") >= 0:
        sys.stdout =-sys.stderr
        print "No dates in", infile
        sys.exit(11)
        
arr = inputs['arr']
nords = arr.shape[0]
if datelist is None:
    datelist = np.zeros(arr.shape[1])
    datelist += 40000

# Set up threads for each order

tlist = []
for tn in range(0, nords):
    t = ordthread(tn, tn+firstord, arr[tn], datelist, (format, ms, prefix, suffix))
    tlist.append(t)
for t in tlist:
    t.start()
for t in tlist:
    t.join()
