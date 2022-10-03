#!  /usr/bin/env python3

"""Produce light curve data emulation"""

import argparse
import sys
import numpy as np
from numpy import random

def gauss(xpoints, amp, mean, sigma):
    """Compute guassian with given amplitude, eman and sigma"""
    return  amp * np.exp((xpoints - mean) ** 2 / (-2.0 * sigma**2))

def wrapgauss(xpoints, amp, mean, sigma, wrapat=1.0):
    """Generate gaussian wrapped around as a cylinder"""
    return  gauss(xpoints, amp, mean, sigma) +\
            gauss(xpoints + wrapat, amp, mean, sigma) +\
            gauss(wrapat - xpoints, amp, -mean, sigma)

parsearg = argparse.ArgumentParser(description='Produce light curve data emulation', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('outfile', nargs='*', type=str, help='Output file or use stdout')
parsearg.add_argument('--timefile', type=str, help='File to take times from /dev/fd/0 for stdin')
parsearg.add_argument('--period', type=float, default=10.0, help='Period of rotatation to emulate')
parsearg.add_argument('--cycles', type=float, default=1.0, help='Number of cycles to emulate')
parsearg.add_argument('--npoints', type=int, default=100, help='Number of points to generate')
parsearg.add_argument('--baseflux', type=float, default=100.0, help='Base flux to emulate')
parsearg.add_argument('--uniform', type=float, default=0.0, help='Uniform noise to emulate')
parsearg.add_argument('--gaussian', type=float, default=0.0, help='Gaussian noise to emulate')
parsearg.add_argument('--position', type=float, nargs='*', help='Position of spots in degrees')
parsearg.add_argument('--amplitudes', type=float, nargs='*', help='Amplitures of spots in degrees maybe negative')
parsearg.add_argument('--stds', type=float, nargs='*', help='Std devs of spots')

resargs = vars(parsearg.parse_args())
outfile = resargs['outfile']
timefile = resargs['timefile']
period = resargs['period']
cycles = resargs['cycles']
npoints = resargs['npoints']
baseflux = resargs['baseflux']
unoise = resargs['uniform']
gnoise = resargs['gaussian']
positions = resargs['position']
amplitudes = resargs['amplitudes']
stds = resargs['stds']

if positions is None or amplitudes is None or stds is None:
    if positions is not None or amplitudes is not None or stds is not None:
        print("Need to specify all of positions/amplitudes/stds", file=sys.stderr)
        sys.exit(10)
elif len(positions) != len(amplitudes) or len(amplitudes) != len(stds):
    print("Positions, amplitudes, stds should all be the same length not {:d},{:d},{:d}".format(len(positions), len(amplitudes), len(stds)), file=sys.stderr)
    sys.exit(11)

if timefile is None:
    xlist = random.uniform(high=cycles*period, size=npoints)
else:
    try:
        arr = np.loadtxt(timefile, unpack=True)
    except OSError as e:
        print("Could not open", timefile, "error was", e.args[-1], file=sys.stderr)
        sys.exit(12)
    xlist = arr[0]
    xlist -= xlist.min()
    npoints = len(xlist)

ylist = np.full(npoints, baseflux)

if positions is not None:
    for pos, ampl, std in zip(positions, amplitudes, stds):
        ylist += wrapgauss(xlist % period, ampl, (pos % 360.0) * period / 360.0, std, wrapat=period)

if unoise >= 0.0:
    ylist += random.uniform(low=-unoise, high=unoise, size=npoints)
if gnoise >= 0.0:
    ylist += random.normal(loc=0, scale=gnoise, size=npoints)

order = np.argsort(xlist)
xlist = xlist[order]
ylist = ylist[order]

result = np.array((xlist, ylist)).transpose()
if len(outfile) == 0:
    np.savetxt(sys.stdout, result)
else:
    np.savetxt(outfile[0], result)
