#!  /usr/bin/env python3

"""Display paths of objects with PM"""

import argparse
import sys
import datetime
import copy
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import remdefaults
import remgeom
import objdata
import parsetime
import miscutils

dispnames = dict(prox='Proxima Centauri', bstar="Barnard's Star", ross='Ross 154')


def get_dispname(objn):
    """Get display name of object, allowing for things with \ in front"""
    ret = objn
    if ret[0] != '\\':
        return  ret
    ret = ret[1:]
    try:
        return  dispnames[ret]
    except KeyError:
        return  ret


rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Display paths of object', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('object', nargs=1, type=str, help='Object to trace')
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
parsearg.add_argument('--fromdate', type=str, default='1/1/2017', help='Starting date for plot')
parsearg.add_argument('--todate', type=str, help='End date for plot, default now')
parsearg.add_argument('--incrs', type=int, default=20, help='Number of intervals to plot')
parsearg.add_argument('--minpm', type=float, default=100.0, help='Minimum PM to accept in mas/yr')
parsearg.add_argument('--decoffs', type=float, default=0.01, help='Factor of max DEC range for text offset')
parsearg.add_argument('--raoffs', type=float, default=-0.03, help='Factor of max RA range for text offset')
parsearg.add_argument('--plotcolour', type=str, default='b', help='Colour of plot')
parsearg.add_argument('--plotmarker', type=str, default='*', help='Marker of dates on plot')
parsearg.add_argument('--objcolour', type=str, default='g', help='Colour of objects')
parsearg.add_argument('--objmarker', type=str, default='*', help='Marker of objects on plot')
parsearg.add_argument('--highcolour', type=str, default='r', help='Colour for highlighted objects')
parsearg.add_argument('--highmarker', type=str, default='*', help='Marker for highlighted objects')
parsearg.add_argument('--highlight', type=str, nargs='*', help='Highlight object names')
parsearg.add_argument('--idfont', type=int, default=0, help='Font to write names of objects in, 0 means do not display')
parsearg.add_argument('--extra', type=float, default=.01, help='Amount to add to local search in deg')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
target = resargs['object'][0]
remdefaults.getargs(resargs)
figout = rg.disp_getargs(resargs)
fromd = resargs['fromdate']
tod = resargs['todate']
incrs = resargs['incrs']
minpm = resargs['minpm']
decoffs = resargs['decoffs']
raoffs = resargs['raoffs']
plotcolour = resargs['plotcolour']
plotmarker = resargs['plotmarker']
objcolour = resargs['objcolour']
objmarker = resargs['objmarker']
idfont = resargs['idfont']
highcolour = resargs['highcolour']
highmarker = resargs['highmarker']
highlight = resargs['highlight']
hlist = set()
if highlight is not None:
    hlist = set(highlight)
extra = resargs["extra"]

try:
    fromd = parsetime.parsetime(fromd)
except ValueError as e:
    print("Did not understand from date, error was", e.args[0], file=sys.stderr)
    sys.exit(10)
if tod is None:
    tod = datetime.datetime.now()
else:
    try:
        tod = parsetime.parsetime(tod, atend=True)
    except ValueError as e:
        print("Did not understand to date, error was", e.args[0], file=sys.stderr)
        sys.exit(11)

intv = datetime.timedelta(seconds=(tod - fromd).total_seconds() / incrs)

mydb, dbcurs = remdefaults.opendb()
targobj = objdata.ObjData(target)
try:
    targobj.get(dbcurs)
except objdata.ObjDataError as e:
    print("Could not get object", target, "error was", e.args[0], file=sys.stderr)
    sys.exit(12)

if not targobj.is_target():
    if targobj.objname != target:
        print(target, "(" + targobj.objname + ")", "is not a target - in vicinity of", targobj.vicinity, file=sys.stderr)
    else:
        print(target, "is not a target - in vicinity of", targobj.vicinity, file=sys.stderr)
    sys.exit(13)

target = get_dispname(targobj.dispname)
targname = targobj.objname

if targobj.rapm is None or targobj.decpm is None:
    print(target, "has no proper motion recorded", file=sys.stderr)
    sys.exit(14)

if abs(targobj.rapm) < minpm and abs(targobj.decpm) < minpm:
    print("PMs are too samll, less than", minpm, "RA", targobj.rapm, "DEC", targobj.decpm, "min is", minpm, file=sys.stderr)
    sys.exit(15)

ras = []
decs = []
dates = []
cdat = fromd
lastra = lastdec = 1e10
plotfigure = rg.plt_figure()

while cdat < tod:
    dates.append(cdat.strftime("%Y-%m-%d"))
    ct = copy.copy(targobj)
    ct.apply_motion(cdat)
    ras.append(ct.ra)
    decs.append(ct.dec)
    cdat += intv

dates.append(tod.strftime("%Y-%m-%d"))
targobj.apply_motion(tod)
ras.append(targobj.ra)
decs.append(targobj.dec)

formatter = mtick.ScalarFormatter(useOffset=False)
plt.gca().xaxis.set_major_formatter(formatter)
plt.gca().yaxis.set_major_formatter(formatter)

plt.plot(ras, decs, marker=plotmarker, color=plotcolour)
plt.legend([target])

mindec = min(decs)
maxdec = max(decs)
minra = min(ras)
maxra = max(ras)

decdiff = (maxdec - mindec) * decoffs
radiff = (maxra - minra) * raoffs

for ra, dec, dat in zip(ras, decs, dates):
    plt.text(ra + radiff, dec + decdiff, dat)

dbcurs.execute(("SELECT objname,dispname,radeg,decdeg FROM objdata WHERE " +
               "radeg >= {minra:.8e} AND radeg <= {maxra:.8e} AND " +
               "decdeg >= {mindec:.8e} AND decdeg <= {maxdec:.8e}").format(minra=minra - extra, maxra=maxra + extra, mindec=mindec - extra, maxdec=maxdec + extra))

dispnames = []
objnames = []
ras = []
decs = []
hdispnames = []
hobjnames = []
hras = []
hdecs = []

rows = dbcurs.fetchall()

for onam, dispn, ra, dec in rows:
    if onam == targname:
        continue
    if onam in hlist:
        hdispnames.append(get_dispname(dispn))
        hobjnames.append(onam)
        hras.append(ra)
        hdecs.append(dec)
    else:
        dispnames.append(get_dispname(dispn))
        objnames.append(onam)
        ras.append(ra)
        decs.append(dec)

plt.scatter(ras, decs, color=objcolour, marker=objmarker)
if len(hras) != 0:
    plt.scatter(hras, hdecs, color=highcolour, marker=highmarker)

if idfont != 0:
    for ra, dec, onam, dname in zip(ras, decs, objnames, dispnames):
        plt.text(ra + radiff, dec + decdiff, dname, fontsize=idfont)
    for ra, dec, onam, dname in zip(hras, hdecs, hobjnames, hdispnames):
        plt.text(ra + radiff, dec + decdiff, dname, fontsize=idfont, color=highcolour)

plt.xlabel("RA (deg)")
plt.ylabel("DEC (deg)")

if figout is not None:
    outfile = miscutils.addsuffix(figout, "png")
    plotfigure.savefig(outfile)
    plt.close(plotfigure)
else:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
