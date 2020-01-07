#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:59+00:00
# @Email:  jmc@toad.me.uk
# @Filename: setgeom.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:24:29+00:00

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
parsearg.add_argument('--nocoords', action='store_true', help='Suppress coord display')
parsearg.add_argument('--invert', action='store_false', help='Invert image')
parsearg.add_argument('--divisions', type=int, help='Divisions in RA/Dec lines')
parsearg.add_argument('--divprec', type=int, help='Precision for axes')
parsearg.add_argument('--divthresh', type=int, help='Pixels from edge for displaying divisions')
parsearg.add_argument('--racolour', type=str, help='Colour of RA lines')
parsearg.add_argument('--deccolour', type=str, help='Colour of DEC lines')
parsearg.add_argument('--divalpha', type=float, help='Alpha of divisions')
parsearg.add_argument('--objcolour', type=str, help='Object colour or colon-sep list')
parsearg.add_argument('--hilalpha', type=float, help='Object alpha')
parsearg.add_argument('--objtextfs', type=int, help='Font size object labels')
parsearg.add_argument('--textdisp', type=int, help='Displacement of object labels')
parsearg.add_argument('--objfill', action='store_true', help='Fill object markers')

resargs = vars(parsearg.parse_args())
doreset = resargs['reset']
width = resargs['width']
height = resargs['height']
trimbottom = resargs['trimbottom']
trimleft = resargs['trimleft']
trimright = resargs['trimright']
trimtop = resargs['trimtop']

nocoords = resargs['nocoords']
invertim = resargs['invert']
divisions = resargs['divisions']
divprec = resargs['divprec']
divthresh = resargs['divthresh']
racol = resargs['racolour']
deccol = resargs['deccolour']
divalpha = resargs['divalpha']

objfill = resargs['objfill']
objcolour = resargs['objcolour']
objalpha = resargs['hilalpha']
objtextfs = resargs['objtextfs']
textdisp = resargs['textdisp']

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

if nocoords != rg.divspec.nocoords:
    rg.divspec.nocoords = nocoords
    changes += 1
if invertim != rg.divspec.invertim:
    rg.divspec.invertim = invertim
    changes += 1
if divisions is not None:
    rg.divspec.divisions = divisions
    changes += 1
if divprec is not None:
    rg.divspec.divprec = divprec
    changes += 1
if divthresh is not None:
    rg.divspec.divthresh = divthresh
    changes += 1
if racol is not None:
    rg.divspec.racol = racol
    changes += 1
if deccol is not None:
    rg.divspec.deccol = deccol
    changes += 1
if divalpha is not None:
    rg.divspec.divalpha = divalpha
    changes += 1

if objfill != rg.objdisp.objfill:
    rg.objdisp.objfill = objfill
    changes += 1
if objcolour is not None:
    rg.objdisp.objcolour = objcolour.split(":")
    changes += 1
if objalpha is not None:
    rg.objdisp.objalpha = objalpha
    changes += 1
if objtextfs is not None:
    rg.objdisp.objtextfs = objtextfs
    changes += 1
if textdisp is not None:
    rg.objdisp.objtextdisp = textdisp
    changes += 1

print("Width: %.2f" % rg.width)
print("height: %.2f" % rg.height)
print("Trimtop: %d" % rg.trims.top)
print("Trimbottom: %d" % rg.trims.bottom)
print("Trimleft: %d" % rg.trims.left)
print("Trimright: %d" % rg.trims.right)
if nocoords:
    print("No coords")
if invertim:
    print("Invert image")
print("Divisions: %d" % rg.divspec.divisions)
print("Div prec: %d" % rg.divspec.divprec)
print("Divthresh: %d" % rg.divspec.divthresh)
print("RA colour: %s" % rg.divspec.racol)
print("Dec colour: %s" % rg.divspec.deccol)
print("Div alpha: %.3g" % rg.divspec.divalpha)
if objfill:
    print("Fill object highlight")
print("Object colour(s): ", ", ".join(rg.objdisp.objcolour))
print("Object alpha: %.3g" % rg.objdisp.objalpha)
print("Object text font size: %d" % rg.objdisp.objtextfs)
print("Object text displacement: %d" % rg.objdisp.objtextdisp)

if changes > 0:
    remgeom.save(rg)
