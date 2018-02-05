#! /usr/bin/env python

import matplotlib.pyplot as plt
import matplotlib.patches as mp
import matplotlib.dates as mdates
from matplotlib import colors 
import numpy as np
import argparse
import sys
import string
import datetime

parsearg = argparse.ArgumentParser(description='Plot light curves', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs='+', help='IMcalc results files')
parsearg.add_argument('--title', type=str, default='Light curve', help='Title for plot')
parsearg.add_argument('--width', type=float, default=10.0, help='Width of plot')
parsearg.add_argument('--height', type=float, default=12.0, help='height of plot')
parsearg.add_argument('--printdates', action='store_true', help='Print dates oN x axis')
parsearg.add_argument('--dayint', type=int, help='Interval between dates')
parsearg.add_argument('--outfig', type=str, help='Output file rather than display')
           
resargs = vars(parsearg.parse_args())
fnames = resargs['file']
tit = resargs['title']
width = resargs['width']
height = resargs['height']
printdates = resargs['printdates']
dayint = resargs['dayint']

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

for f in fnames:
    fnbits = string.split(f, '.')
    parts = []
    for lin in open(f):
        bits = string.split(lin, ' ')
        if len(bits) != 4: continue
        dt = datetime.datetime.strptime(bits[0], "%Y-%m-%dT%H:%M:%S:")
        mo = float(bits[1])
        ro = float(bits[2])
        rat = float(bits[3])
        parts.append((dt, mo, ro, rat))
    
    if len(parts) == 0: continue
    
    dates = [p[0] for p in parts]
    rats = [rat[3] for rat in parts]
    
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
    
    plt.plot(dates[sa], rats[sa])
    legs.append("Filter " + fnbits[0])

plt.legend(legs, loc='best')
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

