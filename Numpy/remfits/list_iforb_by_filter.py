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


parsearg = argparse.ArgumentParser(description='List number of flat or bias files by filter',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--type', type=str, required=True, choices=['f', 'b'], help='Required type f or b')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
parsearg.add_argument('--latex', action='store_true', help='Latex output')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
dtype = resargs['type']
latex = resargs['latex']
gain = resargs['gain']

mydb, dbcurs = remdefaults.opendb()

sel = ' WHERE '
if dtype == 'f':
    sel += "typ='flat'"
else:
    sel += "typ='bias'"

if gain is not None:
    sel += " AND ABS(gain-%.3g) < %.3g" % (gain, gain * 1e-3)

dbcurs.execute("SELECT filter,COUNT(*) FROM iforbinf" + sel + " GROUP BY filter")

results = dict()

total = 0
for row in dbcurs.fetchall():
    filter, count = row
    results[filter] = count
    total += count

if latex:
    locale.setlocale(locale.LC_ALL, "")
    for filter in 'girz':
        try:
            print(filter, thou(results[filter]), sep=' & ', end=' \\\\\n')
        except KeyError:
            pass
    print("\\hline")
    print('Total', thou(total), sep=' & ', end=' \\\\\n')
else:
    for filter in 'girz':
        try:
            print("%s\t%7d" % (filter, results[filter]))
        except KeyError:
            pass
    print("Total\t%7d" % total)
