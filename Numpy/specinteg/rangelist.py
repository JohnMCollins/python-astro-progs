#! /local/home/jcollins/lib/anaconda/bin/python

# Display ratio calculation vs EW

import argparse
import sys
import string
import datarange

parsearg = argparse.ArgumentParser(description='List ranges')
parsearg.add_argument('--rangefile', help="XML file of ranges", type=str)
parsearg.add_argument('--outfile', help="Output file if not STDOUT", type=str)

res = vars(parsearg.parse_args())
rf = res['rangefile']
outf = res['outfile']

if rf is None:
    print "No range file specified"
    sys.exit(100)
try:
    rangelist = datarange.load_ranges(rf)
except datarange.DataRangeError as e:
    print "Range load error", e.args[0]
    sys.exit(101)

rsnames = rangelist.listranges()
rlist = [ rangelist.getrange(r) for r in rsnames]
rlist.sort(key=lambda r: r.description)
dw = reduce(lambda x,y: max(x,len(y.description)), rlist, 0)
sw = reduce(lambda x,y: max(x,len(y.shortname)), rlist, 0)
tf = "%-" + str(dw) + "s %-" + str(sw) + "s %10s %10s %10s"
if outf is not None:
    ofil = open(outf, 'w')
    sys.stdout = ofil
print tf % ('Description', 'Short', 'Low', 'High', 'Diff')
print tf % ('=' * 11, '=' * 5, '===', '====', '====')
fmt = "%-" + str(dw) + "s %-" + str(sw) + "s %#10.6g %#10.6g %#10.6g%s"
for r in rlist:
    niu = ""
    if r.notused: niu = " (not in use)"
    print fmt % (r.description, r.shortname, r.lower, r.upper, r.upper-r.lower, niu)

