#! /usr/bin/python

import os
import os.path
import sys
import string
import glob
import argparse
import re
import cPickle

import specarray
import xmlutil

def hassuffix(st, suff):
    """Return whether string (usually file name) has given suffix"""
    try:
        if st[st.rindex(suff):] == suff: return True
    except ValueError:
        pass
    return False

parsearg = argparse.ArgumentParser(description='Rescale Y in spectal data file')
parsearg.add_argument('--srcfile', type=str, help='Source File')
parsearg.add_argument('--destfile', type=str, help='Destination file')
parsearg.add_argument('--mult', type=float, help='Factor to multiply by', default=1.0)
parsearg.add_argument('--divide', type=float, help='Factor to divide by', default=1.0)
parsearg.add_argument('--reset', action="store_true", help='Kill any existing scaling')

res = vars(parsearg.parse_args())
srcfile = res['srcfile']
destfile = res['destfile']

if srcfile is None or len(srcfile) == 0:
    print "No source file specified"
    sys.exit(20)

if destfile is None or len(destfile) == 0:
    destfile = srcfile

# Load up srcfile, get format from suffix

xmlformat = hassuffix(srcfile, '.xml')

if not xmlformat and not hassuffix(srcfile, '.pick'):
    print "Don't know the format of", srcfile
    sys.exit(19)

if xmlformat:
    try:
        doc, root = xmlutil.load_file(srcfile, "specdata")
    except xmlutil.XMLError as e:
        print e.args[0]
        sys.exit(21)
    
    Sl = None

    child = root.firstChild()
    while not child.isNull():
        if child.toElement().tagName() == "speclist":
            Sl = specarray.Specarraylist()
            Sl.load(child)
        child = child.nextSibling()

    if Sl is None:
        print "Couldn't find an obs list in file"
        sys.exit(22)
else:
    try:
        inf = open(srcfile)
        Sl = cPickle.load(inf)
    except IOError as e:
        print e.args[0]
        sys.exit(21)
    except EOFError:
        print "Nothing in", srcfile
    except cPickle.UnpicklingError as e:
        print e.args[0]
        sys.exit(21)

Existing_scale = Sl.yscale
Specified_scale = res['mult'] / res['divide']

if res['reset']:
    New_scale = Specified_scale
    Scaling_by = Specified_scale / Existing_scale
else:
    New_scale = Specified_scale * Existing_scale
    Scaling_by = Specified_scale

print "Existing scale = %.6f, rescale by %.6f to %.6f" % (Existing_scale, Scaling_by, New_scale)

if abs(New_scale - 1.0) < 1e-6:
    print "No rescaling, nothing to do"
    sys.exit(0)

# Apply scaling factor to Y

for obs in Sl.obslist():
    for datum in obs.datalist:
        datum.yvalue *= Scaling_by
Sl.yscale = New_scale

# If the output file has a recognised format, write in that format
# Otherwise copy the input file format sticking the appropriate suffix on

if hassuffix(destfile, '.xml'):
    outxml = True
elif hassuffix(destfile, '.pick'):
    outxml = False
elif xmlformat:
    destfile += '.xml'
    outxml = True
else:
    destfile += '.pick'
    outxml = False

if outxml:
    # Generate XML file

    (doc, root) = xmlutil.init_save("SPECDATA", "specdata")
    Sl.save(doc, root, "speclist")

    try:
        xmlutil.complete_save(destfile, doc)
    except xmlutil.XMLerror as e:
        print e.args[0]
        sys.exit(200)
else:
    try:
        outf = open(destfile, 'w')
        cPickle.dump(Sl, outf)
    except IOError as e:
        print e.args[0]
        sys.exit(200)


