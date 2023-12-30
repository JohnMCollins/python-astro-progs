#! /usr/bin/env python3

"""Plot Proper Motions of object"""

import sys
import argparse
from astropy.time import Time
from barycorrpy import utc_tdb
import remdefaults

La_Silla_lat = -70.7380
La_Silla_long = -29.2563
La_Silla_alt = 2400

HIPs = {"ProximaCenb": 70890, "BarnardStar": 87937, "Ross154": 92403}

parsearg = argparse.ArgumentParser(description='Calculate Barycentric dates of targets', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--listn', type=int, default=10, help="List progress every n")
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
resargs = vars(parsearg.parse_args())
countevery = resargs['listn']
remdefaults.getargs(resargs)

mydb, mycurs = remdefaults.opendb()

mycurs.execute("SELECT obsind,date_obs,object FROM obsinf WHERE " + "(" + " OR ".join(["object=" + mydb.escape(t) for t in HIPs]) + ") AND bjdobs IS NULL")

rows = mycurs.fetchall()

ToDo = len(rows)
if  ToDo == 0:
    print("No Barcycentric conversions to do", file=sys.stderr)
    sys.exit(0)

Todopc = 100.0 / ToDo
Done = 0

for obsind, date_obs, objname in rows:
    bjdresult = utc_tdb.JDUTC_to_BJDTDB(Time(date_obs), hip_id=HIPs[objname], lat=La_Silla_lat, longi=La_Silla_long, alt=La_Silla_alt)[0][0]
    mycurs.execute(f"UPDATE obsinf SET bjdobs={bjdresult:.12e} WHERE obsind={obsind}")
    Done += 1
    if countevery > 0 and Done % countevery == 0:
        mydb.commit()
        print(f"Done {Done} out of {ToDo} {Done * Todopc:.2f}%", file=sys.stderr)

mydb.commit()
print("Update of BJDs complete", file=sys.stderr)
