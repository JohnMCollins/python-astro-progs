#!  /usr/bin/env python3

"""List aperture optimisation results for given objects"""

import argparse
import sys
import os
import glob
from dateutil.relativedelta import *
from astropy.time import Time
import numpy as np
import matplotlib.pyplot as plt
import col_from_file
import remdefaults
import remgeom
import objdata
import logs

def plot_segments(arry, daybreak, colour):
    """Plot segments from list of tuples (date, value), breaking at points > daybreak. Use given colour"""

    arry = np.array(arry).transpose()
    arry = arry[:,arry[0].argsort()]
    days, vals = arry
    days -= firstday
    breaks = np.where(days[1:] - days[:-1] > daybreak)[0] + 1
    sp = nd = 0
    for b in breaks:
        nd = b
        plt.plot(days[sp:nd], vals[sp:nd], color=colour)
        sp = nd
    if nd < vals.size:
        plt.plot(days[nd:], vals[nd:], color=colour)

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Generate optimised aperture list with various restrictions', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsids', type=int, nargs='*', help='List of obs ids or use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--object', type=str, required=True, help='Object by ID name or label to consider')
parsearg.add_argument('--vicinity', type=str, help='Vicinity when identifying by label')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--indir', type=str, help='List directory if not CWD')
parsearg.add_argument('--ignull', action='store_true', help='Ignore non-files')
parsearg.add_argument('--break', type=float, default=1.0, help='Days to break plot at')
parsearg.add_argument('--xlabel', type=str, help='X axis label')
parsearg.add_argument('--ylabel', type=str, help='Y axis label')
parsearg.add_argument('--ycolour', type=str, default='k', help='Colour for year marks')
parsearg.add_argument('--ymstyle', type=str, default='dotted', help='Line style for year markers')
parsearg.add_argument('--yalpha', type=float, default=.5, help='Alpha for years')
parsearg.add_argument('--scatter', action='store_true', help='Scatter plot')
parsearg.add_argument('--marker', type=str, default='*', help='Marker for scatter plot')
logs.parseargs(parsearg)
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())

obsids = resargs["obsids"]
if len(obsids) == 0:
    obsids = map(int, col_from_file.col_from_file(sys.stdin, resargs['colnum']))

obj = resargs['object']
remdefaults.getargs(resargs)
logging = logs.getargs(resargs)
indir = resargs['indir']
ignull = resargs['ignull']
breakat = resargs['break']
vicinity = resargs['vicinity']
ylab = resargs['ylabel']
xlab = resargs['xlabel']
ycolour = resargs['ycolour']
ymstyle = resargs['ymstyle']
yalpha = resargs['yalpha']
scatter = resargs['scatter']
marker = resargs['marker']
ofig = rg.disp_getargs(resargs)

if indir is not None:
    prevdir = os.getcwd()
    try:
        os.chdir(indir)
    except  OSError as e:
        logging.die(10, "Could not select directory", indir, e.args[1])

mydb, dbcurs = remdefaults.opendb()

if vicinity is not None:
    try:
        vicinity = objdata.get_objname(dbcurs, vicinity)
    except objdata.ObjDataError:
        logging.die(13, "Do not understand vicinity", vicinity)

if obj.isdigit():
    objind = int(obj)
    objd = objdata.ObjData(objind=objind)
    try:
        objd.get(dbcurs)
    except objdata.ObjDataError as e:
        logging.die(14, "Could not find object id", objind, "error", e.args[0])
else:
    if len(obj) <= 4:
        if vicinity is None:
            logging.die(15, "No vicinity specified for label")
        objd = objdata.ObjData(vicinity=vicinity, label=obj)
    else:
        try:
            name = objdata.get_objname(dbcurs, obj)
        except objdata.ObjDataError:
            logging.die(16, "Unknown name", obj)
        objd = objdata.ObjData(name=name)
        try:
            objd.get(dbcurs)
        except objdata.ObjDataError as e:
            logging.die(17, "Could not find object", obj, e.args[0])
        objind = objd.objind

favail = glob.glob('*-{:d}.apopt'.format(objind))
if len(favail) == 0:
    logging.die(18, "No files available for object")

obsinds_avail = set(map(int, [f.split('-')[0] for f in favail]))
obsids_req = set(obsids)
if len(obsids_req) == 0:
    logging.die(19, "No obs requested")

looking_at = obsinds_avail & obsids_req
if len(looking_at) == 0:
    logging.die(20, "No files available for observations")

byfilt = dict()
errors = 0
totals = []
for obsind in looking_at:
    dbcurs.execute("SELECT filter,bjdobs FROM obsinf WHERE obsind={:d}".format(obsind))
    orow = dbcurs.fetchone()
    if orow is None:
        logging.write("Could not find record for obsind", obsind)
        errors += 1
        continue
    filt, dat = orow
    if filt in byfilt:
        fdict = byfilt[filt]
    else:
        byfilt[filt] = fdict = []

    arr = np.loadtxt("{:d}-{:d}.apopt".format(obsind, objind), unpack=True)
    apsizes, adus, amps, sigmas, ampstds, sigstds = arr
    adus /= adus.mean()
    ampstds /= ampstds.mean()
    sigstds /= sigstds.mean()
    combs = np.abs(adus-ampstds) + np.abs(adus-sigstds) + np.abs(ampstds-sigstds)
    ast = combs.argsort(kind='stable')
    ent = (dat, apsizes[ast[0]])
    fdict.append(ent)
    totals.append(ent)

fig = rg.plt_figure()
#fig.canvas.manager.set_window_title(miscutils.removesuffix(moanname))
ax = plt.subplot(111)

arr = np.array(totals)
firstday = arr[:,0].min()
lastday = arr[:,0].max()

filtcols = dict(g='g',r='r',i='b',z='b')
if scatter:
    arry = np.array(totals).transpose()
    plt.scatter(arry[0]-firstday, arry[1], color='purple', marker=marker)
    for filt, totf in byfilt.items():
        arry = np.array(totf).transpose()
        plt.scatter(arry[0]-firstday, arry[1], color=filtcols[filt], marker=marker)
else:
    plot_segments(totals, breakat, 'purple')
    for filt, totf in byfilt.items():
        plot_segments(totf, breakat, filtcols[filt])

years = []
if xlab is None:
    if firstday < 2450000:
        firstday += 2450000
        lastday += 2450000
    firstday = Time(firstday, format='jd')
    firstday = firstday.datetime
    endt = Time(lastday, format='jd').datetime
    yr = firstday + relativedelta(year=firstday.year+1, day=1, month=1)
    while yr < endt:
        years.append((yr - firstday).days)
        yr = yr + relativedelta(year=yr.year+1, day=1, month=1)
    plt.xlabel("Days from {:%d %b %Y}".format(firstday))
    for y in years:
        plt.axvline(y, color=ycolour, linestyle=ymstyle, alpha=yalpha)
else:
    plt.xlabel(xlab)
if ylab:
    plt.ylabel(ylab)

remgeom.end_figure(fig, ofig)
remgeom.end_plot(ofig)
