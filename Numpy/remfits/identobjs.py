#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:56+00:00
# @Email:  jmc@toad.me.uk
# @Filename: identobjs.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:07:16+00:00


from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import numpy as np
import argparse
import sys
import string
import objcoord
import warnings

def dispres(r, d, rr, alld):
    if r is None:
        print(" " * 20, end=' ')
    else:
        print("%9.4f %9.4f:" % (r, d), end=' ')
    mo, alts, ot = rr
    if not alld:
        print(mo)
        return
    print(mo, ot)
    for al in alts:
        print(" " * 20, al)


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Identify objects from ooords', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs=1, help='Coord file to process')
parsearg.add_argument('--radius', type=float, help='Search radius', default=2.0)
parsearg.add_argument('--alldata', action='store_true', help='Show all data')
parsearg.add_argument('--allobjs', action='store_true', help='Show all targets')

resargs = vars(parsearg.parse_args())
ffname = resargs['file'][0]
radius = resargs['radius']
alld = resargs['alldata']
allo = resargs['allobjs']

coords = np.loadtxt(ffname)

for lin in coords:
    r, d = lin
    res = objcoord.coord2objs(r, d, radius, True)
    if len(res) == 0:
        print("%9.4f %9.4f: None Found" % (r, d))
        continue
    if allo:
        rc = r
        dc = d
        for rr in res:
            dispres(rc, dc, rr, alld)
            rc = None
            dc = None
    else:
        dispres(r, d, res[0], alld)
