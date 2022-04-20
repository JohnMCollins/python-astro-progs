#! /usr/bin/env python3

"""Display all objects in pie chart"""

from operator import attrgetter
import argparse
import numpy as np
import remdefaults
import remgeom
import matplotlib.pyplot as plt
import miscutils


class obstot:
    """Details of result"""

    def __init__(self, objname, nobs):
        self.objname = objname
        self.count = int(nobs)
        self.isothers = False


def add_or_fields(mainfields, orfields):
    """Add subfields with OR to mainfields"""
    if len(orfields) == 0:
        return
    if len(orfields) == 1:
        mainfields.append(orfields[0])
        return
    mainfields.append("(" + " OR ".join(orfields) + ")")


rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='List all objects with first and last date',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--order', type=str, help='Order - (n)umber obs')
parsearg.add_argument('--cutoff', type=float, help='Summarise for percent arg less than this')
parsearg.add_argument('--targets', action='store_true', help='Show for targets, summarise for rest')
parsearg.add_argument('--dither', type=int, nargs='*', default=[0], help='Dither ID to limit to')
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to limit to')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
parsearg.add_argument('--title', type=str, default='Distribution of observation targets', help='Title')
parsearg.add_argument('--explode', type=float, default=0.5, help='Explode others by this')
parsearg.add_argument('--colours', type=str, default='blue,yellow,green,red', help='Colours of slices of pie as comma-sep')
rg.disp_argparse(parsearg, fmt='single')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
order = resargs['order']
cutoff = resargs['cutoff']
targets = resargs['targets']
gain = resargs["gain"]
dither = resargs['dither']
filters = resargs['filter']
title = resargs['title']
explodeamt = resargs['explode']
colours = resargs['colours'].split(',')
outfig = rg.disp_getargs(resargs)

mydb, dbcurs = remdefaults.opendb()

fields = []
if gain is not None:
    fields.append("ABS(gain-{:.3g}) < {:.3g}".format(gain, gain * 1e-3))

if filters is not None:
    ffs = []
    for o in filters:
        ffs.append("filter={:s}".format(mydb.escape(o)))
        add_or_fields(fields, ffs)

ffs = []
for d in dither:
    if d >= 0:
        ffs.append("dithID={:d}".format(d))
add_or_fields(fields, ffs)

sel = ''
if len(fields) != 0:
    sel = " WHERE " + " AND ".join(fields)

dbcurs.execute("SELECT object,COUNT(*) AS number FROM obsinf" + sel + " GROUP BY object")

results = []

for row in dbcurs.fetchall():
    obj, num = row
    results.append(obstot(obj, num))

nonproxr = [r for r in results if r.objname[0:4] != 'Prox']
proxr = [r for r in results if r.objname[0:4] == 'Prox']

prox = obstot('Proxima', np.sum([r.count for r in proxr]))

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
        summ.isothers = True
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
            summ.isothers = True
    results = intarg

if order is not None and len(order) != 0:
    f = order[0].lower()
    if f == 'n':
        results.sort(key=attrgetter('count'), reverse=True)

if summ is not None:
    results.append(summ)

counts = [k.count for k in results]
objnames = []
explodes = []
for k in results:
    n = k.objname
    if n == "Proxima":
        n = "Proxima Centauri"
    elif n == "BarnardStar":
        n = "Barnard's Star"
    elif n == 'Ross154':
        n = "Ross 154"
    objnames.append(n)
    exp = 0.0
    if k.isothers:
        exp = explodeamt
    explodes.append(exp)

plotfigure = rg.plt_figure()
plotfigure.canvas.manager.set_window_title("Distribution of objects")

if len(title) != 0:
    plt.title(title)
plt.pie(counts, labels=objnames, explode=explodes, colors=colours, autopct='%1.2f%%', shadow=True, textprops={'fontsize': rg.defwinfmt.ticksize})
plt.gca().axis('equal')
if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)
