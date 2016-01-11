#! /usr/bin/env python

import sys
import os
import os.path
import re
import string
import locale
import argparse
import datetime

import numpy as np

import miscutils
import specdatactrl
import datarange
import specinfo
import jdate

parsearg = argparse.ArgumentParser(description='Batch mode set jdates from file names', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infofiles', type=str, help='Specinfo file', nargs='+')
parsearg.add_argument('--force', action='store_true', help='Force change even if dates set')

res = vars(parsearg.parse_args())

infofiles = res['infofiles']
forceit = res['force']

errors = 0

for infofile in infofiles:
    
    if not os.path.isfile(infofile):
        infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)
    
    try:
        inf = specinfo.SpecInfo()
        inf.loadfile(infofile)
        ctrllist = inf.get_ctrlfile()
    except specinfo.SpecInfoError as e:
        sys.stdout = sys.stderr
        print "Cannot load info file", infofile
        print "Error was:", e.args[0]
        errors += 1
        sys.stdout = sys.__stdout__
        continue
    
    if len(ctrllist.datalist) == 0:
        sys.stdout = sys.stderr
        print "No data files referred to in", infofile
        errors += 1
        sys.stdout = sys.__stdout__
        continue
    
    if ctrllist.datalist[0].modjdate != 0 and not forceit:
        sys.stdout = sys.stderr
        print "Already got dates in", infofile
        errors += 1
        sys.stdout = sys.__stdout__
        continue
    
    cerrors = 0
    
    for spec in ctrllist.datalist:
        
        jd = specdatactrl.jd_parse_from_filename(spec.filename)
        if jd is None:
            sys.stdout = sys.stderr
            print "File name format not understood in", infofile
            errors += 1
            sys.stdout = sys.__stdout__
            cerrors += 1
            break
        spec.modjdate = jd

        if cerrors != 0: continue
        
        try:
            inf.savefile()
        except specinfo.SpecInfoError as e:
            sys.stdout = sys.stderr
            print "Cannot re-save", infofile
            print "Error was", e.args[0]
            errors += 1
            sys.stdout = sys.__stdout__
 
if errors != 0:
     print errors, "files had errors"
     sys.exit(2)
sys.exit(0)