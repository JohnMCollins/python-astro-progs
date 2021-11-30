#!  /usr/bin/env python3

"""Process CSV result from GAIA DR3"""

import argparse
import sys
import csv
import math
from operator import attrgetter
import astropy.units as u
import remdefaults
import objdata
import miscutils
import vicinity
import numpy as np
import parsedms

Parallax_conv = u.parallax()


class csvobj:
    """Remember object extracted from CSV"""

    def __init__(self, csvrow):
        self.id = csvrow['source_id']
        self.radeg = float(csvrow['ra'])
        self.decdeg = float(csvrow['dec'])
        try:
            self.pmra = float(csvrow['pmra'])
        except ValueError:
            self.pmra = None
        try:
            self.pmdec = float(csvrow['pmdec'])
        except ValueError:
            self.pmdec = None
#         try:
#             self.ruwe = float(csvrow['ruwe'])
#         except ValueError:
#             self.ruwe = 1e6
        self.gmag = float(csvrow['phot_g_mean_mag'])
        try:
            self.rv = float(csvrow['dr2_radial_velocity'])
        except ValueError:
            self.rv = None
        try:
            self.distance = (float(csvrow['parallax']) * u.arcsec).to(u.lightyear, equivalencies=Parallax_conv).value
            if math.isnan(self.distance):
                self.distance = None
        except ValueError:
            self.distance = None

    def gen_insert(self):
        """Generate insert statement - need dbase for escapes"""

        global mydb, vic

        fields = []
        values = []

        fields.append("objname")
        escname = mydb.escape("Gaia DR3 " + self.id)
        values.append(escname)
        fields.append("dispname")
        values.append(escname)
        fields.append("objtype")
        values.append(mydb.escape('Star'))
        fields.append('vicinity')
        values.append(mydb.escape(vic))

        fields.append("radeg")
        values.append("{:.8e}".format(self.radeg))
        fields.append("decdeg")
        values.append("{:.8e}".format(self.decdeg))

        if self.rv is not None:
            fields.append('rv')
            values.append("{:.8e}".format(self.rv))

        if self.pmra is not None:
            fields.append('rapm')
            values.append("{:.8e}".format(self.pmra))
        if self.pmdec is not None:
            fields.append('decpm')
            values.append("{:.8e}".format(self.pmdec))

        if self.distance is not None:
            fields.append("dist")
            values.append("{:.8e}".format(self.distance))

        fields.append("gmag")
        values.append("{:.8e}".format(self.gmag))
        return "INSERT INTO objdata (" + ",".join(fields) + ") VALUES (" + ",".join(values) + ")"


parsearg = argparse.ArgumentParser(description='Process output from GAIA DR3 to identify objects', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('csvfile', nargs=1, type=str, help='CSV file to process')
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--diffmin', type=str, default='1s', help='Difference between RA and DEC to decide whether they are same in dms')
# parsearg.add_argument('--maxruew', type=float, default=3.0, help='Maximum acceptable RUWE')
parsearg.add_argument('--sepmin', type=str, default='2s', help='Sparation minimum in DMS to avoid close objects')
parsearg.add_argument('--update', action='store_true', help='Update database with findings"')

resargs = vars(parsearg.parse_args())
csvfile = miscutils.addsuffix(resargs['csvfile'][0], 'csv')
remdefaults.getargs(resargs)
difference = resargs['diffmin']
# maxruew = resargs['maxruew']
minsep = resargs['sepmin']
update = resargs['update']

try:
    difference = parsedms.parsedms(difference)
except ValueError:
    print("Could not understand diffmin", difference, file=sys.stderr)
    sys.exit(10)
try:
    minsep = parsedms.parsedms(minsep)
except ValueError:
    print("Could not understand sepmen", minsep, file=sys.stderr)
    sys.exit(11)

try:
    inf = open(csvfile, 'rt')
except OSError as e:
    print("Could not open", csvfile, e.args[1], file=sys.stderr)
    sys.exit(12)

reader = csv.DictReader(inf)

mydb, dbcurs = remdefaults.opendb()

ilist = []
# nonruwe = 0

for row in reader:
    try:
        newitem = csvobj(row)
    except ValueError:
        print("Input error in", csvfile, "line", reader.line_num, "expected fields missing", file=sys.stderr)
        continue
#     if newitem.ruwe <= maxruew:
    ilist.append(newitem)
#     else:
#         nonruwe += 1

if len(ilist) == 0:
    print("No acceptable lines found", file=sys.stderr)
    sys.exit(51)

# if nonruwe > 0:
#     print(nonruwe, "lines omitted as excess RUWE")

ilist = sorted(ilist, key=attrgetter('radeg', 'decdeg'))

vic = vicinity.get_vicinity(dbcurs, ilist[0].radeg, ilist[0].decdeg)
if vic is None:
    print("Cannot find vicinity of object at", ilist[0].radeg, ilist[0].decdeg, file=sys.stderr)
    sys.exit(50)
print("Vicinity of", vic)

coord_pos = [complex(a.radeg, a.decdeg) for a in ilist]

diffs = np.append(np.abs(np.diff(coord_pos)), 1e50)
rdiffs = np.roll(diffs, 1)

distinct_list = [a for a, d, rd in zip(ilist, diffs, rdiffs) if d >= minsep and rd >= minsep]

print("Before pruning for too adjacent", len(ilist), "after", len(distinct_list))

diffsq = difference ** 2
nomatches = dupmatches = foundmatch = already = 0
newentries = newaliases = updrv = upddist = 0

for item in distinct_list:
    pmra = item.pmra
    pmdec = item.pmdec
    if pmra is None:
        pmra = 0
    if pmdec is None:
        pmdec = 0
 #   print("{id:<16s}{ra:9.3f}{dec:9.3f}{pmra:9.3f}{pmdec:9.3f} {mag:6.3f}".format(id=item.id, ra=item.radeg, dec=item.decdeg, pmra=pmra, pmdec=pmdec, mag=item.gmag), item.rv, sep='\t')
    dbcurs.execute("SELECT objname,radeg,decdeg,dist,rv FROM objdata WHERE POWER(radeg-{radeg:.8e},2)+POWER(decdeg-{decdeg:.8e},2)<={diff:.8e}".format(radeg=item.radeg, decdeg=item.decdeg, diff=diffsq))
    inreg = dbcurs.fetchall()
    if len(inreg) == 0:
        nomatches += 1
        if update:
            dbcurs.execute(item.gen_insert())
            newentries += 1
        continue
    if len(inreg) > 1:
        possnames = sorted([m[0] for m in inreg])
        print("\t***Near to", len(inreg), "objects", ", ".join(possnames))
        dupmatches += 1
        continue
    dbobjname, dbra, dbdec, dbdist, dbrv = inreg[0]
    dbobj = objdata.ObjData(dbobjname)
    alist = dbobj.list_aliases(dbcurs)
    anames = [a.aliasname for a in alist]
    anames.append(dbobj.objname)
    anames.sort()
    matched = False
    for a in anames:
        try:
            if a[0:7] == 'Gaia DR' and item.id in a:
                matched = True
                break
        except (IndexError, ValueError):
            continue
    if matched:
        print("\t***", item.id, "Previously matched to GAIA release", ", ".join(anames))
        already += 1
    else:
        print("{id:<16s}{ra:9.3f}{dec:9.3f}{pmra:9.3f}{pmdec:9.3f} {mag:6.3f}".format(id=item.id, ra=item.radeg, dec=item.decdeg, pmra=pmra, pmdec=pmdec, mag=item.gmag), item.rv, sep='\t')
        print("\t***Found object", item.id, "before with names", ", ".join(anames))
        if update:
            dbcurs.execute("INSERT INTO objalias (objname,alias,source,sbok) VALUES (%s,%s,%s,0)", (dbobjname, 'Gaid DR3 ' + item.id, "Gaia DR3"))
            newaliases += 1
    foundmatch += 1
    if update:
        if dbdist is None and item.distance is not None:
            dbcurs.execute("UPDATE objdata SET dist={:.8e}".format(item.distance) + " WHERE objname=%s", dbobjname)
            upddist += 1
        if dbrv is None and item.rv is not None:
            dbcurs.execute("UPDATE objdata SET rv={:.8e}".format(item.rv) + " WHERE objname=%s", dbobjname)
            updrv += 1

print(nomatches, "not matched", dupmatches, "duplicate", foundmatch, "found match", already, "already as GAIA")
if update and (nomatches > 0 or newentries > 0 or newaliases > 0 or upddist > 0 or updrv > 0):
    print(newentries, "new entries", newaliases, "new aliases", upddist, "update dists", updrv, "update rv")
    mydb.commit()
