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
    ddates = dates
    if dispdate:
        ddates += refdate
        if ddates.min() < 2450000:
            ddates += 2450000
        ddates = list(map(lambda x:Time(x, format='jd').datetime, dates))

    fig = rg.plt_figure()
    fig.canvas.manager.set_window_title(miscutils.removesuffix(moanname))
    ax = plt.subplot(111)
    if ylower is not None:
        ax.set_ylim(ylower / yscale, yupper / yscale)
    # y_formatter = mtick.ScalarFormatter(useOffset=False)

    years = []
    if xlab is None:
        if not dispdate:
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
        breakpoints = np.where(dates[1:] - dates[:-1] >= breakat)[0]
        if len(breakpoints) == 0 or lstyle == "none":
            plt.plot(ddates, values, linestyle=lstyle, marker=marker, color=lcolour)
        else:
            breakpoints += 1
            breakpoints = list(breakpoints)
            st = 0
            while len(breakpoints) != 0:
                nd = breakpoints.pop(0)
                plt.plot(ddates[st:nd], values[st:nd], linestyle=lstyle, marker=marker, color=lcolour)
                st = nd
            if st < len(dates):
                plt.plot(ddates[st:], values[st:], linestyle=lstyle, marker=marker, color=lcolour)
    else:
        if yscale is not None:
            errs /= yscale
        elif sepplot:
            values /= values.mean()
            errs /= errs.mean()
            rerrs = errs/values
        breakpoints = np.where(dates[1:] - dates[:-1] >= breakat)[0]
        if len(breakpoints) == 0 or lstyle == "none":
            if sepplot:
                plt.plot(ddates, values, linestyle=lstyle, marker=marker, color=lcolour)
                plt.plot(ddates, errs, linestyle=lstyle, marker=marker, color=ecolour)
                plt.plot(ddates, rerrs, linestyle=lstyle, marker=marker, color=recolour)
            else:
                plt.errorbar(ddates, values, errs, linestyle=lstyle, marker=marker, color=lcolour, ecolor=ecolour)
        else:
            breakpoints += 1
            breakpoints = list(breakpoints)
            st = 0
            while len(breakpoints) != 0:
                nd = breakpoints.pop(0)
                if sepplot:
                    plt.plot(ddates[st:nd], values[st:nd], linestyle=lstyle, marker=marker, color=lcolour)
                    plt.plot(ddates[st:nd], errs[st:nd], linestyle=lstyle, marker=marker, color=ecolour)
                    plt.plot(ddates[st:nd], rerrs[st:nd], linestyle=lstyle, marker=marker, color=recolour)
                else:
                    plt.errorbar(ddates[st:nd], values[st:nd], errs[st:nd], linestyle=lstyle, marker=marker, color=lcolour, ecolor=ecolour)
                st = nd
            if st < len(dates):
                if sepplot:
                    plt.plot(ddates[st:], values[st:], linestyle=lstyle, marker=marker, color=lcolour)
                    plt.plot(ddates[st:], errs[st:], linestyle=lstyle, marker=marker, color=ecolour)
                    plt.plot(ddates[st:], rerrs[st:], linestyle=lstyle, marker=marker, color=recolour)
                else:
                    plt.errorbar(ddates[st:], values[st:], errs[st:], linestyle=lstyle, marker=marker, color=lcolour, ecolor=ecolour)
    if vmark is not None:
        vml = vmark
        if dispdate:
            vml = list(map(lambda x:Time(x, format='jd').datetime, vmark))
        for vm in vml:
            plt.axvline(vm, color=vcolour, alpha=valpha)
    if not dispdate:
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
parsearg.add_argument('--sepplot', action='store_true', help='Separate plots for value/error')
parsearg.add_argument('--break', type=float, default=1.0, help='Days to break plot at')
parsearg.add_argument('--marker', type=str, default='.', help='Marker for points')
parsearg.add_argument('--lstyle', type=str, default='dotted', help='Line style connecting points')
parsearg.add_argument('--colour', type=str, default='b', help='Colour of lines')
parsearg.add_argument('--ecolour', type=str, default='r', help='Colour of error bars')
parsearg.add_argument('--recolour', type=str, default='purple', help='Colour of relative error bars')
parsearg.add_argument('--refdate', type=float, default=0.0, help='Add to dates')
parsearg.add_argument('--vmark', type=float, nargs='*', help='Place given mark at days')
parsearg.add_argument('--vcolour', type=str, default='k', help='vmark colour')
parsearg.add_argument('--valpha', type=float, default=.75, help='Alpha for vmrks')
parsearg.add_argument('--ycolour', type=str, default='k', help='Colour for year marks')
parsearg.add_argument('--ymstyle', type=str, default='dotted', help='Line style for year markers')
parsearg.add_argument('--yalpha', type=float, default=.5, help='Alpha for years')
parsearg.add_argument('--multi', action='store_true', help='Treat one file as multiple')
parsearg.add_argument('--dispdate', action='store_true', help='Display dates rather than as days')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
infiles = resargs['files']
remdefaults.getargs(resargs)
ylab = resargs['ylabel']
xlab = resargs['xlabel']
sepplot = resargs['sepplot']
#daterot = resargs['daterot']
#bytime = resargs['bytime']
ylower = resargs['ylower']
yupper = resargs['yupper']
yscale = resargs['yscale']
lstyle = resargs['lstyle']
marker = resargs['marker']
lcolour = resargs['colour']
ecolour = resargs['ecolour']
recolour = resargs['recolour']
refdate = resargs['refdate']
breakat = resargs['break']
vmark = resargs['vmark']
vcolour = resargs['vcolour']
valpha = resargs['valpha']
ycolour = resargs['ycolour']
ymstyle = resargs['ymstyle']
yalpha = resargs['yalpha']
dispdate = resargs['dispdate']
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
