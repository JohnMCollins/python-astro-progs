#!  /usr/bin/env python3

# This program is intended to be run non-interactively.
# It copies new observation data but not the FITS files to the named
# #database, by default "remfits" but an alternative can be given as the
# first argument

import sys
import remdefaults
import remget
import argparse

parsearg = argparse.ArgumentParser(description='Copy new bias or flat FITS files to local DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--verbose', action='store_false', help='Print out summary of what has been loaded')
resargs = vars(parsearg.parse_args())
verbose = resargs['verbose']
remdefaults.getargs(resargs)

fieldselect = []
fieldselect.append("ind=0")
fieldselect.append("rejreason IS NULL")

mydb, mycurs = remdefaults.opendb()

loaded = errors = 0

selection = "SELECT iforbind,ffname FROM iforbinf WHERE " + " AND ".join(fieldselect)
mycurs.execute(selection)
dbrows = mycurs.fetchall()

for iforbind, ffname in dbrows:
	try:
		ffile = remget.get_iforb(ffname)
		mycurs.execute("INSERT INTO fitsfile (side,fitsgz) VALUES (1024,%s)", ffile)
		mycurs.execute("UPDATE iforbinf SET ind=%d WHERE iforbind=%d" % (mycurs.lastrowid, iforbind))
		mydb.commit()
		loaded += 1
	except remget.RemGetError as e:
		print("Caould not fetch %d error was %s" % (iforbind, e.args[0]), file=sys.stderr)
		mycurs.execute("UPDATE iforbinf SET rejreason='FITS file not found' WHERE iforbind=%d" % iforbind)
		errors += 1

if verbose:
	if errors > 0:
		print(errors, "files not loaded", file=sys.stderr)
	if loaded > 0:
		print(loaded, "files loaded", file=sys.stderr)
	else:
		print("Nothing loaded", file=sys.stderr)
if errors > 0:
	sys.exit(1)
sys.exit(0)
