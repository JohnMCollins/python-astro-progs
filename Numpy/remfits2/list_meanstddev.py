#!  /usr/bin/env python3

# Duplicate creation of master bias file

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import os.path
import remdefaults
import remfits
import col_from_file
import miscutils


def lpad(st, maxlen):
    """Pad column on left to maximum length"""
    return  " " * (maxlen - len(st)) + st

# Shut up warning messages


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='List means and standard deviations from file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Filenames or iforbinds to process, otherwise use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--outfile', type=str, help='Output file file (adds .tex if latex mode)')
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file')
parsearg.add_argument('--titles', type=str, help='Titles separated by :: - strip off suffixes from file names if not given')
parsearg.add_argument('--latex', action='store_true', help='Latex style output')
parsearg.add_argument('--type', type=str, choices=['F', 'B'], help='Specify F or B if id args are to be daily flat or bias')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['files']
outfile = resargs['outfile']
force = resargs['force']
titles = resargs['titles']
latex = resargs['latex']
type = resargs['type']

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

mydb, mycurs = remdefaults.opendb()

if outfile is not None:
    if latex:
        outfile = miscutils.addsuffix(outfile, 'tex')
    if os.path.exists(outfile) and not force:
        print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
        sys.exit(50)
    try:
        outf = open(outfile, 'wt')
    except OSError as e:
        print("Count not open", outfile, "error was", e.args[1], file=sys.stderr)
else:
    outf = sys.stdout

if titles is not None:
    titles = titles.split("::")
    if len(titles) == 1:
        titles = titles * len(files)
    elif len(titles) != len(files):
        print("Expecting titles (%d) to be of same length as files (%d)" % (len(titles), len(files)), files=sys.stderr)
        sys.exit(51)
else:
    titles = []
    for f in files:
        titles.append(miscutils.removesuffix(f, all=True))

errors = 0

restab = []

for f in files:
    try:
        ff = remfits.parse_filearg(f, mycurs, type=type)
    except remfits.RemFitsErr as e:
        print("file", f, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    fdat = ff.data
    minus = np.count_nonzero(fdat < 0.0)
    restab.append(("{:.1f}".format(fdat.min()), "{:.1f}".format(fdat.max()), "{:.1f}".format(np.median(fdat)), "{:.3f}".format(fdat.mean()), "{:.3f}".format(fdat.std())))

if errors > 0:
    print("Stopping due to", errors, "errors", file=sys.stderr)
    sys.exit(80)

output = []
if latex:
    for t, r in zip(titles, restab):
        mn, mx, med, mean, std = r
        output.append(' & '.join((t, mn, mx, med, mean, std)) + ' \\\\')
else:
    maxtit = max([len(t) for t in titles])
    maxmin = max([len(t[0]) for t in restab])
    maxmax = max([len(t[1]) for t in restab])
    maxmed = max([len(t[2]) for t in restab])
    maxmean = max([len(t[3]) for t in restab])
    maxstd = max([len(t[4]) for t in restab])
    for t, r in zip(titles, restab):
        mn, mx, med, mean, std = r
        output.append(" ".join((t + " " * (maxtit - len(t)), lpad(mn, maxmin), lpad(mx, maxmax), lpad(med, maxmed), lpad(mean, maxmean), lpad(std, maxstd))))

for o in output:
    print(o, file=outf)
