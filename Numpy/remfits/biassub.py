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

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Make table of obs versus bias', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--obs', type=str, required=True, help='Prefix for obs files')
parsearg.add_argument('--bias', type=str, required=True, help='Prefix for bias files')
parsearg.add_argument('--ffref', type=str, required=True, help='Flat file for reference')

resargs = vars(parsearg.parse_args())
obspref = resargs['obs']
biaspref = resargs['bias']
ffref = resargs['ffref']

ffreff = fits.open(ffref)
ffrefim = trimarrays.trimzeros(trimarrays.trimnan(ffreff[0].data))
ffreff.close()

obsfiles = glob.glob(obspref + '*')
if len(obsfiles) == 0:
    print("No obs files found with prefix", obspref, file=sys.stderr)
    sys.exit(10)

biasfiles = glob.glob(biaspref + '*')
if len(biasfiles) == 0:
    print("No bias files found with prefix", biaspref, file=sys.stderr)
    sys.exit(11)

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

obsims = trimarrays.trimto(ffrefim, *obsims)
biasims = trimarrays.trimto(ffrefim, *biasims)

print("Bias ->  ", end='')
for bdat in biasdates:
    print(bdat.strftime(" %H:%M:%S"), end=" ")
print()

for obs, obsdate in zip(obsims, obsdates):
    
    print(obsdate.strftime("%H:%M:%S:"), end="")
    for bia in biasims:
        print("%9.0f" % (obs-bia).min(), end=' ')
    print()

    print(9 * " ", end="")
    for bia in biasims:
        print("%9d" % np.count_nonzero(obs-bia < 0), end=' ')
    print()


               
