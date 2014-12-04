#! /usr/bin/env python

# Correlate the wavelengths in a set of spectra to try and make them line up

import argparse
import os.path
import sys
import numpy as np
import scipy.signal as ss
import specdatactrl
import datarange
import xmlutil
import datetime
import jdate
import rangearg
import re

parsearg = argparse.ArgumentParser(description='Try to line up X (wavelengths)')
parsearg.add_argument('--specfile', type=str, help='Spectrum data controlfile')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--range', type=str, help='Short name for range in range file or range arg')
parsearg.add_argument('--lower', type=float, default=0.0, help='Lower limit of range')
parsearg.add_argument('--upper', type=float, default=0.0, help='Upper limit of range')
parsearg.add_argument('--useall', action='store_true', help='Do not bother with ranges, use everything')
parsearg.add_argument('--noexcluded', action='store_true', help='Omit excluded spectra')
parsearg.add_argument('--basenum', type=int, default=1, help='Spectrum to use as base, default=first (valid)')
parsearg.add_argument('--basedate', type=str, help='Base date to use, default=first (valid)')

SPC_DOC_ROOT = "spcctrl"
SPC_DOC_NAME = "SPCCTRL"

resvars = vars(parsearg.parse_args())

sf = resvars['specfile']

if sf is None:
    print "No spec data control specified"
    sys.exit(100)

useall = resvars['useall']

# If we're not using all the data, then select the required range

if not useall:
    rf = resvars['rangefile']
    if rf is None:
        # Must be specified by numbers
        try:
            lrange, urange = rangearg.getrangearg(resvars)
        except ValueError as e:
            print e.args[0]
            sys.exit(101)
    else:
        
        # Have specified a range file and name of range
        # Load it up and get the range from that
        
        rname = resvars['range']
        if rname is None:
            print "No range name given"
            sys.exit(102)
        try:
            rangelist = datarange.load_ranges(rf)
        except datarange.DataRangeError as e:
            print "Range load error", e.args[0]
            sys.exit(103)
        try:
            selr = rangelist.getrange(rname)
        except datarange.DataRangeError as e:
            print e.args[0]
            sys.exit(104)
        lrange = selr.lower
        urange = selr.upper

# Load up spectrum file and find which one we want to use to base everything on

noexcl = resvars['noexcluded']
basenum = resvars['basenum']
basedate = resvars['basedate']

try:
    doc, root = xmlutil.load_file(sf, SPC_DOC_ROOT)
    spclist = specdatactrl.SpecDataList(sf)
    cnode = xmlutil.find_child(root, "cfile")
    spclist.load(cnode)
except xmlutil.XMLError as e:
    print "Load control file XML error", e.args[0]
    sys.exit(105)

# Get ourselves reference spectra
# First zap any previous effort

spclist.reset_indiv_x()
spclist.reset_x()

if basedate is not None:
    if re.match('\d+(\.\d+)?$', basedate):
        look4 = float(basedate)
    else:
        matches = re.match('(\d+)\D(\d+)\D(\d+)\D+(\d+)\D(\d+)', basedate)
        if not matches:
            print "Do not understand date argument", basedate
            sys.exit(106)
        yr, mnth, day, hr, minute = map(lambda x: int(x), matches.groups())
        if yr < 1900:
            if yr < 50:
                yr += 2000
            else:
                yr += 1900
        look4 = jdate.datetime_to_jdate(datetime.datetime(yr, mnth, day, hr, minute))
    look4 = round(look4, 4)
    sel = -1
    for n, dataset in enumerate(spclist.datalist):
        if noexcl and dataset.discount: continue
        if round(dataset.modbjdate, 4) == look4 or round(dataset.modjdate, 4) == look4:
            sel = n
            break
    if sel < 0:
        print "Could not find spectrum corresponding to date of", basedate
        sys.exit(107)
else:
    sel = resvars['basenum'] - 1
    if sel < 0: sel = 0
    try:
        while noexcl and spclist.datalist[sel].discount:
            sel += 1
    except IndexError:
        print "Run off end of spectrum list at", sel
        sys.exit(108)

# OK we're ready to roll

print "Loading data"

spclist.loadfiles()

print "Load complete, generating reference x/y values"



for n, dataset in enumerate(spclist.datalist):
    
    if n == sel: continue
    
    print "Doing spectrum for", jdate.display(dataset.modbjdate)
