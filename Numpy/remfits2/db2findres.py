#!  /usr/bin/env python3

"""Display findresult file"""

import argparse
import sys
import warnings
from astropy.utils.exceptions import ErfaWarning
import remdefaults
import find_results
import objdata
import col_from_file

warnings.simplefilter('ignore', ErfaWarning)

parsearg = argparse.ArgumentParser(description='Create findres files from database', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ids', nargs='*', type=str, help='Obs ids to convert or stdin')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--prefix', type=str, default='frout', help='Prefix of output files')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
parsearg.add_argument('--force', action='store_true', help='Force if file exists')

resargs = vars(parsearg.parse_args())
ids = resargs['ids']
remdefaults.getargs(resargs)
prefix = resargs['prefix']
force = resargs['force']
if len(ids) == 0:
    ids = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

errors = 0
frfields = "INSERT INTO findresult (obsind,objind,nrow,ncol,radeg,decdeg,apsize,adus) VALUES ({:s})"

mydb, dbcurs = remdefaults.opendb()

for idstr in ids:
    try:
        intid = int(idstr)
    except ValueError:
        print(idstr, "is an invalid obsid", file=sys.stderr)
        errors += 1
        continue

    dbcurs.execute("SELECT objind,nrow,ncol,radeg,decdeg,rdiff,cdiff,apsize,adus,hide FROM findresult WHERE obsind={:d}".format(intid))
    frres = dbcurs.fetchall()
    if len(frres) == 0:
        print(idstr, "does not have any results in DB", file=sys.stderr)
        errors += 1
        continue

    # Get stuff from obsinf record

    dbcurs.execute("SELECT filter,date_obs,nrows,ncols FROM obsinf WHERE obsind={:d}".format(intid))
    obsinf = dbcurs.fetchall()
    if len(obsinf) != 1:
        print(idstr, "does not have an obsinf???", file=sys.stderr)
        errors += 1
        continue

    findres = find_results.FindResults()
    findres.filter, findres.obsdate, findres.nrows, findres.ncols = obsinf[0]
    findres.obsind = intid

    for objind, nrow, ncol, radeg, decdeg, rdiff, cdiff, apsize, adus, hide in frres:
        fr = find_results.FindResult(col=ncol, row=nrow, rdiff=rdiff, cdiff=cdiff, apsize=apsize, adus=adus, radeg=radeg, decdeg=decdeg, hide=hide)
        fr.obj = objdata.ObjData()
        fr.obj.get(dbcurs, ind=objind)
        fr.istarget = fr.obj.is_target()
        if round(radeg, 4) != round(fr.obj.ra, 4) or round(decdeg, 4) != round(fr.obj.dec, 4):
            # NB we're not worrying about distance
            fr.obj.origra = fr.obj.ra
            fr.obj.origdec = fr.obj.dec
            fr.obj.ra = radeg
            fr.obj.dec = decdeg
        findres.resultlist.append(fr)

    findres.reorder()
    findres.relabel()
    findres.rekey()

    try:
        find_results.save_results_to_file(findres, prefix + idstr, force=force)
    except find_results.FindResultErr as e:
        print("Could not save results for", idstr, "error was", e.args[0], file=sys.stderr)
        errors += 1

if errors != 0:
    print(errors, "erroneous ids out of", len(ids), file=sys.stderr)
    sys.exit(1)
sys.exit(0)
