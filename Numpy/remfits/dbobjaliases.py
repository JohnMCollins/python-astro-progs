#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-10-12T15:05:17+01:00
# @Email:  jmc@toad.me.uk
# @Filename: dbobjaliases.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:03:06+00:00

# Update aliases

import argparse
import sys
import dbops
import remdefaults

parsearg = argparse.ArgumentParser(description='Create/delete alias names for objects', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('names', nargs='*', type=str, help='Main name followed by aliases')
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--delete', action='store_true', help='Delete aliases main name not needed')
parsearg.add_argument('--alldelete', action='store_true', help='Delete all aliases for main name')
parsearg.add_argument('--source', type=str, default='By hand', help='Source of alias names')
parsearg.add_argument('--verbose', action='store_true', help='Give info about what is happening')
parsearg.add_argument('--list', action='store_true', help='Just list existing aliases')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
objnames = resargs['names']
delete = resargs['delete']
alldelete = resargs['alldelete']
source = resargs['source']
verbose = resargs['verbose']
listem = resargs['list']

mydb, dbcurs = remdefaults.opendb()

if listem:
    dbcurs.execute("SELECT objname,alias,source FROM objalias ORDER BY objname,alias,source")
    stuff = dbcurs.fetchall()
    tabs = []
    nsize = 0
    asize = 0
    for row in stuff:
        name, alias, source = row
        nsize = max(nsize, len(name) + 1)
        asize = max(asize, len(alias) + 1)
        tabs.append(row)
    lastname = ""
    for row in tabs:
        name, alias, source = row
        if name == lastname:
            print(" " * nsize, end=' ')
        else:
            print(name + " " * (nsize - len(name)), end=' ')
            lastname = name
        print(alias + " " * (asize - len(alias)), end=' ')
        print(source)
    sys.exit(0)

if alldelete:
    for name in objnames:
        ndone = dbcurs.execute("DELETE FROM objalias WHERE objname=" + mydb.escape(name))
        if verbose:
            print("Deleted", ndone, "alises from", name, file=sys.stderr)
    mydb.commit()
    sys.exit(0)

if delete:
    for name in objnames:
        ndone = dbcurs.execute("DELETE FROM objalias WHERE alias=" + mydb.escape(name))
        if verbose:
            if ndone > 0:
                print("Deleted", name, "OK", file=sys.stderr)
            else:
                print("Did not delete", name, file=sys.stderr)
    mydb.commit()
    sys.exit(0)

if len(objnames) < 2:
    print("Expecting main name followed by alias names", file=sys.stderr)
    sys.exit(10)

mainname = objnames.pop(0)
qmainname = mydb.escape(mainname)
dbcurs.execute("SELECT COUNT(*) FROM objdata where objname=" + qmainname)
ndone = dbcurs.fetchall()
if ndone[0][0] == 0:
    print("Unknown object name", mainname, file=sys.stderr)
    sys.exit(1)

qsource = mydb.escape(source)

for name in objnames:
    qname = mydb.escape(name)
    ndone = dbcurs.execute("DELETE FROM objalias WHERE alias=" + qname)
    if verbose and ndone > 0:
        print("Deleted old alias", name, file=sys.stderr)
    ndone = dbcurs.execute("INSERT INTO objalias (objname,alias,source) VALUES (" + qmainname + "," + qname + "," + qsource + ")")
    if  verbose and ndone > 0:
        print("Added new alias", name, "for", mainname, file=sys.stderr)
mydb.commit()
