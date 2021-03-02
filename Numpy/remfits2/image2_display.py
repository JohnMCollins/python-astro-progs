#! /usr/bin/env python3

"""Display a pair of images side by side"""

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

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display 2 image files side by side', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('files', type=str, nargs=2, help='File names/IDs to display')
parsearg.add_argument('--greyscale', type=str, help="Standard greyscale to use")
parsearg.add_argument('--type', type=str, help='Put F or B here to select daily flat or bias for numerics')

figout = rg.disp_argparse(parsearg, "dwin")

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
typef = resargs['type']

files = resargs['files']
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

errors = 0

fpair = []

for file in files:

    try:
        ff = remfits.parse_filearg(file, dbcurs, typef=typef)
    except remfits.RemFitsErr as e:
        print("Open of", file, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    fpair.append(ff)

if errors > 0:
    print("Stopping due to errors", file=sys.stderr)
    sys.exit(20)

plotfigure = rg.plt_figure()
plotfigure.canvas.set_window_title("Composite 2 images")

for ff, subp in zip(fpair, (121, 122)):

    data = ff.data
    crange = gsdets.get_cmap(data)
    norm = colors.BoundaryNorm(crange, cmap.N)
    plt.subplot(subp)
    img = plt.imshow(data, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
    plt.xlabel(ff.description)

plt.tight_layout()
if figout is None:
    plt.show()
else:
    figout = miscutils.replacesuffix(figout, ".png")
    plotfigure.savefig(figout)
    plt.close(plotfigure)
