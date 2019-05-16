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

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='List bias file contents', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='List of bias files')
parsearg.add_argument('--compare', type=str, help='File to compare against')
parsearg.add_argument('--ffref', type=str, help='Flat file for reference')
parsearg.add_argument('--trim', type=str, help='Trim to rows:coliumns')

resargs = vars(parsearg.parse_args())
filelist = resargs['files']
comparefile = resargs['compare']
ffref = resargs['ffref']
rc = resargs['trim']

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
    print("No reference flat file or trim arg given", file=sys.stederr)
    sys.exit(11) 

imlist = []
datelist = []

for ffile in filelist:
    
    ff = fits.open(ffile)
    imlist.append(ff[0].data.astype(np.float64))
    datelist.append(Time(ff[0].header['DATE']).datetime)
    ff.close()

imlist = list(trimarrays.trimrc(rows, cols, *imlist))

if comparefile is not None:
    ff = fits.open(comparefile)
    (compim, ) = trimarrays.trimrc(rows, cols, ff[0].data.astype(np.float64))
    ff.close()
    
    while len(imlist) != 0:
        im = imlist.pop(0)
        dat = datelist.pop(0)
        diff = np.abs(im - compim)
        print(dat.strftime("%Y-%m-%d %H:%M:%S"), "%8.0f %8.0f %8.0f %8.0f %8.0f" % (im.min(), np.median(im), im.max(), np.median(diff), diff.max()))
else:
    while len(imlist) != 0:
        im = imlist.pop(0)
        dat = datelist.pop(0)
        print(dat.strftime("%Y-%m-%d %H:%M:%S"), "%8.0f %9.0f %8.0f" % (im.min(), np.median(im), im.max()))
