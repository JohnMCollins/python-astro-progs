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

# Make mapping of obj inds to names

indict = dict()


def getname(indx):
    """Get name of object from index"""
    global dbcurs, indict
    try:
        return  indict[indx]
    except  KeyError:
        pass
    dbcurs.execute("SELECT objname, dispname FROM objdata WHERE ind={:d}".format(indx))
    rows = dbcurs.fetchall()
    if len(rows) == 0:
        ret = "(Unknown)"
    else:
        objn, dispn = rows[0]
        if objn == dispn:
            ret = objn
        else:
            ret = "{:s} ({:s})".format(dispn, objn)
    indict[indx] = ret
    return  ret


parsearg = argparse.ArgumentParser(description='Build table of proper motions for specified dates',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('datelist', type=str, nargs='*', help='Dates to calculate for - empty to take from stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
parsearg.add_argument('--replace', action='store_true', help='Replace existing entries')
parsearg.add_argument('--verbose', action='count', help='Give increasing commentary on stderr')
parsearg.add_argument('--commit', type=int, default=10, help='Commit after this number of inserts')
parsearg.add_argument('--vicinity', type=str, help='Only consider objects in this vicinity')

remdefaults.parseargs(parsearg)
resargs = vars(parsearg.parse_args())
datelist = resargs['datelist']
if len(datelist) == 0:
    datelist = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
remdefaults.getargs(resargs)
commitint = resargs['commit']
if commitint <= 0:
    print("Do not understand commit", commitint, "reverting to 10", file=sys.stderr)
    commitint = 10
verbose = resargs['verbose']
repl = resargs['replace']
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

if vicinity is not None:
    vicinity = objdata.get_objname(dbcurs, vicinity)
    dbcurs.execute("SELECT ind,radeg,decdeg,dist,rapm,decpm,rv FROM objdata WHERE (rapm!=0 OR decpm!=0) AND vicinity=%s", vicinity)
else:
    dbcurs.execute("SELECT ind,radeg,decdeg,dist,rapm,decpm,rv FROM objdata WHERE rapm!=0 OR decpm!=0")

dbtab = dbcurs.fetchall()

ntot = 0

for poss_date in set(convdates):

    n4date = 0

    if verbose > 0:
        print("Commencing work for", poss_date, "out of", len(convdates), file=sys.stderr)

    newtime = Time(poss_date)

    for ind, radeg, decdeg, dist, rapm, decpm, rv in dbtab:
        dbcurs.execute("SELECT COUNT(*) FROM objpm WHERE objind={:d} AND obsdate=%s".format(ind), poss_date)
        nexist = dbcurs.fetchall()[0][0]
        if nexist > 1:
            if repl:
                if verbose > 1:
                    print("Replacing existing data for", getname(ind), file=sys.stderr)
                dbcurs.execute("DELETE FROM objpm WHERE ind={:d} AND obsdate=%s".format(ind), poss_date)
            else:
                if verbose > 1:
                    print("Skipping with existing data for", getname(ind), file=sys.stderr)
                n4date += 1
                continue
        if verbose > 2:
            print("Starting pm calculation for", getname(ind), file=sys.stderr)
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
        if verbose > 2:
            print("Created PM data for", getname(ind), file=sys.stderr)
        ntot += 1
        n4date += 1
        if ntot % 10 == 0:
            mydb.commit()
            if verbose > 0:
                print("Completed", n4date, "out of", len(dbtab), "for", poss_date, file=sys.stderr)

if verbose > 0:
    print("Completed", ntot, "altogether")
mydb.commit()
