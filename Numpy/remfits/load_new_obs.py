#!  /usr/bin/env python3

"""Load new FITS files from observations"""

import sys
import argparse
import remdefaults
import remtargets
import parsetime
import remget
import logs

parsearg = argparse.ArgumentParser(description='Copy new or specified FITS files to local DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsinds', type=int, nargs='*', help='Specific obsids to load if required')
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
logs.parseargs(parsearg)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--remir', action='store_true', help='Load REMIR files')
parsearg.add_argument('--verbose', action='store_false', help='Print out summary of what has been loaded')
parsearg.add_argument('--targets', action='store_false', help='Load files for targets otherwise everything')
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to restrict load to (plus targets if specified)')
parsearg.add_argument("--debug", action='store_true', help='Debug selection command')
resargs = vars(parsearg.parse_args())
logging = logs.getargs(resargs)
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
        oids = '(' + " OR ".join([ f"obsind={x}" for x in obsinds]) + ')'
    else:
        oids = f"obsind={obsinds[0]}"
    fieldselect.append(oids)
else:
    fieldselect.append("rejreason IS NULL")
    try:
        parsetime.getargs_daterange(resargs, fieldselect)
    except ValueError as e:
        logging.die(20, e.args[0])
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
    logging.write("Selection:", selection)
mycurs.execute(selection)

dbrows = mycurs.fetchall()

for ffname, dithID, obsind in dbrows:
    try:
        ffile = remget.get_obs(ffname, dithID != 0)
        side = 1024
        if dithID != 0:
            side = 512
        mycurs.execute(f"INSERT INTO fitsfile (side,fitsgz) VALUES ({side},%s)", ffile)
        mycurs.execute(f"UPDATE obsinf SET ind={mycurs.lastrowid} WHERE obsind={obsind}")
        mydb.commit()
        loaded += 1
    except remget.RemGetError as e:
        logging.write(f"Caould not fetch {obsind} error was {e.args[0]}")
        mycurs.execute(f"UPDATE obsinf SET rejreason='FITS file not found' WHERE obsind={obsind}")
        errors += 1

if verbose:
    if errors > 0:
        logging.write(errors, "files not loaded")
    if loaded > 0:
        logging.write(loaded, "files loaded")
    else:
        logging.write("No new obs files loaded")
if errors > 0:
    sys.exit(1)
sys.exit(0)
