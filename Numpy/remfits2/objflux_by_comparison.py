#!  /usr/bin/env python3

"""Get object flux by comparison with other objects"""

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

def combine_errors(f, x, y, xerr, yerr):
    """Combine stds for things we are multiplying or dividing
    return tuple of value and stddev"""
    return (f, f * math.sqrt((xerr/x)**2+(yerr/y)**2))

parsearg = argparse.ArgumentParser(description='Get object flux by comparison with sum of reference objects', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('refobjs', type=str, nargs='+', help='Reference objects to use by name label or objid')
parsearg.add_argument('--filter', type=str, required=True, help='Filter to limit refs to')
parsearg.add_argument('--object', type=str, required=True, help='Object to study as id label or objid')
parsearg.add_argument('--vicinity', type=str, help='Study objects in vicinity if we cannot otherwise work it out')
parsearg.add_argument('--outfile', type=str, help='Output file or use stdout')
parsearg.add_argument('--interpolate', action='store_true', help='Interpolate missing objects')
parsearg.add_argument('--weighting', action='store_true', help='Weight each ref star by apparent variability')

resargs = vars(parsearg.parse_args())
refobjs = resargs['refobjs']
remdefaults.getargs(resargs)
filtname = resargs['filter']
filtbri = filtname + 'bri'
filtbristd = filtbri + 'sd'
target = resargs['object']
vicinity = resargs['vicinity']
outfile = resargs['outfile']
interpolate = resargs['interpolate']
weighting = resargs['weighting']

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
    sys.exit(15)

target = targobj.objname
if vicinity is None:
    vicinity = targobj.vicinity
    vicobj = objdata.ObjData()
    vicobj.get(mycu, name=vicinity)
elif vicinity != targobj.vicinity:
    print("Confused about vicinity, target was", targobj.vicinity, "specified was", vicinity, file=sys.stderr)
    sys.exit(14)

refobjlist = []
objinddict = dict()
errors = 0

for refobjname in refobjs:
    robj = objdata.ObjData()
    if refobjname.isdigit():
        try:
            robj.get(mycu, ind=int(refobjname))
        except objdata.ObjDataError as e:
            print("Did not find object ID", refobjname, file=sys.stderr)
            errors += 1
            continue
    else:
        try:
            robj.get(mycu, name=refobjname)
        except objdata.ObjDataError as e:
            robj = get_obj_by_label(mycu, vicinity, refobjname)
            if robj is None:
                print("Did not find object name or label", refobjname, file=sys.stderr)
                errors += 1
                continue

    # Check we've got brightness set for that object and it's in vicinity

    if robj.vicinity != vicinity:
        print(robj.dispname, "is in vicinity of", robj.vicinity, "not", vicinity, file=sys.stderr)
        errors += 1
        continue

    robjbri = getattr(robj, filtbri, None)
    if robjbri is None:
        print(refobjname, "does not have a", filtbri, "field", file=sys.stderr)
        errors += 1
        continue

    if robj.objind == targobj.objind:
        print(refobjname, "is same as target", file=sys.stderr)
        errors += 1
        continue
    if robj.objind in objinddict:
        print(refobjname, "is duplicated", file=sys.stderr)
        errors += 1
        continue
    objinddict[robj.objind] = (robjbri, getattr(robj, filtbristd))
    refobjlist.append(robj)

if errors > 0:
    print("Aborting due to", errors, "errors", file=sys.stderr)
    sys.exit(100)

# Grab ourselves a load of existing counts

mycu.execute("SELECT bjdobs,aducount,aduerr,obsinf.obsind " \
             "FROM obsinf INNER JOIN aducalc ON obsinf.obsind=aducalc.obsind " \
             "WHERE filter=%s AND aducalc.objind={:d} ORDER BY bjdobs".format(targobj.objind), filtname)

targrows = mycu.fetchall()

resarray = []
weight_resarray = []

for bjdate, aducount, aduerr, obsind in targrows:

    # Get all matches for this observation

    mycu.execute("SELECT objind,aducount,aduerr FROM aducalc WHERE obsind={:d}".format(obsind))
    objrows = mycu.fetchall()

    obsadus = dict()

    actual_sum_adus = actual_sum_errors_sq = expected_sum_adus = expected_sum_errors_sq = 0.0
    weighted_sum = sum_weights_sq = expected_weighted_sum = expected_sum_weights_sq = 0.0

    for objind, aduc, adue in objrows:
        if objind != targobj.objind and objind in objinddict:
            obsadus[objind] = (aduc, adue)
            actual_sum_adus += aduc
            sqw = adue**2
            actual_sum_errors_sq += sqw
            weighted_sum += aduc/sqw
            sum_weights_sq += sqw
            c, e = objinddict[objind]
            expected_sum_adus += c
            sqw = e**2
            expected_sum_errors_sq += sqw
            expected_weighted_sum += c/sqw
            expected_sum_weights_sq += 1/sqw

    numv = len(obsadus)
    if numv == 0:
        continue

    mult_fact, mult_fact_err = combine_errors(actual_sum_adus / expected_sum_adus,
                                              actual_sum_adus, expected_sum_adus,
                                              math.sqrt(actual_sum_errors_sq), math.sqrt(expected_sum_errors_sq))

    weighted_act_mean = weighted_sum / sum_weights_sq
    weighted_act_err = math.sqrt(1/sum_weights_sq)
    weighted_exp_mean = expected_weighted_sum / expected_sum_weights_sq
    weighted_exp_err = math.sqrt(1/expected_sum_weights_sq)
    weighted_mult_fact, weighted_mult_fact_err = combine_errors(weighted_act_mean / weighted_exp_mean,
                                                                weighted_act_mean, weighted_exp_mean,
                                                                weighted_act_err, weighted_exp_err)

    if numv != len(objinddict):
        if not interpolate:
            continue

        # Invent missing ones by scaling up

        for oi, ce in objinddict.items():
            if oi not in obsadus:
                c, e = ce           # These are the "expected" ones
                # Construct the "actual" ones
                aduc, adue = combine_errors(c * mult_fact, c, mult_fact, e, mult_fact_err)
                waduc, wadue = combine_errors(c * weighted_mult_fact, c, weighted_mult_fact, e, weighted_mult_fact_err)
                actual_sum_adus += aduc
                actual_sum_errors_sq += adue**2
                weighted_sum += waduc/wadue**2
                sum_weights_sq += wadue**2
                expected_sum_adus += c
                sqw = e**2
                expected_sum_errors_sq += sqw
                expected_weighted_sum += c/sqw
                expected_sum_weights_sq += 1/sqw

        # Now recalculate total

        mult_fact, mult_fact_err = combine_errors(actual_sum_adus / expected_sum_adus,
                                              actual_sum_adus, expected_sum_adus,
                                              math.sqrt(actual_sum_errors_sq), math.sqrt(expected_sum_errors_sq))

        weighted_act_mean = weighted_sum / sum_weights_sq
        weighted_act_err = math.sqrt(1/sum_weights_sq)
        weighted_exp_mean = expected_weighted_sum / expected_sum_weights_sq
        weighted_exp_err = math.sqrt(1/expected_sum_weights_sq)
        weighted_mult_fact, weighted_mult_fact_err = combine_errors(weighted_act_mean / weighted_exp_mean,
                                                                    weighted_act_mean, weighted_exp_mean,
                                                                    weighted_act_err, weighted_exp_err)

    rescnt, reserr = combine_errors(aducount / mult_fact, aducount, mult_fact, aduerr, mult_fact_err)
    wrescnt, wreserr = combine_errors(aducount / weighted_mult_fact, aducount, weighted_mult_fact, aduerr, weighted_mult_fact_err)
    resarray.append((bjdate, rescnt, reserr))
    weight_resarray.append((bjdate, wrescnt, wreserr))

if weighting:
    resarray = np.array(weight_resarray)
else:
    resarray = np.array(resarray)
if outfile is None:
    np.savetxt(sys.stdout, resarray)
else:
    np.savetxt(outfile, resarray)
