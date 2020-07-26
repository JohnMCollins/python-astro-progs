#! /usr/bin/env python3

import os
import sys
import datetime
import string
import warnings
import dbops

if len(sys.argv) > 1:
    db = sys.argv[-1]
else:
    db = "remfits"

remdbase = dbops.opendb(db)
remcursor = remdbase.cursor()
remcopy = dbops.opendb("remcopy")
copycursor = remcopy.cursor()

remcursor.execute("SELECT obsind, date_obs, filter, dithID FROM obsinf WHERE serial=0")
remrows = remcursor.fetchall()

updates = 0
notfoundIR = 0
notfoundvis = 0

for obsind, date_obs, filter, dithID in remrows:
    copycursor.execute("SELECT serial FROM Obslog_myro WHERE date_obs=%s AND filter='" + filter + "' AND dithID=" + str(dithID), date_obs.strftime("%Y-%m-%d %H:%M:%S"))
    srows = copycursor.fetchall()
    if len(srows) == 0:
        print("Couldn't find serial for filter %s date %s, dithID %d" % (filter, date_obs.strftime("%Y-%m-%d %H:%M:%S"), dithID), file=sys.stderr)
        if dithID == 0:
            notfoundvis += 1
        else:
            notfoundIR += 1
        continue
    if len(srows) > 1:
        slist = [str(s[0]) for s in srows]
        print("Serials", ", ".join(slist), "Match filter", filter, "date", date_obs.strftime("%Y-%m-%d %H:%M:%S"), "dithID", dithID, file=sys.stderr)
        continue
    remcursor.execute("UPDATE obsinf SET serial=%d WHERE obsind=%d" % (srows[0][0], obsind))
    updates += 1

remdbase.commit()
print(updates, "obs rows updated", notfoundIR, "IR not found", notfoundvis, "visible not found", file=sys.stderr)
