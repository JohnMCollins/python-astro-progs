#!  /usr/bin/env python3

""""Geometry selection for scripts"""

import sys
import datetime
import argparse
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import parsetime
import remdefaults
import remfits

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
# warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Shell utility to aid selection of geometry ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('date', nargs=1, type=str, help='Date in question or fits file')
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
parsearg.add_argument('--fromfile', action='store_true', help='Argument is fits file not date')
parsearg.add_argument('--changeover', action='store_true', help='Exit code for switchover month')
parsearg.add_argument('--after', action='store_true', help='If on cusp give later parameters')
parsearg.add_argument('--filter', type=str, choices=('g', 'i', 'r', 'z'), help='Filter name')
parsearg.add_argument('--specday', type=int, help='Specify day of month in output file name rather than date <0 means omit')

resargs = vars(parsearg.parse_args())
seldate = resargs['date'][0]
fromfile = resargs['fromfile']
remdefaults.getargs(resargs)
flip = resargs['changeover']
filter_name = resargs['filter']
after = resargs['after']
tday = resargs['specday']

on_cusp = False

if fromfile:
    db, cu = remdefaults.opendb()
    try:
        ff = remfits.parse_filearg(seldate, cu)
    except remfits.RemFitsErr as e:
        print("Could not open", seldate, e.args[0], file=sys.stderr)
        sys.exit(20)
    if filter_name is not None and filter_name != ff.filter:
        print("Specified Filter of", filter_name, "is wrong for", seldate, "which is", seldate.filter, file=sys.stderr)
        sys.exit(21)
    filter_name = ff.filter
    seldate = ff.date
    startx = ff.startx
    tdate = (seldate.year, seldate.month)
    if tdate != (2019, 3):
        is_after = tdate > (2019, 3)
    else:
        on_cusp = True
        is_after = startx == remdefaults.get_geom(seldate + datetime.timedelta(days=31), filter_name)[0]
else:
    if filter_name is None:
        print("Have to specify filter unless parsing file", file=sys.stderr)
        sys.exit(22)
    try:
        seldate = parsetime.parse_datetime(seldate)
    except ValueError:
        print("Cannot understand date", seldate, file=sys.stderr)
        sys.exit(10)
    tdate = (seldate.year, seldate.month)
    if tdate != (2019, 3):
        is_after = tdate > (2019, 3)
        spec_startx = remdefaults.get_geom(seldate, filter_name)
    else:
        on_cusp = True
        if after:
            is_after = True
            spec_startx = remdefaults.get_geom(seldate + datetime.timedelta(days=31), filter_name)
        else:
            is_after = False
            spec_startx = remdefaults.get_geom(seldate - datetime.timedelta(days=31), filter_name)
    startx = spec_startx[0]

if flip:
    if on_cusp:
        sys.exit(0)
    sys.exit(1)

if tday is None:
    pday = "{:02d}".format(seldate.day)
elif tday < 0:
    pday = ""
else:
    pday = "{:02d}".format(tday)
seq = '1'
if is_after:
    seq = '2'

for descr, ftype in (('biasfile', 'b'), ('flatfile', 'f')):
    print("{:s}={:s}{:s}{:s}-{:d}{:02d}{:s}".format(descr, filter_name, ftype, seq, seldate.year, seldate.month, pday))
print("startx={:d}".format(startx))
print("day={:d}\nmonth={:d}\nyear={:d}".format(seldate.day, seldate.month, seldate.year))
if tday is not None:
    print("specday={:d}".format(tday))
print("filt={:s}".format(filter_name))
sys.exit(0)
