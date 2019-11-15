#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T18:57:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: lcurve3.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:14+00:00

import matplotlib.pyplot as plt
import matplotlib.patches as mp
import matplotlib.dates as mdates
from matplotlib import colors
import numpy as np
import argparse
import sys
import math
import string
import remgeom
import dbops
import remdefaults
import dbremfitsobj
import os
import os.path
import trimarrays
from _pylief import parse

rg = remgeom.load()
mydbname = remdefaults.default_database()
tmpdir = remdefaults.get_tmpdir()

parsearg = argparse.ArgumentParser(description='Plot std deviation versus mean of daily flatsl', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
parsearg.add_argument('--divmean', action='store_true', help="Divide std dev by mean")
parsearg.add_argument('--filter', type=str, help='Restrict to given filter')
parsearg.add_argument('--title', type=str, default='Mean count of daily flats v Std devl', help='Title for plot')
parsearg.add_argument('--xlabel', type=str, default='Mean value', help='X axis label')
parsearg.add_argument('--ylabel', type=str, default='Std deviationl', help='Y axis label')
parsearg.add_argument('--outfig', type=str, help='Output file rather than display')
parsearg.add_argument('--colour', type=str, default='b', help='Plot points colour')
parsearg.add_argument('--width', type=float, default=rg.width, help="Width of figure")
parsearg.add_argument('--height', type=float, default=rg.height, help="height of figure")
parsearg.add_argument('--labsize', type=int, default=10, help='Label and title font size')
parsearg.add_argument('--ticksize', type=int, default=10, help='Tick font size')

resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
title = resargs['title']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
ofig = resargs['outfig']
colour = resargs['colour']
width = resargs['width']
height = resargs['height']
labsize = resargs['labsize']
ticksize = resargs['ticksize']
filter = resargs['filter']
divmean = resargs['divmean']

if ofig is not None:
    ofig = os.path.abspath(ofig)

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    print("Unable to select temporary directory", tmpdir, file=sys.stderr)
    sys.exit(100)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

plt.rc('xtick',labelsize=ticksize)
plt.rc('ytick',labelsize=ticksize)

if filter is None:
    dbcurs.execute("SELECT mean,std FROM iforbinf WHERE mean IS NOT NULL AND typ='flat' AND ind!=0 AND gain=1")
else:
    dbcurs.execute("SELECT mean,std FROM iforbinf WHERE mean IS NOT NULL AND typ='flat' AND ind!=0 AND gain=1 AND filter=" + dbase.escape(filter))

rows = np.array(dbcurs.fetchall())
if len(rows) < 20:
    print("Not enough data points found to plot", file=sys.stderr)
    sys.exit(2)

means = np.array(rows[:,0])
stdds = np.array(rows[:,1])
if divmean:
    stdds /= means
ass = np.argsort(stdds)
means = means[ass]
stdds = stdds[ass]
ass = np.argsort(means)
means = means[ass]
stdds = stdds[ass]


plt.figure(figsize=(width, height))
plt.plot(means, stdds, color=colour)
plt.title(title, fontsize=labsize)
plt.xlabel(xlab, fontsize=labsize)
plt.ylabel(ylab, fontsize=labsize)
if ofig is None:
    plt.show()
else:
    plt.gcf().savefig(ofig)
