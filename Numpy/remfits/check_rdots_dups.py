#! /usr/bin/env python3

from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import numpy as np
import os
import sys
import datetime
import string
import warnings
import dbops
import fitsops
import remget

rdotsdb = dbops.opendb('rdots')
rdotscurs = rdotsdb.cursor()

# Get a list of duplicated files

rdotscurs.execute("SELECT COUNT(*) AS n,filter,ffname(date_obs,fname) AS ff FROM Obslog GROUP BY ff,filter HAVING n>1")
dbrows = rdotscurs.fetchall()

print(len(dbrows), "duplications found", file=sys.stderr)
if len(dbrows) == 0:
    sys.exit(0)

for n, filter, ffname in dbrows:
    rdotscurs.execute("SELECT serial,dithID,date_obs,ffname(date_obs, fname) AS ff FROM Obslog HAVING ff=%s", ffname)
    sds = []
    for serial, dithid, date_obs, ff in rdotscurs.fetchall():
        sds.append((serial, date_obs))
    try:
        fhdr, fdata = fitsops.mem_get(remget.get_obs(ffname, dithid != 0))
        obsdate = Time(fhdr['DATE-OBS']).datetime
    except remget.RemGetError as e:
        print("Cannot fetch filel", ff, "error was", e.args[0], file=sys.stderr)
        continue
    except OSError as e:
        print("Cannot open FITS file from", ff, "error was", e.args[0], file=sys.stderr)
        continue
    except KeyError:
        print("Cannot find date in file", ff, file=sys.stderr)
        continue
    print("File", ffname, "with obs date of", obsdate.strftime("%d/%m/%Y @ %H:%M:%S"))
    for serial, date_obs in sds:
        if abs((date_obs - obsdate).total_seconds()) <= 1:
            msg = "Same date"
        else:
            msg = "Different date"
        ts = date_obs.strftime("%d/%m/%Y @ %H:%M:%S")
        print("%16d %s %s" % (serial, ts, msg))
    print()
