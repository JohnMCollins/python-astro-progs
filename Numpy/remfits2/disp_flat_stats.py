#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T18:57:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: lcurve3.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:14+00:00

import matplotlib.pyplot as plt
import numpy as np
import argparse
import sys
import remgeom
import dbops
import remdefaults
import os
import miscutils
import parsetime
import remfield

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Plot stat measures for daily flats', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
remfield.parseargs(parsearg)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--colour', type=str, default='b', help='Plot points colour')
parsearg.add_argument('--bins', type=int, default=30, help='Bins in histogram')
parsearg.add_argument('--logmean', action='store_true', help='Plot mean hist on log scale')
parsearg.add_argument('--logstd', action='store_true', help='Plot std hist on log scale')
parsearg.add_argument('--logskew', action='store_true', help='Plot skew hist on log scale')
parsearg.add_argument('--logkurt', action='store_true', help='Plot kurt hist on log scale')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
colour = resargs['colour']
bins = resargs['bins']
ofig = rg.disp_getargs(resargs)

logsc = [resargs['logmean'], resargs['logstd'], resargs['logskew'], resargs['logkurt']]

fieldselect = ["typ='flat'", "ind!=0", "gain=1", "rejreason IS NULL"]
try:
    dstring = parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)
remfield.getargs(resargs, fieldselect)

dbase, dbcurs = remdefaults.opendb()

dbcurs.execute("SELECT mean,std,skew,kurt FROM iforbinf WHERE " + " AND ".join(fieldselect))

dbrows = dbcurs.fetchall()
if len(dbrows) < bins * 2:
    print("Not enough data points found to plot", file=sys.stderr)
    sys.exit(2)

dbrows = np.array(dbrows)

means = dbrows[:, 0]
stds = dbrows[:, 1]

fig = rg.plt_figure()
fig.canvas.set_window_title("Stats of daily flats")

for colnum, (subp, title) in enumerate(((221, 'Means'), (222, 'Std'), (223, 'Skew'), (224, 'Kurtosis'))):
    plt.subplot(subp)
    plt.hist(dbrows[:, colnum], color=colour, bins=bins, log=logsc[colnum])
    plt.legend((title,))

plt.tight_layout()
if ofig is None:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
else:
    ofig = miscutils.replacesuffix(ofig, ".png")
    fig.savefig(ofig)
    plt.close(fig)
