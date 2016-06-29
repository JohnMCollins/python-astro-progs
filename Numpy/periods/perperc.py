#! /usr/bin/env python

# Analyse period recovery results and produce lines of percent recovery to given percentages

import argparse
import os
import os.path
import sys
import string
import numpy as np

parsearg = argparse.ArgumentParser(description='Analysse period recovery',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infile', type=str, nargs=1, help='List of periods (Printpgram output)')
parsearg.add_argument('--periods', type=float, nargs='+', help='Periods')
parsearg.add_argument('--percent', type=float, nargs='+', help='Acceptable percents')
parsearg.add_argument('--cumulative', action='store_true', help='Do we want numbers in each range or cumulative on successive ones')
parsearg.add_argument('--latex', action='store_true', help='Insert Latex separateors')
parsearg.add_argument('--precision', type=int, default=0, help='Precision of result')

resargs = vars(parsearg.parse_args())

infile = resargs['infile'][0]
periods = resargs['periods']
percents = resargs['percent']
cumul = resargs['cumulative']
latex = resargs['latex']
prec = resargs['precision']

fmt = "%%.%df" % prec

try:
    inf = np.loadtxt(infile)    # No unpack we're going in rows not cols
except IOError:
    print "Cannot open file", infile
    sys.exit(10)

pdiffs = np.outer(periods, percents) / 100.0
res = np.zeros_like(pdiffs)

for row in inf:
    upd = np.zeros_like(pdiffs, dtype=np.bool)
    for nper, per in enumerate(pdiffs):
        for npc, pc in enumerate(per):
            upd[nper,npc] |= np.count_nonzero(np.abs(row-periods[nper]) < pc) != 0
    if cumul:
        for nper, per in enumerate(pdiffs):
            for npc, pc in enumerate(per):
                upd[nper:,npc] |= upd[nper,npc]
    res += upd

res /= inf.shape[0]
res *= 100.0
resb = [fmt % p for p in res.flatten()]
if latex:
    resbp = string.join(resb, ' & ') + '\\\\'
else:
    resbp = string.join(resb, ' ')
print resbp



            