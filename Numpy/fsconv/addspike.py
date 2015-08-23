#! /usr/bin/env python

# Program to add nice spikes to spectra

import argparse
import os.path
import sys
import numpy as np
import string
import re
import math
import miscutils

Log2 = math.log(2.0)
Gaussdiv = 2.0 * math.sqrt(2.0 * Log2)

def calcgauss(xvals, offset, scale, fhwm):
    """Calculate Gaussian profile"""
    sigma = fhwm / Gaussdiv
    return  scale * np.exp(-0.5 * ((xvals - offset) / sigma)**2)

parsearg = argparse.ArgumentParser(description='Add spikes to fake spectra')
parsearg.add_argument('spikes', type=str, nargs='+', help='Spikes as E/G:fhwm:amp:specnum')
parsearg.add_argument('--obsfile', type=str, required=True, help='Filename/obs time file')
parsearg.add_argument('--prefix', type=str, help='Prefix to add to spectrum file names')
parsearg.add_argument('--suffix', type=str, help='Suffix to replace in spectrum file names')

resargs = vars(parsearg.parse_args())

spikes = resargs['spikes']
obsfile = resargs['obsfile']

prefix = resargs['prefix']
suffix = resargs['suffix']
if prefix is not None:
    if len(prefix) == 0:
        print "Invalid prefix"
        sys.exit(9)
    if prefix[-1] != '.':
        prefix += '.'
elif suffix is None:
    print "Have to have prefix or suffix"
    sys.exit(8)

try:
    inf = open(obsfile)
except IOError as e:
    print "Cannot open obs file", obsfile, e.args[1]
    sys.exit(10)

dir, obsfname = os.path.split(obsfile)
if len(dir) != 0:
    dir += '/'

obst = []
dates = []

for line in inf:
    line = string.strip(line)
    try:
        fn, dat = string.split(line, ' ')
        dat = float(dat)
    except (ValueError, TypeError):
        print "Unexpected format obs file", obsfile
        sys.exit(11)
    obst.append((fn, dat))
    dates.append(dat)

# Turn dates into numpy array

dates = np.array(dates)
dates -= dates[0]
spikelist = np.zeros_like(dates)

spikeparse = re.compile('([eg]):([-.ed\d]+):([-.ed\d]+):(\d+)$')

for sp in spikes:
    smtch = spikeparse.match(string.lower(sp))
    if not smtch:
        print "Could not parse spike arg", sp
        sys.exit(12)
    eorg, hw, amp, snum = smtch.groups()
    try:
        hw = float(hw)
        amp = float(amp)
        snum = int(snum)
    except ValueError as e:
        print "Error parsing spike arg", sp
        print e.args[0]
        sys.exit(13)
    
    try:
        if eorg == 'e':
            addondates = dates[snum:]
            addondates -= addondates[0]
            n = Log2 / hw
            spikelist[snum:] += amp * np.exp(- addondates * n)
        else:
            spikelist += calcgauss(dates, dates[snum], amp, hw)
    except IndexError:
        print "Invalid date index in", sp
        sys.exit(14)
    except ZeroDivisionError:
        print "Invalid value (zero divide) in", sp
        sys.exit(15)

# Now go through the files and add in the spikes
# Build up new obs time file as we go

try:
    fname = obsfname
    if suffix is not None:
        fname = miscutils.replacesuffix(fname, suffix)
    if prefix is not None:
        fname = prefix + fname
    outf = open(dir + fname, "w")
except IOError as e:
    print "Cannot create output file", fname
    print "Error was", e.args[1]
    sys.exit(19)

n = 0
for fn, dat in obst:
    try:
        wls, amps = np.loadtxt(dir + fn, unpack=True)
    except ValueError:
        print "Cannot understand spectrum file", fn
        sys.exit(16)
    except IOError as e:
        print "Cannot open spectrum file", fn
        print "Error was", e.args[1]
        sys.exit(17)
    amps += spikelist[n]
    n += 1
    amps /= amps[0]
    try:
        fname = fn
        if suffix is not None:
            fname = miscutils.replacesuffix(fname, suffix)
        if prefix is not None:
            fname = prefix + fname
        np.savetxt(dir + fname, np.array([wls, amps]).transpose())
    except IOError as e:
        print "Cannot save spectrum file", fname
        print "Error was", e.args[1]
        sys.exit(18)
    outf.write(fname + " %#.16g\n" % dat)

sys.exit(0)
