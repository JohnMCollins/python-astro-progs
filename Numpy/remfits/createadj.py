#!  /usr/bin/env python3

# Create a FITS file by applying a bias and flat file

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import trimarrays
import strreplace
import miscutils
import remgeom
import loadimage
import wcscoord

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Create a new fits file by applying ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--outfile', type=str, required=True, help='Output FITS file')
parsearg.add_argument('--flatfile', type=str, required=True, help='Flat file to use')
parsearg.add_argument('--biasfile', type=str, required=True, help='Bias file to use')
parsearg.add_argument('--imagefile', type=str, required=True, help='Image file to use')
parsearg.add_argument('--applytrim', action='store_true', help='apply saved trim parameters')

resargs = vars(parsearg.parse_args())
imagefile = resargs['imagefile']
flatfile = resargs['flatfile']
biasfile = resargs['biasfile']
outfile = resargs['outfile']
applytrim = resargs['applytrim']

ffhdr, resimage = loadimage.loadimagehdr(imagefile, flatfile, biasfile)

w = wcscoord.wcscoord(ffhdr)

if applytrim:
    rg = remgeom.load()
    (resimage,) = rg.apply_trims(w, resimage)

# Now create the new fits file

fhdr = fits.Header()

for card, value, comment in ffhdr.cards:
    if card == 'NAXIS1':
        value = resimage.shape[1]
    elif card == 'NAXIS2@':
        value = resimage.shape[0]
    elif card == "BZERO":
        continue
    elif card == "BITPIX":
        value = -32
        comment = "IEEE single precision floating point"
    elif applytrim and card == 'CRPIX1':
        value -= rg.trims.left
    elif applytrim and card == 'CRPIX2':
        value -= rg.trims.bottom
    elif card == 'DATAMIN':
        value = resimage.min()
    elif card == 'DATAMAX':
        value = resimage.max()
    fhdr.set(card, value, comment)

print(fhdr.cards)
hdu = fits.PrimaryHDU(resimage, fhdr)
try:
    hdu.writeto(outfile, overwrite=False, checksum=True)
except OSError:
    print("Could not write", outfile, file=sys.stderr)
    sys.exit(200)
