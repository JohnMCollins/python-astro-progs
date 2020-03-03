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
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
ffile = resargs['file'][0]
columns = resargs['columns']
nplot = resargs['nplot']
lefttrim = resargs['lefttrim']
righttrim = resargs['righttrim']
outfig = resargs['outfig']
outfig = rg.disp_getargs(resargs)

ff = fits.open(ffile)
fhdr = ff[0].header

filter = None

try:
    filter = fhdr['FILTER']
except KeyError:
    pass

try:
    ffilename = fhdr['FILENAME']
except KeyError:
    print(ffile, "has no file name in it", file=sys.stdder)
    sys.exit(9)

if filter is None:
    m = re.search('([UB][LR])', ffilename)
    if m:
        filter = filtfn[m.group(1)]
    else:
        print("Cannot find filter in filename", ffilename, "in", ffile, file=sys.stderr)
        sys.exit(10)

mtype = ffilename

if ffilename[0] == 'F':
    mtype = "Daily flat"
elif ffilename[0] == 'B':
    mtype = "Daily bias"
elif ffilename[0] == 'I':
    mtype = "Obs image"
elif ffilename[0] == 'm' and len(ffilename) > 7:
    if ffilename[7] == 'f':
        mtype = "Master flat"
    elif ffilename[7] == 'b':
        mtype = "Master bias"

datef = Time(fhdr['DATE-OBS']).datetime
fd = trimarrays.trimzeros(trimarrays.trimnan(ff[0].data))
ff.close()

plotfigure = rg.plt_figure()

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
    tbits.append("%s file for %s filter displayed by columns" % (mtype, filter))
    tbits.append("Dated %s" % datef.strftime("%d/%m/%Y @ %H:%M:%S"))
    tbits.append("Mean value %.2f Std devv %.2f" % (fd.mean(), fd.std()))
    plt.title("\n".join(tbits))
    legs = []
    for c in nplot:
        legs.append("Column %d" % c)
        plt.plot(xdisp, fd[:, c])
    plt.legend(legs)
    plt.xlabel("Row number")
    plt.ylabel("Column value")
else:
    plotfigure.canvas.set_window_title("Flat file display by rows")
    plt.title("Flat file display by rows filter " + filter + datef.strftime(" %d/%m/%Y @ %H:%M:%S"))
    xdisp = np.arange(0, fd.shape[1])
    if lefttrim > 0:
        fd = fd[:, lefttrim:]
        xdisp = xdisp[lefttrim:]
    if righttrim > 0:
        fd = fd[:, :-righttrim]
        xdisp = xdisp[:-righttrim]
    tbits = []
    tbits.append("%s file for %s filter displayed by rows" % (mtype, filter))
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
