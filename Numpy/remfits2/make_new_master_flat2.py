#!  /usr/bin/env python3

""""Create new-style master flat files part 2"""

import argparse
import sys
import os
import os.path
import numpy as np
import remdefaults
import col_from_file
import stdarray

# Shut up warning messages

parsearg = argparse.ArgumentParser(description='Create of new-stylemaster flat file part 2 ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Filenames to process, otherwise use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg, inlib=False, tempdir=False)
parsearg.add_argument('--outfile', type=str, default="Flat", help='Output file prefix')
#parsearg.add_argument('--badpix', type=str, help='Bad pixel mask file to use')
parsearg.add_argument('--force', action='store_true', help='Force overwrite if file(s) exist')
parsearg.add_argument('--stoperr', action='store_true', help='Stop processing if any files rejected')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
outfile = resargs['outfile']
#badpix = resargs['badpix']
stoperr = resargs['stoperr']
force = resargs['force']

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
    if len(files) == 0:
        print("No files to process", file=sys.stderr)
        sys.exit(51)

outfile = remdefaults.stdarray_file(outfile)
if os.path.exists(outfile) and not force:
    print(outfile, "already exists, use --force if needed", file=sys.stderr)
    sys.exit(52)

datalist = []
stdlist = []
errors = 0

for file in files:
    try:
        arr = stdarray.load_array(remdefaults.stdarray_file(file))
    except  stdarray.StdArrayErr  as  e:
        print("Could not open", file, file=sys.stderr)
        errors += 1

    datalist.append(arr.get_values())
    stdlist.append(arr.get_stddev())

if len(datalist) == 0:
    print("Stopping as no files to process", file=sys.stderr)
    sys.exit(100)

datalist = np.array(datalist)
stdlist = np.array(stdlist)

weights = datalist.mean(axis=(1,2))
sumweights = np.sum(weights)
numweights = len(weights)
vecweights = weights.reshape((numweights, 1, 1))

# So we're normalising now

datalist /= vecweights
stdlist /= vecweights

# Compute weighted geometric means as exp(SIGMA(wi * log xi) / W) where W is sigma(wi)
# Compute variance as g**2 * SIGMA(wi**2/W**2 * sigmai**2 / xi**2)

logdata = np.log(datalist)
gmeans = np.exp(np.sum(logdata * vecweights, axis=0) / sumweights)
gstdsq = gmeans**2 * np.sum((((stdlist * vecweights) / datalist) / sumweights) ** 2, axis=0)
normv = gmeans.mean()
gmeans *= normv
gstdsq *= normv
result = stdarray.StdArray(values=gmeans, stdsq=gstdsq)

try:
    stdarray.save_array(outfile, result)
except stdarray.StdArrayErr as e:
    print("Could not save", outfile, "error was", e.args[0], file=sys.stderr)
    sys.exit(200)
