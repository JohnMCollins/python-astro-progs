#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-24T22:41:12+01:00
# @Email:  jmc@toad.me.uk
# @Filename: listobs.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:00:35+00:00

import dbops
import argparse
import datetime
import re
import sys

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
                print("Could not understand date", dat)
                sys.exit(10)
    except ValueError:
        print("Could not understand date", dat)
        sys.exit(10)

    return ret.strftime("%Y-%m-%d")

parsearg = argparse.ArgumentParser(description='List available observations',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default='remfits', help='Database to use')
parsearg.add_argument('--fromdate', type=str, help='Earlist date to list from')
parsearg.add_argument('--todate', type=str, help='Latest date to list from (same as fromdate if that specified)')
parsearg.add_argument('--allmonth', type=str, help='All of given year-month as alternative to from/to date')
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to limit to')
parsearg.add_argument('--dither', type=int, nargs='*', help='Dither ID to limit to')
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to limit to')
parsearg.add_argument('--summary', action='store_true', help='Just summarise objects and number of obs')
parsearg.add_argument('--idonly', action='store_true', help='Just give ids no other data')
parsearg.add_argument('--fitsind', action='store_true', help='Show fits ind not obs ind')

resargs = vars(parsearg.parse_args())

dbname = resargs['database']
idonly = resargs['idonly']
fd = parsedate(resargs['fromdate'])
td = parsedate(resargs['todate'])
if td is None:
    td = fd
allmonth = resargs['allmonth']
objlist = resargs['objects']
dither = resargs['dither']
filters = resargs['filter']
summary = resargs['summary']
fitsind = resargs['fitsind']

if idonly and summary:
    print("Cannot have both idonly and summary", file=sys.stderr)
    sys.exit(10)

mydb = dbops.opendb(dbname)

dbcurs = mydb.cursor()

sel = ""
if fd is None:
    if allmonth is not None:
        mtch = re.match('(\d\d\d\d)-(\d+)$', allmonth)
        if mtch is None:
            print("Cannot understand allmonth arg " + allmonth, file=sys.stderr);
            sys.exit(31)
        sel += "(date_obs>='"+allmonth+"-01' AND date_obs<=date_sub(date_add('"+allmonth+"-01',interval 1 month),interval 1 second))"
else:
    sel += "(date_obs>='" + fd + " 00:00:00' AND date_obs<='" + td + " 23:59:59')"

if objlist is not None:
    qobj = [ "object='" + o + "'" for o in objlist]
    if len(sel) != 0: sel += " AND "
    sel += "(" + " OR ".join(qobj) +")"

if filters is not None:
    qfilt = [ "filter='" + o + "'" for o in filters]
    if len(sel) != 0: sel += " AND "
    sel += "(" + " OR ".join(qfilt) +")"

if dither is not None:
    qdith = [ "dithID=" + str(d) for d in dither]
    if len(sel) != 0: sel += " AND "
    sel += "(" + " OR ".join(qdith) +")"

if len(sel) != 0: sel = " WHERE " + sel
if summary:
    sel = "SELECT object,count(*) FROM obsinf" + sel + "GROUP BY object"
else:
    sel += " ORDER BY object,dithID,date_obs"
    sel = "SELECT obsind,ind,date_obs,object,filter,dithID FROM obs" + sel
dbcurs.execute(sel)
if idonly:
    for row in dbcurs.fetchall():
        print(row[0])
elif summary:
    for row in dbcurs.fetchall():
        print("%-10s\t%d" % row)
else:
    for row in dbcurs.fetchall():
        obsind,ind,dat,obj,filt,dith = row
        if fitsind: obsind = ind
        print("%d\t%s\t%s\t%s\t%d" % (obsind, dat.strftime("%Y-%m-%d %H:%M:%S"), obj, filt, dith))
