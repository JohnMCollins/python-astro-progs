#! /usr/bin/env python

import sys
import os
import os.path
import locale
import xml.etree.ElementTree as ET
import miscutils
import xmlutil
import specdatactrl

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
    cf = specdatactrl.Load_specctrl(cfilename)
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
    specdatactrl.Save_specctrl(cfilename, cf)
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Save control file error", e.args[0]
    sys.exit(16)



