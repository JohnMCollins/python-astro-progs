#!  /usr/bin/env python

# Update aliases

import numpy as np
import os.path
import argparse
import xmlutil
import objinfo
import sys

parsearg = argparse.ArgumentParser(description='Create/delete alias names for objectse', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('names', nargs='+', type=str, help='Main name followed by aliases')
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--delete', action='store_true', help='Delete aliases main name not needed')
parsearg.add_argument('--alldelete', action='store_true', help='Delete all aliases for main name')

resargs = vars(parsearg.parse_args())

objnames = resargs['names']
libfile = os.path.expanduser(resargs['libfile'])
delete = resargs['delete']
alldelete = resargs['alldelete']

objinf = objinfo.ObjInfo()
try:
    objinf.loadfile(libfile)
except objinfo.ObjInfoError as e:
    if e.warningonly:
        print "(Warning) file does not exist:", libfile >>sys.stderr
    else:
        print "Error loading file", e.args[0] >> sys.stderr
        sys.exit(30)

errors = 0
if alldelete:
    for name in objnames:
        try:
            alist = objinf.get_aliases(name)
        except objinfo.ObjInfoError as e:
            print e.args[0] >>sys.stderr
            errors += 1
            continue
        objinf.del_aliases(*alist)
elif delete:
    try:
        objinf.del_aliases(*objnames)
    except objinfo.ObjInfoError as e:
        print e.args[0] >>sys.stderr
        errors += 1
else:
    mainname = objnames.pop(0)
    if len(objnames) == 0:
        print "Expecting aliase names for", mainname >>sys.stderr
        errors += 1
    else:
        try:
            objinf.add_aliases(mainname, *objnames)
        except objinfo.ObjInfoError as e:
            print e.args[0] >>sys.stderr
            errors += 1        

if errors > 0:
    print "Aborting due to errors" >>sys.stderr
    sys.exit(20)

objinf.savefile(libfile)
    