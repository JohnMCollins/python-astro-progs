#! /usr/bin/env python

import argparse
import numpy as np
import string
import sys
import os
import os.path
import glob
import noise

parsearg = argparse.ArgumentParser(description='Add noise to fake spectra')
parsearg.add_argument('specs', type=str, nargs='+', help='Input spectra')
parsearg.add_argument('--glob', action='store_true', help='Apply glob to arguments')
parsearg.add_argument('--suff', type=str, help='Suffix to append to file names otherwise make one up')
parsearg.add_argument('--snr', type=float, default=10.0, help='SNR of noise to add (db)')
parsearg.add_argument('--gauss', type=float, default=1.0, help='Proportion uniform to gauss noise 0=all uniform 1=all gauss')
parsearg.add_argument('--ycolumn', help='Column in data for Y values', type=int, default=1)

resargs = vars(parsearg.parse_args())

specs = resargs['specs']
if resargs['glob']:
    sfs = specs
    specs = []
    for sf in sfs:
        gs = glob.glob(sf)
        gs.sort()
        specs.extend(gs)

ycolumn = resargs['ycolumn']
snr = resargs['snr']
gauss = resargs['gauss']
if gauss < 0.0 or gauss > 1.0:
    print "Invalid gauss %#.3g should be 0 to 1" % gauss
    sys.exit(10)
suff = resargs['suff']

if suff is None:
    suff = '.' + string.replace("n%#.3g" % snr, ".", "_")
elif len(suff) == 0:
    print "Invalid suffix should be at least 1 char"
    sys.exit(11)
elif suff[0] != '.':
    suff = '.' + suff

errors = 0
ok = 0
for spec in specs:
    try:
        indata = np.loadtxt(spec, unpack=True)
        indata[ycolumn] = noise.noise(indata[ycolumn], snr, gauss)
        np.savetxt(spec + suff, indata.transpose())
    except IndexError:
        print "Invalid y column", ycolumn, "in", spec
        errors += 1
        continue
    except ValueError:
        print "Invalid values in", spec
        errors += 1
        continue
    except IOError as e:
        print "IO Error in", spec, "was", e.args[1]
        errors += 1
    ok += 1

if errors > 0:
    print errors, "error(s) in data"
    sys.exit(1)
