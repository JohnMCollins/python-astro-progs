#!  /usr/bin/env python3

"""Get object flux by comparison"""

import argparse
import sys
import numpy as np
import remdefaults
import objdata
import col_from_file
import logs

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

def get_object_dat(dbcu, obj, vic):
    """Get object by label or name"""
    resobj = objdata.ObjData()
    if obj.isdigit():
        try:
            resobj.get(dbcu, ind=int(obj))
        except objdata.ObjDataError as err:
            logging.die(12, "Cannot find object id", obj, "error was", err.args[0])
    else:
        try:
            resobj.get(mycu, name=obj)
        except objdata.ObjDataError:
            resobj = get_obj_by_label(mycu, vic, obj)
    if resobj is None:
        logging.die(13, "Unknown object", obj)
    return  resobj


parsearg = argparse.ArgumentParser(description='Get object flux by comparison with other object', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsids', type=int, nargs='*', help='List of obs ids or use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--object', type=str, required=True, help='Object to study as id label or objid')
parsearg.add_argument('--refobj', type=str, required=True, help='Reference object to compare against')
parsearg.add_argument('--vicinity', type=str, help='Study objects in vicinity if we cannot otherwise work it out')
parsearg.add_argument('--outfile', type=str, help='Output file or use stdout')
parsearg.add_argument('--maxsky', type=float, default=1000.0, help='Maximum sky level')
parsearg.add_argument('--minsnr', type=float, default=1.0, help='Minimum SNR for ref stars')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
obsids = resargs['obsids']
if len(obsids) == 0:
    obsids = map(int, col_from_file.col_from_file(sys.stdin, resargs['colnum']))
target = resargs['object']
refobjname = resargs['refobj']
vicinity = resargs['vicinity']
maxsky = resargs['maxsky']
minsnr = resargs['minsnr']
outfile = resargs['outfile']
logging = logs.getargs(resargs)

mydb, mycu = remdefaults.opendb()

if vicinity is not None:
    try:
        vicobj = objdata.ObjData()
        if vicinity.isdigit():
            vicobj.get(mycu, ind=int(vicinity))
        else:
            vicobj.get(mycu, name=vicinity)
    except objdata.ObjDataError as e:
        logging.die(10, "Cannot understand vicinity", vicinity, "error was", e.args[0])
    if not vicobj.is_target():
        logging.die(11, "Vicinity object", vicinity, "is not a target object")
    vicinity = vicobj.objname

# Figure out what the target is supposed to be
# First allow for case where given as object id

targobj = get_object_dat(mycu, target, vicinity)
target = targobj.objname
if vicinity is None:
    vicinity = targobj.vicinity
    vicobj = objdata.ObjData()
    vicobj.get(mycu, name=vicinity)
elif vicinity != targobj.vicinity:
    logging.die(14, "Confused about vicinity, target was", targobj.vicinity, "specified was", vicinity)

refobj = get_object_dat(mycu, refobjname, vicinity)

mycu.execute("SELECT bjdobs,obsinf.obsind,aducalc.objind,aducount,aduerr,filter " \
             "FROM obsinf INNER JOIN aducalc ON obsinf.obsind=aducalc.obsind " \
             "WHERE obsinf.obsind IN ({:s}) " \
             "AND (aducalc.objind={:d} OR aducalc.objind={:d}) " \
             "AND aducalc.skylevel<={:.8e} " \
             "ORDER BY date_obs".format(",".join(map(str, obsids)), targobj.objind, refobj.objind, maxsky))

targrows = mycu.fetchall()
if len(targrows) == 0:
    logging.die(20, "No target rows to display")

resultlist = []
last_date = -1
filtres = targres = refres = targerr = referr = None

for bjdate, obsind, objind, acttargadus, acttargaduerr, filt in targrows:

    if acttargadus / acttargaduerr < minsnr:
        continue

    if filtres != filt:
        if filtres is not None:
            continue
        filtres = filt

    if bjdate != last_date:
        if targres is not None and refres is not None:
            resultlist.append((last_date, targres, refres, targerr, referr))
        targres = refres = None
        last_date = bjdate

    if objind == targobj.objind:
        targres = acttargadus
        targerr = acttargaduerr
    else:
        refres = acttargadus
        referr = acttargaduerr

if len(resultlist) < 2:
    logging.die(21, "Too few ({:d}) rows in results".format(len(resultlist)))

resultlist = np.transpose(np.array(resultlist))

datelist, targvals, refvals, targerrs, referrs = resultlist
diffvals = targvals - refvals
differrs = np.sqrt(targerrs**2 + referrs**2)

resarray = np.transpose(np.array((datelist, diffvals, differrs)))

if outfile is None:
    np.savetxt(sys.stdout, resarray)
else:
    np.savetxt(outfile, resarray)
