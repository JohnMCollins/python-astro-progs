#! /usr/bin/env python3

"""Do 3d plot of image"""

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
from mpl_toolkits.mplot3d import Axes3D
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

parsearg = argparse.ArgumentParser(description='Display image files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('files', type=str, nargs='*', help='File names/IDs to display otherwise use id/file list from standard input')
parsearg.add_argument('--type', type=str, choices=['F', 'B', 'Z', 'I'], help='Insert Z F B or I to select numerics as FITS ind, flat, bias, or Obs image (default)')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--colour', type=str, default='b', help="Colour of plot")
parsearg.add_argument('--title', type=str, help='Optional title to put at head of image otherwise based on file')
parsearg.add_argument('--findres', type=str, help='File of find results')
parsearg.add_argument('--limfind', type=int, default=1000000, help='Maximumm number of find results')
parsearg.add_argument('--brightest', action='store_true', help='Mark brightest object as target if no target')
parsearg.add_argument('--displimit', type=int, default=30, help='Maximum number of images to display')
parsearg.add_argument('--trim', type=int, default=0, help='Rows and columns to trim"')

rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

files = resargs['files']
if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
ftype = resargs['type']
figout = rg.disp_getargs(resargs)
plotcolour = resargs['colour']
title = resargs['title']
findres = resargs['findres']
limfind = resargs['limfind']
brightest = resargs['brightest']
displimit = resargs['displimit']
trim = resargs['trim']

findresults = None
if findres is not None:
    try:
        findresults = find_results.load_results_from_file(findres)
    except find_results.FindResultErr as e:
        print("Read of results file gave error", e.args[0], file=sys.stderr)
        sys.exit(6)
    idcolour = rg.objdisp.idcolour
    objcolour = rg.objdisp.objcolour
    targetcolour = rg.objdisp.targcolour

nfigs = len(files)
fignum = 0

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

db, dbcurs = remdefaults.opendb()

# Get details of object once only if doing multiple pictures

for file in files:

    try:
        ff = remfits.parse_filearg(file, dbcurs, typef=ftype)
    except remfits.RemFitsErr as e:
        print(file, "open error", e.args[0], file=sys.stderr)
        continue

    data = ff.data
    plotfigure = rg.plt_figure()
    plotfigure.canvas.set_window_title('FITS Image from file ' + file)
    ax = plotfigure.add_subplot(111, projection='3d')
    rows, cols = data.shape
    xvals = np.tile(range(0, cols), (rows, 1))
    yvals = np.tile(range(0, rows), (cols, 1)).transpose()
    if trim != 0:
        data = data[trim:-trim, trim:-trim]
        xvals = xvals[trim:-trim, trim:-trim]
        yvals = yvals[trim:-trim, trim:-trim]
    ax.plot_wireframe(xvals, yvals, data, color=plotcolour)
#     try:
#         rg.radecgridplt(ff.wcs, data)
#     except AttributeError:
#         pass  # Lazy way of testing for WCS coords
    if title is None:
        plt.title(ff.description)
    elif len(title) != 0:
        plt.title(title)

    if findresults is not None:
        w = ff.wcs
        countt = 0
        targetcount = -1
        for fr in findresults.results():
            if fr.istarget:
                targetcount = countt
                break
            countt += 1
        if targetcount < 0 and brightest:
            targetcount = 0
        n = 0
        for fr in findresults.results():
            coords = w.coords_to_pix(np.array((fr.radeg, fr.decdeg)).reshape(1, 2))[0]
            # print("Name is:", "'" + fr.name + "'", file=sys.stderr)
            if n == targetcount:
                objc = targetcolour
            elif len(fr.name) != 0:
                objc = idcolour
            else:
                objc = objcolour
            ptch = mp.Circle(coords, radius=fr.apsize, alpha=rg.objdisp.objalpha, color=objc, fill=rg.objdisp.objfill)
            plt.gca().add_patch(ptch)
            displ = coords[0] + rg.objdisp.objtextdisp
            if displ > data.shape[0]:
                displ = coords[0] - rg.objdisp.objtextdisp
            plt.text(displ, coords[1], fr.label, fontsize=rg.objdisp.objtextfs, color=objc)
            n += 1
            if n >= limfind:
                break
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
