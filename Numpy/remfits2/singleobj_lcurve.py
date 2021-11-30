#!  /usr/bin/env python3

"""Make light curve from findresults for one object"""

import argparse
import datetime
import warnings
import sys
import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import miscutils
import remdefaults
import remfits
import find_results
import objdata
import remgeom

matchname = re.compile('(\w+?)(\d+)$')

Filt_colour = dict(g='g', r='r', i='k', z='b')

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Get light curve for one object over time', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results')
parsearg.add_argument('--object', type=str, required=True, help='Object we are considering')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--marker', type=str, default=',', help='Marker style for scatter plot')
parsearg.add_argument('--dayint', type=int, help='Interval between dates')
parsearg.add_argument('--filter', type=str, help='Restrict display to just given filter')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
flist = resargs['files']
remdefaults.getargs(resargs)
targobj = resargs['object']
dayint = resargs['dayint']
marker = resargs['marker']
filt = resargs['filter']

if filt and filt not in Filt_colour:
    print("Unknown filter", filt, file=sys.stderr)
    sys.exit(11)

ofig = rg.disp_getargs(resargs)

mydb, mycurs = remdefaults.opendb()

try:
    targobj = objdata.get_objname(mycurs, targobj)
except objdata.ObjDataError as e:
    print("Trouble with", targobj, e.args[0], file=sys.stderr)
    sys.exit(10)

datelist = dict(g=[], i=[], r=[], z=[])
aducount = dict(g=[], i=[], r=[], z=[])

for ffile in flist:

    pref = miscutils.removesuffix(ffile, allsuff=True)
    mg = matchname.match(pref)
    if mg is None:
        print("Confused about name", pref, file=sys.stderr)
        continue

    try:
        imageff = remfits.parse_filearg(pref, mycurs)
    except remfits.RemFitsErr as e:
        print(e.args[0], file=sys.stderr)
        continue

    try:
        rstr = find_results.load_results_from_file(pref, imageff)
    except find_results.FindResultErr as e:
        print(e.args[0], file=sys.stderr)
        continue

    try:
        trstr = rstr[targobj]
    except find_results.FindResultErr:
        continue

    datelist[rstr.filter].append(rstr.obsdate)
    aducount[rstr.filter].append(trstr.adus)

fig = rg.plt_figure()

alldates = []
for f in 'girz':
    alldates += datelist[f]
mindate = min(alldates)
maxdate = max(alldates)
hrloc = mdates.HourLocator()
minloc = mdates.MinuteLocator()
secloc = mdates.SecondLocator()
df = mdates.DateFormatter("%Y-%m-%d")
ax = plt.gca()
ax.xaxis.set_major_locator(minloc)
ax.xaxis.set_major_formatter(df)

if dayint is None:
    dayint = 1
sd = mindate.toordinal()
ed = maxdate.toordinal() + 1
dlist = [datetime.datetime.fromordinal(x) for x in range(sd, ed, dayint)]

y_formatter = mtick.ScalarFormatter(useOffset=False)

if filt:
    dl = datelist[filt]
    aduc = aducount[filt]
    col = Filt_colour[filt]
    if len(dl) < 2:
        print("Not enough points to display for filter", filt, file=sys.stderr)
        sys.exit(20)
    ax = plt.subplot(111)
    ax.yaxis.set_major_formatter(y_formatter)
    plt.scatter(dl, aduc, marker=marker, color=col)
    plt.legend([targobj + " " + filt + " filter"])
    plt.xticks(dlist, rotation=45)
else:
    axlist = []
    for f, sp in (('g', 411), ('r', 412), ('i', 413), ('z', 414)):
        dl = datelist[f]
        aduc = aducount[f]
        col = Filt_colour[f]
        if len(dl) >= 2:
            ax = plt.subplot(sp)
            ax.yaxis.set_major_formatter(y_formatter)
            plt.scatter(dl, aduc, marker=marker, color=col)
            axlist.append(ax)
            plt.legend([targobj + " " + f + " filter"])
    lastax = axlist.pop()
    for ax in axlist:
        ax.xaxis.set_visible(False)
    plt.sca(lastax)
    plt.xticks(dlist, rotation=45)

plt.tight_layout()
if ofig is None:
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    fig.savefig(ofig)
