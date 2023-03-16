#!  /usr/bin/env python3

"""Select poritions of light curves"""

import argparse
import sys
import math
import numpy as np
import logs

def zap_stddev(dats, vals, err, minnum, stdmult, loopn):
    """Prune a list to exclude values outside n*stu"""

    for dummy in range(0, loopn):
        zap = np.abs(vals - vals.mean()) <= stdmult * vals.std()
        dats =  dats[zap]
        vals = vals[zap]
        err = err[zap]
        if dats.size < minnum:
            break
    return (dats, vals, err)

parsearg = argparse.ArgumentParser(description='Prune light curves', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs='*', type=str, help='Data table or use stdin')
parsearg.add_argument('--outfile', type=str, help='Output file or use stdout' )
parsearg.add_argument('--minvals', type=int, default=10, help='Minimum number of output values')
parsearg.add_argument('--vgroup', type=int, default=2, help='Minumum number of output values per group')
parsearg.add_argument('--toflux', type=float, help='If specified, add this value and treat as magnitude')
parsearg.add_argument('--normalise', type=float, help='Normalise results to this value after processing')
parsearg.add_argument('--break', type=float, help='Interval to break at when grouping')
parsearg.add_argument('--nstd', type=float, help='Min number of stds to exclude obs')
parsearg.add_argument('--loopstds', type=int, default=1, help='Loops in number of stds')
parsearg.add_argument('--maxswing', type=float, help='Percent swing over group to exclude whole group')
parsearg.add_argument('--bin', action='store_true', help='Bin groups together after processing')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
infile = resargs['file']
outfile = resargs['outfile']
minvals = resargs['minvals']
toflux = resargs['toflux']
normalise = resargs['normalise']
breakat = resargs['break']
vgroup = resargs['vgroup']
nstd = resargs['nstd']
loopstds = resargs['loopstds']
bins = resargs['bin']
maxswing = resargs['maxswing']
logging = logs.getargs(resargs)

input_array = None

if len(infile) == 0:
    input_array = np.loadtxt(sys.stdin, unpack=True)
else:
    for inf in infile:
        try:
            newa = np.loadtxt(inf, unpack=True)
            if input_array is None:
                input_array = newa
            else:
                input_array = np.concatenate((input_array, newa))
        except OSError as e:
            logging.die(20, "Could not open", inf, "error was", e.args[-1])
        except ValueError:
            logging.die(21, "Input arrays do not have same dimensions after reading", inf)

try:
    inrows, incols = input_array.shape
except ValueError:
    logging.die(22, "Unable to unpack array, expecting 2D")

if incols < minvals:
    logging.die(23, "Not got enough values at", incols, "expecting at least", minvals)

if inrows == 2:
    dates, values = input_array
    errs = np.zeros_like(values)
elif inrows != 3:
    logging.die(24, "Expecting 2 or 3 columns in data not", inrows)
else:
    dates, values, errs = input_array

# Save ourselves worrying about whether they are sorted or not

sres = dates.argsort()
dates = dates[sres]
values = values[sres]
errs = errs[sres]

output_array = np.array([]).reshape(3,0)

if breakat is None:
    if nstd is not None:
        dates, values, errs = zap_stddev(dates, values, errs, minvals, nstd, loopstds)
    output_array = np.concatenate((output_array, np.array([dates, values, errs])), axis=1)
else:
    startcol = endcol = 0
    breakpoints = np.where(dates[1:] - dates[:-1] > breakat)[0] + 1
    for  brk in breakpoints:
        endcol = brk
        dates_seg = dates[startcol:endcol]
        values_seg = values[startcol:endcol]
        errs_seg = errs[startcol:endcol]
        if nstd is not None and endcol-startcol >= vgroup:
            dates_seg, values_seg, errs_seg = zap_stddev(dates_seg, values_seg, errs_seg, vgroup, nstd, loopstds)
        if maxswing is None or values_seg.std() / values_seg.mean() <= maxswing / 100.0:
            if bins:
                dates_seg = np.array([dates_seg.mean()])
                values_seg = np.array([values_seg.mean()])
                errs_seg = np.array([math.sqrt(np.sum(errs_seg**2))/errs_seg.size])
            output_array = np.concatenate((output_array,np.array([dates_seg, values_seg, errs_seg])), axis=1)
        startcol = endcol

    if startcol < dates.size:
        dates_seg = dates[startcol:]
        values_seg = values[startcol:]
        errs_seg = errs[startcol:]
        if nstd is not None and dates.size-startcol >= vgroup:
            dates_seg, values_seg, errs_seg = zap_stddev(dates_seg, values_seg, errs_seg, vgroup, nstd, loopstds)
        if maxswing is None or values_seg.std() / values_seg.mean() <= maxswing / 100.0:
            if bins:
                dates_seg = np.array([dates_seg.mean()])
                values_seg = np.array([values_seg.mean()])
                errs_seg = np.array([math.sqrt(np.sum(errs_seg**2))/errs_seg.size])
            output_array = np.concatenate((output_array,np.array([dates_seg, values_seg, errs_seg])), axis=1)

if normalise is not None:
    # print("shape before", output_array.shape, file=sys.stderr)
    output_array[1:] *= normalise / output_array[1].mean()
    # print("shape after", output_array.shape, file=sys.stderr)
if inrows == 2:
    output_array = output_array[0:1]
output_array = output_array.transpose()

try:
    if outfile is None:
        np.savetxt(sys.stdout, output_array)
    else:
        np.savetxt(outfile, output_array)
except (KeyboardInterrupt, BrokenPipeError):
    pass
