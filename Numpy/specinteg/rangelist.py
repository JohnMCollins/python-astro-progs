#! /usr/bin/env python

# Display ratio calculation vs EW

import argparse
import sys
import string
import datarange

parsearg = argparse.ArgumentParser(description='List ranges')
parsearg.add_argument('rangefile', help="XML file of ranges", nargs='+', type=str)
parsearg.add_argument('--outfile', help="Output file if not STDOUT", type=str)

res = vars(parsearg.parse_args())
rfs = res['rangefile']
outf = res['outfile']

save_stdout = sys.stdout
ofil = sys.stdout

if outf is not None:
    try:
        ofil = open(outf, 'w')
    except IOError as e:
        sys.stdout = sys.stderr
        print "Error creating output file", outf, "error was", e.args[1]
        sys.exit(100)

errors = 0
had = 0

for rf in rfs:
    try:
        rangelist = datarange.load_ranges(rf)
    except datarange.DataRangeError as e:
        sys.stdout = sys.stderr
        print "Range load error", e.args[0], "file", rf
        errors += 1
        continue
    rsnames = rangelist.listranges()
    rlist = [ rangelist.getrange(r) for r in rsnames]
    rlist.sort(key=lambda r: r.description)
    dw = reduce(lambda x,y: max(x,len(y.description)), rlist, 0)
    sw = reduce(lambda x,y: max(x,len(y.shortname)), rlist, 0)
    tf = "%-" + str(dw) + "s %-" + str(sw) + "s %10s %10s %10s"
    sys.stdout = ofil
    if had > 0: print "\n"
    had += 1
    print rf
    print "=" * len(rf)
    print tf % ('Description', 'Short', 'Low', 'High', 'Diff')
    print tf % ('=' * 11, '=' * 5, '===', '====', '====')
    fmt = "%-" + str(dw) + "s %-" + str(sw) + "s %#10.6g %#10.6g %#10.6g%s"
    for r in rlist:
        niu = ""
        if r.notused: niu = " (not in use)"
        print fmt % (r.description, r.shortname, r.lower, r.upper, r.upper-r.lower, niu)
