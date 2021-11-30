#!  /usr/bin/env python3

""""Create master flat files"""

import datetime
import argparse
import warnings
import sys
import math
import os.path
from scipy.stats import gmean
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import numpy as np
import remdefaults
import remfits
import col_from_file

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
warnings.simplefilter('error', RuntimeWarning)

parsearg = argparse.ArgumentParser(description='Duplicate creation of master flat file ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('iforbinds', nargs='*', type=str, help='Filenames or ids to process, otherwise use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--biasfile', type=str, required=True, help='Bias file to use')
parsearg.add_argument('--outfile', type=str, required=True, help='Output FITS file')
parsearg.add_argument('--badpix', type=str, help='Bad pixel mask file to use')
parsearg.add_argument('--filter', type=str, help='Specify filter otherwise deduced from files')
parsearg.add_argument('--stoperr', action='store_true', help='Stop processing if any files rejected')
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file or things queried')
parsearg.add_argument('--baseid', type=int, help='ID to use for constructing FITS file if possible')

resargs = vars(parsearg.parse_args())
files = resargs['iforbinds']
remdefaults.getargs(resargs)
biasfile = resargs['biasfile']
outfile = resargs['outfile']
badpix = resargs['badpix']
filter_name = resargs['filter']
stoperr = resargs['stoperr']
force = resargs['force']
baseid = resargs['baseid']

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(50)

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
    if len(files) == 0:
        print("No files to process", file=sys.stderr)
        sys.exit(51)

mydb, mycurs = remdefaults.opendb()

try:
    biasstr = remfits.parse_filearg(biasfile, 'B')
except remfits.RemFitsErr as e:
    print("Bias file", biasfile, "gave error", e.args[0], file=sys.stderr)
    sys.exit(10)

if biasstr.ftype != 'Daily bias' and biasstr.ftype != 'Combined bias':
    print(biasfile, "is", biasstr.ftype, "not a bias file", file=sys.stderr)
    sys.exit(11)

if filter_name is None:
    filter_name = biasstr.filter
elif filter_name != biasstr.filter:
    print(biasfile, "is for filter", biasstr.filter, "but filter given as", filter_name, file=sys.stderr)
    sys.exit(12)

Bdims = biasstr.dimscr()
biasdata = biasstr.data

badpixmask = None
if badpix is not None:
    try:
        badpixmask = remdefaults.load_bad_pixmask(badpix)
    except remdefaults.RemDefError as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(13)
    badpixmask = badpixmask[biasstr.starty:biasstr.starty + biasstr.nrows, biasstr.startx:biasstr.startx + biasstr.ncolumns]

# If none given as base, use first one

sfiles = set(files)
if baseid is None or baseid not in sfiles:
    baseid = files[0]
# This manoeuvre is a quick way to eliminate duplicates
files = sorted(sfiles)

ffiles = []
usedids = []
basef = None
errors = 0
intfiles = []

for file in files:
    try:
        rf = remfits.parse_filearg(file, mycurs, 'F')
    except remfits.RemFitsErr as e:
        print("Loading from", file, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    if rf.ftype != "Daily flat":
        print("File type of", file, "is", rf.ftype, "not flat", file=sys.stderr)
        errors += 1
        continue
    if rf.filter != filter_name:
        print("Filter of", file, "is", rf.filter, "but using", filter_name, file=sys.stderr)
        errors += 1
        continue
    if Bdims != rf.dimscr():
        print("Dimensions of", file, "are", rf.dimscr(), "whereas previous are", Bdims, file=sys.stderr)
        errors += 1
        continue
    if file == baseid:
        basef = rf
    ffiles.append(rf)
    usedids.append(file)
    try:
        intfiles.append(rf.hdr['FILENAME'])
    except KeyError:
        pass

if (errors > 0  and  stoperr) or len(ffiles) == 0:
    print("Stopping due to", errors, "-", len(ffiles), "files loaded", file=sys.stderr)
    sys.exit(100)

# If we lost the indication, then just reset to first one

if basef is None:
    print("Selected baseid lost, using first available", file=sys.stderr)
    basef = ffiles[0]

arrblock = []
temps = []
dates = []
prebadpm = []
postbadpm = []
for ff in ffiles:
    dat = ff.data - biasdata
    prebadpm.append(np.count_nonzero(dat <= 0.0))
    postbadpm.append(np.count_nonzero(dat <= 0.0))
    arrblock.append(dat)
    temps.append(ff.ccdtemp)
    dates.append(ff.date)

arrblock = np.array(arrblock)
arrblock -= biasdata

try:
    if badpixmask is not None:
        arrblock[:, badpixmask] = 1.0
    result = gmean(arrblock, axis=0)
except RuntimeWarning:
    print("Zeror or negative values in result - aborting", file=sys.stderr)
    sys.exit(200)

result /= result.mean()
if badpixmask is not None:
    result[badpixmask] = 1.0
data_min = result.min()
data_max = result.max()
min_date = Time(min(dates))
max_date = Time(max(dates))
rrows, rcols = result.shape
result = np.pad(result, ((0, 1024 - rrows), (0, 1024 - rcols)), 'constant', constant_values=math.nan)

first_header = basef.hdr

first_header.set('DATE_MIN', str(min_date.isot), ' (UTC) start date of used flat frames')
first_header.set('DATE_MAX', str(max_date.isot), ' (UTC) end date of used flat frames')
first_header.set('MJD_MIN', min_date.mjd, ' [day] start MJD of used flat frames')
first_header.set('MJD_MAX', max_date.mjd, ' [day] end MJD of used flat frames')
first_header.set('N_IMAGES', len(dates), '  number of images used')
first_header['DATAMIN'] = data_min
first_header['DATAMAX'] = data_max
quadrant = remfits.revfn[filter_name]
first_header.set('FILTER', filter_name, " filter corresponding to " + quadrant + " quadrant")
first_header.set('FILENAME', "Generated flat for " + quadrant, ' filename of the image')
if len(intfiles) != 0:
    first_header['COMMENT'] = 'The following keywords refer to files used to build the image'
    histb = []
    while len(intfiles) != 0:
        nxt = []
        while len(intfiles) != 0 and len(nxt) < 4:
            nxt.append(intfiles.pop(0))
        histb.append(nxt)
    for n in histb:
        first_header['HISTORY'] = ",".join(n)

first_header['HISTORY'] = datetime.datetime.now().strftime("Created on %a %b %d %H:%M:%S %Y")

for todel in ('BZERO', 'BSCALE', 'BUNIT', 'BLANK'):
    try:
        del first_header[todel]
    except KeyError:
        pass
hdu = fits.PrimaryHDU(result, first_header)
try:
    hdu.writeto(outfile, overwrite=force, checksum=True)
except OSError:
    print("Could not write", outfile, file=sys.stderr)
    sys.exit(200)
