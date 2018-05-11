#! /usr/bin/env python

from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy import coordinates
import astroquery.utils as autils
import astropy.units as u
from astropy.time import Time
import numpy as np
import argparse
import sys
import string
import re
import objcoord
import warnings
import datetime
import objinfo
import os.path

parsearg = argparse.ArgumentParser(description='Make table of objects and positions for date', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('datefrom', type=str, nargs='+', help='Eaither a date or a FitS file to get date from')
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--outfile', type=str, required=True, help='Output file')
parsearg.add_argument('--ramin', type=float, help='Minimum RA')
parsearg.add_argument('--ramax', type=float, help='Maximum RA')
parsearg.add_argument('--decmin', type=float, help='Minimum DEC')
parsearg.add_argument('--decmax', type=float, help='Maximum DEC')

resargs = vars(parsearg.parse_args())
libfile = os.path.expanduser(resargs['libfile'])
ffnames = resargs['datefrom']
outfile = resargs['outfile']
ramin = resargs['ramin']
ramax = resargs['ramax']
decmin = resargs['decmin']
decmax = resargs['decmax']

objinf = objinfo.ObjInfo()
try:
    objinf.loadfile(libfile)
except objinfo.ObjInfoError as e:
    if e.warningonly:
        print  >>sys.stderr, "(Warning) file does not exist:", libfile
    else:
        print >>sys.stderr,  "Error loading file", e.args[0]
        sys.exit(30)

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

firstfile = ffnames[0]
mtch = re.match('(\d+)[-/](\d+)[-/](\d+)$', firstfile)
if mtch:
    d1, d2, d3 = map(lambda x: int(x), mtch.groups())
    if d1 > 1000:
        t = d1
        d1 = d3
        d3 = t
    odt = datetime.datetime(year = d3, month = d2, day=d1, hour=12)
else:
    try:
        ffile = fits.open(firstfile)
    except IOError as e:
        print >>sys.stderr, "Cannot open fits file", firstfile, "error was", e.args[-1]
        sys.exit(10)
    ffhdr = ffile[0].header
    odt = datetime.datetime.now()
    for dfld in ('DATE-OBS', 'DATE', '_ATE'):
        if dfld in ffhdr:
            odt = ffhdr[dfld]
            break

objlist = objinf.list_objects()

if ramin is not None:
    objlist = [oitem for oitem in objlist if oitem.get_ra() >= ramin]
if ramax is not None:
    objlist = [oitem for oitem in objlist if oitem.get_ra() <= ramax]
if decmin is not None:
    objlist = [oitem for oitem in objlist if oitem.get_dec() >= decmin]
if decmax is not None:
    objlist = [oitem for oitem in objlist if oitem.get_dec() <= decmax]

outf = open(outfile, "w")

for oitem in objlist:
    rastr = oitem.rightasc
    decstr = oitem.decl
    # We don't have to worry about those being None because list_objects won't have returned them
    distance = oitem.dist
    rv = oitem.rv
    if rv is None:
        rv = 0
    raval = rastr.getvalue(odt)
    decval = decstr.getvalue(odt)
    mag = oitem.mag
    magerr = oitem.magerr
    if mag is None:
        mag = -1.0
        magerr = 0
    if magerr is None:
        magerr = 0
    print >>outf, "%.16e %.16e %.16e, %.16e %s" % (raval, decval, mag, magerr, oitem.objname)

    
