#! /usr/bin/env python

import sys
import os
import os.path
import string
import re
import locale
import argparse
import numpy as np
import miscutils
import specdatactrl
import datarange
import specinfo
import equivwidth
import meanval
import jdate
import datetime

def parsedate(arg, h, m, s):
    """Parse date given and make up datetime with specified h m s"""
    
    if arg is None:
        return None
    mt = re.match('(\d+)/(\d+)/(\d+)', arg)
    if mt is None:
        sys.stdout = sys.stderr
        print "Do not understand date arg", arg
        sys.exit(101)
    dy, mn, yr = map(lambda x: int(x), mt.groups())
    if yr < 1000:
        if yr > 50: yr += 1900
        else: yr += 2000
    dat = datetime.date(yr, mn, dy)
    tim = datetime.time(h, m, s)
    return jdate.datetime_to_jdate(datetime.datetime.combine(dat, tim))

parsearg = argparse.ArgumentParser(description='Extract obs times from info file')
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)
parsearg.add_argument('--outfile', type=str, help='Output file if not stdout')
parsearg.add_argument('--after', type=str, help='Specify earliest date to use')
parsearg.add_argument('--before', type=str, help='Specify latest date to use')

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile'][0]
outfile = resargs['outfile']

afterdate = parsedate(resargs['after'], 0, 0, 1)
beforedate = parsedate(resargs['before'], 23, 59, 59)

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

if outfile is not None:
    try:
        outf = open(outfile, 'w')
    except IOError as e:
        sys.stdout = sys.stderr;
        print "Cannot open output file", outfile
        print "Error was:", e.args[1]
        sys.exit(100)
    sys.stdout = outf

result = []
for datum in ctrllist.datalist:
    if afterdate is not None and datum.modjdate < afterdate:
        continue
    if beforedate is not None and datum.modjdate > beforedate:
        continue
    result.append(datum.modbjdate)

if len(result) == 0:
    sys.stdout = sys.stderr
    print "No dates left after restrictions"
    sys.exit(102)

print len(result), 1, 1
for r in result:
    print "%#.16g" % r
sys.exit(0)
