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


def parsedate(dat):
    """Parse an argument date and try to interpret common things"""
    if dat is None:
        return None
    now = datetime.datetime.now()
    rnow = datetime.datetime(now.year, now.month, now.day)
    m = re.match("(\d+)\D(\d+)(?:\D(\d+))?", dat)
    try:
        if m:
            dy, mn, yr = m.groups()
            dy = int(dy)
            mn = int(mn)
            if yr is None:
                yr = now.year
                ret = datetime.datetime(yr, mn, dy)
                if ret > rnow:
                    ret = datetime.datetime(yr - 1, mn, dy)
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
            m = re.match("[tT]-(\d+)$", dat)
            if m:
                ret = rnow - datetime.timedelta(days=int(m.group(1)))
            else:
                print("Could not understand date", dat)
                sys.exit(10)
    except ValueError:
        print("Could not understand date", dat)
        sys.exit(10)

    return ret.strftime("%Y-%m-%d")


def parsepair(arg, name, fslist, colname):
    """Parse an argument pair of the form a:b with a and b optional and
    generate a field selection thing for database."""

    if arg is None:
        return
    # Bodge because it gets args starting with - wrong
    if len(arg) > 2 and arg[1] == '-':
        arg = arg[1:]
    bits = arg.split(':')
    if len(bits) != 2:
        print("Cannot understand", name, "arg expection m:n with either number opptional", file=sys.stderr);
        sys.exit(21)
    lov, hiv = bits
    if len(lov) != 0:
        fslist.append(colname + ">=" + lov)
    if len(hiv) != 0:
        fslist.append(colname + "<=" + hiv)


parsearg = argparse.ArgumentParser(description='List flat or bias',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--dates', type=str, help='From:to dates')
parsearg.add_argument('--allmonth', type=str, help='All of given year-month as alternative to from/to date')
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to limit to')
parsearg.add_argument('--type', type=str, default='any', help='Type wanted flat, bias, any')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
parsearg.add_argument('--minval', type=str, help='Minimum value to restrict to as m:n')
parsearg.add_argument('--maxval', type=str, help='Maximum value to restrict to as m:n')
parsearg.add_argument('--median', type=str, help='Median value to restrict to as m:n')
parsearg.add_argument('--mean', type=str, help='Meanv value to restrict to as m:n')
parsearg.add_argument('--std', type=str, help='Stde dev value to restrict to as m:n')
parsearg.add_argument('--skew', type=str, help='Skew value to restrict to as m:n')
parsearg.add_argument('--kurt', type=str, help='Kurtosis value to restrict to as m:n')
parsearg.add_argument('--idonly', action='store_true', help='Just give ids no other data')

resargs = vars(parsearg.parse_args())

dbname = resargs['database']
idonly = resargs['idonly']
dates = resargs['dates']
allmonth = resargs['allmonth']
filters = resargs['filter']
typereq = resargs['type']
gain = resargs["gain"]
minval = resargs['minval']
maxval = resargs['maxval']
medians = resargs['median']
means = resargs['mean']
stds = resargs['std']
skews = resargs['skew']
kurts = resargs['kurt']

mydb = dbops.opendb(dbname)
dbcurs = mydb.cursor()

fieldselect = ["rejreason is NULL"]
fieldselect.append("ind!=0")

if allmonth is not None:
    mtch = re.match('(\d\d\d\d)-(\d+)$', allmonth)
    if mtch is None:
        print("Cannot understand allmonth arg " + allmonth, "expecting yyyy-mm", file=sys.stderr);
        sys.exit(31)
    smonth = allmonth + "-01"
    fieldselect.append("date(date_obs)>='" + smonth + "'")
    fieldselect.append("date(date_obs)<=date_sub(date_add('" + smonth + "',interval 1 month),interval 1 day)")
elif dates is not None:
    datesp = dates.split(':')
    if len(datesp) == 1:
        fieldselect.append("date(date_obs)='" + parsedate(dates) + "'")
    elif len(datesp) != 2:
        print("Don't understand whate date", dates, "is supposed to be", file=sys.stderr)
        sys.exit(20)
    else:
        fd, td = datesp
        if len(fd) != 0:
            fieldselect.append("date(date_obs)>='" + parsedate(fd) + "'")
        if len(td) != 0:
            fieldselect.append("date(date_obs)<='" + parsedate(td) + "'")

if filters is not None:
    qfilt = [ "filter='" + o + "'" for o in filters]
    fieldselect.append("(" + " OR ".join(qfilt) + ")")

if typereq[0] == 'f':
    fieldselect.append("typ='flat'")
elif typereq[0] == 'b':
    fieldselect.append("typ='bias'")

if gain is not None:
    fieldselect.append("ABS(gain-%.3g) < %.3g" % (gain, gain * 1e-3))

parsepair(minval, "minval", fieldselect, "minv")
parsepair(maxval, "maxval", fieldselect, "maxv")
parsepair(medians, "median", fieldselect, "median")
parsepair(means, "mean", fieldselect, "mean")
parsepair(stds, "std", fieldselect, "std")
parsepair(skews, "skew", fieldselect, "skew")
parsepair(kurts, "kurtosis", fieldselect, "kurt")

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
