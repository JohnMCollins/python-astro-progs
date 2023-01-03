#!  /usr/bin/env python3

"""Record ADU calculations"""

import argparse
import sys
import math
import warnings
import numpy as np
from astropy.utils.exceptions import ErfaWarning
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import col_from_file
import stdarray

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
parsearg.add_argument('--skylevelstd', type=float, default=0.5, help='Theshold level of std devs to include points in sky')
parsearg.add_argument('--stoperr', action='store_false', help='Stop processing if any errors met')
parsearg.add_argument('--nullstop', action='store_true', help='Stop processing if nothing found for an observation')

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

try:
    biasarray = stdarray.load_array(biasfile)
except stdarray.StdArrayErr as e:
    print("Cannot open bias file", biasfile, "error was", e.args[0], file=sys.stderr)
    sys.exit(10)
try:
    flatarray = stdarray.load_array(flatfile)
except stdarray.StdArrayErr as e:
    print("Cannot open flat file", flatfile, "error was", e.args[0], file=sys.stderr)
    sys.exit(11)

errors = nullres = 0

mydb, dbcurs = remdefaults.opendb()

objsfound = dict()
had_obsind = set()
resulttab = []

for file in ids:
    try:
        ff = remfits.parse_filearg(file, dbcurs)
    except remfits.RemFitsErr as e:
        print("Cannot open", file, "error was", e.args[0], file=sys.stderr)
        errors += 1
        continue

    obsind = ff.from_obsind
    if obsind == 0:
        print("No obsind found in", file, file=sys.stderr)
        errors += 1
        continue

    had_obsind.add(obsind)
    dbcurs.execute("SELECT objind,nrow,ncol,apsize,ind FROM findresult WHERE hide=0 AND obsind={:d}".format(obsind))
    frows = dbcurs.fetchall()
    if  len(frows) == 0:
        print("No find results for", file, file=sys.stderr)
        nullres += 1
        continue

    imagedata = ff.data
    fimagedata = imagedata.flatten()
    skymask = fimagedata - ff.meanval <= skylevelstd * ff.stdval
    fimagedata = fimagedata[skymask]
    if len(fimagedata) < 100:
        print("No possible sky in", file, file=sys.stderr)
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

        if objind in objsfound:
            iapsize, apmask = objsfound[objind]
        else:
            iapsize = int(math.floor(apsize))
            xpoints, ypoints = np.meshgrid(range(-iapsize, iapsize + 1), range(-iapsize, iapsize + 1))
            radsq = apsize ** 2
            xsq = xpoints ** 2
            ysq = ypoints ** 2
            apmask = xsq + ysq <= radsq
            apmask = apmask.flatten()
            objsfound[objind] = (iapsize, apmask)

        try:
            adus, aduerr = imagedata.get_sum(row, col, iapsize, apmask)
        except stdarray.StdArrayErr as e:
            if e.errortype == stdarray.INVALID_COL:
                print("Cannot fetch for obj", objind, "column", e.args[1], "out of range", file=sys.stderr)
            elif e.errortype == stdarray.INVALID_ROW:
                print("Cannot fetch for obj", objind, "row", e.args[1], "out of range", file=sys.stderr)
            else:
                print("Cannot fetch for obj", objind, e.args[0], file=sys.stderr)
            continue
        if adus <= 0:
            print("Skipping", objind, "as negative", adus, file=sys.stderr)
            continue
        resulttab.append((obsind, objind, frind, skylevel, skystd, adus, aduerr))

if errors != 0:
    print(errors, "errors found", file=sys.stderr)
    if stoperr:
        sys.exit(1)
if nullres != 0:
    print(nullres, "have no results", file=sys.stderr)
    if nullstop:
        sys.exit(1)

if len(resulttab) == 0:
    print("No usable results found", file=sys.stderr)
    sys.exit(2)

# Delete previous with the observations we had

deletions = 0
for obsind in had_obsind:
    deletions += dbcurs.execute("DELETE FROM aducalc WHERE obsind={:d}".format(obsind))
if deletions == 0:
    print("No existing adu calculations deleted", file=sys.stderr)
else:
    mydb.commit()
    print(deletions, "existing calculations deleted", file=sys.stderr)

for obsind, objind, frind, skylevel, skystd, adus, aduerr in resulttab:
    dbcurs.execute("INSERT INTO aducalc (objind,obsind,frind skylevel,skystd,aducount,aduerr) " \
                   "VALUES ({:d},{:d},{:d},{:.8e},{:.8e},{:.8e},{:.8e})".format(objind,obsind,frind,skylevel,skystd,adus, aduerr))
mydb.commit()
print(len(resulttab), "rows added", file=sys.stderr)


sys.exit(0)
