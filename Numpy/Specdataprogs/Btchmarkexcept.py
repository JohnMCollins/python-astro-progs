#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse

import scipy.integrate as si
import scipy.optimize as so

import miscutils
import specdatactrl
import datarange
import specinfo
import simbad
import doppler

parsearg = argparse.ArgumentParser(description='Batch mode mark exceptional')
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)
parsearg.add_argument('--include', type=str, help='Comma-separated ranges to take points from (otherwise whole)')
parsearg.add_argument('--exclude', type=str, default='halpha', help='Comma-separated ranges to exclude (default halpha)')
parsearg.add_argument('--existing', type=str, default='leave', help='Actuion with existing marks leave/reset/clear')
parsearg.add_argument('--median', action='store_true', help='Use median rather than mean')
parsearg.add_argument('--upper', type=float, default=3.0, help='Upper mult of SD to exclude above')
parsearg.add_argument('--lower', type=float, default=2.0, help='Lower mult of SD to exclude below')

res = vars(parsearg.parse_args())

infofile = res['infofile'][0]
inclranges = res['include']
exclranges = res['exclude']
existact = res['existing']
medians = res['median']
uppersd = res['upper']
lowersd = res['lower']

if not os.path.isfile(infofile):
    infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infofile)
    ctrllist = inf.get_ctrlfile()
    rangl = inf.get_rangelist()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", infofile
    print "Error was:", e.args[0]
    sys.exit(100)

try:
    ctrllist.loadfiles()
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Problem loading files via", infofile
    print "Error was:", e.args[0]
    sys.exit(101)

inclrange = None
exclrange = None

try:
    if inclranges is not None and len(inclranges) != 0:
        inclrange = datarange.Rangeset(rangl)
        inclrange.parseset(inclranges)
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print "Problem seting include ranges"
    print "Error was:", e.args[0]
    sys.exit(102)
try:
    if exclranges is not None and len(exclranges) != 0:
        exclrange = datarange.Rangeset(rangl)
        exclrange.parseset(exclranges)
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print "Problem seting exclude ranges"
    print "Error was:", e.args[0]
    sys.exit(103)

# Remember how many we started with

pre_existing = ctrllist.count_markers()

# Do what we have to to reset markers etc

ndone = 0
if existact is not None and len(existact) != 0:
    existact = string.upper(existact[0:1])
    if  existanct == 'R':
        ndone = ctrllist.reset_markers()
    elif existact == 'C':
        ndone = ctrllist.clear_remarks()

# So now we actually do the job



