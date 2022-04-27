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
import objdata

# Units ready for use

MAS_YR = u.mas / u.yr


def count_pm(cond):
    """Count the number of objpms which fit the given condition"""
    dbcurs.execute("SELECT COUNT(*) FROM objpm WHERE " + cond)
    return  dbcurs.fetchall()[0][0]


def create_pm(dbe, date_pm, thresh=0):
    """Create an objpm entry"""
    indc, dummy, rad, decd, distance, ra_pm, dec_pm, rvel = dbe
    args = dict(ra=rad * u.deg, dec=decd * u.deg, obstime=Time('J2000'), pm_ra_cosdec=ra_pm * MAS_YR, pm_dec=dec_pm * MAS_YR)
    if distance is not None and rvel is not None:
        args['distance'] = distance * u.lightyear
        args['radial_velocity'] = rvel * u.km / u.second
    spos = SkyCoord(**args).apply_space_motion(new_obstime=Time(date_pm))
    fields = ["objind", "obsdate", "radeg", "decdeg"]
    values = [ "{:d}".format(indc), mydb.escape(date_pm), str(spos.ra.deg), str(spos.dec.deg)]
    if distance is not None and rvel is not None:
        fields.append("dist")
        values.append(str(spos.distance.lightyear))
    if thresh != 0:
        fields.append('slow')
        values.append('1')
        fields.append('slowth')
        values.append("{:.6e}".format(thresh))
    dbcurs.execute("INSERT INTO objpm (" + ",".join(fields) + ") VALUES (" + ",".join(values) + ")")


parsearg = argparse.ArgumentParser(description='Update table of proper motions to cope with slow-moving objects',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('datelist', type=str, nargs='*', help='Dates to calculate for - empty to take from stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
parsearg.add_argument('--threshold', type=float, default=20.0, help='Threshold in MAS at which we just store single value')
parsearg.add_argument('--verbose', action='count', help='Give increasing commentary on stderr')
parsearg.add_argument('--commit', type=int, default=10, help='Commit after this number of inserts')
parsearg.add_argument('--vicinity', type=str, help='Only consider objects in this vicinity')
parsearg.add_argument('--basedate', type=str, default='2020-01-01', help='Date to calculate slow-moving things for')

remdefaults.parseargs(parsearg)
resargs = vars(parsearg.parse_args())

try:
    basedate = parsetime.parsedate(resargs["basedate"])
except ValueError:
    print("Could not understand basedate", resargs['basedate'], file=sys.stderr)
    sys.exit(11)

datelist = resargs['datelist']
if len(datelist) == 0:
    datelist = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
remdefaults.getargs(resargs)
commitint = resargs['commit']
if commitint <= 0:
    print("Do not understand commit", commitint, "reverting to 10", file=sys.stderr)
    commitint = 10
verbose = resargs['verbose']
threshold = resargs['threshold']
thresholdsq = threshold ** 2
vicinity = resargs['vicinity']

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

convdates = sorted(list(set(convdates)))

if vicinity is not None:
    vicinity = objdata.get_objname(dbcurs, vicinity)
    dbcurs.execute("SELECT ind,dispname,radeg,decdeg,dist,rapm,decpm,rv FROM objdata WHERE (rapm!=0 OR decpm!=0) AND vicinity=%s", vicinity)
else:
    dbcurs.execute("SELECT ind,dispname,radeg,decdeg,dist,rapm,decpm,rv FROM objdata WHERE rapm!=0 OR decpm!=0")

dbtab = dbcurs.fetchall()

# Divide up into ones we need full records for and ones we can just have a single entry for

fullrecord = dict()
slowmoving = dict()

for dbent in dbtab:
    ind, dispname, radeg, decdeg, dist, rapm, decpm, rv = dbent
    if rapm ** 2 + decpm ** 2 > thresholdsq:
        fullrecord[ind] = dbent
    else:
        slowmoving[ind] = dbent

# First check through the ones we are saying are slow moving and move any across to that
# if we've got full records

dbchanges = 0

for ind, dbent in slowmoving.items():

    if count_pm("objind={:d} AND slow!=0".format(ind)) != 0:
        if verbose > 2:
            print("Already got", dbent[1], "on slow", file=sys.stderr)
        continue
    ndel = dbcurs.execute("DELETE FROM objpm WHERE objind={:d}".format(ind))
    if ndel != 0:
        dbchanges += ndel
        if verbose > 0:
            print("Deleting {:d} individual PMs for {:s}".format(ndel, dbent[1]), file=sys.stderr)
    create_pm(dbent, basedate, threshold)
    if verbose > 0:
        print("Creating slow entry for {:s}".format(dbent[1]), file=sys.stderr)

# Check we haven't got items as slow-moving which shouldn't be

for ind, dbent in fullrecord.items():
    ndel = dbcurs.execute("DELETE FROM objpm WHERE objind={:d} AND slow!=0".format(ind))
    if ndel != 0:
        dbchanges += ndel
        if verbose > 0:
            print("Removing slow entry for {:s}".format(dbent[1]), file=sys.stderr)

# Get all the dates we have entries for for each object we're thinking about

frsets = dict()
for ind in fullrecord:
    try:
        indset = frsets[ind]
    except KeyError:
        indset = frsets[ind] = set()
    dbcurs.execute("SELECT obsdate FROM objpm WHERE objind={:d}".format(ind))
    for dat, in dbcurs.fetchall():
        indset.add(dat.strftime("%Y-%m-%d"))

for poss_date in convdates:

    descr = poss_date
    if vicinity is not None:
        descr += " " + vicinity

    if verbose > 0:
        print("Commencing work for", descr, "out of", len(convdates), file=sys.stderr)

    for ind, dbent in fullrecord.items():
        if poss_date in frsets[ind]:
            if verbose > 2:
                print("Already have full record for", poss_date, "in", dbent[1], file=sys.stderr)
            continue
        create_pm(dbent, poss_date)
        if verbose > 0:
            print("Created full record for", poss_date, "in", dbent[1], file=sys.stderr)
        dbchanges += 1
        if dbchanges % commitint == 0:
            mydb.commit()

if dbchanges > 0:
    mydb.commit()
    if verbose > 0:
        print(dbchanges, "database changes", file=sys.stderr)
