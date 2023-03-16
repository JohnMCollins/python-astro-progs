#!  /usr/bin/env python3

"""Scatter plot of objects found"""

import argparse
import sys
import matplotlib.pyplot as plt
import numpy as np
import remdefaults
import remgeom

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Show scatter of number of objects found versus airmass', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--xlabel', type=str, help='X axis label')
parsearg.add_argument('--ylabel', type=str, help='Y axis label')
parsearg.add_argument('--colour', type=str, default='b', help='Colour of points')
parsearg.add_argument('--rejcolour', type=str, default='r', help='Colour for rejected points')
parsearg.add_argument('--marker', type=str, default='*', help='Marker shape')
parsearg.add_argument('--filter', type=str, required=True, help='Filter analysed for')
parsearg.add_argument('--field', type=str, choices=('airmass', 'moonphase', 'moondist'), required=True, help='Database field to select')
parsearg.add_argument('--target', type=str, required=True, help='target object for observations considered')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
ylab = resargs['ylabel']
xlab = resargs['xlabel']
colour = resargs['colour']
rejcolour = resargs['rejcolour']
marker = resargs['marker']
filt = resargs['filter']
target = resargs['target']
field = resargs['field']

ofig = rg.disp_getargs(resargs)

dbase, dbcurs = remdefaults.opendb()

dbcurs.execute("SELECT " + field + ",COUNT(*) FROM obsinf INNER JOIN findresult ON obsinf.obsind=findresult.obsind WHERE obsinf.filter=%s AND object=%s AND rejreason IS NULL GROUP BY findresult.obsind", (filt, target))
scattv = np.array(dbcurs.fetchall())
fv = scattv[:,0]
occs = scattv[:,1]
dbcurs.execute("SELECT " + field + ",COUNT(*) FROM obsinf WHERE rejreason=%s AND object=%s AND filter=%s GROUP BY " + field, ("Not enough objects", target, filt))
rejectv = np.array(dbcurs.fetchall())
rfv = rejectv[:,0]
roccs = rejectv[:,1]

fig = rg.plt_figure()
plt.scatter(fv, occs, color=colour, marker=marker)
plt.scatter(rfv, roccs, color=rejcolour, marker=marker)

if xlab is not None:
    plt.xlabel(xlab)
if ylab is not None:
    plt.ylabel(ylab)
remgeom.end_figure(fig, ofig)
remgeom.end_plot(ofig)
