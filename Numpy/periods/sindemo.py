#! /usr/bin/env python

import numpy as np
import argparse

parsearg = argparse.ArgumentParser(description='Display complex sin function')
parsearg.add_argument('out', type=str, nargs=1, help='Output file')

resargs = vars(parsearg.parse_args())

X = np.arange(-4, 4, 0.25)
Y = np.arange(-4, 4, 0.25)
X, Y = np.meshgrid(X, Y)
CY = np.zeros_like(Y,dtype=np.complex128)
CY += Y
CY *= 0+1j
R = X + CY
Z = np.real(np.sin(R))

np.save(resargs['out'][0], np.array((X,Y,Z)))
