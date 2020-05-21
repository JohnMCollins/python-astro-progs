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

tmpdir = remdefaults.get_tmpdir()
mydbname = remdefaults.default_database()

parsearg = argparse.ArgumentParser(description='Display image files raw', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='File names to display (or FITS its)')
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use if needed')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files if needed')
parsearg.add_argument('--title', type=str, default="Image display", help="Title for each plot")
parsearg.add_argument('--xlabel', type=str, default="Column number", help="X xxis label")
parsearg.add_argument('--ylabel', type=str, default="Row number", help="Y xxis label")
parsearg.add_argument('--greyscale', type=str, required=True, help="Standard greyscale to use")
parsearg.add_argument('--histbins', type=int, default=20, help='Bins for histogram')
parsearg.add_argument('--logscale', action='store_true', help='Use log scale for histogram')
parsearg.add_argument('--colourhist', type=str, default='b', help='Colour of historgram')
parsearg.add_argument('--histtitle', type=str, default='Distribution of pixel values', help='Histogram Title')
parsearg.add_argument('--histxlab', type=str, default='Pixel value', help='Label for histogram X axis')
parsearg.add_argument('--histylab', type=str, default='Occurences of vaalue', help='Label for histogram Y axis')
parsearg.add_argument('--addsk', action='store_false', help='Add stats to histogram title')
parsearg.add_argument('--detach', action='store_true', help='Detaach as child process actter checking args')
rg.disp_argparse(parsearg, "dwin")

resargs = vars(parsearg.parse_args())

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

mydbname = resargs['database']
tmpdir = resargs['tempdir']
greyscalename = resargs['greyscale']
files = resargs['files']
logscale = resargs['logscale']
title = resargs['title']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
figout = rg.disp_getargs(resargs)
histbins = resargs['histbins']
colourhist = resargs['colourhist']
histxlab = resargs['histxlab']
histylab = resargs['histylab']
histtitle = resargs['histtitle']
addsk = resargs['addsk']
detach = resargs['detach']

gsdets = rg.get_greyscale(greyscalename)
if gsdets is None:
    print("Sorry grey scale", greyscalename, "is not defined", file=sys.stderr)
    sys.exit(9)

collist = gsdets.get_colours()
cmap = colors.ListedColormap(collist)

nfigs = len(files)
fignum = 1

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

plt.rc('figure', max_open_warning=100)
# Get details of object once only if doing multiple pictures

dbase = None  # only open this i we need to
origdir = os.getcwd()

if detach:
    if os.fork() != 0:
        os._exit(0)
    sys.stdout = fixtty(sys.stdout)
    sys.stderr = fixtty(sys.stderr)

for file in files:
    
    if file.isdecimal():
        if dbase is None:
            try:
                os.chdir(tmpdir)
            except FileNotFoundError:
                print("Unable to select temporary directory", tmpdir, file=sys.stderr)
                sys.exit(100)
            try:
                dbase = dbops.opendb(mydbname)
                dbcurs = dbase.cursor()
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
    plt.subplot(121)

    crange = gsdets.get_cmap(dat)
    norm = colors.BoundaryNorm(crange, cmap.N)
    img = plt.imshow(dat, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)

    tit = title
    tit += "\nfor " + ftype + " file filter " + filter + "\n" + when.strftime("Date %d/%m/%Y @ %H:%M:%S")
    plt.title(tit)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.subplot(122)

    flatdat = dat.flatten()
    mv = flatdat.mean()
    medv = np.median(flatdat)
    stdv = flatdat.std()
    plt.hist(flatdat, bins=histbins, color=colourhist, log=logscale)
    plt.xlabel(histxlab)
    plt.ylabel(histylab)

    tit = histtitle
    if  addsk:
        tit += " mean %.6g\nMedian=%.6g (norm %.6g)\nStd dev=%.4g (norm %.4g)" % (mv, medv, medv / mv, stdv, stdv / mv)
    plt.title(tit)

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
