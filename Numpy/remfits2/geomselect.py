#!  /usr/bin/env python3

""""Geometry selection for scripts"""

import sys
import datetime
import argparse
import parsetime
import remdefaults

parsearg = argparse.ArgumentParser(description='Shell utility to aid selection of geometry ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('date', nargs=1, type=str, help='Date in question')
remdefaults.parseargs(parsearg, tempdir=False, libdir=False, database=False)
parsearg.add_argument('--changeover', action='store_true', help='Exit code for switchover month')
parsearg.add_argument('--outfile', action='store_true', help='Output file name')
parsearg.add_argument('--geometry', action='store_true', help='Output gemetry parameter')
parsearg.add_argument('--after', action='store_true', help='If on cusp give later parameters')
parsearg.add_argument('--filter', type=str, choices=('g', 'i', 'r', 'z'), required=True, help='Filter name')
parsearg.add_argument('--type', type=str, choices=('f', 'b'), default='b', help='File type')

resargs = vars(parsearg.parse_args())
seldate = resargs['date'][0]
remdefaults.getargs(resargs)
flip = resargs['changeover']
outfile = resargs['outfile']
badpix = resargs['geometry']
filter_name = resargs['filter']
after = resargs['after']
ftype = resargs['type']

try:
    seldate = parsetime.parsetime(seldate)
except ValueError:
    print("Cannot understand date", seldate, file=sys.stderr)
    sys.exit(10)

spec_startx = remdefaults.get_geom(seldate, filter_name)
on_cusp = False
if seldate.year > 2019:
    is_after = True
elif seldate.year < 2019:
    is_after = False
elif seldate.month < 3:
    is_after = False
elif seldate.month > 3:
    is_after = True
else:
    on_cusp = True
    if after:
        is_after = True
        spec_startx = remdefaults.get_geom(seldate + datetime.timedelta(days=31), filter_name)
    else:
        is_after = False
        spec_startx = remdefaults.get_geom(seldate - datetime.timedelta(days=31), filter_name)

if flip:
    if on_cusp:
        sys.exit(0)
    sys.exit(1)

if outfile:
    seq = 'a'
    if is_after:
        seq = 'b'
    print("{:s}{:s}{:s}.{:d}.{:d}".format(filter_name, ftype, seq, seldate.year, seldate.month))
    sys.exit(0)

print(spec_startx[0])
sys.exit(0)
