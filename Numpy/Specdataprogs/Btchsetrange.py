#! /usr/bin/env python

import sys
import os
import os.path
import re
import locale
import argparse
import specdatactrl
import datarange
import specinfo
import miscutils
import numpy.random as nr

lowerupper = re.compile('([^:])+:([^:]+)$')
centrewid = re.compile('([^/]+)/([^/]+)$')

def parse_range(arg):
    """Parse a range argument and return lower, upper limits.
    
    Arguments are as lower:upper or centre/width"""
    
    try:
        mtch = lowerupper.match(arg)
        if mtch is not None:
            lower = float(mtch.group(1))
            upper = float(mtch.group(2))
        else:
            mtch = centrewid.match(arg)
            if mtch is None:
                sys.stdout = sys.stderr
                print "Cannot understand range argument", arg
                sys.exit(12)
            cent = float(mtch.group(1))
            wid = float(mtch.group(2))
            lower = cent - wid/2.0
            upper = cent + wid/2.0
        if lower >= upper or lower <= 0.0:
            sys.stdout = sys.stderr
            print "Cannot understand range argument", arg
            sys.exit(12)
        return  (lower, upper)
    except ValueError:
        sys.stdout = sys.stderr
        print "Invalid float number in", arg
        sys.exit(12)

def parse_colour(arg):
    """Parse a colour argument given as rrggbb"""
    
    if len(arg) != 6:
        sys.stdout = sys.stderr
        print "Cannot understand colour argument", arg
        sys.exit(13)
    try:
        red = int(arg[0:2], 16)
        green = int(arg[2:4], 16)
        blue = int(arg[4:6], 16)
    except ValueError:
        sys.stdout = sys.stderr
        print "Cannot understand colour argument", arg
        sys.exit(13)
    return (red, green, blue)

parsearg = argparse.ArgumentParser(description='Update range in file (batch version)')
parsearg.add_argument('infofile', type=str, help='Spectral info file', nargs=1)
parsearg.add_argument('--name', type=str, help='Range (short) name', required=True)
parsearg.add_argument('--delete', action='store_true', help='Delete specified range')
parsearg.add_argument('--update', action='store_true', help='Update existing range')
parsearg.add_argument('--limits', type=str, help='Range limits as from:to or centre/width')
parsearg.add_argument('--notused', action='store_true', help='Set not-in-use marker')
parsearg.add_argument('--description', type=str, help='Description of range')
parsearg.add_argument('--colour', type=str, help='Colour of display as hex RRGGBB')

res = vars(parsearg.parse_args())

infofile = res['infofile'][0]
rangename = res['name']
deleting = res['delete']
updating = res['update']
limits = res['limits']
notused = res['notused']
descr = res['description']
colour = res['colour']

if not os.path.isfile(infofile):
    infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)
    
try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infofile)
    rlist = inf.get_rangelist()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", infofile
    print "Error was:", e.args[0]
    sys.exit(10)

if deleting and updating:
    sys.stdout = sys.stderr
    print "Am I deleting or updating?"
    sys.exit(2)

try:
    existing_range = rlist.getrange(rangename)
except datarange.DataRangeError:
    existing_range = None

if deleting or updating:
    if existing_range is None:
        sys.stdout = sys.stderr
        print "Range", rangename, "does not exist"
        sys.exit(3)
elif existing_range is not None:
    sys.stdout = sys.stderr
    print "Range", rangename, "already exists, use --update to amend"
    sys.exit(4)

if deleting:
    rlist.removerange(existing_range)
elif updating:
    if limits is not None:
        lower, upper = parse_range(limits)
        existing_range.lower = lower
        existing_range.upper = upper
    existing_range.notused = notused
    if descr is not None:
        existing_range.description = descr
    if colour is not None:
        r, g, b = parse_colour(colour)
        existing_range.red = r
        existing_range.green = g
        existing_range.blue = b
    rlist.setrange(existing_range)
else:
    if limits is None:
        sys.stdout = sys.stderr
        print "Limits not given for range"
        sys.exit(5)
    lower, upper = parse_range(limits)
    if descr is None:
        sys.stdout = sys.stderr
        print "Description not given for range"
    r = g = b = 0
    if colour is not None:
        r, g, b = parse_colour(colour)
    newrange = datarange.DataRange(shortname = rangename, descr = descr, lbound = lower, ubound = upper, notused = notused, red = r, green = g, blue = b)
    rlist.setrange(newrange)  

try:
    inf.set_rangelist(rlist)
    inf.savefile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Could not save info file", infofile
    print "Error was"
    print e.args[0]
    sys.exit(104)
