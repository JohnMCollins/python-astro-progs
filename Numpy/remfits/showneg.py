#!  /usr/bin/env python3

# Get object data and maintain XML Database

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
from scipy.stats import norm
import datetime
import numpy as np
import argparse
import warnings
import sys
import trimarrays
import matplotlib.pyplot as plt
from matplotlib import colors
from astropy.modeling.tests.test_projections import pars
from bokeh.themes import default
from _pylief import parse
import remgeom
import miscutils
import strreplace

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Show where image - bias files are negative', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs=2, help='image file and bias file')
parsearg.add_argument('--trim', type=str, help='rows:cols trim to')
parsearg.add_argument('--ffref', type=str, help='Flat file for reference')
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with median')
parsearg.add_argument('--divff', action='store_true', help='Divide by flat field')
parsearg.add_argument('--extreme', type=float, default=0.5, help='Amount negative to display as extreme')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
ffile, bfile = resargs['files']
ffref = resargs['ffref']
rc = resargs['trim']
replstd = resargs['replstd']
outfig = rg.disp_getargs(resargs)
divff = resargs['divff']
extreme = resargs['extreme']
if extreme >= 1.0 or extreme < 0.0:
    print("extreme should be 0 to 1 not", extreme, file=sys.stderr)
    sys.exit(12)

if ffref is not None:
    ffreff = fits.open(ffref)
    ffrefim = trimarrays.trimzeros(trimarrays.trimnan(ffreff[0].data))
    ffreff.close()
    rows, cols = ffrefim.shape
elif rc is not None:
    try:
        rows, cols = map(lambda x: int(x), rc.split(':'))
    except ValueError:
        print("Unexpected --trim arg", rc, "expected rows:cols", file=sys.stderr)
        sys.exit(10)
    if divff:
        print("Sorry cannot specify --divff if just rows:cols given", file=sys.stderr)
        sys.exit(15)
else:
    print("No reference flat file or trim arg given", file=sys.stderr)
    sys.exit(11)

ff = fits.open(ffile)
bf = fits.open(bfile)
fim = ff[0].data.astype(np.float32)
bim = bf[0].data.astype(np.float32)
ff.close()
bf.close()
fim, bim = trimarrays.trimrc(rows, cols, fim, bim)

if replstd > 0.0:
    bim = strreplace.strreplace(bim, replstd)

diffs = fim - bim
if divff:
	diffs /= ffrefim
sdiffs = diffs.copy()
extval = sdiffs.min() * extreme
print("Extreme", np.count_nonzero(sdiffs < 0), "neg", np.count_nonzero(sdiffs == 0), "pos", np.count_nonzero(sdiffs > 0))
plotfigure = rg.plt_figure()
plotfigure.canvas.set_window_title("Negatives after bias sub")
crange = [sdiffs.min(), extval, 0.0, -extval, sdiffs.max()]
cmap = colors.ListedColormap(['#ff0000', '#0000ff', '#00ff00', '#ffffff'])
norm = colors.BoundaryNorm(crange, 4, clip=True)
img = plt.imshow(sdiffs, cmap=cmap, norm=norm, origin='lower')
plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)
