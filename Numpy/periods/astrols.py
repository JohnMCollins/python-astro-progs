#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-12-21T20:02:50+00:00
# @Email:  jmc@toad.me.uk
# @Filename: astrols.py
# @Last modified by:   jmc
# @Last modified time: 2018-12-21T20:26:37+00:00

# Gatspy version of LSCONV

import argparse
import os
import os.path
import sys
import numpy as np
from astropy.stats import LombScargle
import re

# According to type of display select column

parsearg = argparse.ArgumentParser(description='Perform atropy L-S FFT', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--outspec', type=str, help='Output spectrum file', required=True)
parsearg.add_argument('--periods', type=str, help='Periods as start:stop/number', required=True)

resargs = vars(parsearg.parse_args())

integ = resargs['integ'][0]
outspec = resargs['outspec']
mtch = re.match('(\d+):(\d+)/(\d+)', resargs['periods'])
if mtch is None:
	print >>sys.stder, "Cannot understand period arg", resargs['periods']
	sys.exit(10)

startp = float(mtch.group(1))
endp = float(mtch.group(2))
numb = int(mtch.group(3))

if startp >= endp:
	print >>sys.stderr, "Expecting start period to be less then end period"
	sys.exit(11)

# Load up array of timings/intensities

try:
    arr = np.loadtxt(integ, unpack=True)
    timings = arr[0]
    sums = arr[1]
except IOError as e:
    print >>sys.stderr, "Could not load integration file", integ, "error was", e.args[1]
    sys.exit(12)
except ValueError:
    print >>sys.stderr, "Conversion error on", integ
    sys.exit(13)

frequencies, powers = LombScargle(timings, sums).autopower(minimum_frequency=1/endp, maximum_frequency=1/startp, samples_per_peak=numb)
pers = 1 / frequencies

try:
    np.savetxt(outspec, np.transpose(np.array([pers, powers])))
except IOError as e:
    print >>sys.stderr, "Could not save output file", outspec, "error was", e.args[1]
    sys.exit(20)
