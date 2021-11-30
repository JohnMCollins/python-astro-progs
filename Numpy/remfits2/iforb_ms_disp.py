#!  /usr/bin/env python3

# Duplicate creation of master bias file

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import os.path
import remdefaults
import remfits
import col_from_file
import miscutils
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import remgeom

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Display mean/std dev of daily flat or bias files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Filenames or iforbinds to process, otherwise use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--bias', action='store_false', help='Plot bias rather than flat files')
parsearg.add_argument('--rotation', type=float, default=40.0, help='Rotation for date labels')
parsearg.add_argument('--stderrmult', type=float, default=1.5, help='Multiple of std devs to allow for neat plot of errorbars')
parsearg.add_argument('--ndates', default=5, type=int, help='Number of dates and times to display')
parsearg.add_argument('--marker', type=str, default='.', help='Point marker type for error bars')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['files']
biasfiles = resargs['bias']
stderrmult = resargs['stderrmult']
rot = resargs['rotation']
ndates = resargs['ndates']
marker = resargs['marker']

type = 'F'
if biasfiles:
    type = 'B'

figout = rg.disp_getargs(resargs)

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

mydb, mycurs = remdefaults.opendb()
errors = 0

# Pairs of arrays to hold dates, meams and standard deviations

filterres = dict(g=[], r=[], i=[], z=[])

mindate = datetime.datetime.now()
maxdate = datetime.datetime(year=1970, month=1, day=1, hour=0, minute=0)

maxv = -1
minv = 1e6
maxstd = -1

for f in files:
    try:
        ff = remfits.parse_filearg(f, mycurs, type=type)
    except remfits.RemFitsErr as e:
        print("file", f, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    filterres[ff.filter].append((ff.date, ff.meanval, ff.stdval))
    if ff.date < mindate:
        mindate = ff.date
    if ff.date > maxdate:
        maxdate = ff.date
    if ff.meanval > maxv:
        maxv = ff.meanval
    if ff.meanval < minv:
        minv = ff.meanval
    if ff.stdval > maxstd:
        maxstd = ff.stdval

if errors > 0:
    print("Stopping due to", errors, "errors", file=sys.stderr)
    sys.exit(80)

plotfigure = rg.plt_figure()
plotfigure.canvas.manager.set_window_title("Mean std/dev 4 filters")

# Work out what sort of dates we are doing

fd = mindate.toordinal()
td = maxdate.toordinal()

ndays = td - fd

if ndays < ndates:
    print("Not enough different dates only", ndays, "must be at least", ndates, file=sys.stderr)
    sys.exit(81)

if ndays < ndates * 30:
    locat = mdates.DayLocator(interval=int(round(ndays / ndates)))
    df = mdates.DateFormatter("%Y-%m-%d")
else:
    locat = mdates.MonthLocator(interval=int(round(ndays / (ndates * 30))))
    df = mdates.DateFormatter("%m/%Y")

for filter, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    p = filterres[filter]
    datelist = [x[0] for x in p]
    means = [x[1] for x in p]
    stddevs = [x[2] for x in p]
    ax = plt.subplot(subp)
    plt.ylim(minv - stderrmult * maxstd, maxv + stderrmult * maxstd)
    plt.errorbar(datelist, means, stddevs, fmt=marker)
    plt.ylabel("ADU counts")
    ax.xaxis.set_major_formatter(df)
    ax.xaxis.set_major_locator(locat)
    for label in ax.get_xticklabels():
        label.set_rotation(rot)
        label.set_horizontalalignment('right')
    plt.legend([filter + " filter mean/std"])

plt.tight_layout()
if figout is None:
    plt.show()
else:
    figout = miscutils.replacesuffix(figout, ".png")
    plotfigure.savefig(figout)
    plt.close(plotfigure)
