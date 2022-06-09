#!  /usr/bin/env python3

# This program is intended to be run non-interactively.
# It copies new observation data but not the FITS files to the named
# #database, by default "remfits" but an alternative can be given as the
# first argument

import dbops
import sys
import remdefaults
import remtargets
import parsetime
import remget
import argparse

parsearg = argparse.ArgumentParser(description='Copy new or specified FITS files to local DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsinds', type=int, nargs='*', help='Specific obsids to load if required')
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--remir', action='store_true', help='Load REMIR files')
parsearg.add_argument('--verbose', action='store_false', help='Print out summary of what has been loaded')
parsearg.add_argument('--targets', action='store_false', help='Load files for targets otherwise everything')
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to restrict load to (plus targets if specified)')
parsearg.add_argument("--debug", action='store_true', help='Debug selection command')
resargs = vars(parsearg.parse_args())
obsinds = resargs['obsinds']
plusremir = resargs['remir']
verbose = resargs['verbose']
targets = resargs['targets']
objects = resargs['objects']
debug = resargs['debug']

remdefaults.getargs(resargs)

fieldselect = []
fieldselect.append("ind=0")

if len(obsinds) != 0:
	if len(obsinds) > 1:
		oids = '(' + " OR ".join([ "obsind=%d" % x for x in obsinds]) + ')'
	else:
		oids = "obsind=%d" % obsinds[0]
	fieldselect.append(oids)
else:
	fieldselect.append("rejreason IS NULL")
	try:
		parsetime.getargs_daterange(resargs, fieldselect)
	except ValueError as e:
		print(e.args[0], file=sys.stderr)
		sys.exit(20)
	if not plusremir:
		fieldselect.append("dithID=0")

mydb, mycurs = remdefaults.opendb()

objselect_list = []
if targets:
	remtargets.remtargets(mycurs, objselect_list)
if objects and len(objects) != 0:
	for ob in objects:
		objselect_list.append("object=" + mydb.escape(ob))
if len(objselect_list) != 0:
	if len(objselect_list) == 1:
		fieldselect += objselect_list
	else:
		fieldselect.append("(" + " OR ".join(objselect_list) + ")")

loaded = errors = 0

selection = "SELECT ffname,dithID,obsind FROM obsinf WHERE " + " AND ".join(fieldselect)
if debug:
	print("Selection:", selection, file=sys.stderr)
mycurs.execute(selection)

dbrows = mycurs.fetchall()

for ffname, dithID, obsind in dbrows:
	try:
		ffile = remget.get_obs(ffname, dithID != 0)
		side = 1024
		if dithID != 0:
			side = 512
		mycurs.execute("INSERT INTO fitsfile (side,fitsgz) VALUES (" + str(side) + ",%s)", ffile)
		mycurs.execute("UPDATE obsinf SET ind=%d WHERE obsind=%d" % (mycurs.lastrowid, obsind))
		mydb.commit()
		loaded += 1
	except remget.RemGetError as e:
		print("Caould not fetch %d error was %s" % (obsind, e.args[0]), file=sys.stderr)
		mycurs.execute("UPDATE obsinf SET rejreason='FITS file not found' WHERE obsind=%d" % obsind)
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
