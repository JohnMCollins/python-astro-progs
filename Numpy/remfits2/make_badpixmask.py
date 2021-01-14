#!  /usr/bin/env python3

import remdefaults
import argparse
import sys
import os.path
import numpy as np
import warnings

# Cope with divisions by zero

warnings.simplefilter('ignore', RuntimeWarning)


def comp_gt(w, v): return w > v


def comp_ge(w, v): return w >= v


def comp_eq(w, v): return w == v


def comp_ne(w, v): return w != v


def comp_le(w, v): return w <= v


def comp_lt(w, v): return w < v


comp_funcs = dict(gt=comp_gt, ge=comp_ge, eq=comp_eq, ne=comp_ne, le=comp_le, lt=comp_lt)

parsearg = argparse.ArgumentParser(description=' Make bad pixel mask from mean/std dev file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('msfile', type=str, nargs=1, help='Input mean std dev deviation file')
remdefaults.parseargs(parsearg, tempdir=False, database=False)
parsearg.add_argument('--outfile', type=str, help='Output bad pixel mask default is same prefix as input')
parsearg.add_argument('--force', action='store_true', help='Force if file exists')
parsearg.add_argument('--aspect', type=str, default='mean', choices=['mean', 'std', 'min', 'max', 'range'], help='Choose what to test')
parsearg.add_argument('--metric', type=str, default='mean', choices=['mean', 'std', 'min', 'max'], help='Choose feature')
parsearg.add_argument('--nmults', action='store_true', help='Use multiples of overall rather than actual value')
parsearg.add_argument('--abs', action='store_true', help='Compare absolute value of metric')
parsearg.add_argument('--compare', type=str, default='ge', choices=['eq', 'ne', 'gt', 'ge', 'lt', 'le'], help='Comparison operator')
parsearg.add_argument('--value', type=float, required=True, help='Value to compare')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
msfile = resargs['msfile'][0]
outfile = resargs['outfile']
force = resargs['force']
aspect = resargs['aspect']
metric = resargs['metric']
nmults = resargs['nmults']
absv = resargs['abs']
compare = resargs['compare']
value = resargs['value']

inputfile = remdefaults.meanstd_file(msfile)
try:
    sourcearray = np.load(inputfile)
except OSError as e:
    print("Trouble with source file", inputfile, "error was", e.args[1], file=sys.stderr)
    sys.exit(10)

if outfile is None:
    outfile = inputfile

outfile = remdefaults.bad_pixmask(outfile)

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(11)

counts = sourcearray[0]

if aspect == 'mean':
    working = sourcearray[1]
elif aspect == 'std':
    working = sourcearray[2]
elif aspect == 'min':
    working = sourcearray[3]
elif aspect == 'max':
    working = sourcearray[4]
else:  # Take as range
    working = sourcearray[4] - sourcearray[3]

countmask = counts != 0

flatarray = working.flatten()
flatcount = counts.flatten()

flatarray = flatarray[flatcount != 0]

overall_mean = flatarray.mean()
overall_std = flatarray.std()
overall_min = flatarray.min()
overall_max = flatarray.max()

if metric == 'mean':
    if nmults:
        value *= overall_mean
elif metric == 'std':
    if nmults:
        working -= overall_mean
        if absv:
            working = np.abs(working)
        value *= overall_std
elif metric == 'min':
    if nmults:
        value *= overall_min
elif nmults:
    value *= overall_max

result = comp_funcs[compare](working, value) & countmask

try:
    outf = open(outfile, 'wb')
except OSError as e:
    print("Could not open", outfile, "error was", e.args[1], file=sys.stderr)
    sys.exit(50)

np.save(outf, result)
outf.close()
print("There were", np.count_nonzero(result), "in bad pixel mask out of", np.count_nonzero(flatarray), file=sys.stderr)
sys.exit(0)
