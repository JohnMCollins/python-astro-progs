#!  /usr/bin/env python3

"""Get variability flags on objects from GAIA DR3"""

import datetime
import argparse
import sys
from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord
import astropy.units as u
import remdefaults
import objdata

Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"

parsearg = argparse.ArgumentParser(description='Get variability flags from Gaia DR3', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('target', nargs=1, type=str, help='Target object to search vicinity of')
parsearg.add_argument('--reset', action='store_true', help='Reset any object already marked as variable')
parsearg.add_argument('--vvalue', type=float, default=1.0, help='Value to set variability to')
parsearg.add_argument('--radius', type=float, default=0.5, help='Radius around object in degrees')
parsearg.add_argument('--nresults', type=int, default=10000, help='Search limit for GAIA')
remdefaults.parseargs(parsearg, tempdir=False, database=False)

resargs = vars(parsearg.parse_args())
targname, = resargs['target']
remdefaults.getargs(resargs)
resetv = resargs['reset']
vvalue = resargs['vvalue']
radius = resargs['radius']
Gaia.ROW_LIMIT = resargs['nresults']

mydb, mycursor = remdefaults.opendb()

objdat = objdata.ObjData(name=targname)
try:
    objdat.get(mycursor)
except objdata.ObjDataError as e:
    print("Problem with target", targname, " ".join(e.args), file=sys.stderr)
    sys.exit(20)

objdat.apply_motion(datetime.datetime.now())

j = Gaia.cone_search_async(SkyCoord(ra=objdat.ra, dec=objdat.dec, unit=(u.deg, u.deg)), u.Quantity(radius, u.deg))

gaia_results = j.get_results()
desigs = gaia_results['DESIGNATION']
photvar = gaia_results['phot_variable_flag']

if len(desigs) >= Gaia.ROW_LIMIT:
    print("Warning may be others outside limit of", Gaia.ROW_LIMIT, file=sys.stderr)

varids = [des for des, var in zip(desigs, photvar) if var != 'NOT_AVAILABLE' ]

selids = " OR ".join(["objname=" + mydb.escape(id) for id in varids])
if not resetv:
    selids = "variability IS NULL AND (" + selids + ")"
ndone = mycursor.execute("UPDATE objdata SET variability={:.6g} WHERE ".format(vvalue) + selids)
print(ndone, "records updated", file=sys.stderr)
if ndone != 0:
    mydb.commit()
