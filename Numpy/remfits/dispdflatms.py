#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T18:57:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: lcurve3.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:14+00:00

import matplotlib.pyplot as plt
import matplotlib.patches as mp
import matplotlib.dates as mdates
import warnings
import astroquery.utils as autils
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()
from scipy import stats
from matplotlib import colors
import numpy as np
import argparse
import sys
import math
import string
import remgeom
import dbops
import remdefaults
import dbremfitsobj
import os
import os.path
import subprocess
import trimarrays
import miscutils
import parsetime


def update_annot(ind):
    """Update annotatation for hover"""
    
    global scatterp, annot, fitsinds, means, stdds

    ii = ind['ind'][0]  
    pos = scatterp.get_offsets()[ii]
    annot.xy = pos
    # text = "{}, {}".format(" ".join(list(map(str,ind["ind"]))), " ".join([names[n] for n in ind["ind"]]))
    text = "%.1f %.1f" % (means[ii], stdds[ii])
    annot.set_text(text)
    # annot.get_bbox_patch().set_facecolor("g")
    annot.get_bbox_patch().set_alpha(0.4)


def hover(event):
    """Callback for mouse hover"""
    global scatterp, annot, ax, fig
    
    vis = annot.get_visible()
    if event.inaxes == ax:
        cont, ind = scatterp.contains(event)
        if cont:
            update_annot(ind)
            annot.set_visible(True)
            fig.canvas.draw_idle()
        elif vis:
            annot.set_visible(False)
            fig.canvas.draw_idle()


def donepressed(ind):
    """Respond to mouse click"""

    global pendingout, fitsinds, popupcommand
    
    ii = ind['ind'][0]
    fitsind = fitsinds[ii]
    pendingout.append(fitsind)
    if popupcommand is not None:
        try:
            subprocess.run(popupcommand + [str(fitsind)], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            ef = plt.figure(figsize=(10, 2))
            plt.axis("off")
            plt.text(0.1, 0.2, e.stderr.decode(), fontsize=16, color='r')
            # plt.show()


def pressed(event):
    global scatterp, ax, fig
    
    if event.inaxes == ax:
        cont, ind = scatterp.contains(event)
        if cont:
            donepressed(ind)

# Shut up warning messages


rg = remgeom.load()
mydbname = remdefaults.default_database()
tmpdir = remdefaults.get_tmpdir()

parsearg = argparse.ArgumentParser(description='Plot std deviation versus mean of daily flatsl', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
parsearg.add_argument('--dates', type=str, help='from:to dates to select from')
parsearg.add_argument('--divmean', action='store_true', help="Divide std dev by mean")
parsearg.add_argument('--limits', type=str, help='Lower:upper limit of means')
parsearg.add_argument('--cutlimit', type=str, default='all', choices=('all', 'limits', 'calclimits'), help='Point display and lreg calc, display all,')
parsearg.add_argument('--clipstd', type=float, help='Clip std devs this multiple different from std dev of std devs')
parsearg.add_argument('--filter', type=str, help='Restrict to given filter')
parsearg.add_argument('--title', type=str, default='Mean count of daily flats v Std dev', help='Title for plot')
parsearg.add_argument('--xlabel', type=str, default='Mean value', help='X axis label')
parsearg.add_argument('--ylabel', type=str, default='Std deviation', help='Y axis label')
parsearg.add_argument('--colour', type=str, default='b', help='Plot points colour')
parsearg.add_argument('--popupcolour', type=str, default='g', help='Popup colour')
parsearg.add_argument('--limscolour', type=str, default='k', help='Limit lines colour')
parsearg.add_argument('--regcolour', type=str, default='k', help='Regression colour')
parsearg.add_argument('--indfile', type=str, help='Output file for fits findex')
parsearg.add_argument('--greyscale', type=str, help='Greyscale to use for popup')
parsearg.add_argument('--logscale', action='store_true', help='Use log on popup histogram')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
dates = resargs['dates']
title = resargs['title']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
colour = resargs['colour']
popupcolour = resargs['popupcolour']
limscolour = resargs['limscolour']
regcolour = resargs['regcolour']
ofig = rg.disp_getargs(resargs)
filter = resargs['filter']
divmean = resargs['divmean']
clipstd = resargs['clipstd']
limits = resargs['limits']
cutlimit = resargs['cutlimit']
lowerlim = upperlim = None
greyscale = resargs['greyscale']
logscale = resargs['logscale']

fieldselect = ["mean IS NOT NULL", "typ='flat'", "ind!=0", "gain=1"]

if dates is not None:
    datesp = dates.split(':')
    try:
        if len(datesp) == 1:
            fieldselect.append("date(date_obs)='" + parsetime.parsedate(dates) + "'")
        elif len(datesp) != 2:
            print("Don't understand whate date", dates, "is supposed to be", file=sys.stderr)
            sys.exit(20)
        else:
            fd, td = datesp
            if len(fd) != 0:
                fieldselect.append("date(date_obs)>='" + parsetime.parsedate(fd) + "'")
            if len(td) != 0:
                fieldselect.append("date(date_obs)<='" + parsetime.parsedate(td) + "'")
    except ValueError as e:
        print(e.args[0])
        sys.exit(20)

if ofig is None:
    outputfile = None
    indfile = resargs['indfile']
    if indfile is not None:
        outputfile = open(indfile, "wt")

pendingout = []

popupcommand = None
if greyscale is not None:
    popupcommand = [ "rawimdisp.py", "--detach", "--greyscale", greyscale ]
    if logscale:
        popupcommand.append("--logscale")

if limits is not None:
    try:
        lowerlim, upperlim = [float(x) for x in limits.split(":")]
        if lowerlim >= upperlim:
            raise ValueError("Limits lower limit should be less than upper")
    except ValueError:
        limits = None

if ofig is not None:
    ofig = os.path.abspath(ofig)

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    print("Unable to select temporary directory", tmpdir, file=sys.stderr)
    sys.exit(100)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

if filter is not None:
    fieldselect.append("filter=" + dbase.escape(filter))

dbcurs.execute("SELECT mean,std,ind FROM iforbinf WHERE " + " AND ".join(fieldselect))

rows = np.array(dbcurs.fetchall())
if len(rows) < 20:
    print("Not enough data points found to plot", file=sys.stderr)
    sys.exit(2)
    
means = np.array(rows[:, 0])
stdds = np.array(rows[:, 1])
fitsinds = np.array(rows[:, 2]).astype(np.int64)

lrmeans = means.copy()
lrstdds = stdds.copy()
if limits is not None and cutlimit != 'all':
    mvs = (means >= lowerlim) & (means <= upperlim)
    lrmeans = means[mvs]
    lrstdds = stdds[mvs]
    if cutlimit == 'limits':
        means = lrmeans
        stdds = lrstdds
        fitsinds = fitsinds[mvs]
if divmean:
    stdds /= means
    lrstdds /= lrmeans
    stdds *= 100.0
    lrstdds *= 100.0

if clipstd is not None:
    sc = np.abs(stdds - stdds.mean()) / means < clipstd
    means = means[sc]
    stdds = stdds[sc]
    fitsinds = fitsinds[sc]
    sc = np.abs(lrstdds - lrstdds.mean()) / lrmeans < clipstd
    lrmeans = lrmeans[sc]
    lrstdds = lrstdds[sc]

ass = np.argsort(stdds)
means = means[ass]
stdds = stdds[ass]
fitsinds = fitsinds[ass]
ass = np.argsort(means)
means = means[ass]
stdds = stdds[ass]
fitsinds = fitsinds[ass]

fig = rg.plt_figure()
scatterp = plt.scatter(means, stdds, color=colour)

if ofig is None:
    ax = plt.gca()
    annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points", bbox=dict(boxstyle="round", fc=popupcolour), arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)
    fig.canvas.mpl_connect("motion_notify_event", hover)
    fig.canvas.mpl_connect('button_press_event', pressed)

if limits is not None and cutlimit != 'limits':
    plt.axvline(lowerlim, color=limscolour)
    plt.axvline(upperlim, color=limscolour)
lrslope, lrintercept, lrr, lrp, lrstd = stats.linregress(lrmeans, lrstdds)
lrx = np.array([lrmeans.min(), lrmeans.max()])
lry = lrx * lrslope + lrintercept
plt.plot(lrx, lry, color=regcolour)
xt = ''
if limits is not None:
    if cutlimit == 'all':
        xt = ' (all points)'
    elif cutlimit == 'calclimits':
        xt = ' (between limits)'
plt.title(title + "\n" + "Slope %.3g Intercept %.3g Correlation %.3g" % (lrslope, lrintercept, lrr) + xt + "\nFor " + filter + " filter")
plt.xlabel(xlab)
plt.ylabel(ylab)
if ofig is None:
    plt.show()
    if outputfile is not None and len(pendingout) != 0:
        pendingout = list(set(pendingout))
        pendingout.sort()
        for p in pendingout:
            print(p, file=outputfile)
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    plt.gcf().savefig(ofig)
