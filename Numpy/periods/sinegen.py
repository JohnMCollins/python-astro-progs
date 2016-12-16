#! /usr/bin/env python

import os
import sys
import math
import numpy as np
import argparse
import string
import rangearg

twopi = np.pi * 2.0

parsearg = argparse.ArgumentParser(description='Genereate sine of given period, amplitude, phase and times', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsfile', type=str, nargs=1, help='Obs data file')
parsearg.add_argument('--outfile', type=str, help='Output filed', required=True)
parsearg.add_argument('--tcol', type=int, default=0, help='Column with time in')
parsearg.add_argument('--period', type=float, required=True, help='Period in question to subtract')
parsearg.add_argument('--amplitude', type=float, default=1.0, help='Amplitude')
parsearg.add_argument('--phase', type=float, default=0.0, help='Phase as part of revolution')

resargs = vars(parsearg.parse_args())

obsfile = resargs['obsfile'][0]

outf = resargs['outfile']
tcol = resargs['tcol']
period = resargs['period']
amplitude = resargs['amplitude']
phase = resargs['phase']

try:
    f = np.loadtxt(obsfile, unpack=True)
    timings = f[tcol]
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
sc = np.sin(twopi * (phase + timings/period))
np.savetxt(outf, np.array([timings, sc]).transpose())
