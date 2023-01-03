#!  /usr/bin/env python3

"""Select poritions of light curves"""

import argparse
import sys
import math
import numpy as np

parsearg = argparse.ArgumentParser(description='Prune light curves', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs='*', type=str, help='Data table or use stdin')
parsearg.add_argument('--outfile', type=str, help='Output file or use stdout' )
parsearg.add_argument('--days', type=str, help='n:n days to pick out of data')
parsearg.add_argument('--nstd', type=float, help='Maximum multiple of std devs to prune')
parsearg.add_argument('--minvals', type=int, default=10, help='Minimum number of output values')
parsearg.add_argument('--toflux', type=float, help='If specified, add this value and treat as magnitude')
parsearg.add_argument('--normalise', type=float, help='Normalise result to this value')

resargs = vars(parsearg.parse_args())
infile = resargs['file']
outfile = resargs['outfile']
days = resargs['days']
nstd = resargs['nstd']
minvals = resargs['minvals']
toflux = resargs['toflux']
normalise = resargs['normalise']

minday = 0
maxday = 1e10
if days is not None:
    dsplit = days.split(':')
    if len(dsplit) > 2:
        print("Expecting --days arg to be n:n not", days, file=sys.stderr)
        sys.exit(10)
    try:
        if len(dsplit) == 1:
            if len(days) > 0:
                minday = maxday = int(days)
        else:
            lowd, highd = dsplit
            if len(lowd) > 0:
                minday = int(lowd)
            if len(highd) > 0:
                maxday = int(highd)
    except ValueError:
        print("Unknown --days arg", days, file=sys.stderr)
        sys.exit(11)

if len(infile) == 0:
    input_array = np.loadtxt(sys.stdin, unpack=True)
else:
    try:
        input_array = np.loadtxt(infile[0], unpack=True)
    except OSError as e:
        print("Could not open", infile[0], "error was", e.args[-1], file=sys.stderr)
        sys.exit(20)
if input_array.shape[0] == 2:
    t, f = input_array
    err = None
    s = np.argsort(t)
    t = t[s]
    f = f[s]
    t -= t[0]
    m = (minday <= np.floor(t)) & (np.floor(t) <= maxday)
    if np.count_nonzero(~m) != 0:
        t = t[m]
        f = f[m]
    if len(f) < minvals:
        print("Too few values ({:d}) should be at least {:d}".format(len(f), minvals), file=sys.stderr)
        sys.exit(30)
    if toflux is not None:
        f = 10 ** ((f + toflux) / 2.5)
    if normalise is not None:
        f *= normalise / f.mean()
    if nstd is not None:
        m = np.abs(f - f.mean()) <= f.std() * nstd
        t = t[m]
        f = f[m]
    output_array = np.transpose(np.array((t, f)))
else:
    t, f, err = input_array
    s = np.argsort(t)
    t = t[s]
    f = f[s]
    err = err[s]
    offt = t - t[0]
    m = (minday <= np.floor(offt)) & (np.floor(offt) <= maxday)
    if np.count_nonzero(~m) != 0:
        t = t[m]
        f = f[m]
        err = err[m]
    if len(f) < minvals:
        print("Too few values ({:d}) should be at least {:d}".format(len(f), minvals), file=sys.stderr)
        sys.exit(30)
    if toflux is not None:
        f = 10 ** ((f + toflux) / 2.5)
        err *= 0.4 * math.log(10) * f
    if normalise is not None:
        nf = normalise / f.mean()
        f *= nf
        err *= nf
    if nstd is not None:
        m = np.abs(f - f.mean()) <= f.std() * nstd
        t = t[m]
        f = f[m]
        err = err[m]
    output_array = np.transpose(np.array((t, f, err)))

try:
    if outfile is None:
        np.savetxt(sys.stdout, output_array)
    else:
        np.savetxt(outfile, output_array)
except (KeyboardInterrupt, BrokenPipeError):
    pass
