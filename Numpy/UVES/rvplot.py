#! /usr/bin/env python

# Apply X-ray file to UVES data to mark

import sys
import os
import string
import os.path
import locale
import argparse
import numpy as np
import miscutils
import jdate
import datetime
import matplotlib.pyplot as plt
from matplotlib import dates
import splittime
import histandgauss

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Plot RV table from Barnes14')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=8)
parsearg.add_argument('--splittime', help='Split plot segs on value', type=float, default=1.5)
parsearg.add_argument('--outfile', help='Prefix for output file', type=str)
parsearg.add_argument('rvfile', type=str, nargs=1, help='File of RVs')

resargs = vars(parsearg.parse_args())

rvfile = resargs['rvfile'][0]
splitem = resargs['splittime']
outfile = resargs['outfile']

figuresize = (resargs['width'], resargs['height'])

try:
    datafile = np.loadtxt(rvfile, unpack=True)
except IOError as e:
    print "Could not load", rvfile, "error was", e.args[1]
    sys.exit(10)

if datafile.shape[0] != 5:
    print "Expecting 5 columns of data in", rvfile, "not", datafile.shape[0]
    sys.exit(11)

ddates, drvs, derrs, icrv, acrv = datafile

dtdates = np.array([jdate.jdate_to_datetime(d) for d in ddates])

splits = splittime.splittime(splitem * SECSPERDAY, dtdates, drvs, derrs, icrv, acrv)

if len(splits) != 3:
    print "Expecting data to split over 3 days not", len(splits)
    sys.exit(12)

# Formatting operation to display times as hh:mm

hfmt = dates.DateFormatter('%H:%M')

for daydata in splits:

    day_dtdates, day_rvs, day_errs, day_icrv, day_acrv = daydata

    fig = plt.figure(figsize=figuresize)
    plt.subplots_adjust(hspace = 0)
    fig.canvas.set_window_title(day_dtdates[0].strftime("For %d %b %Y"))
    topax = plt.subplot(2, 1, 1)
    plt.errorbar(day_dtdates, day_rvs, yerr=day_errs, color='black', ecolor='r')
    plt.ylabel('Uncorrected RVs m/s')

    botax = plt.subplot(2, 1, 2, sharex=topax)
    botax.xaxis.set_major_formatter(hfmt)
    plt.gcf().autofmt_xdate()
    plt.plot(day_dtdates, day_icrv)
    plt.plot(day_dtdates, day_acrv)
    plt.axhline(0, color='black')
    plt.legend(['Ind corr', 'Overall corr'])
    plt.ylabel('Corrected Rvs m/s')
    plt.xlabel('Time UTC')
    if outfile is not None:
        fig.savefig(outfile + day_dtdates[0].strftime("rvs_%d%b.png"))

if outfile is None:
    plt.show()
