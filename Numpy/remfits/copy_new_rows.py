#!  /usr/bin/env python3

"""Copy details of new data from Red Dots DB to in-house"""

# This program is intended to be run non-interactively.
# It copies new observation data but not the FITS files to the named
# #database, by default "remfits" but an alternative can be given as the
# first argument

import sys
import argparse
import remdefaults
import dbops
import logs

def get_max_serial(tabname, constraint):
    """Get the maximumn serail number we have from the given table.
	A constraint is given, needed to distinguish between ROS2 and REMIR
	or flat and bias"""

    mycurs.execute("SELECT MAX(serial) FROM " + tabname + " WHERE " + constraint)
    rows = mycurs.fetchall()
    return  rows[0][0]


def insert_obs_row(row):
    """Insert row into my copy of database"""
    serial, radeg, decdeg, obj, dithid, filt, dateobs, mjddate, exptime, fname, ffname = row
    destvals = []
    destvals.append(f'{serial}')
    destvals.append(f'{radeg}')
    destvals.append(f'{decdeg}')
    destvals.append(mydb.escape(obj))
    destvals.append(f'{dithid}')
    destvals.append(mydb.escape(filt))
    destvals.append(dateobs.strftime("'%Y-%m-%d %H:%M:%S'"))
    destvals.append(f'{mjddate}')
    destvals.append(f'{exptime}')
    destvals.append(mydb.escape(fname))
    destvals.append(mydb.escape(ffname))
    query = destfields + "(" + ','.join(destvals) + ")"
    if debug:
        logging.write("Insert query is", query)
    mycurs.execute(query)
    return  1


def insert_iforb_row(t, row):
    """Insert row into my copy of database"""
    serial, filt, dateobs, mjddate, exptime, fname = row
    if filt not in 'griz':
        return 0
    destvals = []
    destvals.append(f'{serial}')
    destvals.append(mydb.escape(t))
    destvals.append(mydb.escape(filt))
    destvals.append(dateobs.strftime("'%Y-%m-%d %H:%M:%S'"))
    destvals.append(f'{mjddate}')
    destvals.append(f'{exptime}')
    destvals.append("'" + fname + "'")
    if t == 'flat':
        ffname = "ImgsDBArchive/Flat/"
    else:
        ffname = "ImgsDBArchive/Dark/"
    ffname += dateobs.strftime("%Y%m%d/") + fname + ".fits.gz"
    destvals.append(mydb.escape(ffname))
    destvals = "(" + ','.join(destvals) + ")"
    query = destfields + destvals
    if debug:
        logging.write("Insert query is", query)
    mycurs.execute(query)
    return 1


remdb = dbops.opendb('rdots')
remcurs = remdb.cursor()

# Can put database name as arg on its own to be consistent with old version

if len(sys.argv) > 1 and sys.argv[1][0] != '-':
    remdefaults.my_database = sys.argv[1]
    verbose = True
else:
    parsearg = argparse.ArgumentParser(description='Copy new entries from rdots log to local DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
    logs.parseargs(parsearg)
    parsearg.add_argument('--verbose', action='store_false', help='Print out summary of what has been loaded')
    parsearg.add_argument('--debug', action='store_true', help='Debug queries')
    resargs = vars(parsearg.parse_args())
    verbose = resargs['verbose']
    debug = resargs['debug']
    remdefaults.getargs(resargs)
    logging = logs.getargs(resargs)

mydb, mycurs = remdefaults.opendb()

# Get maximum ROS2 serial and maximum REMIR serial we have as they are separate

destfields = []
destfields.append('serial')
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
obsfields = "SELECT serial,radeg,decdeg,object,dithID,filter,date_obs,mjdobs,exptime,fname,ffname(date_obs,fname) AS ff FROM Obslog WHERE serial>%d AND %s"

row_add_list = []

for dith_state in ("dithID=0", "dithID!=0"):
    rowsadded = 0
    max_serial = get_max_serial("obsinf", dith_state)
    query = obsfields % (max_serial, dith_state)
    if debug:
        logging.write("Obs query:", query)
    remcurs.execute(query)
    for dbrow in remcurs.fetchall():
        rowsadded += insert_obs_row(dbrow)
    row_add_list.append(rowsadded)
    if rowsadded != 0:
        mydb.commit()

# Now repeat for daily flats and biases

remdb.close()
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
obsfields = "SELECT serial,filter,date_obs,mjdobs,exptime,fname FROM "

for tab, constr, typ in (("Dark", "exptime=0", 'bias'), ("Dark", "exptime!=0", 'dark'), ("Flat", None, 'flat')):
    rowsadded = 0
    max_serial = get_max_serial("iforbinf", "typ='" + typ + "'")
    if max_serial is None:
        row_add_list.append(0)
        continue
    query = obsfields + tab + f" WHERE serial>{max_serial}"
    if constr is not None:
        query += " AND " + constr
    if debug:
        logging.write("Running query for", typ, "-", query)
    remcurs.execute(query)
    for dbrow in remcurs.fetchall():
        rowsadded += insert_iforb_row(typ, dbrow)
    row_add_list.append(rowsadded)
    if rowsadded != 0:
        mydb.commit()

if sum(row_add_list) == 0:
    if verbose:
        print("No new rows added")
    sys.exit(1)

if verbose:
    ros, remir, bias, dark, flat = row_add_list
    if ros != 0:
        print(ros, "new ROS2 rows added")
    if remir != 0:
        print(remir, "new REMIR rows added")
    if bias != 0:
        print(bias, "new daily bias rows added")
    if dark != 0:
        print(dark, "new daily dark rows added")
    if flat != 0:
        print(flat, "new daily flat rows added")

sys.exit(0)
