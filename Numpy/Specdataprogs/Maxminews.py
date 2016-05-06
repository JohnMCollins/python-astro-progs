#! /usr/bin/env python

import sys
import os
import os.path
import argparse
import jdate
import numpy as np

parsearg = argparse.ArgumentParser(description='List minimum and maximum EWs from EW file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ewfile', type=str, help='EW file', nargs=1)
parsearg.add_argument('--limit', type=float, default=20.0, help='Limit to display from')
parsearg.add_argument('--below', action='store_true', help='Display values below limit (otherwise above)')
parsearg.add_argument('--sortval', action='store_true', help='Sort by value not date')

resargs = vars(parsearg.parse_args())
limit = resargs['limit']
below = resargs['below']
sortval = resargs['sortval']

ewfile = resargs['ewfile'][0]

try:
    inf = np.loadtxt(ewfile, unpack=True)
    dates = inf[0]
    ews = inf[2]
except IOError as e:
    sys.stdout = sys.stderr
    print "Cannot load ew file", ewfile
    print "Error was:", e.args[0]
    sys.exit(100)
except ValueError, IndexError:
    sys.stdout = sys.stderr
    print "Cannot parse ew file", ewfile
    sys.exit(101)

if below:
    sel = ews < limit
else:
    sel = ews > limit

dates = dates[sel]
ews = ews[sel]

if len(dates) == 0:
    sys.exit(0)

if sortval:
    if below:
        ast = np.argsort(ews)
    else:
        ast = np.argsort(-ews)
    dates = dates[ast]
    ews = ews[ast]

for d, e in zip(dates, ews):
    dd = jdate.jdate_to_datetime(d)
    print "%s: %.3f" % (dd.strftime("%d/%m/%Y UTC %H:%M:%S"), e)
 
    