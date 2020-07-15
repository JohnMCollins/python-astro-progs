#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-29T16:49:45+00:00
# @Email:  jmc@toad.me.uk
# @Filename: updairmass.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:57:17+00:00

from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import scipy.stats as ss
import numpy as np
import os
import sys
import datetime
import dateutil.relativedelta
import string
import warnings
import dbobjinfo
import dbremfitsobj
import dbops
import remdefaults
import remfitshdr
import argparse
import trimarrays

tmpdir = remdefaults.get_tmpdir()
mydbname = remdefaults.default_database()
parsearg = argparse.ArgumentParser(description='Update database fields from newly-loaded FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
parsearg.add_argument('--trimsides', type=int, default=100, help='Amount to trip off edges')
resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
tmpdir = resargs['tempdir']
trimsides = resargs['trimsides']

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    print("Unable to select temporary directory", tmpdir, file=sys.stderr)
    sys.exit(100)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

# # First get sides and update FITS files
#
# dbcurs.execute("SELECT ind FROM fitsfile WHERE side IS NULL")
# rows = dbcurs.fetchall()
#
# nsides = 0
# errorfiles = []
#
# for (ind,) in rows:
#
#     try:
#         ffile = dbremfitsobj.getfits(dbcurs, ind)
#     except OSError:
#         errorfiles.append(ind)
#         print("Could not get FITS file for ind", ind, file=sys.stderr)
#         continue
#
#     fdat = ffile[0].data
#     ffshape = fdat.shape
#
#     if  ffshape[0] != ffshape[-1]:
#         side = 0
#     else:
#         side = ffshape[0]
#
#     nzfdat = trimarrays.trimzeros(trimarrays.trimnan(fdat))
#     dbcurs.execute("UPDATE fitsfile SET side=%d,rows=%d,cols=%d WHERE ind=%d" % (side, nzfdat.shape[0], nzfdat.shape[1], ind))
#     ffile.close()
#     nsides += 1
#     if nsides % 20 == 0:
#         dbase.commit()
#
# for find in errorfiles:
#     dbremfitsobj.badfitsfile(dbcurs, find)
#
# dbase.commit()

# Fix gain and airmass, check exp time in observations and update fits details as well

dbcurs.execute("SELECT obsind,ind,exptime,filter, date_obs FROM obsinf WHERE dithID=0 AND ind!=0 AND rejreason IS NULL AND (airmass IS NULL OR gain IS NULL OR rows IS NULL OR cols IS NULL OR (startx=0 and starty=0))")
rows = dbcurs.fetchall()

dims_added = 0
nfiles = 0

for obsind, fitsind, exptime, filter, date_obs in rows:

    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    ffhdr = ffile[0].header
    fexptime = ffhdr['EXPTIME']
    fairmass = ffhdr['AIRMASS']
    moonphase = ffhdr['MOONPHAS']
    moondist = ffhdr['MOONDIST']
    fgain = ffhdr['GAIN']
    fdate = Time(ffhdr['DATE-OBS']).datetime

    if abs((fdate - date_obs).total_seconds()) > 1:
        print("Obsind", obsind, "DB hdr date", date_obs.strftime("%Y-%m-%d %H:%M:%S"), "FITS hdr", fdate.strftime("%Y-%m-%d %H:%M:%S"), file=sys.stderr)
    if fexptime != exptime:
        print("Obsind", obsind, "DB hdr exptime", exptime, "FITS exptime", fexptime, file=sys.stderr)

    fdat = ffile[0].data
    sidesize = fdat.shape[0]
    ffile.close()

    sqq = fdat.flatten()
    sqq = sqq[sqq != 0]
    nzfdat = trimarrays.trimzeros(fdat)
    fitsrows = nzfdat.shape[0]
    fitscols = nzfdat.shape[1]
    tsfdat = nzfdat
    if trimsides > 0:
        tsfdat = nzfdat[trimsides:-trimsides, trimsides:-trimsides]

    startx, starty, rcols, rrows = remdefaults.get_geom(date_obs, filter)
    if rcols != fitscols:
        print("Obsind", obsind, "Expected width of image to be", rcols, "but it is", fitscols, file=sys.stderr)
    if rrows != fitsrows:
        print("Obsind", obsind, "Expected height of image to be", rrows, "but it is", fitsrows, file=sys.stderr)

    dbcurs.execute("UPDATE obsinf SET airmass=%.6g,gain=%.6g,moonphase=%.6g,moondist=%.6g,rows=%d,cols=%d,startx=%d,starty=%d,minv=%d,maxv=%d,sidet=%d,median=%.8e,mean=%.8e,std=%.8e,skew=%.8e,kurt=%.8e WHERE obsind=%d" %
                    (fairmass, fgain, moonphase, moondist, fitsrows, fitscols, startx, starty, sqq.min(), sqq.max(), trimsides, np.median(tsfdat), tsfdat.mean(), tsfdat.std(), ss.skew(tsfdat, axis=None), ss.kurtosis(tsfdat, axis=None), obsind))
    dbcurs.execute("UPDATE fitsfile SET side=%d,rows=%d,cols=%d,startx=%d,starty=%d WHERE ind=%d" % (sidesize, fitsrows, fitscols, startx, starty, fitsind))
    if not remfitshdr.check_has_dims(ffhdr):
        remfitshdr.set_dims_in_hdr(ffhdr, startx, starty, fitscols, fitsrows)
        dbcurs.execute("UPDATE fitsfile SET fitsgz=%s WHERE ind=" + str(fitsind), remfitshdr.make_fits(ffhdr, fdat))
        dims_added += 1
        dbase.commit()
    nfiles += 1

dbase.commit()

# Repeat for master flats and biases

dbcurs.execute("SELECT year,month,filter,typ,fitsind FROM forbinf WHERE (rows IS NULL OR cols IS NULL OR gain IS NULL OR (startx=0 AND starty=0)) AND rejreason IS NULL AND fitsind!=0")
rows = dbcurs.fetchall()

nmfb = 0

for year, month, filter, typ, fitsind in rows:

    # Manufacture end of month out of year and month

    date_obs = datetime.date(year, month, 15) + dateutil.relativedelta.relativedelta(day=31)

    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    ffhdr = ffile[0].header
    fgain = ffhdr['GAIN']
    fdat = ffile[0].data
    sidesize = fdat.shape[0]
    ffile.close()
    if typ == 'flat':
        nzfdat = trimarrays.trimnan(fdat)
    else:
        nzfdat = trimarrays.trimzeros(fdat)

    fitsrows = nzfdat.shape[0]
    fitscols = nzfdat.shape[1]

    startx, starty, rcols, rrows = remdefaults.get_geom(date_obs, filter)
    if rcols != fitscols:
        print("Master", typ, year, month, "filter", filter, "Expected width of image to be", rcols, "but it is", fitscols, file=sys.stderr)
    if rrows != fitsrows:
        print("Master", typ, year, month, "filter", filter, "Expected height of image to be", rrows, "but it is", fitsrows, file=sys.stderr)

    dbcurs.execute("UPDATE forbinf SET gain=%.6g WHERE filter='%s' AND typ='%s' AND year=%d AND month=%d" % (fgain, filter, typ, year, month))
    dbcurs.execute("UPDATE fitsfile SET side=%d,rows=%d,cols=%d,startx=%d,starty=%d WHERE ind=%d" % (sidesize, fitsrows, fitscols, startx, starty, fitsind))
    if not remfitshdr.check_has_dims(ffhdr):
        remfitshdr.set_dims_in_hdr(ffhdr, startx, starty, fitscols, fitsrows)
        dbcurs.execute("UPDATE fitsfile SET fitsgz=%s WHERE ind=" + str(fitsind), remfitshdr.make_fits(ffhdr, fdat))
        dims_added += 1
        dbase.commit()
    nmfb += 1

dbase.commit()

# Finally indiviaul flag and bias

dbcurs.execute("SELECT ind,iforbind,typ,filter,date_obs FROM iforbinf WHERE (sidet!=%d OR gain IS NULL OR rows IS NULL OR cols IS NULL OR (startx=0 AND starty=0)) AND rejreason IS NULL AND ind!=0" % trimsides)
rows = dbcurs.fetchall()

nifb = 0

for fitsind, ind, typ, filter, date_obs in rows:

    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    ffhdr = ffile[0].header
    fgain = ffhdr['GAIN']
    fdate = Time(ffhdr['DATE-OBS']).datetime
    if abs((fdate - date_obs).total_seconds()) > 1:
        print("Iforbind", ind, "DB hdr date", date_obs.strftime("%Y-%m-%d %H:%M:%S"), "FITS hdr", fdate.strftime("%Y-%m-%d %H:%M:%S"), file=sys.stderr)

    fdat = ffile[0].data
    sidesize = fdat.shape[0]
    ffile.close()
    sqq = fdat.flatten()
    sqq = sqq[sqq != 0]
    nzfdat = trimarrays.trimzeros(fdat)
    fitsrows = nzfdat.shape[0]
    fitscols = nzfdat.shape[1]
    tsfdat = nzfdat
    if trimsides > 0:
        tsfdat = nzfdat[trimsides:-trimsides, trimsides:-trimsides]

    startx, starty, rcols, rrows = remdefaults.get_geom(date_obs, filter)
    if rcols != fitscols:
        print("Iforbind", ind, "Expected width of image to be", rcols, "but it is", fitscols, file=sys.stderr)
    if rrows != fitsrows:
        print("Iforbind", ind, "Expected height of image to be", rrows, "but it is", fitsrows, file=sys.stderr)

    dbcurs.execute("UPDATE iforbinf SET gain=%.6g,rows=%d,cols=%d,startx=%d,starty=%d,minv=%d,maxv=%d,sidet=%d,median=%.8e,mean=%.8e,std=%.8e,skew=%.8e,kurt=%.8e WHERE iforbind=%d" %
                   (fgain, fitsrows, fitscols, startx, starty, sqq.min(), sqq.max(),
                    trimsides, np.median(tsfdat), tsfdat.mean(), tsfdat.std(),
                    ss.skew(tsfdat, axis=None), ss.kurtosis(tsfdat, axis=None), ind))
    dbcurs.execute("UPDATE fitsfile SET side=%d,rows=%d,cols=%d,startx=%d,starty=%d WHERE ind=%d" % (sidesize, fitsrows, fitscols, startx, starty, fitsind))
    if not remfitshdr.check_has_dims(ffhdr):
        remfitshdr.set_dims_in_hdr(ffhdr, startx, starty, fitscols, fitsrows)
        dbcurs.execute("UPDATE fitsfile SET fitsgz=%s WHERE ind=" + str(fitsind), remfitshdr.make_fits(ffhdr, fdat))
        dims_added += 1
        dbase.commit()
    nifb += 1

dbase.commit()

if nfiles + nmfb + nifb + dims_added == 0:
    print("Nothing needed to be adjusted", file=sys.stderr)
else:
    if nfiles > 0:
        print(nfiles, "Observations updated", file=sys.stderr)
    if nmfb > 0:
        print(nmfb, "naster flat/bias/gains added", file=sys.stderr)
    if nifb > 0:
        print(nifb, "individual flat/bias updated", file=sys.stderr)
    if dims_added > 0:
        print(dims_added, "Dimensions added to FITS files", file=sys.stderr)
