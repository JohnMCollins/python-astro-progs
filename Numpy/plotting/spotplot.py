#! /usr/bin/env python

# Plotting of map taken from http://www.geophysique.be/2011/02/20/matplotlib-basemap-tutorial-09-drawing-circles/
# Note that installation of basemap is needed.

import os
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np
import argparse
import sys

def shoot(lon, lat, azimuth, maxdist=None):
    """Shooter Function
    Original javascript on http://williams.best.vwh.net/gccalc.htm
    Translated to python by Thomas Lecocq
    """
    glat1 = lat * np.pi / 180.
    glon1 = lon * np.pi / 180.
    s = maxdist / 1.852
    faz = azimuth * np.pi / 180.

    EPS= 0.00000000005
    if ((np.abs(np.cos(glat1))<EPS) and not (np.abs(np.sin(faz))<EPS)):
        alert("Only N-S courses are meaningful, starting at a pole!")

    a=6378.13/1.852
    f=1/298.257223563
    r = 1 - f
    tu = r * np.tan(glat1)
    sf = np.sin(faz)
    cf = np.cos(faz)
    if (cf==0):
        b=0.
    else:
        b=2. * np.arctan2 (tu, cf)

    cu = 1. / np.sqrt(1 + tu * tu)
    su = tu * cu
    sa = cu * sf
    c2a = 1 - sa * sa
    x = 1. + np.sqrt(1. + c2a * (1. / (r * r) - 1.))
    x = (x - 2.) / x
    c = 1. - x
    c = (x * x / 4. + 1.) / c
    d = (0.375 * x * x - 1.) * x
    tu = s / (r * a * c)
    y = tu
    c = y + 1
    while (np.abs (y - c) > EPS):

        sy = np.sin(y)
        cy = np.cos(y)
        cz = np.cos(b + y)
        e = 2. * cz * cz - 1.
        c = y
        x = e * cy
        y = e + e - 1.
        y = (((sy * sy * 4. - 3.) * y * cz * d / 6. + x) *
              d / 4. - cz) * sy * d + tu

    b = cu * cy * cf - su * sy
    c = r * np.sqrt(sa * sa + b * b)
    d = su * cy + cu * sy * cf
    glat2 = (np.arctan2(d, c) + np.pi) % (2*np.pi) - np.pi
    c = cu * cy - su * sy * cf
    x = np.arctan2(sy * sf, c)
    c = ((-3. * c2a + 4.) * f + 4.) * c2a * f / 16.
    d = ((e * cy * c + cz) * sy * c + y) * sa
    glon2 = ((glon1 + x - (1. - c) * d * f + np.pi) % (2*np.pi)) - np.pi

    baz = (np.arctan2(sa, b) + np.pi) % (2 * np.pi)

    glon2 *= 180./np.pi
    glat2 *= 180./np.pi
    baz *= 180./np.pi

    return (glon2, glat2, baz)

def equi(m, centerlon, centerlat, radius, *args, **kwargs):
    glon1 = centerlon
    glat1 = centerlat
    X = []
    Y = []
    for azimuth in range(0, 360):
        glon2, glat2, baz = shoot(glon1, glat1, azimuth, radius)
        X.append(glon2)
        Y.append(glat2)
    X.append(X[0])
    Y.append(Y[0])

    #~ m.plot(X,Y,**kwargs) #Should work, but doesn't...
    X,Y = m(X,Y)
    plt.plot(X,Y,**kwargs)

parsearg = argparse.ArgumentParser(description='Display plage file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('plagefile', help='Plage file to display', nargs=1)
parsearg.add_argument('--outfile', type=str, help='Output file')
parsearg.add_argument('--width', type=float, help='Width of figure', default=9.0)
parsearg.add_argument('--height', type=float, help='Height of figure', default=2.95)
parsearg.add_argument('--latint', type=float, help='Latitude grid interval (0 to omit)', default=45.0)
parsearg.add_argument('--longint', type=float, help='Longitude grid interval (0 to omit', default=45.0)
parsearg.add_argument('--fillint', type=float, help='Interval for filling (0 to not fill)', default=10.0)
parsearg.add_argument('--forkoff', action='store_true', help='Fork off process to display results')

resargs = vars(parsearg.parse_args())

inpfile = resargs['plagefile'][0]
outfile = resargs['outfile']
width = resargs['width']
height = resargs['height']
latint = resargs['latint']
longint = resargs['longint']
fillint = resargs['fillint']

try:
	plgf = np.loadtxt(inpfile)
except IOError as e:
	print "Cannot open plage file", inpfile, "error was", e.args[1]
	sys.exit(10)

if outfile is not None or (resargs['forkoff'] and os.fork() != 0):
    sys.exit(0)

fig = plt.figure(figsize=(width,height))
plt.subplots_adjust(left=0,right=1,top=1,bottom=0,wspace=0,hspace=0)
ax = plt.subplot(111)
m = Basemap(resolution='l',projection='cea',lon_0=0)
if latint != 0.0: m.drawparallels(np.arange(-90.,90.,latint))
if longint != 0.0: m.drawmeridians(np.arange(0.,360.,longint))
m.drawmapboundary(fill_color='white')
scale = 6 * np.pi * height

if len(plgf.shape) == 1:
	plgf = plgf.reshape(1,5)
for plg in plgf:
	long, lat, sz, stype, shp = plg
	col = 'black'
	if stype < 0.5: col = 'red'
	elif stype > 1.5: col = 'blue'
	if fillint == 0.0:
		equi(m, long, lat, scale*sz, lw=2., color=col)
	else:
		for f in np.arange(0, scale*sz, fillint):
			equi(m, long, lat, f, lw=2., color=col)
if outfile is not None:
	try:
		plt.savefig(outfile)
	except IOError as e:
		print "Cannot save output file", outfile, "error was", e.args[1]
try:
	plt.show()
except KeyboardInterrupt:
	pass

