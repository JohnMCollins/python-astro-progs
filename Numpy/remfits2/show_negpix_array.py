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

parsearg = argparse.ArgumentParser(description='Display Negative pixel array', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, database=False)
parsearg.add_argument('file', type=str, nargs=1, help='Count file to display')
parsearg.add_argument('--gsnum', type=int, default=10, help='Number of grey scales')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

file = remdefaults.count_file(resargs['file'][0])
gsnum = resargs['gsnum']
figout = rg.disp_getargs(resargs)

try:
    imagedata = np.load(file)
except OSError as e:
    print("Could not open", file, "error was", e.args[1])
    sys.exit(10)
except ValueError:
    print(file, "exists but does not appear to be numpy file", file=sys.stderr)
    sys.exit(11)

if imagedata.shape != (2048, 2048):
    print("Shape in file", file, "is", imagedata.shape, "not 2048x2048 as expected", file=sys.stderr)
    sys.exit(12)
if imagedata.dtype != np.int32 and imagedata.dtype != np.int64:
    print("Expecting file", file, "to be integer type", file=sys.stderr)
    sys.exit(13)

plotfigure = rg.plt_figure()
plotfigure.canvas.set_window_title('Negative pixel counts from ' + file)

cmap = colors.ListedColormap(["#%.2x%.2x%.2x" % (i, i, i) for i in np.linspace(255, 0, gsnum).round().astype(np.int32)])
crange = [0] + list(np.linspace(1, imagedata.max(), gsnum))
norm = colors.BoundaryNorm(crange, cmap.N)
img = plt.imshow(imagedata, cmap=cmap, norm=norm, origin='lower')
plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
plt.xlabel("Column number")
plt.ylabel("Row number")
if figout is not None:
    outfile = miscutils.addsuffix(figout, "png")
    plotfigure.savefig(outfile)
    plt.close(plotfigure)
else:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
