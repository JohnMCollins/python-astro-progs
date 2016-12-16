#! /usr/bin/env python

import os
import sys
import numpy as np
import argparse
import string
import re
import pycurl
from StringIO import StringIO

parsearg = argparse.ArgumentParser(description='Get RV values from Sophie', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objname', type=str, nargs=1, help='Object name')
parsearg.add_argument('--outfile', type=str, help='Output file if required')

resargs = vars(parsearg.parse_args())

objname = resargs['objname'][0]
outf = resargs['outfile']

buffer = StringIO()
c = pycurl.Curl()
c.setopt(c.URL,'http://atlas.obs-hp.fr/sophie/sophie.cgi?n=sophiecc&a=t&ob=ra,seq&c=o&o=' + objname + '&d=objname,seq,mjd,bjd,rv,dvrms,sn26')
c.setopt(c.WRITEDATA, buffer)
c.perform()
status_code = c.getinfo(c.RESPONSE_CODE)
if status_code != 200:
    print "Request failed, code =", status_code
    sys.exit(10)
c.close()
body = buffer.getvalue()
mtch=re.compile('\s+')

if outf is not None:
    fl = open(outf, 'w')
    sys.stdout = fl

nlines = 0
for line in string.split(body, "\n"):
    parts = mtch.split(string.strip(line))
    if len(parts) == 0:
        continue
    if  parts[0] == '!!':
        sys.stdout = sys.stderr
        print "Could not find", objname
        sys.exit(11)
    if len(parts) != 7:
        continue
    nobjname = parts.pop(0)
    nlines += 1
    print string.join(parts, ' ')

sys.stdout = sys.stderr
print "Object name =", nobjname, "with", nlines, "lines"
