#!  /usr/bin/env python3

"""Show linear regression graph for image fits"""

import argparse
import sys
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
import col_from_file
import remdefaults
import remgeom

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Show linear regression graph for image fits', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsinds', nargs='*', type=int, help='Obs ids or take from stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--colour', type=str, default='b', help='Colour of object points for scatter')
parsearg.add_argument('--varobjcolour', type=str, default='r', help='Colour of object points not included in lreg')
parsearg.add_argument('--marker', type=str, default='o', help='Marker for scatter')
parsearg.add_argument('--linecolour', type=str, default='k', help='Line colour')
parsearg.add_argument('--linestyle', type=str, default='solid', help='Line style for line')
parsearg.add_argument('--xlabel', type=str, default='Expected flux', help='X axis label')
parsearg.add_argument('--ylabel', type=str, default='Actual flux', help='Y axis label')
parsearg.add_argument('--verbose', action='store_true', help='Give blow-by-blow account')
parsearg.add_argument('--variability', type=float, default=0.0, help='Maximum variability acceptable')
parsearg.add_argument('--maxsky', type=float, default=1000.0, help='Maximum sky level')
parsearg.add_argument('--objects', type=str, nargs='*', help='Specific objects to track by label')
parsearg.add_argument('--objregress', action='store_true', help='Regression by specified objects only')
parsearg.add_argument('--multi', action='store_true', help='Treat one file as multiple')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
obsinds = resargs['obsinds']
if len(obsinds) == 0:
    try:
        obsinds = [ int(x) for x in col_from_file.col_from_file(sys.stdin, resargs['colnum'])]
    except ValueError:
        print("Invalid obsinds on stdin, should all be integer", file=sys.stderr)
        sys.exit(10)

remdefaults.getargs(resargs)
ylab = resargs['ylabel']
xlab = resargs['xlabel']
verbose = resargs['verbose']
colour = resargs['colour']
varobjcolour = resargs['varobjcolour']
marker = resargs['marker']
linecolour = resargs['linecolour']
linestyle = resargs['linestyle']
objects = resargs['objects']
objregress = False
if objects is not None:
    objects = set(objects)
    objregress = resargs['objregress']
maxvar = resargs['variability']
maxsky = resargs['maxsky']
multi = resargs['multi'] or len(obsinds) > 1

ofig = rg.disp_getargs(resargs)
mydb, mycurs = remdefaults.opendb()

# Record results by label

result_by_date = dict()

for obsind in obsinds:

    mycurs.execute("SELECT date_obs,label,variability,findresult.objind,aducount,"
                   "IF(filter='g',gbri,IF(filter='r',rbri,IF(filter='i',ibri,IF(filter='z',zbri,1e6)))) AS bri"
                   " FROM obsinf INNER JOIN findresult ON obsinf.obsind=findresult.obsind "
                   "INNER JOIN aducalc ON findresult.ind=aducalc.frind "
                   "INNER JOIN objdata ON aducalc.objind=objdata.ind "
                   "WHERE obsinf.obsind={:d} AND label IS NOT NULL AND aducalc.skylevel<={:.8e}".format(obsind, maxsky))

    adusres = mycurs.fetchall()

    for dateobs, label, variability, objind, aducount, bri in adusres:

        if dateobs in result_by_date:
            drdict = result_by_date[dateobs]
        else:
            result_by_date[dateobs] = drdict = dict()

        drdict[label] = (aducount, bri, variability)

plotnum = 0

for d in sorted(result_by_date.keys()):

    lrlist = []
    vrlist = []

    if len(result_by_date[d]) < 2:
        continue

    for lab, stats in result_by_date[d].items():

        adus, expadus, var = stats

        if  var > maxvar or (objregress  and  lab not in objects):
            vrlist.append((expadus, adus))
        else:
            lrlist.append((expadus, adus))

    fig = rg.plt_figure()
    ax = plt.subplot(111)
    plt.xlabel(xlab)
    plt.ylabel(ylab)

    if len(vrlist) > 0:
        vrlist = np.array(vrlist)
        plt.scatter(vrlist[0], vrlist[1], color=varobjcolour, marker=marker)

    if len(lrlist) > 0:
        lrlist = np.array(lrlist)
        expvals = lrlist[0]
        actvals = lrlist[1]
        plt.scatter(expvals, actvals, color=colour, marker=marker)

        if len(lrlist) > 1:
            lreg = linregress(expvals, actvals)
            minx, maxx = ax.get_xlim()
            miny = lreg.slope * minx + lreg.intercept
            maxy = lreg.slope * maxx + lreg.intercept
            plt.plot((minx, maxx), (miny, maxy), color=linecolour, linestyle=linestyle)

    plt.tight_layout()
    plotnum += 1
    remgeom.end_figure(fig, ofig, plotnum, multi)

remgeom.end_plot(ofig)
