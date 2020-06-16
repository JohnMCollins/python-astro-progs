#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-24T22:41:12+01:00
# @Email:  jmc@toad.me.uk
# @Filename: listobs.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:00:35+00:00

import dbops
import remdefaults
import argparse
import datetime
import re
import sys
import parsetime
import remfield

parsearg = argparse.ArgumentParser(description='List available observations',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to limit to')
parsearg.add_argument('--dither', type=int, nargs='*', default=[0], help='Dither ID to limit to')
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to limit to')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
parsearg.add_argument('--summary', action='store_true', help='Just summarise objects and number of obs')
parsearg.add_argument('--idonly', action='store_true', help='Just give ids no other data')
parsearg.add_argument('--fitsind', action='store_true', help='Show fits ind not obs ind')
parsearg.add_argument('--hasfile', action='store_false', help='Only display obs which have FITS files')
remfield.parseargs(parsearg)
parsearg.add_argument('--debug', action='store_true', help='Display selection command')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

fieldselect = ["rejreason is NULL"]
try:
    parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

idonly = resargs['idonly']
objlist = resargs['objects']
dither = resargs['dither']
filters = resargs['filter']
summary = resargs['summary']
fitsind = resargs['fitsind']
gain = resargs["gain"]
hasfile = resargs['hasfile']
debug = resargs['debug']

if idonly and summary:
    print("Cannot have both idonly and summary", file=sys.stderr)
    sys.exit(10)

try:
    remfield.getargs(resargs, fieldselect)
except remfield.RemFieldError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(21) 

mydb, dbcurs = remdefaults.opendb()

if hasfile:
    fieldselect.append("ind!=0")

if objlist is not None:
    qobj = [ "object='" + o + "'" for o in objlist]
    fieldselect.append("(" + " OR ".join(qobj) + ")")

if filters is not None:
    qfilt = [ "filter='" + o + "'" for o in filters]
    fieldselect.append("(" + " OR ".join(qfilt) + ")")

if len(dither) != 0 and dither[0] != -1:
    qdith = [ "dithID=" + str(d) for d in dither]
    if len(qdith) == 1:
        fieldselect.append(qdith[0])
    else:
        fieldselect.append("(" + " OR ".join(qdith) + ")")

if gain is not None:
    fieldselect.append("ABS(gain-%.3g) < %.3g" % (gain, gain * 1e-3))

sel = ""

if len(fieldselect) != 0:
    sel = "WHERE " + " AND ".join(fieldselect)

if summary:
    sel = "SELECT object,count(*) FROM obsinf " + sel + " GROUP BY object"
else:
    sel += " ORDER BY object,dithID,date_obs"
    sel = "SELECT obsind,ind,date_obs,object,filter,dithID FROM obsinf " + sel

if debug:
    print(sel, file=sys.stderr)
dbcurs.execute(sel)
if idonly:
    n = 0
    if fitsind: n = 1
    for row in dbcurs.fetchall():
        print(row[n])
elif summary:
    for row in dbcurs.fetchall():
        print("%-10s\t%d" % row)
else:
    for row in dbcurs.fetchall():
        obsind, ind, dat, obj, filt, dith = row
        if fitsind: obsind = ind
        print("%d\t%s\t%s\t%s\t%d" % (obsind, dat.strftime("%Y-%m-%d %H:%M:%S"), obj, filt, dith))
