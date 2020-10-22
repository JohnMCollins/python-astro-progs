#!  /usr/bin/env python3

# Get object data and maintain XML Database

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
from scipy.stats import norm
from numpy.random import uniform
import datetime
import numpy as np
import argparse
import warnings
import sys
import trimarrays
import matplotlib.pyplot as plt
from matplotlib import colors
import remgeom
import miscutils
import re
import remdefaults
import dbops

filtfn = dict(BL='z', BR="r", UR="g", UL="i")
fmtch = re.compile('([FBIm]).*([UB][LR])')

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()

mydbname = remdefaults.default_database()
parsearg = argparse.ArgumentParser(description='Classify bias file pixels by std devs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='List of files to select grom')
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--wtitle', type=str, default='Invalid pixelss in image collection', help='Title for overall')
parsearg.add_argument('--title', type=str, default='Pixels classified by std deviation', help='Label for pixel map')
parsearg.add_argument('--greyscale', type=str, required=True, help="Standard greyscale to use")
parsearg.add_argument('--histbins', type=int, default=20, help='Bins for histogram')
parsearg.add_argument('--logscale', action='store_false', help='Use log scale for histogram')
parsearg.add_argument('--colourhist', type=str, default='b', help='Colour of historgram')
parsearg.add_argument('--histtitle', type=str, default='Distribution of std deviations', help='Histogram Title')
parsearg.add_argument('--histxlab', type=str, default='Pixel value normalised to mean', help='Label for histogram X axis')
parsearg.add_argument('--histylab', type=str, default='Occurences of vaalue', help='Label for histogram Y axis')
parsearg.add_argument('--percent', type=float, default=.25, help='Percentage of files to select')
# parsearg.add_argument('--above', type=float, default=0.0, help='Only show points with meanv values this number of overall stds devs above this')

rg.disp_argparse(parsearg, "dwin")
resargs = vars(parsearg.parse_args())

mydbname = resargs['database']

files = resargs['files']
wtitle = resargs['wtitle']
title = resargs['title']
histbins = resargs['histbins']
colourhist = resargs['colourhist']
histxlab = resargs['histxlab']
histylab = resargs['histylab']
histtitle = resargs['histtitle']
logscale = resargs['logscale']
# abovev = resargs['above']
greyscalename = resargs['greyscale']
percentsel = resargs['percent']
outfig = rg.disp_getargs(resargs)

gsdets = rg.get_greyscale(greyscalename)
if gsdets is None:
    print("Sorry grey scale", greyscalename, "is not defined", file=sys.stderr)
    sys.exit(9)

collist = gsdets.get_colours()
cmap = colors.ListedColormap(collist)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

filesdone = dict()
ndone = 0

filter = None

selection = uniform(size=len(files)) > percentsel
nf = -1

for file in files:

    nf += 1
    if selection[nf]: continue

    try:
        ff = fits.open(file)
    except OSError as e:
        print("Cannot open", file, e.strerror, file=sys.stderr)
        continue

    fhdr = ff[0].header
    fdat = ff[0].data
    ff.close()

    try:
        filename = fhdr['FILENAME']
    except KeyError:
        print("No file name in", file, file=sys.stderr)
        continue

    if filename in filesdone:
        print("Already done", filename, "in", file, file=sys.stderr)
        continue

    filesdone[filename] = 1
    mf = fmtch.match(filename)
    if mf is None:
        print("Cannot match filename", filename, "in", file, file=sys.stderr)
        continue

    ft, quad = mf.groups()
    if ft != 'B':
        print(file, "filename", filename, "does not look like daily bias file")
        continue

    ffilt = filtfn[quad]
    if filter is None:
        filter = ffilt
        qfilt = dbase.escape(filter)
        dbcurs.execute("SELECT MIN(nrows),MIN(ncols) FROM iforbinf WHERE nrows IS NOT NULL AND filter=" + qfilt)
        rows = dbcurs.fetchall()
        rdim, coldim = rows[0]
        fdat = fdat[0:rdim, 0:coldim]
        pending = fdat.reshape(1, rdim, coldim)
    elif ffilt != filter:
        print(file, "filename", filename, "has wrong filter type", ffilt, "previous was", filter, file=sys.stderr)
        continue
    else:
        fdat = fdat[0:rdim, 0:coldim].reshape(1, rdim, coldim)
        pending = np.concatenate((pending, fdat), axis=0)

    ndone += 1

if ndone == 0:
    print("No files to process", file=sys.stderr)
    sys.exit(1)

# Now do sums

sdevs = pending.std(axis=0)
# if abovev > 0.0:
#     overall_mean = pending.mean()
#     overall_std = pending.std()
#     cutoff = overall_mean + abovev * overall_std
#     sdevs[pending.mean(axis=0) < cutoff] = 0

plotfigure = rg.plt_figure()
plotfigure.canvas.set_window_title(wtitle)
plt.subplot(121)
crange = gsdets.get_cmap(sdevs)
norm = colors.BoundaryNorm(crange, cmap.N)
img = plt.imshow(sdevs, cmap=cmap, norm=norm, origin='lower')
plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
plt.title(title + "\nFor filter " + filter)
plt.subplot(122)
plt.hist(sdevs.flatten(), bins=histbins, color=colourhist, log=logscale)
plt.xlabel(histxlab)
plt.ylabel(histylab)
plt.title(histtitle)
plt.tight_layout()

if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)
