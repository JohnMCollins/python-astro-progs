#! /usr/bin/env python

import os
import os.path
import sys
import numpy as np
import argparse
import string
import math
import glob
import re
import jdate

parsearg = argparse.ArgumentParser(description='Merge in RV values from file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--inew', type=str, required=True, help='EW file in')
parsearg.add_argument('--rvin', type=str, required=True, help='RV file')
parsearg.add_argument('--outfile', type=str, required=True, help='Output file')

resargs = vars(parsearg.parse_args())

inew = resargs['inew']
rvin = resargs['rvin']
outfile = resargs['outfile']

try:
	rvinfile = open(rvin)
except IOError as e:
	print "Cannot open", rvin, "error was", e.args[1]
	sys.exit(9)

dtab = dict()

for lin in rvinfile:
	lin = string.strip(lin)
	bjd, rv, erv = [float(x) for x in string.split(lin)]
	bjd -= 0.5
	dtab[round(bjd,5)] = (bjd, rv, erv)

rvinfile.close()	

try:
    rvdata = np.loadtxt(inew, unpack=True)
except IOError as e:
    sys.stdout = sys.stderr
    print "Cannot open", rvin, "error was", e.args[1]
    sys.exit(12)

rvarr = []

ok = 0
missed = 0
for d in rvdata[0]:
	try:
		bjd, rv, erv = dtab[round(d, 5)]
		rvarr.append((rv, erv))
		ok += 1
	except KeyError:
		print "Unknown date", d, jdate.display(d)
		rvarr.append((0.0, 0.0))
		missed += 1

rvarr = np.array(rvarr).transpose()
rvarr /= 1000.0
print "Maatched", ok, "dates, no data for", missed

results = np.concatenate((rvdata[0:1,:],rvarr[:,:],rvdata[1:,:]),axis=0)

np.savetxt(outfile, results.transpose())

