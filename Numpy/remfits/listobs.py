#!  /usr/bin/env python

import dbops
import argparse
import string
import datetime
import re

def parsedate(dat):
    """Parse an argument date and try to interpret common things"""
    if dat is None:
        return None
    now = datetime.datetime.now()
    rnow = datetime.datetime(now.year,now.month,now.day)
    m = re.match("(\d+)\D(\d+)(?:\D(\d+))?", dat)
    try:
        if m:
            dy,mn,yr = m.groups()
            dy = int(dy)
            mn = int(mn)
            if yr is None:
                yr = now.year
                ret = datetime.datetime(yr, mn, dy)
                if ret > rnow:
                    ret = datetime.datetime(yr-1,mn,dy)
            else:
                yr = int(yr)
                if dy > 31:
                    yr = dy
                    dy = int(m.group(3))
                if yr < 50:
                    yr += 2000
                elif yr < 100:
                    yr += 1900
                ret = datetime.datetime(yr, mn, dy)
        elif dat == 'today':
            ret = rnow
        elif dat == 'yesterday':
            ret = rnow - datetime.timedelta(days=1)
        else:
            m = re.match("-(\d+)$", dat)
            if m:
                ret = rnow - datetime.timedelta(days=int(m.group(1)))
            else:
                print "Could not understand date", dat
                sys.exit(10)
    except ValueError:
        print "Could not understand date", dat
        sys.exit(10)

    return ret.strftime("%Y-%m-%d")

parsearg = argparse.ArgumentParser(description='List available observations',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parsearg.add_argument('--fromdate', type=str, help='Earlist date to list from')
parsearg.add_argument('--todate', type=str, help='Latest date to list from (same as fromdate if that specified')
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to llimit to')
parsearg.add_argument('--dither', type=int, nargs='*', help='Dither ID to limits to')
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to llimit to')
parsearg.add_argument('--idonly', action='store_true', help='Just give ids no other data')

resargs = vars(parsearg.parse_args())

idonly = resargs['idonly']
fd = parsedate(resargs['fromdate'])
td = parsedate(resargs['todate'])
if td is None:
    td = fd
objlist = resargs['objects']
dither = resargs['dither']
filters = resargs['filter']

mydb = dbops.opendb('remfits')

dbcurs = mydb.cursor()

sel = ""
if fd is not None:
    sel += "(date_obs>='" + fd + " 00:00:00' AND date_obs<='" + td + " 23:59:59')"

if objlist is not None:
    qobj = [ "object='" + o + "'" for o in objlist]
    if len(sel) != 0: sel += " AND "
    sel += "(" + string.join(qobj, " OR ") +")"

if filters is not None:
    qfilt = [ "filter='" + o + "'" for o in filters]
    if len(sel) != 0: sel += " AND "
    sel += "(" + string.join(qfilt, " OR ") +")"

if dither is not None:
    qdith = [ "dithID=" + str(d) for d in dither]
    if len(sel) != 0: sel += " AND "
    sel += "(" + string.join(qdith, " OR ") +")"

if len(sel) != 0: sel = " WHERE " + sel
sel += " ORDER BY object,dithID,date_obs"
sel = "SELECT ind,date_obs,object,filter,dithID FROM obs" + sel
dbcurs.execute(sel)
if idonly:
    for row in dbcurs.fetchall():
        print row[0]
else:
    for row in dbcurs.fetchall():
        ind,dat,obj,filt,dith = row
        print "%d\t%s\t%s\t%s\t%d" % (ind, dat.strftime("%Y-%m-%d %H:%M:%S"), obj, filt, dith)
