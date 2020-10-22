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

parsearg = argparse.ArgumentParser(description='Duplicate creation of master flat file ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('iforbinds', nargs='*', type=str, help='Filenames or ids to process, otherwise use stdin')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--biasfile', type=str, required=True, help='Bias file to use"')
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
filter = resargs['filter']
stoperr = resargs['stoperr']
force = resargs['force']
baseid = resargs['baseid']

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(50)

idlist, errors = col_from_file.ids_from_file_list(files)

if len(idlist) == 0:
    print("No IDs to preocess", errors, "errors", file=sys.stderr)
    sys.exit(99)

biasstr = remfits.RemFits()
try:
    biasstr.load_from_fits(biasfile)
except remfits.RemFitsErr as e:
    print("Bias file", biasfile, "gave error", e.args[0], file=sys.stderr)
    sys.exit(10)

if biasstr.ftype != 'Daily bias' and biasstr.ftype != 'Combined bias':
    print(biasfile, "is", biasstr.ftype, "not a bias file", file=sys.stderr)
    sys.exit(11)

if filter is None:
    filter = biasstr.filter
elif filter != biasstr.filter:
    print(biasfile, "is for filter", biasstr.filter, "but filter given as", filter, file=sys.stderr)
    sys.exit(12)

Bdims = (biasstr.ncolumns, biasstr.nrows)
Bstarts = (biasstr.startx, biasstr.starty)
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

sidlist = set(idlist)
if baseid is None or baseid not in sidlist:
    baseid = idlist[0]
# This manoeuvre is to eliminate duplicates
idlist = sorted(list(sidlist))

# Now load up daily flats

mydb, mycurs = remdefaults.opendb()

ffiles = []
usedids = []
basef = None

for id in idlist:
    try:
        rf = remfits.RemFits()
        rf.load_from_iforbind(mycurs, id)
    except remfits.RemFitsErr as e:
        print("Loading from", id, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    if rf.ftype != "Daily flat":
        print("File type of", id, "is", rf.ftype, "not flat", file=sys.stderr)
        errors += 1
        continue
    if rf.filter != filter:
        print("Filter of", id, "is", rf.filter, "but using", filter, file=sys.stderr)
        errors += 1
        continue
    if Bdims != (rf.ncolumns, rf.nrows):
        print("Dimensions of", id, "are", (rf.ncolumns, rf.nrows), "whereas previous are", Bdims, file=sys.stderr)
        errors += 1
        continue
    if Bstarts != (rf.startx, rf.starty):
        print("Starts of", id, "are", (rf.startx, rf.starty), "whereas previous are", Bstarts, file=sys.stderr)
        errors += 1
        continue
    if id == baseid:
        basef = rf
    ffiles.append(rf)
    usedids.append(id)

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
for id, ff in zip(usedids, ffiles):
    dat = ff.data - biasdata
    prebadpm.append(np.count_nonzero(dat <= 0.0))
    if badpixmask is not None:
        dat[badpixmask] = 1.0
    postbadpm.append(np.count_nonzero(dat <= 0.0))
    arrblock.append(dat)
    temps.append(ff.ccdtemp)
    dates.append(ff.date)

arrblock = np.array(arrblock)

for id, ff, pre, post in zip(usedids, ffiles, prebadpm, postbadpm):
    print("%10d %5d %5d" % (id, pre, post))

sys.exit(0)

rimmed_image.mean()
ffin = final_image.flatten()
ffin = ffin[ffin > 0.0]
data_min = ffin.min()
data_max = ffin.max()

final_image[final_image <= 0.0] = math.nan

first_header = hdrs[0]

first_header.set('DATE_MIN', str(Time(min_date, format='mjd', precision=0).isot), ' (UTC) start date of used flat frames')
first_header.set('DATE_MAX', str(Time(max_date, format='mjd', precision=0).isot), ' (UTC) end date of used flat frames')
first_header.set('MJD_MIN', min_date, ' [day] start MJD of used flat frames')
first_header.set('MJD_MAX', max_date, ' [day] end MJD of used flat frames')
first_header.set('N_IMAGES', len(mjd), '  number of images used')
first_header['DATAMIN'] = data_min
first_header['DATAMAX'] = data_max
first_header.set('FILENAME', miscutils.removesuffix(outfile), ' filename of this median image')
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
hdu = fits.PrimaryHDU(final_image, first_header)
try:
    hdu.writeto(outfile, overwrite=force, checksum=True)
except OSError:
    print("Could not write", outfile, file=sys.stderr)
    sys.exit(200)
