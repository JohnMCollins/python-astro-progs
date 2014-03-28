#! /local/home/jcollins/lib/anaconda/bin/python

# Integrate the H alpha peaks to get figures for the total values,
# assume continuum is normalised at 1 unless otherwise specified

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
        self.peaksize = 0.0

parsearg = argparse.ArgumentParser(description='Get sizes of H Alpha peaks')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data controlfile')
parsearg.add_argument('--outfile', type=str, help='Output file')
parsearg.add_argument('--sepdays', type=int, default=1, help='Separate plots if this number of days apart')
parsearg.add_argument('--continuum', type=float, default=1.0, help='Value for continuum')

SPC_DOC_ROOT = "spcctrl"
SPC_DOC_NAME = "SPCCTRL"

res = vars(parsearg.parse_args())
rf = res['rangefile']
sf = res['specfile']
outf = res['outfile']
sepdays = res['sepdays']
continuum = res['continuum']

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
    halphar = rangelist.getrange("halpha")
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

resultdict = dict()

for dataset in spclist.datalist:
    try:
        xvalues = dataset.get_xvalues(False)
        yvalues = dataset.get_yvalues(False)
    except specdatactrl.SpecDataError:
        continue
    har, hir = meanval.mean_value(halphar, xvalues, yvalues)
    res = intresult(dataset)
    res.peaksize = hir / har - continuum
    resultdict[dataset.modjdate] = res

dates = resultdict.keys()
dates.sort()

rxarray = []
ryarray = []
rxvalues = []
ryvalues = []

lastdate = 1e12

for rk in dates:
    datum = resultdict[rk]
    dat = datum.dataarray.modbjdate
    ps = datum.peaksize
    if dat - lastdate > sepdays and len(rxvalues) != 0:
        rxarray.append(rxvalues)
        ryarray.append(ryvalues)
        rxvalues = []
        ryvalues = []
    rxvalues.append(dat)
    ryvalues.append(ps)
    lastdate = dat

if len(rxvalues) != 0:
   rxarray.append(rxvalues)
   ryarray.append(ryvalues)

colours = ('black','red','green','blue','yellow','magenta','cyan') * ((len(rxarray) + 6) / 7)

for xarr, yarr, col in zip(rxarray,ryarray,colours):
    reset = xarr[0]
    xa = np.array(xarr) - reset
    ya = np.array(yarr)
    plt.plot(xa, ya, col)
plt.show()



