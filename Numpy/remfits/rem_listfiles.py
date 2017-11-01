#! /usr/bin/env python

# Display columns in obs times file

import os.path
import sys
import numpy as np

sys.argv.pop(0)

for arg in sys.argv:
    try:
        conts = np.loadtxt(arg, unpack=True)
        print arg, "-", conts.shape[0], "columns"
        for n,col in enumerate(conts):
            print "\tColumn", n+1, "min", col.min(), "max", col.max() 
    except (IOError, TypeError, ValueError):
        print "Cannot read", arg


