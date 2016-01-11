#! /usr/bin/env python

import os
import sys
import math
import numpy as np
import argparse

parsearg = argparse.ArgumentParser(description='Calculate temps T0 and T2 for LUT given T1 and possibly diff between T0 and T2',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('t1', type=float, nargs=1, help='Temperature T1 in K')
parsearg.add_argument('--diff', type=float, default=1000.0, help='Difference between T0 and T2 default 1000')

resargs = vars(parsearg.parse_args())

T1 = resargs['t1'][0]
tdiff = resargs['diff']

# Set up polynomial from 2 * T1**4 = (T2**4 + T0**4) where T2 = T0+tdiff, T2**4 = T0**4 + 4*T0**3*tdiff etc

coeffs = np.array([2.0, 4 * tdiff, 6 * tdiff**2, 4 * tdiff**3, tdiff**4 - 2 * T1**4])

roots = np.roots(coeffs)
rroots = np.real_if_close(roots, 1e10)
rrroots = np.real(rroots[np.imag(rroots) == 0.0])
if len(rrroots) > 1:
    rrroots = rrroots[rrroots > 0.0]
    rrroots = rrroots[rrroots < T1]
if len(rrroots) != 1:
    print "Sorry could not discover T0 roots were", roots
    sys.exit(10)
T0 = rrroots[0]
T2 = T0 + tdiff

RT0 = round(T0)
RT2 = round(T2)

print "T0 =", RT0
print "T1 =", T1
print "T2 =", RT2
