#! /usr/bin/env python 

import scipy.optimize as so
import numpy as np
import sys
import string
import argparse
import profcalc

def gaussp(xvals, yoffset, xoffset, scale, fhwm):
    """Gauss only with possible y offset"""
    return yoffset + profcalc.calcgauss(xvals, xoffset, scale, fhwm)

def igaussp(xvals, yoffset, xoffset, scale, fhwm):
    """Inverse gauss only with possible y offset"""
    return yoffset - profcalc.calcgauss(xvals, xoffset, scale, fhwm)

def lorentzp(xvals, yoffset, xoffset, scale, fhwm):
    return yoffset + profcalc.calclorentz(xvals, xoffset, scale, fhwm)

def ilorentzp(xvals, yoffset, xoffset, scale, fhwm):
    return yoffset - profcalc.calclorentz(xvals, xoffset, scale, fhwm)

def gausspgaussp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset + profcalc.calcgauss(xvals, xoffset1, scale1, fhwm1) + profcalc.calcgauss(xvals, xoffset2, scale2, fhwm2)

def gausspigaussp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset + profcalc.calcgauss(xvals, xoffset1, scale1, fhwm1) - profcalc.calcgauss(xvals, xoffset2, scale2, fhwm2)

def gaussplorentzp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset + profcalc.calcgauss(xvals, xoffset1, scale1, fhwm1) + profcalc.calclorentz(xvals, xoffset2, scale2, fhwm2)

def gausspilorentzp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset + profcalc.calcgauss(xvals, xoffset1, scale1, fhwm1) - profcalc.calclorentz(xvals, xoffset2, scale2, fhwm2)

def igausspgaussp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset - profcalc.calcgauss(xvals, xoffset1, scale1, fhwm1) + profcalc.calcgauss(xvals, xoffset2, scale2, fhwm2)

def igausspigaussp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset - profcalc.calcgauss(xvals, xoffset1, scale1, fhwm1) - profcalc.calcgauss(xvals, xoffset2, scale2, fhwm2)

def igaussplorentzp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset - profcalc.calcgauss(xvals, xoffset1, scale1, fhwm1) + profcalc.calclorentz(xvals, xoffset2, scale2, fhwm2)

def igausspilorentzp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset - profcalc.calcgauss(xvals, xoffset1, scale1, fhwm1) - profcalc.calclorentz(xvals, xoffset2, scale2, fhwm2)

def lorentzpgaussp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset + profcalc.calclorentz(xvals, xoffset1, scale1, fhwm1) + profcalc.calcgauss(xvals, xoffset2, scale2, fhwm2)

def lorentzpigaussp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset + profcalc.calclorentz(xvals, xoffset1, scale1, fhwm1) - profcalc.calcgauss(xvals, xoffset2, scale2, fhwm2)

def lorentzplorentzp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset + profcalc.calclorentz(xvals, xoffset1, scale1, fhwm1) + profcalc.calclorentz(xvals, xoffset2, scale2, fhwm2)

def lorentzpilorentzp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset + profcalc.calclorentz(xvals, xoffset1, scale1, fhwm1) - profcalc.calclorentz(xvals, xoffset2, scale2, fhwm2)

def ilorentzpgaussp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset - profcalc.calclorentz(xvals, xoffset1, scale1, fhwm1) + profcalc.calcgauss(xvals, xoffset2, scale2, fhwm2)

def ilorentzpigaussp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset - profcalc.calclorentz(xvals, xoffset1, scale1, fhwm1) - profcalc.calcgauss(xvals, xoffset2, scale2, fhwm2)

def ilorentzplorentzp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset - profcalc.calclorentz(xvals, xoffset1, scale1, fhwm1) + profcalc.calclorentz(xvals, xoffset2, scale2, fhwm2)

def ilorentzpilorentzp(xvals, yoffset, xoffset1, scale1, fhwm1, xoffset2, scale2, fhwm2):
    return yoffset - profcalc.calclorentz(xvals, xoffset1, scale1, fhwm1) - profcalc.calclorentz(xvals, xoffset2, scale2, fhwm2)

Whichrout = ((gaussp, gausspgaussp, gausspigaussp, gaussplorentzp, gausspilorentzp),
            (igaussp, igausspgaussp, igausspigaussp, igaussplorentzp, igausspilorentzp),
            (lorentzp, lorentzpgaussp, lorentzpigaussp, lorentzplorentzp, lorentzpilorentzp),
            (ilorentzp, ilorentzpgaussp, ilorentzpigaussp, ilorentzplorentzp, ilorentzpilorentzp))

parsearg = argparse.ArgumentParser(description='Deduce flux parameters from file')
parsearg.add_argument('fluxfile', type=str, nargs=1)
parsearg.add_argument('--first', type=str, default="gauss", help='Main profile shape')
parsearg.add_argument('--second', type=str, default="none", help='Secondary profile shape')

resargs = vars(parsearg.parse_args())

fluxfile = resargs['fluxfile'][0]
firstprof = resargs['first']
secondprof = resargs['second']

NONE = 0
GAUSS = 1
IGAUSS = 2
LORENTZ = 3
ILORENTZ = 4

tlookup = dict(none = NONE, gauss = GAUSS, igauss = IGAUSS, lorentz = LORENTZ, ilorentz = ILORENTZ, g = GAUSS, ig = IGAUSS, l = LORENTZ, il = ILORENTZ, n = NONE)

firstprof = string.lower(firstprof)
secondprof = string.lower(secondprof)

try:
    indat = np.loadtxt(fluxfile, unpack=True)
except IOError as e:
    print "Cannot read", fluxfile, "error was", e.args[1]

try:
    ftype = tlookup[firstprof]
except KeyError:
    print "Unknown profile type", firstprof
    sys.exit(10)

try:
    stype = tlookup[secondprof]
except KeyError:
    print "Unknown profile type", secondprof
    sys.exit(11)

if ftype == NONE:
    print "Cannot  have NONE as first profile"
    sys.exit(12)

proc = Whichrout[ftype-1][stype]

rnames = ('yoffset', 'xoffset', 'scale', 'fhwm', 'xoffset2', 'scale2', 'fhwm2')

if stype == NONE:
    primewith = [0.0, 0.0, 1.0, 50.0]
else:
    primewith = [0.0, 0.0, 1.0, 50.0, 0.0, 1.0, 50.0]
results, cov = so.curve_fit(proc, indat[0], indat[1], primewith)

results = list(results)
vars = list(cov.diagonal())

for n, v, cv in zip(rnames, results, vars):
    print n, '=', v, ':', cv






