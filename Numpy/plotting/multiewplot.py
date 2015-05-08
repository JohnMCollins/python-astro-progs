#! /usr/bin/env python

# Multiple display of EWs and plots of EWs for separate dates

import argparse
import os.path
import sys
import string
import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
import exclusions
import jdate
import rangearg

# According to type of display select column, xlabel  for hist, ylabel for plot

parsearg = argparse.ArgumentParser(description='Plot comparative equivalent width results')
parsearg.add_argument('integ', type=str, nargs='+', help='Input integration file (time/intensity)')
parsearg.add_argument('--title', type=str, default='Equivalent widths', help='Title for window')
parsearg.add_argument('--bins', type=int, default=20, help='Histogram bins')
parsearg.add_argument('--clip', type=float, default=0.0, help='Number of S.D.s to clip from histogram')
parsearg.add_argument('--gauss', action='store_true', help='Normalise and overlay gaussian on histogram')
parsearg.add_argument('--yhist', type=str, default='Occurrences', help='Label for histogram Y axis')
parsearg.add_argument('--xhist', type=str, help='Label for histogram X axis', default='Equivalent width ($\AA$)')
parsearg.add_argument('--yplot', type=str, help='Label for plot Y axis')
parsearg.add_argument('--xplot', type=str, default='From start', help='Label for plot X axis')
parsearg.add_argument('--yaxr', action='store_true', help='Put Y axis label on right')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--yrange', type=str, help='Range for Y axis')
parsearg.add_argument('--histxrange', type=str, help='Range for Hist X axis')
parsearg.add_argument('--histyrange', type=str, help='Range for Hist Y axis')
parsearg.add_argument('--xaxt', action='store_true', help='Put X axis label on top')
parsearg.add_argument('--width', type=float, default=8, help='Display width')
parsearg.add_argument('--height', type=float, default=6, help='Display height')
parsearg.add_argument('--outprefix', type=str, help='Output file prefix')
parsearg.add_argument('--plotcolours', type=str, default='black,red,green,blue,yellow,magenta,cyan', help='Colours for successive plots')
parsearg.add_argument('--legend', type=str, help='Specify explicit legend as comma-separated list')
parsearg.add_argument('--fork', action='store_true', help='Fork off daemon process to show plot and exit')

res = vars(parsearg.parse_args())
rfiles = res['integ']
title = res['title']
outf = res['outprefix']
clip = res['clip']
gauss = res['gauss']
bins = res['bins']
ytr = res['yaxr']
xtt = res['xaxt']
histxlab = res['xhist']
histylab = res['yhist']
if histylab == "none":
    histylab = ""
xlab = res['xplot']
if xlab == "none":
    xlab = ""
ylab = res['yplot']
if ylab == "none":
    ylab = ""

yrange = rangearg.parserange(res['yrange'])
xrange = rangearg.parserange(res['xrange'])
histyrange = rangearg.parserange(res['histyrange'])
histxrange = rangearg.parserange(res['histxrange'])
forkoff = res['fork']
explicit_legend = res['legend']

dims = (res['width'], res['height'])


inp = np.loadtxt(rf, unpack=True)
dates = inp[0]
vals = inp[1]

fig = plt.figure(figsize=dims)
fig.canvas.set_window_title(title + ' Histogram')

# If clipping histogram, iterate to remove outliers

if clip != 0.0:
    hvals = vals + 0.0
    lh = len(hvals)
    while 1:
        mv = np.mean(hvals)
        std = np.std(hvals)
        sel = np.abs(hvals - mv) <= clip * std
        hvals = hvals[sel]
        nl = len(hvals)
        if nl == 0:
            print "No values left after clip???"
            sys.exit(101)
        if nl == lh:
            break
        lh = nl
    if gauss:
        mv = np.mean(hvals)
        std = np.std(hvals)
        minv = np.min(hvals)
        maxv = np.max(hvals)
        lx = np.linspace(minv,maxv,250)
        garr = ss.norm.pdf(lx, mv, std)
        if histyrange is not None:
            plt.ylim(*histyrange)
        if histxrange is not None:
            plt.xlim(*histxrange)
        plt.hist(hvals, bins=bins, normed = True)
        plt.plot(lx, garr, color='red')
    else:
        if histyrange is not None:
            plt.ylim(*histyrange)
        if histxrange is not None:
            plt.xlim(*histxrange)
        plt.hist(hvals,bins=bins)
else:
    if histyrange is not None:
        plt.ylim(*histyrange)
    if histxrange is not None:
        plt.xlim(*histxrange)
    if gauss:
        mv = np.mean(vals)
        std = np.std(vals)
        minv = np.min(vals)
        maxv = np.max(vals)
        lx = np.linspace(minv, maxv, 250)
        garr = ss.norm.pdf(lx, mv, std)
        plt.hist(vals, bins=bins, normed = True)
        plt.plot(lx, garr, color='red')
    else:
        plt.hist(vals,bins=bins)
if ytr:
    plt.gca().yaxis.tick_right()
    plt.gca().yaxis.set_label_position("right")
if xtt:
    plt.gca().xaxis.tick_top()
    plt.gca().xaxis.set_label_position("top")
if len(histylab) > 0:
    plt.ylabel(histylab)
else:
    plt.yticks([])
if len(histxlab) > 0:
    plt.xlabel(histxlab)
else:
    plt.xticks([])
if explicit_legend is not None:
    plt.legend([explicit_legend], handlelength=0)
if outf is not None:
    fname = outf + '_hist.png'
    plt.savefig(fname)
if not sdp:
    fig = plt.figure(figsize=dims)
    fig.canvas.set_window_title(title + ' Value by time')
 
rxarray = []
ryarray = []
rxvalues = []
ryvalues = []

lastdate = 1e12

for d, v in zip(dates,vals):
    if d - lastdate > sepdays and len(rxvalues) != 0:
        rxarray.append(rxvalues)
        ryarray.append(ryvalues)
        rxvalues = []
        ryvalues = []
    rxvalues.append(d)
    ryvalues.append(v)
    lastdate = d

if len(rxvalues) != 0:
   rxarray.append(rxvalues)
   ryarray.append(ryvalues)

plotcols = string.split(res['plotcolours'], ',')
colours = plotcols * ((len(rxarray) + len(plotcols) - 1) / len(plotcols))

fnum = 1

if sdp:
    for xarr, yarr, col in zip(rxarray,ryarray,colours):
        offs = xarr[0]
        xa = np.array(xarr) - offs
        ya = np.array(yarr)
        f = plt.figure(figsize=dims)
        f.canvas.set_window_title(title + ' Day ' + str(fnum))
        if xrange is not None:
            plt.xlim(*xrange)
        if yrange is not None:
            plt.ylim(*yrange)
        if len(plotylab) == 0:
            plt.yticks([])
        else:
            if ytr:
                plt.gca().yaxis.tick_right()
                plt.gca().yaxis.set_label_position("right")
            plt.ylabel(plotylab)
        if len(xlab) == 0:
            plt.xticks([])
        else:
            if xtt:
                plt.gca().xaxis.tick_top()
                plt.gca().xaxis.set_label_position('top')
            plt.xlabel(xlab)
        plt.plot(xa,ya,col,label=jdate.display(xarr[0]))
        if excludes is not None:
            sube = elist.inrange(np.min(xarr), np.max(xarr))
            had = dict()
            for pl in sube.places():
                xpl = pl - offs
                reas = sube.getreason(pl)
                creas = rlookup[reas]
                if reas in had:
                    plt.axvline(xpl, color=creas, ls="--")
                else:
                    had[reas] = 1
                    plt.axvline(xpl, color=creas, label=reas, ls="--")
        if explicit_legend is not None:
            plt.legend([explicit_legend] + " (%d)" % fnum, handlelength=0)
        if outf is not None:
            fname = outf + ("_f%.3d.png" % fnum)
            f.savefig(fname)
        fnum += 1
else:
    lines = []
    if yrange is not None:
        plt.ylim(*yrange)
    if len(plotylab) == 0:
        plt.yticks([])
    else:
        if ytr:
            plt.gca().yaxis.tick_right()
            plt.gca().yaxis.set_label_position("right")
        plt.ylabel(plotylab)
    if len(xlab) == 0:
        plt.xticks([])
    else:
        if xtt:
            plt.gca().xaxis.tick_top()
            plt.gca().xaxis.set_label_position('top')
        plt.xlabel(xlab)
    
    for xarr, yarr, col in zip(rxarray,ryarray,colours):
        offs = xarr[0]
        xa = np.array(xarr) - offs
        ya = np.array(yarr)
        plt.plot(xa,ya, col)
        if excludes is not None:
            sube = elist.inrange(np.min(xarr), np.max(xarr))
            for pl in sube.places():
                xpl = pl - offs
                reas = sube.getreason(pl)
                creas = rlookup[reas]
                lines.append((xpl,creas))
    
    if explicit_legend is not None:
        plt.legend([explicit_legend], handlelength=0)

    for xpl, creas in lines:
        plt.axvline(xpl, color=creas, ls="--")
    if outf is not None:
        fname = outf + "_f.png"
        plt.savefig(fname)
        sys.exit(0)

# Only display pic if we're not saving

if forkoff:
    if os.fork() == 0:
        plt.show()
else:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
sys.exit(0)
