#! /usr/bin/env python3

"""Obtain parameters of new FITS files and insert into database"""

import sys
import datetime
import argparse
from astropy.time import Time
import scipy.stats as ss
import numpy as np
import dateutil.relativedelta
import remdefaults
import remget
import remfits
import fitsops
import trimarrays
import mydateutil
import wcscoord


def rejectmast(cu, mtyp, myear, mmonth, mfilter, mreason):
    """Set master file to rejected for various reasons"""
    cu.execute("UPDATE forbinf SET rejreason=%s WHERE filter=%s AND typ=%s AND " + "year=%d AND month=%d" % (myear, mmonth), (mreason, mfilter, mtyp))
    cu.connection.commit()


parsearg = argparse.ArgumentParser(description='Update database fields from newly-loaded FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--trimsides', type=int, default=0, help='Amount to trip off edges set -1 to force recalc')
parsearg.add_argument('--remir', action='store_true', help='Include REMIR files (not yet fully implemented')
parsearg.add_argument('--hasfile', action='store_false', help='Restrict to files we have loaded')
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
trimsides = resargs['trimsides']

fieldselect = ['rejreason IS NULL']
sxfields = []
if resargs['remir']:
    sxfields.append("dithID=0")
else:
    fieldselect.append("dithID=0")

if resargs['hasfile']:
    fieldselect.append('ind!=0')

orfields = []
for orf in ('airmass', 'gain', 'nrows', 'ncols'):
    orfields.append(orf + " IS NULL")
sxfields.append("startx=0")
sxfields.append("starty=0")

orfields.append("(" + " AND ".join(sxfields) + ")")
orfields.append("sidet!=%d" % trimsides)
fieldselect.append('(' + " OR ".join(orfields) + ')')

realtrimsides = trimsides
if realtrimsides < 0:
    realtrimsides = 0

dbase, dbcurs = remdefaults.opendb()
dbcurs.execute("SELECT obsind,ind,exptime,filter,date_obs,gain,dithID,ffname FROM obsinf WHERE " + " AND ".join(fieldselect))
rows = dbcurs.fetchall()

dims_added = 0
nfiles = 0
nreject = 0

for obsind, fitsind, exptime, ofilter, date_obs, gain, dithID, ffname in rows:

    try:
        if fitsind == 0:
            ffmem = remget.get_obs(ffname, dithID != 0)
        else:
            ffmem = remget.get_saved_fits(dbcurs, fitsind)
    except remget.RemGetError as e:
        remget.set_rejection(dbcurs, obsind, e.args[0])
        nreject += 1
        continue

    ffhdr, fdat = fitsops.mem_get(ffmem)
    if ffhdr is None:
        remget.set_rejection(dbcurs, obsind, "Cannot read FITS file")
        nreject += 1
        continue

    fdate = Time(ffhdr['DATE-OBS']).datetime
    if not mydateutil.sametime(fdate, date_obs):
        remget.set_rejection(dbcurs, obsind, "FITS date of " + mydateutil.mysql_datetime(fdate) + " does not agree")
        nreject += 1
        continue

    fexptime = ffhdr['EXPTIME']
    if fexptime != exptime:
        remget.set_rejection(dbcurs, obsind, "FITS exposure time of %.4g does not agree" % fexptime)
        nreject += 1
        continue

    fgain = ffhdr['GAIN']
    fairmass = ffhdr['AIRMASS']

    if dithID != 0:
        moonphase = moondist = -1000.0
        sideexpected = 512
    else:
        moonphase = ffhdr['MOONPHAS']
        moondist = ffhdr['MOONDIST']
        sideexpected = 1024

    sidesize = fdat.shape[0]
    if sidesize != sideexpected:
        remget.set_rejection(dbcurs, obsind, "FITS has size of %d not %d as expected" % (sidesize, sideexpected))
        nreject += 1
        continue

    startx, starty, rcols, rrows = remdefaults.get_geom(date_obs, ofilter)
    nzfdat = trimarrays.trimzeros(fdat)
    fitsrows, fitscols = nzfdat.shape

    sqq = fdat.flatten()
    sqq = sqq[sqq != 0]
    tsfdat = nzfdat
    if realtrimsides > 0:
        tsfdat = nzfdat[realtrimsides:-realtrimsides, realtrimsides:-realtrimsides]

    w = wcscoord.wcscoord(ffhdr)
    cornerpix = ((0, 0), (fitscols - 1, fitsrows - 1))
    ((blra, bldec), (trra, trdec)) = w.pix_to_coords(cornerpix)
    if trra < blra:
        if trdec > bldec:
            orient = 0
        else:
            orient = 1
    else:
        if trdec > bldec:
            orient = 3
        else:
            orient = 2
    updfields = []
    updfields.append("gain=%.6g" % fgain)
    updfields.append("orient=%d" % orient)
    updfields.append("airmass=%.6g" % fairmass)
    updfields.append("moonphase=%.6g" % moonphase)
    updfields.append("moondist=%.6g" % moondist)
    updfields.append("nrows=%d" % fitsrows)
    updfields.append("ncols=%d" % fitscols)
    updfields.append("startx=%d" % startx)
    updfields.append("starty=%d" % starty)
    updfields.append("minv=%d" % sqq.min())
    updfields.append("maxv=%d" % sqq.max())
    updfields.append("sidet=%d" % realtrimsides)
    updfields.append("median=%.8e" % np.median(tsfdat))
    updfields.append("mean=%.8e" % tsfdat.mean())
    updfields.append("std=%.8e" % tsfdat.std())
    updfields.append("skew=%.8e" % ss.skew(tsfdat, axis=None))
    updfields.append("kurt=%.8e" % ss.kurtosis(tsfdat, axis=None))
    dbcurs.execute("UPDATE obsinf SET " + ",".join(updfields) + " WHERE obsind=%d" % obsind)
    if fitsind != 0:
        dbcurs.execute("UPDATE fitsfile SET nrows=%d,ncols=%d,startx=%d,starty=%d WHERE ind=%d" % (fitsrows, fitscols, startx, starty, fitsind))
        if dithID == 0 and not remfits.check_has_dims(ffhdr):
            remfits.set_dims_in_hdr(ffhdr, startx, starty, fitscols, fitsrows)
            dbcurs.execute("UPDATE fitsfile SET fitsgz=%s WHERE ind=" + str(fitsind), fitsops.mem_makefits(ffhdr, fdat))
            dims_added += 1

    # Do this check after we've updated the fields
    if rrows != fitsrows:
        remget.set_rejection(dbcurs, obsind, "*** Height %d of FITS not %d as expected" % (fitsrows, rrows))
        nreject += 1
        continue
    if rcols != fitscols:
        remget.set_rejection(dbcurs, obsind, "*** Width %d of FITS not %d as expected" % (fitscols, rcols))
        nreject += 1
        continue

    dbase.commit()
    nfiles += 1

# Repeat for master flats and biases

fieldselect = ['rejreason IS NULL']
orfields = []
sxfields = []

fieldselect.append('fitsind!=0')

for orf in ('gain', 'nrows', 'ncols'):
    orfields.append(orf + " IS NULL")

sxfields.append("startx=0")
sxfields.append("starty=0")
orfields.append("(" + " AND ".join(sxfields) + ")")
fieldselect.append('(' + " OR ".join(orfields) + ')')

dbcurs.execute("SELECT year,month,filter,typ,fitsind FROM forbinf WHERE " + " AND ".join(fieldselect))
rows = dbcurs.fetchall()

nmfb = 0

for year, month, ofilter, typ, fitsind in rows:

    # Manufacture end of month out of year and month

    date_obs = datetime.datetime(year, month, 15, 23, 59, 0) + dateutil.relativedelta.relativedelta(day=31)

    try:
        ffmem = remget.get_saved_fits(dbcurs, fitsind)
    except remget.RemGetError as e:
        rejectmast(dbcurs, typ, year, month, ofilter, e.args[0])
        nreject += 1
        continue

    ffhdr, fdat = fitsops.mem_get(ffmem)
    fgain = ffhdr['GAIN']

    if typ == 'flat':
        nzfdat = trimarrays.trimnan(fdat)
    else:
        nzfdat = trimarrays.trimzeros(fdat)

    fitsrows, fitscols = nzfdat.shape
    startx, starty, rcols, rrows = remdefaults.get_geom(date_obs, ofilter)

    dbcurs.execute("UPDATE forbinf SET gain=%.6g,nrows=%d,ncols=%d,startx=%d,starty=%d WHERE filter='%s' AND typ='%s' AND year=%d AND month=%d" %
                    (fgain, fitsrows, fitscols, startx, starty, ofilter, typ, year, month))

    dbcurs.execute("UPDATE fitsfile SET nrows=%d,ncols=%d,startx=%d,starty=%d WHERE ind=%d" % (fitsrows, fitscols, startx, starty, fitsind))

    if not remfits.check_has_dims(ffhdr):
        remfits.set_dims_in_hdr(ffhdr, startx, starty, fitscols, fitsrows)
        dbcurs.execute("UPDATE fitsfile SET fitsgz=%s WHERE ind=" + str(fitsind), fitsops.mem_makefits(ffhdr, fdat))
        dims_added += 1

    # Do this check after we've updated the fields

    if rrows != fitsrows:
        rejectmast(dbcurs, typ, year, month, ofilter, "*** Height %d of FITS not %d as expected" % (fitsrows, rrows))
        nreject += 1
        continue
    if rcols != fitscols:
        rejectmast(dbcurs, typ, year, month, ofilter, "*** Width %d of FITS not %d as expected" % (fitscols, rcols))
        nreject += 1
        continue

    dbase.commit()
    nmfb += 1

# Finally indiviaul flat and bias

fieldselect = ['rejreason IS NULL']
sxfields = []
fieldselect.append('ind!=0')

orfields = []
for orf in ('gain', 'nrows', 'ncols'):
    orfields.append(orf + " IS NULL")
sxfields.append("startx=0")
sxfields.append("starty=0")

orfields.append("(" + " AND ".join(sxfields) + ")")
orfields.append("sidet!=%d" % trimsides)
fieldselect.append('(' + " OR ".join(orfields) + ')')

dbcurs.execute("SELECT ind,iforbind,typ,gain,exptime,filter,date_obs FROM iforbinf WHERE " + " AND ".join(fieldselect))
rows = dbcurs.fetchall()

nifb = 0

for fitsind, iforbind, typ, gain, exptime, ofilter, date_obs in rows:

    try:
        ffmem = remget.get_saved_fits(dbcurs, fitsind)
    except remget.RemGetError as e:
        remget.set_rejection(dbcurs, iforbind, e.args[0], table='iforbinf', column='iforbind')
        nreject += 1
        continue

    ffhdr, fdat = fitsops.mem_get(ffmem)
    if ffhdr is None:
        remget.set_rejection(dbcurs, iforbind, "Cannot read FITS file", table='iforbinf', column='iforbind')
        nreject += 1
        continue

    fdate = Time(ffhdr['DATE-OBS']).datetime
    if not mydateutil.sametime(fdate, date_obs):
        remget.set_rejection(dbcurs, iforbind, "FITS date of " + mydateutil.mysql_datetime(fdate) + " does not agree", table='iforbinf', column='iforbind')
        nreject += 1
        continue

    fexptime = ffhdr['EXPTIME']
    if fexptime != exptime:
        remget.set_rejection(dbcurs, iforbind, "FITS exposure time of %.4g does not agree" % fexptime, table='iforbinf', column='iforbind')
        nreject += 1
        continue

    fgain = ffhdr['GAIN']

    sqq = fdat.flatten()
    sqq = sqq[sqq != 0]
    nzfdat = trimarrays.trimzeros(fdat)
    fitsrows, fitscols = nzfdat.shape
    tsfdat = nzfdat
    if realtrimsides > 0:
        tsfdat = nzfdat[realtrimsides:-realtrimsides, realtrimsides:-realtrimsides]

    startx, starty, rcols, rrows = remdefaults.get_geom(date_obs, ofilter)

    updfields = []
    updfields.append("gain=%.6g" % fgain)
    updfields.append("nrows=%d" % fitsrows)
    updfields.append("ncols=%d" % fitscols)
    updfields.append("startx=%d" % startx)
    updfields.append("starty=%d" % starty)
    updfields.append("minv=%d" % sqq.min())
    updfields.append("maxv=%d" % sqq.max())
    updfields.append("sidet=%d" % realtrimsides)
    updfields.append("median=%.8e" % np.median(tsfdat))
    updfields.append("mean=%.8e" % tsfdat.mean())
    updfields.append("std=%.8e" % tsfdat.std())
    updfields.append("skew=%.8e" % ss.skew(tsfdat, axis=None))
    updfields.append("kurt=%.8e" % ss.kurtosis(tsfdat, axis=None))
    dbcurs.execute("UPDATE iforbinf SET " + ",".join(updfields) + " WHERE iforbind=%d" % iforbind)
    dbcurs.execute("UPDATE fitsfile SET nrows=%d,ncols=%d,startx=%d,starty=%d WHERE ind=%d" % (fitsrows, fitscols, startx, starty, fitsind))

    # Possibly update FITS file

    if not remfits.check_has_dims(ffhdr):
        remfits.set_dims_in_hdr(ffhdr, startx, starty, fitscols, fitsrows)
        dbcurs.execute("UPDATE fitsfile SET fitsgz=%s WHERE ind=" + str(fitsind), fitsops.mem_makefits(ffhdr, fdat))
        dims_added += 1

    # Do this check after we've put other stuff in

    if rrows != fitsrows:
        remget.set_rejection(dbcurs, iforbind, "*** Height %d of FITS not %d as expected" % (fitsrows, rrows), table='iforbinf', column='iforbind')
        nreject += 1
        continue
    if rcols != fitscols:
        remget.set_rejection(dbcurs, iforbind, "*** Width %d of FITS not %d as expected" % (fitscols, rcols), table='iforbinf', column='iforbind')
        nreject += 1
        continue

    dbase.commit()
    nifb += 1

if nreject + nfiles + nmfb + nifb + dims_added == 0:
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
    if nreject > 0:
        print(nreject, "FITS files rejected", file=sys.stderr)
