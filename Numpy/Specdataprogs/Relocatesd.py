#! /usr/bin/env python

import sys
import os
import os.path
import locale
import xml.etree.ElementTree as ET
import argparse
import miscutils
import xmlutil
import specdatactrl
import specinfo

parsearg = argparse.ArgumentParser(description='List or relocate obs file directory in specinfo files')
parsearg.add_argument('infofile', type=str, help='Input info file(s)', nargs='+')
parsearg.add_argument('--verbose', action='store_true', help='Say what is going on')
parsearg.add_argument('--list', action='store_true', help='List current directory only, no changes')
parsearg.add_argument('--newdir', type=str, help='New directory')
parsearg.add_argument('--force', action='store_true', help='Force change even if directory does not exist')

resargs = vars(parsearg.parse_args())

inffiles = resargs['infofile']
listonly = resargs['list']
verbose = resargs['verbose']
newdir = resargs['newdir']
force = resargs['force']

if listonly:
    if newdir is not None:
        print "New directory not appropriate for list option"
        sys.exit(10)  
    errors = 0
    for inff in inffiles:
        if not os.path.isfile(inff):
            inff = miscutils.replacesuffix(inff, specinfo.SUFFIX)
        try:
            sinf = specinfo.SpecInfo()
            sinf.loadfile(inff)
            clist = sinf.get_ctrlfile()
        except specinfo.SpecInfoError as e:
            print "Cannot read info file", inff, "Error:", e.args[0]
            errors += 1
            continue
        print inff, ": ",
        olddir = clist.dirname
        if olddir is None or len(olddir) == 0:
            print "No directory"
        elif os.path.isdir(olddir):
            print olddir
        else:
            print olddir, " (does not exist)"
    if errors > 0:
        sys.exit(1)
    sys.exit(0)

if len(inffiles) > 1:
    print "Can only relocate in one file at a time"
    sys.exit(11)

if newdir is None:
    print "No new directory specified"
    sys.exit(112)

# Insist on absolute path

newdir = os.path.abspath(newdir)

if not force and not os.path.isdir(newdir):
    print newdir, "Is not a directory"
    sys.exit(13)

inff = inffiles[0]

if not os.path.isfile(inff):
    inff = miscutils.replacesuffix(inff, specinfo.SUFFIX)
try:
    sinf = specinfo.SpecInfo()
    sinf.loadfile(inff)
    clist = sinf.get_ctrlfile()
    if verbose: print inff, "loaded OK"
except specinfo.SpecInfoError as e:
    print "Cannot read info file", inff
    print "Error was:"
    print e.args[0]
    sys.exit(14)

if verbose:
    olddir = clist.dirname
    if olddir is None or len(olddir) == 0:
        olddir = "(None)"
    print "Changing directory", olddir, "to", newdir

clist.dirname = newdir
if clist.obsfname is not None and len(clist.obsfname) != 0:
    clist.obsfname = os.path.join(newdir, os.path.basename(clist.obsfname))

try:
    sinf.set_ctrlfile(clist)
    sinf.savefile()
    if verbose: print sinf, "Saved OK"
    sys.exit(0)
except specinfo.SpecInfoError as e:
    print "Cannot save info file", inff
    print "Error was:"
    print e.args[0]
    sys.exit(15)

