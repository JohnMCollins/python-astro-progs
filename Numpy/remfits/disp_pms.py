#! /usr/bin/env python3

"""Plot Proper Motions of object"""

import sys
import argparse
import matplotlib.pyplot as plt
import remgeom
import remdefaults
import objdata
import miscutils


def plotdate(pentry):
    """Put date as a text entry on an appropriate side of the given point"""
    rad, decd, dat = pentry
    pdat = dat.strftime("%Y-%m-%d")
    leftx, rightx = plt.gca().get_xlim()
    toff = (leftx - rightx) * toffset
    # If it's nearer left margin put it on right otherwise left
    # Remember RA is decreasing to right
    if leftx - rad < rad - rightx:
        plt.text(rad - toff, decd, pdat, va='center')
    else:
        plt.text(rad + toff, decd, pdat, ha='right', va='center')


rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Plot proper motions of object relative to background', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('targets', type=str, nargs='+', help='Target objects to plot for')
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
rg.disp_argparse(parsearg)
parsearg.add_argument('--rarange', type=float, default=0.2, help='Range for RA display')
parsearg.add_argument('--decrange', type=float, default=0.2, help='Range for DEC display')
parsearg.add_argument('--targcolour', type=str, default='b', help='Colour to display target')
parsearg.add_argument('--targalpha', type=float, default=1.0, help='Alpha value for target colour')
parsearg.add_argument('--objcolour', type=str, default='k', help='Colour for objects other than target')
parsearg.add_argument('--otherpmcolour', type=str, default='g', help='Colour for objects other than target which also move')
parsearg.add_argument('--apsize', type=int, help='Aperture size otherwise use DB value')
parsearg.add_argument('--apmult', type=float, default=4.0, help='Multiple of aperture size for scatter')
parsearg.add_argument('--xlabel', type=str, default='RA (deg)', help='Label for X axis')
parsearg.add_argument('--ylabel', type=str, default='Dec (deg)', help='Label for Y axis')
parsearg.add_argument('--xrot', type=float, default=0.0, help="Rotation of X axis ticks")
parsearg.add_argument('--yrot', type=float, default=0.0, help="Rotation of Y axis ticks")
parsearg.add_argument('--toffset', type=float, default=5, help='Offset facfor first/last label')

resargs = vars(parsearg.parse_args())
targets = resargs["targets"]
remdefaults.getargs(resargs)
ofig = rg.disp_getargs(resargs)
ra_disp_range = resargs["rarange"]
dec_disp_range = resargs['decrange']
targcolour = resargs['targcolour']
targalpha = resargs['targalpha']
objcolour = resargs['objcolour']
otherpmcolour = resargs['otherpmcolour']
setapsize = resargs['apsize']
apmult = resargs['apmult']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
xrot = resargs['xrot']
yrot = resargs['yrot']
toffset = resargs['toffset'] / 100.0

if ofig is not None:
    ofig = miscutils.removesuffix(ofig, ".png")

mydb, mycurs = remdefaults.opendb()

targobjs = []
targets = sorted(list(set(targets)))
for targ in targets:
    tobj = objdata.ObjData(name=targ)
    try:
        tobj.get(mycurs)
    except objdata.ObjDataError as e:
        print("Cannot find", targ, "error was", e.args[0], file=sys.stderr)
        continue
    if tobj.rapm is None or tobj.decpm is None:
        print("No proper motion recorded for", targ, file=sys.stderr)
        continue
    targobjs.append(tobj)

if len(targobjs) != len(targets):
    print("Aborteing due to errors", file=sys.stderr)
    sys.exit(10)

multifig = len(targobjs) > 1
fignum = 1

for tobj in targobjs:

    mycurs.execute("SELECT MIN(radeg),MAX(radeg),MIN(decdeg),MAX(decdeg) FROM objpm WHERE objind={:d}".format(tobj.objind))
    minra, maxra, mindec, maxdec = mycurs.fetchall()[0]

    rarange = maxra - minra
    decrange = maxdec - mindec

    if  rarange > ra_disp_range or decrange > dec_disp_range:
        print("Range of ra/disp values in data for", tobj.dispname, "too great please increase --rarange/--decrange", file=sys.stderr)
        print("Ra range is {:.6f} against {:.6f}".format(rarange, ra_disp_range), file=sys.stderr)
        print("Dec range is {:.6f} against {:.6f}".format(decrange, dec_disp_range), file=sys.stderr)
        sys.exit(50)

    # Probably don't need max/min stuff but so "nothing can go wrong"

    rapad = (ra_disp_range - rarange) / 2
    decpad = (dec_disp_range - decrange) / 2
    pminra = max(0, minra - rapad)
    pmaxra = min(360, maxra + rapad)
    pmindec = max(-90, mindec - decpad)
    pmaxdec = min(90, maxdec + decpad)

    pltfig = rg.plt_figure()
    pltfig.canvas.manager.set_window_title("Proper motion for {:s}".format(tobj.dispname))
    plt.ticklabel_format(useOffset=False)
    plt.xlim(pminra, pmaxra)
    plt.ylim(pmindec, pmaxdec)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    if xrot != 0.0:
        plt.xticks(rotation=xrot)
    if yrot != 0.0:
        plt.yticks(rotation=yrot)
    ax = pltfig.axes[0]
    ax.xaxis.set_inverted(True)
    plt.grid()
    mycurs.execute("SELECT radeg,decdeg,obsdate FROM objpm WHERE objind={:d} ORDER BY obsdate".format(tobj.objind))
    plist = mycurs.fetchall()
    tapsize = tobj.apsize
    if setapsize is not None:
        tapsize = setapsize
    xcs = [a[0] for a in plist]
    ycs = [a[1] for a in plist]
    plt.scatter(xcs, ycs, tapsize * apmult, color=targcolour, alpha=targalpha)
    plotdate(plist[0])
    plotdate(plist[-1])
    mycurs.execute("SELECT radeg,decdeg,apsize,rapm,decpm,ind FROM objdata WHERE suppress=0 AND ind!={:d} AND radeg>={:.6e} AND radeg<={:.6e} AND decdeg>={:.6e} AND decdeg<={:.6e}".format(tobj.objind, pminra, pmaxra, pmindec, pmaxdec))
    otherpms = dict()
    for ra, dec, ap, rapm, decpm, ind in mycurs.fetchall():
        if setapsize is not None:
            ap = setapsize
        if rapm is not None and decpm is not None:
            otherpms[ind] = ap
            continue
        plt.scatter((ra,), (dec,), ap * apmult, objcolour, alpha=targalpha)
    for ind, ap in otherpms.items():
        mycurs.execute("SELECT radeg,decdeg FROM objpm WHERE objind={:d} ORDER BY obsdate".format(ind))
        plist = mycurs.fetchall()
        xcs = [a[0] for a in plist]
        ycs = [a[1] for a in plist]
        plt.scatter(xcs, ycs, ap * apmult, color=otherpmcolour, alpha=targalpha)
    if ofig is not None:
        if multifig:
            outfile = "{:s}{:03d}.png".format(ofig, fignum)
        else:
            outfile = "{:s}.png".format(ofig)
        pltfig.savefig(outfile)
        fignum += 1

if ofig is None:
    plt.show()
