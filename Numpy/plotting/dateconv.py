#! /usr/bin/env python

import argparse
import datetime
import re
import sys
import jdate

parsearg = argparse.ArgumentParser(description='Convert to/from Julian Dates', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--nodate', action='store_true', help='No date converting to standard dates')
parsearg.add_argument('--notime', action='store_true', help='No time converting to standard dates')
parsearg.add_argument('--unmod', action='store_true', help='Full unmodified jdate converting to those')
parsearg.add_argument('--nohalf', action='store_true', help='Do not adjust dates by half-day in conversions')
parsearg.add_argument('--iso', action='store_true', help='Display converted dates in ISO format')
parsearg.add_argument('args', type=str, help='Date args', nargs='+')
resargs = vars(parsearg.parse_args())
nodate = resargs['nodate']
notime = resargs['notime']
unmod = resargs['unmod']
nohalf = resargs['nohalf']
iso = resargs['iso']

nummatch = re.compile('\d+(?:\.\d+)$')
isomatch = re.compile('(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d{6,6}))?(?:([-+])(\d\d):(\d\d))?$')
dmatch = re.compile('(\d+)/(\d+)(?:/(\d+))?(?:\D+(\d+):(\d+)(?::(\d+))?)?$')

for arg in sys.argv[1:]:
    if arg[0] == '-': continue
    if nummatch.match(arg):
        conv = float(arg)
        if conv > 1e6:
            if nohalf:
                conv += .5
        elif nohalf:
            conv -= .5
        dt = jdate.jdate_to_datetime(conv)
        if iso:
            res = dt.isoformat()
        else:
            dt += datetime.timedelta(microseconds=500000)
            if nodate:
                res = "%.2d:%.2d:%.2d" % (dt.hour, dt.minute, dt.second)
            elif notime:
                res = "%.2d/%.2d/%.4d" % (dt.day, dt.month, dt-year)
            else:
                res = "%.2d/%.2d/%.4d@%.2d:%.2d:%.2d" % (dt.day, dt.month, dt.year, dt.hour, dt.minute, dt.second)
    else:
        mtch = isomatch.match(arg)
        if mtch:
            yr, mnth, dy, hr, mn, sc, ms, pm, pmhr, pmmn = mtch.groups()
            yr = int(yr)
            mnth = int(mnth)
            dy = int(dy)
            hr = int(hr)
            mn = int(mn)
            sc = int(sc)
            if ms is None: ms = 0
            else: ms = int(ms)
            dt = datetime.datetime(yr, mnth, dy, hr, mn, sc, ms)
            if pm is not None:
                pmhr = int(pmhr)
                pmmn = int(pmmn)
                if pm == '-':
                    pmhr = - pmhr
                    pmmn = - pmmn
                dt += datetime.timedelta(hours=pmhr, minutes=pmmn)
        else:
            mtch = dmatch.match(arg)
            if not mtch:
                print "Cannot understand argument", arg
                continue
            dy, mnth, yr, hr, mn, sc = mtch.groups()
            dy = int(dy)
            mnth = int(mnth)
            if yr is None:
                nowt = datetime.datetime.now()
                yr = nowt.year
                dt = datetime.datetime(yr, mnth, dy, nowt.hour, nowt.minute, nowt.second, nowt.microsecond)
                if dt > nowt:
                    dt -= datetime.timedelta(days=1)
                yr = dt.year
            else:
                yr = int(yr)
                if yr < 1000:
                    if yr < 50:
                        yr += 2000
                    else:
                        yr += 1900
            if hr is None: hr = 12
            else: hr = int(hr)
            if mn is None: mn = 0
            else: mn = int(mn)
            if sc is None: sc = 0
            else: sc = int(sc)
            dt = datetime.datetime(yr, mnth, dy, hr, mn, sc, 0)
        resd = jdate.datetime_to_jdate(dt, not unmod)
        if nohalf:
            if unmod:
                resd -= 0.5
            else:
                resd += 0.5
        res = "%.8f" % resd
    print "%s:\t%s" % (arg, res)
