#!  /usr/bin/env python3

"""Make light curve from findresults for one object"""

import argparse
import sys
import re
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import numpy as np
import remdefaults
import find_results
import objdata
import remgeom
import miscutils


class Result:

    """Recuord results"""

    def __init__(self, when, filtname, findresult, obsind, adubyref=None):
        self.when = when
        self.filtname = filtname
        self.findres = findresult
        if adubyref is None:
            self.refset = self.adubyref = None
        else:
            self.refset = set(adubyref)
            self.adubyref = adubyref
        self.reladus = 0.0
        self.obsind = obsind


Valuelist = np.array([]).reshape(0, 2)
Points_list = []
Annotation = None
XBase = YBase = XScale = YScale = None


def setup_hover(plotres, obs):
    """Set up the parameters needed to do hover over chart"""
    global Valuelist, Points_list
    Valuelist = np.concatenate((Valuelist, plotres[0].get_xydata()))
    Points_list += obs


def complete_hover(figur):
    """Complete setup of hover"""
    global Annotation, XBase, YBase, XScale, YScale, Valuelist
    canv = figur.canvas
    axs = figur.axes[0]
    Annotation = axs.annotate("", xy=(0, 0), xytext=(20, 20),
                              xycoords='figure pixels',
                              textcoords="offset points",
                              bbox=dict(boxstyle="round",
                              fc=popupcolour),
                              arrowprops=dict(arrowstyle="->"))
    Annotation.get_bbox_patch().set_alpha(alphaflag)
    Annotation.set_visible(False)
    canv.mpl_connect('motion_notify_event', hover)
    XBase, XScale = axs.get_xlim()
    YBase, YScale = axs.get_ylim()
    XScale -= XBase
    YScale -= YBase
    Valuelist -= (XBase, YBase)
    Valuelist /= (XScale, YScale)
    Valuelist = np.array([complex(r, i) for r, i in Valuelist])


def find_nearest_result(event):
    """Get result nearest to event"""
    axs = event.inaxes
    if axs is None:
        return  None
    distances = np.abs(Valuelist - complex((event.xdata - XBase) / XScale, (event.ydata - YBase) / YScale))
    min_dist_arg = np.argmin(distances)
    if  distances[min_dist_arg] <= flagdist:
        return  Points_list[min_dist_arg]
    return  None


def hover(event):
    """Callback for mouse hover"""
    global Annotation
    vis = Annotation.get_visible()
    res = find_nearest_result(event)
    if res is None:
        if vis:
            Annotation.set_visible(False)
            event.canvas.draw_idle()
        return
    Annotation.set_text("{:%d/%m/%Y %H:%M:%S} obsid {:d}".format(res.when, res.obsind))
    Annotation.xy = (event.x, event.y)
    Annotation.set_visible(True)
    event.canvas.draw_idle()


resultlist = []

matchname = re.compile('(\w+?)(\d+)$')

Filt_colour = dict(g='g', r='r', i='k', z='b')
Lstyles = ('solid', 'dotted', 'dashed', 'dashdot')
Names = dict(GJ551='Proxima Centauri', GJ699="Barnard\'s Star", GJ729='Ross 154')

nresults = dict()
for filtp in Filt_colour:
    nresults[filtp] = 0

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Get light curve over day', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results files')
parsearg.add_argument('--object', type=str, required=True, help='Object')
remdefaults.parseargs(parsearg, tempdir=False)
# parsearg.add_argument('--marker', type=str, default=',', help='Marker style for scatter plot')
parsearg.add_argument('--userefobj', action='store_true', help='Use reference objects')
parsearg.add_argument('--popupcolour', type=str, default='g', help='Popup colour')
parsearg.add_argument('--alphaflag', type=float, default=0.4, help='Alpha for flag and popup')
parsearg.add_argument('--flagdist', type=float, default=10.0, help='Percentage of range for flag dist')
parsearg.add_argument('--filter', type=str, help='Restrict display to just given filter')
parsearg.add_argument('--xlabel', type=str, help='X axis label')
parsearg.add_argument('--ylabel', type=str, help='Y axis label')
parsearg.add_argument('--daterot', type=float, default=45, help='Rotation of dates')
parsearg.add_argument('--verbose', action='store_true', help='Give blow-by-blow account')
parsearg.add_argument('--bytime', action='store_true', help='Display by time')
parsearg.add_argument('--ylower', type=float, help='Lower limit of Y axis')
parsearg.add_argument('--yupper', type=float, help='Upper limit of Y axis')
parsearg.add_argument('--yscale', type=float, help='Scale for Y axis')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
flist = resargs['files']
remdefaults.getargs(resargs)
targobj = resargs['object']
# marker = resargs['marker']
userefs = resargs['userefobj']
popupcolour = resargs['popupcolour']
alphaflag = resargs['alphaflag']
flagdist = resargs['flagdist'] / 100.0
filt = resargs['filter']
if filt:
    filt = set(list(filt))
verbose = resargs['verbose']
ylab = resargs['ylabel']
xlab = resargs['xlabel']
daterot = resargs['daterot']
bytime = resargs['bytime']
ylower = resargs['ylower']
yupper = resargs['yupper']
yscale = resargs['yscale']

if xlab is None:
    if bytime:
        xlab = "Time observation taken"
    else:
        xlab = "Time & date of observation"
if userefs:
    if yscale is None:
        yscale = 1.0
    if ylab is None:
        if yscale != 1.0:
            ylab = "Relative ADU count (scale x {:.6g})".format(yscale)
        else:
            ylab = "Relative ADU count"
else:
    if yscale is None:
        yscale = 1e3
    if ylab is None:
        if yscale != 1.0:
            ylab = "ADU count (scale x {:.6g})".format(yscale)
        else:
            ylab = "ADU count"

filt_colour_lists = dict(g=[], i=[], r=[], z=[])
filt_colour_counts = dict(g=0, i=0, r=0, z=0)

if filt is not None and len(filt) == 1:
    for ls in Lstyles:
        for col in Filt_colour.values():
            fc = (ls, col)
            for filtp in 'girz':
                filt_colour_lists[filtp].append(fc)
else:
    for filtp, col in Filt_colour.items():
        for ls in Lstyles:
            filt_colour_lists[filtp].append((ls, col))

ofig = rg.disp_getargs(resargs)

mydb, mycurs = remdefaults.opendb()

try:
    targobj = objdata.get_objname(mycurs, targobj)
except objdata.ObjDataError as e:
    print("Trouble with", targobj, e.args[0], file=sys.stderr)
    sys.exit(10)

for fil in flist:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        continue
    if findres.num_results(idonly=True, nohidden=True) == 0:
        print(fil, "has no results", file=sys.stderr)
        continue

    if filt and findres.filter not in filt:
        if verbose:
            print(fil, "is for filter", findres.filter, "skipping", file=sys.stderr)
        continue

    try:
        targfr = findres[targobj]
    except find_results.FindResultErr:
        if verbose:
            print(targobj, "not found in", fil, "skipping", file=sys.stderr)
        continue
    if  targfr.hide:
        if verbose:
            print(targobj, "is in", fil, "but is hidden", file=sys.stderr)
        continue

    if userefs:
        refobjadus = dict()
        for fr in findres.results(idonly=True, nohidden=True):
            name = fr.obj.objname
            if name != targobj:
                refobjadus[name] = fr.adus
        resultlist.append(Result(findres.obsdate, findres.filter, targfr, findres.obsind, refobjadus))
    else:
        resultlist.append(Result(findres.obsdate, findres.filter, targfr, findres.obsind))
    nresults[findres.filter] += 1

if len(resultlist) < 2:
    print("Insufficient results", file=sys.stderr)
    sys.exit(20)

if filt and verbose:
    for filtp in filt:
        if nresults[filtp] < 2:
            print("Insufficient results for filter", filtp, file=sys.stderr)

if userefs:
    # Set up common subset array
    # Grab first one to kick things out of

    filter_subset = dict()
    for r in resultlist:
        if r.filtname not in filter_subset:
            filter_subset[r.filtname] = r.refset

    # Find common subset for each filter as union of what we had before with the new set

    for r in resultlist:
        filter_subset[r.filtname] &= r.refset

    for filtp, fsub in filter_subset.items():
        nsub = len(fsub)
        if nsub == 0:
            if verbose:
                print("No common subset for filter", filtp, file=sys.stderr)
            nresults[filtp] = 0
            continue
        if verbose and nsub < 5:
            print("Warning only", nsub, "in subset for filter", filtp, file=sys.stderr)
        for resp in resultlist:
            if resp.filtname == filtp:
                resp.reladus = resp.findres.adus / np.sum([resp.adubyref[n] for n in fsub])

fig = rg.plt_figure()
ax = plt.subplot(111)
if ylower is not None:
    ax.set_ylim(ylower / yscale, yupper / yscale)
y_formatter = mtick.ScalarFormatter(useOffset=False)
if bytime:
    df = mdates.DateFormatter("%H:%M")
else:
    df = mdates.DateFormatter("%d/%m/%y %H:%M")
ax.xaxis.set_major_formatter(df)
if daterot != 0.0:
    plt.xticks(rotation=daterot)
plt.xlabel(xlab)
plt.ylabel(ylab.format(yscale=yscale))

try:
    targobjname = Names[targobj]
except KeyError:
    targobjname = targobj

leglist = []
if bytime:
    for filtp, nres in nresults.items():
        if nres <= 0:
            continue
        results_for_filter = sorted([res for res in resultlist if res.filtname == filtp], key=lambda x: x.when)
        lastdate = datetime.date(1901, 1, 1)
        timelist = []
        lscount = 0
        while len(results_for_filter) != 0:
            nxtr = results_for_filter.pop(0)
            nxtdt = nxtr.when
            nxtd = nxtdt.date()
            if nxtd != lastdate:
                if len(timelist) > 2:
                    adulist = np.array(adulist) / yscale
                    mnadu = adulist.mean()
                    stadu = adulist.std()
                    if userefs:
                        leglist.append("Filter {:s} {:%d/%m/%y} ${:.3g} \pm {:.2g}$ (ss {:d})".format(filtp, lastdate, mnadu, stadu, len(filter_subset[filtp])))
                    else:
                        leglist.append("Filter {:s} {:%d/%m/%y} ${:.3g} \pm {:.2g}$".format(filtp, lastdate, mnadu, stadu))
                    ls, col = filt_colour_lists[filtp][filt_colour_counts[filtp] % len(filt_colour_lists[filtp])]
                    pstr = plt.errorbar(timelist, adulist, stadu, color=col, linestyle=ls)
                    filt_colour_counts[filtp] += 1
                    setup_hover(pstr, obsinds)
                timelist = []
                adulist = []
                obsinds = []
                lastdate = nxtd
            timelist.append(datetime.datetime(2020, 1, 1, nxtdt.hour, nxtdt.minute, nxtdt.second))
            if userefs:
                adulist.append(nxtr.reladus)
            else:
                adulist.append(nxtr.findres.adus)
            obsinds.append(nxtr)

        # Do trailing ones

        if len(timelist) > 2:
            adulist = np.array(adulist) / yscale
            mnadu = adulist.mean()
            stadu = adulist.std()
            if userefs:
                leglist.append("Filter {:s} {:%d/%m/%y} ${:.3g} \pm {:.2g}$ (ss {:d})".format(filtp, lastdate, mnadu, stadu, len(filter_subset[filtp])))
            else:
                leglist.append("Filter {:s} {:%d/%m/%y} ${:.3g} \pm {:.2g}$".format(filtp, lastdate, mnadu, stadu))
            ls, col = filt_colour_lists[filtp][filt_colour_counts[filtp] % len(filt_colour_lists[filtp])]
            pstr = plt.errorbar(timelist, adulist, stadu, color=col, linestyle=ls)
            setup_hover(pstr, obsinds)
else:
    for filtp, nres in nresults.items():
        if nres <= 0:
            continue
        datelist = []
        adulist = []
        obsinds = []
        for rl in sorted([res for res in resultlist if res.filtname == filtp], key=lambda x: x.when):
            datelist.append(rl.when)
            if userefs:
                adulist.append(rl.reladus)
            else:
                adulist.append(rl.findres.adus)
            obsinds.append(rl)
        if len(datelist) < 2:
            continue
        adulist = np.array(adulist) / yscale
        mnadu = adulist.mean()
        stadu = adulist.std()
        ls, col = filt_colour_lists[filtp][filt_colour_counts[filtp] % len(filt_colour_lists[filtp])]
        pstr = plt.errorbar(datelist, adulist, stadu, color=col, linestyle=ls)
        filt_colour_counts[filtp] += 1
        setup_hover(pstr, obsinds)
        if userefs:
            leglist.append("Filter {:s} ${:.3g} \pm {:.2g}$ ({:d} subset)".format(filtp, mnadu, stadu, len(filter_subset[filtp])))
        else:
            leglist.append("Filter {:s} ${:.3g} \pm {:.2g}$".format(filtp, mnadu, stadu))
plt.legend(leglist)

plt.tight_layout()
if ofig is None:
    complete_hover(fig)
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    fig.savefig(ofig)
