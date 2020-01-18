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
parsearg.add_argument('--outfile', type=str, required=True, help='Output FITS file')
parsearg.add_argument('--listfiles', type=str, help='File containing list of files to process with descriptions')
parsearg.add_argument('--filter', type=str, help='Specify filter otherwise deduced from files')
parsearg.add_argument('--stoperr', action='store_true', help='Stop processing if any files rejected')
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file')
parsearg.add_argument('--exptime', type=float, help='Ignore files which do not have given expossure time')
parsearg.add_argument('--derotang', type=float, help='Ignore files which do not have given derotation angle')

resargs = vars(parsearg.parse_args())
files = resargs['files']
outfile = resargs['outfile']
listfiles = resargs['listfiles']
filter = resargs['filter']
stoperr = resargs['stoperr']
force = resargs['force']
exptime = resargs['exptime']
derotang = resargs['derotang']

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

errors = 0
med = []
ave = []
sd = []
temp = []
mjd = []
hdrs = []
ims = []

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
    
    # OK Checked everything not let's do the biz
    
    trimdata = trimarrays.trimzeros(fdat)
    
    try:
        temperature = fhdr['CCDTEMP']
        mjdate = fhdr['MJD-OBS']
    except KeyError as e:
        print(file, '"' + descr + '" filename', fname, "header item missing", e.args[0], file=sys.stderr)
        errors += 1
        continue
    med.append(np.median(trimdata))
    ave.append(np.mean(trimdata))
    sd.append(np.std(trimdata))
    temp.append(temperature)
    mjd.append(mjdate)
    hdrs.append(fhdr)
    ims.append(fdat)

if len(ims) == 0:
    print("Aborting as no images to process", file=sys.stderr)
    sys.exit(1)

if errors != 0 and stoperr:
    print("Aborting doue to", errors, "error(s)", file=sys.stderr)
    sys.exit(2)

med = np.array(med)
ave = np.array(ave)
sd = np.array(sd)
temp = np.array(temp)
mjd = np.array(mjd)

sd_e = np.median(sd)
med_e = np.median(med)

# May want to parameterise the 3 below, just copying for now

prune = np.abs(ave - med_e) < 3 * sd_e

temp = temp[prune]
mjd = mjd[prune]
hdrs = [h for h, p in zip(hdrs, prune) if p]
ims = [i for i, p in zip(ims, prune) if p]

if len(ims) == 0:
    print("After pruning to 3 * stddev - aborting as no images to process", file=sys.stderr)
    sys.exit(3)

max_date = mjd.max()
min_date = mjd.min()
temp_e = np.median(temp)

final_image = np.median(ims, axis=0)

if asfloat:
    final_image = final.image.astype(np.float32)
else:
    final_image += 0.5  # Because it trunacates
    final_image = final_image.astype(np.uint16)

trimmed_image = trimarrays.trimzeros(final_image)
data_min = trimmed_image.min()
data_max = trimmed_image.max()

first_header = hdrs[0]

first_header.set('DATE_MIN', str(Time(min_date, format='mjd', precision=0).isot), ' (UTC) start date of used bias frames')
first_header.set('DATE_MAX', str(Time(max_date, format='mjd', precision=0).isot), ' (UTC) end date of used bias frames')
first_header.set('MJD_MIN', min_date, ' [day] start MJD of used bias frames')
first_header.set('MJD_MAX', max_date, ' [day] end MJD of used bias frames')
first_header.set('N_IMAGES', len(mjd), '  number of images used')
first_header['DATAMIN'] = data_min
first_header['DATAMAX'] = data_max
first_header.set('FILTER', filter, " filter corresponding to " + revfilt[filter] + " quadrant")
first_header.set('FILENAME', miscutils.removesuffix(outfile), ' filename of this median image')
first_header.set('CCDTEMP', temp_e, ' [C] median value of CCD Temp of used images')

first_header['HISTORY'] = datetime.datetime.now().strftime("Created on %a %b %d %H:%M:%S %Y") 
hdu = fits.PrimaryHDU(final_image, first_header)
try:
    hdu.writeto(outfile, overwrite=force, checksum=True)
except OSError:
    print("Could not write", outfile, file=sys.stderr)
    sys.exit(200)
