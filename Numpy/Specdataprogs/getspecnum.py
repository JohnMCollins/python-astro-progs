#! /usr/bin/env python

# Get spectrum number from Info file by date

import sys
import os
import os.path
import string
import datetime
import argparse
import miscutils
import specinfo
import jdate

def argtojdate(arg):
    """Parse argument as either dd/mm/yy date or jdate"""
    if arg is None:
        return None
    try:
        jd = float(arg)
        if jd >= 2400000.0:
            jd -= 2400000.0
        if bf:
            jd -= 1.0
        else:
            jd += 1.0
    except ValueError:
        bits = string.split(arg, '/')
        try:
            if len(bits) != 3:
                raise ValueError("Not date")
            d, m, y = [int(x) for x in bits]
            if y < 50:
                y += 2000
            elif y < 100:
                y += 1900
            jd = jdate.datetime_to_jdate(datetime.datetime(day=d, month=m, year=y, hour=0, minute=1))
        except ValueError:
            return None
    return int(jd)

parsearg = argparse.ArgumentParser(description='Get spectrum number from info file by date', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)
parsearg.add_argument('--after', type=str, help='Date or jdate for first spectrum after that date')
parsearg.add_argument('--before', type=str, help='Date or jdate for last spectrum before that date')

res = vars(parsearg.parse_args())

infofile = res['infofile'][0]
afterd = argtojdate(res['after'])
befored = argtojdate(res['before'])

if not os.path.isfile(infofile):
    infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infofile)
    ctrllist = inf.get_ctrlfile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", infofile
    print "Error was:", e.args[0]
    sys.exit(100)

n = 0
lastn = -1
for df in ctrllist.datalist:
    intdate = int(df.modjdate)
    if befored is not None and intdate >= befored:
        if lastn < 0:
            sys.stdout = sys.stderr
            print "No detes before", jdate.display(befored)
            sys.exit(101)
        print lastn
        sys.exit(0)
    if afterd is not None and intdate > afterd:
        print n
        sys.exit(0)
    lastn = n
    n += 1

sys.stdout = sys.stderr
print "No dates found"
sys.exit(102)
