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
import scipy.ndimage as spnd

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
warnings.simplefilter('error', RuntimeWarning)  # Want div by zero etc to retunr error

parsearg = argparse.ArgumentParser(description='Apply Gaussian smoothing to FITS file ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='File to work on')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--outfile', required=True, type=str, help='Output FITS file')
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file')
parsearg.add_argument('--sigma', type=float, default=1.0, help='Sigma to use in Gaussian')

resargs = vars(parsearg.parse_args())
file1, = resargs['file']
remdefaults.getargs(resargs)
outfile = resargs['outfile']
force = resargs['force']
sigma = resargs['sigma']

mydb, dbcurs = remdefaults.opendb()

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(50)

try:
    f1 = remfits.parse_filearg(file1, dbcurs)
except remfits.RemFitsErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(52)

f1dat = f1.data
trans = spnd.gaussian_filter(f1dat, sigma)
max_value = trans.max()
min_value = trans.min()
rrows, rcols = trans.shape

trans = np.pad(trans, ((0, 1024 - rrows), (0, 1024 - rcols)), 'constant')

result_header = f1.hdr
result_header['DATAMIN'] = min_value
result_header['DATAMAX'] = max_value
result_header['COMMENT'] = "Gaussian filter applied sigma={:.4g}".format(sigma)

for todel in ('BZERO', 'BSCALE', 'BUNIT', 'BLANK'):
    try:
        del result_header[todel]
    except KeyError:
        pass

hdu = fits.PrimaryHDU(trans, result_header)
try:
    hdu.writeto(outfile, overwrite=force, checksum=True)
except OSError:
    print("Could not write", outfile, file=sys.stderr)
    sys.exit(200)
