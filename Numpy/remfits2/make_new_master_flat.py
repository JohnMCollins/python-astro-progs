#!  /usr/bin/env python3

""""Create new-style master flat files"""

import argparse
import warnings
import sys
import os
import os.path
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import numpy as np
import remdefaults
import remfits
import col_from_file
import stdarray

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
warnings.simplefilter('error', RuntimeWarning)

parsearg = argparse.ArgumentParser(description='Create of new-stylemaster flat file ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('iforbinds', nargs='*', type=str, help='Filenames or ids to process, otherwise use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg, inlib=False, tempdir=False)
parsearg.add_argument('--biasfile', type=str, required=True, help='(New-style) bias file to use')
parsearg.add_argument('--outprefix', type=str, default="Flat", help='Output file prefix')
#parsearg.add_argument('--badpix', type=str, help='Bad pixel mask file to use')
parsearg.add_argument('--filter', type=str, help='Specify filter otherwise deduced from files')
parsearg.add_argument('--force', action='store_true', help='Force overwrite if file(s) exist')
parsearg.add_argument('--stoperr', action='store_true', help='Stop processing if any files rejected')
parsearg.add_argument('--stopneg', action='store_true', help='Stop processing if any negative pixels found')
parsearg.add_argument('--delfail', action='store_true', help='Delete all output files if any fail')

resargs = vars(parsearg.parse_args())
files = resargs['iforbinds']
remdefaults.getargs(resargs)
biasfile = remdefaults.stdarray_file(resargs['biasfile'])
outprefix = resargs['outprefix']
#badpix = resargs['badpix']
filter_name = resargs['filter']
stoperr = resargs['stoperr']
stopneg = resargs['stopneg']
force = resargs['force']
delfail = resargs['delfail']

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
    if len(files) == 0:
        print("No files to process", file=sys.stderr)
        sys.exit(51)

mydb, mycurs = remdefaults.opendb()

try:
    biasstr = stdarray.load_array(biasfile)
except stdarray.StdArrayErr as e:
    print("Bias file", biasfile, "gave error", e.args[0], file=sys.stderr)
    sys.exit(10)

Bdims = biasstr.shape
files = sorted(files)
usedfiles = []
datalist = []

errors = negerrors = 0

for file in files:
    try:
        rf = remfits.parse_filearg(file, mycurs, 'F')
    except remfits.RemFitsErr as e:
        print("Loading from", file, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    if rf.ftype != "Daily flat":
        print("File type of", file, "is", rf.ftype, "not flat", file=sys.stderr)
        errors += 1
        continue
    if filter_name is None:
        filter_name = rf.filter
    elif rf.filter != filter_name:
        print("Filter of", file, "is", rf.filter, "but using", filter_name, file=sys.stderr)
        errors += 1
        continue
    Rfdims = rf.dimscr()
    Rfdims = (Rfdims[-1], Rfdims[-2])
    if Bdims != Rfdims:
        print("Dimensions of", file, "are", Rfdims, "whereas previous are", Bdims, file=sys.stderr)
        errors += 1
        continue
    imagedata = stdarray.StdArray(values=rf.data) - biasstr
    negpix = np.count_nonzero(imagedata.get_values() <= 0)
    if  negpix != 0:
        print(negpix, "negative pixels in", file, file=sys.stderr)
        negerrors += 1
        continue
    ofile = remdefaults.stdarray_file(outprefix + file)
    if not force and os.path.exists(ofile):
        print(ofile, "exists, specify --force if needed", file=sys.stderr)
        errors += 1
        continue
    usedfiles.append(ofile)
    datalist.append(imagedata)

if len(datalist) == 0:
    print("Stopping as no files to process", file=sys.stderr)
    sys.exit(100)

if errors > 0  and  stoperr:
    print("Stopping as", errors, "errors found", file=sys.stderr)
    sys.exit(101)

if negerrors > 0  and  stopneg:
    print("Stopping as", negerrors, "files with negative pixels", file=sys.stderr)
    sys.exit(102)

outerrs = 0
written = set()

for  ofn, dat in zip(usedfiles, datalist):
    try:
        stdarray.save_array(ofn, dat)
        written.add(ofn)
    except  stdarray.StdArrayErr as e:
        print("Write to", ofn, "failed", e.args[0], file=sys.stderr)
        outerrs += 1

if outerrs != 0:
    if  delfail:
        for ofn in written:
            try:
                os.remove(ofn)
            except OSError:
                pass
    sys.exit(1)

if errors + negerrors != 0:
    sys.exit(1)

sys.exit(0)
