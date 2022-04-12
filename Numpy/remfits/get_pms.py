#!  /usr/bin/env python3

"""Build table of object proper motions"""

import argparse
import sys
from astropy.time import Time
from astropy.coordinates import SkyCoord
import astropy.units as u
import remdefaults
import parsetime
import col_from_file

# Units ready for use

MAS_YR = u.mas / u.yr

parsearg = argparse.ArgumentParser(description='Build table of proper motions for specified dates',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('datelist', type=str, nargs='*', help='Dates to calculate for - empty to take from stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg)
resargs = vars(parsearg.parse_args())
datelist = resargs['datelist']
if len(datelist) == 0:
    datelist = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
remdefaults.getargs(resargs)

mydb, dbcurs = remdefaults.opendb()

convdates = []
for d in datelist:
    try:
        cdt = parsetime.parsedate(d)
    except ValueError:
        print("Did not understatnd date", d, file=sys.stderr)
        continue
    convdates.append(cdt)

if len(convdates) != len(datelist):
    print("Aborting due to errors", file=sys.stderr)
    sys.exit(10)

dbcurs.execute("SELECT ind,radeg,decdeg,dist,rapm,decpm,rv FROM objdata WHERE rapm!=0 or decpm!=0")
dbtab = dbcurs.fetchall()

n = 0

for poss_date in convdates:

    dbcurs.execute("DELETE FROM objpm WHERE obsdate=%s", poss_date)
    newtime = Time(poss_date)

    for ind, radeg, decdeg, dist, rapm, decpm, rv in dbtab:
        args = dict(ra=radeg * u.deg, dec=decdeg * u.deg, obstime=Time('J2000'), pm_ra_cosdec=rapm * MAS_YR, pm_dec=decpm * MAS_YR)
        if dist is not None and rv is not None:
            args['distance'] = dist * u.lightyear
            args['radial_velocity'] = rv * u.km / u.second
        spos = SkyCoord(**args).apply_space_motion(new_obstime=newtime)
        fields = ["objind", "obsdate", "radeg", "decdeg"]
        values = [ "{:d}".format(ind), mydb.escape(poss_date), str(spos.ra.deg), str(spos.dec.deg)]
        if dist is not None and rv is not None:
            fields.append("dist")
            values.append(str(spos.distance.lightyear))
        dbcurs.execute("INSERT INTO objpm (" + ",".join(fields) + ") VALUES (" + ",".join(values) + ")")
        n += 1
        if n % 10 == 0:
            mydb.commit()

mydb.commit()
