#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:58+00:00
# @Email:  jmc@toad.me.uk
# @Filename: listobjects.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:43+00:00

import dbops
import remdefaults
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


parsearg = argparse.ArgumentParser(description='List number by filter',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to limit to')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
parsearg.add_argument('--latex', action='store_true', help='Latex output')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
objlist = resargs['objects']
latex = resargs['latex']
gain = resargs['gain']

mydb, dbcurs = remdefaults.opendb()

sel = ''
if objlist is not None:
    qobj = [ "object='" + o + "'" for o in objlist]
    sel = "(" + " OR ".join(qobj) + ")"
if gain is not None:
    if len(sel) != 0: sel += " AND "
    sel += "ABS(gain-%.3g) < %.3g" % (gain, gain * 1e-3)
if len(sel) != 0:
    sel = " WHERE " + sel

dbcurs.execute("SELECT filter,COUNT(*) FROM obsinf" + sel + " GROUP BY filter")

results = dict()

total = 0
for row in dbcurs.fetchall():
    filter, count = row
    results[filter] = count
    total += count

if latex:
    locale.setlocale(locale.LC_ALL, "")
    for filter in 'girzHJK':
        try:
            print(filter, thou(results[filter]), sep=' & ', end=' \\\\\n')
        except KeyError:
            pass
    try:
        print('GRISM', thou(results['GRI']), sep=' & ', end=' \\\\\n')
    except KeyError:
        pass
    print("\\hline")
    print('Total', thou(total), sep=' & ', end=' \\\\\n')

else:
    for filter in 'girzHJK':
        try:
            print("%s\t%7d" % (filter, results[filter]))
        except KeyError:
            pass
    try:
        print("%s\t%7d" % ('GRISM', results['GRI']))
    except KeyError:
        pass

    print("Total\t%7d" % total)
