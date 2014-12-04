#! /usr/bin/env python

# Integrate the H alpha peaks to get figures for the total values,
# assume continuum is normalised at 1 unless otherwise specified

import argparse
import os.path
import sys
import string
import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
import exclusions
import jdate

def parserange(arg):
    """Parse a range argument, either a single floating point number, in which case assume other end is zero,
    or a pair. If only a single number add zero. Return a sorted result"""
    
    if arg is None: return None
    
    bits = string.split(arg, ',')
    try:
        if len(bits) == 1:
            ret = [0, float(arg)]
        elif len(bits) == 2:
            ret = map(lambda x: float(x), bits)
        else:
            raise ValueError
    except:
        print "Did not understand range value of", arg
        return None
    
    ret.sort()
    return ret

parsearg = argparse.ArgumentParser(description='Plot equivalent width results')
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--sepdays', type=int, default=10000, help='Separate plots if this number of days apart')
parsearg.add_argument('--bins', type=int, default=20, help='Histogram bins')
parsearg.add_argument('--clip', type=float, default=0.0, help='Number of S.D.s to clip from histogram')
parsearg.add_argument('--gauss', action='store_true', help='Normalise and overlay gaussian on histogram')
parsearg.add_argument('--sdplot', action='store_true', help='Put separate days in separate figure')
parsearg.add_argument('--yhist', type=str, default='Occurrences', help='Label for histogram Y axis')
parsearg.add_argument('--xhist', type=str, default='Equivalent width (Angstroms)', help='Label for histogram X axis')
parsearg.add_argument('--yplot', type=str, default='Equivalent width (Angstroms)', help='Label for plot Y axis')
parsearg.add_argument('--xplot', type=str, default='Days offset from start', help='Label for plot X axis')
parsearg.add_argument('--yaxr', action='store_true', help='Put Y axis label on right')
parsearg.add_argument('--yrange', type=str, help='Range for Y axis')
parsearg.add_argument('--histyrange', type=str, help='Range for Hist Y axis')
parsearg.add_argument('--xaxt', action='store_true', help='Put X axis label on top')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--histxrange', type=str, help='Range for Hist X axis')
parsearg.add_argument('--width', type=float, default=4, help='Display width')
parsearg.add_argument('--height', type=float, default=3, help='Display height')
parsearg.add_argument('--outprefix', type=str, help='Output file prefix')
parsearg.add_argument('--plotcolours', type=str, default='black,red,green,blue,yellow,magenta,cyan', help='Colours for successive plots')
parsearg.add_argument('--excludes', type=str, help='File with excluded obs times and reasons')
parsearg.add_argument('--exclcolours', type=str, default='red,green,blue,yellow,magenta,cyan,black', help='Colours for successive exclude reasons')
parsearg.add_argument('--legpos', type=str, default='best', help='Legend position')
parsearg.add_argument('--legnum', type=int, default=5, help='Number for legend')
parsearg.add_argument('--fork', action='store_true', help='Fork off daemon process to show plot and exit')

res = vars(parsearg.parse_args())
rf = res['integ'][0]
sepdays = res['sepdays']
sdp = res['sdplot']
outf = res['outprefix']
excludes = res['excludes']
clip = res['clip']
gauss = res['gauss']
bins = res['bins']
ytr = res['yaxr']
xtt = res['xaxt']
yrange = parserange(res['yrange'])
xrange = parserange(res['xrange'])
histyrange = parserange(res['histyrange'])
histxrange = parserange(res['histxrange'])
forkoff = res['fork']                   

dims = (res['width'], res['height'])

if rf is None:
    print "No integration result file specified"
    sys.exit(100)

if excludes is not None:
    try:
        elist = exclusions.Exclusions()
        elist.load(excludes)
    except exclusions.ExcludeError as e:
        print e.args[0] + ': ' + e.args[1]
        sys.exit(101)
    rlist = elist.reasons()
    excols = string.split(res['exclcolours'], ',')
    excolours = excols * ((len(rlist) + len(excols) - 1) / len(excols))
    rlookup = dict()
    for r, c in zip(rlist, excolours):
        rlookup[r] = c

# Load up file of integration results

inp = np.loadtxt(rf, unpack=True)
dates = inp[0]
vals = inp[1]

plt.figure(figsize=dims)

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
        plt.plot(lx, garr)
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
    plt.hist(vals,bins=bins)
if ytr:
    plt.gca().yaxis.tick_right()
    plt.gca().yaxis.set_label_position("right")
if xtt:
    plt.gca().xaxis.tick_top()
    plt.gca().xaxis.set_label_position("top")
histxlab = res['xhist']
histylab = res['yhist']
if histxlab == "none":
	histxlab = ""
if histylab == "none":
	histylab = ""
if len(histylab) > 0:
    plt.ylabel(histylab)
else:
    plt.yticks([])
if len(histxlab) > 0:
    plt.xlabel(histxlab)
else:
    plt.xticks([])
if outf is not None:
    fname = outf + '_hist.png'
    plt.savefig(fname)
if not sdp: plt.figure(figsize=dims)
 
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

xlab = res['xplot']
ylab = res['yplot']
if xlab == "none":
	xlab = ""
if ylab == "none":
	ylab = ""
fnum = 1
legend_number = res['legnum']

if sdp:
    for xarr, yarr, col in zip(rxarray,ryarray,colours):
        offs = xarr[0]
        xa = np.array(xarr) - offs
        ya = np.array(yarr)
        f = plt.figure(figsize=dims)
        if xrange is not None:
            plt.xlim(*xrange)
        if yrange is not None:
            plt.ylim(*yrange)
        if len(ylab) == 0:
            plt.yticks([])
        else:
            if ytr:
                plt.gca().yaxis.tick_right()
                plt.gca().yaxis.set_label_position("right")
            plt.ylabel(ylab)
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
        if legend_number > 0:
            plt.legend(loc=res['legpos'])
        if outf is not None:
            fname = outf + ("_f%.3d.png" % fnum)
            f.savefig(fname)
            fnum += 1
else:
    legends = []
    lines = []
    if yrange is not None:
        plt.ylim(*yrange)
    if len(ylab) == 0:
        plt.yticks([])
    else:
        if ytr:
            plt.gca().yaxis.tick_right()
            plt.gca().yaxis.set_label_position("right")
        plt.ylabel(ylab)
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
        if len(legends) < legend_number:
            legends.append(jdate.display(xarr[0]))
        elif  len(legends) == legend_number:
            legends.append('etc...')
        if excludes is not None:
            sube = elist.inrange(np.min(xarr), np.max(xarr))
            for pl in sube.places():
                xpl = pl - offs
                reas = sube.getreason(pl)
                creas = rlookup[reas]
                lines.append((xpl,creas))
	if legend_number > 0:
	    plt.legend(legends,loc=res['legpos'])
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
