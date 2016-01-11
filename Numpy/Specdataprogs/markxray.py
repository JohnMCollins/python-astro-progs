#! /usr/bin/env python

# Apply X-ray file to UVES data to mark

import sys
import os
import re
import os.path
import locale
import argparse
import numpy as np
import scipy.interpolate as si
import xml.etree.ElementTree as ET
import miscutils
import xmlutil
import specinfo
import jdate
import datetime

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process UVES data marking spectra to be omitted where Xray level exceeds given', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--inctrl', type=str, help='Input control file', required=True)
parsearg.add_argument('--outctrl', type=str, help='Output control file', required=True)
parsearg.add_argument('--xrayfile', type=str, help='Xray data file', required=True)
parsearg.add_argument('--xraylevel', type=float, help='Level of xray activity at which we discount data', required=True)
parsearg.add_argument('--deflevel', type=float, default=0.0, help='Default level of X-ray for points outside time range')
parsearg.add_argument('--date', type=str, help='Date on points to apply', required=True)
parsearg.add_argument('--barycentric', action='store_true', help='Use barycentric date/time now obs date/time')
parsearg.add_argument('--overwrite', action='store_true', help='Replace any existing markers where already excluded')

resargs = vars(parsearg.parse_args())

inctrl = miscutils.replacesuffix(resargs['inctrl'], specinfo.SUFFIX)
outctrl = miscutils.replacesuffix(resargs['outctrl'], specinfo.SUFFIX)
xrayfile = resargs['xrayfile']
xraylevel = resargs['xraylevel']
deflevel = resargs['deflevel']
date = resargs['date']
barycent = resargs['barycentric']
overwrite = resargs['overwrite']

errors = 0

if not os.path.exists(inctrl):
    sys.stdout = sys.stderr
    print "Cannot find input control file", inctrl
    errors += 1
if not os.path.exists(xrayfile):
    sys.stdout = sys.stderr
    print "Cannot find xreay file", outctrl
    errors += 1

dm = re.match('(\d+)/(\d+)/(\d+)', date)
if not dm:
    sys.stdout = sys.stderr
    print "Invalid date format", date
    errors += 1

dday, dmon, dyear = map(lambda x: int(x), dm.groups())

if dyear < 60:
    if dyear < 20:
        dyear += 2000
    else:
        dyear += 1900
try:
    dt = datetime.date(dyear, dmon, dday)
    dt -= datetime.timedelta(days=2)
except ValueError:
    sys.stdout = sys.stderr
    print "Cannot interpret date", date
    errors += 1

if errors > 0:
    print "Aborting due to missing files"
    sys.exit(1)

xray_amp, xray_err, xray_time = np.loadtxt(xrayfile, unpack=True)
xray_time %= SECSPERDAY
interpfn = si.interp1d(xray_time, xray_amp, kind='cubic', bounds_error=False, fill_value=deflevel, assume_sorted=True)

# Load up starting control file

try:
    sinf = specinfo.SpecInfo()
    sinf.loadfile(inctrl)
    speclist = sinf.get_ctrlfile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Load control file data error", e.args[0]
    sys.exit(3)

existing_marked = 0
new_marked = 0
number_spec = len(speclist.datalist)
markmessage = 'Xray level >= %g' % xraylevel

for spec in speclist.datalist:
    reldate = spec.modjdate
    if barycent:
        reldate = spec.modbjdate
    dt_dt = jdate.jdate_to_datetime(reldate)
    dt_date = dt_dt.date()
    if dt_date != dt:
        continue
    if spec.discount:
        existing_marked += 1
        if not overwrite:
            continue
    timeoffs = (reldate * SECSPERDAY) % SECSPERDAY
    xrv = interpfn(timeoffs)
    if xrv >= xraylevel:
        new_marked += 1
        spec.discount = True
        spec.remarks = markmessage

try:
    sinf.set_ctrlfile(speclist)
    sinf.savefile(outctrl)
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Save control file error", e.args[0]
    sys.exit(4)

print "Completed with %d spectra, %d originally marked %d newly marked" % (number_spec, existing_marked, new_marked)
