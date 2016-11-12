#! /usr/bin/env python

# This program is intended to go into a model running results directory where we've done lots of runs with various
# noise etc and have produced files of the form XYZnnn.nn.res where nnn.nn is the noise
# and produce a single file containing two columns of noise level versus percentage recovery of the period

import sys
import os
import string
import re
import glob
import os.path
import math
import argparse
import numpy as np

parsearg = argparse.ArgumentParser(description='Process results of running simulations with various noise levels\nactually in model results directory', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('noiseresults', type=str, nargs='+', help='Noise result file sample to get prefix only bother with first')
parsearg.add_argument('--outfile', type=str, required=True, help='Output results file')
parsearg.add_argument('--pcomp', type=int, default=3, help='Component of path to results giving period counting backwards')
parsearg.add_argument('--period', type=float, help='Period to use over-riding file name')
parsearg.add_argument('--thresh', type=float, default=5.0, help='Percent threshold for accepting result')

resargs = vars(parsearg.parse_args())

resfiles = resargs['noiseresults'][0]
thresh = resargs['thresh'] / 100.0
outfile = resargs['outfile']
pcomp = resargs['pcomp']
period = resargs['period']

srcfile = os.path.abspath(resfiles)
outf = os.path.abspath(outfile)

templ = os.path.basename(resfiles)
os.chdir(os.path.dirname(resfiles))

if period is None:
    srcbits = string.split(srcfile, '/')
    period = float(srcbits[-pcomp])

# Split name up to get prefix (we might have just prefix)
# and don't forget we've just chdir-ed to it

m = re.match('(.*?)[\d.]+\.res$', templ)
if m:
    templ = m.group(1)

flist = glob.glob(templ + '*.res')
pmtch = re.compile(templ + '([\d.]+)\.res$')

nd = dict()

for f in flist:
    m = pmtch.match(f)
    if m is None: continue
    snr = m.group(1)
    nvec = np.loadtxt(f)
    if len(nvec.shape) != 1:
        print f, "has unexpected shape", nvec.shape
        continue
    perc = np.count_nonzero(abs(nvec - period)/nvec.shape[0] <= thresh)
    nd[snr] = perc

snr, percacc = np.array([(float (x[0]), x[1]) for x in nd.items()]).transpose()
srt = np.argsort(snr)
np.savetxt(outf, np.array([snr[srt], percacc[srt]]).transpose())
    

    