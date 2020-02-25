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
import re
import trimarrays
import miscutils
import math

filtfn = dict(BL='z', BR="r", UR="g", UL="i")
revfilt = dict()
for k, v in filtfn.items():
    revfilt[v] = k

qfilt = 'zrig'

fmtch = re.compile('([FB]).*([UB][LR])')

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Duplicate creation of master flat file ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='List of files to process')
parsearg.add_argument('--biasfile', type=str, required=True, help='Bias file to use"')
parsearg.add_argument('--outfile', type=str, required=True, help='Output FITS file')
parsearg.add_argument('--listfiles', type=str, help='File containing list of files to process with descriptions')
parsearg.add_argument('--filter', type=str, help='Specify filter otherwise deduced from files')
parsearg.add_argument('--stoperr', action='store_true', help='Stop processing if any files rejected')
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file or things queried')
parsearg.add_argument('--exptime', type=float, help='Ignore files which do not have given expossure time')
parsearg.add_argument('--derotang', type=float, help='Ignore files which do not have given derotation angle')

resargs = vars(parsearg.parse_args())
files = resargs['files']
biasfile = resargs['biasfile']
outfile = resargs['outfile']
listfiles = resargs['listfiles']
filter = resargs['filter']
stoperr = resargs['stoperr']
force = resargs['force']
exptime = resargs['exptime']
derotang = resargs['derotang']

bf = fits.open(biasfile)
bh = bf[0].header
biasdata = bf[0].data.astype(np.float32)

errors = 0

if bh['EXPTIME'] != 0:
    print(biasfile, "does not look like a bias file", file=sys.stderr)
    errors += 1

bf.close()

bfilt = None
if 'FILTER' in bh:
    bfilt = bh['FILTER']
else:
    try:
        fname = bh['FILENAME']
        mtch = fmtch.match(fname)
        if mtch is not None:
            typ, seg = mtch.groups()
            if typ != 'B':
                print(file, '"' + descr + '" filename', fname, "in bias file", biasfile, "Does not look like that of a bias file", file=sys.stderr)
                errors += 1
            bfilt = filtfn[seg]
    except KeyError:
        pass

if bfilt is not None:
    if filter is None:
        filter = bfilt
    elif filter != bfilt:
        print("bias file ", biasfile, "is for filter", bfilt, "not", filter, file=sys.stderr)
        errors += 1

if listfiles is not None:
    if len(files) != 0:
        print("Confused between --listfiles arg of", listfiles, "and file arguments", file=sys.stderr)
        sys.exit(10)
    try:
        lf = open(listfile)
    except OSError as e:
        print("Cannot open", listfile, "error was", e.strerror, file=sys.stderr)
        sys.exit(11)

    descrs = []
    for lin in lf:
        fn, descr = lin.split(" ", 1)
        files.append(fn)
        descrs.append(descr)
    lf.close()
elif len(files) == 0:
    print("No input files specfied", file=sys.stderr)
    sys.exit(12)
else:
    descrs = ['(no descr)'] * len(files)

intfiles = []  # Internal filenames
ims = []
hdrs = []
mjd = []

for file, descr in zip(files, descrs):
    try:
        ff = fits.open(file)
    except OSError as e:
        # FITS routines don't set up OSError correctly
        if e.strerror is None:
            print("File", file, '"' + descr + '" is not a valid FITS file', e, args[0], file=sys.stderr)
        else:
            print("Could not open", file, '"' + descr + '" error was', e.strerror, file=sys.stderr)
        errors += 1
        continue

    fhdr = ff[0].header
    fdat = ff[0].data

    ff.close()

    try:
        fname = fhdr['FILENAME']
    except KeyError:
        print("No filename found in", file, '"' + descr + '"', file=sys.stderr)
        errors += 1
        continue

    mtch = fmtch.match(fname)
    if mtch is None:
        print("Could not match filename", fname, "in", file, '"' + descr + '"', file=sys.stderr)
        errors += 1
        continue

    typ, seg = mtch.groups()
    if typ != 'F':
        print(file, '"' + descr + '" filename', fname, "Does not look like a flat file", file=sys.stderr)
        errors += 1
        continue
    nfilt = filtfn[seg]
    if filter is None:
        filter = nfilt
    elif filter != nfilt:
        print(file, '"' + descr + '" filename', fname, "appears to be flat file for filter", nfilt, "not", filter, file=sys.stderr)
        errors += 1
        continue

    try:
        if qfilt[fhdr['QUADID']] != filter:
            print(file, '"' + descr + '" filename', fname, "has unexpected quadrant for filter", qfilt[fhdr['QUADID']], "not", filter, file=sys.stderr)
            errors += 1
            continue
    except KeyError:
        print(file, '"' + descr + '" filename', fname, "has no quadrant setting", file=sys.stderr)
        errors += 1
        continue

    try:
        if fhdr['FILTER'] != filter:
            print(file, '"' + descr + '" filename', fname, "has unexpected filter", fhdr['FILTER'], "not", filter, file=sys.stderr)
            errors += 1
            continue
    except KeyError:
        print(file, '"' + descr + '" filename', fname, "has no FILTER keyword", file=sys.stderr)
        errors += 1
        continue

    try:
        mjdate = fhdr['MJD-OBS']
    except KeyError as e:
        print(file, '"' + descr + '" filename', fname, "header item missing", e.args[0], file=sys.stderr)
        errors += 1
        continue

    ims.append(fdat)
    intfiles.append(miscutils.removesuffix(fname))
    mjd.append(mjdate)
    hdrs.append(fhdr)

if len(ims) == 0:
    print("Aborting as no images to process", file=sys.stderr)
    sys.exit(1)

if errors != 0 and stoperr:
    print("Aborting doue to", errors, "error(s)", file=sys.stderr)
    sys.exit(2)

mjd = np.array(mjd)
ims = np.array(ims)

max_date = mjd.max()
min_date = mjd.min()

final_image = np.median(ims, axis=0).astype(np.float32)
final_image -= biasdata
trimmed_image = trimarrays.trimzeros(final_image)
final_image /= trimmed_image.mean()
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
