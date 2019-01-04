#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-12-06T17:47:07+00:00
# @Email:  jmc@toad.me.uk
# @Filename: countoccs.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:28:07+00:00

import sys
import string
import numpy as np
import argparse
import locale

def thou(n):
    """Print n with thousands separator"""
    return locale.format("%d", n, grouping=True)

parsearg = argparse.ArgumentParser(description='Tabulate first 3 occs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='File args')
resargs = vars(parsearg.parse_args())

flist = resargs['files']

nonefound = []
found1oth = []
found2oth = []
found3oth = []
found12oth = []
found13oth = []
found23oth = []
found1 = []
found2 = []
found3 = []
found12 = []
found13 = []
found23 = []
found123 = []

for f in flist:

    rf = open(f)
    rf.readline()
    rf.readline()

    tab = []
    for lin in rf:
        bits = string.split(lin)
        bits.pop(0)
        bits.pop(0)
        arr = [float(x) for x in bits]
        tab.append(arr)

    rf.close()
    tab = np.array(tab)
    o1 = tab[:, 1]
    o2 = tab[:, 2]
    o3 = tab[:, 3]
    nonefound.append(np.count_nonzero((o1<0) & (o2<0) & (o3<0)))
    found1oth.append(np.count_nonzero(o1>0))
    found2oth.append(np.count_nonzero(o2>0))
    found3oth.append(np.count_nonzero(o3>0))
    found1.append(np.count_nonzero((o1>0) & (o2<0) & (o3<0)))
    found2.append(np.count_nonzero((o1<0) & (o2>0) & (o3<0)))
    found3.append(np.count_nonzero((o1<0) & (o2<0) & (o3>0)))
    found12oth.append(np.count_nonzero((o1>0) & (o2>0)))
    found13oth.append(np.count_nonzero((o1>0) & (o3>0)))
    found23oth.append(np.count_nonzero((o2>0) & (o3>0)))
    found12.append(np.count_nonzero((o1>0) & (o2>0) & (o3<0)))
    found13.append(np.count_nonzero((o1>0) & (o2<0) & (o3>0)))
    found23.append(np.count_nonzero((o1<0) & (o2>0) & (o3>0)))
    found123.append(np.count_nonzero((o1>0) & (o2>0) & (o3>0)))

print("No ref objs found &", " & ".join([thou(x) for x in nonefound]), "\\\\")
print("Obj 1 &", " & ".join([thou(x) for x in found1oth]), "\\\\")
print("Obj 2 &", " & ".join([thou(x) for x in found2oth]), "\\\\")
print("Obj 3 &", " & ".join([thou(x) for x in found3oth]), "\\\\")
print("Obj 1 only &", " & ".join([thou(x) for x in found1]), "\\\\")
print("Obj 2 only &", " & ".join([thou(x) for x in found2]), "\\\\")
print("Obj 3 only &", " & ".join([thou(x) for x in found3]), "\\\\")
print("Objs 1 and 2 &", " & ".join([thou(x) for x in found12oth]), "\\\\")
print("Objs 1 and 3 &", " & ".join([thou(x) for x in found13oth]), "\\\\")
print("Objs 2 and 3 &", " & ".join([thou(x) for x in found23oth]), "\\\\")
print("Objs 1 and 2 only &", " & ".join([thou(x) for x in found12]), "\\\\")
print("Objs 1 and 3 only &", " & ".join([thou(x) for x in found13]), "\\\\")
print("Objs 2 and 3 only &", " & ".join([thou(x) for x in found23]), "\\\\")
print("Objs 1,2 and 3 &", " & ".join([thou(x) for x in found123]), "\\\\")
