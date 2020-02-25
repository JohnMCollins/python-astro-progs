#!  /usr/bin/env python3

# This program is intended to be run non-interactively.
# It copies new observation data but not the FITS files to the named
# #database, by default "remfits" but an alternative can be given as the
# first argument

import dbops
import sys
import remdefaults
import argparse

def insert_row(row):
	"""Insert row into my copy of database"""
	global mycurs, destfields
	global rowsadded
	radeg, decdeg, object, dithid, filter, dateobs, mjddate, exptime, fname, ffname = row
	destvals = []
	destvals.append("%.16e" % radeg)
	destvals.append("%.16e" % decdeg)
	destvals.append("'" + object + "'")
	destvals.append("%d" % dithid)
	destvals.append("'" + filter + "'")
	destvals.append(dateobs.strftime("'%Y-%m-%d %H:%M:%S'"))
	destvals.append("%.16e" % mjddate)
	destvals.append("%.16e" % exptime)
	destvals.append("'" + fname + "'")
	destvals.append("'" + ffname + "'")
	destvals = "(" + ','.join(destvals) + ")"
	mycurs.execute(destfields + destvals)
	rowsadded += 1

remdb = dbops.opendb('rdots')

# Open appropriate local database according to what machine we are on or options supplied

mydbname = remdefaults.default_database()
try:
    firstarg = sys.argv[1]
    if firstarg[0] == '-':
        parsearg = argparse.ArgumentParser(description='Copy new entries from rdots log to local DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parsearg.add_argument('--database', type=str, default=mydbname, help='Local database to use')
        resargs = vars(parsearg.parse_args())
        mydbname = resargs['database']
    else:
        mydbname = firstarg
except IndexError:
        pass

mydb = dbops.opendb(mydbname)

remcurs = remdb.cursor()
mycurs = mydb.cursor()

destfields = []
destfields.append('radeg')
destfields.append('decdeg')
destfields.append('object')
destfields.append('dithID')
destfields.append('filter')
destfields.append('date_obs')
destfields.append('mjdobs')
destfields.append('exptime')
destfields.append('fname')
destfields.append('ffname')

destfields = "INSERT INTO obsinf (" + ','.join(destfields) + ") VALUES"
obsfields = "SELECT radeg,decdeg,object,dithID,filter,date_obs,mjdobs,exptime,fname,ffname(date_obs,fname) AS ff FROM Obslog"

# Get the latest date we have copies of

have_max = mycurs.execute("SELECT MAX(date_obs) FROM obsinf")
rowlist = mycurs.fetchall()
latest_got = rowlist[0][0]

# If zero, we've not done it yet

rowsadded = 0

if latest_got is None:
	remcurs.execute(obsfields)
else:
	datemin = latest_got.strftime("'%Y-%m-%d 00:00:00'")
	datemax = latest_got.strftime("'%Y-%m-%d 23:59:59'")
	wherecl = "WHERE date_obs>=" + datemin + " AND date_obs<=" + datemax
	mycurs.execute("SELECT ffname FROM obsinf " + wherecl)
	fgot = dict()
	for row in mycurs.fetchall():
		fgot[row[0]] = 1
	remcurs.execute(obsfields + " " + wherecl)
	for row in remcurs.fetchall():
		if row[-1] not in fgot:
			insert_row(row)
	remcurs.execute(obsfields + " WHERE date_obs>" + datemax)

for row in remcurs.fetchall():
	insert_row(row)

mydb.commit()
print(rowsadded, "row(s) added")
if rowsadded == 0:
	sys.exit(1)
sys.exit(0)
