#! /usr/bin/env python

"""Extract times and flux from ASAS Data files"""

import argparse
import os.path
import sys
import numpy as np

parsearg = argparse.ArgumentParser(description='Extract times and flux ASAS zip', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='ASAS file to process')
parsearg.add_argument('--outfile', type=str, help='Output file name if not stdout')
parsearg.add_argument('--column', type=int, default=1, help='Column 1 to 5')
parsearg.add_argument('--noclass', type=str, help='Exclude obs of given class')
parsearg.add_argument('--inclerr', action='store_false', help='Include std dev column')

resargs = vars(parsearg.parse_args())
input_file = resargs['file'][0]
output_file = resargs['outfile']
column = resargs['column']
noclass = resargs['noclass']
inclerr = resargs['inclerr']

if column < 1 or column > 5:
    print("Column should be between 1 and 5", file=sys.stderr)
    sys.exit(9)

if not os.path.exists(input_file):
    print("Cannot find input file", input_file, file=sys.stderr)
    sys.exit(10)

results = []

with open(input_file, 'rt') as inf:
    for line in inf:
        if len(line) == 0 or line[0] == '#':
            continue
        parts = line.split()
        if len(parts) != 13:
            continue
        if noclass is not None and parts[-2] in noclass:
            continue
        results.append((float(parts[0]), float(parts[column]), float(parts[column+5])))

if len(results) == 0:
    print("No results found", file=sys.stderr)
    sys.exit(11)

results = np.array(results)
if not inclerr:
    results = results[:,:1]

if output_file is None:
    output_file = sys.stdout
else:
    output_file = open(output_file, 'wt')

np.savetxt(output_file, results)
