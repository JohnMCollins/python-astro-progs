#! /usr/bin/env python

import argparse
import matplotlib.pyplot as plt
import numpy as np
import string
import sys
import os
import rangearg

parsearg = argparse.ArgumentParser(description='Display range for use as range arg')

parsearg.add_argument('--col', type=int, default=1, help='Column of data to use')
parsearg.add_argument('--pad', type=float, default=0.1, help='Padding to add either side')
parsearg.add_argument('spectra', type=str, nargs='+', help='Spectra to analyse')

resargs = vars(parsearg.parse_args())

column = resargs['col']
padding = resargs['pad']
spectra = resargs['spectra']

errors = 0
done = 0

vmin = 1e90
vmax = -1e90

for spec in spectra:
    try:
        spect = np.loadtxt(spec, unpack=True)
    except IOError as e:
        print "Could not load", spec, "error was", e.args[1]
        errors += 1
        continue
    vals = spect[column]
    vmin = min(vmin, np.min(vals))
    vmax = max(vmax, np.max(vals))
    done += 1

if done <= 0:
    print "No files processed"
    sys.exit(10)

vmin -= padding
vmax += padding

print "%.6g,%.6g" % (vmin, vmax)
