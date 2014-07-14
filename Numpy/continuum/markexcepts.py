#! /local/home/jcollins/lib/anaconda/bin/python

# Mark exceptionial spectra

import argparse
import os.path
import sys
import numpy as np
import scipy.integrate as si
import scipy.optimize as so
import matplotlib.pyplot as plt

import specdatactrl
import datarange
import xmlutil

def selectrange(rangev, xvals, yvals):
    """Using the specified range, extract the xvals in the range and return those plus the corresponding
    Y values"""
    sel = (xvals >= rangev.lower) & (xvals <= rangev.upper)
    return (xvals[sel], yvals[sel])

class intresult(object):
    """Record integration results"""

    def __init__(self, da):
        self.dataarray = da
        self.bluecont = 0.0
        self.redcont = 0.0
        self.totcont = 0.0
        #self.medcont = 0.0
        self.note = None

parsearg = argparse.ArgumentParser(description='Mark exceptional spectra')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data controlfile')
parsearg.add_argument('--entirespec', action='store_true', help="Use entire spectrum, don't bother with ranges")
parsearg.add_argument('--median', action='store_true', help='Use median not mean')
parsearg.add_argument('--upperstd', type=float, default=5.0, help='Upper range of std devs to exclude')
parsearg.add_argument('--lowerstd', type=float, default=3.0, help='Lower range of std devs to exclude')
parsearg.add_argument('--reset', action='store_true', help='Reset discount markers')
parsearg.add_argument('--clear', action='store_true', help='Clear discount markers and remarks')
parsearg.add_argument('--markexc', action='store_true', help='Mark exceptional data sets')

SPC_DOC_ROOT = "spcctrl"
SPC_DOC_NAME = "SPCCTRL"

res = vars(parsearg.parse_args())
rf = res['rangefile']
sf = res['specfile']
entire = res['entirespec']
median = res['median']
upperstd = res['upperstd']
lowerstd = res['lowerstd']
reset = res['reset']
clear = res['clear']
markexc = res['markexc']

if not entire and rf is None:
    print "No range file specified"
    sys.exit(100)

if sf is None:
    print "No spec data control specified"
    sys.exit(101)

try:
    doc, root = xmlutil.load_file(sf, SPC_DOC_ROOT)
    spclist = specdatactrl.SpecDataList(sf)
    cnode = xmlutil.find_child(root, "cfile")
    spclist.load(cnode)
except xmlutil.XMLError as e:
    print "Load control file XML error", e.args[0]
    sys.exit(50)

if not entire:
    try:
        rangelist = datarange.load_ranges(rf)
    except datarange.DataRangeError as e:
        print "Range load error", e.args[0]
        sys.exit(51)

    try:
        contb = rangelist.getrange("contblue")
        contr = rangelist.getrange("contred")
    except datarange.DataRangeError as e:
        print e.args[0]
        sys.exit(52)

print "Loading data files"

try:
    spclist.loadfiles()
except specdatactrl.SpecDataError as e:
    print "Loading spectral data error", e.args[0]
    sys.exit(53)

print "load complete"

anychanges = 0

if reset:
    ndone = spclist.reset_markers()
    anychanges += ndone
    if ndone > 0:
        if ndone == 1: print "Reset a discount marker"
        else: print "Reset", ndone, "discount markers"
if clear:
    ndone = spclist.clear_remarks()
    anychanges += ndone
    if ndone > 0:
        if ndone == 1: print "Cleared a remark"
        else: print "Cleared", ndone, "remarks"

# Accumulate Y values to get median

allyvalues = np.empty((0,),dtype=np.float64)
resultdict = dict()
total = 0.0

if entire:
    for dataset in spclist.datalist:
        if dataset.modbjdate in resultdict:
            print "OOPS mod bjdate of", dataset.modbjdate, "dupllicated in data"
            sys.exit(200)
        try:
            xvalues = dataset.get_xvalues(False)
            yvalues = dataset.get_yvalues(False)
        except specdatactrl.SpecDataError:
            continue

        allyvalues = np.concatenate((allyvalues, yvalues))
        area = si.trapz(yvalues, xvalues)
        width = np.max(xvalues) - np.min(xvalues)
        mv = area / width
        resitem = intresult(dataset)
        resitem.totcont = mv
        resultdict[dataset.modbjdate] = resitem
        total += mv

else:

    totred = 0.0
    totblue = 0.0
    
    for dataset in spclist.datalist:
        if dataset.modbjdate in resultdict:
            print "OOPS mod bjdate of", dataset.modbjdate, "dupllicated in data"
            sys.exit(200)
        try:
            xvalues = dataset.get_xvalues(False)
            yvalues = dataset.get_yvalues(False)
        except specdatactrl.SpecDataError:
            continue

        # Extract the continuum ranges from the data

        contrx, contry = selectrange(contr, xvalues, yvalues)
        contbx, contby = selectrange(contb, xvalues, yvalues)
        conty = np.concatenate((contby, contry))
        allyvalues = np.concatenate((allyvalues, conty))
        rarea = si.trapz(contry, contrx)
        barea = si.trapz(contby, contbx)
        rwidth = np.max(contrx) - np.min(contrx)
        bwidth = np.max(contbx) - np.min(contbx)
        mvr = rarea / rwidth
        mvb = barea / bwidth
        mvtot = (rarea + barea) / (rwidth + bwidth)
        resitem = intresult(dataset)
        resitem.bluecont = mvb
        resitem.redcont = mvr
        resitem.totcont = mvtot
        resultdict[dataset.modbjdate] = resitem
        totred += mvr
        totblue += mvb
        total += mvtot

dates = resultdict.keys()
dates.sort()
numdates = len(dates)

meancont = total / numdates
mediancont = np.median(allyvalues)

if not entire:
    print "Finished scan av red", totred / numdates
    print "Av blue", totblue / numdates

print "Overall average", meancont
print "Median value is", mediancont

normto = meancont
normcol = "magenta"
if median:
    normto = mediancont
    normcol = "g"

totconts = [resultdict[r].totcont for r in dates]
if not entire:
    redconts = [resultdict[r].redcont for r in dates]
    blueconts = [resultdict[r].bluecont for r in dates]

fig = plt.gcf()
fig.canvas.set_window_title('Continuum levels')
if entire:
    plt.plot(dates, totconts, color='black', label='Overall level')
else:
    plt.plot(dates, totconts, color='black', label='Overall')
    plt.plot(dates, redconts, color="r", label="Red continuum")
    plt.plot(dates, blueconts, color="b", label="Blue continuum")

plt.axhline(y=mediancont, label="Median", color="g")
plt.axhline(y=meancont, label="Mean", color="magenta")

rms = totconts - normto
rms = np.sqrt(sum(rms * rms) / numdates)
ulim = normto + rms*upperstd
llim = normto - rms*lowerstd
plt.axhline(y=ulim, color=normcol, ls='--', label='Stddev+')
plt.axhline(y=llim, color=normcol, ls='--', label='Stddev-')
if markexc:
    notechanges = []
    if entire:
        for rk in dates:
            rd = resultdict[rk]
            totc = rd.totcont
            if not (llim < totc < ulim):
                rd.node = "Continuum outside range"
                notechanges.append(rd)
    else:
        for rk in dates:
            rd = resultdict[rk]
            redc = rd.redcont
            bluec = rd.bluecont
            if not (llim < redc < ulim) and (llim < bluec < ulim):
                rd.note = "Blue/Red outside range"
            elif not (llim < redc < ulim):
                rd.note = "Red outside range"
            elif not (llim < bluec < ulim):
                rd.note = "Blue Outside range"
            if rd.note is not None:
                notechanges.append(rd)
    for nt in notechanges:
        nt.dataarray.skip(nt.note)
    numch = len(notechanges)
    anychanges += numch
    print "Marked", numch, "Out of range"

if anychanges != 0:
    try:
        doc, root = xmlutil.init_save(SPC_DOC_NAME, SPC_DOC_ROOT)
        spclist.save(doc, root, "cfile")
        xmlutil.complete_save(sf, doc)
    except xmlutil.XMLError as e:
        print "XML error -", e.args[0]
       
plt.legend()
try:
    plt.show()
except KeyboardInterrupt:
    pass

