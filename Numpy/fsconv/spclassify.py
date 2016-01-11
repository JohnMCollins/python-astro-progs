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

class Accdict(object):
    """Class for supporting auto-creating dictionary of vectors"""
    
    def __init__(self):
        self.dicttab = dict()
        
    def append(self, key, value):
        """Append value to vector for key, creating it if it exists"""
        try:
            self.dicttab[key].append(value)
        except KeyError:
            self.dicttab[key] = [value]

    def plus(self, key):
        """Add one to value"""
        try:
            self.dicttab[key] += 1
        except KeyError:
            self.dicttab[key] = 1

    def keys(self):
        """Get sorted list of keys from dictionary"""
        return sorted(self.dicttab.keys())
    
    def __getitem__(self, key):
        try:
            return self.dicttab[key]
        except KeyError:
            return 0
    
    def __len__(self):
        return  len(self.dicttab)

spiketypes = dict(none = 0, sp3 = 1, sp2 = 2, sp1 = 3, sp23 = 4, sp13 = 5, sp12 = 6, sp123 = 7, sp1234 = 8)
spikedescr = ('None', 'Peak 3', 'Peak 2', 'Peak 1', 'Peaks 2 & 3', 'Peaks 1 & 3', 'Peaks 1 & 2', 'Peaks 1,2,3', 'Peaks 1-4')

parsearg = argparse.ArgumentParser(description='Classify noise.spike files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('spfiles', type=str, nargs='+', help='Periodogram results')
parsearg.add_argument('--thresh', type=float, default=5.0, help='Percent threshold for accepting result')
parsearg.add_argument('--minp', type=float,default=-1.0, help='Minimum period to count')
parsearg.add_argument('--maxp', type=float,default=1e10, help='Maximum period to count')
parsearg.add_argument('--imin', type=float,default=0.0, help='Minimum inclination to count')
parsearg.add_argument('--imax', type=float,default=90.0, help='Maximum inclination to count')
parsearg.add_argument('--spreq', type=str, help='Spike type required')

resargs = vars(parsearg.parse_args())

resfiles = resargs['spfiles']
thresh = resargs['thresh'] / 100.0
minp = resargs['minp']
maxp = resargs['maxp']
imin = resargs['imin']
imax = resargs['imax']
spreq = resargs['spreq']

noisere = re.compile('n([-.0-9]+)')
spre = re.compile('(sp[1234]+)')
hasew = re.compile('ew')

Byspike = Accdict()

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
            print "Could not understand", rf, "line=", inline
            sys.stdout = sys.__stdout__
            break

        if not hasew.search(fname): continue
        if per < minp or per > maxp: continue
        if incl < imin or incl > imax: continue
        
        m = noisere.search(fname)
        noise = 0.0
        if m:
            noise = float(m.group(1))

        spiketype = 0     
        sp = spre.search(fname)
        if sp:
            try:
                spiketype = spiketypes[sp.group(1)]
            except KeyError:
                pass

        Byspike.append(spiketype, (per, calc, incl, noise)) 
    
    fin.close()

for spiketype in Byspike.keys():
    
    if spreq is None:
        print "%s:" % spikedescr[spiketype]
    elif spiketypes[spreq] != spiketype:
        continue

    bynoiserr = Accdict()
    bynoisen = Accdict()
    bynoiseok = Accdict()
    
    for per, calc, incl, noise in Byspike[spiketype]:       
        bynoisen.plus(noise)
        err = abs(per-calc) / per
        if err <= thresh:
            bynoiseok.plus(noise)
            bynoiserr.append(noise, err*err)
    
    for noise in bynoisen.keys():
        err = math.sqrt(reduce(lambda x,y: x+y, bynoiserr[noise])/len(bynoiserr))
        print "%.1f %.2f %.1f" % (noise, err, float(bynoiseok[noise]) * 100.0 / float(bynoisen[noise])) 
