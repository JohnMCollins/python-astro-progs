#!  /usr/bin/env python3

"""Output statistics about bad pixel mask files"""

import argparse
import warnings
import numpy as np
import remdefaults
import logs

# Cope with divisions by zero

warnings.simplefilter('ignore', RuntimeWarning)

parsearg = argparse.ArgumentParser(description="Annlysis of bed pixel mask", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('bpm', type=str, nargs=1, help='Input Pixel mask')
remdefaults.parseargs(parsearg, tempdir=False, database=False)
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
bpmfile = remdefaults.bad_pixmask(resargs['bpm'][0])
logging = logs.getargs(resargs)

try:
    mask = np.load(bpmfile)
except OSError as e:
    logging.die(10, "Could not load", bpmfile, "error was", e.args[1])

neighbours = np.zeros(mask.shape, dtype=np.uint16)

# See about adjacent columns

overlap = mask[:, 0:-1] & mask[:, 1:]
neighbours[:, 0:-1] += overlap
neighbours[:, 1:] += overlap

# See about adjacent rows

overlap = mask[0:-1, :] & mask[1:, :]
neighbours[0:-1, :] += overlap
neighbours[1:, :] += overlap

# One diagonal

overlap = mask[0:-1, 0:-1] & mask[1:, 1:]
neighbours[0:-1, 0:-1] += overlap
neighbours[1:, 1:] += overlap

# The other diagonal

overlap = mask[0:-1, 1:] & mask[1:, 0:-1]
neighbours[0:-1, 1:] += overlap
neighbours[1:, 0:-1] += overlap

print("Total bad px:%10d" % np.count_nonzero(mask))
print("0 neighbours:%10d" % np.count_nonzero((neighbours == 0) & mask))
for n in range(1, 9):
    print("%d neighbours:%10d" % (n, np.count_nonzero(neighbours == n)))
