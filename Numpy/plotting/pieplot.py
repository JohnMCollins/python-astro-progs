#! /usr/bin/env python

# Integrate the H alpha peaks to get figures for the total values,
# assume continuum is normalised at 1 unless otherwise specified

import argparse
import os.path
import sys
import string
import numpy as np
import matplotlib.pyplot as plt

class rangedescr(object):
    """Describe required range"""
    
    def __init__(self, lower, upper, colour, label, exp=False):
        
        self.lower = lower
        self.upper = upper
        self.colour = colour
        self.label = label
        self.count = 0
        self.explode = exp
    
    def checkrange(self, vals):
        """Bump count according to the numbers in range and return what isn't in the range"""
        sel = (vals >= self.lower) & (vals <= self.upper)
        self.count += np.count_nonzero(sel)
        return vals[~sel]

# According to type of display select column, xlabel  for hist, ylabel for plot

parsearg = argparse.ArgumentParser(description='Plot ranges on pie charter', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ranges', type=str, nargs='+', help='ranges as low:high:colour:e to explode')
parsearg.add_argument('--infile', type=str, required=True, help='Input file of numbers, will be flattened')
parsearg.add_argument('--outfile', type=str, help='Output file if required, else display')
parsearg.add_argument('--title', type=str, default='Range dist', help='Title for window')
parsearg.add_argument('--width', type=float, default=6, help='Display width')
parsearg.add_argument('--height', type=float, default=6, help='Display height')
parsearg.add_argument('--pieradius', type=float, default=1.0, help='Pie radius')
parsearg.add_argument('--restcolour', type=str, default='k', help='Colour for rest segment')
parsearg.add_argument('--restlabel', type=str, default='Rest', help='Label for rest segment')
parsearg.add_argument('--restexp', action='store_true', help='Select whether rest segment is exploded')
parsearg.add_argument('--explodeamt', type=float, default=.1, help='Explode amount')
parsearg.add_argument('--legend', type=str, help='Legend for pie')

resargs = vars(parsearg.parse_args())
rangeargs = resargs['ranges']
infile = resargs['infile']
outfile = resargs['outfile']
title = resargs['title']
dims = (resargs['width'], resargs['height'])
leg = resargs['legend']

restcolour = resargs['restcolour']
restlab = resargs['restlabel']
restexp = resargs['restexp']
explodeamount = resargs['explodeamt']
pierad = resargs['pieradius']
restcount = 0

rangelist = []

try:
    inf = np.loadtxt(infile, unpack=True)
except IOError as e:
    print "Error loading input file", infile
    print "Error was", e.args[1]
    sys.exit(100)
except (ValueError,TypeError):
    print "Conversion error input file", infile
    sys.exit(101)

inf = inf.flatten()

for ra in rangeargs:
    
    parts = string.split(ra, ':')
    
    if len(parts) == 4:
        lows, highs, col, lab = parts
        expl = False
    elif len(parts) == 5:
        lows, highs, col, lab, exp = parts
        expl = True
    else:
        print "Do not understand range arg", ra
        sys.exit(102)
    
    try:
        lows = float(lows)
        highs = float(highs)
    except ValueError:
        print "Expected numeric low/high at", ra
        sys.exit(103)
    
    if lows >= highs:
        print "Invalid range in", ra
        sys.exit(104)
    
    rangelist.append(rangedescr(lows, highs, col, lab, expl))

for ra in rangelist:
    inf = ra.checkrange(inf)

restcount += len(inf)

labs = []
expls = []
sizes = []
cols = []

for ra in rangelist:
    if ra.count != 0:
        labs.append(ra.label)
        cols.append(ra.colour)
        sizes.append(ra.count)
        ramt = 0.0
        if ra.explode:
            ramt = explodeamount
        expls.append(ramt)

if restcount != 0:
    labs.append(restlab)
    cols.append(restcolour)
    sizes.append(restcount)
    ramt = 0.0
    if restexp:
        ramt = explodeamount
    expls.append(ramt)

fig = plt.figure(figsize=dims)
fig.canvas.set_window_title(title)
plt.pie(sizes, labels=labs, shadow=True, explode=expls, colors=cols, autopct='%1.1f%%', radius=pierad)
if leg is not None:
    plt.legend([leg], handlelength=0, handletextpad=0, fancybox=True, loc='lower right')
if outfile is None:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
else:
    fig.savefig(outfile)
sys.exit(0)
