#! /usr/bin/env python

import numpy as np
import numpy.random as nr
import argparse
import sys

parsearg = argparse.ArgumentParser(description='Make a fake spectrum')
parsearg.add_argument('--specout', type=str, help='Result output')
parsearg.add_argument('--period', type=float, default=80, help='Period')
parsearg.add_argument('--obsdays', type=float, default=80, help='Observation days')
parsearg.add_argument('--obsnum', type=int, default=40, help='Number of observations')
parsearg.add_argument('--fuzz', type=float, default=0, help='Sigma fuzz')

resargs = vars(parsearg.parse_args())
print sys.argv

specout = resargs['specout']
period = resargs['period']
obsdays = resargs['obsdays']
obsnum = resargs['obsnum']
fuzz = resargs['fuzz']

obsints = np.linspace(0, obsdays, obsnum, endpoint=True)

diff = obsints[1]-obsints[0]
if fuzz != 0.0:
    fuzzarr = diff * fuzz * nr.randn(len(obsints))
    obsints += fuzzarr
    obsints = np.sort(obsints)

intens = np.sin((2 * np.pi * obsints) / period)

result = np.array([obsints, intens])
result = np.transpose(result)

np.savetxt(specout, result)

