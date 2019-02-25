#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:58+00:00
# @Email:  jmc@toad.me.uk
# @Filename: listobjects.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:43+00:00

import dbops
import datetime
import argparse
from operator import attrgetter
import dbobjinfo
import numpy as np
import locale

def thou(n):
    """Print n with thousands separator"""
    return locale.format_string("%d", n, grouping=True)

class obstot(object):
	"""Details of result"""

	def __init__(self, objname, n):
		self.objname = objname
		self.count = int(n)
		self.fromdate = None
		self.todate = None
		self.isundef = None

parsearg = argparse.ArgumentParser(description='List all objects with first and last date',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default='remfits', help='Database to use')
parsearg.add_argument('--order', type=str, help='Order - (n)umber obs (e)arlist (l)atest')
parsearg.add_argument('--cutoff', type=float, help='Summarise for %arg less than this')
parsearg.add_argument('--latex', action='store_true', help='Latex output')

resargs = vars(parsearg.parse_args())
dbname = resargs['database']
order = resargs['order']
cutoff = resargs['cutoff']
latex = resargs['latex']

mydb = dbops.opendb(dbname)

dbcurs = mydb.cursor()

dbcurs.execute("SELECT object,COUNT(*) AS number FROM obs GROUP BY object")

results = []

for row in dbcurs.fetchall():
	obj, num = row
	results.append(obstot(obj, num))

for k in results:
	obj = k.objname
	dbcurs.execute("SELECT date_obs FROM obs WHERE object='" + obj + "' ORDER BY date_obs LIMIT 1")
	row = dbcurs.fetchall()
	k.fromdate = row[0][0]
	dbcurs.execute("SELECT date_obs FROM obs WHERE object='" + obj + "' ORDER BY date_obs DESC LIMIT 1")
	row = dbcurs.fetchall()
	k.todate = row[0][0]
	try:
		dbobjinfo.get_targetname(dbcurs, k.objname)
		k.isundef = False
	except dbobjinfo.ObjDataError:
		k.isundef = True

nonproxr = [r for r in results if r.objname[0:4] != 'Prox']
proxr = [r for r in results if r.objname[0:4] == 'Prox']

prox = obstot('Proxima', np.sum([r.count for r in proxr]))
prox.fromdate = min([r.fromdate for r in proxr])
prox.todate = max([r.todate for r in proxr])
prox.isundef = False

results = nonproxr
results.append(prox)

total = np.sum([r.count for r in results])
summ = None

if cutoff is not None:
	cutperc = cutoff * total / 100.0
	keeping = [r for r in results if r.count >= cutperc]
	summing = [r for r in results if r.count < cutperc]
	if len(summing) != 0:
		summ = obstot('Others', np.sum([r.count for r in summing]))
		summ.fromdate = min([r.fromdate for r in summing])
		summ.todate = max([r.todate for r in summing])
		summ.isundef = False
		results = keeping

if order is not None and len(order) != 0:
	f = order[0].lower()
	if f == 'n':
		results.sort(key=attrgetter('count'),reverse=True)
	elif f == 'e':
		results.sort(key=attrgetter('fromdate'))
	elif f == 'l':
		results.sort(key=attrgetter('todate'),reverse=True)
		
if summ is not None:
	results.append(summ)

if latex:
	locale.setlocale(locale.LC_ALL, "")
	for k in results:
		n = k.objname
		if n == "Proxima":
			n = "\\prox"
		elif n == "BarnardStar":
			n = "\\bstar"
		print(n, thou(k.count), "%.2f" % (100.0 * k.count / total), sep=' & ', end=' \\\\\n')
	print("\\hline")
	print("Total", thou(total), sep=' & ', end=' \\\\\n')
else:
	mind = min([r.fromdate for r in results])
	maxd = max([r.todate for r in results])
	for k in results:
		if k.isundef:
			print('*', end='')
		else:
			print(' ', end='')
		print("%-14s\t%7d%8.2f\t" % (k.objname, k.count, 100.0 * k.count / total) + k.fromdate.strftime("%d/%m/%Y ") + k.todate.strftime("%d/%m/%Y"))

	print(" Total          %7d\t\t" % total + mind.strftime("%d/%m/%Y ") + maxd.strftime("%d/%m/%Y"))
