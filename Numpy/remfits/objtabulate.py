#! /usr/bin/env python

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import math
import numpy as np
import argparse
import sys
import datetime
import os.path
import string
import objcoord
import trimarrays
import wcscoord
import warnings
import miscutils
import objinfo
import findnearest
import findbrightest
import calcadus
import parsetime
import remfitsobj

def pmjdate(arg):
    """Grab mjd from arg if possible"""
    if arg is None:
        return None
    try:
        t = Time(parsetime.parsetime(arg))
    except ValueError:
        print >>sys.stderr, "Could not understand time arg", arg
        sys.exit(50)
    return  t.mjd

class duplication(Exception):
    """Throw to get out of duplication loop"""
    pass

parsearg = argparse.ArgumentParser(description='Tabulate ADUs from FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('results', type=str, nargs=1, help='XML file of found objects updated with results')
parsearg.add_argument('--outfile', type=str, required=True, help='Output table file')
parsearg.add_argument('--filter', type=str, help='Filter to select', required=True)
parsearg.add_argument('--firstdate', type=str, help='First date to prcoess')
parsearg.add_argument('--lastdate', type=str, help='Last date to process')
parsearg.add_argument('--refobjs', type=str, nargs='+', help='Reference objects')

resargs = vars(parsearg.parse_args())

# The reason why we don't get RA and DECL info out of this is because we have
# to adjust for proper motion which requires Python 3 (as the versions of astropy that
# support it only run with that)

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

resultsfile = resargs['results'][0]
results = remfitsobj.RemobjSet()
try:
    results.loadfile(resultsfile)
except remfitsobj.RemObjError as e:
    print >>sys.stderr,  "Error loading results file", resultsfile, e.args[0]
    sys.exit(30)

target = results.targname
if target is None:
    print >>sys.stderr, "Results file", resultsfile, "does not have target"
    sys.exit(31)

firstdate = pmjdate(resargs['firstdate'])
lastdate = pmjdate(resargs['lastdate'])
filter = resargs['filter']
outfile = resargs['outfile']
refobjs = resargs['refobjs']

ncols = 5 + len(refobjs) * 2

nc = 5
colnums = dict()
for r in refobjs:
    colnums[r] = nc
    nc+=2

# Get list of observations and found objects

oblist = results.getobslist(filter = filter, firstdate = firstdate, lastdate = lastdate, resultsonly = True)

if len(oblist) == 0:
    print >>sys.stderr, "Sorry no observations with results found try finding/calculating some more"
    sys.exit(1)
    
outtab = np.array([]).reshape(0, ncols) 

for ob in oblist:
    
    nfound = 0
    
    nextrow = np.full((ncols,), -1.0)
    nextrow[0] = ob.obsdate
    nextrow[1] = ob.airmass
    nextrow[2] = ob.skylevel
    nextrow[3] = ob.target.aducount
    nextrow[4] = ob.target.aduerror
    
    for oitem in ob.objlist:
        try:
            wcol = colnums[oitem.objname]
        except KeyError:
            continue
        nfound += 1
        nextrow[wcol] = oitem.aducount
        nextrow[wcol+1] = oitem.aduerror
    
    if nfound == 0:
        continue
    
    nextrow = nextrow.reshape(1, ncols)
    outtab = np.concatenate((outtab, nextrow))

if outtab.shape[0] == 0:
    print >>sys.stderr, "Sorry didn not find anything"
    sys.exit(1)

np.savetxt(outfile, outtab)
