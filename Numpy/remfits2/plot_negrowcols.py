#!  /usr/bin/env python3

import dbops
import remdefaults
import argparse
import sys
import os.path
import miscutils
import numpy as np
import remfits
import remdefaults
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remgeom
import matplotlib.pyplot as plt

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Display selected row or column in obs and bias', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
rg.disp_argparse(parsearg)
parsearg.add_argument('files', type=str, nargs='+', help='Files to find zero rows/columns in')
parsearg.add_argument('--biasfile', type=str, required=True, help='Bias file to use')
parsearg.add_argument('--column', type=int, help='Column to select')
parsearg.add_argument('--row', type=int, help='Row to select')
parsearg.add_argument('--plotcolours', type=str, default='b,r,g', help='Comma separated colour list for plots of obs files')
parsearg.add_argument('--alphas', type=str, default="0.75", help='List of alpha values, comma separated for plots of obs files')
parsearg.add_argument('--biascolour', type=str, default='k', help='Colour for bias file')
parsearg.add_argument('--biasalpha', type=float, default=0.75, help='Alpha for bias plot')
parsearg.add_argument('--flats', action='store_true', help='Take files as flat files')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['files']
biasfile = resargs['biasfile']
column = resargs['column']
row = resargs['row']
if row is None and column is None:
    print("Must specify --row or --coloumn", file=sys.stderr)
    sys.exit(10)
if row is not None and column is not None:
    print("Cannot specify both --row and --coloumn", file=sys.stderr)
    sys.exit(11)
plotcolours = resargs['plotcolours'].split(',') * len(files)
alphas = [float(x) for x in resargs['alphas'].split(',')] * len(files)
biascolour = resargs['biascolour']
biasalpha = resargs['biasalpha']
ftype = None
if resargs['flats']:
    ftype = 'F'

figout = rg.disp_getargs(resargs)

mydb, mycurs = remdefaults.opendb()

try:
    bf = remfits.parse_filearg(biasfile, mycurs, 'B')
except remfits.RemFitsErr as e:
    print("Biasfile", biasfile, "error", e.args[0], file=sys.stderr)
    sys.exit(10)

bdims = bf.dimscr()
bdata = bf.data

plotfigure = rg.plt_figure()
if row is None:
    plt.plot(bdata[:, column], color=biascolour, alpha=biasalpha)
    plt.xlabel("Row number")
else:
    plt.plot(bdata[row], color=biascolour, alpha=biasalpha)
    plt.xlabel("Column number")

plt.ylabel("ADU counts")

legs = ['Bias']

for file in files:

    currcolour = plotcolours.pop(0)
    curralpha = alphas.pop(0)

    try:
        ff = remfits.parse_filearg(file, mycurs, ftype)
    except remfits.RemFitsErr as e:
        print("Could not open", file, "error", e.args[0], file=sys.stderr)
        continue

    if ff.dimscr() != bdims:
        print("Dimensions of", file, "does not match bias", file=sys.stderr)
        continue

    fdat = ff.data

    if row is None:
        plt.plot(fdat[:, column], color=currcolour, alpha=curralpha)
    else:
        plt.plot(fdat[row], color=currcolour, alpha=curralpha)

    descr = ff.date.strftime(ff.filter + " filt at %Y-%m-%d %H:%M:%S")
    legs.append(descr)

plt.legend(legs)

if figout is None:
    plt.show()
else:
    figout = miscutils.replacesuffix(figout, ".png")
    plotfigure.savefig(figout)
    plt.close(plotfigure)
