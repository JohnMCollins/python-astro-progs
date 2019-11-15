#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T18:57:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: lcurve3.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:14+00:00

import numpy as np
import argparse
import sys
import math
import string
import remgeom
import dbops
import remdefaults
import dbremfitsobj
import os
import os.path
import trimarrays
from scipy.signal.tests.test_upfirdn import UpFIRDnCase

rg = remgeom.load()
mydbname = remdefaults.default_database()
tmpdir = remdefaults.get_tmpdir()

parsearg = argparse.ArgumentParser(description='Calculate std deviation and mean of daily flatsl', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
parsearg.add_argument('--filter', type=str, help='Restrict to given filter')

resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
filter = resargs['filter']

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    print("Unable to select temporary directory", tmpdir, file=sys.stderr)
    sys.exit(100)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

if filter is None:
    dbcurs.execute("SELECT iforbind,ind FROM iforbinf WHERE mean IS NULL AND typ='flat' AND ind!=0 AND gain=1")
else:
    dbcurs.execute("SELECT iforbind,ind FROM iforbinf WHERE mean IS NULL AND typ='flat' AND ind!=0 AND gain=1 AND filter=" + dbase.escape(filter))

rows = dbcurs.fetchall()
ndone = 0
for iforbind, ind in rows:
    try:
        ffile = dbremfitsobj.getfits(dbcurs, ind)
    except OSError:
        errorfiles.append(ind)
        print("Could not get FITS file for ind", ind, file=sys.stderr)
        continue
    ffd = ffile[0].data
    ffd = trimarrays.trimzeros(ffd)
    ffile.close()
    ffd = ffd.astype(np.float32)
    dbcurs.execute("UPDATE iforbinf SET mean=%.8e,std=%.8e WHERE iforbind=%d" % (ffd.mean(), ffd.std(), iforbind))
    ndone += 1
    if ndone % 30 == 0:
        dbase.commit()

dbase.commit()
print(ndone, "maens added", file=sys.stderr)
