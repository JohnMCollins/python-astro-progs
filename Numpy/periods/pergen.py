#! /usr/bin/env python

# Generate random periodic data for LS routine to analyse

import argparse
import os
import os.path
import sys
import numpy as np
import numpy.random as nr
import scipy.signal as ss

parsearg = argparse.ArgumentParser(description='Generate periodic data')
parsearg.add_argument('pars', type=float, nargs='+', help='List of periods and amplitudes')
parsearg.add_argument('--out', type=str, help='Output file')
parsearg.add_argument('--npers', type=float, default=10, help='Number of periods (mult of max period)')
parsearg.add_argument('--pnum', type=int, default=500, help='Number of x/y values up to max period')
parsearg.add_argument('--extracols', action='store_true', help='Generate output in 4 column format')
parsearg.add_argument('--xurand', type=float, default=0.0, help='Random offset uniform max proportion')
parsearg.add_argument('--xnrand', type=float, default=0.0, help='Random offset normal std dev')
parsearg.add_argument('--randphase', action='store_true', help='Add random phases to output')
parsearg.add_argument('--unoise', type=float, default=0.0, help='Uniform noise (fraction of max amp)')
parsearg.add_argument('--nnoise', type=float, default=0.0, help='Normal noise std (fraction of max amp')

resargs = vars(parsearg.parse_args())

xnum = resargs['pnum']
xmax = resargs['npers']

persamps = resargs['pars']

if len(persamps) % 2 != 0:
    print "Have to alternate periods and amplitudes"
    sys.exit(10)

persamps = np.array(persamps)
pers = persamps[range(0, len(persamps), 2)]
amps = persamps[range(1, len(persamps), 2)]
freqs = 2 * np.pi / pers

xv = np.linspace(0, np.max(pers)*xmax, xnum)
yv = np.zeros(xnum)
if resargs['randphase']:
    phases = nr.uniform(high=np.pi*2, size=xnum)
else:
    phases = np.zeros(xnum)

# Incorporate any specified randomness in the periods

xurand = resargs['xurand']
xnrand = resargs['xnrand']

if xurand < 0.0 or xnrand < 0.0:
    print "Cannot have negative random X"
    sys.exit(11)

if xurand != 0.0 or xnrand != 0.0:
    maxx = np.max(xv)
    dx = xv[1]-xv[0]
    if xurand != 0.0:
        lim = xurand * dx
        xv += nr.uniform(-lim, lim, size=xnum)
    if xnrand != 0.0:
        lim = xnrand * dx
        xv += nr.normal(scale=lim, size=xnum)
    # All of that may have left it unsorted
    xv.sort()
    # Reset first element to zero
    xv -= xv[0]
    # Scale whole lot so maxx is what it was
    xv *= maxx / np.max(xv)

for f, a, p in zip(list(freqs), list(amps), list(phases)):
    yv += a * np.sin(xv * f + p)

unoise = resargs['unoise']
nnoise = resargs['nnoise']

if unoise != 0.0 or nnoise != 0:
    maxy = np.max(yv)
    lim = unoise * maxy
    if unoise != 0.0:
        yv += nr.uniform(-lim, lim, size=xnum)
    if nnoise != 0.0:
        yv += nr.normal(scale=lim, size=xnum)
    # Fix if anything now negative
    miny = np.min(yv)
    if miny < 0.0:
        yv -= miny

if resargs['extracols']:
    z = np.zeros(len(xv))
    o = z + 1
    outarray = np.array([xv, yv, z, o])
else:
    outarray = np.array([xv, yv])
outarray = np.transpose(outarray)

if resargs['out'] is None:
    np.savetxt(sys.stdout, outarray)
else:
    np.savetxt(resargs['out'], outarray)
