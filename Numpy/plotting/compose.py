#! /usr/bin/env python

# Integrate the H alpha peaks to get figures for the total values,
# assume continuum is normalised at 1 unless otherwise specified

import argparse
import os.path
import sys
import string
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

parsearg = argparse.ArgumentParser(description='Compose immages into one', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('images', type=str, nargs='+')
parsearg.add_argument('--width', type=float, default=16, help='Display width max')
parsearg.add_argument('--height', type=float, default=8, help='Display height max')
parsearg.add_argument('--output', type=str, help='Output file')
parsearg.add_argument('--rows', type=int, default=1, help='Output rows')
parsearg.add_argument('--cols', type=int, default=0, help='Output columns 0=as needed')

res = vars(parsearg.parse_args())

outfile = res['output']

imagefiles = res['images']
images = []
errors = 0

for im in imagefiles:
    try:
        a = mpimg.imread(im)
        images.append(a)
    except IOError as e:
        print "Error with", im, e.args[1]
        errors += 1

if errors > 0:
    print "Aborting due to errors"
    sys.exit(10)

width = res['width']
height = res['height']
plt.figure(figsize=(width,height))

nrows = res['rows']
ncols = res['cols']
nimages = len(images)

# Special case of one image

if nimages == 1:
    plt.xticks([])
    plt.yticks([])
    plt.imshow(images[0])
    if outfile is not None:
        plt.savefig(outfile)
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
    sys.exit(0)

# Get number of columns required

if ncols <= 0:
    ncols = (nimages + nrows - 1) // nrows

plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

for pl, im in enumerate(images, 1):
    plt.subplot(nrows, ncols, pl)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(im)

if outfile is not None:
    try:
        plt.savefig(outfile)
        sys.exit(0)
    except IOError as e:
        print "Error saving file", outfile, "error was", e.args[1]
        sys.exit(20)
try:
    plt.show()
except KeyboardInterrupt:
    pass
sys.exit(0)

