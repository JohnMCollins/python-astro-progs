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
    
    def __init__(self, id, bjd, rv, sn):
        self.id = id
        self.bjd = bjd - 2400000.5
        self.jd = math.floor(self.bjd)
        self.rv = rv
        self.sn = sn
        self.refs = 1

parsearg = argparse.ArgumentParser(description='Process log file and link across data', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--indir', type=str, required=True, help='Input directory name')
parsearg.add_argument('--outdir', type=str, required=True, help='Output directory name')
parsearg.add_argument('--login', type=str, required=True, help='Input log file')
parsearg.add_argument('--rvout', type=str, required=True, help='Output file (in same directory as outdir if not abs)')

resargs = vars(parsearg.parse_args())

indir = resargs['indir']
outdir = resargs['outdir']
infile = resargs['login']
outfile = resargs['rvout']

if os.path.exists(outdir):
    sys.stdout = sys.stderr
    print "Sorry but", outdir, "already exists"
    sys.exit(9)

outdir = os.path.abspath(outdir)

if not os.path.isabs(outfile):
    outfile = os.path.join(outdir, outfile)

# First check input directory and file exists

if not os.path.isdir(indir):
    sys.stdout = sys.stderr
    print indir, "is not a directory"
    sys.exit(10)

# Work out number of orders from suffixes

flist = glob.glob(indir + '/*.[0-9][0-9][0-9]')
if len(flist) == 0:
    sys.stdout = sys.stderr
    print "No spectral orders in", indir
    sys.exit(11)

maxorder = 1 + max([int(k[-3:]) for k in flist])
flist = []

try:
    fin = open(infile)
except IOError as e:
    sys.stdout = sys.stderr
    print "Cannot open", infile, "error was", e.args[1]
    sys.exit(12)

try:
    os.mkdir(outdir)
except OSError as e:
    sys.stdout = sys.stderr
    print "Cannot create", outdir, "error was", e.args[1]
    sys.exit(13)

for p in range(0, maxorder):
    subd = outdir + "/Order.%.3d" % p 
    try:
        os.mkdir(subd)
    except OSError as e:
        sys.stdout = sys.stderr
        print "Cannot create", subd, "error was", e.args[1]
        sys.exit(14)

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
        dat -= 2400000.5
        if pent.rv != em or pent.bjd != dat:
            print "Duplicated ID", r[0]
            print "em %.16g/%.16g dat %.16g/%.16g" % (pent.rv, em, pent.bjd, dat)
        pent.sn = min(pent.sn, snr)
        pent.refs += 1
    else:
        byid[id] = entry(id, dat, em, snr)

ids = byid.keys()
ids.sort()
bydate = dict()
for id in ids:
    ent = byid[id]
    #print "%d: %.16g %.16g %.16g (%d)" % (id, ent.rv, ent.bjd, ent.sn, ent.refs)
    dat = ent.jd
    try:
        bydate[dat].append(ent)
    except KeyError:
        bydate[dat] = [ent]

for dat in bydate.keys():
    ents = bydate[dat]
    if len(ents) == 1:
        ents[0].jd += 0.2   # Off midnight
        continue
    incr = 1.0 / round(len(ents)+9, -1)
    for n,e in enumerate(ents,1):
        e.jd += n * incr 

retarray = []

morder = re.compile('.*\.(\d\d\d)$')
for id in ids:
    ent = byid[id]
    if ent.sn > 600.0:
        continue
    gpatt = "/%d_e2ds*.[0-9][0-9][0-9]" % id
    flist = glob.glob(indir + gpatt)
    if len(flist) != maxorder:
        continue
    dt = jdate.jdate_to_datetime(ent.jd)
    newname = dt.strftime('HARPS.%Y-%m-%dT%H:%M:%S.ascii.')
    for f in flist:
        mo = morder.match(f)
        if mo is None:
            continue
        ordr = mo.group(1)
        try:
            os.link(f, outdir + '/Order.' + ordr + '/' + newname + ordr)
        except OSError as e:
            if e.errno == 18:
                sys.stdout = sys.stderr
                print indir, "and", outdir, "are on different file systems"
                sys.exit(19)
            else:
                sys.stdout = sys.stderr
                print "Link error", e.args[1]
                sys.exit(20)
    retarray.append([ent.bjd, ent.rv/1000.0, ent.sn, ent.jd])

np.savetxt(outfile, retarray)
bname = os.path.basename(outfile)
for n in range(0, maxorder):
    os.link(outfile, outdir + '/Order.%.3d/' % n + bname)
