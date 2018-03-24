#!  /usr/bin/env python

import dbops
import string
import sys

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
	destvals = "(" + string.join(destvals, ',') + ")"
	mycurs.execute(destfields + destvals)
	rowsadded += 1

remdb = dbops.opendb('rdots')
mydb = dbops.opendb('remfits')

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

destfields = "INSERT INTO obsinf (" + string.join(destfields, ',') + ") VALUES"
obsfields = "SELECT radeg,decdeg,object,dithID,filter,date_obs,mjdobs,exptime,fname,ffname(date_obs,fname) AS ff FROM Obslog"

# Get the latest date we have copies of

have_max = mycurs.execute("SELECT MAX(date_obs) FROM obs")
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
print rowsadded, "row(s) added"
if rowsadded == 0:
	sys.exit(1)
sys.exit(0)

