#!  /usr/bin/env python3

"""Load new individual flat or bias files"""

import sys
import argparse
import remdefaults
import remget
import logs

parsearg = argparse.ArgumentParser(description='Copy new bias or flat FITS files to local DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
logs.parseargs(parsearg)
parsearg.add_argument('--verbose', action='store_false', help='Print out summary of what has been loaded')
parsearg.add_argument('--debug', action='store_true', help='Debug queries')
resargs = vars(parsearg.parse_args())
logging = logs.getargs(resargs)
verbose = resargs['verbose']
debug = resargs['debug']
remdefaults.getargs(resargs)

fieldselect = []
fieldselect.append("ind=0")
fieldselect.append("rejreason IS NULL")

mydb, mycurs = remdefaults.opendb()

loaded = errors = 0

selection = "SELECT iforbind,ffname FROM iforbinf WHERE " + " AND ".join(fieldselect)
if debug:
    logging.write("Selection is:", selection)
mycurs.execute(selection)
dbrows = mycurs.fetchall()

for iforbind, ffname in dbrows:
    try:
        ffile = remget.get_iforb(ffname)
        mycurs.execute("INSERT INTO fitsfile (side,fitsgz) VALUES (1024,%s)", ffile)
        mycurs.execute(f"UPDATE iforbinf SET ind={mycurs.lastrowid} WHERE iforbind={iforbind}")
        mydb.commit()
        loaded += 1
    except remget.RemGetError as e:
        logging.write(f"Caould not fetch {iforbind} error was {e.args[0]}")
        mycurs.execute(f"UPDATE iforbinf SET rejreason='FITS file not found' WHERE iforbind={iforbind}")
        errors += 1

if verbose:
    if errors > 0:
        logging.write(errors, "files not loaded")
    if loaded > 0:
        logging.write(loaded, "files loaded")
    else:
        logging.write("Nothing loaded")
if errors > 0:
    sys.exit(1)
sys.exit(0)
