#!  /usr/bin/env python3

# This program is intended to be run non-interactively.
# It copies new observation data but not the FITS files to the named
# #database, by default "remfits" but an alternative can be given as the
# first argument

import dbops
import sys
import remdefaults
import argparse
import mydateutil


def gotserial(serial):
	"""Check if we've got that serial already"""
	global mycurs
	mycurs.execute("SELECT COUNT(*) FROM iforbinf WHERE serial=%d" % serial)
	r = mycurs.fetchall()
	return  r[0][0] != 0


parsearg = argparse.ArgumentParser(description='Copy dark frams info to local DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

mydb, mycurs = remdefaults.opendb()
remdb = dbops.opendb('rdotsquery')
remcurs = remdb.cursor()

destfields = []
destfields.append('serial')
destfields.append('typ')
destfields.append('filter')
destfields.append('date_obs')
destfields.append('mjdobs')
destfields.append('exptime')
destfields.append('fname')
destfields.append('ffname')

destfields = "INSERT INTO iforbinf (" + ','.join(destfields) + ") VALUES"

rowsadded = rowsalready = 0

remcurs.execute("SELECT serial,filter,date_obs,mjdobs,exptime,fname FROM Dark WHERE exptime!=0 AND filter REGEXP '[griz]'")
darkrows = remcurs.fetchall()

for serial, filter, dateobs, mjddate, exptime, fname in darkrows:
	if filter not in 'griz':
		continue
	if gotserial(serial):
		rowsalready += 1
		continue
	destvals = []
	destvals.append("%d" % serial)
	destvals.append(mydb.escape('dark'))
	destvals.append(mydb.escape(filter))
	destvals.append(mydb.escape(mydateutil.mysql_datetime(dateobs)))
	destvals.append("%.16e" % mjddate)
	destvals.append("%.16e" % exptime)
	destvals.append(mydb.escape(fname))
	ffname = "ImgsDBArchive/Dark/"
	ffname += dateobs.strftime("%Y%m%d/") + fname + ".fits.gz"
	destvals.append(mydb.escape(ffname))
	destvals = "(" + ','.join(destvals) + ")"
	print(destfields)
	print(destvals)
	mycurs.execute(destfields + destvals)
	rowsadded += 1

if rowsadded != 0:
	mydb.commit()

print(rowsadded, "rows added had", rowsalready, "already", file=sys.stderr)

sys.exit(0)
