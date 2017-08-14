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

def facc(dic, x):
    """Count occurrences of string x" in dict"""
    try:
        dic[x] += 1
    except KeyError:
        dic[x] = 1

class ordthread(threading.Thread):
    def __init__(self, threadID, whichord):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.whichord = whichord
    def run(self):
        global dclist, stk
        for dc in dclist:
            f, ordr = dc
            if  ordr != self.whichord:
                continue
            try:
                arr = np.loadtxt(f, unpack=True)
            except:
                print "Could not load", f;
                sys.exit(13)
            stk[ordr].append(arr)

 
parsearg = argparse.ArgumentParser(description='Construct up to 4D array from ASCII spectral data', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('indir', type=str, help='Input directory if not CWD', nargs='?')
parsearg.add_argument('--outfile', type=str, help='Output file name (otherwise basaed on last part of directory name)')
parsearg.add_argument('--idates', action='store_false', help='Try to extract MJD from file names')
parsearg.add_argument('--prefix', type=str, help='Prefix to file names if not most frequent')
parsearg.add_argument('--nprefix', type=int, default=5, help='Number of chars to look for file name prefix')
parsearg.add_argument('--threshold', type=int, default=5, help='Number of occurences of file name to consider significant')

resargs = vars(parsearg.parse_args())

outfile = resargs['outfile']
indir = resargs['indir']
if indir is None:
    if outfile is None:
        outfile = os.path.basename(os.getcwd())
else:
    if outfile is None:
        outfile = os.path.basename(indir)
    outfile = os.path.abspath(outfile)
    try:
        os.chdir(indir)
    except OSError as e:
        sys.stdout = sys.stderr
        print "Cannot select", indir, "error was", e.args[1]
        sys.exit(10)

# Grab ourselves a list of the files

prefix = resargs['prefix']
thresh = resargs['threshold']
doing_dates = resargs['idates']

# If no prefix given, try to work one out

if prefix is None:
    flist = glob.glob('*')
    psize = resargs['nprefix']
    prefixes = [item[0:psize] for item in flist]
    pcnt = dict()
    map(lambda x: facc(pcnt,x), prefixes)
    fv = pcnt.values()
    fk = pcnt.keys()
    mx = np.argmax(fv)
    if fv[mx] < thresh:
        sys.stdout = sys.stderr
        print "Cannot discover prefix for files, sorry"
        sys.exit(12)
    prefix = fk[mx]

flist = glob.glob(prefix + '*')
if len(flist) < thresh:
    sys.stdout = sys.stderr
    print "Too few files found with prefile", prefix
    sys.exit(11)

# Might as well sort that lot

flist = sorted(flist)
dclist = []
datelist = []
errors = 0
mxord = -1
mnord = 10000000

if doing_dates:
    reg = re.compile("(.*?)(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)(?:\.(\d+))?(.*)\.(\d+)")
    
    for f in flist:
        mtch = reg.match(f)
        if mtch is None:
            print "Sorry", f, "does not match"
            errors += 1
            continue
        pref, yr, mn, dy, hr, minute, sec, msec, suff, ordr = mtch.groups()
        if msec is None: msec = 0
        else: msec = int(msec) * 1000
        dt = datetime.datetime(int(yr), int(mn), int(dy), int(hr), int(minute), int(sec), msec)
        ordr = int(ordr)
        if ordr > mxord: mxord = ordr
        if ordr < mnord: mnord = ordr
        dclist.append([f, ordr])
        datelist.append([jdate.datetime_to_jdate(dt), pref, suff, ordr])
else:
    reg = re.compile("(.*)\.(\d+)")
    
    for f in flist:
        mtch = reg.match(f)
        if mtch is None:
            print "Sorry", f, "does not match"
            errors += 1
            continue
        pref, ordr = mtch.groups()
        ordr = int(ordr)
        if ordr > mxord: mxord = ordr
        if ordr < mnord: mnord = ordr
        dclist.append([f, ordr])
        datelist.append(pref)

if errors > 0:
    sys.stdout = sys.stderr
    print "Aborting due to", errors, "error(s)"
    sys.exit(12)
    
stk = []
for nn in range(0, mxord+1):
    stk.append([])

# Set up threads for each order

tlist = []
for tn in range(mnord, mxord+1):
    t = ordthread(tn, tn)
    tlist.append(t)
for t in tlist:
    t.start()
for t in tlist:
    t.join()

# Squash down results to where we've got something

rstk = [s for s in stk if len(s) != 0]

if doing_dates:
    dates = []
    
    for dc in datelist:
        dat, pref, suff, ordr = dc
        if ordr == mnord:
            dates.append(dat)

    np.savez_compressed(outfile, arr=np.stack(rstk), dates=dates)
else:
    np.savez_compressed(outfile, arr=np.stack(rstk))
