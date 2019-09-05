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

parsearg = argparse.ArgumentParser(description='List individual flat bias or dims',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to limit to')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
parsearg.add_argument('--exptime', type=float, help='Exposure time to select')
parsearg.add_argument('--criterion', type=int, default=60000, help='Critierion for saturation')

resargs = vars(parsearg.parse_args())

dbname = resargs['database']
filters = resargs['filter']
gain = resargs["gain"]
exptime = resargs['exptime']
crit = resargs['criterion']

mydb = dbops.opendb(dbname)

dbcurs = mydb.cursor()

sel = ''
if filters is not None:
    qfilt = [ "filter='" + o + "'" for o in filters]
    sel = "(" + " OR ".join(qfilt) +")"

if len(sel) != 0: sel += " AND "
sel += "typ='flat'"

if gain is not None:
    if len(sel) != 0: sel += " AND "
    sel += "ABS(gain-%.3g) < %.3g" % (gain, gain * 1e-3)

if exptime is not None:
    if len(sel) != 0: sel += " AND "
    sel += "ABS(exptime-%.3g) < %.3g" % (exptime, exptime * 1e-3)

if len(sel) != 0: sel = " WHERE " + sel
sel += " ORDER BY date_obs"
sel = "SELECT ind,date_obs,filter,gain,exptime FROM iforbinf" + sel
dbcurs.execute(sel)
try:
    nwarn = ncount = nlots = 0
    for row in dbcurs.fetchall():
        ind, dat, filt, gain, exptime = row
        if gain is None:
            gain = "-"
        else:
            gain = "%6.3g" % gain
        ffile = dbremfitsobj.getfits(dbcurs, ind)
        fdat = ffile[0].data
        fdat = trimarrays.trimzeros(fdat)
        rows, cols = fdat.shape
        fmax = fdat.max()
        fwarn = ''
        nplus = np.count_nonzero(fdat >= crit)
        if nplus > 0:
            perc = nplus * 100.0 / fdat.size
            fwarn = "\t%.3g%%" % perc
            nwarn += 1
            if perc >= 50.0:
                nlots += 1
        ncount += 1
        print("%s %s %s %.3g %d %d %5d %5d %10.2f %10.2f %s" % (dat.strftime("%Y-%m-%d %H:%M:%S"), filt, gain, exptime, rows, cols, fdat.min(), fmax, fdat.mean(), fdat.std(), fwarn))
except KeyboardInterrupt:
    pass
finally:
    print("\n", nwarn,"saturated", nlots, "more than 50% out of", ncount, "%.2f%%/%.2f%%" % ((float(nwarn) * 100 / ncount), (float(nlots)*100/ncount)))
