#! /usr/bin/env python3

"""Display images of obs mostly"""

import sys
import warnings
import argparse
import signal
import subprocess
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import astroquery.utils as autils
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib import colors
from matplotlib.backend_bases import MouseButton
import miscutils
import remdefaults
import remgeom
import remfits
import col_from_file
import find_results
from argon2._ffi import ffi


class figuredata:
    """Remember image file and find results data for display"""

    def __init__(self, prefixname, fitsfile, annot, findr=None):
        self.prefix = prefixname
        self.fitsfile = fitsfile
        self.findres = findr
        self.carray = None
        self.labs = None
        if findr:
            car = []
            labs = []
            for r in findr.results():
                if not r.hide:
                    car.append(complex(r.col, r.row))
                    labs.append(r.label)
            self.carray = np.array(car)
            self.labs = labs
        self.annot = annot

    def results_in_area(self, event):
        """Get results in area closest to given event row and column"""
        if self.findres is None or event.xdata is None or event.ydata is None:
            return  None
        dists = np.abs(self.carray - complex(event.xdata, event.ydata))
        asrt = np.argsort(dists)
        asrt = asrt[dists[asrt] <= tagdist]
        if asrt.size == 0:
            return  None
        return  [self.findres[self.labs[a]] for a in asrt]

    def result_closest_to(self, event):
        """Get result closest to given event row and column"""
        ret = self.results_in_area(event)
        if ret is None:
            return  None
        return  ret[0]


figdict = dict()


def findfig(event):
    """Get figuredata instance from event"""
    try:
        return  figdict[event.canvas.get_window_title()]
    except KeyError:
        return  None


def setfig(fig, pref, fitsfile, findr=None):
    """Set up figure structure and callbacks and add to list"""
    ax = fig.axes[0]
    canv = fig.canvas
    canv.manager.set_window_title(pref)
    annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points", fontsize=rg.objdisp.objtextfs, bbox=dict(boxstyle="round", fc=popupcolour), arrowprops=dict(arrowstyle="->"))
    annot.get_bbox_patch().set_alpha(alphaflag)
    annot.set_visible(False)
    canv.mpl_connect('motion_notify_event', hover)
    canv.mpl_connect('button_press_event', button_press)
    figdict[prefix] = figuredata(prefix, fitsfile, annot, findr)


def hover(event):
    """Callback for mouse hover"""

    fd = findfig(event)
    if fd is None:
        return
    vis = fd.annot.get_visible()
    objr = fd.result_closest_to(event)
    if objr is None:
        if vis:
            fd.annot.set_visible(False)
            event.canvas.draw_idle()
        return
    dispn = "(not known)"
    if objr.obj is not None: dispn = objr.obj.dispname
    atxt = "{:s}: {:s}".format(objr.label, dispn)
    if objr.obj is not None or objr.adus > 0.0:
        atxt += "\n"
        if objr.obj is not None and objr.obj.gmag is not None:
            atxt += "gmag: {:.2f}".format(objr.obj.gmag)
            if objr.adus > 0.0:
                atxt += " "
        if objr.adus > 0.0:
            atxt += "adus: {:.1f} ap: {:.4g}".format(objr.adus, objr.apsize)
    fd.annot.set_text(atxt)
    # fd.annot.get_bbox_patch().set_alpha(0.4)
    fd.annot.xy = (objr.col, objr.row)
    fd.annot.set_visible(True)
    event.canvas.draw_idle()


def button_press(event):
    """Callback for button press"""

    if event.button is not MouseButton.RIGHT:
        return
    fd = findfig(event)
    if fd is None:
        return
    objr = fd.results_in_area(event)
    if objr is None:
        coordlist = fd.fitsfile.wcs.pix_to_coords(np.array(((event.xdata, event.ydata),)))
        ra, dec = coordlist[0]
        subprocess.Popen(('markobj.py', '--create', '--findres', fd.prefix, str(round(event.xdata)), str(round(event.ydata)), str(ra), str(dec)))
    else:
        for r in objr:
            subprocess.Popen(("markobj.py", '--findres', fd.prefix, r.label))


def display_findresults(ffile, work_findres):
    """Insert find results from supplied structure and image file"""
    w = ffile.wcs
    n = 0
    for fr in work_findres.results():
        if fr.hide:
            continue
        # coords = w.coords_to_pix(np.array((fr.radeg, fr.decdeg)).reshape(1, 2))[0]
        # print("Name is:", "'" + fr.name + "'", file=sys.stderr)
        coords = (fr.col, fr.row)
        if fr.istarget or (n == 0 and brightest):
            objc = targetcolour
        elif fr.obj is None or not fr.obj.valid_label():
            objc = idcolour
        else:
            objc = objcolour
        ptch = mp.Circle(coords, radius=fr.apsize, alpha=rg.objdisp.objalpha, color=objc, fill=rg.objdisp.objfill)
        ax = plt.gca()
        ax.add_patch(ptch)
        annot = ax.annotate(fr.label, xy=coords, xytext=(rg.objdisp.objtextdisp, rg.objdisp.objtextdisp), fontsize=rg.objdisp.objtextfs,
                            textcoords="offset points", bbox=dict(boxstyle="round", fc=flagcolour), arrowprops=dict(arrowstyle="->"))
        annot.get_bbox_patch().set_alpha(alphaflag)
        n += 1
        if n >= limfind:
            break

def set_zoom(ffile, zoomcol, zoomrow):
    """Set yo ziin ariybd guveb row and column"""
    prows, pcols = ffile.data.shape
    zrows = prows / factorzoom / 2
    zcols = pcols / factorzoom / 2
    plt.xlim(max(0, zoomcol-zcols), min(pcols, zoomcol+zcols))
    plt.ylim(max(0, zoomrow-zrows), min(prows, zoomrow+zrows))

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
parsearg.add_argument('--greyscale', type=str, help="Standard greyscale to use")
parsearg.add_argument('--title', type=str, help='Optional title to put at head of image otherwise based on file')
parsearg.add_argument('--findres', type=str, help='File of find results if not the same as input file')
parsearg.add_argument('--limfind', type=int, default=1000000, help='Maximumm number of find results')
parsearg.add_argument('--brightest', action='store_true', help='Mark brightest object as target if no target')
parsearg.add_argument('--displimit', type=int, default=30, help='Maximum number of images to display')
parsearg.add_argument('--setmax', type=str, help='Specify colour to set max to and max=1 to max')
parsearg.add_argument('--griddisp', action='store_false', help='Display RA/DEC grid if possible')
parsearg.add_argument('--flagcolour', type=str, default='yellow', help='Flag colour')
parsearg.add_argument('--popupcolour', type=str, default='g', help='Popup colour')
parsearg.add_argument('--alphaflag', type=float, default=0.4, help='Alpha for flag and popup')
parsearg.add_argument('--tagdist', type=float, default=15.0, help='Number of pixel distance to treat as closeby')
parsearg.add_argument('--zoomcoords', type=str, help='RA (deg)/DEC (deg) for centre zoom or object label')
parsearg.add_argument('--factorzoom', type=float, default=5.0, help='Factor to zoom by')

rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

files = resargs['files']
if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
ftype = resargs['type']
figout = rg.disp_getargs(resargs)
greyscalename = resargs['greyscale']
if greyscalename is None:
    greyscalename = rg.defgreyscale
    if greyscalename is None:
        print("No greyscale given, use --greyscale or set default one", file=sys.stderr)
        sys.exit(0)

title = resargs['title']
findres = resargs['findres']
limfind = resargs['limfind']
brightest = resargs['brightest']
displimit = resargs['displimit']
setmax = resargs['setmax']
griddisp = resargs['griddisp']
popupcolour = resargs['popupcolour']
flagcolour = resargs['flagcolour']
alphaflag = resargs['alphaflag']
tagdist = resargs['tagdist']
zoomcoords = resargs['zoomcoords']
factorzoom = resargs['factorzoom']

if zoomcoords is not None:
    griddisp = False
    zparts = zoomcoords.split(",")
    if len(zparts) == 2:
        try:
            zoomcoords = tuple(map(lambda x: float(x), zparts))
        except (TypeError, ValueError):
            print("Did not understand zoom coords", zoomcoords, "expecting RA/Dec or label", file=sys.stderr)
            sys.exit(80)
    elif len(zparts) != 1:
        print("Did not understand zoom coords", zoomcoords, "expecting RA/Dec or label", file=sys.stderr)
        sys.exit(81)

idcolour = rg.objdisp.idcolour
objcolour = rg.objdisp.objcolour
targetcolour = rg.objdisp.targcolour

# findresults = None
# if findres is not None and findres != '@':
#    try:
#        findresults = find_results.load_results_from_file(findres)
#    except find_results.FindResultErr as e:
#        print("Read of results file gave error", e.args[0], file=sys.stderr)
#        sys.exit(6)

gsdets = rg.get_greyscale(greyscalename)
if gsdets is None:
    print("Sorry grey scale", greyscalename, "is not defined", file=sys.stderr)
    sys.exit(9)

collist = gsdets.get_colours()
if setmax is not None:
    collist[-2] = collist[-1]
    collist[-1] = setmax
cmap = colors.ListedColormap(collist)

nfigs = len(files)
fignum = 0

if figout is None:
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
else:
    figout = miscutils.removesuffix(figout, '.png')

db, dbcurs = remdefaults.opendb()

plt.rc('figure', max_open_warning=0)

# Get details of object once only if doing multiple pictures

for file in files:

    try:
        ff = remfits.parse_filearg(file, dbcurs, typef=ftype)
    except remfits.RemFitsErr as e:
        print(file, "open error", e.args[0], file=sys.stderr)
        continue

    data = ff.data
    plotfigure = rg.plt_figure()
    # plotfigure.canvas.manager.set_window_title('FITS Image from file ' + file)

    crange = gsdets.get_cmap(data)
    norm = colors.BoundaryNorm(crange, cmap.N)

    if isinstance(zoomcoords, tuple):
        zcol, zrow = ff.wcs.coords_to_colrow(*zoomcoords)
        set_zoom(ff, zcol, zrow)
        # ax = plt.gca()
        # xx = ax.get_xlim()
        # yy = ax.get_ylim()
        # print("after xlim {:}-{:} ylim={:}-{:}".format(*xx,*yy))

    img = plt.imshow(data, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
    if griddisp:
        try:
            rg.radecgridplt(ff.wcs, data)
        except AttributeError:
            pass  # Lazy way of testing for WCS coords
    if title is None:
        tit = ff.description
        if ff.filter is not None:
            tit += " (filter " + ff.filter + ")"
        plt.title(tit)
    elif len(title) != 0:
        plt.title(title)

    prefix = miscutils.removesuffix(file)
    if findres is not None and findres != '@':
        prefix = findres
    try:
        tfindres = find_results.load_results_from_file(prefix)
        if tfindres.obsind == ff.from_obsind:
            if isinstance(zoomcoords, str):
                try:
                    fr = tfindres[zoomcoords]
                    set_zoom(ff, fr.col, fr.row)
                except KeyError:
                    pass
            display_findresults(ff, tfindres)
            setfig(plotfigure, prefix, ff, tfindres)
    except find_results.FindResultErr:
        pass

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
