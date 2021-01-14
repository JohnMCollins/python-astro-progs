#!  /usr/bin/env python3

import dbops
import remdefaults
import argparse
import sys
import os.path
import miscutils
import numpy as np
import remfield
import remdefaults
import warnings
import copy

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Display percentage effect of cutoffs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
remfield.parseargs(parsearg)
parsearg.add_argument('--outfile', type=str, help='Output file for results')
parsearg.add_argument('--prec', type=int, default=2, help="Digits of precison for percentages")
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
outfile = resargs['outfile']
prec = resargs['prec']

outputfile = sys.stdout
if outfile is not None:
    outfile = miscutils.addsuffix(outfile, "tex")
    outputfile = open(outfile, "wt")

fieldselect = ["typ='flat'", "ind!=0", "gain=1", "rejreason IS NULL"]
noselect = copy.copy(fieldselect)
origselect = copy.copy(fieldselect)
newmeansel = copy.copy(fieldselect)
origselect.append('mean>=5000')
origselect.append('mean<=50000')
origselect.append('skew<0')
origselect.append('kurt<6')
remfield.getargs(resargs, fieldselect)
remfield.parsepair(resargs, 'mean', newmeansel, 'mean')

mydb, mycurs = remdefaults.opendb()

mycurs.execute("SELECT filter,COUNT(*) FROM iforbinf WHERE " + " AND ".join(noselect) + " GROUP BY filter")
totalrows = mycurs.fetchall()

totalfiles = dict()
for f, t in totalrows:
    totalfiles[f] = t

mycurs.execute("SELECT filter,COUNT(*) FROM iforbinf WHERE " + " AND ".join(origselect) + " GROUP BY filter")
totalrows = mycurs.fetchall()

origfiles = dict()
for f, t in totalrows:
    origfiles[f] = t

mycurs.execute("SELECT filter,COUNT(*) FROM iforbinf WHERE " + " AND ".join(newmeansel) + " GROUP BY filter")
totalrows = mycurs.fetchall()

newmeanselfiles = dict()
for f, t in totalrows:
    newmeanselfiles[f] = t

mycurs.execute("SELECT filter,COUNT(*) FROM iforbinf WHERE " + " AND ".join(fieldselect) + " GROUP BY filter")
totalrows = mycurs.fetchall()

fsfiles = dict()
for f, t in totalrows:
    fsfiles[f] = t

fstring = "{pref}{filter}{suff} & {orig:.{prec}f} & {newmean:.{prec}f} & {newsel:.{prec}f}\\\\"
for f in sorted(totalfiles.keys()):
    tt = totalfiles[f] / 100.00
    print(fstring.format(pref="\\texttt{", suff="}", filter=f, prec=prec, orig=origfiles[f] / tt, newmean=newmeanselfiles[f] / tt, newsel=fsfiles[f] / tt), file=outputfile)

tt = sum([totalfiles[f] for f in totalfiles.keys()]) / 100.0
torig = sum([origfiles[f] for f in origfiles.keys()])
tnew = sum([newmeanselfiles[f] for f in newmeanselfiles.keys()])
tfs = sum([fsfiles[f] for f in fsfiles.keys()])
print("\\hline", file=outputfile)
print(fstring.format(pref="", suff="", filter="Overall", prec=prec, orig=torig / tt, newmean=tnew / tt, newsel=tfs / tt), file=outputfile)
