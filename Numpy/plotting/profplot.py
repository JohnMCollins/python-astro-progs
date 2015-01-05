#! /usr/bin/env python

import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import argparse
import string

import lutdata

parsearg = argparse.ArgumentParser(description='Display flux profile file')
parsearg.add_argument('profile', type=str, nargs=1, help='LUT file optionally followed by point args')
parsearg.add_argument('--outfile', type=str, help='Output file if required')
parsearg.add_argument('--width', type=float, help='Width of figure', default=8.0)
parsearg.add_argument('--height', type=float, help='Height of figure', default=6.0)
parsearg.add_argument('--forkoff', action='store_true', help='Fork off process to display results')

resargs = vars(parsearg.parse_args())

arg = resargs['profile'][0]

try:
	pf = np.loadtxt(arg, unpack=True)
except IOError as e:
    print "Could not open", lutf, "error was", e.args[1]
    sys.exit(10)

outf = resargs['outfile']

if outf is not None or (resargs['forkoff'] and os.fork() != 0):
    sys.exit(0)

plt.xlabel('Wavelength offset')
plt.ylabel('Intensity')
plt.plot(pf[0], pf[1])

if outf is not None:
    try:
        plt.savefig(outf)
        sys.exit(0)
    except IOError as e:
        print "Could not save to", outf, "error was", e.args[1]
        sys.exit(30)
try:
    plt.show()
except KeyboardInterrupt:
    pass
