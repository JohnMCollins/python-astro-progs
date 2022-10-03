#!  /usr/bin/env python3

"""Prune light curves in segments and plot trends in period peaks"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.timeseries import LombScargle
import remgeom
import argmaxmin

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Prune light curves in segments and plot trends in period peaks', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs='*', type=str, help='Data table or use stdin')
parsearg.add_argument('--nstd1', type=float, help='Maximum multiple of std devs to prune (pass 1)')
parsearg.add_argument('--nstd2', type=float, help='Maximum multiple of std devs to prune (pass 2)')
parsearg.add_argument('--minvals', type=int, default=10, help='Minimum number of values per window')
parsearg.add_argument('--windays', type=int, default=10, help='Days to pick out of data')
parsearg.add_argument('--precentre', action='store_true', help='Precentre to maan')
parsearg.add_argument('--minperiod', type=float, help='Minimum period to accept')
parsearg.add_argument('--maxperiod', type=float, help='Maximum period to accept')
parsearg.add_argument('--npowers', type=int, default=1, help='Number of powers to highlight')
parsearg.add_argument('--xlabel', type=str, default='Starting day', help='Label for X axis')
parsearg.add_argument('--ylabel', type=str, default='Peak value', help='Label for Y axis')
parsearg.add_argument('--plotcolour', type=str, default='b,g,r,k,cyan,magenta,yellow', help='Colours to cycle round for plots')
parsearg.add_argument('--meanls', type=str, default='dotted', help='Line style for mean indication')
parsearg.add_argument('--xoffset', type=float, default=0.1, help="Offset as proportion of X span for text display")
parsearg.add_argument('--yoffset', type=float, default=0.01, help="Offset as proportion of Y span for text display")
parsearg.add_argument('--sepplot', action='store_true', help='If more than one peak, plot in separate subplots')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
infile = resargs['file']
nstd1 = resargs['nstd1']
nstd2 = resargs['nstd2']
minvals = resargs['minvals']
windays = resargs['windays']
precentre = resargs['precentre']
minperiod = resargs['minperiod']
maxperiod = resargs['maxperiod']
npowers = resargs['npowers']
plotcolour = resargs['plotcolour'].split(',') * npowers
xlab = resargs['xlabel']
ylab = resargs['ylabel']
meanls = resargs['meanls']
#marker = resargs['marker']
xoffset = resargs['xoffset']
yoffset = resargs['yoffset']
sepplot = resargs['sepplot'] and npowers > 1
outfile = rg.disp_getargs(resargs)

if len(infile) == 0:
    input_array = np.loadtxt(sys.stdin, unpack=True)
else:
    try:
        input_array = np.loadtxt(infile[0], unpack=True)
    except OSError as e:
        print("Could not open", infile[0], "error was", e.args[-1], file=sys.stderr)
        sys.exit(20)

if nstd1 is not None:
    maskcol = input_array[1]
    maskv = np.abs(maskcol - maskcol.mean()) <= maskcol.std()*nstd1
    input_array = input_array[:,maskv]
if nstd2 is not None:
    maskcol = input_array[1]
    maskv = np.abs(maskcol - maskcol.mean()) <= maskcol.std()*nstd2
    input_array = input_array[:,maskv]

timearr = input_array[0]
fluxarr = input_array[1]
lskws = dict()

try:
    errarr = input_array[2]
    if precentre:
        lskws['center_data'] = True
except IndexError:
    errarr = None
    if precentre:
        lskws['fit_mean'] = True

elskws = lskws.copy()
if minperiod is not None:
    elskws['maximum_frequency'] = 1.0 / (minperiod * u.day)
if maxperiod is not None:
    elskws['minimum_frequency'] = 1.0 / (maxperiod * u.day)

startday = int(np.floor(timearr.min()))
endday = int(np.ceil(timearr.max()))

dspan = endday - startday

if dspan <= windays:
    print("Window size of", windays, "too big for data difference of", dspan, file=sys.stderr)
    sys.exit(30)

rtab = []
dsteps = []

for dstep in range(0, dspan - windays):
    maskcol = (timearr >- startday + dstep) & (timearr <= startday + dstep + windays)
    if np.count_nonzero(maskcol) < minvals:
        print("Skipping day", dstep, "as only", np.count_nonzero(maskcol), "values", file=sys.stderr)
        continue
    tseg = timearr[maskcol] * u.day
    fseg = fluxarr[maskcol]
    try:
        eseg = errarr[maskcol]
    except TypeError:
        eseg = None

    Lomb = LombScargle(tseg, fseg, eseg, **lskws)
    freq, power = Lomb.autopower(method='slow', **elskws)
    periods = 1 / freq
    power_peak_locs = argmaxmin.maxmaxes(periods.value, power)
    if len(power_peak_locs) < minvals:
        print("Not enough peaks ({:d}) for day {:d}".format(len(power_peak_locs), dstep), file=sys.stderr)
        continue
    dsteps.append(dstep)
    rtab.append([p.value for p in periods[power_peak_locs[:npowers]]])

if len(rtab) <= 2:
    print("Not enough results found to display", file=sys.stderr)
    sys.exit(50)

rtab = np.array(rtab).transpose()

pfig = rg.plt_figure()

if sepplot:
    axlist = []
    ylims = []
    means = []
    for n in range(0, npowers):
        ax = plt.subplot(npowers*100+11+n)
        axlist.append(ax)
        mn = rtab[n].mean()
        means.append(mn)
        ax.plot(dsteps, rtab[n], color=plotcolour[n])
        ax.axhline(mn, color=plotcolour[n], linestyle=meanls)
        ylims.append(ax.get_ylim())
        ax.yaxis.set_label_text(ylab)

    rangemax = max([p[1]-p[0] for p in ylims])
    rangemaxd2 = rangemax / 2.0
    for ax, yl in zip(axlist, ylims):
        ylo, yhi = yl
        midp = (yhi + ylo) / 2.0
        ax.set_ylim(midp-rangemaxd2, midp+rangemaxd2)


    axlist[-1].xaxis.set_label_text(xlab)
    xlims = axlist[-1].get_xlim()
    xoff = (xlims[1] - xlims[0]) * xoffset + xlims[0]
    yoff = rangemax * yoffset

    for n, ax in enumerate(axlist):
        mn = means[n]
        ax.text(xoff, mn+yoff, r"{:.2f} $\pm$ {:.2f}".format(mn, rtab[n].std()))

    plt.tight_layout()

else:
    means = []
    for n in range(0, npowers):
        plt.plot(dsteps, rtab[n], color=plotcolour[n])
        mn = rtab[n].mean()
        means.append(mn)
        plt.axhline(mn, color=plotcolour[n], linestyle=meanls)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    ax = plt.gca()
    xlims = ax.get_xlim()
    ylims = ax.get_ylim()
    xoff = (xlims[1] - xlims[0]) * xoffset + xlims[0]
    yoff = (ylims[1] - ylims[0]) * yoffset

    for n in range(0, npowers):
        mn = means[n]
        plt.text(xoff, mn+yoff, r"{:.2f} $\pm$ {:.2f}".format(mn, rtab[n].std()))

remgeom.end_figure(pfig, outfile)
remgeom.end_plot(outfile)
