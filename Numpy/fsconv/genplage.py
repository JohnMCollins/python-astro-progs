#! /usr/bin/env python

# Program to convert fake spectra array to files of spectra looking like ones we know and love

import argparse
import sys
import os.path
import numpy as np
import numpy.random as nr
from scipy.stats import cosine
import datarange

parsearg = argparse.ArgumentParser(description='Generate a random plage file')
parsearg.add_argument('outfile', help="Generated plage file", nargs=1, type=str)
parsearg.add_argument('--force', help='Force overwrite of existing file', action='store_true')
parsearg.add_argument('--percent', type=float, default=2.0, help='Percentage of surface to fill')
parsearg.add_argument('--number', type=int, default=10, help='Number of spots to create')
parsearg.add_argument('--maxdeg', type=float, default=40.0, help='Maximum degrees for spot size')
parsearg.add_argument('--mindeg', type=float, default=1.0, help='Minimum degrees for spot size')
parsearg.add_argument('--latrange', type=str, default='-90:90', help='Range of latitudes (default all)')
parsearg.add_argument('--longrange', type=str, default='0:360', help='Range of longitudes (default all)')
parsearg.add_argument('--taillat', action='store_true', help='Reduce spot size at high latitudes')
parsearg.add_argument('--cosdist', action='store_true', help='Use cosine distribution of latitudes')
resargs = vars(parsearg.parse_args())

outfile = resargs['outfile'][0]
number = resargs['number']
maxdeg = resargs['maxdeg']
mindeg = resargs['mindeg']
perc = resargs['percent']

if number <= 0:
    print "Invalid number must be greater than 0"
    sys.exit(10)

if maxdeg <= mindeg or mindeg <= 0.0:
    print "Invalid maxima and minima"
    sys.exit(11)

if os.path.exists(outfile) and not resargs['force']:
    print "Will not overwrite existing", outfile
    sys.exit(12)

try:
    latrange = datarange.ParseArg(resargs['latrange'])
    longrange = datarange.ParseArg(resargs['longrange'])
    if latrange.lower < -90.0 or latrange.upper > 90.0:
        raise datarange.DataRangeError("Invalid latitude range")
    if longrange.lower < 0.0 or longrange.upper > 360.0:
        raise datarange.DataRangeError("Invalid longitude range")
except datarange.DataRangeError as e:
    print "Error in lat/long range", e.args[0]
    sys.exit(13)

longs = nr.uniform(longrange.lower, longrange.upper, size=number)
sizes = np.sqrt(nr.uniform(mindeg**2, maxdeg**2, size=number))
if resargs['cosdist']:
    cosrv = cosine(scale = 90.0 / np.pi)
    while 1:
        lats = cosrv.rvs(size = number * 4)
        lats = lats[(lats >= latrange.lower) & (lats <= latrange.upper)]
        if len(lats) >= number:
            break
    lats = lats[0:number]
else:
    lats = nr.uniform(latrange.lower, latrange.upper, size=number)

prop = np.zeros_like(longs) + 1.99
gsize = np.zeros_like(longs) + 10.0

repos = longs.argsort()
longs = longs[repos]
lats = lats[repos]
sizes = sizes[repos]

if resargs['taillat']:
    sizes *= np.cos(lats * np.pi / 180.0)

# Prune the list down if needed to the required cover
# Area is proportianal to the square of the radius, at most 90

accsizes = np.cumsum((sizes / 90.0) ** 2) * 100.0
pind = np.where(accsizes >= perc)[0]
if len(pind) > 1:
    resperc = accsizes[pind[0]]
    pind = pind[1]
    longs = longs[0:pind]
    lats = lats[0:pind]
    sizes = sizes[0:pind]
    prop = prop[0:pind]
    gsize = gsize[0:pind]
else:
    resperc = accsizes[-1]

result = np.array([longs, lats, sizes, prop, gsize]).transpose()

np.savetxt(outfile, result, fmt='%#12.8g')
print "Percent cover = %.2F" % resperc
