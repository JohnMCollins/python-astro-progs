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
from astropy._erfa.core import dat

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Plot Prox/BS/Ross obs by dates', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--width', type=float, default=rg.width, help="Width of figure")
parsearg.add_argument('--height', type=float, default=rg.height, help="height of figure")
parsearg.add_argument('--marker', type=str, default=',', help='Marker style for scatter plot')
parsearg.add_argument('--outfig', type=str, help='Output file rather than display')

resargs = vars(parsearg.parse_args())
dbname = resargs['database']
width = resargs['width']
height = resargs['height']
marker = resargs['marker']
ofig = resargs['outfig']

mydb = dbops.opendb(dbname)
mycurs = mydb.cursor()

mycurs.execute("select date(date_obs) as odate,count(*) from obsinf where dithID=0 and object regexp 'Prox.*' group by odate order by odate")
rows = mycurs.fetchall()
proxdates = []
proxcounts = []
for dat, count in rows:
    proxdates.append(dat)
    proxcounts. append(count)
mycurs.execute("select date(date_obs) as odate,count(*) from obsinf where dithID=0 and object regexp 'Barn.*' group by odate order by odate")
rows = mycurs.fetchall()
barndates = []
barncounts = []
for dat, count in rows:
    barndates.append(dat)
    barncounts. append(count)
mycurs.execute("select date(date_obs) as odate,count(*) from obsinf where dithID=0 and object regexp 'Ross.*' group by odate order by odate")
rows = mycurs.fetchall()
rossdates = []
rosscounts = []
for dat, count in rows:
    rossdates.append(dat)
    rosscounts. append(count)
mydb.close()

plt.figure(figsize=(width, height))
df = mdates.DateFormatter("%b %Y")
hrloc = mdates.HourLocator()
minloc = mdates.MinuteLocator()
secloc = mdates.SecondLocator()
ax = plt.gca()
ax.xaxis.set_major_locator(minloc)
ax.xaxis.set_major_formatter(df)

mindate = min(proxdates+barndates+rossdates)
maxdate = max(proxdates+barndates+rossdates)
sd = mindate.toordinal()
ed = maxdate.toordinal()+1
plt.xlim(sd, ed)
dlist = []
nextd = mindate + dateutil.relativedelta.relativedelta(day=1) + dateutil.relativedelta.relativedelta(months=1)
while nextd < maxdate:
    dlist.append(nextd)
    nextd += dateutil.relativedelta.relativedelta(months=1)
plt.xticks(dlist, rotation=45)
plt.xlabel("Date of observation")
plt.ylabel("Number of obs (visible light filters)")
plt.title("Observations of main targets by date")

plt.scatter(proxdates, proxcounts, color='r', marker=marker)
plt.scatter(barndates, barncounts, color='g', marker=marker)
plt.scatter(rossdates, rosscounts, color='b', marker=marker)
plt.legend(['Proxima Centauri', "Barnard's Star", 'Ross 154'])

ofig = resargs['outfig']
if ofig is None:
    plt.show()
else:
    plt.gcf().savefig(ofig)
