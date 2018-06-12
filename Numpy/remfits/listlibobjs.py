#!  /usr/bin/env python

# Update aliases

import numpy as np
import os.path
import argparse
import xmlutil
import objinfo
import sys
import string

parsearg = argparse.ArgumentParser(description='List objects from record', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')

resargs = vars(parsearg.parse_args())

libfile = os.path.expanduser(resargs['libfile'])

objinf = objinfo.ObjInfo()
try:
    objinf.loadfile(libfile)
except objinfo.ObjInfoError as e:
    if e.warningonly:
        print  >>sys.stderr, "(Warning) file does not exist:", libfile
    else:
        print >>sys.stderr,  "Error loading file", e.args[0]
        sys.exit(30)

ol = objinf.list_objects()
al = [string.join(x.list_alias_names(), ',') for x in ol]

nlength = reduce(max, [len(x.objname) for x in ol])
alength = reduce(max, [len(a) for a in al])

npfmt = "%%-%ds" % nlength + " %%-%ds" % alength
nfmt = npfmt +  " %7.3f %7.3f %s"

print npfmt % ("Name", "Aliases"), "  RA      Decl  Dist (pc)"
for ap, obj in zip(al, ol):
    ra = obj.get_ra()
    dec = obj.get_dec()
    if obj.dist is None:
       dist = "Unknown"
    else:
       dist = "%#.3g" % obj.dist
    print nfmt % (obj.objname, ap, ra, dec, dist)
    
    