#! /usr/bin/env python

# Program to convert fake spectra array to files of spectra looking like ones we know and love

import argparse
import os.path
import sys
import numpy as np
import dotsdata
import veltowavel

parsearg = argparse.ArgumentParser(description='Convert fake spectra')
parsearg.add_argument('--velocities', type=str, help='File giving velocities')
parsearg.add_argument('--spectra', type=str, help='File giving fake spectra')
parsearg.add_argument('--timings', type=str, help='Timings data file')
parsearg.add_argument('--outtime', type=str, help='Output timings file')
parsearg.add_argument('--lambda', type=float, default=-1.0, help='Base wavelength for peak')
parsearg.add_argument('--resdir', type=str, help='Output directory')
parsearg.add_argument('--resprefix', type=str, help='File prefix')
parsearg.add_argument('--ressuffix', type=str, help='File suffix')
parsearg.add_argument('--norm', action='store_true', help='Normalise each fake spectrum')

resargs = vars(parsearg.parse_args())

velfile = resargs['velocities']
specfile = resargs['spectra']
timefile = resargs['timings']
outtime = resargs['outtime']
basewl = resargs['lambda']
resdir = resargs['resdir']
respref = resargs['resprefix']
ressuff = resargs['ressuffix']
norm = resargs['norm']

errors = 0

if velfile is None or not os.path.isfile(velfile):
    print "No velocties file"
    errors += 1
if specfile is None or not os.path.isfile(specfile):
    print "No spectrum file"
    errors += 1
if timefile is None or not os.path.isfile(timefile):
    print "No timings file"
    errors += 1
    timefile = "none"
if outtime is None:
    outtime = os.path.basename(timefile)
if basewl < 0.0:
    print "No wavelength given"
    errors += 1
if resdir is None or not os.path.isdir(resdir):
    print "No results directory"
    errors += 1
if respref is None: respref=""
if ressuff is None: ressuff=""

if errors > 0:
    sys.exit(10)

try:
    velocities = dotsdata.dotsdata(velfile)
    fakespecs = dotsdata.dotsdata(specfile)
    timings = dotsdata.dotsdata(timefile)
except dotsdata.DOTSError as e:
    print e.args[0]
    sys.exit(11)

if velocities.shape[-1] != fakespecs.shape[-1] or fakespecs.shape[0] != timings.shape[-1]:
    print "Confused about files, velocities shape is", velocities.shape, "fake spec shape is", fakespecs.shape, "Timings shape", timings.shape
    sys.exit(12)

# Convert velocities to wavelengths
wavelengths = veltowavel.veltowavel(basewl, velocities)

# Now do the business

try:
    tout = open(resdir + '/' + outtime, "w")
except IOError as e:
    print "Cannot create timings file error:", e.args[1]
    sys.exit(13)

fsize = len(respref + '###' + ressuff)

for n, dat in enumerate(fakespecs):
    fbase = (respref + "%.3d" + ressuff) % (n+1,)
    fname = resdir + '/' + fbase
    tout.write("%-*s %#.18g\n" % (fsize, fbase, timings[n]))
    if norm:
        dat = dat / dat[0]
    specn = np.array([wavelengths,dat])
    specn = specn.transpose()
    np.savetxt(fname, specn, "%#.18g")

tout.close()