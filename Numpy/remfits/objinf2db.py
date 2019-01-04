#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-10-10T10:54:34+01:00
# @Email:  jmc@toad.me.uk
# @Filename: objinf2db.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:00:50+00:00

def radec_copy(rad, prefix):
    """Copy out RA or DEC values and return tuple of array of field names and values to append"""
    fields = []
    values = []
    if rad is None or rad.value is None:
        return  (fields, values)
    fields.append(prefix + "deg")
    values.append(str(rad.value))
    if rad.err is not None:
        fields.append(prefix + 'err')
        values.append(str(rad.err))
    if rad.pm is not None:
        fields.append(prefix + 'pm')
        values.append(str(rad.pm))
    return  (fields, values)

import argparse
import dbops
import objinfo
import os.path
import sys

mydb = dbops.opendb('remfits')
dbcurs = mydb.cursor()

parsearg = argparse.ArgumentParser(description='Copy XML library of objects to MySQL DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--force', action='store_true', help='Force copy even if DB looks full')
parsearg.add_argument('--delete', action='store_true', help='Delete existing aliaes and objects')
parsearg.add_argument('--verbose', action='store_true', help='Say what we are doing')

resargs = vars(parsearg.parse_args())
libfile = os.path.expanduser(resargs['libfile'])
delex = resargs['delete']
force = resargs['force']
verbose = resargs['verbose']

objinf = objinfo.ObjInfo()
try:
    objinf.loadfile(libfile)
except objinfo.ObjInfoError as e:
    if e.warningonly:
        print("(Warning) file does not exist cannot proceed:", libfile, file=sys.stderr)
    else:
        print("Error loading file", e.args[0], file=sys.stderr)
    sys.exit(30)

mydb = dbops.opendb('remfits')
dbcurs = mydb.cursor()
dbcurs.execute('SELECT COUNT(*) FROM objdata')
row = dbcurs.fetchall()
nexist = row[0][0]
if delex:
    if nexist == 0:
        print("(warning) no existing to delete", file=sys.stderr)
    na = dbcurs.execute("DELETE FROM objalias")
    nobj = dbcurs.execute("DELETE FROM objdata")
    if verbose:
        print(nobj, "object(s) deleted", na, "aliases deleted", file=sys.stderr)
elif not force and nexist != 0:
    print(nexist, "Objects already in file use --force or --delete", file=sys.stderr)
    sys.exit(21)

obsadded = 0
aliasesadded = 0

for ob in list(objinf.objects.values()):
    if ob.objname is None:
        continue
    obfnames = []
    obfvals = []
    obfnames.append('objname')
    obfvals.append(mydb.escape(ob.objname))
    if ob.objtype is not None:
        obfnames.append('objtype')
        obfvals.append(mydb.escape(ob.objtype))
    if ob.dist is not None:
        obfnames.append('dist')
        obfvals.append(str(ob.dist))
    if ob.rv is not None:
        obfnames.append('rv')
        obfvals.append(str(ob.rv))
    nf, nv = radec_copy(ob.rightasc, "ra")
    obfnames += nf
    obfvals += nv
    nf, nv = radec_copy(ob.decl, "dec")
    obfnames += nf
    obfvals += nv
    ml = ob.maglist.maglist
    nf = []
    nv = []
    for k, v in list(ml.items()):
        if k not in 'giruz':
            continue
        if v.value is None:
            continue
        nf.append(k + "mag")
        nv.append(str(v.value))
        if v.err is not None:
            nf.append(k + "merr")
            nv.append(str(v.err))
    obfnames += nf
    obfvals += nv
    if ob.apsize is not None:
        obfnames.append("apsize")
        obfvals.append(str(ob.apsize))
    stmt = "INSERT INTO objdata (" + ','.join(obfnames) + ") VALUES (" + ','.join(obfvals) + ")"
    obsadded += dbcurs.execute(stmt)
    if verbose:
        print("added", ob.objname, file=sys.stderr)
    anames = ob.list_aliases()
    for an in anames:
        obfnames = ["objname", "alias"]
        obfvals = []
        obfvals.append(mydb.escape(ob.objname))
        obfvals.append(mydb.escape(an.objname))
        if an.source is not None:
            obfnames.append("source")
            obfvals.append(mydb.escape(an.source))
        stmt = "INSERT INTO objalias (" + ','.join(obfnames) + ") VALUES (" + ','.join(obfvals) + ")"
        aliasesadded += dbcurs.execute(stmt)
        if verbose:
            print("added alias", an.objname, "for", ob.objname, file=sys.stderr)
    mydb.commit()

if verbose:
    print(obsadded, "objects added", aliasesadded, "aliases added", file=sys.stderr)
