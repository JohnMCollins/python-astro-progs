#!  /usr/bin/env python

import dbops
import argparse
import string

parsearg = argparse.ArgumentParser(description='List available observations',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parsearg.add_argument('--fromdate', type=str, help='Earlist date to list from')
parsearg.add_argument('--todate', type=str, help='Latest date to list from (same as fromdate if that specified')
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to llimit to')
parsearg.add_argument('--dither', type=int, nargs='*', help='Dither ID to limits to')

resargs = vars(parsearg.parse_args())

fd = resargs['fromdate']
td = resargs['todate']
if td is None:
    td = fd
objlist = resargs['objects']
dither = resargs['dither']

mydb = dbops.opendb('remfits')

dbcurs = mydb.cursor()

sel = ""
if fd is not None:
    sel += "(date_obs>='" + fd + " 00:00:00' AND date_obs<='" + td + " 23:59:59')"

if objlist is not None:
    qobj = [ "object='" + o + "'" for o in objlist]
    if len(sel) != 0: sel += " AND "
    sel += "(" + string.join(qobj, " OR ") +")"

if dither is not None:
    qdith = [ "dithID=" + str(d) for d in dither]
    if len(sel) != 0: sel += " AND "
    sel += "(" + string.join(qdith, " OR ") +")"

if len(sel) != 0: sel = " WHERE " + sel
sel += " ORDER BY object,dithID,date_obs"
sel = "SELECT ind,date_obs,object,filter,dithID FROM obs" + sel
dbcurs.execute(sel)
for row in dbcurs.fetchall():
    ind,dat,obj,filt,dith = row
    print "%d\t%s\t%s\t%s\t%d" % (ind, dat.strftime("%Y-%m-%d %H:%M:%S"), obj, filt, dith)
    