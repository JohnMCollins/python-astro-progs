#! /usr/bin/env python

# Generate random periodic data for LS routine to analyse

import argparse
import os
import os.path
import sys
import numpy as np
import numpy.random as nr
import scipy.signal as ss
import matplotlib.pylab as plt

parsearg = argparse.ArgumentParser(description='Generate periodic data')
parsearg.add_argument('pars', type=int, nargs='+', help='List of periods and amplitudes')
parsearg.add_argument('--xnum', type=int, default=500, help='Number of x/y values')
parsearg.add_argument('--sampling', type=int, default=500000, help='Sampling interval')
parsearg.add_argument('--scaling', type=float, default=1.0, help='Scaling of X values')

resargs = vars(parsearg.parse_args())

xnum = resargs['xnum']
sampling = resargs['sampling']
scaling = resargs['scaling']
persamps = resargs['pars']

if len(persamps) % 2 != 0:
    print "Have to alternate periods and amplitudes"
    sys.exit(10)

persamps = np.array(persamps)
pers = persamps[range(0, len(persamps), 2)]
amps = persamps[range(1, len(persamps), 2)]

freqs = 2 * np.pi / pers

minfreq = np.min(freqs)
maxfreq = np.max(freqs)

xv = np.linspace(minfreq * 0.1, maxfreq * 2.0, xnum)
yv = np.zeros(xnum)
for f,a in zip(list(freqs),list(amps)):
    yv += a * np.sin(xv * f)

samps = np.linspace(minfreq * 0.9, maxfreq * 1.1, sampling)
pgm = ss.lombscargle(xv, yv, samps)
amppgm = np.sqrt(4 * pgm / len(xv))
perscalc = 2*np.pi/samps

mxamp = np.max(amppgm)
maxes = ss.argrelmax(amppgm)[0]
if len(maxes) > len(pers):
    imxes = np.argsort(amppgm[maxes])
    maxes = maxes[imxes[-len(pers):]]

plt.plot(perscalc, amppgm)
for mx in maxes:
    plt.axvline(perscalc[mx], color='red')
    plt.text(perscalc[mx], mxamp * .9, "%.2f" % perscalc[mx], color='red', rotation=90) 
plt.show()