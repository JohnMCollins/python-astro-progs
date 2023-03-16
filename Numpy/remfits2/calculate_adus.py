#!  /usr/bin/env python3

"""Record ADU calculations"""

import argparse
import sys
#import math
import warnings
#import numpy as np
from astropy.utils.exceptions import ErfaWarning
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import col_from_file
import stdarray
import find_results
import logs

warnings.simplefilter('ignore', ErfaWarning)
warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Calculate ADUs from findresults records in DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('files', type=str, nargs='*', help='List of obsids or use stdin')
parsearg.add_argument('--biasfile', type=str, required=True, help='New-style bias file to use')
parsearg.add_argument('--flatfile', type=str, required=True, help='New style flat file to use')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
parsearg.add_argument('--skylevelstd', type=float, default=remfits.DEFAULT_SKYLEVELSTD, help='Theshold level of std devs to include points in sky')
parsearg.add_argument('--stoperr', action='store_false', help='Stop processing if any errors met')
parsearg.add_argument('--nullstop', action='store_true', help='Stop processing if nothing found for an observation')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
ids = resargs['files']
remdefaults.getargs(resargs)
skylevelstd = resargs['skylevelstd']
stoperr = resargs['stoperr']
nullstop = resargs['nullstop']
if len(ids) == 0:
    ids = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
biasfile = remdefaults.stdarray_file(resargs['biasfile'])
flatfile = remdefaults.stdarray_file(resargs['flatfile'])
logging = logs.getargs(resargs)

try:
    biasarray = stdarray.load_array(biasfile)
except stdarray.StdArrayErr as e:
    logging.die(10, "Cannot open bias file", biasfile, "error was", e.args[0])
try:
    flatarray = stdarray.load_array(flatfile)
except stdarray.StdArrayErr as e:
    logging.die(11,"Cannot open flat file", flatfile, "error was", e.args[0])

errors = nullres = 0

mydb, dbcurs = remdefaults.opendb(waitlock=True)

had_obsind = set()
resulttab = []

for file in ids:
    logging.set_filename(file)
    try:
        ff = remfits.parse_filearg(file, dbcurs)
    except remfits.RemFitsErr as e:
        logging.write("Cannot open error was", e.args[0])
        errors += 1
        continue

    obsind = ff.from_obsind
    if obsind == 0:
        logging.write("No obsind found")
        errors += 1
        continue

    had_obsind.add(obsind)
    dbcurs.execute("SELECT objind,nrow,ncol,apsize,ind FROM findresult WHERE hide=0 AND obsind={:d}".format(obsind))
    frows = dbcurs.fetchall()
    if  len(frows) == 0:
        logging.write("No find results")
        nullres += 1
        continue

    imagedata = ff.data
    fimagedata = imagedata.flatten()
    skymask = fimagedata - ff.meanval <= skylevelstd * ff.stdval
    fimagedata = fimagedata[skymask]
    if len(fimagedata) < 100:
        logging.write("No possible sky")
        errors += 1
        continue

    # We've hopefully excluded objects from result so we can put
    # the std dev of the sky in as the error

    imagedata = stdarray.StdArray(values=imagedata, stddevs=fimagedata.std())

    # Apply bias and flats

    imagedata -= biasarray
    imagedata /= flatarray

    # Calculate sky level again and subtract.

    fimagedata = imagedata.get_values().flatten()[skymask]
    skylevel = fimagedata.mean()
    skystd = fimagedata.std()

    for objind, row, col, apsize, frind in frows:

        try:
            adus, aduerr = imagedata.get_sum(col, row, apsize)
        except stdarray.StdArrayErr as e:
            if e.errortype == stdarray.INVALID_COL:
                logging.write("Cannot fetch for obj", objind, "column", e.args[1], "out of range")
            elif e.errortype == stdarray.INVALID_ROW:
                logging.write("Cannot fetch for obj", objind, "row", e.args[1], "out of range")
            else:
                logging.write("Cannot fetch for obj", objind, e.args[0])
            continue
        if adus <= 0:
            logging.write("Skipping", objind, "as negative", adus)
            continue
        fr = find_results.FindResult()
        fr.loaddb(dbcurs, ind=frind)
        modadus = fr.calculate_mod_integral()
        modaduerr = aduerr # cheat for now
        resulttab.append((obsind, objind, frind, skylevel, skystd, apsize, adus, aduerr, modadus, modaduerr))

if errors != 0:
    logging.write(errors, "errors found")
    if stoperr:
        sys.exit(1)
if nullres != 0:
    logging.write(nullres, "have no results")
    if nullstop:
        sys.exit(1)

if len(resulttab) == 0:
    logging.die(2, "No usable results found")

# Delete previous with the observations we had

deletions = 0
for obsind in had_obsind:
    deletions += dbcurs.execute("DELETE FROM aducalc WHERE obsind={:d}".format(obsind))
if deletions == 0:
    logging.write("No existing adu calculations deleted")
else:
    mydb.commit()
    logging.write(deletions, "existing calculations deleted")

for obsind, objind, frind, skylevel, skystd, apsize, adus, aduerr, modadus, modaduerr in resulttab:
    dbcurs.execute("INSERT INTO aducalc (objind,obsind,frind,skylevel,skystd,apsize,aducount,aduerr,modaducount,modaduerr) " \
                   "VALUES ({:d},{:d},{:d},{:.8e},{:.8e},{:.2f},{:.8e},{:.8e},{:.8e},{:.8e})".format(objind,
                                                                                                      obsind,
                                                                                                      frind,
                                                                                                      skylevel,
                                                                                                      skystd,
                                                                                                      apsize,
                                                                                                      adus,
                                                                                                      aduerr,
                                                                                                      modadus,
                                                                                                      modaduerr))
    dbcurs.execute("UPDATE findresult SET apsize={:.2f},adus={:.8e},modadus={:.8e} WHERE ind={:d}".format(apsize,adus,modadus,frind))
mydb.commit()
logging.write(len(resulttab), "rows added")
sys.exit(0)
