#! /usr/bin/env python3

"""Display a block of 4 images"""

import argparse
import sys
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import astroquery.utils as autils
import matplotlib.pyplot as plt
from matplotlib import colors
import miscutils
import remdefaults
import remgeom
import remfits
import col_from_file

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display 4 image files for different filters', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('files', type=str, nargs='*', help='File names/IDs to display otherwise use id/file list from standard input')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--greyscale', type=str, help="Standard greyscale to use")
parsearg.add_argument('--type', type=str, help='Put F or B here to select daily flat or bias for numerics')

figout = rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
typef = resargs['type']

files = resargs['files']
if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

if len(files) != 4:
    print("Expecting 4 argument files not", ", ".join(files), file=sys.stderr)
    sys.exit(10)

figout = rg.disp_getargs(resargs)
greyscalename = resargs['greyscale']
if greyscalename is None:
    greyscalename = rg.defgreyscale
    if greyscalename is None:
        print("No greyscale given, use --greyscale or set default one", file=sys.stderr)
        sys.exit(0)

gsdets = rg.get_greyscale(greyscalename)
if gsdets is None:
    print("Sorry grey scale", greyscalename, "is not defined", file=sys.stderr)
    sys.exit(9)

collist = gsdets.get_colours()
cmap = colors.ListedColormap(collist)

db, dbcurs = remdefaults.opendb()

filterobj = dict(g=None, r=None, i=None, z=None)

# Get details of object once only if doing multiple pictures

errors = 0

for file in files:

    try:
        ff = remfits.parse_filearg(file, dbcurs, typef=typef)
    except remfits.RemFitsErr as e:
        print("Open of", file, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue

    try:
        existf = filterobj[ff.filter]
    except KeyError:
        print("This should be visible light filters griz only not", ff.filter, file=sys.stderr)
        errors += 1
        continue

    if existf is not None:
        print("Need 1 each of griz got two of", ff.filter, file=sys.stderr)
        errors += 1
        continue

    filterobj[ff.filter] = ff

if errors > 0:
    print("Stopping due to errors", file=sys.stderr)
    sys.exit(20)

plotfigure = rg.plt_figure()
plotfigure.canvas.set_window_title("Composite 4 filters")

for filt, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    ff = filterobj[filt]
    data = ff.data
    crange = gsdets.get_cmap(data)
    norm = colors.BoundaryNorm(crange, cmap.N)
    plt.subplot(subp)
    img = plt.imshow(data, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
    plt.xlabel(filt + " filter")

plt.tight_layout()
if figout is None:
    plt.show()
else:
    figout = miscutils.replacesuffix(figout, ".png")
    plotfigure.savefig(figout)
    plt.close(plotfigure)
