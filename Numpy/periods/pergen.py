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
parsearg.add_argument('--xmax', type=float, default=100, help='Maximum value for x')
parsearg.add_argument('--xnum', type=int, default=500, help='Number of x/y values')
parsearg.add_argument('--extracols', action='store_true', help='Generate output in 4 column format')

resargs = vars(parsearg.parse_args())

xnum = resargs['xnum']
xmax = resargs['xmax']

persamps = resargs['pars']

if len(persamps) % 2 != 0:
    print "Have to alternate periods and amplitudes"
    sys.exit(10)

persamps = np.array(persamps)
pers = persamps[range(0, len(persamps), 2)]
amps = persamps[range(1, len(persamps), 2)]
freqs = 2 * np.pi / pers

xv = np.linspace(0, xmax, xnum)
yv = np.zeros(xnum)

for f, a in zip(list(freqs), list(amps)):
    yv += a * np.sin(xv * f)

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
