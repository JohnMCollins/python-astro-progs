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
import datetime
import os.path
import objcoord
import trimarrays
import wcscoord
import warnings
import miscutils
import remdefaults
import remgeom
import remget
import remfits
import fitsops
import strreplace
import col_from_file
import find_results

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display negative pixels', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('files', type=str, nargs='*', help='File names/IDs to display otherwise use id/file list from standard input')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--colours', type=str, default='red,white,blue', help='3 comma-sep colour names')
parsearg.add_argument('--hpercent', type=float, default=90.0, help='Percent at which to display in high colour')
parsearg.add_argument('--displimit', type=int, default=30, help='Maximum number of images to display')

rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

files = resargs['files']
if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
figout = rg.disp_getargs(resargs)
displimit = resargs['displimit']
hpercent = resargs['hpercent']

collist = resargs['colours'].split(',')
if len(collist) != 3:
    print("Expecting 3 colours, not", resargs['colours'], file=sys.stderr)
    sys.exit(20)
cmap = colors.ListedColormap(collist)

nfigs = len(files)
fignum = 0

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

db, dbcurs = remdefaults.opendb()

# Get details of object once only if doing multiple pictures

for file in files:

    try:
        ff = remfits.parse_filearg(file, dbcurs)
    except remfits.RemFitsErr as e:
        print(file, "open error", e.args[0], file=sys.stderr)
        continue

    fdat = ff.data
    plotfigure = rg.plt_figure()
    plotfigure.canvas.manager.set_window_title('Negative pixels ' + file)

    crange = [fdat.min(), 0.0, np.percentile(fdat, hpercent), fdat.max()]
    norm = colors.BoundaryNorm(crange, cmap.N)
    img = plt.imshow(fdat, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)

    fignum += 1
    if figout is None:
        if fignum >= displimit:
            print("Stopping display as reached", displimit, "images", file=sys.stderr)
            break
    else:
        if nfigs > 1:
            outfile = figout + "%.3d" % fignum + ".png"
        else:
            outfile = figout + ".png"
        plotfigure.savefig(outfile)
        plt.close(plotfigure)

if fignum == 0:
    print("Nothing displayed", file=sys.stderr)
    sys.exit(1)
if figout is None:
    plt.show()
