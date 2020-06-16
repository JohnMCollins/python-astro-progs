#! /usr/bin/env python3

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import math
import numpy as np
import argparse
import sys
import re
import os.path
import datetime
import warnings
import miscutils
import remgeom
import remfitshdr
import remdefaults
import dbops
import dbremfitsobj


def getfilter(filename):
    """Get filter amd data from fits header"""

    global mydbname, tmpdir, dbase, dbcurs

    if filename.isdecimal():
        if dbase is None:
            try:
                os.chdir(tmpdir)
            except FileNotFoundError:
                print("Unable to select temporary directory", tmpdir, file=sys.stderr)
                sys.exit(100)
            try:
                dbase = dbops.opendb(mydbname)
                dbcurs = dbase.cursor()
            except dbops.dbopsError as e:
                print("Could not open database", mydbname, "error was", e.args[0], file=sys.stderr)
                sys.exit(101)
        try:
            ffile = dbremfitsobj.getfits(dbcurs, int(filename))
        except dbremfitsobj.RemObjError as e:
            print("Cannot open FITS id", file, e.args[0], file=sys.stderr)
            sys.exit(102)
        except OSError as e:
            print("Cannot open FITS id", file, "error was", e.args[1], file=sys.stderr)
            sys.exit(103)
    else:
        try:
            ffile = fits.open(filename)
        except (FileNotFoundError, PermissionError):
            print("Cannot open file", filename, file=sys.stderr)
            sys.exit(105)

    fdata = ffile[0].data.astype(np.float32)
    fhdr = ffile[0].header
    try:
        fhs = remfitshdr.RemFitsHdr(fhdr)
    except remfitshdr.RemFitsHdrErr as e:
        print("Header error file", filename, "error was", e.args[0], file=sys.stderr)
        sys.exit(106)
    return  (fhs.filter, fhdr, fdata)

#####
# Do the biz interpret ars, get files


rg = remgeom.load()
tmpdir = remdefaults.get_tmpdir()
mydbname = remdefaults.default_database()

parsearg = argparse.ArgumentParser(description='Extract image array from FITS file possibly subtracting bias and dividing by flat', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs=1, help='File to process')
parsearg.add_argument('--outfile', type=str, required=True, help='Output file"')
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use if needed')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files if needed')
parsearg.add_argument('--asfits', action='store_true', help='Save result as FITS file (conver to 32-bit float perhaps)')
parsearg.add_argument('--force', action='store_true', help='Force overwrite existing file')
parsearg.add_argument('--biasfile', type=str, help='Bias file to subtract if required')
parsearg.add_argument('--flatfile', type=str, help='Flat file to divide if required')

resargs = vars(parsearg.parse_args())

# The reason why we don't get RA and DECL info out of this is because we have
# to adjust for proper motion which requires Python 3 (as the versions of astropy that
# support it only run with that)

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

infile = resargs['file'][0]
outfile = resargs['outfile']
mydbname = resargs['database']
tmpdir = resargs['tempdir']
biasfile = resargs['biasfile']
flatfile = resargs['flatfile']
asfits = resargs['asfits']
force = resargs['force']

orig_dir = os.getcwd()

filter, fhdr, ifdata = getfilter(infile)
ilimit = rg.get_imlim(filter)
ifdata = ilimit.apply(ifdata)

if biasfile is not None:
    bfilt, bhdr, bdata = getfilter(biasfile)
    if bfilt != filter:
        print("Bias file %s is filter type %s but input file %s is filter type %s" % (biasfile, bfilt, infile, filter), file=sys.stederr)
        sys.exit(11)
    bdata = ilimit.apply(bdata)
    ifdata -= bdata

if flatfile is not None:
    ffilt, flhdr, fdata = getfilter(flatfile)
    if ffilt != filter:
        print("Flat file %s is filter type %s but input file %s is filter type %s" % (flatfile, ffilt, infile, filter), file=sys.stederr)
        sys.exit(12)
    fdata = ilimit.apply(fdata)
    ifdata *= fdata.mean()
    ifdata /= fdata

if asfits:
    outfile = miscutils.addsuffix(outfile, ".fits.gz")
else:
    outfile = miscutils.addsuffix(outfile, ".npy")

outfile = os.path.join(orig_dir, outfile)

if os.path.exists(outfile):
    if force:
        try:
            os.unlink(outfile)
        except OSError as e:
            print("Could not remove old", outfile, "error was", e.args[1], file=sys.stderr)
            sys.exit(30)
    else:
        print("Will not remove existing", outfile, "use --force if needed", file=sys.stderr)
        sys.exit(31)

if asfits:
    for todel in ('BZERO', 'BSCALE', 'BUNIT', 'BLANK'):
        try:
            del fhdr[todel]
        except KeyError:
            pass
    fhdr['DATAMIN'] = ifdata.min()
    fhdr['DATAMAX'] = ifdata.max()
    fhdr['IMAGEH'] = fhdr['NAXIS1'] = ifdata.shape[1]
    fhdr['IMAGEW'] = fhdr['NAXIS2'] = ifdata.shape[0]
    fhdr['HISTORY'] = datetime.datetime.now().strftime("Created on %a %b %d %H:%M:%S %Y")
    hdu = fits.PrimaryHDU(ifdata, fhdr)
    try:
        hdu.writeto(outfile, overwrite=True, checksum=True)
    except OSError:
        print("Could not write", outfile, file=sys.stderr)
        sys.exit(200)
else:
    np.save(outfile, ifdata)
