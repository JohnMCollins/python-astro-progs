#! /usr/bin/env python

import argparse
import sys
import string
import remgeom

parsearg = argparse.ArgumentParser(description='Set Rem geom parameters', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--reset', action='store_true', help='Initialise to standard')
parsearg.add_argument('--width', type=float, help='Width of plots')
parsearg.add_argument('--height', type=float, help='height of plots')
parsearg.add_argument('--trimbottom', type=int, help='Pixels to trim off bottom of picture')
parsearg.add_argument('--trimleft', type=int, help='Pixels to trim off left of picture')
parsearg.add_argument('--trimright', type=int, help='Pixels to trim off right of picture')
parsearg.add_argument('--trimtop', type=int, help='Pixels to trim off top of picture')

resargs = vars(parsearg.parse_args())
doreset = resargs['reset']
width = resargs['width']
height = resargs['height']
trimbottom = resargs['trimbottom']
trimleft = resargs['trimleft']
trimright = resargs['trimright']
trimtop = resargs['trimtop']

changes = 0

if doreset:
    rg = remgeom.RemGeom()
    changes += 1
else:
    rg = remgeom.load()
if width is not None:
    rg.width = width
    changes += 1
if height is not None:
    rg.height = height
    changes += 1
if trimbottom is not None:
    rg.trims.bottom = trimbottom
    changes += 1
if trimleft is not None:
    rg.trims.left = trimleft
    changes += 1
if trimright is not None:
    rg.trims.right = trimright
    changes += 1
if trimtop is not None:
    rg.trims.top = trimtop
    changes += 1

print "Width: %.2f" % rg.width
print "height: %.2f" % rg.height
print "Trimtop: %d" % rg.trims.top
print "Trimbottom: %d" % rg.trims.bottom
print "Trimleft: %d" % rg.trims.left
print "Trimright: %d" % rg.trims.right

if changes > 0:
    remgeom.save(rg)
