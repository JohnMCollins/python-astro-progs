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
import matplotlib.pyplot as plt
import remgeom
import miscutils
import strreplace
import parsetime
import remdefaults
import remget
import fitsops
import remfits
import mydateutil

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Plot mean or standard deviations of bias files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsetime.parseargs_daterange(parsearg)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--showstd', action='store_true', help='Show standard deviations rather than mean')
parsearg.add_argument('--bins', type=int, default=10, help='Number of histogram bins')
# parsearg.add_argument('--norm', type=str, help='Plot normal curse in specified colour')
parsearg.add_argument('--colourhist', type=str, default='b', help='Historgrapm colour')
parsearg.add_argument('--histalpha', type=float, default=0.75, help='Alpha value for historgram only if plotting norm curve')
parsearg.add_argument('--logscale', action='store_true', help='Show results on log scale')
parsearg.add_argument('--xlog', action='store_true', help='Display X axis on log scale')

rg.disp_argparse(parsearg)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
showstd = resargs['showstd']
bins = resargs['bins']
histalpha = resargs['histalpha']
colourhist = resargs['colourhist']
# normplot = resargs['norm']
# if normplot is None: histalpha = 1.0
histalpha = 1.0
logscale = resargs['logscale']
xlog = resargs['xlog']

outfig = rg.disp_getargs(resargs)

fieldselect = []
parsetime.getargs_daterange(resargs, fieldselect)
fieldselect.append("ind!=0")
fieldselect.append("rejreason IS NULL")
fieldselect.append("gain=1")
fieldselect.append("typ='bias'")

dbase, curs = remdefaults.opendb()

curs.execute("SELECT filter,mean,std FROM iforbinf WHERE " + " AND ".join(fieldselect))
dbrows = curs.fetchall()

dbyfilt = dict(g=[], i=[], r=[], z=[])

for filter, mn, st in dbrows:
    dbyfilt[filter].append((mn, st))

plotfigure = rg.plt_figure()
plotfigure.canvas.set_window_title("BIAS file differences")

for filter, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    fres = np.array(dbyfilt[filter])
    if showstd:
        disp = fres[:, 1]
        lab = "Standard deviations"
    else:
        disp = fres[:, 0]
        lab = "Mean values"
    ax = plt.subplot(subp)
    if xlog:
        plt.xscale('log')
    plt.hist(disp, bins=bins, color=colourhist, alpha=histalpha, log=logscale)
    plt.legend([filter + " filter"])
#     if normplot is not None:
#         medv = np.median(disp)
#         stdv = disp.std()
#         rv = norm(loc=medv, scale=stdv)
#         xd = np.linspace(disp.min(), disp.max(), 200)
#         yd = rv.pdf(xd) * float(disp.size)
#         plt.plot(xd, yd, color=normplot)
    plt.xlabel(lab)

plt.tight_layout()

if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)
