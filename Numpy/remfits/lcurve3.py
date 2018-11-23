#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T18:57:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: lcurve3.py
# @Last modified by:   jmc
# @Last modified time: 2018-11-22T23:31:08+00:00

import matplotlib.pyplot as plt
import matplotlib.patches as mp
import matplotlib.dates as mdates
from matplotlib import colors
import numpy as np
import argparse
import sys
import string
import datetime
import parsetime

parsearg = argparse.ArgumentParser(description='Plot light curves', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs='+', help='imtabulate results files')
parsearg.add_argument('--fromdate', type=str, help='Earliest date/time to select')
parsearg.add_argument('--todate', type=str, help='Latest date/time to select')
parsearg.add_argument('--title', type=str, default='Light curve', help='Title for plot')
parsearg.add_argument('--width', type=float, default=10.0, help='Width of plot')
parsearg.add_argument('--height', type=float, default=12.0, help='height of plot')
parsearg.add_argument('--printdates', action='store_true', help='Print dates oN x axis')
parsearg.add_argument('--dayint', type=int, help='Interval between dates')
parsearg.add_argument('--outfig', type=str, help='Output file rather than display')
parsearg.add_argument('--line', action='store_true', help='Use line plots rather than scatter')

resargs = vars(parsearg.parse_args())
fnames = resargs['file']
fromdate = resargs['fromdate']
todate = resargs['todate']
tit = resargs['title']
width = resargs['width']
height = resargs['height']
printdates = resargs['printdates']
dayint = resargs['dayint']
lineplot = resargs['line']

if fromdate is not None:
    fromdate = parsetime.parsetime(fromdate)
    if fromdate.hour == 12 and fromdate.minute == 0:
        fromdate = datetime.datetime(fromdate.year, fromdate.month, fromdate.day, 0, 0, 0)
    if todate is None:
        todate = datetime.datetime(fromdate.year, fromdate.month, fromdate.day, 23, 59, 59)
    else:
        todate = parsetime.parsetime(todate)
        if todate.hour == 0 and todate.minute == 0:
            todate = datetime.datetime(todate.year, todate.month, todate.day, 23, 59, 59)

plt.figure(figsize=(width,height))

hrloc = mdates.HourLocator()
minloc = mdates.MinuteLocator()
secloc = mdates.SecondLocator()
if printdates:
    df = mdates.DateFormatter("%Y-%m-%d")
else:
    df = mdates.DateFormatter('%H:%M')
ax = plt.gca()
ax.xaxis.set_major_locator(minloc)
ax.xaxis.set_major_formatter(df)
#ax.xaxis.set_minor_locator(secloc)

#ax.format_xdata = mdates.DateFormatter('%H:%M')

legs = []
mindate = None
maxdate = None

for flin in fnames:
    f, leg, colour = string.split(flin, ':')
    parts = []
    for lin in open(f):
        bits = string.split(lin, ' ')
        try:
            fd = bits[0] + ' ' + bits[1]
            fd = fd[0:-1]
            dt = datetime.datetime.strptime(fd, "%Y-%m-%d %H-%M-%S")
        except ValueError:
            print "Had val error with date", fd
            continue
        if fromdate is not None and (fromdate > dt or todate < dt):
            continue
        rat = float(bits[2])
        parts.append((dt, rat))

    if len(parts) == 0: continue

    dates = [p[0] for p in parts]
    rats = [rat[-1] for rat in parts]

    mind = min(dates)
    maxd = max(dates)
    if mindate is None:
        mindate = mind
    else:
        mindate = min(mindate, mind)
    if maxdate is None:
        maxdate = maxd
    else:
        maxdate = max(maxdate, maxd)

    dates = np.array(dates)
    rats = np.array(rats)
    sa = dates.argsort()

    if lineplot:
        plt.plot(dates[sa], rats[sa], color=colour)
    else:
        pdates = dates[sa]
        offset = min(pdates[-1]-pdates[-2],pdates[1]-pdates[0])
        plt.xlim(pdates.min() - offset, pdates.max() + offset)
        plt.scatter(pdates, rats[sa], color=colour)

    legs.append(leg)

plt.legend(legs)

ylo, yhi = plt.ylim()
if ylo < 0.0:
	plt.gca().set_ylim(0, yhi)

#plt.legend(legs, loc='best')
if printdates:
    if dayint is None:
        dayint = 1
    sd = mindate.toordinal()
    ed = maxdate.toordinal()+1
    dlist = [datetime.datetime.fromordinal(x) for x in range(sd, ed, dayint)]
    plt.xticks(dlist, rotation=45)
    plt.xlabel("Date of observation")
else:
    if dayint is None:
        plt.xticks(rotation=90)
    else:
        tsecs = (maxdate-mindate).seconds
        dlist = [mindate + datetime.timedelta(seconds=s) for s in np.linspace(0, tsecs, dayint)]
        plt.xticks(dlist, rotation=90)
    plt.xlabel("Time of observation HH:MM")
plt.ylabel("Brightness relative to reference object")
plt.title(tit)
ofig = resargs['outfig']
if ofig is None:
    plt.show()
else:
    plt.gcf().savefig(ofig)
