#!  /usr/bin/env python3

"""List ADU calculations"""

import argparse
import sys
import parsetime
import objdata
import remdefaults

parsearg = argparse.ArgumentParser(description='List calculated ADUs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('target', nargs=1, type=str, help='Object to list ADUs for')
parsearg.add_argument('--filter', type=str, required=True, help='Filter name to list for')
parsearg.add_argument('--outfile', type=str, help='Output file if not stdout')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsetime.parseargs_daterange(parsearg)

resargs = vars(parsearg.parse_args())
targname = resargs['target']
filtname = resargs['filter']
outfile = resargs['outfile']
remdefaults.getargs(resargs)

dbfieldsel = ["filter='" + filtname + "'"]
parsetime.getargs_daterange(resargs, dbfieldsel)

mydb, dbcurs = remdefaults.opendb()

targobj = objdata.ObjData()
try:
    targobj.get(dbcurs, name=targname)
except objdata.ObjDataError as e:
    print("Cannot find", targname, "error was", e.args[0], file=sys.stderr)
    sys.exit(10)

dbfieldsel.append("objind={:d}".format(targobj.objind))
dbcurs.execute("SELECT bjdobs,aducount,aduerr FROM obsinf INNER JOIN aducalc WHERE aducalc.obsind=obsinf.obsind AND " +
               " AND ".join(dbfieldsel) + " ORDER BY bjdobs")
res = dbcurs.fetchall()
if len(res) == 0:
    print("No results found", file=sys.stderr)
    sys.exit(1)

outf = sys.stdout
if  outfile is not None:
    try:
        outf = open(outfile, 'wt')
    except OSError as e:
        print("Unable to write to", outfile, "error was", e.args[1], file=sys.stderr)
        sys.exit(20)
for dat, aducount, aduerr in res:
    print("{:16.6f} {:16.3f} {:13.3f}".format(dat, aducount, aduerr), file=outf)
