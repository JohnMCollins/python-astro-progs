#! /usr/bin/env python

# Program to convert normalise fake spectra

import argparse
import os.path
import sys
import numpy as np
import glob

parsearg = argparse.ArgumentParser(description='Normalise fake spectra', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('spectra', type=str, nargs='+', help='Fake spectra files')
parsearg.add_argument('--glob', action='store_true', help='Apply glob to arguments')

resargs = vars(parsearg.parse_args())
specfiles = resargs['spectra']

errors = 0

if resargs['glob']:
    sfs = specfiles
    specfiles = []
    for sf in sfs:
        gs = glob.glob(sf)
        gs.sort()
        specfiles.extend(gs)

for sf in specfiles:
    
    try:
        spec = np.loadtxt(sf, unpack=True)
    except IOError as e:
        print "Cannot load", sf, "error was", e.args[1]
        errors += 1
        continue
    
    div = spec[1][0]
    if abs(div) < 1e-10:
        print "Avoiding division by zero file", sf
        errors += 1
        continue
    
    spec[1] /= div
    
    spec = spec.transpose()
    try:
        np.savetxt(sf, spec, "%#.18g")
    except IOError as e:
        print "Cannot save", sf, "error was", e.args[1]
        errors += 1

if errors:
    print errors, "errors"
    sys.exit(10)
   
