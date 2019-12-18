#!  /usr/bin/env python3

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import re
import trimarrays
import matplotlib.pyplot as plt
from matplotlib import colors
import remgeom
import miscutils

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

filtfn = dict(BL='z', BR="r", UR="g", UL="i")

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display slices through flat file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs=1, help='File to display')
parsearg.add_argument('--columns', action='store_true', help='Display by columns default by rows')
parsearg.add_argument('--nplot', type=int, nargs='+', help='Rows or columns to select')
parsearg.add_argument('--lefttrim', type=int, default=0, help='Trim columns of display on left')
parsearg.add_argument('--righttrim', type=int, default=0, help='Trim columns of display on right')
parsearg.add_argument('--width', type=float, default=rg.width, help="Width of figure")
parsearg.add_argument('--height', type=float, default=rg.height, help="height of figure")
parsearg.add_argument('--outfig', type=str, help='Output figure if required')

resargs = vars(parsearg.parse_args())
ffile = resargs['file'][0]
columns = resargs['columns']
nplot = resargs['nplot']
lefttrim = resargs['lefttrim']
righttrim = resargs['righttrim']
width = resargs['width']
height = resargs['height']
outfig = resargs['outfig']

ff = fits.open(ffile)
fhdr = ff[0].header
ffilename = fhdr['FILENAME']
mtype = 'Daily'
if ffilename[0] != 'F':
    mtype = "Master"

m = re.search('([UB][LR])', ffilename)
if m:
    filter = filtfn[m.group(1)]
else:
    print("Cannot find filter in filename", ffilename, file=sys.stderr)
    sys.exit(10)

datef = Time(fhdr['DATE-OBS']).datetime
fd = trimarrays.trimzeros(trimarrays.trimnan(ff[0].data))
ff.close()

plotfigure = plt.figure(figsize=(width, height))

if columns:
    plotfigure.canvas.set_window_title("Flat file display by columns")
    xdisp = np.arange(0, fd.shape[0])
    if lefttrim > 0:
        fd = fd[lefttrim:]
        xdisp = xdisp[lefttrim:]
    if righttrim > 0:
        fd = fd[:-righttrim]
        xdisp = xdisp[:-righttrim]
    tbits = []
    tbits.append("%s flat file for %s filter displayed by coloumns" % (mtype, filter))
    tbits.append("Dated %s" % datef.strftime("%d/%m/%Y @ %H:%M:%S"))
    tbits.append("Mean value %.2f Std devv %.2f" % (fd.mean(), fd.std()))
    plt.title("\n".join(tbits))
    legs = []
    for c in nplot:
        legs.append("Column %d" % c)
        plt.plot(xdisp, fd[:,c])
    plt.legend(legs)
    plt.xlabel("Row number")
    plt.ylabel("Column value")
else:
    plotfigure.canvas.set_window_title("Flat file display by rows")
    plt.title("Flat file display by rows filter " + filter + datef.strftime(" %d/%m/%Y @ %H:%M:%S"))
    xdisp = np.arange(0, fd.shape[1])
    if lefttrim > 0:
        fd = fd[:,lefttrim:]
        xdisp = xdisp[lefttrim:]
    if righttrim > 0:
        fd = fd[:,:-righttrim]
        xdisp = xdisp[:-righttrim]
    tbits = []
    tbits.append("%s flat file for %s filter displayed by rows" % (mtype, filter))
    tbits.append("Dated %s" % datef.strftime("%d/%m/%Y @ %H:%M:%S"))
    tbits.append("Mean value %.2f Std dev %.2f" % (fd.mean(), fd.std()))
    plt.title("\n".join(tbits))
    legs = []
    for r in nplot:
        legs.append("Row %d" % r)
        plt.plot(xdisp, fd[r])
    plt.legend(legs)
    plt.xlabel("Column number")
    plt.ylabel("Row value")

if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)
