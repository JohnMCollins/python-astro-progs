#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-23T14:20:00+01:00
# @Email:  jmc@toad.me.uk
# @Filename: dbobjdisp.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:02:43+00:00

import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib import colors
import argparse
import sys
import miscutils
import remdefaults
import remgeom

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display extreme mean or std', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, database=False)
parsearg.add_argument('file', type=str, nargs=1, help='Maan/std file to display')
parsearg.add_argument('--nscales', type=int, default=10, help='Number of grey scales')
parsearg.add_argument('--meanorstd', type=str, choices=['M', 'S', 'L', 'H'], default='M', help='Select mean, std, min, max')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

file = remdefaults.meanstd_file(resargs['file'][0])
nscales = resargs['nscales']
meanorstd = resargs['meanorstd']
figout = rg.disp_getargs(resargs)

try:
    msfile = np.load(file)
except OSError as e:
    print("Could not open", file, "error was", e.args[1])
    sys.exit(10)
except ValueError:
    print(file, "exists but does not appear to be numpy file", file=sys.stderr)
    sys.exit(11)

if msfile.shape != (5, 2048, 2048):
    print("Shape in file", file, "is", msfile.shape, "not 5x2048x2048 as expected", file=sys.stderr)
    sys.exit(12)

plotfigure = rg.plt_figure()
plotfigure.canvas.set_window_title('Extreme mean/std counts from ' + file)
wplane = dict(M=1, S=2, L=3, H=4)
values = msfile[wplane[meanorstd]]
counts = msfile[0]

fvalues = values.flatten()
fcounts = counts.flatten()
fvalues = fvalues[fcounts > 0]
meanv = fvalues.mean()
stdv = fvalues.std()

crange = list(np.linspace(fvalues.min(), fvalues.max(), nscales))
if fvalues.min() > 0:
    crange = [0.0] + crange
cmap = colors.ListedColormap(["#%.2x%.2x%.2x" % (i, i, i) for i in np.linspace(255, 0, len(crange) - 1).round().astype(np.int32)])
norm = colors.BoundaryNorm(crange, cmap.N)
img = plt.imshow(values, cmap=cmap, norm=norm, origin='lower')
plt.colorbar(img, boundaries=crange, ticks=crange)
plt.xlabel("Column number")
plt.ylabel("Row number")
if figout is not None:
    outfile = miscutils.addsuffix(figout, ".png")
    plotfigure.savefig(outfile)
    plt.close(plotfigure)
else:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
