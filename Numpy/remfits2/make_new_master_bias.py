#!  /usr/bin/env python3

"""Create new-style master bias file"""

import argparse
import warnings
import sys
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

parsearg = argparse.ArgumentParser(description='Create new-style master bias file ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('iforbinds', nargs='*', type=str, help='Filenames or iforbinds to process, otherwise use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg, inlib=False, tempdir=False)
parsearg.add_argument('--outfile', type=str, required=True, help='Output new array file')
parsearg.add_argument('--filter', type=str, help='Specify filter otherwise deduced from files')
parsearg.add_argument('--stoperr', action='store_true', help='Stop processing if any files rejected')
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file')
parsearg.add_argument('--usemean', action='store_true', help='Use mean of values rather than median')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['iforbinds']
outfile = remdefaults.stdarray_file(resargs['outfile'])
filter_name = resargs['filter']
stoperr = resargs['stoperr']
force = resargs['force']
usemean = resargs['usemean']

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(50)

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
    if len(files) == 0:
        print("No files to process", file=sys.stderr)
        sys.exit(51)

mydb, mycurs = remdefaults.opendb()

# If none given as base, use first one

sfiles = set(files)

# This manoeuvre is to eliminate duplicates

files = sorted(list(sfiles))

# Save all the remfits structs in ffiles

ffiles = []
dims = None
basef = None
errors = 0

for file in files:
    try:
        rf = remfits.parse_filearg(file, mycurs, 'B')
    except remfits.RemFitsErr as e:
        print("Loading from", file, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    if rf.ftype != "Daily bias":
        print("File type of", file, "is", rf.ftype, "not bias", file=sys.stderr)
        errors += 1
        continue
    if filter_name is None:
        filter_name = rf.filter
    elif rf.filter != filter_name:
        print("Filter of", file, "is", rf.filter, "but using", filter_name, file=sys.stderr)
        errors += 1
        continue
    if dims is None:
        dims = rf.dimscr()
    elif dims != rf.dimscr():
        print("Dimensions of", file, "filter", rf.filter, "are", rf.dimscr(), "whereas previous are", dims, file=sys.stderr)
        errors += 1
        continue
    ffiles.append(rf)

if (errors > 0  and  stoperr) or len(ffiles) == 0:
    print("Stopping due to", errors, "-", len(ffiles), "files loaded", file=sys.stderr)
    sys.exit(100)

arrblock = []
for ff in ffiles:
    arrblock.append(ff.data)
arrblock = np.array(arrblock)

if usemean:
    result_values = arrblock.mean(axis=0)
else:
    result_values = np.median(arrblock, axis=0)

try:
    result = stdarray.StdArray(values=result_values, stddevs=arrblock.std(axis=0))
    stdarray.save_array(outfile, result)
except stdarray.StdArrayErr  as  e:
    print("Could not save result error was", e.args[0], file=sys.stderr)
    sys.exit(100)
