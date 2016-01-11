#! /usr/bin/env python

import argparse
import numpy as np

parsearg = argparse.ArgumentParser(description='Join arrays', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='Array files')
parsearg.add_argument('--axis', type=int, default=0, help='Axis to join on')
parsearg.add_argument('--outfile', type=str, required=True, help='Output file')

resargs = vars(parsearg.parse_args())

arrays = []

ax = resargs['axis']

for file in resargs['files']:
    try:
        ar = np.loadtxt(file, unpack=True)
        if len(ar.shape) == 1:
            ar = ar.reshape(1,len(ar))
        arrays.append(ar)
    except IOError as e:
        print "Cannot open", file
        print "Error was", e.args[1]
        sys.exit(10)
    except ValueError as e:
        print "Cannot parse", file
        print "Error was", e.args[0]

result = np.concatenate(arrays, ax)

np.savetxt(resargs['outfile'], result.transpose())
