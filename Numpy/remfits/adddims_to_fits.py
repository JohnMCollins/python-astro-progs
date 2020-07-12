#!  /usr/bin/env python3

# Add dimensions to saved fits files

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
import argparse
import warnings
import sys
import remdefaults
import io
import gzip
import datetime
import pymysql

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Work through FITS files and add startX/Y endX/Y fields', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, inlib=False, libdir=False, tempdir=False)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

mydb, dbcurs = remdefaults.opendb()

dbcurs.execute("SELECT ind,rows,cols,startx,starty FROM fitsfile WHERE startx!=0 OR starty!=0")
dbrows = dbcurs.fetchall()

nfits = len(dbrows)
if nfits == 0:
    print("No FITS files to process", file=sys.stderr)
    sys.exit(1)

ndone = 0
nalready = 0
nnew = 0
starttime = datetime.datetime.now()

for dbrow in dbrows:
    ind, rows, cols, startx, starty = dbrow
    dbcurs.execute("SELECT fitsgz FROM fitsfile WHERE ind=" + str(ind))
    fitsgz = dbcurs.fetchone()[0]
    unc = gzip.decompress(fitsgz)
    ff = fits.open(io.BytesIO(unc), memmap=False, lazy_load_hdus=False)
    hdr = ff[0].header
    dat = ff[0].data
    ff.close()
    if 'startX' in hdr:
        nalready += 1
    else:
        hdr['startX'] = (startx, 'Starting CCD pixel column')
        hdr['endX'] = (startx + cols, 'Ending CCD pixel column+1')
        hdr['startY'] = (starty, 'Starting CCD pixel row')
        hdr['endY'] = (starty + rows, 'Ending CCD pixel row+1')
        hdu = fits.PrimaryHDU(dat, hdr)
        mm = io.BytesIO()
        hdu.writeto(mm)
        fitsgz = gzip.compress(mm.getvalue())
        try:
            dbcurs.execute("UPDATE fitsfile SET fitsgz=%s WHERE ind=" + str(ind), (fitsgz,))
        except pymysql.err.OperationalError:
            print("DATABASE aborted", file=sys.stderr)
            sys.exit(200)
        if nnew == 0:
            newtime = datetime.datetime.now()
        nnew += 1
    ndone += 1
    if ndone % 100 == 0:
        propdone = ndone / nfits
        print("Reached %d of %d: %.2f%%" % (ndone, nfits, propdone * 100.0), end=' ', file=sys.stderr)
        ctime = datetime.datetime.now()
        tdiff = ctime - starttime
        rate = ndone / tdiff.total_seconds()
        print("Rate %.2f/s" % rate, end=' ', file=sys.stderr)
        daysd = tdiff.days
        if daysd != 0:
            print("%d days" % daysd, end=' ', file=sys.stderr)
            tdiff -= datetime.timedelta(days=daysd)
        hoursd = tdiff.seconds // 3600
        tdiff -= datetime.timedelta(hours=hoursd)
        minsd = tdiff.seconds // 60
        tdiff -= datetime.timedelta(minutes=minsd)
        secsd = tdiff.total_seconds()
        print("%dh %dm %.2fs" % (hoursd, minsd, secsd), end=' ', file=sys.stderr)
        ediff = datetime.timedelta(seconds=(nfits - ndone) / rate)
        eta = starttime + ediff
        print(eta.strftime("ETA %d/%m/%Y %H:%M:%S"), file=sys.stderr)
        mydb.commit()

mydb.commit()
print("Run complete", nalready, "were done already", file=sys.stderr)
