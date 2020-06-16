#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-23T14:20:00+01:00
# @Email:  jmc@toad.me.uk
# @Filename: dbobjdisp.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:02:43+00:00

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib import colors
import argparse
import sys
import re
import datetime
import os
import os.path
import trimarrays
import warnings
import miscutils
import strreplace
import remgeom
import remdefaults
import dbops
import dbremfitsobj
import remfitshdr


def fixtty(f):
    """If output stream is connected to a pipe, we need to reconnect it to tty
    otherwise pipes won't be closed"""
    if f.isatty():
        return f
    nt = open("/dev/tty", 'wb')
    fd = f.fileno()
    os.dup2(nt.fileno(), fd)
    nt.close()
    return os.fdopen(fd, 'wb', 0)


rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Highlight bias values with extremes in diff colour', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='File names to display (or FITS its)')
remdefaults.parseargs(parsearg)
parsearg.add_argument('--title', type=str, default="Extremes display", help="Title for each plot")
parsearg.add_argument('--xlabel', type=str, default="Column number", help="X xxis label")
parsearg.add_argument('--ylabel', type=str, default="Row number", help="Y xxis label")
parsearg.add_argument('--histbins', type=float, nargs='+', default=[20.0], help='Bins for histogram and colour scale')
parsearg.add_argument('--nozeros', action='store_false', help='Do not include zeros in histogram')
parsearg.add_argument('--logscale', action='store_true', help='Use log scale for histogram')
parsearg.add_argument('--xlog', action='store_true', help='Use log scale on histogram X aris')
parsearg.add_argument('--hvcolour', type=str, nargs='*', help='Colours for exceptional high values')
parsearg.add_argument('--histtitle', type=str, default='Distribution of values', help='Histogram Title')
parsearg.add_argument('--histxlab', type=str, default='Value', help='Label for histogram X axis')
parsearg.add_argument('--histylab', type=str, default='Occurences of value', help='Label for histogram Y axis')
parsearg.add_argument('--addsk', action='store_false', help='Add stats to histogram title')
parsearg.add_argument('--detach', action='store_true', help='Detaach as child process actter checking args')
rg.disp_argparse(parsearg, "dwin")

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

files = resargs['files']
logscale = resargs['logscale']
hxlog = resargs['xlog']
nozeros = resargs['nozeros']
title = resargs['title']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
figout = rg.disp_getargs(resargs)
histbins = resargs['histbins']
hvcolour = resargs['hvcolour']
histxlab = resargs['histxlab']
histylab = resargs['histylab']
histtitle = resargs['histtitle']
addsk = resargs['addsk']
detach = resargs['detach']

if hvcolour is None:
    hvcolour = []
nhvs = len(hvcolour)

nhistbins = len(histbins)
if nhistbins == 1:
    nhistbins = int(histbins[0])
    histbins = None
else:
    nhistbins += 1  # One more than number of colours

collist = ['#%.2x%.2x%.2x' % (int(l), int(l), int(l)) for l in np.linspace(255, 0, nhistbins - nhvs).round()] + hvcolour
    
cmap = colors.ListedColormap(collist)

nfigs = len(files)
fignum = 1

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

plt.rc('figure', max_open_warning=100)

dbase = None  # only open this i we need to

if detach:
    if os.fork() != 0:
        os._exit(0)
    sys.stdout = fixtty(sys.stdout)
    sys.stderr = fixtty(sys.stderr)

for file in files:

    if not file.isdecimal() and not miscutils.hassuffix(file, '.fits.gz') and not miscutils.hassuffix(file, '.fits'):
        lf = remdefaults.libfile(miscutils.addsuffix(file, '.npy'))
        if not os.path.exists(lf):
            print("Cannot find", lf, file=sys.stderr)
            continue
        dat = np.load(lf)
        if len(dat.shape) != 2:
            print("Expecting", lf, "to be 2d array not", dat.shape, file=sys.stderr)
            continue
        rfh = None
    else:
        if file.isdecimal():
            if dbase is None:
                try:
                    dbase, dbcurs = remdefaults.opendb()
                except dbops.dbopsError as e:
                    print("Could not open database", mydbname, "error was", e.args[0], file=sys.stderr)
                    sys.exit(101)
            try:
                ff = dbremfitsobj.getfits(dbcurs, int(file))
            except dbremfitsobj.RemObjError as e:
                print("Cannot open FITS id", file, e.args[0], file=sys.stderr)
                continue
            except OSError as e:
                print("Cannot open FITS id", file, "error was", e.args[1], file=sys.stderr)
                continue
        else:
            try:
                ff = fits.open(os.path.join(origdir, file))
            except OSError as e:
                print("Cannot open", file, e.strerror, file=sys.stderr)
                continue
        try:
            rfh = remfitshdr.RemFitsHdr(ff[0].header)
        except remfitshdr.RemFitsHdrErr as e:
            print("Problem with file", file, "error was", e.args[0])
            continue
        
        dat = trimarrays.trimzeros(trimarrays.trimnan(ff[0].data.astype(np.float64)))
        ff.close()

        when = rfh.date
        filter = rfh.filter
        ftype = rfh.ftype

    plotfigure = rg.plt_figure()
    plotfigure.canvas.set_window_title('FITS Image from file ' + file)
    
    hax = plt.subplot(122)

    flatdat = dat.flatten()
    if nozeros:
        flatdat = flatdat[flatdat != 0]
    mv = flatdat.mean()
    medv = np.median(flatdat)
    stdv = flatdat.std()
    if histbins is None:
        bspec = nhistbins
    else:
        bspec = sorted(histbins + [flatdat.min(), flatdat.max()])
    if hxlog:
        hax.set_xscale('log')
    vals, bins, patches = plt.hist(flatdat, bins=bspec, log=logscale)
    for p, c in zip(patches, collist):
        p.set_facecolor(c)
    plt.xlabel(histxlab)
    plt.ylabel(histylab)
    
    tit = histtitle
    if  addsk:
        tit += " mean %.6g\nMedian=%.6g (norm %.6g)\nStd dev=%.4g (norm %.4g)" % (mv, medv, medv / mv, stdv, stdv / mv)
    plt.title(tit)
    
    plt.subplot(121)
    if nozeros:
        bins[0] = dat.min()
    
    norm = colors.BoundaryNorm(bins, cmap.N)
    img = plt.imshow(dat, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=bins, ticks=bins)

    tit = title
    if rfh is not None:
        tit += "\nfor " + ftype + " file filter " + filter + "\n" + when.strftime("Date %d/%m/%Y @ %H:%M:%S")
    plt.title(tit)
    plt.xlabel(xlab)
    plt.ylabel(ylab)

    if figout is not None:
        if nfigs > 1:
            outfile = figout + "%.3d" % fignum + ".png"
            fignum += 1
        else:
            outfile = figout + ".png"
        plotfigure.savefig(outfile)
        plt.close(plotfigure)

if figout is None:
    plt.show()
    os._exit(0)
