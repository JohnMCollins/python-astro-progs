#! /usr/bin/env python3

from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import scipy.stats as ss
import numpy as np
import os
import sys
import datetime
import string
import warnings
import dbops
import remdefaults
import remget
import fitsops
import argparse
import mydateutil

parsearg = argparse.ArgumentParser(description='Fix missing gains in obs records', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

doneok = 0
errors = 0

mydbase, mycurs = remdefaults.opendb()

mycurs.execute("SELECT obsind FROM obsinf WHERE rejreason IS NULL AND gain IS NULL")
obsinds = mycurs.fetchall()

for obsind, in obsinds:
    try:
        ffmem = remget.get_obs_fits(mycurs, obsind)
        hdr, data = fitsops.mem_get(ffmem)
    except remget.RemGetError as e:
        remget.set_rejection(mycurs, obsind, e.args[0])
        errors += 1
        continue
    if hdr is None:
        remget.set_rejection(mycurs, obsind, "Could not decipher FITS")
        errors += 1
        continue
    try:
        mycurs.execute("UPDATE obsinf SET gain=%.6e WHERE obsind=%d" % (hdr['GAIN'], obsind))
        mydbase.commit()
        doneok += 1
    except KeyError:
        remget.set_rejection(mycurs, obsind, "No GAIN in FITS header")
        errors += 1

mycurs.execute("SELECT iforbind FROM iforbinf WHERE rejreason IS NULL AND gain IS NULL")
iforbinds = mycurs.fetchall()
for iforbind, in iforbinds:
    try:
        ffmem = remget.get_iforb_fits(mycurs, iforbind)
        hdr, data = fitsops.mem_get(ffmem)
    except remget.RemGetError as e:
        remget.set_rejection(mycurs, iforbind, e.args[0], table='iforbinf', column='iforbind')
        errors += 1
        continue
    if hdr is None:
        remget.set_rejection(mycurs, iforbind, "Could not decipher FITS", table='iforbinf', column='iforbind')
        errors += 1
        continue
    try:
        mycurs.execute("UPDATE iforbinf SET gain=%.6e WHERE iforbind=%d" % (hdr['GAIN'], iforbind))
        mydbase.commit()
        doneok += 1
    except KeyError:
        remget.set_rejection(mycurs, iforbind, "No GAIN in FITS header", table='iforbinf', column='iforbind')
        errors += 1

print(doneok, "Done OK", errors, "Errors")
