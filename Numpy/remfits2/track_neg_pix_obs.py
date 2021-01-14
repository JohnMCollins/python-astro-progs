#!  /usr/bin/env python3

# Duplicate creation of master flat file

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import remdefaults
import remfits
import col_from_file

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
warnings.simplefilter('error', RuntimeWarning)  # Want div by zero etc to retunr error

parsearg = argparse.ArgumentParser(description='Observe effects of binning/trimming on negative pixels ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Filenames or obsinds to process, otherwise use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
parsearg.add_argument('--binint', type=int, default=0, help="Bin interval which is too much")
parsearg.add_argument('--trim', type=int, default=0, help="Pixels to trim from each edge")
parsearg.add_argument('--biasfile', type=str, required=True, help="Bias file to use")
parsearg.add_argument('--negamt', type=float, default=0.0, help='Amount negative')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
binint = resargs['binint']
trim = resargs['trim']
biasfile = resargs['biasfile']
negamt = -abs(resargs['negamt'])

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

mydb, dbcurs = remdefaults.opendb()

try:
    bfile = remfits.parse_filearg(biasfile, dbcurs, 'B')
except remfits.RemFitsErr as e:
    print("Cannot open bias file", biasfile, "error was", e.args[0], file=sys.stderr)
    sys.exit(20)

bdata = bfile.data
if trim != 0:
    bdata = bdata[trim:-trim, trim:-trim]

filter = bfile.filter
brc = bfile.dimscr()

binned = []
cbin = []
lastdate = datetime.datetime.now()
for file in files:
    try:
        rf = remfits.parse_filearg(file, dbcurs)
    except remfits.RemFitsErr as e:
        print("Cannot open file", file, "error was", e.args[0], file=sys.stderr)
        continue
    if rf.filter != filter:
        print("File", file, "has different filter", rf.filter, "from bias of", filter, file=sys.stdderr)
        continue
    if rf.dimscr() != brc:
        print("File", file, "has different dims", rf.dimscr(), "from bias of", brc, file=sys.stderr)
        continue
    if (rf.date - lastdate).total_seconds() > binint:
        binned.append(cbin)
        cbin = []
    cbin.append(rf)
    lastdate = rf.date

if len(cbin) != 0:
    binned.append(cbin)

for cbin in binned:
    fdata = np.array([f.data for f in cbin])
    fdates = [f.date for f in cbin]
    if trim != 0:
        fdata = fdata[:, trim:-trim, trim:-trim]
    diffs = fdata - bdata
    zers = np.count_nonzero(diffs < negamt, axis=(1, 2))
    for d, zc in zip(fdates, zers):
        print("{:%Y-%m-%d %H:%M:%S}: {:6d}".format(d, zc))
    if len(fdates) > 1:
        print("Max run -ve:{:15d} out of {:d}".format(np.count_nonzero(diffs < negamt, axis=0).max(), len(fdates)))
        print("Median negative:      {:5d}".format(np.count_nonzero(np.median(fdata, axis=0) - bdata < 0)))
    print()
