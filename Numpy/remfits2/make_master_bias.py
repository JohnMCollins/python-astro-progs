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

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Create master bias file ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('iforbinds', nargs='*', type=str, help='Filenames or iforbinds to process, otherwise use stdin')
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--outfile', type=str, required=True, help='Output FITS file')
parsearg.add_argument('--filter', type=str, help='Specify filter otherwise deduced from files')
parsearg.add_argument('--stoperr', action='store_true', help='Stop processing if any files rejected')
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file')
parsearg.add_argument('--usemean', action='store_true', help='Use mean of values rather than median')
parsearg.add_argument('--baseid', type=int, help='ID to use for constructing FITS file if possible')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['iforbinds']
outfile = resargs['outfile']
filter = resargs['filter']
stoperr = resargs['stoperr']
force = resargs['force']
usemean = resargs['usemean']
baseid = resargs['baseid']

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(50)

idlist, errors = cols_from_file.ids_from_file_list(files)

if len(idlist) == 0:
    print("No IDs to preocess", errors, "errors", file=sys.stderr)
    sys.exit(99)

mydb, mycurs = remdefaults.opendb()

# If none given as base, use first one

sidlist = set(idlist)

if baseid is None or baseid not in sidlist:
    baseid = idlist[0]

# This manoeuvre is to eliminate duplicates

idlist = sorted(list(sidlist))

ffiles = []
dims = None
starts = None

basef = None

for id in idlist:
    try:
        rf = remfits.RemFits()
        rf.load_from_iforbind(mycurs, id)
    except remfits.RemFitsErr as e:
        print("Loading from", id, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    if rf.ftype != "Daily bias":
        print("File type of", id, "is", rf.ftype, "not bias", file=sys.stderr)
        errors += 1
        continue
    if filter is None:
        filter = rf.filter
    elif rf.filter != filter:
        print("Filter of", id, "is", rf.filter, "but using", filter, file=sys.stderr)
        errors += 1
        continue
    if dims is None:
        dims = (rf.ncolumns, rf.nrows)
    elif dims != (rf.ncolumns, rf.nrows):
        print("Dimensions of", id, "are", (rf.ncolumns, rf.nrows), "whereas previous are", dims, file=sys.stderr)
        errors += 1
        continue
    if starts is None:
        starts = (rf.startx, rf.starty)
    elif starts != (rf.startx, rf.starty):
        print("Starts of", id, "are", (rf.startx, rf.starty), "whereas previous are", starts, file=sys.stderr)
        errors += 1
        continue
    if id == baseid:
        basef = rf
    ffiles.append(rf)

if (errors > 0  and  stoperr) or len(ffiles) == 0:
    print("Stopping due to", errors, "-", len(ffiles), "files loaded", file=sys.stderr)
    sys.exit(100)

# If we lost the indication, then just reset to first one

if basef is None:
    print("Selected baseid lost, using first available", file=sys.stderr)
    basef = ffiles[0]

first_header = basef.hdr

arrblock = []
temps = []
dates = []
for ff in ffiles:
    arrblock.append(ff.data)
    temps.append(ff.ccdtemp)
    dates.append(ff.date)
arrblock = np.array(arrblock)

if usemean:
    result = arrblock.mean(axis=0)
else:
    result = np.median(arrblock, axis=0)
data_min = result.min()
data_max = result.max()
min_date = Time(min(dates))
max_date = Time(max(dates))
rrows, rcols = result.shape
result = np.pad(result, ((0, 1024 - rrows), (0, 1024 - rcols)), 'constant')

first_header.set('DATE_MIN', str(min_date.isot), ' (UTC) start date of used bias frames')
first_header.set('DATE_MAX', str(max_date.isot), ' (UTC) end date of used bias frames')
first_header.set('MJD_MIN', min_date.mjd, ' [day] start MJD of used bias frames')
first_header.set('MJD_MAX', max_date.mjd, ' [day] end MJD of used bias frames')
first_header.set('N_IMAGES', len(ffiles), '  number of images used')
first_header['DATAMIN'] = data_min
first_header['DATAMAX'] = data_max
quadrant = remfits.revfn[filter]
first_header.set('FILTER', filter, " filter corresponding to " + quadrant + " quadrant")
first_header.set('FILENAME', "Combined bias for " + quadrant, ' filename of the image')
first_header.set('CCDTEMP', np.median(temps), ' [C] median value of CCD Temp of used images')

first_header['HISTORY'] = datetime.datetime.now().strftime("Created on %a %b %d %H:%M:%S %Y")

hdu = fits.PrimaryHDU(result, first_header)
try:
    hdu.writeto(outfile, overwrite=force, checksum=True)
except OSError:
    print("Could not write", outfile, file=sys.stderr)
    sys.exit(200)
