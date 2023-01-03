#!  /usr/bin/env python3

"""Make light curve from given obsids for specified objects"""

import argparse
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import numpy as np
from scipy.stats import linregress
import col_from_file
import remdefaults
import remgeom

class Objresult:

    """Recuord results for object"""

    def __init__(self, oi, ln, var, dat, aduc, ebri):
        self.objind = oi
        self.label = ln
        self.variability = var
        self.datelist = [dat]
        self.adulist = [aduc]
        self.meanval = aduc
        self.expbri = ebri

    def append(self, dat, aduc):
        """Append a result to results for a given object"""
        self.datelist.append(dat)
        self.adulist.append(aduc)

    def numobs(self):
        """Return number of observations recorded"""
        return len(self.datelist)

    def get_mean(self):
        """Set mean value to mean of adus"""
        self.meanval = np.mean(self.adulist)

    def prepare(self):
        """Sort arrays and return (dates, values)"""
        self.datelist = np.array(self.datelist)
        self.adulist = np.array(self.adulist)
        ast = np.argsort(self.datelist)
        return (self.datelist[ast], self.adulist[ast])

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Get comparative light curves for objects', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsinds', nargs='*', type=int, help='Obs ids or take from stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--colours', type=str, default='b,r,g,magenta,cyan,yellow,k', help='Comma-separated list of colours for lines')
parsearg.add_argument('--linestyles', type=str, default='solid,dotted,dashed,dashdot', help='Comma-separate list of line styles')
parsearg.add_argument('--markers', type=str, default='.ov^<>12348spP*+xXdD', help='List of possible markers')
parsearg.add_argument('--xlabel', type=str, help='X axis label')
parsearg.add_argument('--ylabel', type=str, help='Y axis label')
parsearg.add_argument('--daterot', type=float, default=45, help='Rotation of dates')
parsearg.add_argument('--verbose', action='store_true', help='Give blow-by-blow account')
parsearg.add_argument('--bytime', action='store_true', help='Display by time')
parsearg.add_argument('--ylower', type=float, help='Lower limit of Y axis')
parsearg.add_argument('--yupper', type=float, help='Upper limit of Y axis')
parsearg.add_argument('--yscale', type=float, help='Scale for Y axis')
parsearg.add_argument('--variability', type=float, default=0.0, help='Maximum variability acceptable')
parsearg.add_argument('--maxsky', type=float, default=1000.0, help='Maximum sky level')
parsearg.add_argument('--nresults', type=int, default=10, help='Number of results')
parsearg.add_argument('--objects', type=str, nargs='*', help='Specific objects to track by label')
parsearg.add_argument('--normalise', action='store_true', help='Normalise flux around 1')
parsearg.add_argument('--regress', action='store_true', help='Perform regression analysis')
parsearg.add_argument('--objregress', action='store_true', help='Regression by specified objects only')
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
verbose = resargs['verbose']
ylab = resargs['ylabel']
xlab = resargs['xlabel']
daterot = resargs['daterot']
bytime = resargs['bytime']
ylower = resargs['ylower']
yupper = resargs['yupper']
yscale = resargs['yscale']
colours = resargs['colours'].split(',')
markers = resargs['markers']
linestyles = resargs['linestyles'].split(',')
nresults = resargs['nresults']
objects = resargs['objects']
normalise = resargs['normalise']
regress = resargs['regress']
objregress = resargs['objregress']
maxvar = resargs['variability']
maxsky = resargs['maxsky']

if xlab is None:
    if bytime:
        xlab = "Time observation taken"
    else:
        xlab = "Time & date of observation"

ofig = rg.disp_getargs(resargs)
mydb, mycurs = remdefaults.opendb()

# Record results by label

resulttab = dict()
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

        if  label in resulttab:
            resulttab[label].append(dateobs, aducount)
        else:
            resulttab[label] = Objresult(objind, label, variability, dateobs, aducount, bri)

        if variability > maxvar:
            continue

        if dateobs in result_by_date:
            drdict = result_by_date[dateobs]
        else:
            result_by_date[dateobs] = drdict = dict()

        drdict[label] = (aducount, bri)

if objects is not None:
    objects = set(objects)
    newrestab = dict()
    for lab, rt in resulttab.items():
        if lab in objects:
            newrestab[lab] = rt
    resulttab = newrestab
    if objregress:
        for d, dtab in result_by_date.items():
            newrestab = dict()
            for k in objects:
                if k in dtab:
                    newrestab[k] = dtab[k]
            result_by_date[d] = newrestab

for v in resulttab.values():
    v.get_mean()

lablist = sorted(resulttab, key=lambda x: -resulttab[x].meanval)
fig = rg.plt_figure()
ax = plt.subplot(111)
if ylower is not None:
    ax.set_ylim(ylower / yscale, yupper / yscale)
y_formatter = mtick.ScalarFormatter(useOffset=False)
if bytime:
    df = mdates.DateFormatter("%H:%M")
else:
    df = mdates.DateFormatter("%d/%m/%y %H:%M")
ax.xaxis.set_major_formatter(df)
if daterot != 0.0:
    plt.xticks(rotation=daterot)
plt.xlabel(xlab)
plt.ylabel(ylab)

ncolours = len(colours)
nmarkers = len(markers)
nstyles = len(linestyles)

ccol = cmark = cstyle = resnum = 0
leglist = []

for lab in lablist:

    if resulttab[lab].numobs() < 2:
        continue

    dates, adus = resulttab[lab].prepare()

    if regress:
        revadus = []
        revdates = []
        for d, a in zip(dates, adus):
            dresults = result_by_date[d]
            expadus = []
            actadus = []
            for l in dresults:
                if l == lab:
                    continue
                act, ex = dresults[l]
                expadus.append(ex)
                actadus.append(act)
            if len(actadus) < 2:
                continue
            lreg = linregress(expadus, actadus)
            if verbose:
                print("After lreg points={:d} slope={:.5g} intercept={:.5g}"
                      " std={:.5g} istd={:.5g} r={:.5g} p={:.5g}".
                      format(len(actadus), lreg.slope, lreg.intercept, lreg.stderr, lreg.intercept_stderr, lreg.rvalue, lreg.pvalue), file=sys.stderr)
            if lreg.slope <= 0:
                continue
            revdates.append(d)
            revadus.append((a - lreg.intercept) / lreg.slope)
            if verbose:
                print(lab, d, a, "replaced by", revadus[-1], file=sys.stderr)
        if len(revadus) < 2:
            continue
        revadus = np.array(revadus)
        revdates = np.array(revdates)
        asort = revdates.argsort()
        adus = revadus[asort]
        dates = revdates[asort]

    if normalise:
        adus /= adus.mean()

    plt.plot(dates, adus, color=colours[ccol], marker=markers[cmark], linestyle=linestyles[cstyle])
    ccol += 1
    if ccol >= ncolours:
        ccol = 0
        cmark += 1
        if cmark >= nmarkers:
            cmark = 0
            cstyle = (cstyle + 1) % nstyles
    leglist.append(lab)
    resnum += 1
    if resnum >= nresults:
        break

plt.legend(leglist)
plt.tight_layout()
remgeom.end_figure(fig, ofig)
remgeom.end_plot(ofig)
