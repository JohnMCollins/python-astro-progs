#! /usr/bin/env python

# Program to convert fake spectra array to files of spectra looking like ones we know and love

import argparse
import sys
import os.path
import numpy as np
import numpy.random as nr

parsearg = argparse.ArgumentParser(description='Generate a random plage file')
parsearg.add_argument('outfile', help="Generated plage file", nargs=1, type=str)
parsearg.add_argument('--force', help='Force overwrite of existing file', action='store_true')
parsearg.add_argument('--number', type=int, default=10, help='Number of spots to create')
parsearg.add_argument('--maxdeg', type=float, default=40.0, help='Maximum degrees for spot size')
parsearg.add_argument('--mindeg', type=float, default=1.0, help='Minimum degrees for spot size')
resargs = vars(parsearg.parse_args())

outfile = resargs['outfile'][0]
number = resargs['number']
maxdeg = resargs['maxdeg']
mindeg = resargs['mindeg']

if number <= 0:
    print "Invalid number must be greater than 0"
    sys.exit(10)

if maxdeg <= mindeg or mindeg <= 0.0:
    print "Invalid maxima and minima"
    sys.exit(11)

if os.path.exists(outfile) and not resargs['force']:
    print "Will not overwirte existing", outfile
    sys.exit(12)

longs = nr.uniform(0.0, 360.0, size=number)
lats = nr.uniform(-90.0, 90.0, size=number)
sizes = np.sqrt(nr.uniform(mindeg**2, maxdeg**2, size=number))

prop = np.zeros_like(longs) + 1.99
gsize = np.zeros_like(longs) + 10.0

repos = longs.argsort()

result = np.array([longs[repos], lats[repos], sizes[repos], prop, gsize]).transpose()

np.savetxt(outfile, result, fmt='%#12.8g')
