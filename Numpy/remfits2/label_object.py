#!  /usr/bin/env python3

"""Label objects in database"""

import argparse
import sys
import remdefaults
import objdata
import vicinity

parsearg = argparse.ArgumentParser(description='Apply lable to object at given position', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('coords', nargs=2, type=float, help='RA and DEC of object in degrees')
parsearg.add_argument('--name', type=str, help='Name of object')
parsearg.add_argument('--tolerance', type=float, default=30.0, help='Totlerance for existing object check in arcsec')
parsearg.add_argument('--replace', action='store_true', help='Replace existing value')
parsearg.add_argument('--type', type=str, default='Star', help='Type of object')
parsearg.add_argument('--dispname', type=str, help='Display name if not same as object name')
parsearg.add_argument('--distance', type=float, help='Distance of object in light years')
parsearg.add_argument('--rv', type=float, help='Radial velocity of object in km/s')
parsearg.add_argument('--pmra', type=float, help='RA PM in mas/yr')
parsearg.add_argument('--pmdec', type=float, help='DEC PM in mas/yr')
parsearg.add_argument('--apsize', type=int, help='Aperture size to set')
parsearg.add_argument('--invented', action='store_true', help='Mark name as invented')
parsearg.add_argument('--notinvented', action='store_true', help='Mark name as not invented')
remdefaults.parseargs(parsearg, tempdir=False)

resargs = vars(parsearg.parse_args())
radeg, decdeg = resargs['coords']
objname = resargs['name']
tolerance = resargs['tolerance']
replaceobj = resargs['replace']
objtype = resargs['type']
dispname = resargs['dispname']
distance = resargs['distance']
rv = resargs['rv']
pmra = resargs['pmra']
pmdec = resargs['pmdec']
apsize = resargs['apsize']
invented = resargs['invented']
notinvented = resargs['notinvented']
remdefaults.getargs(resargs)

mydb, dbcurs = remdefaults.opendb()

dbcurs.execute("SELECT objname,objtype,dispname,vicinity,dist,rv,radeg,decdeg,rapm,decpm,apsize,invented FROM objdata WHERE" +
               " ABS(radeg-{ra:.6e})<={tol:.6e} AND ABS(decdeg-{dec:.6e})<={tol:.6e}".format(ra=radeg, dec=decdeg, tol=tolerance / 3600.0))
matchreg = dbcurs.fetchall()

if len(matchreg) != 0:
    if len(matchreg) > 1:
        names = [m[0] for m in matchreg]
        print("Coords could be any of", ", ".join(names), "narrow toleraance of", tolerance, "arcsec", file=sys.stderr)
        sys.exit(10)
    elif not replaceobj:
        print("Coords match existing", matchreg[0][2], "Narror tolerenace of", tolerance, "or use --replace", fil=sys.stderr)
        sys.exit(11)

    exist_name, exist_type, exist_disp, exist_vic, exist_dist, exist_rv, exist_ra, exist_dec, exist_rapm, exist_decpm, exist_apsize, exist_inv = matchreg[0]
    updfields = []
    if objname is not None and objname != exist_name:
        if objdata.nameused(dbcurs, objname):
            print("New name", objname, "clashes with an existing name", file=sys.stderr)
            sys.exit(20)
        updfields.append("objname=" + mydb.escape(objname))
    if objtype is not None and objtype != exist_type:
        updfields.append("objtype=" + mydb.escape(objtype))
    if dispname is not None and dispname != exist_disp:
        updfields.append("dispname=" + mydb.escape(dispname))
    if distance is not None:
        updfields.append("dist={:.8e}".format(distance))
    if rv is not None:
        updfields.append("rv={:.8e}".format(rv))
    if radeg != exist_ra:
        updfields.append("radeg={:.8e}".format(radeg))
    if decdeg != exist_dec:
        updfields.append("decdeg={:.8e}".format(decdeg))
    if pmra is not None:
        updfields.append("rapm={:.8e}".format(pmra))
    if pmdec is not None:
        updfields.append("decpm={:.8e}".format(pmdec))
    if apsize is not None:
        updfields.append("apsize={:d}".format(apsize))
    if invented and not exist_inv:
        updfields.append("invented=1")
    elif notinvented and exist_inv:
        updfields.append("invented=0")
    if len(updfields) == 0:
        print("No changes made", file=sys.stderr)
        sys.exit(12)
    dbcurs.execute("UPDATE objdata SET " + ",".join(updfields) + " WHERE objname=%s", exist_name)
    mydb.commit()
    sys.exit(0)

# New case, first get vicinity by finding nearest of targets
# (assume OK to ignore proper motion of targets)

if replaceobj:
    print("Did not find object to replace", file=sys.stderr)
    sys.exit(14)

if objname is None:
    print("New objects need name", file=sys.stderr)
    sys.exit(13)
if objdata.nameused(dbcurs, objname):
    print(objname, "clashes with existing name", file=sys.stderr)
    sys.exit(20)
if objtype is None:
    objtype = 'Star'
if dispname is None:
    dispname = objname

vicinity = vicinity.get_vicinity(dbcurs, radeg, decdeg)

if vicinity is None:
    print("Cannot find vicinity of target for given coords", radeg, "and", decdeg, file=sys.stderr)
    sys.exit(14)

addfields = []
addvalues = []

addfields.append("objname")
addvalues.append(mydb.escape(objname))

addfields.append("objtype")
addvalues.append(mydb.escape(objtype))

addfields.append("dispname")
addvalues.append(mydb.escape(dispname))

addfields.append("vicinity")
addvalues.append(mydb.escape(vicinity))

addfields.append("radeg")
addvalues.append("{:.8e}".format(radeg))

addfields.append("decdeg")
addvalues.append("{:.8e}".format(decdeg))
if pmra is not None:
    addfields.append("rapm")
    addvalues.append("{:.8e}".format(pmra))
if pmdec is not None:
    addfields.append("decpm")
    addvalues.append("{:.8e}".format(pmdec))
if distance is not None:
    addfields.append("dist")
    addvalues.append("{:.8e}".format(distance))
if rv is not None:
    addfields.append("rv")
    addvalues.append("{:.8e}".format(rv))
if apsize is not None:
    addfields.append("apsize")
    addvalues.append("{:d}".format(apsize))
if invented:
    addfields.append("invented")
    addvalues.append("1")

dbcurs.execute("INSERT INTO objdata (" + ','.join(addfields) + ") VALUES (" + ','.join(addvalues) + ")")
mydb.commit()
