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
import trimarrays
import matplotlib.pyplot as plt
from astropy.modeling.tests.test_projections import pars
from bokeh.themes import default

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Compare bias files and plot hist of differences', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs=2, help='Pair of bias files')
parsearg.add_argument('--ffref', type=str, required=True, help='Flat file for reference')
parsearg.add_argument('--abs', action='store_true', help='Take absolute value of differfences')
parsearg.add_argument('--bins', type=int, default=10, help='Number of histogram bins')
parsearg.add_argument('--clip', type=int, default=5, help='Level at which we count exceiptionals')

resargs = vars(parsearg.parse_args())
file1, file2 = resargs['files']
bins = resargs['bins']
absval = resargs['abs']
ffref = resargs['ffref']
clip = resargs['clip']

ffreff = fits.open(ffref)
ffrefim = trimarrays.trimzeros(trimarrays.trimnan(ffreff[0].data))
ffreff.close()

bf1 = fits.open(file1)
bim1 = bf1[0].data.astype(np.float32)
bdate1 = Time(bf1[0].header['DATE']).datetime
bf1.close()

bf2 = fits.open(file2)
bim2 = bf2[0].data.astype(np.float32)
bdate2 = Time(bf2[0].header['DATE']).datetime
bf2.close()

bim1, bim2 = trimarrays.trimto(ffrefim, bim1, bim2)
bdiffs = (bim1 - bim2).flatten()
absdiffs = np.abs(bdiffs)
mv = np.round(absdiffs.mean())
mstd = absdiffs.std()
if absval:
    bdiffs = absdiffs
    bdiffs[bdiffs > clip * mstd] = mv
else:
    bdiffs[bdiffs < -clip * mstd] = - mv
    bdiffs[bdiffs > clip * mstd] = mv

plt.hist(bdiffs.flatten(), bins=bins)
plt.title("Compare bias" + bdate1.strftime(" %Y-%m-%d %H:%M:%S -v- ") + bdate2.strftime("%Y-%m-%d %H:%M:%S"))
plt.show()
