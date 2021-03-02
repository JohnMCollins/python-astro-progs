#!  /usr/bin/env python3

"""List objects with earliest and latest dates"""

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:58+00:00
# @Email:  jmc@toad.me.uk
# @Filename: listobjects.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:43+00:00

import argparse
from operator import attrgetter
import objdata
import numpy as np
import remdefaults


class obstot:
    """Details of result"""

    def __init__(self, objname, n):
        self.objname = objname
        self.count = int(n)
        self.fromdate = None
        self.todate = None
        self.isundef = None


parsearg = argparse.ArgumentParser(description='List all objects with first and last date',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--order', type=str, help='Order - (n)umber obs (e)arlist (l)atest')
parsearg.add_argument('--cutoff', type=float, help='Summarise for percent arg less than this')
parsearg.add_argument('--targets', action='store_true', help='Show for targets, summarise for rest')
parsearg.add_argument('--dither', type=int, nargs='*', default=[0], help='Dither ID to limit to')
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to limit to')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
parsearg.add_argument('--latex', action='store_true', help='Latex output')
parsearg.add_argument('--noundef', action='store_true', help='Do not summarise undefined')
parsearg.add_argument('--thousand', action='store_false', help='Separate thousands')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
order = resargs['order']
cutoff = resargs['cutoff']
targets = resargs['targets']
latex = resargs['latex']
gain = resargs["gain"]
dither = resargs['dither']
filters = resargs['filter']
noundef = resargs['noundef']
thousand = resargs['thousand']

mydb, dbcurs = remdefaults.opendb()

sel = ''
if gain is not None:
    sel = "ABS(gain-%.3g) < %.3g " % (gain, gain * 1e-3)

if filters is not None:
    qfilt = [ "filter='" + o + "'" for o in filters]
    if len(sel) != 0: sel += " AND "
    sel += "(" + " OR ".join(qfilt) + ")"

if len(dither) != 1 or dither[0] != -1:
    qdith = [ "dithID=" + str(d) for d in dither]
    if len(sel) != 0: sel += " AND "
    sel += "(" + " OR ".join(qdith) + ")"

if len(sel) != 0: sel = "WHERE " + sel
dbcurs.execute("SELECT object,COUNT(*) AS number FROM obsinf " + sel + "GROUP BY object")

results = []

for row in dbcurs.fetchall():
    obj, num = row
    results.append(obstot(obj, num))

for k in results:
    obj = k.objname
    dbcurs.execute("SELECT date_obs FROM obsinf WHERE object='" + obj + "' ORDER BY date_obs LIMIT 1")
    row = dbcurs.fetchall()
    k.fromdate = row[0][0]
    dbcurs.execute("SELECT date_obs FROM obsinf WHERE object='" + obj + "' ORDER BY date_obs DESC LIMIT 1")
    row = dbcurs.fetchall()
    k.todate = row[0][0]
    try:
        objdata.get_objname(dbcurs, k.objname)
        k.isundef = False
    except objdata.ObjDataError:
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
    if noundef:
        keeping = [r for r in results if r.count >= cutperc and not r.isundef]
        summing = [r for r in results if r.count < cutperc or r.isundef]
    else:
        keeping = [r for r in results if r.count >= cutperc]
        summing = [r for r in results if r.count < cutperc]
    if len(summing) != 0:
        summ = obstot('Others', np.sum([r.count for r in summing]))
        summ.fromdate = min([r.fromdate for r in summing])
        summ.todate = max([r.todate for r in summing])
        summ.isundef = False
    results = keeping
elif targets:
    intarg = []
    summing = []
    for r in results:
        if r.objname == 'Proxima' or r.objname == 'BarnardStar' or r.objname == 'Ross154':
            intarg.append(r)
        else:
            summing.append(r)
    if len(summing) != 0:
        summ = obstot('Others', np.sum([r.count for r in summing]))
        summ.fromdate = min([r.fromdate for r in summing])
        summ.todate = max([r.todate for r in summing])
        summ.isundef = False
    results = intarg

if order is not None and len(order) != 0:
    f = order[0].lower()
    if f == 'n':
        results.sort(key=attrgetter('count'), reverse=True)
    elif f == 'e':
        results.sort(key=attrgetter('fromdate'))
    elif f == 'l':
        results.sort(key=attrgetter('todate'), reverse=True)
    elif f == 'a':
        results.sort(key=attrgetter('objname'))

if summ is not None:
    results.append(summ)

if latex:
    if thousand:
        lfmt = "{nam:s} & {num:,d} & {pc:.2f} \\\\"
        tfmt = "Total & {num:,d} \\\\"
    else:
        lfmt = "{nam:s} & {num:d} & {pc:.2f} \\\\"
        tfmt = "Total & {num:d} \\\\"
    for k in results:
        nam = k.objname
        if nam == "Proxima":
            nam = "\\prox"
        elif nam == "BarnardStar":
            nam = "\\bstar"
        elif nam == 'Ross154':
            nam = "\\ross"
        print(lfmt.format(nam=nam, num=k.count, pc=100.0 * k.count / total))
    print("\\hline")
    print(tfmt.format(num=total))
else:
    mind = min([r.fromdate for r in results])
    maxd = max([r.todate for r in results])
    nsize = max(5, max([len(r.objname) for r in results]))
    if thousand:
        tsize = len("{:,d}".format(total))
        lfmt = "{nam:<{wid}s} {num:{tsize},d}{pc:8.2f} {sd:%d/%m/%Y} {ed:%d/%m/%Y}"
        tfmt = " {nam:<{wid}s} {num:{tsize},d}{sp:8s} {sd:%d/%m/%Y} {ed:%d/%m/%Y}"
    else:
        tsize = len("{:d}".format(total))
        lfmt = "{nam:<{wid}s} {num:{tsize}d}{pc:8.2f} {sd:%d/%m/%Y} {ed:%d/%m/%Y}"
        tfmt = " {nam:<{wid}s} {num:{tsize}d}{sp:8s} {sd:%d/%m/%Y} {ed:%d/%m/%Y}"
    for k in results:
        if k.isundef:
            print('*', end='')
        else:
            print(' ', end='')
        print(lfmt.format(wid=nsize, tsize=tsize, nam=k.objname, num=k.count, pc=100.0 * k.count / total, sd=k.fromdate, ed=k.todate))

    print(tfmt.format(wid=nsize, tsize=tsize, nam="Total", num=total, sp="", sd=mind, ed=maxd))
