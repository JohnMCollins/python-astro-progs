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
import miscutils
import dbops
import remdefaults

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display usable rows/cols over time', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--filter', type=str, required=True, help='Filter to display for')
parsearg.add_argument('--title', type=str, default='Usable rows and columns', help='Title for plot')
parsearg.add_argument('--rowcolour', type=str, default='b', help='Colour for row display')
parsearg.add_argument('--colcolour', type=str, default='g', help='Colour for column display')
parsearg.add_argument('--legends', action='store_false', help='Turn on/off legend')
parsearg.add_argument('--dayint', type=int, help='Interval between dates')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
title = resargs['title']
filter = resargs['filter']
title = resargs['title']
plegend = resargs['legends']
rowcolour = resargs['rowcolour']
colcolour = resargs['colcolour']
dayint = resargs['dayint']
ofig = rg.disp_getargs(resargs)

mydb, dbcurs = remdefaults.opendb()
fieldselect = ["rejreason is NULL"]
fieldselect.append("ind!=0")
fieldselect.append("filter=" + mydb.escape(filter))

try:
    parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

datelist = []
rows = []
cols = []
for tab in ('obsinf', 'iforbinf'):
    selstmt = "select date_obs,nrows,ncols from " + tab + " where " + " and ".join(fieldselect)
    dbcurs.execute(selstmt)
    for row in dbcurs.fetchall():
        dat, r, c = row
        datelist.append(dat)
        rows.append(r)
        cols.append(c)

if len(datelist) == 0:
    print("No records to process withiin specified dates", file=sys.stderr)
    sys.exit(1)

datelist = np.array(datelist)
rows = np.array(rows)
cols = np.array(cols)
mindate = datelist.min()
maxdate = datelist.max()

order = datelist.argsort()
datelist = datelist[order]
rows = rows[order]
cols = cols[order]
msk = np.append([True], np.diff(datelist, 1) != 0)
datelist = datelist[msk]
rows = rows[msk]
cols = cols[msk]

plotfigure = rg.plt_figure()

hrloc = mdates.HourLocator()
minloc = mdates.MinuteLocator()
secloc = mdates.SecondLocator()
df = mdates.DateFormatter("%Y-%m-%d")
ax = plt.gca()
ax.xaxis.set_major_locator(minloc)
ax.xaxis.set_major_formatter(df)

plt.plot(datelist, rows, color=rowcolour)
plt.plot(datelist, cols, color=colcolour)
plt.legend(['Rows', "Columns"])
if dayint is None:
    dayint = 1
sd = mindate.toordinal()
ed = maxdate.toordinal() + 1
dlist = [datetime.datetime.fromordinal(x) for x in range(sd, ed, dayint)]
plt.xticks(dlist, rotation=45)

plt.xlabel("Date")
plt.ylabel("Size")
plt.title(title + "\nFilter " + filter)

if ofig is None:
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    plotfigure.savefig(ofig)
