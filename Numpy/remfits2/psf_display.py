#! /usr/bin/env python3

"""Display cross-sections in image showing PSFs"""

import sys
import warnings
import argparse
import math
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import astroquery.utils as autils
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np
import scipy.optimize as opt
import remdefaults
import remgeom
import remfits
import objdata
import col_from_file
import find_results
import gauss2d

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display profile of image round given source', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('files', type=str, nargs='*', help='File names/IDs to display otherwise use ids or files from standard input')
parsearg.add_argument('--prefix', type=str, help='Prefix to apply to numeric file names')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--title', type=str, help='Optional title to put at head of image otherwise based on file')
parsearg.add_argument('--findres', type=str, help='File of find results if not the same as input file')
parsearg.add_argument('--limfind', type=int, default=1000000, help='Maximumm number of find results')
parsearg.add_argument('--displimit', type=int, default=30, help='Maximum number of images to display')
parsearg.add_argument('--object', type=str, nargs='+', required=True, help='Object labels or names (get vicinity from file if needed)')
parsearg.add_argument('--plotcolour', type=str, default='b', help='Colour of plot')
parsearg.add_argument('--plotalpha', type=float, default=0.8, help='Alpha for plot"')
parsearg.add_argument('--negresidcolour', type=str, default='r', help='Colour for residuals negative plot')
parsearg.add_argument('--posresidcolour', type=str, default='g', help='Colour for residuals positive plot')
parsearg.add_argument('--residalpha', type=float, default=1.0, help='Colour for residuals alpha')
parsearg.add_argument('--fitcolour', type=str, default='g', help='Colour of fit surface')
parsearg.add_argument('--minap', type=float, default=1.0, help="Minimum aperture")
parsearg.add_argument('--plotstep', type=float, default=.25, help="Step when plotting fit")
parsearg.add_argument('--margin', type=float, default=3.0, help='Margin round object in display')
parsearg.add_argument('--multi', action='store_true', help='Treat one file as multiple')
parsearg.add_argument('--surfalpha', type=float, default=0.25, help='Alpha value for surface plot')

rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

files = resargs['files']
if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

figout = rg.disp_getargs(resargs)

title = resargs['title']
fprefix = resargs['prefix']
if fprefix is None:
    fprefix = ""
findres = resargs['findres']
limfind = resargs['limfind']
displimit = resargs['displimit']
objnames = resargs['object']
minap = resargs['minap']
margin = resargs['margin']
multi = resargs['multi'] or len(files) > 1
pstep = resargs['plotstep']
surfalpha = resargs['surfalpha']
fitcolour = resargs['fitcolour']
plotcolour = resargs['plotcolour']
plotalpha = resargs['plotalpha']
negresidcolour = resargs['negresidcolour']
posresidcolour = resargs['posresidcolour']
residalpha = resargs['residalpha']

cmap = colors.ListedColormap([negresidcolour,posresidcolour])
norm = colors.BoundaryNorm([-1e6, 0, 1e6], cmap.N)
db, dbcurs = remdefaults.opendb()
plt.rc('figure', max_open_warning=0)

verified_objnames = []
for objname in objnames:
    if len(objname) > 4:
        try:
            verified_objnames.append(objdata.get_objname(dbcurs, objname))
        except objdata.ObjDataError as e:
            print("Cannot understand object name", objname, e.args[0], file=sys.stderr)
    else:
        verified_objnames.append(objname)

# Get details of object once only if doing multiple pictures

plotnum = 0

for file in files:

    try:
        ff = remfits.parse_filearg(fprefix + file, dbcurs)
    except remfits.RemFitsErr as e:
        print(file, "open error", e.args[0], file=sys.stderr)
        continue

    data = ff.data - ff.meanval
    pixrows, pixcols = data.shape


    # Get findres from file if it exists, otherwise get from database

    try:
        findres = find_results.load_results_from_file(fprefix + file, ff)
    except find_results.FindResultErr as e:
        findres = find_results.FindResults(ff)
        findres.loaddb(dbcurs)

    for objname in verified_objnames:

        try:
            fr = findres[objname]
        except find_results.FindResultErr as e:
            print("Could not find", objname, "in", file=sys.stderr)
            continue

        apsize = max(fr.apsize, minap)
        minrow = int(math.ceil(fr.row - apsize - margin))
        maxrow = int(math.floor(fr.row + apsize + 1 + margin))
        mincol = int(math.ceil(fr.col - apsize - margin))
        maxcol = int(math.floor(fr.col + apsize + 1 + margin))
        if minrow < 0 or mincol < 0 or maxrow > pixrows or maxcol > pixcols:
            print("Omitting", objname, "too close to edge", file=sys.stderr)
            continue

        datseg = data[minrow:maxrow, mincol:maxcol]
        scdat = datseg / datseg.mean()
        iapsize = int(apsize)
        iapplusmarg = int(apsize + margin)
        apsq = apsize ** 2
        aprange = range(-iapsize, iapsize+1)
        aplusmarg = range(-iapplusmarg, iapplusmarg+1)
        faplusmarg = np.arange(-iapplusmarg,iapplusmarg+1.0, pstep)
        datcoords = [(y, x) for y in aprange for x in aprange if x**2+y**2 <= apsq]
        datvals = np.array([scdat[y+iapplusmarg,x+iapplusmarg] for y, x in datcoords])
        lresult = opt.curve_fit(gauss2d.gauss_circle, np.array(datcoords), datvals, p0=(0, 0, max(datvals), np.std(datvals)))

        xoffset, yoffset, amp, sig = lresult[0]
        amp *= datseg.mean()
        print("x/yoffs={:.2f}/{:.2f} amp={:.6g} sig={:.6g}".format(xoffset, yoffset, amp, sig), file=sys.stderr)

        plotfigure = rg.plt_figure()
        plotfigure.canvas.manager.set_window_title("{:s} ({:s}) filter {:s} on {:%d/%m/%Y at %H:%M:%S}".format(fr.obj.dispname, fr.label, findres.filter, findres.obsdate))
        ax = plotfigure.add_subplot(121, projection='3d')
        xvals = np.tile(aplusmarg, (iapplusmarg*2+1, 1))
        yvals = xvals.transpose()
        ax.plot_wireframe(xvals, yvals, datseg, color=plotcolour, alpha=plotalpha)
        zmin, zmax = ax.get_zlim()
        fitpoints = gauss2d.gauss2d(xvals-xoffset, yvals-yoffset, amp, sig)
        ax.plot_surface(xvals, yvals, fitpoints, color=fitcolour, alpha=surfalpha)
        ax = plotfigure.add_subplot(122, projection='3d')
        fitpoints -= datseg
        if np.sum(fitpoints) < 0.0:
            fitpoints = - fitpoints
        ax.plot_surface(xvals, yvals, fitpoints, cmap=cmap, alpha=residalpha)
        zmin2, zmax2 = ax.get_zlim()
        mult = (zmax-zmin)/(zmax2-zmin2)
        ax.set_zlim(zmin2*mult, zmax2*mult)
        plt.tight_layout()
        plotnum += 1
        remgeom.end_figure(plotfigure, figout, plotnum, multi)

remgeom.end_plot(figout)
