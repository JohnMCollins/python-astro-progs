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
parsearg.add_argument('--title', type=str, help='Title for plot')
parsearg.add_argument('--width', type=float, default=10.0, help='Width of plot')
parsearg.add_argument('--height', type=float, default=12.0, help='height of plot')
           
resargs = vars(parsearg.parse_args())
fnames = resargs['file']
tit = resargs['title']
width = resargs['width']
height = resargs['height']

plt.figure(figsize=(width,height))

hrloc = mdates.HourLocator()
minloc = mdates.MinuteLocator()
secloc = mdates.SecondLocator()
df = mdates.DateFormatter('%H:%M')
ax = plt.gca()
ax.xaxis.set_major_locator(minloc)
ax.xaxis.set_major_formatter(df)
#ax.xaxis.set_minor_locator(secloc)

#ax.format_xdata = mdates.DateFormatter('%H:%M')

legs = []
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
    
    plt.plot(dates, rats)
    legs.append("Filter " + fnbits[0])

plt.legend(legs, loc='best')
plt.xticks(rotation=90)
plt.xlabel("Time of observation HH:MM")
plt.ylabel("Brightness relative to reference object")
plt.title(tit)
plt.show()
