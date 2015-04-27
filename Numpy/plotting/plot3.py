#! /usr/bin/env python

# Generalised 3D plotting thing

import sys
import argparse
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# Colour maps

cmapd = dict(coolwarm = plt.cm.coolwarm,
             hot = plt.cm.hot,
             cool = plt.cm.cool,
             spring = plt.cm.spring,
             summer = plt.cm.summer,
             autumn = plt.cm.autumn,
             winter = plt.cm.winter)

parsearg = argparse.ArgumentParser(description='Display of 3-D data file')
parsearg.add_argument('input', type=str, nargs=1, help='Input file (numpy 3D array of X,Y,Z)')
parsearg.add_argument('--width', type=float, default=8, help='Display width')
parsearg.add_argument('--height', type=float, default=6, help='Display height')
parsearg.add_argument('--wirecolour', type=str, help='Specify display as wireframe of given colour')
parsearg.add_argument('--contourcolour', type=str, default="coolwarm", help='Style of contour when displaying thus')
parsearg.add_argument('--xlabel', type=str, help='Label for X axis')
parsearg.add_argument('--ylabel', type=str, help='Label for Y axis')
parsearg.add_argument('--zlabel', type=str, help='Label for Z axis')
parsearg.add_argument('--rstride', type=int, default=1, help='Row stride')
parsearg.add_argument('--cstride', type=int, default=1, help='Column stride')

resargs = vars(parsearg.parse_args())

inputfile = resargs['input'][0]

try:
    inarray = np.load(inputfile)
except IOError as e:
    if e.arg[0] == 2:
        try:
            inarray = np.load(inputfile + '.npy')
        except IOError as e:
            print "Cannot open", inputfile, "(with suffix)"
            sys.exit(2)
    print "Cannot open", inputfile, "error was", e.arg[1]
    sys.exit(1)

sa = inarray.shape
if len(sa) != 3:
    print "Expecting 3-d array for", inputfile, "not", sa
    sys.exit(2)

if sa[0] != 3:
    print "Expecting 3 rows for", inputfile, "not", sa[0]
    sys.exit(3)

X, Y, Z = inarray

wc = resargs['wirecolour']

if wc is None:
    try:
        cmapv = cmapd[resargs['contourcolour']]
    except KeyError:
        print "Unknown colour map", resargs['contourcolour']
        sys.exit(4)   

fig = plt.figure(figsize=(resargs['width'],resargs['height']))
ax = Axes3D(fig)

rstride = resargs['rstride']
cstride = resargs['cstride']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
zlab = resargs['zlabel']

if wc is None:
    ax.plot_surface(X, Y, Z, rstride=rstride, cstride=cstride, cmap=cmapv)
else:
    ax.plot_wireframe(X, Y, Z, rstride=rstride, cstride=cstride, color=wc)
if xlab is not None: ax.set_xlabel(xlab)
if ylab is not None: ax.set_ylabel(ylab)
if zlab is not None: ax.set_zlabel(zlab)
plt.show()
