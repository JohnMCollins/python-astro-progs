#! /usr/bin/env python

# Display ratio calculation vs EW

import argparse
import os.path
import sys
import string
import datarange
import specinfo
import miscutils

RANGESUFF = 'spcr'      # Old range file

parsearg = argparse.ArgumentParser(description='List ranges in spectrum data input file or old range file')
parsearg.add_argument('infofile', help="XML file of ranges or spec info", nargs='+', type=str)
parsearg.add_argument('--outfile', help="Output file if not STDOUT", type=str)
parsearg.add_argument('--latex', help='Latex output format', action='store_true')

res = vars(parsearg.parse_args())
rfs = res['infofile']
outf = res['outfile']
latex = res['latex']

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
sys.stdout = ofil

for rf in rfs:
    if miscutils.hassuffix(rf, RANGESUFF):
        try:
            rangelist = datarange.load_ranges(rf)
        except datarange.DataRangeError as e:
            sys.stdout = sys.stderr
            print "Range load error on file", rf
            print "Errow was:"
            print e.args[0]
            errors += 1
            sys.stdout = ofil
            continue
    else:
        if not os.path.isfile(rf):
            rf = miscutils.replacesuffix(rf, specinfo.SUFFIX)
        try:
            sinf = specinfo.SpecInfo()
            sinf.loadfile(rf)
            rangelist = sinf.get_rangelist()
        except specinfo.SpecInfoError as e:
            sys.stdout = sys.stderr
            print "Range load error on file", rf
            print "Errow was:"
            print e.args[0]
            errors += 1
            sys.stdout = ofil
            continue
    rsnames = rangelist.listranges()
    rlist = [ rangelist.getrange(r) for r in rsnames]
    rlist.sort(key=lambda r: r.description)
    if latex:
        print "\\begin{center}"
        print "\\begin{tabular}{ |l r r r| }"
        print "\\hline"
        print "\\multicolumn{4}{|c|}{%s}" % rf, "\\\\\\hline"
        print "Description & Low & High & Difference \\\\\\hline"
        for r in rlist:
            print "%s & %#.6g & %#.6g & %#.6g \\\\" % (r.description, r.lower, r.upper, r.upper-r.lower)
        print "\\hline"
        print "\\end{tabular}"
        print "\\end{center}"
    else:
        dw = reduce(lambda x,y: max(x,len(y.description)), rlist, 0)
        sw = reduce(lambda x,y: max(x,len(y.shortname)), rlist, 0)
        tf = "%-" + str(dw) + "s %-" + str(sw) + "s %10s %10s %10s"
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
