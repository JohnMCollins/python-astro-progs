#! /usr/bin/env python

import os
import sys
import math
import numpy as np
import argparse
import string
import rangearg
import scipy.optimize as sopt

twopi = np.pi * 2.0

def sinefunc(x, dc, phase, amp):
    """Sine function for optimisation"""
    global period, twopi
    return  amp * np.sin(twopi * (phase + x/period)) + dc

parsearg = argparse.ArgumentParser(description='Get phase/amplitude of bit fit sine and subtract', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsfile', type=str, nargs=1, help='Obs data file')
parsearg.add_argument('--outfile', type=str, help='Output filed', required=True)
parsearg.add_argument('--tcol', type=int, default=0, help='Column with time in')
parsearg.add_argument('--icol', type=int, default=1, help='Column with intensity in')
parsearg.add_argument('--period', type=float, required=True, help='Period in question to subtract')

resargs = vars(parsearg.parse_args())

obsfile = resargs['obsfile'][0]

outf = resargs['outfile']
tcol = resargs['tcol']
icol = resargs['icol']
period = resargs['period']

try:
    f = np.loadtxt(obsfile, unpack=True)
    timings = f[tcol]
    intens = f[icol]
except IOError as e:
    print "Could not load obs  file", obsfile, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", obsfile
    sys.exit(12)
except IndexError:
    print "File of wrong shape -", obsfile

# Might as well start the timings from 0

timings -= timings.min()
popt, pcov = sopt.curve_fit(sinefunc, timings, intens, (intens.mean(), 0.5, 1.0))
sc = sinefunc(timings, *popt)
i2 = intens - sc

np.savetxt(outf, np.array([timings, i2]).transpose())
