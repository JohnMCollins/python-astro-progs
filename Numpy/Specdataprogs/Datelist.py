#! /usr/bin/env python

import sys
import os
import os.path
import argparse
import miscutils
import specinfo
import jdate

parsearg = argparse.ArgumentParser(description='List dates and spectrum numbers in info file')
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)

res = vars(parsearg.parse_args())

infofile = res['infofile'][0]

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
for df in ctrllist.datalist:
    dt = jdate.jdate_to_datetime(df.modjdate)
    print "%d: %s" % (n, dt.strftime("%d/%m/%y %H:%M:%S"))
    n += 1
