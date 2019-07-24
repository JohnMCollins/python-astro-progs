#!  /usr/bin/env python3

# Get object data and maintain XML Database

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import trimarrays
import strreplace
from email.utils import parseaddr

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Statistics on FITS file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs='+', type=str, help='FITS files to process')
parsearg.add_argument('--ffref', type=str, help='Flat file for reference')
parsearg.add_argument('--trim', type=str, help='Trim to rows:coliumns')
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with median')
parsearg.add_argument('--total', action='store_false', help='Print all lines as wel as total')

resargs = vars(parsearg.parse_args())
files = resargs['file']
ffref = resargs['ffref']
rc = resargs['trim']
replstd = resargs['replstd']
pall = resargs['total']

if ffref is not None:
    ffreff = fits.open(ffref)
    ffrefim = trimarrays.trimzeros(trimarrays.trimnan(ffreff[0].data))
    ffreff.close()
    rows, cols  = ffrefim.shape
elif rc is not None:
    try:
        rows, cols = map(lambda x: int(x), rc.split(':'))
    except ValueError:
        print("Unexpected --trim arg", rc, "expected rows:cols", file=sys.stderr)
        sys.exit(10)
else:
    print("No reference flat file or trim arg given", file=sys.stderr)
    sys.exit(11) 

allvals = None
for file in files:
    ff = fits.open(file)
    fd = ff[0].data
    (fd,) = trimarrays.trimrc(rows, cols, fd)
    ff.close()
    if replstd > 0:
        fd = strreplace.strreplace(fd, replstd)
    if allvals is None:
        allvals = fd.copy()
    else:
        allvals = np.concatenate((allvals, fd))
    if pall:
        print(file, fd.min(), fd.max(), "%.2f" % fd.mean(), "%.2f" % fd.std(), sep="\t")

print("Total\t", allvals.min(), allvals.max(), "%.2f" % allvals.mean(), "%.2f" % allvals.std(), sep="\t")