#! /usr/bin/env python3

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import numpy as np
import remdefaults
import remgeom
import argparse
import miscutils

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Show used areas on CCD for visible filters', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
rg.disp_argparse(parsearg, fmt='single"')

resargs = vars(parsearg.parse_args())
ofig = rg.disp_getargs(resargs)

pltfig = rg.plt_figure()
ax = pltfig.gca()
plt.xlim(0, 2048)
plt.ylim(0, 2048)
plt.tight_layout()

colours = [ 'red', 'yellow', 'cyan']

for rgeom in remdefaults.regeom_config:
    patchlist = []
    colour = colours.pop(0)
    for geom in rgeom.values():
        startx, starty, cols, rows = geom
        rect = Rectangle((startx, starty), width=cols, height=rows)
        patchlist.append(rect)

    pc = PatchCollection(patchlist, facecolor=colour, alpha=0.25, edgecolor='k')
    ax.add_collection(pc)

plt.title("Areas of CCD used at various times")
plt.text(500, 512, "z filter (LL)")
plt.text(500, 512 + 1024, "i filter (UL)")
plt.text(500 + 1024, 512, "r filter (LR)")
plt.text(500 + 1024, 512 + 1034, "g filter (UR)")
if ofig is None:
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    plt.gcf().savefig(ofig)
