#!  /usr/bin/env python3

import remdefaults
import argparse
import sys
import numpy as np
import warnings
import os.path

# Cope with divisions by zero

warnings.simplefilter('ignore', RuntimeWarning)

parsearg = argparse.ArgumentParser(description="Merge bed pixel masks", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('bpms', type=str, nargs='+', help='Input Pixel masks')
remdefaults.parseargs(parsearg, tempdir=False, database=False)
parsearg.add_argument('--outfile', type=str, required=True, help='Output bad pixel mask')
parsearg.add_argument('--force', action='store_true', help='Force if file exists')
parsearg.add_argument('--or', action='store_true', help='Use OR to combine not AND')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
bpmfiles = resargs['bpms']
outfile = resargs['outfile']
force = resargs['force']
orcomb = resargs['or']

if len(bpmfiles) < 2:
    print("Need at least 2 bad pixel masks", file=sys.stderr)
    sys.exit(5)

outfile = remdefaults.bad_pixmask(outfile)

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(11)

masks = []
for bpmf in bpmfiles:
    bpmfile = remdefaults.bad_pixmask(bpmf)
    try:
        mask = np.load(bpmfile)
    except OSError as e:
        print("Could not load", bpmflle, "error was", e.args[1], file=sys.stderr)
        sys.exit(10)
    masks.append(mask)

first = masks.pop(0)
result = first.copy()
try:
    if orcomb:
        for mask in masks:
            result |= mask
    else:
        for mask in masks:
            result &= mask
except ValueError:
    print("Arrays are not all the same size", file=sys.stderr)
    sys.exit(12)
except TypeError:
    print("Arrays all need to be boolean", file=sys.stderr)
    sys.exit(13)

try:
    outf = open(outfile, 'wb')
except OSError as e:
    print("Could not open", outfile, "error was", e.args[1], file=sys.stderr)
    sys.exit(50)

np.save(outf, result)
outf.close()

masks.insert(0, first)  # Put back

nres = np.count_nonzero(result)
print("Result:", "%10d" % nres, sep="\t")
for bpmf, mask in zip(bpmfiles, masks):
    nm = np.count_nonzero(mask)
    if nm == nres and np.count_nonzero(mask ^ result) == 0:
        print(bpmf + ':', "%10d" % nm, "Same as result", sep="\t")
    else:
        print(bpmf + ':', "%10d" % nm, sep="\t")

sys.exit(0)
