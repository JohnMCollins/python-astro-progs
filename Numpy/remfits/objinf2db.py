#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-10-10T10:54:34+01:00
# @Email:  jmc@toad.me.uk
# @Filename: objinf2db.py
# @Last modified by:   jmc
# @Last modified time: 2018-10-11T11:03:24+01:00

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
import string

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
        print  >>sys.stderr, "(Warning) file does not exist cannot proceed:", libfile
    else:
        print >>sys.stderr,  "Error loading file", e.args[0]
    sys.exit(30)

mydb = dbops.opendb('remfits')
dbcurs = mydb.cursor()
dbcurs.execute('SELECT COUNT(*) FROM objdata')
row = dbcurs.fetchall()
nexist = row[0][0]
if delex:
    if nexist == 0:
        print >>sys.stderr, "(warning) no existing to delete"
    na = dbcurs.execute("DELETE FROM objalias")
    nobj = dbcurs.execute("DELETE FROM objdata")
    if verbose:
        print >>sys.stderr, nobj, "object(s) deleted", na, "aliases deleted"
elif not force and nexist != 0:
    print >>sys.stderr,  nexist, "Objects already in file use --force or --delete"
    sys.exit(21)

obsadded = 0
aliasesadded = 0

for ob in objinf.objects.values():
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
    for k, v in ml.items():
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
    stmt = "INSERT INTO objdata (" + string.join(obfnames, ',') + ") VALUES (" + string.join(obfvals, ',') + ")"
    obsadded += dbcurs.execute(stmt)
    if verbose:
        print >>sys.stderr,  "added", ob.objname
    anames = ob.list_aliases()
    for an in anames:
        obfnames = ["objname", "alias"]
        obfvals = []
        obfvals.append(mydb.escape(ob.objname))
        obfvals.append(mydb.escape(an.objname))
        if an.source is not None:
            obfnames.append("source")
            obfvals.append(mydb.escape(an.source))
        stmt = "INSERT INTO objalias (" + string.join(obfnames, ',') + ") VALUES (" + string.join(obfvals, ',') + ")"
        aliasesadded += dbcurs.execute(stmt)
        if verbose:
            print >>sys.stderr,  "added alias", an.objname, "for", ob.objname
    mydb.commit()

if verbose:
    print >>sys.stderr, obsadded, "objects added", aliasesadded, "aliases added"
