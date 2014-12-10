#! /usr/bin/env python

# Display ratio calculation vs EW

import argparse
import os.path
import sys
import string
import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
import rangearg

parsearg = argparse.ArgumentParser(description='Plot peak ratio vs EW')
parsearg.add_argument('specs', type=str, help='File pairs of ratio by days and EW by days', nargs='+')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)
parsearg.add_argument('--logplot', action='store_true', help='Plot logarithmic')
parsearg.add_argument('--ploty', type=str, default='Ratio of peaks', help='Label for plot Y axis')
parsearg.add_argument('--plotx', type=str, default='Equivalent widths', help='Label for plot X axis')
parsearg.add_argument('--outfile', type=str, help='Output file')
parsearg.add_argument('--plotcolours', type=str, default='black,red,green,blue,yellow,magenta,cyan', help='Colours for successive plots')
parsearg.add_argument('--legpos', type=str, default='best', help='Legend position')
parsearg.add_argument('--xrange', type=str, help='Display range for X values')
parsearg.add_argument('--xupper', type=float, help='Upper limit of range for X values')
parsearg.add_argument('--xlower', type=float, help='Lower limit of range for X values')
parsearg.add_argument('--yrange', type=str, help='Display range for Y values')
parsearg.add_argument('--yupper', type=float, help='Upper limit of range for Y values')
parsearg.add_argument('--ylower', type=float, help='Lower limit of range for Y values')

res = vars(parsearg.parse_args())
flist = res['specs']
outf = res['outfile']

plotcols = string.split(res['plotcolours'], ',')
colours = plotcols * ((len(flist) + len(plotcols) - 1) / len(plotcols))

plots = []
minew = 1e6
maxew = -1e6

limxl,limxu = rangearg.getrangearg(res, rangename="xrange", lowerarg="xlower", upperarg="xupper")
limyl,limyu = rangearg.getrangearg(res, rangename="yrange", lowerarg="ylower", upperarg="yupper")

for p in flist:
    fpair = string.split(p, ',', 2)
    if len(fpair) != 3:
        print "Argument", p, "is not a pair of files and name"
        sys.exit(100)
    
    # Load up equivalent width and ratio data

    ewdata = np.loadtxt(fpair[0], unpack=True)
    ratdata = np.loadtxt(fpair[1], unpack=True)
    name = fpair[2]

    if ewdata.shape[-1] != ratdata.shape[-1]:
        print "Sizes of array don't seem right for arg", p, "ewfile =", ewdata.shape, "ratfile =", ratdata.shape
        sys.exit(101)

    # Sort both by sizes EW

    sortind = np.argsort(ewdata[1])

    ews = ewdata[1][sortind]
    minew = min(minew, np.min(ews))
    maxew = max(maxew, np.max(ews))
    rats = ratdata[1][sortind]
    plots.append((ews, rats, name))

if limxl is not None and limxu is not None and limxl != 0.0 and limxu != 0.0:
    minew = limxl
    maxew = limxu

plt.rcParams['figure.figsize'] = (res['width'], res['height'])

if res['logplot']:
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xscale('log')
    if limyl is not None and limyu is not None and limyl != 0.0 and limyu != 0.0:
        ax.set_ylim(limyl, limyu)
    ax.set_xlim(minew, maxew)
    for ews, rats, name in plots:
        col = colours.pop(0)
        ax.plot(ews, rats, color=col, label=name)
    plt.ylabel(res['ploty'])
    plt.xlabel(res['plotx'])
    plt.legend()
    if outf is not None:
        plt.savefig(outf)
    try:
        plt.show()
    except:
        pass
else:
    if limyl is not None and limyu is not None and limyl != 0.0 and limyu != 0.0:
        plt.ylim(limyl, limyu)
    plt.xlim(minew, maxew)
    for ews, rats, name in plots:
        col = colours.pop(0)
        plt.plot(ews, rats, color=col, label=name)
    plt.ylabel(res['ploty'])
    plt.xlabel(res['plotx'])
    plt.legend()
    if outf is not None:
        plt.savefig(outf)
    try:
        plt.show()
    except:
        pass

