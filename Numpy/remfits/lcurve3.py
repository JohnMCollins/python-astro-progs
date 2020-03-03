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


def make_bucket(lastdate, bacc):
    """Make a bucket out of a section of the points"""

    global  stdclip, clipped

    if stdclip > 0.0:
        intens = np.array([targinten / denom for targinten, denom, obsind, dt in bacc])
        bmean = np.mean(intens)
        bstd = np.std(intens) * stdclip
        if bstd > 0.0:
            intens -= bmean
            newbacc = []
            for inten, bb in zip(intens, bacc):
                if abs(inten) > bstd:
                    diff = (inten * stdclip) / bstd
                    clipped.append((bb[2], bb[3], diff))
                else:
                    newbacc.append(bb)
            bacc = newbacc

    tis = [x[0] for x in bacc]
    rfs = [x
    [1] for x in bacc]
    return  (lastdate, len(bacc), np.sum(tis), np.sum(rfs), np.std(tis), np.std(rfs))


rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Plot light curves', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs='+', help='Results files from dblcuregen')
parsearg.add_argument('--columns', type=str, help='Columns to select for reference objects')
parsearg.add_argument('--fromdate', type=str, help='Earliest date/time to select')
parsearg.add_argument('--todate', type=str, help='Latest date/time to select')
parsearg.add_argument('--forcerange', action='store_true', help='Force x asis to fit from/to dates')
parsearg.add_argument('--margin', type=int, default=0, help='Margin on x asix in minutes or days')
parsearg.add_argument('--title', type=str, default='Light curve', help='Title for plot')
parsearg.add_argument('--legends', action='store_false', help='Turn on/off legend')
parsearg.add_argument('--printdates', action='store_true', help='Print dates oN x axis')
parsearg.add_argument('--dayint', type=int, help='Interval between dates')
parsearg.add_argument('--line', action='store_true', help='Use line plots rather than scatter')
parsearg.add_argument('--bucket', action='store_true', help='Bucket days')
parsearg.add_argument('--sepbuck', type=int, default=12, help='Bucket separation in hours')
parsearg.add_argument('--buckls', type=str, default='none', help='Line style for error bars')
parsearg.add_argument('--normalise', type=str, default='none', help='Normalisation none/range/all')
parsearg.add_argument('--marker', type=str, default=',', help='Marker style for scatter plot')
parsearg.add_argument('--stdclip', type=float, default=0.0, help='Number of std devs to clip results')
parsearg.add_argument('--clipfile', type=str, help='File to objsinds of clipped results')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
fnames = resargs['file']
columns = resargs['columns']
if columns is not None:
    columns = [int(x) for x in string.split(columns, ',')]
title = resargs['title']
fromdate = resargs['fromdate']
todate = resargs['todate']
margin = resargs['margin']
tit = resargs['title']
plegend = resargs['legends']
bucket = resargs['bucket']
buckls = resargs['buckls']
printdates = resargs['printdates'] or bucket
dayint = resargs['dayint']
lineplot = resargs['line']
sepbuck = resargs['sepbuck']
marker = resargs['marker']
normalise = resargs['normalise']
if len(normalise) == 0 or normalise[0] not in 'arn':
    print("Normalise argument unknown please use n/r/a", file=sys.stderr)
    sys.exit(10)
normalise = normalise[0]
stdclip = resargs['stdclip']
clipfile = resargs['clipfile']
ofig = rg.disp_getargs(resargs)

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

forcerange = resargs['forcerange']

rg.plt_figure()

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
# ax.xaxis.set_minor_locator(secloc)

# ax.format_xdata = mdates.DateFormatter('%H:%M')

legs = []
mindate = None
maxdate = None
objectnames = None

clipped = []

for flin in fnames:
    f, leg, colour = string.split(flin, ':')
    parts = []
    lcount = 0
    for lin in open(f):
        bits = string.split(lin)
        lcount += 1
        if lcount < 3:
            # Extract object names from first line
            if lcount == 1:
                bits.pop(0)
                bits.pop(0)
                bits.pop(0)
                if objectnames is None:
                    objectnames = bits
                else:
                    for o, b in zip(objectnames, bits):
                        if o != b:
                            print("Objectnames differ between files", ','.join(objectnames), "-v-", ','.join(bits), file=sys.stderr)
                            sys.exit(200)
            continue

        dt = dateutil.parser.parse(bits.pop(0))
        obsind = int(bits.pop(0))
        exptime = float(bits.pop(0))

        targinten = float(bits[0])
        denom = 1.0

        if columns is not None:
            denom = 0.0
            try:
                for c in columns:
                    p = float(bits[c])
                    if p < 0.0:
                        raise ValueError
                    denom += p
            except ValueError:
                continue
            if denom <= 0.0:
                continue
            # targinten /= denom

        parts.append((dt, obsind, targinten, denom))

    if len(parts) == 0:
        continue

    if stdclip > 0.0 and not bucket:
        clippedsome = 0
        intlist = np.array([ targinten / denom for dt, obsind, targinten, denom in parts ])
        mint = np.mean(intlist)
        mstd = np.std(intlist)
        denom = mint * mstd
        intlist -= mint
        newparts = []
        for inten, p in zip(intlist, parts):
            diff = inten / denom
            if abs(diff) > stdclip:
                clipped.append((p[1], p[0], diff))
                clippedsome += 1
            else:
                newparts.append(p)

            if clippedsome > 0:
                parts = newparts
                if len(parts) == 0:
                    continue

    if bucket:
        diffsepbuck = datetime.timedelta(hours=sepbuck)
        lastdate = datetime.datetime(2000, 1, 1, 0, 0, 0)
        bparts = []
        bacc = []
        for dt, obsind, targinten, denom in parts:
            if dt - lastdate > diffsepbuck:
                if len(bacc) != 0:
                    tis = [x[0] for x in bacc]
                    rfs = [x[1] for x in bacc]
                    bparts.append(make_bucket(lastdate, bacc))
                    bacc = []
                lastdate = dt
            bacc.append((targinten, denom, obsind, dt))
        if  len(bacc) != 0:
            bparts.append(make_bucket(lastdate, bacc))

        # Now assemble parts array as (date, value, error)
        # Also apply normalisation

        parts = []
        for dt, num, targinten, refinten, targstd, refstd in bparts:
            errmult = math.sqrt(float(num))
            targerr = targstd * errmult
            if columns is not None:
                referr = refstd * errmult
                targerr = math.sqrt((targerr / targinten) ** 2 + (referr / refinten) ** 2)
                targinten /= refinten
            else:
                targinten /= float(num)
            parts.append((dt, targinten, targerr))

        if normalise == 'a':
            meanval = np.mean([inten for dt, inten, err in parts])
            parts = [(dt, inten / meanval, err / meanval) for dt, inten, err in parts]
        if fromdate is not None:
            parts = [(dt, inten, err) for dt, inten, err in parts if dt >= fromdate and dt <= todate]
        if len(parts) == 0:
            continue
        if normalise == 'r':
            meanval = np.mean([inten for dt, inten, err in parts])
            parts = [(dt, inten / meanval, err / meanval) for dt, inten, err in parts]

        dates = [p[0] for p in parts]
        rats = [rat[1] for rat in parts]
        errs = [err[2] for err in parts]

        plt.errorbar(dates, rats, errs, color=colour, linestyle=buckls, fmt='o')

    else:

        if columns is not None:
            parts = [(dt, obsind, inten / refinten, 1.0) for dt, obsind, inten, refinten in parts]

        if normalise == 'a':
            meanval = np.mean([inten for dt, obsind, inten, refinten in parts])
            parts = [(dt, obsind, inten / meanval, 1.0) for dt, obsind, inten, refinten in parts]
        if fromdate is not None:
            parts = [(dt, obsind, inten, 1.0) for dt, obsind, inten, refinten in parts if dt >= fromdate and dt <= todate]
        if len(parts) == 0:
            continue
        if normalise == 'r':
            meanval = np.mean([inten for dt, obsind, inten, refinten in parts])
            parts = [(dt, obsind, inten / meanval) for dt, obsind, inten, refinten in parts]

        dates = [p[0] for p in parts]
        rats = [rat[2] for rat in parts]

        if lineplot:
            plt.plot(dates, rats, color=colour)
        else:
            plt.scatter(dates, rats, color=colour, marker=marker)

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

    legs.append(leg)

if len(clipped) != 0 and clipfile is not None:
    print(clipped)
    clipped.sort(key=lambda x:-abs(x[2]))
    clipout = open(clipfile, "wt")
    for obsind, dt, idiff in clipped:
        print(dt.isoformat(), "%8d %.6e" % (obsind, idiff), file=clipout)
    clipout.close()

if len(legs) == 0:
    print("Nothing to plot", file=sys.stderr)
    sys.exit(1)

if plegend:
    plt.legend(legs)

if not lineplot:
    fd = mindate
    td = maxdate
    if margin != 0:
        if printdates:
            offs = datetime.timedelta(days=margin)
        else:
            offs = datetime.timedelta(minutes=margin)
        fd -= offs
        td += offs
    if forcerange and fromdate is not None:
        fd = fromdate
        td = todate
    plt.xlim(fd, td)

ylo, yhi = plt.ylim()
if ylo < 0.0:
	plt.gca().set_ylim(0, yhi)

if printdates:
    if dayint is None:
        dayint = 1
    sd = mindate.toordinal()
    ed = maxdate.toordinal() + 1
    dlist = [datetime.datetime.fromordinal(x) for x in range(sd, ed, dayint)]
    plt.xticks(dlist, rotation=45)
    plt.xlabel("Date of observation")
else:
    if dayint is None:
        plt.xticks(rotation=90)
    else:
        tsecs = (maxdate - mindate).seconds
        dlist = [mindate + datetime.timedelta(seconds=s) for s in np.linspace(0, tsecs, dayint)]
        plt.xticks(dlist, rotation=90)
    plt.xlabel("Time of observation HH:MM")

targname = objectnames[0]
relto = ""
if columns is not None:
    relto = [objectnames[c] for c in columns]
    if len(relto) == 1:
        relto = relto[0]
    else:
        relto = "sum of" + ', '.join(relto)
    relto = " relative to sum of " + relto

ylab = "Brightness of " + targname + relto
if normalise != 'n':
    if normalise == "r" and fromdate is not None:
        ylab += " norm to range"
    else:
        ylab += " norm to all obs"

plt.ylabel(ylab)
plt.title(tit)
if ofig is None:
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    plt.gcf().savefig(ofig)
