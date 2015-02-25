#! /usr/bin/env python

import sys
import os
import os.path
import locale
import xml.etree.ElementTree as ET
import miscutils
import xmlutil
import specdatactrl

SPC_DOC_NAME = "SPCCTRL"
SPC_DOC_ROOT = "spcctrl"

if len(sys.argv) != 3:
    sys.stdout = sys.stderr
    print "Usage: %s ctrl-file newdir" % sys.argv[0]
    sys.exit(10)

cfilename = sys.argv[1]
if not miscutils.hassuffix(cfilename, '.sac'):
    cfilename += '.sac'

newdir = sys.argv[2]

if not os.path.isfile(cfilename):
    sys.stdout = sys.stderr
    print "Cannot find control file", cfilename
    sys.exit(11)

if not os.path.isdir(newdir):
    sys.stdout = sys.stderr;
    print "No such directory", newdir
    sys.exit(12)

try:
    doc, root = xmlutil.load_file(cfilename, SPC_DOC_ROOT)
    cf = specdatactrl.SpecDataList(cfilename)
    cnode = xmlutil.find_child(root, "cfile")
    cf.load(cnode)
except xmlutil.XMLError as e:
    sys.stdout = sys.stderr
    print "Load control file XML error", e.args[0]
    sys.exit(13)
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Load control file data error", e.args[0]
    sys.exit(14)

if len(cf.dirname) == 0:
    sys.stdout = sys.stderr
    print "Cfile has no existing directory"
    sys.exit(14)

if len(cf.obsfname) == 0:
    sys.stdout = sys.stderr
    print "Cfile has no existing obs file name"
    sys.exit(15)

cf.dirname = newdir
cf.obsfname = os.path.join(newdir, os.path.basename(cf.obsfname))

try:
    doc, root = xmlutil.init_save(SPC_DOC_NAME, SPC_DOC_ROOT)
    cf.save(doc, root, "cfile")
    xmlutil.complete_save(cfilename, doc)
except xmlutil.XMLError as e:
    sys.stdout = sys.stderr
    print "Save control file XML error", e.args[0]
    sys.exit(16)



