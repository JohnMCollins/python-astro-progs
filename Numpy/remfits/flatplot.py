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
import dbops
import remdefaults

mydbname = remdefaults.default_database()
parsearg = argparse.ArgumentParser(description='Plot stats for daily flat files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--filter', type=str, required=True, help='FIlter to select')
parsearg.add_argument('--fromdate', type=str, help='Earliest date/time to select')
parsearg.add_argument('--todate', type=str, help='Latest date/time to select')
parsearg.add_argument('--forcerange', action='store_true', help='Force x asis to fit from/to dates')
parsearg.add_argument('--margin', type=int, default=0, help='Margin on x asix in minutes or days')
parsearg.add_argument('--title', type=str, default='Means by date', help='Title for plot')
parsearg.add_argument('--legends', action='store_false', help='Turn on/off legend')
parsearg.add_argument('--dayint', type=int, help='Interval between dates')
parsearg.add_argument('--outfig', type=str, help='Output file rather than display')
parsearg.add_argument('--marker', type=str, default=',', help='Marker style for scatter plot')
parsearg.add_argument('--lower', type=int, default=5000, help='Lower limit of means')
parsearg.add_argument('--upper', type=int, default=50000, help='Upper limit of means')
parsearg.add_argument('--clip', action='store_true', help='Clip means rather t han darw lines')
parsearg.add_argument('--errorbars', action='store_true', help='Plot with error bars rather than scatter')
parsearg.add_argument('--showskew', action='store_true', help='Show skew and kurtosis')
parsearg.add_argument('--colours', type=str, default='b,g,r', help='Colours for plot, skew, kurtosis')
parsearg.add_argument('--smax', type=float, default=0.0, help='Max limit for skew"')
parsearg.add_argument('--kmax', type=float, default=7.0, help='Max limit for kurtosis')
parsearg.add_argument('--skclip', action='store_true', help='Clip values outside upper limit for skew and kurtosis')

resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
filter = resargs['filter']
title = resargs['title']
forcerange = resargs['forcerange']
fromdate = resargs['fromdate']
todate = resargs['todate']
margin = resargs['margin']
tit = resargs['title']
plegend = resargs['legends']
dayint = resargs['dayint']
marker = resargs['marker']
ofig = resargs['outfig']
llim = resargs['lower']
ulim = resargs['upper']
clip = resargs['clip']
errorbars = resargs['errorbars']
showskew = resargs['showskew']
colours = resargs['colours'].split(',') * 3
smax = resargs['smax']
kmax = resargs['kmax']
skclip = resargs['skclip']

dsel = ""
if fromdate is not None:
    fromdate = parsetime.parsetime(fromdate)
    fromdate = fromdate.strftime("%Y-%m_%d")
    if todate is not None:
        todate = parsetime.parsetime(todate)
        todate = todate.strftime("%Y-%m_%d")
        dsel = " AND date(date_obs) >= '" + fromdate + "' AND date(date_obs) <= '" + todate + "'"
    else:
        todate = "(end)"
        dsel = " AND date(date_obs) >= '" + fromdate + "'"
elif todate is not None:
    fromdate = "(beginning)"
    todate = parsetime.parsetime(todate)
    todate = todate.strftime("%Y-%m_%d")
    dsel = " AND sRWe(date_obs) <= '" + todate + "'"
else:
    fromdate = "(beginning)"
    todate = "(end)"

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

dbcurs.execute("SELECT date_obs,mean,std,skew,kurt FROM iforbinf WHERE skew IS NOT NULL AND typ='flat' AND gain=1 AND filter='" + filter + "'" + dsel + " ORDER by date_obs")

stuff = dbcurs.fetchall()

dates = []
means = []
stds = []
skews = []
kurts = []

for dat, mn, st, sk, kt in stuff:
    dates.append(dat)
    means.append(mn)
    stds.append(st)
    skews.append(sk)
    kurts.append(kt)

if clip or skclip:
    dates = np.array(dates)
    means = np.array(means)
    stds = np.array(stds)
    skews = np.array(skews)
    kurts = np.array(kurts)
    if clip:
        sel = (means >= llim) & (means <= ulim)
        dates = dates[sel]
        means = means[sel]
        stds = stds[sel]
        skews = skews[sel]
        kurts = kurts[sel]
    if skclip:
        sel = (skews < smax) & (kurts < kmax)
        dates = dates[sel]
        means = means[sel]
        stds = stds[sel]
        skews = skews[sel]
        kurts = kurts[sel]
try:
    mindate = min(dates)
    maxdate = max(dates)
except ValueError:
    print("Nothing found between", fromdate, "and", todate, "for filter", filter, file=sys.stderr)
    sys.exit(1)

rg = remgeom.load()
plt.figure(figsize=(rg.width, rg.height))
ax1 = plt.gca()

plt.xlim(mindate, maxdate)
plt.ylim(0, 66000)
sd = mindate.toordinal()
ed = maxdate.toordinal() + 1
dlist = [datetime.datetime.fromordinal(x) for x in range(sd, ed, dayint)]
plt.xticks(dlist, rotation=45)
plt.xlabel("Date of observation")
ax1.set_ylabel("Mean value")
df = mdates.DateFormatter("%Y-%m-%d")
ax1.xaxis.set_major_formatter(df)

if errorbars:
    c1 = ax1.errorbar(dates, means, stds, fmt='o', label='Means', color=colours[0])
else:
    c1 = ax1.scatter(dates, means, marker=marker, label='Means', color=colours[0])

if showskew:
    ax2 = ax1.twinx()
    ax2.set_ylabel("Skew and Kurtosis")
    c2 = ax2.scatter(dates, skews, marker=marker, label='Sjew', color=colours[1])
    c3 = ax2.scatter(dates, kurts, marker=marker, label='Kurtosis', color=colours[2])
    # ax1.legend(['Means'])
    # ax2.legend(["Skew", "Kurtosis"])
    curves = (c1, c2, c3)
    ax2.legend(curves, [curve.get_label() for curve in curves])

if not clip:
    ax1.axhline(ulim, color='k')
    ax1.axhline(llim, color='k')
plt.title(tit)
if ofig is None:
    plt.show()
else:
    plt.gcf().savefig(ofig)
