#!  /usr/bin/env python3

"""Track calibrated light curve versus statistics of obs"""

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

class ObjResult:

    """Record results for object"""

    def __init__(self, olabel, oi, var, expbri, actbri, brierr):
        self.objind = oi
        self.label = olabel
        self.variability = var
        self.expbri = expbri
        self.actbri = actbri
        self.brierr = brierr

class DateResult:

    """Recuord results for date obs"""

    def __init__(self, rdate, rmin, rmax, rmean, rstd):
        self.obsdate = rdate
        self.minpix = rmin
        self.maxpix = rmax
        self.meanpix = rmean
        self.stdpix = rstd
        self.objlist = dict()

    def append(self, olabel, oi, var, expbri, actbri, brierr):
        """Append object result to list for given date"""

        self.objlist[olabel] = ObjResult(olabel, oi, var, expbri, actbri, brierr)

    def numobjs(self, maxvarability, notlab = None):
        """Return number of observations recorded with acceptable variability"""
        return len([k for k, v in self.objlist.items() if k != notlab and v.variability <= maxvarability])

    def gettargbri(self, targlab):
        """Get actual brightness of target"""
        try:
            return  self.objlist[targlab].actbri
        except  KeyError:
            return  None

    def getlrlist(self, maxvariability, notlab = None):
        """Get lists suitable for doing lreg op on"""
        explist = []
        actlist = []
        for lab, objr in self.objlist.items():
            if lab != notlab and objr.variability <= maxvariability:
                explist.append(objr.expbri)
                actlist.append(objr.actbri)
        return  (np.array(explist), np.array(actlist))

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Get light curve for object versus statistics', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsinds', nargs='*', type=int, help='Obs ids or take from stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--target', type=str, required=True, help='Target object to track')
parsearg.add_argument('--colours', type=str, default='b,r,g,magenta,cyan,yellow,k', help='Comma-separated list of colours for lines')
parsearg.add_argument('--linestyle', type=str, default='solid', help='Line style for plot')
parsearg.add_argument('--marker', type=str, default='o', help='Marker')
parsearg.add_argument('--xlabel', type=str, help='X axis label')
parsearg.add_argument('--ylabel', type=str, help='Y axis label')
parsearg.add_argument('--daterot', type=float, default=45, help='Rotation of dates')
parsearg.add_argument('--verbose', action='store_true', help='Give blow-by-blow account')
parsearg.add_argument('--bytime', action='store_true', help='Display by time')
parsearg.add_argument('--variability', type=float, default=0.0, help='Maximum variability acceptable')
parsearg.add_argument('--maxsky', type=float, default=1000.0, help='Maximum sky level')
parsearg.add_argument('--normalise', action='store_true', help='Normalise flux around 1')
parsearg.add_argument('--recip', action='store_true', help='Take reciprocal of minimum and means when normalising')
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
colours = resargs['colours'].split(',')
marker = resargs['marker']
linestyle = resargs['linestyle']
normalise = resargs['normalise']
recip = resargs['recip']
maxvar = resargs['variability']
maxsky = resargs['maxsky']
target = resargs['target']

if xlab is None:
    if bytime:
        xlab = "Time observation taken"
    else:
        xlab = "Time & date of observation"

ofig = rg.disp_getargs(resargs)
mydb, mycurs = remdefaults.opendb()

# Record results by label

result_by_date = dict()

for obsind in obsinds:

    mycurs.execute("SELECT date_obs,minv,maxv,mean,std,label,variability,findresult.objind,aducount,aduerr,"
                   "IF(filter='g',gbri,IF(filter='r',rbri,IF(filter='i',ibri,IF(filter='z',zbri,1e6)))) AS bri"
                   " FROM obsinf INNER JOIN findresult ON obsinf.obsind=findresult.obsind "
                   "INNER JOIN aducalc ON findresult.ind=aducalc.frind "
                   "INNER JOIN objdata ON aducalc.objind=objdata.ind "
                   "WHERE obsinf.obsind={:d} AND label IS NOT NULL AND aducalc.skylevel<={:.8e}".format(obsind, maxsky))

    for dateobs, minvalobs, maxvalobs, meanvalobs, stdobs, label, variability, objind, aducount, aduerr, bri in mycurs.fetchall():

        try:
            drdict = result_by_date[dateobs]
        except KeyError:
            drdict = result_by_date[dateobs] = DateResult(dateobs, minvalobs, maxvalobs, meanvalobs, stdobs)

        drdict.append(label, objind, variability, bri, aducount, aduerr)

fig = rg.plt_figure()
ax = plt.subplot(111)
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
ccol = 0
leglist = []

mins = []
maxes = []
means = []
stds = []
bris = []
dates = []

for dat in sorted(result_by_date.keys()):
    drdict = result_by_date[dat]
    targbri = drdict.gettargbri(target)
    if  targbri is None or drdict.numobjs(maxvar, target) < 2:
        continue
    lrexp, lract = drdict.getlrlist(maxvar, target)
    lreg = linregress(lrexp, lract)
    if lreg.slope <= 0:
        continue
    targexp = (targbri - lreg.intercept) / lreg.slope
    dates.append(dat)
    mins.append(drdict.minpix)
    maxes.append(drdict.maxpix)
    means.append(drdict.meanpix)
    stds.append(drdict.stdpix)
    bris.append(targexp)

legs = ['Calibrated flux', 'Minimum value', 'Maximum value', "Means", "Std dev"]
if normalise:
    mins = np.array(mins) / np.mean(mins)
    maxes = np.array(maxes) / np.mean(maxes)
    means = np.array(means) / np.mean(means)
    stds = np.array(stds) / np.mean(stds)
    bris = np.array(bris) / np.mean(bris)
    if recip:
        mins = 1/mins
        means = 1/means

colours = colours * 5
plt.plot(dates, bris, color=colours[0], marker=marker, linestyle=linestyle)
plt.plot(dates, mins, color=colours[1], marker=marker, linestyle=linestyle)
plt.plot(dates, maxes, color=colours[2], marker=marker, linestyle=linestyle)
plt.plot(dates, means, color=colours[3], marker=marker, linestyle=linestyle)
plt.plot(dates, stds, color=colours[4], marker=marker, linestyle=linestyle)
if recip:
    legs[1] = "Recip min value"
    legs[3] = "Recip means"
plt.legend(legs)
plt.tight_layout()
remgeom.end_figure(fig, ofig)
remgeom.end_plot(ofig)
