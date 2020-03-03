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
import remgeom
import dbops
import remdefaults
import miscutils

rg = remgeom.load()
mydbname = remdefaults.default_database()

parsearg = argparse.ArgumentParser(description='Plot moon phase versus sky level', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--usedist', action='store_true', help='Take distance into account')
parsearg.add_argument('--filter', type=str, help='Restrict to given filter')
parsearg.add_argument('--target', type=str, help='Restrict to given target')
parsearg.add_argument('--title', type=str, default='Moon phase verus sky level', help='Title for plot')
parsearg.add_argument('--xlabel', type=str, default='Moon phase as percentage of full', help='X axis label')
parsearg.add_argument('--ylabel', type=str, default='Sky level', help='Y axis label')
parsearg.add_argument('--marker', type=str, default=',', help='Marker style for scatter plot')
parsearg.add_argument('--colour', type=str, default='b', help='Plot points colour')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
title = resargs['title']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
marker = resargs['marker']
colour = resargs['colour']
usedist = resargs['usedist']
filter = resargs['filter']
target = resargs['target']
ofig = rg.disp_getargs(resargs)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

if target is None and filter is None:
    dbcurs.execute("SELECT moonphase,moondist,skylevel,skystd FROM obscalc WHERE moonvis!=0")
else:
    parts = [ "obscalc.obsind=obsinf.obsind", "moonvis!= 0"]
    if target is not None:
        parts.append("object=" + dbase.escape(target))
    if filter is not None:
        parts.append("filter=" + dbase.escape(filter))
    whc = " AND ".join(parts)
    dbcurs.execute("SELECT obscalc.moonphase,obscalc.moondist,skylevel,skystd FROM obscalc INNER JOIN obsinf WHERE " + whc)

rows = dbcurs.fetchall()

poms = []
skys = []

if usedist:
    dists = []
    for moonphase, moondist, skylevel, skystd in rows:
        if moondist > 90.0:
            moondist = 90.0
        poms.append(moonphase)
        skys.append(skylevel)
        dists.append(moondist)
    poms = np.array(poms) * 100.0 * np.cos(np.array(dists) * np.pi / 180.0)
else:
    for moonphase, moondist, skylevel, skystd in rows:
        poms.append(moonphase)
        skys.append(skylevel)
    poms = np.array(poms) * 100.0

if len(poms) < 10:
    print("Not enought points read", file=sys.stderr)
    sys.exit(2)

rg.plt_figure()
plt.scatter(poms, skys, color=colour, marker=marker)
plt.title(title)
plt.xlabel(xlab)
plt.ylabel(ylab)
if ofig is None:
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    plt.gcf().savefig(ofig)
