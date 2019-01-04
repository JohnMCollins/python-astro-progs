#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:59+00:00
# @Email:  jmc@toad.me.uk
# @Filename: rem_listfiles.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:24:59+00:00

# Display columns in obs times file

import os.path
import sys
import numpy as np

sys.argv.pop(0)

for arg in sys.argv:
    try:
        conts = np.loadtxt(arg, unpack=True)
        print(arg, "-", conts.shape[0], "columns")
        for n,col in enumerate(conts):
            print("\tColumn", n+1, "min", col.min(), "max", col.max())
    except (IOError, TypeError, ValueError):
        print("Cannot read", arg)
