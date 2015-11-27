#! /usr/bin/env python

# Analyse results of running repeated periodicity scans

import sys
import os
import string
import re
import os.path
import math
import argparse
import numpy as np

def rootms(vals, n):
    """Return root mean square difference from n"""
    return math.sqrt(np.mean((vals - n)**2))

parsearg = argparse.ArgumentParser(description='Classify noise.spike files')
parsearg.add_argument('spfiles', type=str, nargs='+', help='Periodogram results')
parsearg.add_argument('--thresh', type=float, default=5.0, help='Percent threshold for accepting result')

resargs = vars(parsearg.parse_args())

resfiles = resargs['spfiles']
thresh = resargs['thresh'] / 100.0

noisere = re.compile('n(\d+)')
spre = re.compile('sp([123]+)')
hasew = re.compile('ew')

badres = []
okres = []
for rf in resfiles:
    
    try:
        fin = open(rf)
    except:
        sys.stdout = sys.stderr
        print "Could not open", rf
        sys.stdout = sys.__stdout__
        continue
    
    for inline in fin:
        
        try:
            per, incl, fname, calc = string.split(inline, ' ')
            per = float(per)
            incl = float(incl)
            calc = float(calc)
        except ValueError:
            sys.stdout = sys.stderr
            print "Could not understand", rf
            sys.stdout = sys.__stdout__
            break
        
        if not hasew.search(fname): continue
        
        m = noisere.search(fname)
        noise = 0.0
        if m:
            noise = float(m.group(1))

        sp1 = sp2 = sp3 = False      
        sp = spre.search(fname)
        if sp:
            nn = int(sp.group(1))
            
            if nn >= 100:
                sp1 = sp2 = sp3 = True
            elif nn >= 20:
                sp2 = sp3 = True
            elif nn == 13:
                sp1 = sp3 = True
            elif nn == 12:
                sp1 = sp2 = True
            elif nn == 3:
                sp3 = True
            elif nn == 2:
                sp2 = True
            else:
                sp1 = True
             
        res = (per, calc, incl, noise, sp1, sp2, sp3)
        if abs(per - calc) / per <= thresh:
            okres.append(res)
        else:
            badres.append(res)
    
    fin.close()
    
print "okres=", len(okres)
print "badres=", len(badres)
