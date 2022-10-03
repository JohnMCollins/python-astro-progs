#!  /usr/bin/env python3

"""Rename Gaia objects to shortest alias"""

import argparse
import sys
import remdefaults

parsearg = argparse.ArgumentParser(description='Rename GAIA objects from Gaia xxxxxxxxxx to shortest alias where possible', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

mydb, mycurs = remdefaults.opendb()

namelookup = dict()

mycurs.execute("SELECT objname,alias FROM objalias WHERE objname REGEXP 'Gaia' AND NOT alias REGEXP 'Gaia' AND sbok!=0")
posslist = mycurs.fetchall()

for oname, als in posslist:

    try:
        s = namelookup[oname]
    except KeyError:
        s = namelookup[oname] = set()
    s.add(oname)
    s.add(als)

for original_name, als in namelookup.items():
    names = sorted(list(als))
    nls = [len(n) for n in names]
    minlen = min(nls)
    if minlen >= len(original_name):
        print("Not bothering with", original_name, "already shortest at", minlen, file=sys.stderr)
        continue
    w = nls.index(minlen)
    new_name = names[w]
    print("Selecting for", original_name, "changing to", new_name, "length", minlen, "out of\n\t" + "\n\t".join(names), file=sys.stderr)
    mycurs.execute("SELECT dispname FROM objdata WHERE objname=%s", original_name)
    dnr = mycurs.fetchone()
    if dnr is None:
        print("Failed to find", original_name, "in objdata", file=sys.stderr)
        sys.exit(100)
    dnr = dnr[0]
    if dnr == original_name:
        print("Need to update dispname for", original_name, "to", new_name, file=sys.stderr)
        mycurs.execute("UPDATE objdata SET objname=%s,dispname=%s WHERE objname=%s", (new_name, new_name, original_name))
    else:
        print("Keeping original dispname of", dnr, "for", original_name, file=sys.stderr)
        mycurs.execute("UPDATE objdata SET objname=%s WHERE objname=%s", (new_name, original_name))
    na1 = mycurs.execute("UPDATE objalias SET objname=%s WHERE objname=%s", (new_name, original_name))
    na2 = mycurs.execute("UPDATE objalias SET alias=%s WHERE alias=%s", (original_name, new_name))
    if na2 != 1:
        print("Expecting 1 update from final alias", file=sys.stderr)
        sys.exit(101)
    print(na1+na2, "aliases updated", file=sys.stderr)

mydb.commit()