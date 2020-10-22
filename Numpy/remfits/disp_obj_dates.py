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
import datetime
import dateutil
import parsetime
import remgeom
import remdefaults
import dbops
import miscutils

targd = dict(P=("Proxima Centauri", 'Prox.*'), B=("Barnard's Star", 'Barn.*'), R=("Ross 154", 'Ross.*'))

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Plot object obs by dates', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--target', type=str, required=True, choices=['P', 'B', 'R'], help='Target name P B or R for Proxima, Barnards or Ross154')
parsearg.add_argument('--bins', type=int, default=50, help='Number of bins for histogram')
parsearg.add_argument('--colour', type=str, default='b', help='Colour of histogram bars00000')
parsearg.add_argument('--monthint', type=int, default=3, help='Month interval for X axis')
rg.disp_argparse(parsearg, fmt='single')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
target = targd[resargs['target']]
bins = resargs['bins']
colour = resargs['colour']
monthint = resargs['monthint']
ofig = rg.disp_getargs(resargs)

mydb, mycurs = remdefaults.opendb()

mycurs.execute("select date(date_obs) as odate,count(*) from obsinf where dithID=0 and object regexp %s group by odate order by odate", target[1])
rows = mycurs.fetchall()
targdates = []
for dat, count in rows:
    md = mdates.date2num(dat)
    for x in range(0, count):
        targdates.append(md)
mydb.close()

rg.plt_figure()
df = mdates.DateFormatter("%b %Y")
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=monthint))
ax.xaxis.set_major_formatter(df)

plt.hist(targdates, bins=bins, color=colour)
plt.xticks(rotation=45)
plt.ylabel("Number of observations")
plt.xlabel("Date")
plt.title("Observations of %s by date" % target[0])

if ofig is None:
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    plt.gcf().savefig(ofig)
