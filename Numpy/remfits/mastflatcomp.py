#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-24T22:41:12+01:00
# @Email:  jmc@toad.me.uk
# @Filename: listobs.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:00:35+00:00

import dbops
import remdefaults
import trimarrays
import dbremfitsobj
import argparse
import datetime
import re
import sys
import numpy as np
from astropy.wcs.docstrings import row

parsearg = argparse.ArgumentParser(description='List individual flat files used in master flat',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--filter', type=str, required=True, help='filters to limit to')
parsearg.add_argument('--year', type=int, required=True, help='Year of master filter')
parsearg.add_argument('--month', type=int, required=True, help='Month of master filter')
parsearg.add_argument('--criterion', type=int, default=60000, help='Critierion for saturation')
parsearg.add_argument('--latex', action="store_true", help='Output as latex table')

resargs = vars(parsearg.parse_args())

dbname = resargs['database']
filter = resargs['filter']
year = resargs["year"]
month = resargs['month']
crit = resargs['criterion']
latex = resargs['latex']

mydb = dbops.opendb(dbname)
dbcurs = mydb.cursor()

dbcurs.execute("SELECT fitsind FROM forbinf WHERE typ='flat' AND filter='%s' AND year=%d AND month=%d" % (filter, year,month))
rows = dbcurs.fetchall()
if len(rows) != 1:
    print("No master flat found for year=%d month=%d" % (year,month),file=sys.stderr)
    sys.exit(10)
fitsind = rows[0][0]
if fitsind == 0:
    print("No FITS file found for year=%d month=%d" % (year,month),file=sys.stderr)
    sys.exit(11)
mastfile = dbremfitsobj.getfits(dbcurs, fitsind)
mastheader = mastfile[0].header
masthist = mastheader['HISTORY']
indivs = []
for hl in masthist:
    if hl[0] != 'F':
        break
    newi = hl.split(',')
    indivs += newi

sels = " OR ".join(["fname=" + mydb.escape(f) for f in indivs])

dbcurs.execute("SELECT fname,date_obs,ind FROM iforbinf WHERE " + sels)
for row in dbcurs.fetchall():
    fname, dat, fitsind = row
    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    fdat = ffile[0].data
    fdat = trimarrays.trimzeros(fdat)
    fmax = fdat.max()
    fwarn = ''
    nplus = np.count_nonzero(fdat >= crit)
    if nplus > 0:
        perc = nplus * 100.0 / fdat.size
        if latex:
            fwarn = "%.2f" % perc
        else:
            fwarn = "\t%.3g%%" % perc
    if latex:
        print(dat.strftime("%d/%m/%Y & %H:%M:%S"),"& %d & %d & %.2f & %.2f & %s \\\\" % (fdat.min(), fmax, fdat.mean(), fdat.std(), fwarn))
    else:
        print("%s %s %5d %5d %10.2f %10.2f %s" % (fname, dat.strftime("%Y-%m-%d %H:%M:%S"), fdat.min(), fmax, fdat.mean(), fdat.std(), fwarn))
