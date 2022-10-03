#!  /usr/bin/env python3

"""Get object flux on its own"""

import argparse
import sys
import math
import numpy as np
import remdefaults
import objdata

def get_obj_by_label(dbcu, vic, lab):
    """Work out what the object is by the label"""
    if vic is None:
        return None
    dbcu.execute("SELECT ind FROM objdata WHERE vicinity=%s AND label=%s AND suppress=0", (vic, lab))
    r = dbcu.fetchone()
    if r is None:
        return  None
    res = objdata.ObjData()
    res.get(dbcu, ind=r[0])
    return  res

parsearg = argparse.ArgumentParser(description='Obtain object brightness results in DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--filter', type=str, required=True, help='Filter to limit refs to')
parsearg.add_argument('--object', type=str, required=True, help='Object to study as id label or objid')
parsearg.add_argument('--vicinity', type=str, help='Study objects in vicinity if we cannot otherwise work it out')
parsearg.add_argument('--outfile', type=str, help='Output file or use stdout')
parsearg.add_argument('--minvalid', type=int, default=10, help='Minimum number to be valid')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
filtname = resargs['filter']
filtbri = filtname + 'bri'
target = resargs['object']
vicinity = resargs['vicinity']
outfile = resargs['outfile']
minvalid = resargs['minvalid']

mydb, mycu = remdefaults.opendb()

if vicinity is not None:
    try:
        vicobj = objdata.ObjData()
        if vicinity.isdigit():
            vicobj.get(mycu, ind=int(vicinity))
        else:
            vicobj.get(mycu, name=vicinity)
    except objdata.ObjDataError as e:
        print("Cannot understand vicinity", vicinity, "error was", e.args[0], file=sys.stderr)
        sys.exit(10)
    if not vicobj.is_target():
        print("Vicinity object", vicinity, "is not a target object", file=sys.stderr)
        sys.exit(11)
    vicinity = vicobj.objname

# Figure out what the target is supposed to be
# First allow for case where given as object id

targobj = objdata.ObjData()
if target.isdigit():
    try:
        targobj.get(mycu, ind=int(target))
    except objdata.ObjDataError as e:
        print("Cannot find object id", target, "error was", e.args[0], file=sys.stderr)
        sys.exit(12)
else:
    try:
        targobj.get(mycu, name=target)
    except objdata.ObjDataError as e:
        targobj = get_obj_by_label(mycu, vicinity, target)
        if targobj is None:
            print("Unknown target", target, file=sys.stderr)
            sys.exit(13)

targbri = getattr(targobj, filtbri, None)
if targbri is None:
    print(target, "has no", filtbri, file=sys.stderr)

target = targobj.objname
if vicinity is None:
    vicinity = targobj.vicinity
    vicobj = objdata.ObjData()
    vicobj.get(mycu, name=vicinity)
elif vicinity != targobj.vicinity:
    print("Confused about vicinity, target was", targobj.vicinity, "specified was", vicinity, file=sys.stderr)
    sys.exit(14)

# Grab ourselves a load of existing counts

mycu.execute("SELECT bjdobs,aducount,aduerr " \
             "FROM obsinf INNER JOIN aducalc ON obsinf.obsind=aducalc.obsind " \
             "WHERE filter=%s AND aducalc.objind={:d} ORDER BY bjdobs".format(targobj.objind), filtname)

targrows = mycu.fetchall()
if len(targrows) < minvalid:
    print("Not enough rows to be valid, minimum is", minvalid, file=sys.stderr)
    sys.exit(150)

resarray = np.array(targrows)
if outfile is None:
    np.savetxt(sys.stdout, resarray)
else:
    np.savetxt(outfile, resarray)
