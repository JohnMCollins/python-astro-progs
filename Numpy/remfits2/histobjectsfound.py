#!  /usr/bin/env python3

"""Histogram of objects found"""

import argparse
import sys
import matplotlib.pyplot as plt
import numpy as np
import remdefaults
import remgeom

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Make histogram of objects found', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--xlabel', type=str, help='X axis label')
parsearg.add_argument('--ylabel', type=str, help='Y axis label')
parsearg.add_argument('--colour', type=str, default='b', help='Colour of lines')
parsearg.add_argument('--filter', type=str, required=True, help='Filter analysed for')
parsearg.add_argument('--bins', type=int, nargs='+', required=True, help='bins for histogram')
parsearg.add_argument('--target', type=str, required=True, help='target object for observations considered')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
ylab = resargs['ylabel']
xlab = resargs['xlabel']
colour = resargs['colour']
filt = resargs['filter']
target = resargs['target']
bins = sorted(resargs['bins'])

ofig = rg.disp_getargs(resargs)

dbase, dbcurs = remdefaults.opendb()

dbcurs.execute("SELECT COUNT(*) FROM obsinf INNER JOIN findresult ON obsinf.obsind=findresult.obsind WHERE obsinf.filter=%s AND object=%s AND rejreason IS NULL GROUP BY findresult.obsind", (filt, target))
histv = np.array(dbcurs.fetchall()).flatten()
dbcurs.execute("SELECT COUNT(*) FROM obsinf WHERE rejreason=%s AND object=%s AND filter=%s", ("Not enough objects", target, filt))
n = dbcurs.fetchone()
if n is not None and n[0] != 0:
    histv = np.concatenate((histv, n))

if histv.max() > max(bins):
    bins.append(histv.max())

fig = rg.plt_figure()
plt.hist(histv, bins, color=colour)
if xlab is not None:
    plt.xlabel(xlab)
if ylab is not None:
    plt.ylabel(ylab)
remgeom.end_figure(fig, ofig)
remgeom.end_plot(ofig)
