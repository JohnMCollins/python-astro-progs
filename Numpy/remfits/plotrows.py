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

parsearg = argparse.ArgumentParser(description='Display slices through file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='Files to display')
parsearg.add_argument('--columns', action='store_true', help='Display by columns default by rows')
parsearg.add_argument('--nplot', type=int, nargs='+', help='Rows or columns to select')
parsearg.add_argument('--lefttrim', type=int, default=0, help='Trim rows/columns of display on left')
parsearg.add_argument('--righttrim', type=int, default=0, help='Trim rows/columns of display on right')
parsearg.add_argument('--colours', type=str, default='b,g,r,k,brown,purple', help='Colours of successive plots')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
ffiles = resargs['files']
columns = resargs['columns']
nplot = resargs['nplot']
lefttrim = resargs['lefttrim']
righttrim = resargs['righttrim']
outfig = rg.disp_getargs(resargs)
colours = resargs['colours'].split(',')

nplots = len(ffiles) * len(nplot)
colours *= nplots  # Way too many but don't faff around

plotfigure = rg.plt_figure()
tbits = []
if columns:
    plotfigure.canvas.manager.set_window_title("File comparison by columns")
    plt.xlabel("Row number")
    plt.ylabel("Column value")
else:
    plotfigure.canvas.manager.set_window_title("File comparison by rlws")
    plt.xlabel("Column number")
    plt.ylabel("Row value")

nplots = cplot = 0
legends = []

for ffile in ffiles:

    try:
        ff = fits.open(ffile)
    except OSError as e:
        print("Cannot open", ffile, e.strerror, file=sys.stderr)
        continue

    abbfile = miscutils.removesuffix(ffile)

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
    cplot += 1

    if columns:
        xdisp = np.arange(0, fd.shape[0])
        if lefttrim > 0:
            fd = fd[lefttrim:]
            xdisp = xdisp[lefttrim:]
        if righttrim > 0:
            fd = fd[:-righttrim]
            xdisp = xdisp[:-righttrim]
        tbits.append("%d. %s file for %s filter by cols" % (cplot, abbfile, filter))
        for c in nplot:
            legends.append("File %s column %d" % (cplot, c))
            plt.plot(xdisp, fd[:, c], color=colours[nplots])
            nplots += 1
    else:
        xdisp = np.arange(0, fd.shape[1])
        if lefttrim > 0:
            fd = fd[:, lefttrim:]
            xdisp = xdisp[lefttrim:]
        if righttrim > 0:
            fd = fd[:, :-righttrim]
            xdisp = xdisp[:-righttrim]
        tbits.append("%d. %s file for %s filter by rows" % (cplot, abbfile, filter))
        for r in nplot:
            legends.append("File %s row %d" % (cplot, r))
            plt.plot(xdisp, fd[r], color=colours[nplots])
            nplots += 1

plt.title("\n".join(tbits))
plt.legend(legends)

if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)
