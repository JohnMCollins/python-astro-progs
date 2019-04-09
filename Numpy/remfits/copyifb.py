#!  /usr/bin/env python3

# This program is intended to be run non-interactively.
# It copies new observation data but not the FITS files to the named
# #database, by default "remfits" but an alternative can be given as the
# first argument

import dbops
import sys
import remdefaults
import argparse

def insert_row(typ, row):
	"""Insert row into my copy of database"""
	global mycurs, destfields
	global rowsadded
	filter, dateobs, mjddate, exptime, fname = row
	if filter not in 'griz':
		return
	destvals = []
	destvals.append("'" + typ + "'")
	destvals.append("'" + filter + "'")
	destvals.append(dateobs.strftime("'%Y-%m-%d %H:%M:%S'"))
	destvals.append("%.16e" % mjddate)
	destvals.append("%.16e" % exptime)
	destvals.append("'" + fname + "'")
	if typ == 'flat':
		ffname = "ImgsDBArchive/Flat/"
	else:
		ffname = "ImgsDBArchive/Dark/"
	ffname += dateobs.strftime("%Y%m%d/") + fname + ".fits.gz"
	destvals.append("'" + ffname + "'")
	destvals = "(" + ','.join(destvals) + ")"
	mycurs.execute(destfields + destvals)
	rowsadded += 1

remdb = dbops.opendb('rdotsquery')

# Open appropriate local database according to what machine we are on or options supplied

mydbname = remdefaults.default_database()
try:
    firstarg = sys.argv[1]
    if firstarg[0] == '-':
        parsearg = argparse.ArgumentParser(description='Copy new entries from rdots dark/flat files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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
destfields.append('typ')
destfields.append('filter')
destfields.append('date_obs')
destfields.append('mjdobs')
destfields.append('exptime')
destfields.append('fname')
destfields.append('ffname')

destfields = "INSERT INTO iforbinf (" + ','.join(destfields) + ") VALUES"
obsfields = "SELECT filter,date_obs,mjdobs,exptime,fname FROM "

# Get the latest date we have copies of

have_max = mycurs.execute("SELECT MAX(date_obs) FROM iforbinf")
rowlist = mycurs.fetchall()
latest_got = rowlist[0][0]

# If zero, we've not done it yet

rowsadded = 0

if latest_got is None:
	remcurs.execute(obsfields + "Dark WHERE exptime=0")
	for row in remcurs.fetchall():
		insert_row('bias', row)
	remcurs.execute(obsfields + "Flat")
	for row in remcurs.fetchall():
		insert_row('flat', row)
else:
	datemax = latest_got.strftime("'%Y-%m-%d %H:%M:%S'")
	remcurs.execute(obsfields + "Dark WHERE exptime=0 AND date_obs>" + datemax)
	for row in remcurs.fetchall():
		insert_row('bias', row)
	remcurs.execute(obsfields + "Flat WHERE date_obs>" + datemax)
	for row in remcurs.fetchall():
		insert_row('flat', row)

mydb.commit()
print(rowsadded, "row(s) added")
if rowsadded == 0:
	sys.exit(1)
sys.exit(0)
