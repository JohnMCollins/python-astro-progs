#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse
import numpy as np
import noise
from astroML.time_series import lomb_scargle as lsas
from gatspy.periodic import LombScargle
import periodarg
import argmaxmin
import matplotlib.pyplot as plt

TWOPI = 2.0 * np.pi

def parseperamp(arg):
    """Parse argument a:b into period, amp tuple. Assume amp 1 if not given"""
    
    try:
        parts = map(lambda x: float(x), string.split(arg, ':'))
        if len(parts) > 2:
            raise ValueError("too many values")
    except ValueError:
        print "Invalid period arg", arg
        sys.exit(20)
    if len(parts) == 1:
        return (parts[0], 1.0)
    return parts  

parsearg = argparse.ArgumentParser(description='Generate periodic data fitting times')
parsearg.add_argument('ewfile', type=str, help='EW file to take times from', nargs=1)
parsearg.add_argument('--double', type=int, default=0, help='Number of times to double data')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)
parsearg.add_argument('--xlab', type=str, default='Phase as proportion of full cycle', help='X asis label')
parsearg.add_argument('--ylab1', type=str, default='Calculated period (ordered)', help='Y axis label for sorted plot')
parsearg.add_argument('--ylab2', type=str, default='Calculated period (by level)', help='Y axis label for plot by level')
parsearg.add_argument('--per1', help='First period[:amp]', type=str, required=True)
parsearg.add_argument('--per2', help='Second period[:amp]', type=str, required=True)
parsearg.add_argument('--ylim', type=float, default=1e10, help='Limit on Y values')
parsearg.add_argument('--pstep', help='Phase step', type=float, default=0.01)
parsearg.add_argument('--periods', type=str, default="1d:.01d:100d", help='Periods as start:step:stop or start:stop/number')
parsearg.add_argument('--error', type=float, default=.01, help='Error bar')
parsearg.add_argument('--gatspy', action='store_true', help='Use gatspy rather than AstroML')
parsearg.add_argument('--snr', type=float, default=0.0, help='SNR of noise to add 0=none (default)')
parsearg.add_argument('--gauss', type=float, default=0.0, help='Proportion uniform to gauss noise 0=all uniform 1=all gauss')
parsearg.add_argument('--outfile', help='Output file prefix to save plot', type=str)
parsearg.add_argument('--tonly', action='store_true', help='Only plot highest/max peak only')
parsearg.add_argument('--accept', type=float, default=0.1, help='Difference to count match to p1 in total')

res = vars(parsearg.parse_args())
ewfile = res['ewfile'][0]
dims = (res['width'], res['height'])
xlab = res['xlab']
ylab1 = res['ylab1']
ylab2 = res['ylab2']
ylim = res['ylim']
usegatspy = res['gatspy']
doublings = res['double']
tonly = res['tonly']
accept = res['accept']

p1, a1 = parseperamp(res['per1'])
p2, a2 = parseperamp(res['per2'])

f1 = TWOPI / p1
f2 = TWOPI / p2

try:
    periods = periodarg.periodrange(res['periods'])
except ValueError as e:
    print "Invalid period range", res['periods']
    sys.exit(10)

freqs = TWOPI / periods

err = res['error']
if err <= 0.0:
    print "Error value must be +ve"
    sys.exit(11)

snr = res['snr']
gauss = res['gauss']
outfile = res['outfile']

if gauss < 0.0 or gauss > 1.0:
    print "Invalid gauss proportion, should be between 0 and 1"
    sys.exit(12)

try:
    ewf = np.loadtxt(ewfile, unpack = True)
except IOError as e:
    print "Unable to open", ewfile, "error was", e.args[1]
    sys.exit(13)
except ValueError as e:
    print "Conversion error in", ewfile, "error was", e.args[0]
    sys.exit(14)

# Get barycentric times

times = ewf[1]
times -= times[0]
for d in range(0, doublings):
    times = np.concatenate((times, (times[1:]+times[0:len(times)-1]) / 2.0))
    times.sort(kind='mergesort')

phasesr = np.arange(0.0, 1.0, res['pstep'])
phases = phasesr  * TWOPI
errs = np.zeros_like(times) + err

lo = []
mid = []
hi = []

s1 = []
s2 = []
s3 = []

for p in phases:
    sig = a1 * np.sin(f1 * times) + a2 * np.sin(f2 * times + p)
    if snr != 0:
        sig = noise.noise(sig, snr, gauss)
    if usegatspy:
        model = LombScargle().fit(times, sig, err)
        pgram = model.periodogram(periods)
    else:
        pgram = lsas(times, sig, errs, freqs)
    maxima = argmaxmin.maxmaxes(periods, pgram)
    if len(maxima) > 3:
        maxima = maxima[0:3]
    maxp = list(periods[maxima])
    h, m, l = maxp
    s1.append(h)
    s2.append(m)
    s3.append(l)
    maxp.sort()
    l, m, h = maxp
    lo.append(l)
    mid.append(m)
    hi.append(h)

fig1 = plt.figure(figsize=dims)
if ylim < 1e6:
    plt.ylim(0, ylim)
plt.plot(phasesr, hi)
if not tonly:
    plt.plot(phasesr, mid)
    plt.plot(phasesr, lo)
if p1 < ylim:
    plt.axhline(p1, color='black', ls=':')
if p2 < ylim:
    plt.axhline(p2, color='black', ls=':')
plt.xlabel(xlab)
plt.ylabel(ylab1)

fig2 = plt.figure(figsize=dims)
if ylim < 1e6:
    plt.ylim(0, ylim)
plt.plot(phasesr, s1)
if not tonly:
    plt.plot(phasesr, s2)
    plt.plot(phasesr, s3)
if p1 < ylim:
    plt.axhline(p1, color='black', ls=':')
if p2 < ylim:
    plt.axhline(p2, color='black', ls=':')
plt.xlabel(xlab)
plt.ylabel(ylab2)

print "Percent in range of p1 %.2f" % (100.0 * (np.abs(p1 - np.array(s1)) <= accept).sum()/len(s1))

if outfile is None:
    plt.show()
else:
    fig1.savefig(outfile + '_sort.png')
    fig2.savefig(outfile + "_levs.png")

