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
parsearg.add_argument('--precentre', action='store_true', help='Precentre to maan')
parsearg.add_argument('--minperiod', type=float, help='Minimum period to accept')
parsearg.add_argument('--maxperiod', type=float, help='Maximum period to accept')
parsearg.add_argument('--npowers', type=int, default=1, help='Number of powers to highlight')
parsearg.add_argument('--xlabel', type=str, default='Window size', help='Label for X axis')
parsearg.add_argument('--y1label', type=str, default='Mean value', help='Label for LH Y axis')
parsearg.add_argument('--y2label', type=str, default='Standard deviation value', help='Label for RH Y axis')
parsearg.add_argument('--plotcolour', type=str, default='b,g,r,k,cyan,magenta,yellow', help='Colours to cycle round for plots')
#parsearg.add_argument('--errstyle', type=str, default='dotted', help='Line style for stddev plot')
parsearg.add_argument('--erralpha', type=float, default=1.0, help='Alpha for error bars')

rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
infile = resargs['file']
nstd1 = resargs['nstd1']
nstd2 = resargs['nstd2']
minvals = resargs['minvals']
precentre = resargs['precentre']
minperiod = resargs['minperiod']
maxperiod = resargs['maxperiod']
npowers = resargs['npowers']
plotcolour = resargs['plotcolour'].split(',') * npowers
#errstyle = resargs['errstyle']
erralpha = resargs['erralpha']
xlab = resargs['xlabel']
y1lab = resargs['y1label']
y2lab = resargs['y2label']
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
dspan = int(endday - startday)

windaylist = []
meanstdlist = []

for windays in range(1, dspan):

    rtab = []
    dsteps = []

    for dstep in range(0, dspan - windays):
        maskcol = (timearr >- startday + dstep) & (timearr <= startday + dstep + windays)
        if np.count_nonzero(maskcol) < minvals:
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
            continue
        dsteps.append(dstep)
        rtab.append([p.value for p in periods[power_peak_locs[:npowers]]])

    if len(rtab) <= 2:
        continue

    rtab = np.array(rtab)
    windaylist.append(windays)
    meanstdlist.append((rtab.mean(axis=0), rtab.std(axis=0)))

if len(meanstdlist) < 2:
    print("Not enough results to display", file=sys.stderr)
    sys.exit(100)

pfig = rg.plt_figure()

means, stds = np.array(meanstdlist).transpose(1, 2, 0)

ax = plt.subplot(111)
for n, ms in enumerate(zip(means, stds)):
    m, s = ms
    mk, cp, bars = ax.errorbar(windaylist, m, s, color=plotcolour[n])
    if erralpha != 1.0:
        for bar in bars:
            bar.set_alpha(erralpha)
plt.xlabel(xlab)
plt.ylabel(y1lab)
# ax2 = ax.twinx()
# for n, p in enumerate(stds):
#     ax2.plot(windaylist, p, linestyle=errstyle, color=plotcolour[n])
# plt.ylabel(y2lab)

remgeom.end_figure(pfig, outfile)
remgeom.end_plot(outfile)
