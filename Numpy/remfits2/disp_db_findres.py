#!  /usr/bin/env python3

"""Display findresult file"""

import argparse
import sys
import warnings
from astropy.utils.exceptions import ErfaWarning
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import col_from_file
import remdefaults
import find_results
import objdata
import miscutils
import parsetime
import remfits

warnings.simplefilter('ignore', ErfaWarning)
warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Display find object results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ids', nargs='*', type=str, help='Obs ids or files containing them')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--dispname', action='store_true', help='Display file name etc if only one file')
parsearg.add_argument('--summary', action='store_true', help='Display summary of file')
parsearg.add_argument('--testmin', type=int, help='Test at least the given number of objects found no output')
parsearg.add_argument('--object', type=str, help='Give statistics for object if listing summary')
parsearg.add_argument('--present', action='store_true', help='Return 0 exit code if given object present default target')
parsearg.add_argument('--daterange', type=str, help='Range of dates to limit to')
parsearg.add_argument('--filter', type=str, help='Filter name to limit to')
parsearg.add_argument('--diffs', action='store_true', help='Show row/col diffs')
parsearg.add_argument('--nohide', action='store_false', help='Do not show hidden results')

resargs = vars(parsearg.parse_args())
ids = resargs['ids']
if len(ids) == 0:
    ids = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
remdefaults.getargs(resargs)
summary = resargs['summary']
testmin = resargs['testmin']
targobj = resargs['object']
present = resargs['present']
daterange = resargs['daterange']
filtonly = resargs['filter']
diffs = resargs['diffs']
nohide = resargs['nohide']

dispname = len(ids) > 1 or resargs['dispname']

if daterange is not None:
    dr = parsetime.DateRangeArg()
    try:
        dr.parsearg(daterange)
    except ValueError as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(30)
    daterange = dr

mydb, dbcurs = remdefaults.opendb()
if targobj:
    targobj = objdata.get_objname(dbcurs, targobj)

findres_array = []

for sobsind in ids:
    if sobsind.isnumeric():
        obsind = int(sobsind)
        dbcurs.execute("SELECT filter,date_obs,nrows,ncols FROM obsinf WHERE obsind={:d}".format(obsind))
        params = dbcurs.fetchone()
        if params is None:
            print("Cannot find record of obsind {:d}".format(obsind), file=sys.stderr)
            continue
        findres = find_results.FindResults()
        findres.obsind = obsind
        findres.filter, findres.obsdate, findres.nrows, findres.ncols = params
    else:
        try:
            fitsfile = remfits.parse_filearg(sobsind, dbcurs)
        except remfits.RemFitsErr as e:
            print(sobsind, "gave error", e.args[0], file=sys.stderr)
            continue
        findres = find_results.FindResults(remfitsobj = fitsfile)

    if daterange and not daterange.inrange(findres.obsdate):
        continue
    if filtonly and filtonly != findres.filter:
        continue

    findres.loaddb(dbcurs)
    findres_array.append(findres)

if present:
    for findres in findres_array:
        if targobj is None:
            if findres.num_results() == 0  or not findres[0].istarget:
                sys.exit(1)
        elif  targobj not in findres:
            sys.exit(1)
        continue
    sys.exit(0)

if testmin is not None:
    if len(findres_array) == 0:
        sys.exit(1)
    for findres in findres_array:
        if  findres.num_results(idonly=True, nohidden=True) < testmin:
            sys.exit(1)
    sys.exit(0)

if summary:
    names = []
    totid = []
    totf = []
    dats = []
    adus = []
    filts = []

    if targobj is None:
        targobj = 0

    for findres in findres_array:

        names.append("{:d}".format(findres.obsind))
        totid.append(findres.num_results(True))
        totf.append(findres.num_results())
        dats.append(findres.obsdate)
        filts.append(findres.filter)

    nw = max([0] + [len(n) for n in names])
    for nam, i, ni, dat, adus, filt in zip(names, totid, totf, dats, adus, filts):
        print("{n:<{nw}s} {dat:%Y-%m-%d} {filt:s} {i:4d} {ni:4d} {adus:12.2f}".format(n=nam, nw=nw, dat=dat, filt=filt, i=i, ni=ni, adus=adus))
    sys.exit(0)

# Just list

had = 0

try:
    for findres in findres_array:
        namelength = max([len(r.obj.dispname) for r in findres.results() if r.obj is not None] + [0])
        if dispname:
            if had != 0:
                print("\n")
            had += 1
            print("{:d}: {:%d/%m/%Y @ %H:%M:%S}".format(findres.obsind, findres.obsdate))
            print("Filter:", findres.filter, findres.nrows, "rows", findres.ncols, "columns")
            print()
        dnamelength = max([len(r.obj.dispname) for r in findres.results() if r.obj is not None] + [1])
        lnamelength = max([len(r.label) for r in findres.results()] + [1])
        for r in findres.results():
            if nohide and r.hide:
                continue
            try:
                dispn = r.obj.dispname
            except AttributeError:
                dispn = ""
            print("{lab:<{lw}s} {dn:<{dnw}s} {ap:5.2f} {adus:10.2f} {ra:8.3f} {dec:8.3f}".
                  format(dn=dispn, lab=r.label, ap=r.apsize, adus=r.adus, ra=r.radeg, dec=r.decdeg,
                         lw=lnamelength, dnw=dnamelength))
except (KeyboardInterrupt, BrokenPipeError):
    pass
