#!  /usr/bin/env python3

"""Display findresult file"""

import argparse
import sys
import warnings
from astropy.utils.exceptions import ErfaWarning
import remdefaults
import find_results
import objdata
import miscutils
import parsetime
import remfits

warnings.simplefilter('ignore', ErfaWarning)

parsearg = argparse.ArgumentParser(description='Display find object results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results file(s)')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--dispname', action='store_true', help='Display file name etc if only one file')
parsearg.add_argument('--summary', action='store_true', help='Display summary of file')
parsearg.add_argument('--testmin', type=int, help='Test at least the given number of objects found no output')
parsearg.add_argument('--object', type=str, help='Give statistics for object if listing summary')
parsearg.add_argument('--present', action='store_true', help='Return 0 exit code if given object present default target')
parsearg.add_argument('--daterange', type=str, help='Range of dates to limit to')
parsearg.add_argument('--filter', type=str, help='Filter name to limit to')
parsearg.add_argument('--onlyfile', action='store_true', help='Only show file name')
parsearg.add_argument('--diffs', action='store_true', help='Show row/col diffs')
parsearg.add_argument('--nohide', action='store_false', help='Do not show hidden results')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
summary = resargs['summary']
testmin = resargs['testmin']
targobj = resargs['object']
present = resargs['present']
daterange = resargs['daterange']
filtonly = resargs['filter']
onlyfile = resargs['onlyfile']
diffs = resargs['diffs']
nohide = resargs['nohide']

dispname = len(files) > 1 or resargs['dispname']

if daterange is not None:
    dr = parsetime.DateRangeArg()
    try:
        dr.parsearg(daterange)
    except ValueError as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(30)
    daterange = dr

ndone = 0

if onlyfile:
    for fil in files:
        try:
            findres = find_results.load_results_from_file(fil)
        except find_results.FindResultErr as e:
            print(fil, "gave error", e.args[0], file=sys.stderr)
            sys.exit(10)
        if daterange and not daterange.inrange(findres.obsdate):
            continue
        if filtonly and filtonly != findres.filter:
            continue
        ndone += 1
        print(miscutils.removesuffix(fil, 'findres'))
    if ndone == 0:
        sys.exit(1)
    sys.exit(0)

mydb, dbcurs = remdefaults.opendb()
if targobj:
    targobj = objdata.get_objname(dbcurs, targobj)

if present:
    for fil in files:
        try:
            findres = find_results.load_results_from_file(fil)
        except find_results.FindResultErr as e:
            print(fil, "gave error", e.args[0], file=sys.stderr)
            sys.exit(10)
        if daterange and not daterange.inrange(findres.obsdate):
            continue
        if filtonly and filtonly != findres.filter:
            continue
        try:
            if targobj:
                tres = findres[targobj]
                continue
            tres = findres[0]
            if not tres.istarget:
                sys.exit(1)
        except find_results.FindResultErr:
            sys.exit(1)
        ndone += 1
    if ndone == 0:
        sys.exit(1)
    sys.exit(0)

if testmin is not None:
    for fil in files:
        try:
            findres = find_results.load_results_from_file(fil)
        except find_results.FindResultErr as e:
            print(fil, "gave error", e.args[0], file=sys.stderr)
            sys.exit(10)
        if daterange and not daterange.inrange(findres.obsdate):
            continue
        if filtonly and filtonly != findres.filter:
            continue
        if findres.num_results() < testmin:
            sys.exit(1)
        ndone += 1
    if ndone == 0:
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
    for fil in files:
        try:
            findres = find_results.load_results_from_file(fil)
        except find_results.FindResultErr as e:
            print(fil, "gave error", e.args[0], file=sys.stderr)
            sys.exit(10)
        if daterange and not daterange.inrange(findres.obsdate):
            continue
        if filtonly and filtonly != findres.filter:
            continue
        names.append(miscutils.removesuffix(fil, 'findres'))
        totid.append(findres.num_results(True))
        totf.append(findres.num_results())
        dats.append(findres.obsdate)
        filts.append(findres.filter)
        try:
            tobj = findres[targobj]
            if tobj.objident is None:
                tobj = 0.0
            else:
                tobj = tobj.adus
        except find_results.FindResultErr:
            tobj = 0.0
        adus.append(tobj)
        ndone += 1
    nw = max([0] + [len(n) for n in names])
    for nam, i, ni, dat, adus, filt in zip(names, totid, totf, dats, adus, filts):
        print("{n:<{nw}s} {dat:%Y-%m-%d} {filt:s} {i:4d} {ni:4d} {adus:12.2f}".format(n=nam, nw=nw, dat=dat, filt=filt, i=i, ni=ni, adus=adus))
    if ndone == 0:
        sys.exit(1)
    sys.exit(0)

had = 0

try:
    for fil in files:
        try:
            findres = find_results.load_results_from_file(fil)
        except find_results.FindResultErr as e:
            print(fil, "gave error", e.args[0], file=sys.stderr)
            continue
        if daterange and not daterange.inrange(findres.obsdate):
            continue
        if filtonly and filtonly != findres.filter:
            continue
        ndone += 1
        namelength = max([len(r.obj.objname) for r in findres.results() if r.obj is not None] + [0])
        if namelength == 0:
            print("No identified results in", fil, file=sys.stderr)
        if dispname:
            if had != 0:
                print("\n")
            had += 1
            print(fil, findres.obsdate.strftime("%d/%m/%Y @ %H:%M:%S:"))
            print("Filter:", findres.filter, findres.nrows, "rows", findres.ncols, "columns")
            if findres.signif is not None and findres.totsignif is not None:
                print("Significance {:.2f} total significance {:.2f}".format(findres.signif, findres.totsignif))
            pixoff = remfits.Pixoffsets(obsind=findres.obsind)
            if pixoff.get_offsets(dbcurs):
                print("Offsets in DB: Row={:.2f} Col={:.3f}".format(pixoff.rowoffset, pixoff.coloffset))
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
                         lw=lnamelength, dnw=dnamelength), end='')
            if diffs:
                print("\tr={:.2f} c={:.2f} ({:.2f}/{:.2f})".format(r.row, r.col, r.rdiff, r.cdiff), end='')
            print()
#            robj = objdata.ObjData()
#            robj.get(dbcurs, r.objident.objname)
#            robj.apply_motion(findres.obsdate)
#            print("{lab:<{lw}s} {dn:<{dnw}s} {ap:5.2f} {adus:10.2f} {ra:8.3f} {dec:8.3f} {radiff:8.3f} {decdiff:8.3f}".
#                  format(dn=r.dispname, lab=r.label, ap=r.apsize, adus=r.adus, ra=r.radeg, dec=r.decdeg, radiff=r.radeg - robj.objposition.ra, decdiff=r.decdeg - robj.objposition.dec,
#                         lw=lnamelength, dnw=dnamelength))
except (KeyboardInterrupt, BrokenPipeError):
    pass
if ndone == 0:
    sys.exit(1)
sys.exit(0)
