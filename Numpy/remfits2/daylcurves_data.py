#!  /usr/bin/env python3

"""Make light curve from findresults for one object"""

import argparse
import sys
from dateutil.relativedelta import *
from astropy.time import Time
import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import matplotlib.ticker as mtick
import numpy as np
import remdefaults
import remgeom
import miscutils


def plot_array(filestr, moanname):
    """Plot the array with given data and if need to moan,
    use "moanname"""

    try:
        data = np.loadtxt(filestr, unpack=True)
    except OSError as e:
        print("Cannot load from", moanname, "error was", e.args[1], file=sys.stderr)
        return  None
    try:
        if data.shape[0] == 2:
            dates, values = data
            errs = None
        else:
            dates, values, errs = data
    except ValueError:
        print("Unexpected format of", moanname, "expecting 3 columns", file=sys.stderr)
        return  None

    ass = np.argsort(dates)
    dates = dates[ass]
    values = values[ass]
    if errs is not None:
        errs = errs[ass]

    fig = rg.plt_figure()
    fig.canvas.manager.set_window_title(miscutils.removesuffix(moanname))
    ax = plt.subplot(111)
    if ylower is not None:
        ax.set_ylim(ylower / yscale, yupper / yscale)
    # y_formatter = mtick.ScalarFormatter(useOffset=False)

    years = []
    if xlab is None:
        t = dates.min() + refdate
        lastt = dates.max() + refdate
        if t < 2450000:
            t += 2450000
            lastt += 2450000
        t = Time(t, format='jd')
        t = t.datetime
        endt = Time(lastt, format='jd').datetime
        yr = t + relativedelta(year=t.year+1, day=1, month=1)
        while yr < endt:
            years.append((yr - t).days)
            yr = yr + relativedelta(year=yr.year+1, day=1, month=1)
        plt.xlabel("Days from {:%d %b %Y}".format(t))
    else:
        plt.xlabel(xlab)
    if ylab is not None:
        plt.ylabel(ylab)
    dates -= dates[0]
    if yscale is not None:
        values /= yscale
    if errs is None:
        plt.plot(dates, values, linestyle=lstyle, marker=marker, color=lcolour)
    else:
        if yscale is not None:
            errs /= yscale
        plt.errorbar(dates, values, errs, linestyle=lstyle, marker=marker, color=lcolour, ecolor=ecolour)
    if vmark is not None:
        for vm in vmark:
            plt.axvline(vm, color=vcolour, alpha=valpha)
    for y in years:
        plt.axvline(y, color=ycolour, linestyle=ymstyle, alpha=yalpha)
    plt.tight_layout()
    return  fig

#Lstyles = ('solid', 'dotted', 'dashed', 'dashdot')

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Get light curve from data', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Data table or use stdin')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--xlabel', type=str, help='X axis label')
parsearg.add_argument('--ylabel', type=str, help='Y axis label')
#parsearg.add_argument('--daterot', type=float, default=45, help='Rotation of dates')
#parsearg.add_argument('--bytime', action='store_true', help='Display by time')
parsearg.add_argument('--ylower', type=float, help='Lower limit of Y axis')
parsearg.add_argument('--yupper', type=float, help='Upper limit of Y axis')
parsearg.add_argument('--yscale', type=float, help='Scale for Y axis')
parsearg.add_argument('--marker', type=str, default='.', help='Marker for points')
parsearg.add_argument('--lstyle', type=str, default='dotted', help='Line style connecting points')
parsearg.add_argument('--colour', type=str, default='b', help='Colour of lines')
parsearg.add_argument('--ecolour', type=str, default='r', help='Colour of error bars')
parsearg.add_argument('--refdate', type=float, default=0.0, help='Add to dates')
parsearg.add_argument('--vmark', type=float, nargs='*', help='Place given mark at days')
parsearg.add_argument('--vcolour', type=str, default='k', help='vmark colour')
parsearg.add_argument('--valpha', type=float, default=.75, help='Alpha for vmrks')
parsearg.add_argument('--ycolour', type=str, default='k', help='Colour for year marks')
parsearg.add_argument('--ymstyle', type=str, default='dotted', help='Line style for year markers')
parsearg.add_argument('--yalpha', type=float, default=.5, help='Alpha for years')
parsearg.add_argument('--multi', action='store_true', help='Treat one file as multiple')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
infiles = resargs['files']
remdefaults.getargs(resargs)
ylab = resargs['ylabel']
xlab = resargs['xlabel']
#daterot = resargs['daterot']
#bytime = resargs['bytime']
ylower = resargs['ylower']
yupper = resargs['yupper']
yscale = resargs['yscale']
lstyle = resargs['lstyle']
marker = resargs['marker']
lcolour = resargs['colour']
ecolour = resargs['ecolour']
refdate = resargs['refdate']
vmark = resargs['vmark']
vcolour = resargs['vcolour']
valpha = resargs['valpha']
ycolour = resargs['ycolour']
ymstyle = resargs['ymstyle']
yalpha = resargs['yalpha']
multi = resargs['multi'] or len(infiles) > 1

ofig = rg.disp_getargs(resargs)

if len(infiles) == 0:
    resfig = plot_array(sys.stdin, 'standard input')
    if  resfig is None:
        sys.exit(50)
    remgeom.end_figure(resfig, ofig, 1, multi)
    remgeom.end_plot(ofig)
else:
    donesome = 0
    for file in infiles:
        resfig = plot_array(file, file)
        if  resfig is None:
            continue
        donesome += 1
        remgeom.end_figure(resfig, ofig, donesome, multi)
    if donesome == 0:
        sys.exit(50)
    remgeom.end_plot(ofig)
