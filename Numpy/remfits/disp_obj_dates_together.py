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
parsearg.add_argument('--bins', type=int, default=50, help='Number of bins for histogram')
parsearg.add_argument('--colour', type=str, default='b:g:r', help='Colour of histogram bars colon sep')
parsearg.add_argument('--monthint', type=int, default=3, help='Month interval for X axis')
rg.disp_argparse(parsearg, fmt='single')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
bins = resargs['bins']
colour = resargs['colour'].split(':') * 3
monthint = resargs['monthint']
ofig = rg.disp_getargs(resargs)

mydb, mycurs = remdefaults.opendb()

tdlist = []
for targ in ('Prox.*', 'Barn.*', 'Ross.*'):
    mycurs.execute("select date(date_obs) as odate,count(*) from obsinf where dithID=0 and object regexp %s group by odate order by odate", targ)
    rows = mycurs.fetchall()
    targdates = []
    for dat, count in rows:
        md = mdates.date2num(dat)
        for x in range(0, count):
            targdates.append(md)
    tdlist.append(targdates)
mydb.close()

fign = rg.plt_figure()
axs = fign.subplots(3, sharex=True, gridspec_kw={'hspace': 0})
df = mdates.DateFormatter("%b %Y")
ax = fign.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=monthint))
ax.xaxis.set_major_formatter(df)

for n, l in zip(range(0, 3), ('Proxima Centauri', "Barnard's Star", "Ross 154")):
    axs[n].hist(tdlist[n], bins=bins, color=colour[n])
    axs[n].set_ylabel('Observations')
    axs[n].legend([l])

plt.xticks(rotation=45)
plt.xlabel("Date")

if ofig is None:
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    plt.gcf().savefig(ofig)
