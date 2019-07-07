#!  /usr/bin/env python3

# Get object data and maintain XML Database

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import glob
import trimarrays
import strreplace

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Make table of obs versus bias', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--obs', type=str, required=True, help='Prefix for obs files')
parsearg.add_argument('--bias', type=str, required=True, help='Prefix for bias files')
parsearg.add_argument('--ffref', type=str, help='Flat file for reference')
parsearg.add_argument('--trim', type=str, help='Trim to rows:coliumns')
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with median')
parsearg.add_argument('--latex', action='store_true', help='Output in Latex Format')
parsearg.add_argument('--divff', action='store_true', help='Divide by flat field')

resargs = vars(parsearg.parse_args())
obspref = resargs['obs']
biaspref = resargs['bias']
ffref = resargs['ffref']
rc = resargs['trim']
replstd = resargs['replstd']
latex = resargs['latex']
divff = resargs['divff']

if ffref is not None:
    ffreff = fits.open(ffref)
    ffrefim = trimarrays.trimzeros(trimarrays.trimnan(ffreff[0].data))
    ffreff.close()
    rows, cols  = ffrefim.shape
elif rc is not None:
    try:
        rows, cols = map(lambda x: int(x), rc.split(':'))
    except ValueError:
        print("Unexpected --trim arg", rc, "expected rows:cols", file=sys.stderr)
        sys.exit(10)
    if divff:
        print("Sorry cannot specify --divff if just rows:cols given", file=sys.stderr)
        sys.exit(15)
else:
    print("No reference flat file or trim arg given", file=sys.stederr)
    sys.exit(11) 

biasfiles = glob.glob(biaspref + '*')
if len(biasfiles) == 0:
    print("No bias files found with prefix", biaspref, file=sys.stderr)
    sys.exit(12)
obsfiles = glob.glob(obspref + '*')
if len(obsfiles) == 0:
    print("No obs files found with prefix", obspref, file=sys.stderr)
    sys.exit(13)

obsims = []
biasims = []
obsdates = []
biasdates = []

for obsf in obsfiles:
    ff = fits.open(obsf)
    obsim = ff[0].data.astype(np.float64)
    if obsim.shape[0] != 1024:
        continue
    obsims.append(obsim)
    obsdates.append(Time(ff[0].header['DATE-OBS']))
    ff.close()
for biasf in biasfiles:
    ff = fits.open(biasf)
    biasims.append(ff[0].data.astype(np.float64))
    biasdates.append(Time(ff[0].header['DATE']))
    ff.close()

Day = obsdates[0].strftime("%Y-%m-%d")

print("Results for", Day)

obsims = trimarrays.trimrc(rows,cols, *obsims)
biasims = trimarrays.trimrc(rows, cols, *biasims)

if replstd > 0.0:
    newbi = []
    for b in biasims:
        newbi.append(strreplace.strreplace(b, replstd))
    biasims = newbi

if len(biasims) > 1:
    comb = np.array(biasims)
    comb = np.median(comb, axis=0)
else:
    comb = np.array(biasims.copy())

lenc = 100.0 / float(len(comb.flatten()))
if divff:
    comb /= ffrefim

if latex:
    print("Bias ->  ", end='&')
    for bdat in biasdates:
        print(bdat.strftime(" %H:%M:%S"), end="&")
    print("Combined\\\\")

    for obs, obsdate in zip(obsims, obsdates):
    
        if divff:
            obs = obs.copy() / ffrefim
        print(obsdate.strftime("%H:%M:%S:"), end="&")
        for bia in biasims:
            if divff:
                bia = bia.copy() / ffrefim
            print("%.0f" % (obs-bia).min(), end='&')
        print("%.0f\\\\" % (obs-comb).min())

        print("", end="&")
        for bia in biasims:
            if divff:
                bia = bia.copy() / ffrefim
            print("%.2f" % (np.count_nonzero(obs-bia < 0) * lenc), end='&')
        print("%.2f\\\\" % (np.count_nonzero(obs-comb < 0) * lenc))
    
else:
    print("Bias ->  ", end='')
    for bdat in biasdates:
        print(bdat.strftime(" %H:%M:%S"), end=" ")
    print(" Combined")

    for obs, obsdate in zip(obsims, obsdates):
    
        if divff:
            obs = obs.copy() / ffrefim
        print(obsdate.strftime("%H:%M:%S:"), end="")
        for bia in biasims:
            if divff:
                bia = bia.copy() / ffrefim
            print("%9.0f" % (obs-bia).min(), end=' ')
        print("%9.0f" % (obs-comb).min())

        print(9 * " ", end="")
        for bia in biasims:
            if divff:
                bia = bia.copy() / ffrefim
            print("%9.2f" % (np.count_nonzero(obs-bia < 0) * lenc), end=' ')
        print("%9.2f" % (np.count_nonzero(obs-comb < 0) * lenc))
