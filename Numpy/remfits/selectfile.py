#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-24T22:41:12+01:00
# @Email:  jmc@toad.me.uk
# @Filename: listobs.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:00:35+00:00

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import argparse
import datetime
import re
import sys
import warnings
import remgeom
import trimarrays
import numpy as np
import scipy.stats as ss

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

filtfn = dict(BL='z', BR="r", UR="g", UL="i")

fmtch = re.compile('([FBI]).*([UB][LR])')


def parsepair(arg):
    """Parse an argument pair of the form a:b with a and b optional"""

    if arg is None:
        return  None
    bits = arg.split(':')
    if len(bits) != 2:
        print("Cannot understand", name, "arg expection m:n with either number opptional", file=sys.stderr);
        sys.exit(21)
    lov, hiv = bits
    if len(lov) != 0:
        lov = float(lov)
    else:
        lov = -1e60
    if len(hiv) != 0:
        hiv = float(hiv)
    else:
        hiv = 1e60
    return  (lov, hiv)


parsearg = argparse.ArgumentParser(description='Select flat or bias files by restrictions',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='List of files to select grom')
parsearg.add_argument('--fromdate', type=str, help='From:to dates')
parsearg.add_argument('--todate', type=str, help='From:to dates')
parsearg.add_argument('--filter', type=str, nargs='+', help='filters to limit to')
parsearg.add_argument('--type', type=str, default='any', help='Type wanted flat, bias, any')
parsearg.add_argument('--minval', type=str, help='Minimum value to restrict to as m:n')
parsearg.add_argument('--maxval', type=str, help='Maximum value to restrict to as m:n')
parsearg.add_argument('--median', type=str, help='Median value to restrict to as m:n')
parsearg.add_argument('--mean', type=str, help='Meanv value to restrict to as m:n')
parsearg.add_argument('--std', type=str, help='Stde dev value to restrict to as m:n')
parsearg.add_argument('--skew', type=str, help='Skew value to restrict to as m:n')
parsearg.add_argument('--kurt', type=str, help='Kurtosis value to restrict to as m:n')
parsearg.add_argument('--trim', type=int, default=100, help='Ammount to trim each side')

resargs = vars(parsearg.parse_args())

files = resargs['files']
fromdate = resargs['fromdate']
todate = resargs['todate']
filters = resargs['filter']
typereq = resargs['type'][0].upper()
minval = resargs['minval']
maxval = resargs['maxval']
medians = resargs['median']
means = resargs['mean']
stds = resargs['std']
skews = resargs['skew']
kurts = resargs['kurt']
trimsides = resargs['trim']

mangling_data = minval is not None or maxval is not None or medians is not None or means is not None or stds is not None or skews is not None or kurs is not None
try:
    if fromdate is not None:
        fromdate = parsetime.parsetime(fromdate)
    if todate is not None:
        todate = parsetime.parsetime(todate, True)
except ValueError:
    sys.exit(10)

minval = parsepair(minval)
maxval = parsepair(maxval)
medians = parsepair(medians)
means = parsepair(means)
stds = parsepair(stds)
skews = parsepair(skews)
kurts = parsepair(kurts)

for file in files:

    try:
        ff = fits.open(file)
    except OSError as e:
        print("Cannot open", file, e.strerror, file=sys.stderr)
        continue

    hdr = ff[0].header
    fdat = ff[0].data
    ff.close()

    # Check it meets filter requirements

    ffilt = None
    try:
        ffilt = hdr['FILTER']
        if filters is not None and ffilt not in filters:
            continue
    except KeyError:
        pass

    # Check it meets file type requirements or filter type if not found in file already

    if (ffilt is None and filters is not None) or typereq != 'A':
        try:
            ifname = hdr['FILENAME']
        except KeyError:
            print("Cannot find internal file name in", file, file=sys.stderr)
            continue
        m = fmtch.match(ifname)
        if m is None:
            print("Cannot match internal file name", ifname, "in", file, file=sys.stderr)
            continue
        ift, quad = m.groups()
        if typereq != 'A' and ift != typereq:
            continue
        if filters is not None and filtfn[quad] not in filters:
            continue

    # Compare dates if we need them

    if fromdate is not None or todate is not None:
        try:
            dat = Time(fhdr['DATE_OBS']).datetime
        except KeyError:
            print("No date found in", file, file=sys.stderr)
            continue
        if fromdate is not None and dat < fromdate:
            continue
        if todate is not None and dat > todate:
            continue

    if mangling_data:
        fdat = trimarrays.trimzeros(trimarrays.trimnan(fdat))
        if  trimsides > 0:
            fdat = fdat[trimsides:-trimsides, trimsides:-trimsides]
        fdat = fdat.flatten()
        if minval is not None:
            mv = fdat.min()
            if mv < minval[0] or mv > minval[1]:
                continue
        if maxval is not None:
            mv = fdat.min()
            if mv < maxval[0] or mv > maxval[1]:
                continue
        if medians is not None:
            mv = np.median(fdat)
            if mv < medians[0] or mv > medians[1]:
                continue
        if means is not None:
            mv = fdat.mean()
            if mv < means[0] or mv > means[1]:
                continue
        if stds is not None:
            mv = fdat.std()
            if mv < stds[0] or mv > stds[1]:
                continue
        if skews is not None:
            mv = ss.skew(fdat)
            if mv < skews[0] or mv > skews[1]:
                continue
        if kurts is not None:
            mv = ss.kurtosis(fdat)
            if mv < kurts[0] or mv > kurts[1]:
                continue

    # OK passed all checks writer it out

    print(file)
