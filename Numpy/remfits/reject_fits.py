#!  /usr/bin/env python3

"""Reject a FITS file with a reason"""

import argparse
import sys
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Mark FITS file with options',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='*', help='Files or ids to process')
parsearg.add_argument('--reason', type=str, nargs='+', required=True, help='Reason for rejecting files')
parsearg.add_argument('--quality', type=float, default=0.0, help='Quality code to assign')
parsearg.add_argument('--delfits', action='store_true', help='Remove FITS file from DB')
parsearg.add_argument('--force', action='store_true', help='Force if already rejected')
parsearg.add_argument('--verbose', action='store_true', help='Give blow by blow account')

remdefaults.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

mydb, mycu = remdefaults.opendb()

files = resargs['files']
reason = resargs['reason']
quality = resargs['quality']
delfits = resargs['delfits']
force = resargs['force']
verbose = resargs['verbose']

reason = " ".join(reason)

dbchanges = 0
updates = []
updates.append("quality={:.6f}".format(quality))
updates.append("rejreason={:s}".format(mydb.escape(reason)))
if  delfits:
    updates.append("ind=0")
updates = "UPDATE obsinf SET " + ",".join(updates)

errors = 0

for file in files:

    try:
        ff = remfits.parse_filearg(file, mycu)
    except remfits.RemFitsErr as e:
        print("Open of", file, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue

    try:
        obsind = ff.from_obsind
    except  AttributeError:
        try:
            obsind = int(file)
        except  ValueError:
            print("Cannot find ind from", file, file=sys.stderr)
            errors += 1
            continue

    mycu.execute("SELECT ind,quality,rejreason FROM obsinf WHERE obsind={:d}".format(obsind))
    existing = mycu.fetchall()
    if  len(existing) == 0:
        print("Did not find obsinf record corresponding to", file, file=sys.stderr)
        errors += 1
        continue

    fitsind, existq, existr = existing[0]
    if  existr is not None and existr != reason:
        if force:
            if  verbose:
                print("Replacing existing reason for", file, "from", existr, "to", reason, file=sys.stderr)
        else:
            print("Reason for", file, "already set to", existr, "use --force if needed", file=sys.stderr)
            errors += 1
            continue

    query = updates + " WHERE obsind={:d}".format(obsind)
    if delfits and fitsind != 0:
        if verbose:
            print("Deleting fits file ind {:d}".format(fitsind), file=sys.stderr)
        mycu.execute("DELETE FROM fitsfile WHERE ind={:d}".format(fitsind))
        dbchanges += 1
    if verbose:
        print("Update obsinf for", file, file=sys.stderr)
    mycu.execute(query)
    dbchanges += 1
    if quality == 0.0:
        for tab in ('findresult', 'aducalc'):
            ndone = mycu.execute("DELETE FROM {:s} WHERE obsind={:d}".format(tab, obsind))
            if verbose and ndone != 0:
                print("Deleted", ndone, "from", tab, file=sys.stderr)
            dbchanges += ndone

if errors != 0:
    sys.exit(1)

if dbchanges != 0:
    mydb.commit()
