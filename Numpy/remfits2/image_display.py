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

parsearg = argparse.ArgumentParser(description='Display image files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('files', type=str, nargs='*', help='File names/IDs to display otherwise use id/file list from standard input')
parsearg.add_argument('--type', type=str, choices=['F', 'B', 'Z', 'I'], help='Insert Z F B or I to select numerics as FITS ind, flat, bias, or Obs image (default)')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--greyscale', type=str, required=True, help="Standard greyscale to use")
parsearg.add_argument('--title', type=str, help='Optional title to put at head of image otherwise based on file')
parsearg.add_argument('--findres', type=str, help='File of find results')
parsearg.add_argument('--limfind', type=int, default=1000000, help='Maximumm number of find results')
parsearg.add_argument('--brightest', action='store_true', help='Mark brightest object as target')
parsearg.add_argument('--displimit', type=int, default=30, help='Maximum number of images to display')

rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

files = resargs['files']
if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
ftype = resargs['type']
figout = rg.disp_getargs(resargs)
greyscalename = resargs['greyscale']
title = resargs['title']
findres = resargs['findres']
limfind = resargs['limfind']
brightest = resargs['brightest']
displimit = resargs['displimit']

findresults = None
if findres is not None:
    try:
        findresults = find_results.load_results_from_file(findres)
    except find_results.FindResultErr as e:
        print("Read of results file gave error", e.args[0], file=sys.stderr)
        sys.exit(6)
    objcolours = rg.objdisp.objcolour
    targetcolour = objcolours[0]
    if len(objcolours) > 1:
        objcolours.pop(0)

gsdets = rg.get_greyscale(greyscalename)
if gsdets is None:
    print("Sorry grey scale", greyscalename, "is not defined", file=sys.stderr)
    sys.exit(9)

collist = gsdets.get_colours()
cmap = colors.ListedColormap(collist)

nfigs = len(files)
fignum = 0

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

db, dbcurs = remdefaults.opendb()

# Get details of object once only if doing multiple pictures

for file in files:

    try:
        ff = remfits.parse_filearg(file, dbcurs, type=ftype)
    except remfits.RemFitsErr as e:
        print(file, "open error", e.args[0], file=sys.stderr)
        continue

    data = ff.data
    plotfigure = rg.plt_figure()
    plotfigure.canvas.set_window_title('FITS Image from file ' + file)

    crange = gsdets.get_cmap(data)
    norm = colors.BoundaryNorm(crange, cmap.N)
    img = plt.imshow(data, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
    try:
        rg.radecgridplt(ff.wcs, data)
    except AttributeError:
        pass  # Lazy way of testing for WCS coords
    if title is None:
        plt.title(ff.description)
    elif len(title) != 0:
        plt.title(tit)

    if findresults is not None:
        w = ff.wcs
        countt = n = 0
        for fr in findresults.results():
            coords = w.coords_to_pix(np.array((fr.radeg, fr.decdeg)).reshape(1, 2))[0]
            if brightest:
                if countt == 0:
                    objc = targetcolour
                else:
                    objc = objcolours[n % len(objcolours)]
                    n += 1
            elif fr.istarget:
                objc = targetcolour
            else:
                objc = objcolours[n % len(objcolours)]
                n += 1
            ptch = mp.Circle(coords, radius=fr.apsize, alpha=rg.objdisp.objalpha, color=objc, fill=rg.objdisp.objfill)
            plt.gca().add_patch(ptch)
            displ = coords[0] + rg.objdisp.objtextdisp
            if displ > data.shape[0]:
                displ = coords[0] - rg.objdisp.objtextdisp
            plt.text(displ, coords[1], fr.label, fontsize=rg.objdisp.objtextfs, color=objc)
            countt += 1
            if countt >= limfind:
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
