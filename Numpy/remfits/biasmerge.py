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
import miscutils

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Merge bias files into a combined one', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='Bias files to be combined')
parsearg.add_argument('--outfile', type=str, required=True, help='Output filts file')
parsearg.add_argument('--ffref', type=str, help='Flat file for reference')
parsearg.add_argument('--trim', type=str, help='Trim to rows:coliumns')
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with median in bias files before combining')
parsearg.add_argument('--divff', action='store_true', help='Divide by flat field')
parsearg.add_argument('--force', action='store_true', help='Overwrite existing files')

resargs = vars(parsearg.parse_args())
filelist = resargs['files']
outfile = resargs['outfile']
ffref = resargs['ffref']
rc = resargs['trim']
replstd = resargs['replstd']
divff = resargs['divff']
force = resargs['force']
rows = None
cols = None

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
    if divff:
        print("Sorry cannot specify --divff if just rows:cols given", file=sys.stderr)
        sys.exit(15)
elif divff:
    print("Cannot specify divff unless flag file given", file=sys.stderr)
    sys.exit(16)

errors = 0
biasims = []
biasdates = []

for biasf in filelist:
    try:
        bf = fits.open(biasf)
    except OSError as e:
        errors += 1
        print("Cannot open", biasf, "error was", e.args[1], file=sys.stderr)
        continue
    bhdr = bf[0].header
    if bhdr['EXPTIME'] != 0:
        errors += 1
        print(biasf, "is not a bias file", file=sys.stderr)
        bf.close()
        continue
    biasdates.append(Time(bhdr['DATE-OBS']).mjd)
    bdat = bf[0].data.astype(np.float64)
    biasims.append(bdat)
    bf.close()

if errors > 0:
    print("aborting due to", errors, "error(s)", file=sys.stderr)
    sys.exit(100)

if rows is None:
    xc = [b.shape[0] for b in biasims]
    yc = [b.shape[1] for b in biasims]
    if min(xc) != max(xc) or min(yc) != max(yc):
        rows = min(xc)
        cols = min(yc)

if rows is not None:
   biasims = trimarrays.trimrc(rows, cols, *biasims)
   if divff:
       biasims = [b / ffrefim for b in biasims]

if replstd > 0.0:
    biasims = [strreplace.strreplace(b, replstd) for b in biasims]

if len(biasims) < 2:
    resimage = biasims[0]
else:
    resimage = np.median(np.array(biasims), axis=0)

# Now create the new fits file

fhdr = fits.Header()
fhdr.set('SIMPLE', True, 'File does conform to FITS standard')
fhdr.set('NAXIS', 2, 'Number of data axes')
fhdr.set('NAXIS1', resimage.shape[0], 'Length of data axis 1')
fhdr.set('NAXIS1', resimage.shape[1], 'Length of data axis 2')
fhdr.set('EXPTIME', 0, 'Total integration Time')
fhdr.set('GAIN', 1.0, '[e/ADU] CCD gain')           # CHDEATING HERE
fhdr.set('DATE-OBS', Time(np.mean(biasdates), format='mjd').iso, 'Mean value of supplied dates')

hdu = fits.PrimaryHDU(resimage, fhdr)
try:
    hdu.writeto(outfile, overwrite=force, checksum=True)
except OSError:
    print("Could not write", outfile, file=sys.stderr)
    sys.exit(200)
