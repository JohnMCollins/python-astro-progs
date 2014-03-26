#! /local/home/jcollins/lib/anaconda/bin/python

# Integrate the continuum to give an overall value for normalising the intensity of a spectrum

import argparse
import os.path
import sys
import numpy as np
import matplotlib.pyplot as plt

import specdatactrl
import datarange
import xmlutil
import meanval

class intresult(object):
    """Record integration results"""

    def __init__(self, da):
        self.dataarray = da
        self.bluecont = 0.0
        self.redcont = 0.0
        self.totcont = 0.0

parsearg = argparse.ArgumentParser(description='Calculate continuum')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data controlfile')
parsearg.add_argument('--renorm', action='store_true', help='Rescale intensity to normalise')
parsearg.add_argument('--stddev', type=int, default=5, help='Number of std devs to highlight')

SPC_DOC_ROOT = "spcctrl"

res = vars(parsearg.parse_args())
rf = res['rangefile']
sf = res['specfile']
renorm = res['renorm']
stdevs = res['stddev']

if rf is None:
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

totred = 0.0
totblue = 0.0
totboth = 0.0
resultdict = dict()

for dataset in spclist.datalist:
    try:
        xvalues = dataset.get_xvalues(False)
        yvalues = dataset.get_yvalues(False)
    except specdatactrl.SpecDataError:
        continue
    rr, ir = meanval.mean_value(contr, xvalues, yvalues)
    br, ib = meanval.mean_value(contb, xvalues, yvalues)
    mvr = ir / rr
    mvb = ib / br
    totmv = (ir + ib) / (rr + br)
    res = intresult(dataset)
    res.bluecont = mvb
    res.redcont = mvr
    res.totcont = totmv
    resultdict[dataset.modjdate] = res
    totred += mvr
    totblue += mvb
    totboth += totmv

dates = resultdict.keys()
dates.sort()

redconts = [resultdict[r].redcont for r in dates]
blueconts = [resultdict[r].bluecont for r in dates]

redmean = np.mean(redconts)
redstddev = np.std(redconts)
bluemean = np.mean(blueconts)
bluestddev = np.std(blueconts)

rednote = stdevs * redstddev
bluenote = stdevs * bluestddev

for rk in dates:
    datum = resultdict[rk]
    dat = datum.dataarray.modjdate
    rd = datum.redcont
    bl = datum.bluecont
#    print "%15.6f %15.6f %15.6f" % (dat, rd, bl),
#    if abs(rd-redmean) >= rednote: print " Except red",
#    if abs(bl-bluemean) >= bluenote: print " Except blue",
#    print

num = float(len(dates))
print "Av red=",totred/num,"Av blue=",totblue/num,"overall=",totboth / num
plt.plot(dates,redconts,"r",dates,blueconts,"b")
plt.show()



