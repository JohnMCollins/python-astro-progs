#! /usr/bin/env python

import os
import os.path
import sys
import numpy as np
import argparse
import string
import glob
import re
import jdate

class entry(object):
    """Keep details of rv file entry"""
    
    def __init__(self, id, jd, bjd, rv, erv, sn):
        self.id = int(id)
        self.jd = jd
        self.bjd = bjd - 2400000.5
        self.rv = rv
        self.erv = erv
        self.sn = sn
        self.used = False

parsearg = argparse.ArgumentParser(description='Get RV file and link across files from Sophie', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--indir', type=str, required=True, help='Input directory name')
parsearg.add_argument('--outdir', type=str, required=True, help='Output directory name')
parsearg.add_argument('--rvin', type=str, required=True, help='Input file (from sophierv)')
parsearg.add_argument('--rvout', type=str, required=True, help='Output file (in same directory as outdir if not abs)')

resargs = vars(parsearg.parse_args())

indir = resargs['indir']
outdir = resargs['outdir']
infile = resargs['rvin']
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

try:
    fin = np.loadtxt(infile)
except IOError as e:
    sys.stdout = sys.stderr
    print infile, "Cannot open", infile, "error was", e.args[0]
    sys.exit(11)

bydate = dict()
byid = dict()
for line in fin:
    ent = entry(*line)
    sid = ent.id
    if sid in byid:
        sys.stdout = sys.stderr
        print "Id %d is duplicated, run prune program" % sid
        sys.exit(16)
    n = ent.jd
    while n in bydate:
        n = round(n+0.001,3)
        ent.jd = n
    bydate[n] = ent
    byid[sid] = ent

# Move to source directory and compile file list

try:
    os.chdir(indir)
except OSError as e:
    sys.stdout = sys.stderr
    print "Unable to select directory", indir, "Error was", e.strerror
    sys.exit(14)

flist = glob.glob('*.[0-9][0-9][0-9]')
if len(flist) == 0:
    sys.stdout = sys.stderr
    print "There do not seem to be any files in", indir
    sys.exit(15)

flist.sort()

mp = re.compile('(\d+).*\.(\d\d\d)$')

maxord = -1
errors = 0
moaned = dict()

for f in flist:
    mtch = mp.match(f)
    if not mtch:
        sys.stdout = sys.stderr
        print "Regex wrong for", f
        sys.exit(16)
    order = int(mtch.group(2))
    if order > maxord:
        maxord = order
    id = int(mtch.group(1))
    if id in byid:
        byid[id].used = True
    else:
        errors += 1
        if id not in moaned:
            moaned[id] = True
            sys.stdout = sys.stderr
            print "Unknown spectral id", id
            sys.sydout = sys.__stdout__

if errors > 0:
    sys.stdout = sys.stderr
    print "Error count =", errors
    sys.stdout = sys.__stdout__

# Now create result directory and order subdirectories

try:
    os.mkdir(outdir)
except OSError as e:
    sys.stdout = sys.stderr
    print "Unable to create directory", outdir, "Error was", e.strerror
    sys.exit(16)

for n in range(0, maxord+1):
    subd = "Order.%.3d" % n
    os.mkdir(os.path.join(outdir, subd))

# Now run through doing the business

try:
    for f in flist:
        mtch = mp.match(f)
        corder = mtch.group(2)
        order = int(corder)
        id = int(mtch.group(1))
        try:
            ent = byid[id]
        except KeyError:
            continue
        dt = jdate.jdate_to_datetime(ent.jd)
        newname = dt.strftime('SOPHIE.%Y-%m-%dT%H:%M:%S.ascii.') + corder
        subd = "Order.%.3d" % order
        newdest = os.path.join(outdir, subd, newname)
        os.link(f, newdest)
except OSError as e:
    if e.errno == 18:
        sys.stdout = sys.stderr
        print indir, "and", outdir, "are on different file systems"
        sys.exit(19)
    else:
        sys.stdout = sys.stderr
        print "Link error with", newdest, e.args[0]
        sys.exit(20)

# Now create RV file

rvf = []

ids = byid.keys()
ids.sort()
for id in ids:
    ent = byid[id]
    if not ent.used:
        continue
    rvf.append([ent.bjd, ent.rv, ent.sn, ent.erv])

os.chdir(outdir)
np.savetxt(outfile, np.array(rvf))
outbase = os.path.basename(outfile)
for n in range(0, maxord+1):
    npath = os.path.join("Order.%.3d" % n, outbase)
    os.link(outfile, npath)
