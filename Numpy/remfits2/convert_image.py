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
import miscutils
import math
import remdefaults
import remfits
import os.path
import col_from_file

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
warnings.simplefilter('error', RuntimeWarning)  # Want div by zero etc to retunr error

parsearg = argparse.ArgumentParser(description='Do specified operation on FITS files ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs=2, type=str, help='File1 and File2')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--outfile', type=str, help='Output FITS file otherwise replace first file')
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file if --outfile given')
parsearg.add_argument('--operation', type=str, choices=['add', 'sub', 'mult', 'div', 'rsub', 'rdiv'], required=True,
                      help='Operation required, rsub rdiv apply file1 to file2 result still in file1')
parsearg.add_argument('--single', type=str, choices=['mean', 'median', 'min', 'max'], help='Use selected value of second file rather than whole')

resargs = vars(parsearg.parse_args())
file1, file2 = resargs['files']
remdefaults.getargs(resargs)
outfile = resargs['outfile']
force = resargs['force']
operation = resargs['operation']
single = resargs['single']

mydb, dbcurs = remdefaults.opendb()

if outfile is None:
    if  file1.isnumeric() or (len(file1) > 2 and file1[1] == ':' and file1[2:].isnumeric()):
        print("First file must be file name if not --outfile given not", file1, file=sys.stderr)
        sys.exit(51)
    outfile = file1
    force = True
elif  os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(50)

try:
    f1 = remfits.parse_filearg(file1, dbcurs)
except remfits.RemFitsErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(52)

try:
    f2 = remfits.parse_filearg(file2, dbcurs)
except remfits.RemFitsErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(53)

if f1.filter != f2.filter:
    print("Filters incompatible between", file1, "-", f1.filter, "and", file2, "-", f2.filter, file=sys.stderr)
    sys.exit(54)

if f1.dims() != f2.dims():
    print("Dimensions incompatible between", file1, "-", f1.dims(), "and", file2, "-", f2.dims(), file=sys.stderr)
    sys.exit(55)

f1dat = f1.data
f2dat = f2.data
try:
    if single is None:
        if operation == 'add':
            result = f1dat + f2dat
        elif operation == 'sub':
            result = f1dat - f2dat
        elif operation == 'rsub':
            result = f2dat - f1dat
        elif operation == 'mult':
            result = f1dat * f2dat
        elif operation == 'div':
            result = f1dat / f2dat
        else:
            result = f2dat / f1dat
    else:
        if single == 'min':
            val = f2dat.min()
        elif single == 'max':
            val = f2dat.max()
        elif single == 'mean':
            val = f2dat.mean()
        else:
            val = np.median(f2dat)
        if operation == 'add':
            result = f1dat + val
        elif operation == 'sub':
            result = f1dat - val
        elif operation == 'rsub':
            result = val - f1dat
        elif operation == 'mult':
            result = f1dat * val
        elif operation == 'div':
            result = f1dat / val
        else:
            result = val / f1dat
except RuntimeWarning as e:
    print("OPeraiont", operation, "gave error", e.args[0], file=sys.stderr)
    sys.exit(100)

max_value = result.max()
min_value = result.min()
rrows, rcols = result.shape

result = np.pad(result, ((0, 1024 - rrows), (0, 1024 - rcols)), 'constant')

result_header = f1.hdr
result_header.set('FILENAME', miscutils.removesuffix(outfile), ' filename of this image')
result_header['DATAMIN'] = min_value
result_header['DATAMAX'] = max_value
result_header['COMMENT'] = "Constructed by " + operation + " on " + file1 + " and " + file2

for todel in ('BZERO', 'BSCALE', 'BUNIT', 'BLANK', 'DATE_MIN', 'DATE_MAX', 'MJD_MIN', 'MJD_MAX', 'N_IMAGES'):
    try:
        del result_header[todel]
    except KeyError:
        pass

hdu = fits.PrimaryHDU(result, result_header)
try:
    hdu.writeto(outfile, overwrite=force, checksum=True)
except OSError:
    print("Could not write", outfile, file=sys.stderr)
    sys.exit(200)
