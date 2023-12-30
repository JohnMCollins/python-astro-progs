#! /usr/bin/env python3

"""Obtain parameters of new FITS files and insert into database"""

import sys
import datetime
import argparse
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
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
import logs

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)


def rejectmast(cu, mtyp, myear, mmonth, mfilter, mreason):
    """Set master file to rejected for various reasons"""
    cu.execute("UPDATE forbinf SET rejreason=%s WHERE filter=%s AND typ=%s AND " + f"year={myear} AND month={mmonth}", (mreason, mfilter, mtyp))
    cu.connection.commit()


parsearg = argparse.ArgumentParser(description='Update database fields from newly-loaded FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
logs.parseargs(parsearg)
parsearg.add_argument('--trimsides', type=int, default=0, help='Amount to trip off edges set -1 to force recalc')
parsearg.add_argument('--remir', action='store_true', help='Include REMIR files (not yet fully implemented')
parsearg.add_argument('--hasfile', action='store_false', help='Restrict to files we have loaded')
parsearg.add_argument('--inclreject', action='store_true', help='Include files already rejected')
parsearg.add_argument('--verbose', action='count', help='Be increasingly verbose')
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
logging = logs.getargs(resargs)
trimsides = resargs['trimsides']
verbose = resargs['verbose']
inclrej = resargs['inclreject']

fieldselect = []
if not inclrej:
    fieldselect.append('rejreason IS NULL')
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
orfields.append(f"sidet!={trimsides}")
fieldselect.append('(' + " OR ".join(orfields) + ')')

realtrimsides = max(trimsides, 0)

dbase, dbcurs = remdefaults.opendb()
dbcurs.execute("SELECT obsind,ind,exptime,filter,date_obs,gain,dithID,ffname FROM obsinf WHERE " + " AND ".join(fieldselect))
rows = dbcurs.fetchall()

dims_added = 0
nfiles = 0
nreject = 0
nrows = len(rows)

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
        remget.set_rejection(dbcurs, obsind, f"FITS exposure time of {fexptime} does not agree" % fexptime)
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
        remget.set_rejection(dbcurs, obsind, f"FITS has size of {sidesize} not {sideexpected} as expected")
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
    updfields.append(f"gain={fgain}")
    updfields.append(f"orient={orient}")
    updfields.append(f"airmass={fairmass}")
    try:
        fseeing = ffhdr['SEEING']
        updfields.append(f"seeing={fseeing}")
    except KeyError:
        pass
    updfields.append(f"moonphase={moonphase}")
    updfields.append(f"moondist={moondist}")
    updfields.append(f"nrows={fitsrows}")
    updfields.append(f"ncols={fitscols}")
    updfields.append(f"startx={startx}")
    updfields.append(f"starty={starty}")
    updfields.append(f"minv={sqq.min()}")
    updfields.append(f"maxv={sqq.max()}")
    updfields.append(f"sidet={realtrimsides}")
    updfields.append(f"median={np.median(tsfdat)}")
    updfields.append(f"mean={tsfdat.mean()}")
    updfields.append(f"std={tsfdat.std()}")
    updfields.append(f"skew={ss.skew(tsfdat, axis=None)}")
    updfields.append(f"kurt={ss.kurtosis(tsfdat, axis=None)}")
    dbcurs.execute("UPDATE obsinf SET " + ",".join(updfields) + f" WHERE obsind={obsind}")
    if fitsind != 0:
        dbcurs.execute(f"UPDATE fitsfile SET nrows={fitsrows},ncols={fitscols},startx={startx},starty={starty} WHERE ind={fitsind}")
        if dithID == 0 and not remfits.check_has_dims(ffhdr):
            remfits.set_dims_in_hdr(ffhdr, startx, starty, fitscols, fitsrows)
            dbcurs.execute(f"UPDATE fitsfile SET fitsgz=%s WHERE ind={fitsind}", fitsops.mem_makefits(ffhdr, fdat))
            dims_added += 1

    # Do this check after we've updated the fields
    if rrows != fitsrows:
        remget.set_rejection(dbcurs, obsind, f"*** Height {fitsrows} of FITS not {rrows} as expected")
        nreject += 1
        continue
    if rcols != fitscols:
        remget.set_rejection(dbcurs, obsind, f"*** Width {fitscols} of FITS not {rcols} as expected")
        nreject += 1
        continue

    dbase.commit()
    nfiles += 1
    if verbose:
        if verbose == 1:
            if nfiles % 10 == 0:
                logging.write(f"Processed {nfiles} observations out of {nrows}")
        else:
            logging.write(f"Processed observation dated {date_obs.strftime('%d/%m/%Y %H:%M:%S')} filter {ofilter} out of {nrows} obs")

# Repeat for master flats and biases

fieldselect = []
if not inclrej:
    fieldselect.append('rejreason IS NULL')
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
nrows = len(rows)

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

    dbcurs.execute(f"UPDATE forbinf SET gain={fgain},nrows={fitsrows},ncols={fitscols},startx={startx},starty={starty} WHERE filter='{ofilter}' AND typ='{typ}' AND year={year} AND month={month}")
    dbcurs.execute(f"UPDATE fitsfile SET nrows={fitsrows},ncols={fitscols},startx={startx},starty={starty} WHERE ind={fitsind}")

    if not remfits.check_has_dims(ffhdr):
        remfits.set_dims_in_hdr(ffhdr, startx, starty, fitscols, fitsrows)
        dbcurs.execute(f"UPDATE fitsfile SET fitsgz=%s WHERE ind={fitsind}", fitsops.mem_makefits(ffhdr, fdat))
        dims_added += 1

    # Do this check after we've updated the fields

    if rrows != fitsrows:
        rejectmast(dbcurs, typ, year, month, ofilter, f"*** Height {fitsrows} of FITS not {rrows} as expected")
        nreject += 1
        continue
    if rcols != fitscols:
        rejectmast(dbcurs, typ, year, month, ofilter, f"*** Width {fitscols} of FITS not {rcols} as expected" % (fitscols, rcols))
        nreject += 1
        continue

    dbase.commit()
    nmfb += 1
    if verbose:
        if verbose == 1:
            if nmfb % 10 == 0:
                logging.write(f"Processed {nmfb} master files out of {nrows}")
        else:
            logging.write(f"Processed master file for {year}/{month} filter {ofilter} out of {nrows}")


# Finally indiviaul flat and bias

fieldselect = []
if not inclrej:
    fieldselect.append('rejreason IS NULL')
sxfields = []
fieldselect.append('ind!=0')

orfields = []
for orf in ('gain', 'nrows', 'ncols'):
    orfields.append(orf + " IS NULL")
sxfields.append("startx=0")
sxfields.append("starty=0")

orfields.append("(" + " AND ".join(sxfields) + ")")
orfields.append(f"sidet!={trimsides}")
fieldselect.append('(' + " OR ".join(orfields) + ')')

dbcurs.execute("SELECT ind,iforbind,typ,gain,exptime,filter,date_obs FROM iforbinf WHERE " + " AND ".join(fieldselect))
rows = dbcurs.fetchall()

nifb = 0
nrows = len(rows)

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
        remget.set_rejection(dbcurs, iforbind, f"FITS exposure time of {fexptime} does not agree", table='iforbinf', column='iforbind')
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
    updfields.append(f"gain={fgain}")
    updfields.append(f"nrows={fitsrows}")
    updfields.append(f"ncols={fitscols}")
    updfields.append(f"startx={startx}")
    updfields.append(f"starty={starty}")
    updfields.append(f"minv={sqq.min()}")
    updfields.append(f"maxv={sqq.max()}")
    updfields.append(f"sidet={realtrimsides}")
    updfields.append(f"median={np.median(tsfdat)}")
    updfields.append(f"mean={tsfdat.mean()}")
    updfields.append(f"std={tsfdat.std()}")
    updfields.append(f"skew={ss.skew(tsfdat, axis=None)}")
    updfields.append(f"kurt={ss.kurtosis(tsfdat, axis=None)}")
    dbcurs.execute("UPDATE iforbinf SET " + ",".join(updfields) + f" WHERE iforbind={iforbind}")
    dbcurs.execute(f"UPDATE fitsfile SET nrows={fitsrows},ncols={fitscols},startx={startx},starty={starty} WHERE ind={fitsind}")

    # Possibly update FITS file

    if not remfits.check_has_dims(ffhdr):
        remfits.set_dims_in_hdr(ffhdr, startx, starty, fitscols, fitsrows)
        dbcurs.execute(f"UPDATE fitsfile SET fitsgz=%s WHERE ind={fitsind}", fitsops.mem_makefits(ffhdr, fdat))
        dims_added += 1

    # Do this check after we've put other stuff in

    if rrows != fitsrows:
        remget.set_rejection(dbcurs, iforbind, f"*** Height {fitsrows} of FITS not {rrows} as expected", table='iforbinf', column='iforbind')
        nreject += 1
        continue
    if rcols != fitscols:
        remget.set_rejection(dbcurs, iforbind, f"*** Width {fitscols} of FITS not {rcols} as expected", table='iforbinf', column='iforbind')
        nreject += 1
        continue

    dbase.commit()
    nifb += 1
    if verbose:
        if verbose == 1:
            if nifb % 10 == 0:
                logging.write(f"Processed {nifb} flat/bias files out of {nrows}")
        else:
            logging.write(f"Processed individual {typ} file dated {date_obs.strftime('%d/%m/%Y %H:%M:%S')} filter {ofilter} out of {nrows}")

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
