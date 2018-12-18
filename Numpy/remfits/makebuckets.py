#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T18:57:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: lcurve3.py
# @Last modified by:   jmc
# @Last modified time: 2018-12-13T22:01:11+00:00

import numpy as np
import argparse
import sys
import math
import string
import datetime
import dateutil.parser
import parsetime
import remgeom

def make_bucket(lastdate, bacc):
    """Make a bucket out of a section of the points"""

    global  stdclip, clipped

    if stdclip > 0.0:
        intens = np.array([targinten/denom for targinten, denom, obsind, dt in bacc])
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

parsearg = argparse.ArgumentParser(description='Plot light curves', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs=1, help='Results files from dblcuregen')
parsearg.add_argument('--columns', type=str, help='Columns to select for reference objects')
parsearg.add_argument('--fromdate', type=str, help='Earliest date/time to select')
parsearg.add_argument('--todate', type=str, help='Latest date/time to select')
parsearg.add_argument('--outfile', type=str, help='Output file rather than stderr')
parsearg.add_argument('--bucket', action='store_true', help='Bucket days')
parsearg.add_argument('--sepbuck', type=int, default=12, help='Bucket separation in hours')
parsearg.add_argument('--normalise', type=str, default='none', help='Normalisation none/range/all')
parsearg.add_argument('--stdclip', type=float, default=0.0, help='Number of std devs to clip results')

resargs = vars(parsearg.parse_args())
fnames = resargs['file'][0]
columns = resargs['columns']
if columns is not None:
    columns = map(lambda x: int(x),string.split(columns, ','))
fromdate = resargs['fromdate']
todate = resargs['todate']
bucket = resargs['bucket']
sepbuck = resargs['sepbuck']
normalise = resargs['normalise']
if len(normalise) == 0 or normalise[0] not in 'arn':
    print >>sys.stderr, "Normalise argument unknown please use n/r/a"
    sys.exit(10)
normalise = normalise[0]
stdclip = resargs['stdclip']
outfile = resargs['outfile']

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

rg = remgeom.load()

mindate = None
maxdate = None
objectnames = None

# In case we're using same argument as for lcurve3

f = string.split(fnames, ':')[0]

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
            objectnames = bits
        continue

    dt = dateutil.parser.parse(bits.pop(0))
    obsind = int(bits.pop(0))

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
            print >>sys.stderr, "No inensity in columns"
            sys.exit(15)
        if denom <= 0.0:
            print >>sys.stderr, "No inensity in columns"
            sys.exit(16)

    parts.append((dt, obsind, targinten, denom))

if len(parts) == 0:
    print >>sys.stderr, "No results found"
    sys.exit(17)

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
            targerr = math.sqrt((targerr/targinten)**2 + (referr/refinten)**2)
            targinten /= refinten
        else:
            targinten /= float(num)
        parts.append((dt, targinten, targerr))

    if normalise == 'a':
        meanval = np.mean([inten for dt,inten,err in parts])
        parts = [(dt, inten/meanval, err/meanval) for dt, inten, err in parts]
    if fromdate is not None:
        parts = [(dt, inten, err) for dt, inten, err in parts if dt >= fromdate and dt <= todate]
    if len(parts) == 0:
        print >>sys.stderr, "No results found for dates"
        sys.exit(18)
    if normalise == 'r':
        meanval = np.mean([inten for dt,inten,err in parts])
        parts = [(dt, inten/meanval, err/meanval) for dt, inten, err in parts]

    dates = [p[0] for p in parts]
    rats = [rat[1] for rat in parts]

else:

    if columns is not None:
        parts = [(dt, obsind, inten/refinten, 1.0) for dt, obsind, inten, refinten in parts]

    if normalise == 'a':
        meanval = np.mean([inten for dt, obsind, inten, refinten in parts])
        parts = [(dt, obsind, inten/meanval, 1.0) for dt, obsind, inten, refinten in parts]
    if fromdate is not None:
        parts = [(dt, obsind, inten, 1.0) for dt, obsind, inten, refinten in parts if dt >= fromdate and dt <= todate]
    if len(parts) == 0:
        print >>sys.stderr, "No results found"
        sys.exit(17)

    if normalise == 'r':
        meanval = np.mean([inten for dt, obsind, inten, refinten in parts])
        parts = [(dt, obsind, inten/meanval) for dt, obsind, inten,refinten in parts]

    dates = [p[0] for p in parts]
    rats = [rat[2] for rat in parts]

firstdate = parts[0][0]
secsperday = 3600.0 * 24.0
ddiff = [(d - firstdate).seconds for d in dates]
results = np.array([ddiff, rats, rats]).transpose()
results[:,0] /= secsperday

if outfile is None:
    outfile = "/dev/stdout"

np.savetxt(outfile, results)
