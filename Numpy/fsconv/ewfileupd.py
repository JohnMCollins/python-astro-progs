#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse
import numpy as np

parsearg = argparse.ArgumentParser(description='Convert EW files to new standard format')
parsearg.add_argument('ewfile', type=str, help='EW file', nargs='+')

resargs = vars(parsearg.parse_args())

ewfiles = resargs['ewfile']

errors = 0

for ewf in ewfiles:
    
    try:
        infile = np.loadtxt(ewf, unpack=True)
    except IOError as e:
        sys.stdout = sys.stderr
        print "Cannot open", ewf
        print "Error was:"
        print e.args[1]
        sys.stdout = sys.__stdout__
        errors += 1
        continue
    except ValueError as e:
        sys.stdout = sys.stderr
        print "Conversion problem with", ewf
        print "Error was:"
        print e.args[0]
        sys.stdout = sys.__stdout__
        errors += 1
        continue
    
    if infile.shape[0] == 2:
        
        # Take that as being date, ew and add the other columns
        
        dates, ews = infile
        
        zs = np.zeros_like(ews)
        ones = zs + 1.0
        
        result = np.array([dates, dates, ews, zs, zs, zs, ones, zs])
    
    elif infile.shape[0] == 4:
        
        # Assume that is date/ew/peak size/peak ratio
        
        dates, ews, psizes, prats = infile
        
        zs = np.zeros_like(ews)
        
        result = np.array([dates, dates, ews, zs, psizes, zs, prats, zs])
    
    elif infile.shape[0] == 5:
        
        # Assume that it is date/ew/peak size/peak ratio/log peak ratio
        # Check last two
        
        dates, ews, psizes, prats, lprats = infile
        
        if np.min(prats) < 0.0 or np.max(np.abs(np.round(np.log(prats), 5)-np.round(lprats, 5))) > 1e-4:
            sys.stdout = sys.stderr
            print "Cannot convert", ewf
            print "Expecting 5 column file to be peak rat/log peak rat in last 2 columns"
            sys.stdout = sys.__stdout__
            errors += 1
            continue
    
        zs = np.zeros_like(ews)
        
        result = np.array([dates, dates, ews, zs, psizes, zs, prats, zs])
    
    else:
        sys.stdout = sys.stderr
        print "Cannot understand file", ewf, "which has", infile.shape[0], "columns"
        sys.stdout = sys.__stdout__
        errors += 1
        continue
    
    try:
        np.savetxt(ewf, result.transpose())
    except IOError as e:
        sys.stdout = sys.stderr
        print "Cannot save", ewf
        print "Error was:"
        print e.args[1]
        sys.stdout = sys.__stdout__
        errors += 1

if errors > 0:
    if errors > 1:
        sys.stdout = sys.stderr
        print "There were %d errors" % errors
    else:
        print "There was one error"
    sys.exit(1)
