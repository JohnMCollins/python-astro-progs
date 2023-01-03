#!  /usr/bin/env python3

"""Get object flux by linear regression"""

import argparse
import sys
import math
import numpy as np
from scipy.stats import linregress
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

def combine_errors(f, x, y, xerr, yerr):
    """Combine stds for things we are multiplying or dividing
    return tuple of value and stddev"""
    return (f, f * math.sqrt((xerr/x)**2+(yerr/y)**2))

parsearg = argparse.ArgumentParser(description='Get object flux by linear regression from reference objects', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--filter', type=str, required=True, help='Filter to limit refs to')
parsearg.add_argument('--object', type=str, required=True, help='Object to study as id label or objid')
parsearg.add_argument('--vicinity', type=str, help='Study objects in vicinity if we cannot otherwise work it out')
parsearg.add_argument('--outfile', type=str, help='Output file or use stdout')
parsearg.add_argument('--minrefs', type=int, default=5, help='Minimum number of reference stars')
parsearg.add_argument('--minsnr', type=float, default=1.0, help='Minimum SNR for ref stars')
parsearg.add_argument('--mincorrelation', type=float, default=0.5, help='Minimum correlation coeff')
parsearg.add_argument('--maxsky', type=float, default=1000.0, help='Maximum sky level')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
filtname = resargs['filter']
filtbri = filtname + 'bri'
filtbristd = filtbri + 'sd'
target = resargs['object']
vicinity = resargs['vicinity']
outfile = resargs['outfile']
minrefs = resargs['minrefs']
minsnr = resargs['minsnr']
mincorr = resargs['mincorrelation']
maxsky = resargs['maxsky']

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
targbrisd = getattr(targobj, filtbristd, None)
if targbri is None or targbrisd is None:
    print(target, "has no", filtbri, "and", filtbristd, file=sys.stderr)
    sys.exit(15)

target = targobj.objname
if vicinity is None:
    vicinity = targobj.vicinity
    vicobj = objdata.ObjData()
    vicobj.get(mycu, name=vicinity)
elif vicinity != targobj.vicinity:
    print("Confused about vicinity, target was", targobj.vicinity, "specified was", vicinity, file=sys.stderr)
    sys.exit(14)

mycu.execute("SELECT bjdobs,obsinf.obsind,aducount,aduerr " \
             "FROM obsinf INNER JOIN aducalc ON obsinf.obsind=aducalc.obsind " \
             "WHERE obsinf.filter=%s AND aducalc.objind={:d} AND aducalc.skylevel<={:.8e} ORDER BY date_obs".format(targobj.objind, maxsky), filtname)

targrows = mycu.fetchall()
if len(targrows) == 0:
    print("No target rows to display", file=sys.stderr)
    sys.exit(20)

objindtobri = dict()
resarray = []

for bjdate, obsind, acttargadus, acttargaduerr in targrows:

    if acttargadus / acttargaduerr < minsnr:
        continue

    mycu.execute("SELECT aducount,aduerr,objind FROM aducalc WHERE obsind={:d} AND objind!={:d}".format(obsind, targobj.objind))
    refrows = mycu.fetchall()

    if len(refrows) < minrefs:
        continue

    refresults = []

    for aducount, aduerr, objind in refrows:

        if objind in objindtobri:
            bri, brisd = objindtobri[objind]
        else:
            mycu.execute("SELECT " + filtbri + "," + filtbristd + " FROM objdata WHERE ind={:d}".format(objind))
            try:
                bri, brisd = mycu.fetchone()
            except TypeError:
                continue
            objindtobri[objind] = (bri, brisd)

        if bri is None or brisd is None:
            continue

        if aducount / aduerr < minsnr:
            continue

        refresults.append((aducount, aduerr, bri, brisd))

    if  len(refresults) < minrefs:
        continue

    refresults = np.array(refresults).transpose()
    actualvals, dummy, expectedvals, dummy = refresults

    # Now for linear regression rejecting if correlation is too small

    lreg = linregress(expectedvals, actualvals)
    if lreg.rvalue ** 2 < mincorr:
        continue

    # Rescale actual value back to "expected" axis

    scaledtargbri, scaledtargbrierr = \
        combine_errors((acttargadus - lreg.intercept) / lreg.slope, acttargadus - lreg.intercept, lreg.slope,
                       math.sqrt(acttargaduerr**2 + lreg.intercept_stderr**2),
                       lreg.stderr)

    resarray.append((bjdate, scaledtargbri, scaledtargbrierr))

if outfile is None:
    np.savetxt(sys.stdout, resarray)
else:
    np.savetxt(outfile, resarray)
