#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-23T14:20:00+01:00
# @Email:  jmc@toad.me.uk
# @Filename: dbobjdisp.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:02:43+00:00

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
import warnings
import miscutils
import remgeom

filtfn = dict(BL='z', BR="r", UR="g", UL="i")
fmtch = re.compile('([FBIm]).*([UB][LR])')


def getfilter(filename):
    """Get filter amd data from fits header"""
    global filtfn, filtfn

    try:
        ffile = fits.open(filename)
    except (FileNotFoundError, PermissionError):
        print("Cannot open file", filename, file=sys.stderr)
        sys.exit(10)

    fdata = ffile[0].data.astype(np.float32)
    fhdr = ffile[0].header
    ffile.close()

    # Try to get filter from header if there
    try:
        return  (fhdr['FILTER'], fdata)
    except KeyError:
        pass

    # Otherwise get it from file name

    try:
        fn = fhdr['FILENAME']
    except KeyError:
        print("Cannot discover filter from", filename, file=sys.stderr)
        sys.exit(11)

    fmt = fmtch.match(fn)
    if fmt is None:
        print("Cannot figure internal filename", fn, "from", filename, file=sys.stderr)
        sys.exit(12)
    ft, quad = fmt.groups()
    return (filtfn[quad], fdata)

#####
# Do the biz interpret ars, get files


rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Extract image array from FITS file possibly subtracting bias and dividing by flat', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs=1, help='File to process')
parsearg.add_argument('--outfile', type=str, required=True, help='Output file"')
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
biasfile = resargs['biasfile']
flatfile = resargs['flatfile']

filter, ifdata = getfilter(infile)
ilimit = rg.get_imlim(filter)
ifdata = ilimit.apply(ifdata)

if biasfile is not None:
    bfilt, bdata = getfilter(biasfile)
    if bfilt != filter:
        print("Bias file %s is filter type %s but input file %s is filter type %s" % (biasfile, bfilt, infile, filter), file=sys.stederr)
        sys.exit(11)
    bdata = ilimit.apply(bdata)
    ifdata -= bdata

if flatfile is not None:
    ffilt, fdata = getfilter(flatfile)
    if ffilt != filter:
        print("Flat file %s is filter type %s but input file %s is filter type %s" % (flatfile, ffilt, infile, filter), file=sys.stederr)
        sys.exit(12)
    fdata = ilimit.apply(fdata)
    ifdata *= fdata.mean()
    ifdata /= fdata

np.save(outfile, ifdata)
