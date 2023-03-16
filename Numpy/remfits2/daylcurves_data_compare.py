#!  /usr/bin/env python3

"""Make light curves comparing several objects"""

import argparse
import sys
import os.path
from dateutil.relativedelta import *
from astropy.time import Time
import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import matplotlib.ticker as mtick
import numpy as np
import remdefaults
import remgeom
import miscutils
import logs

def make_array(args, sep=','):
    """Make array from args which might be as array or separated by given character"""
    if args is None:
        return  None
    result = []
    for arg in args:
        result += arg.split(sep)
    return  result

#Lstyles = ('solid', 'dotted', 'dashed', 'dashdot')

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Get light curve from data from various sources', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Data files - use /dev/fd/0 etc for various sources or - for stdin')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--xlabel', type=str, help='X axis label')
parsearg.add_argument('--ylabel', type=str, help='Y axis label')
#parsearg.add_argument('--daterot', type=float, default=45, help='Rotation of dates')
#parsearg.add_argument('--bytime', action='store_true', help='Display by time')
parsearg.add_argument('--marker', type=str, default='*', help='Marker for points')
parsearg.add_argument('--colour', type=str, default=['b,g,r,k'], nargs='+', help='Comma-separated colours of lines')
parsearg.add_argument('--names', type=str, nargs='+', help='Labels for lines use quotes if needed and - to copy file name')
parsearg.add_argument('--refdate', type=float, default=0.0, help='Add to dates')
parsearg.add_argument('--dispdate', action='store_true', help='Display dates rather than as days')
parsearg.add_argument('--ycolour', type=str, default='k', help='Colour for year marks')
parsearg.add_argument('--ymstyle', type=str, default='dotted', help='Line style for year markers')
parsearg.add_argument('--yalpha', type=float, default=.5, help='Alpha for years')
rg.disp_argparse(parsearg)
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
infiles = resargs['files']
remdefaults.getargs(resargs)
ylab = resargs['ylabel']
xlab = resargs['xlabel']
#daterot = resargs['daterot']
#bytime = resargs['bytime']
marker = resargs['marker']
lcolour = make_array(resargs['colour']) * len(infiles)
names = make_array(resargs['names'])
refdate = resargs['refdate']
dispdate = resargs['dispdate']
ycolour = resargs['ycolour']
ymstyle = resargs['ymstyle']
yalpha = resargs['yalpha']

ofig = rg.disp_getargs(resargs)
logging = logs.getargs(resargs)

legends = []
actual_files = []
for infile in infiles:
    if infile == '-':
        actual_files.append("/dev/fd/0")
        legends.append("(stdin)")
    else:
        actual_files.append(infile)
        legends.append(miscutils.removesuffix(os.path.basename(infile), allsuff=True))
if names is not None:
    for n, nam in enumerate(names):
        iname = nam
        if nam == 'F':
            continue
        try:
            legends[n] = nam
        except IndexError:
            break

arraylist = []
for infile in actual_files:
    try:
        dat = np.loadtxt(infile, unpack=True)
    except OSError as e:
        logging.die(10, "Cannot open input file". e.args[0])
    arraylist.append(dat[0:2])

fig = rg.plt_figure()
ax = plt.subplot(111)

mindate = 1e10
maxdate = -1e10

for dates, values in arraylist:

    dates += refdate
    if dates.min() < 2450000:
        dates += 2450000
    mindate = min(mindate, dates.min())
    maxdate = max(maxdate, dates.max())

for n, dat in enumerate(arraylist):

    dates, values = dat
    dates += refdate
    if dates.min() < 2450000:
        dates += 2450000
    ddates = dates
    values -= values.min()
    values /= values.mean()
    if dispdate:
        ddates = list(map(lambda x:Time(x, format='jd').datetime, dates))
    else:
        ddates -= mindate
    plt.scatter(ddates, values, marker=marker, color=lcolour[n])

plt.legend(legends)

years = []
ydays = []

startdate = Time(mindate, format='jd').datetime
enddate = Time(maxdate, format='jd').datetime
yr = startdate + relativedelta(year=startdate.year+1, day=1, month=1)
while yr < enddate:
    ydays.append((yr - startdate).days)
    years.append(yr)
    yr = yr + relativedelta(year=yr.year+1, day=1, month=1)

if xlab is None:
    if dispdate:
        plt.xlabel("Date starting {:%d %b %Y}".format(startdate))
    else:
        plt.xlabel("Days from {:%d %b %Y}".format(startdate))
else:
    plt.xlabel(xlab)
if dispdate:
    for y in years:
        plt.axvline(y, color=ycolour, linestyle=ymstyle, alpha=yalpha)
else:
    for y in ydays:
        plt.axvline(y, color=ycolour, linestyle=ymstyle, alpha=yalpha)
if ylab is not None:
    plt.ylabel(ylab)

plt.tight_layout()
remgeom.end_figure(fig, ofig)
remgeom.end_plot(ofig)
