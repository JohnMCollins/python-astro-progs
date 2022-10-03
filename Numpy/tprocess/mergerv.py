#! /usr/bin/env python

import os
import os.path
import sys
import numpy as np
import argparse
import string
import math
import glob
import re
import jdate

class hadeof(Exception): pass

class entry(object):
    """Keep details of rv file entry"""
    
    def __init__(self, id, jd, bjd, rv, erv, sn):
        self.id = id
        self.bjd = float(bjd) - 2400000.5
        self.jd = math.floor(self.bjd)
        self.rv = float(rv)
        self.erv = float(erv)
        self.sn = float(sn)

class logentry(object):
    """Keep details of rv file entry"""
    
    def __init__(self, id, bjd, rv, sn):
        self.id = id
        self.bjd = bjd - 2400000.5
        self.jd = math.floor(self.bjd)
        self.rv = rv
        self.sn = sn
        self.refs = 1

parsearg = argparse.ArgumentParser(description='Process log file and get rv and erv stuff', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--insoph', type=str, required=True, help='Input sophie parameters')
parsearg.add_argument('--login', type=str, required=True, help='Input log file')
parsearg.add_argument('--rvout', type=str, required=True, help='Output file')

resargs = vars(parsearg.parse_args())

insoph = resargs['insoph']
login = resargs['login']
rvout = resargs['rvout']

try:
	sophin = open(insoph)
except IOError as e:
	print "Cannot open", insoph, "error was", e.args[1]
	sys.exit(9)

idtab = dict()

for lin in sophin:
	lin = string.strip(lin)
	id, jd, bjd, rv, erv, sn = string.split(lin)
	id = int(id)
	nent = entry(id, jd, bjd, rv, erv, sn)
	if id in idtab:
		orig = idtab[id]
		if abs(nent.rv) < abs(orig.rv):
			idtab[id] = nent
	else:
		idtab[id] = nent

sophin.close()	

try:
    fin = open(login)
except IOError as e:
    sys.stdout = sys.stderr
    print "Cannot open", login, "error was", e.args[1]
    sys.exit(12)

mtch_upload = re.compile('HARPS spectrum uploaded\s*:\s*/.*/data/(\d+)_e2ds\.fits')
mtch_bem = re.compile('Barycentric Earth motion\s*:\s*([-\d.]+)')
mtch_bjd = re.compile('Barycentric Julian date\s*:\s*([\d.]+)')
mtch_skip = re.compile('Skipping epoch\s*: SNR.*Maximum.*/data/(\d+)_e2ds\.fits')
mtch_snr = re.compile('SNR\s+@\s+order\s+\d+\s*=\s*([.\d]+)\.\s+.*/data/(\d+)_e2ds\.fits')

results = []

while 1:
    lin = fin.readline()
    if len(lin) == 0:
        sys.stdout = sys.stderr
        print "Could not find first upload in file"
        sys.exit(12)
    lin = string.strip(lin)
    mu = mtch_upload.search(lin)
    if mu is None:
        continue
    curr_id = int(mu.group(1))
    break

# Got first ID or next ID

try:
    while 1:
        # Look for Earth Motion
        while 1:
            lin = fin.readline()
            if len(lin) == 0:
                sys.stdout = sys.stderr
                print "Run out of lines looking for EM after id", curr_id
                sys.exit(13)
            lin = string.strip(lin)
            mem = mtch_bem.search(lin)
            if mem:
                curr_em = float(mem.group(1))
                break

        # Look for date
        
        while 1:
            lin = fin.readline()
            if len(lin) == 0:
                sys.stdout = sys.stderr
                print "Run out of lines looking for date after id", curr_id
                sys.exit(14)
            lin = string.strip(lin)
            mdat = mtch_bjd.search(lin)
            if mdat:
                curr_dat = float(mdat.group(1))
                break
            
        # Read until we find a new spectrum file, in which case all is OK,
        # or until we find it's skipped
        
        while 1:
            lin = fin.readline()
            if len(lin) == 0:
                results.append((curr_id, curr_em, curr_dat, curr_snr))
                raise hadeof
            lin = string.strip(lin)
            msn = mtch_snr.search(lin)
            if msn:
                curr_snr = float(msn.group(1))
                sn_id = int(msn.group(2))
                if sn_id != curr_id:
                    print "Confused by curr_id =", curr_id, "snr id =", sn_id
                continue
            ms = mtch_skip.search(lin)
            if  ms:
                skip_id = int(ms.group(1))
                curr_snr = 1e10
                if curr_id != skip_id:
                    print "Confused by curr_id =", curr_id, "skip id =", skip_id
                continue
            mu = mtch_upload.search(lin)
            if mu:
                results.append((curr_id, curr_em, curr_dat, curr_snr))
                curr_id = int(mu.group(1))
                break
    #end of outer while
except hadeof:
    pass

byid = dict()
for r in results:
    id, em, dat, snr = r
    if id in byid:
        pent = byid[id]
        mdat = dat - 2400000.5
        if pent.rv != em or pent.bjd != mdat:
            print "Duplicated ID", r[0]
            print "em %.16g/%.16g dat %.16g/%.16g" % (pent.rv, em, pent.bjd, dat)
        pent.sn = min(pent.sn, snr)
        pent.refs += 1
    else:
        byid[id] = logentry(id, dat, em, snr)

ids = byid.keys()
ids.sort()
bydate = dict()
for dat in bydate.keys():
    ents = bydate[dat]
    if len(ents) == 1:
        ents[0].jd += 0.2   # Off midnight
        continue
    incr = 1.0 / round(len(ents)+9, -1)
    for n,e in enumerate(ents,1):
        e.jd += n * incr

final_results = []
skipped = 0
for r in results:
    id, em, dat, snr = r
    if snr > 600.0:
		continue
    try:
        tent = idtab[id]
        mdat = dat - 2400000.5
        td = round(mdat, 5)
        qd = round(tent.bjd, 5)
        if  td != qd:
            print "Dates differ %.16g/%.16g" % (tent.bjd, mdat)
        final_results.append((dat, em, tent.rv, tent.erv))
    except KeyError:
        skipped += 1
        final_results.append((dat, em, -1e10, -1e9))
        pass

print "Skipped", skipped
np.savetxt(rvout, final_results)

