#! /usr/bin/env python

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import math
import numpy as np
import argparse
import string
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

parsearg = argparse.ArgumentParser(description='List reference objects in results files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('results', type=str, nargs='+', help='XML files of found objects updated with results')

resargs = vars(parsearg.parse_args())

resultsfiles = resargs['results']

namedict = dict()

for rf in resultsfiles:
    
    results = remfitsobj.RemobjSet()
    try:
        results.loadfile(rf)
    except remfitsobj.RemObjError as e:
        print >>sys.stderr,  "Error loading results file", rf, e.args[0]
        continue

    target = results.targname
    if target is None:
        print >>sys.stderr, "Results file", resultsfile, "does not have target"
        continue
    
    for ol in results.getobslist():
        for oitem in ol.objlist:
            nam = oitem.objname
            try:
                namedict[nam] += 1
            except KeyError:
                namedict[nam] = 1

print string.join(sorted(namedict.keys()), ' ')
