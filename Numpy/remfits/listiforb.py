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

parsearg = argparse.ArgumentParser(description='List flat or bias',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to limit to')
parsearg.add_argument('--type', type=str, default='any', help='Type wanted flat, bias, any')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
remfield.parseargs(parsearg)
parsearg.add_argument('--idonly', action='store_true', help='Just give ids no other data')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

fieldselect = ["rejreason is NULL"]
fieldselect.append("ind!=0")

try:
    parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

try:
    remfield.getargs(resargs, fieldselect)
except remfield.RemFieldError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(21) 

idonly = resargs['idonly']
filters = resargs['filter']
typereq = resargs['type']
gain = resargs["gain"]

mydb, dbcurs = remdefaults.opendb()

if filters is not None:
    qfilt = [ "filter='" + o + "'" for o in filters]
    fieldselect.append("(" + " OR ".join(qfilt) + ")")

if typereq[0] == 'f':
    fieldselect.append("typ='flat'")
elif typereq[0] == 'b':
    fieldselect.append("typ='bias'")

if gain is not None:
    fieldselect.append("ABS(gain-%.3g) < %.3g" % (gain, gain * 1e-3))

sel = ""

if len(fieldselect) != 0:
    sel = "WHERE " + " AND ".join(fieldselect)

sel += " ORDER BY date_obs"
sel = "SELECT ind,filter,typ,date_obs,gain,minv,maxv,median,mean,std,skew,kurt FROM iforbinf " + sel

dbcurs.execute(sel)

if idonly:
    for row in dbcurs.fetchall():
        print(row[0])
else:
    for row in dbcurs.fetchall():
        ind, filt, typ, dat, g, minv, maxv, median, mean, std, skew, kurt = row
        print(filt, end=' ')
        if typ == 'flat':
            print('F', end=' ')
        else:
            print('B', end=' ')
        print(dat.strftime("%Y-%m-%d %H:%M:%S"), end=' ')
        if gain is None:
            print("%3.1f" % g, end=' ')
        print("%5d" % minv, end=' ')
        print("%5d" % maxv, end=' ')
        print("%9.2f" % median, end=' ')
        print("%9.2f" % mean, end=' ')
        print("%#9.3g" % std, end=' ')
        print("%#10.3g" % skew, end=' ')
        print("%#10.3g" % kurt)
