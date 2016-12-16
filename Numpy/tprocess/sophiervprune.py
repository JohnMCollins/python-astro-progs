#! /usr/bin/env python

import os
import os.path
import sys
import numpy as np
import argparse
import jdate

parsearg = argparse.ArgumentParser(description='Get RV file from Sophie and try to identify anomalies', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--rvin', type=str, required=True, help='Input file (from sophierv)')
parsearg.add_argument('--rvout', type=str, required=True, help='Output file')
parsearg.add_argument('--minsnr', type=float, default=1.0, help='Minimum acceptable SNR')

resargs = vars(parsearg.parse_args())

infile = resargs['rvin']
outfile = resargs['rvout']
minsnr = resargs['minsnr']

if not os.path.isfile(infile):
    sys.stdout = sys.stderr
    print infile, "is not a file"
    sys.exit(11)

try:
    fin = open(infile, "r")
except IOError:
    sys.stdout = sys.stderr
    print "Cannot open", infile
    sys.exit(12)

intab = np.loadtxt(infile, unpack=True)

# Do trimming now

lenbefore = intab.shape[-1]
intab = intab[:, intab[5]>= minsnr]
lenafter = intab.shape[-1]
iids=np.array(intab[0], dtype=np.int)

# Find duplications in reverse

dups = np.where(np.diff(iids)==0)[0]
dups = - np.array(sorted(-dups))

medrv = np.median(intab[3])

for d in dups:
    line1 = intab[:,d]
    line2 = intab[:,d+1]
    
    id1, jd1, bjd1, rv1, erv1, sn1 = line1
    id2, jd2, bjd2, rv2, erv2, sn2 = line2
    
    print "Duplicate id %d, rv1=%.4e rv2=%.4e" % (int(id1), rv1, rv2)
    
    if abs(medrv-rv1) < abs(medrv-rv2):
        print "Choosing rv1 as closer to median of %.4e" % medrv
        intab = np.delete(intab, d+1, axis=1)
    else:
        print "Choosing rv2 as closer to median of %.4e" % medrv
        intab = np.delete(intab, d, axis=1)

lenfinal = intab.shape[-1]
np.savetxt(outfile, intab.transpose())

print "Length at start = %d\n%d removed as below SNR %.2f\n%d duplicates removed, finally %d" % (lenbefore, lenbefore-lenafter, minsnr, lenafter-lenfinal, lenfinal)
