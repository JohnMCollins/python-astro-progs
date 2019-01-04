#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:58+00:00
# @Email:  jmc@toad.me.uk
# @Filename: objaliases.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:27:10+00:00

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
parsearg.add_argument('--source', type=str, default='By hand', help='Source of alias names')

resargs = vars(parsearg.parse_args())

objnames = resargs['names']
libfile = os.path.expanduser(resargs['libfile'])
delete = resargs['delete']
alldelete = resargs['alldelete']
source = resargs['source']

objinf = objinfo.ObjInfo()
try:
    objinf.loadfile(libfile)
except objinfo.ObjInfoError as e:
    if e.warningonly:
        print("(Warning) file does not exist:", libfile, file=sys.stderr)
    else:
        print("Error loading file", e.args[0], file=sys.stderr)
        sys.exit(30)

errors = 0
if alldelete:
    for name in objnames:
        try:
            alist = objinf.get_aliases(name)
        except objinfo.ObjInfoError as e:
            print(e.args[0], file=sys.stderr)
            errors += 1
            continue
        objinf.del_aliases(*alist)
elif delete:
    try:
        objinf.del_aliases(*objnames)
    except objinfo.ObjInfoError as e:
        print(e.args[0] >>sys.stderr)
        errors += 1
else:
    mainname = objnames.pop(0)
    if len(objnames) == 0:
        print("Expecting aliase names for", mainname, file=sys.stderr)
        errors += 1
    else:
        try:
            objinf.add_aliases(mainname, source, *objnames)
        except objinfo.ObjInfoError as e:
            print(e.args[0], file=sys.stderr)
            errors += 1

if errors > 0:
    print("Aborting due to errors", file=sys.stderr)
    sys.exit(20)

objinf.savefile(libfile)
