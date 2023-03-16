#! /usr/bin/env python3

"""Display fields in FTIS files"""

import argparse
import sys
import remdefaults
import logs
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import col_from_file
import remfits

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Display field from FITS header',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='*', help='List of FITS files or use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--field', type=str, help='Field to displa, comma separatedy', default='OBJECT')
parsearg.add_argument('--plusfn', action='store_true', help='Prepend file name if listing for only one file')
parsearg.add_argument('--list', action='store_true', help='List field names in each file')
parsearg.add_argument('--padding', type=str, default="\t", help='Padding in front of field lines')
remdefaults.parseargs(parsearg, inlib=False, libdir=False, tempdir=False)
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
filelist = resargs['files']
if len(filelist) == 0:
    filelist = col_from_file.col_from_file(sys.stdin, resargs["colnum"])
fields = resargs['field'].split(',')
plusfn = resargs['plusfn'] or len(filelist) > 1
listf = resargs['list']
padding = resargs['padding']
remdefaults.getargs(resargs)
logging = logs.getargs(resargs)

mydb, dbcurs = remdefaults.opendb()

errors = 0

try:

    for filen in filelist:

        try:
            ff = remfits.parse_filearg(filen, dbcurs)
        except remfits.RemFitsErr as e:
            logging.write("Could not open", filen, "error was", e.args[0])
            errors += 1
            continue

        h = ff.hdr

        if listf:
            ks = sorted(list(h.keys()))
            vals = [str(h[k]) for k in ks]
        else:
            ks = fields
            vals = []
            for k in ks:
                try:
                    vals.append(h[k])
                except KeyError:
                    vals.append("Not known")

        maxl = max([len(k) for k in ks])
        pad = ""
        if plusfn:
            print(filen, ":", sep='')
            pad = padding
        for k,v in zip(ks, vals):
            print("{pad:s}{name:<{lng}s} = {val:}".format(pad=pad, name=k, val=v, lng=maxl))
except (KeyboardInterrupt, BrokenPipeError):
    pass
if errors > 0:
    sys.exit(1)
sys.exit(0)
