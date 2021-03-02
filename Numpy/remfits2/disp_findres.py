#!  /usr/bin/env python3

"""Display findresult file"""

import argparse
import warnings
import sys
import remdefaults
import obj_locations
import find_results
import match_finds
import objdata

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Display find object results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results file(s)')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--dispname', action='store_true', help='Display file name if only one file')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)

dispname = len(files) > 1 or resargs['dispname']

mydb, dbcurs = remdefaults.opendb()

for fil in files:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        continue
    namelength = max([len(r.name) for r in findres.results()] + [0])
    if namelength == 0:
        print("No identified results in", fil, file=sys.stderr)
    if dispname:
        print(fil, ":\n\n", sep='')
    dnamelength = max([len(r.dispname) for r in findres.results()] + [1])
    lnamelength = max([len(r.label) for r in findres.results()] + [1])
    for r in findres.results():
        if len(r.name) == 0:
            print("{lab:<{lw}s} {dn:<{dnw}s} {ap:2d} {ra:8.3f} {dec:8.3f}".
              format(nam=r.name, dn=r.dispname, lab=r.label, ap=r.apsize, ra=r.radeg, dec=r.decdeg,
                     lw=lnamelength, nw=namelength, dnw=dnamelength))
            continue
        robj = objdata.ObjData(r.name)
        robj.get(dbcurs)
        robj.apply_motion(findres.obsdate)
        print("{lab:<{lw}s} {dn:<{dnw}s} {ap:2d} {ra:8.3f} {dec:8.3f} {radiff:8.3f} {decdiff:8.3f}".
              format(nam=r.name, dn=r.dispname, lab=r.label, ap=r.apsize, ra=r.radeg, dec=r.decdeg, radiff=r.radeg - robj.ra, decdiff=r.decdeg - robj.dec,
                     lw=lnamelength, nw=namelength, dnw=dnamelength))
