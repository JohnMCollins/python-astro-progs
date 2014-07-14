#! /local/home/jcollins/lib/anaconda/bin/python

# Integrate the continuum to give an overall value for normalising the intensity of a spectrum

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
import polynomial

def selectrange(rangev, xvals, yvals):
    """Using the specified range, extract the xvals in the range and return those plus the corresponding
    Y values"""
    sel = (xvals >= rangev.lower) & (xvals <= rangev.upper)
    return (xvals[sel], yvals[sel])

def poly0(x, a):
    """Polynomial of order 0 of x with coeffs a"""
    return  a

def poly1(x, a, b):
    """Polynomial of order 1 of x with coeffs a b a + b*x"""
    return  a + b * x

def poly2(x, a, b, c):
    """Return a + b*x + c*x^2"""
    return  a + (b + c*x) * x

def poly3(x, a, b, c, d):
    """Cubic"""
    return  a + (b + (c + d*x) * x) * x

def poly4(x, a, b, c, d, e):
    """Quartic"""
    return  a + (b + (c + (d + e*x) * x) * x) * x

polytypes = (poly0, poly1, poly2, poly3, poly4)

class intresult(object):
    """Record integration results"""

    def __init__(self, da):
        self.dataarray = da
        self.yoffsets = None
        self.yscale = 1.0

parsearg = argparse.ArgumentParser(description='Calculate continuum polynomial(s)')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data controlfile')
parsearg.add_argument('--save', action='store_true', help='Clear existing results and save')
parsearg.add_argument('--indiv', action='store_true', help='Do each spectrum individually')
parsearg.add_argument('--order', default=2, type=int, help='Order of polynomial for continuum (default 2)')
parsearg.add_argument('--entirespec', action='store_true', help="Use entire spectrum, don't bother with ranges")

SPC_DOC_ROOT = "spcctrl"
SPC_DOC_NAME = "SPCCTRL"

res = vars(parsearg.parse_args())
rf = res['rangefile']
sf = res['specfile']
save = res['save']
indiv = res['indiv']
entire = res['entirespec']
order = res['order']

if not (0 < order < len(polytypes)):
    print "Invalid order", order, "of polynomial, supporting 1 to", len(polytypes)-1, "currently"
    sys.exit(99)

polfunc = polytypes[order]

if not entire and rf is None:
    print "No range file specified"
    sys.exit(100)

if sf is None:
    print "No spec data control specified"
    sys.exit(101)

# Load up spectrum control file

try:
    doc, root = xmlutil.load_file(sf, SPC_DOC_ROOT)
    spclist = specdatactrl.SpecDataList(sf)
    cnode = xmlutil.find_child(root, "cfile")
    spclist.load(cnode)
except xmlutil.XMLError as e:
    print "Load control file XML error", e.args[0]
    sys.exit(50)

# Load up range file if we are using it

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

# Load up all the data files

print "Loading data files"

try:
    spclist.loadfiles()
except specdatactrl.SpecDataError as e:
    print "Loading spectral data error", e.args[0]
    sys.exit(53)

print "load complete"

# If we are regenerating this, clear existing stuff and print appropriate messages
# Likewise discount data markers

anychanges = 0
if save:
    if spclist.reset_x():
        print "Reset global X scale/offset"
        anychanges += 1
    if spclist.reset_indiv_x():
        print "Reset individual X scale/offset"
        anychanges += 1
    if spclist.reset_y():
        print "Reset global Y scale/offsets"
        anychanges += 1
    if spclist.reset_indiv_y():
        print "Reset individual Y scale/offsets"
        anychanges += 1

allxvalues = np.empty((0,),dtype=np.float64)
allyvalues = np.empty((0,),dtype=np.float64)
resultdict = dict()

# OK do the business

for dataset in spclist.datalist:
    if dataset.modbjdate in resultdict:
        print "OOPS mod bjdate of", dataset.modbjdate, "dupllicated in data"
        sys.exit(200)
    try:
        xvalues = dataset.get_xvalues(False)
        yvalues = dataset.get_yvalues(False)
    except specdatactrl.SpecDataError:
        continue

    # If doing ranges cut down X and Y values to the ones in the range

    if not entire:
        contrx, contry = selectrange(contr, xvalues, yvalues)
        contbx, contby = selectrange(contb, xvalues, yvalues)
        xvalues = np.concatenate((contbx, contrx))
        yvalues = np.concatenate((contby, contry))

    # Subtract reference wavelength from x values

    xvalues -= spclist.refwavelength

    allxvalues = np.concatenate((allxvalues, xvalues))
    allyvalues = np.concatenate((allyvalues, yvalues))

    resitem = intresult(dataset)    
    offsets, errors = so.curve_fit(polfunc, xvalues, yvalues)

    minx = np.min(xvalues)
    maxx = np.max(xvalues)
    meanval = (polynomial.areapol(maxx, offsets) - polynomial.areapol(minx,offsets)) / (maxx - minx)
        
    # Scale is reciprocal of mean value

    resitem.yscale = 1.0 / meanval

    # Subtract the mean value from the first offset so when we subtract that again and then multiply
    # back by the scale, we end up with a continuum of 1.

    offsets[0] -= meanval
    resitem.yoffsets = offsets
    resultdict[dataset.modbjdate] = resitem

# OK now work out the overall curve fit.

offsets, errors = so.curve_fit(polfunc, allxvalues, allyvalues)
minx = np.min(allxvalues)
maxx = np.max(allxvalues)
meanval = (polynomial.areapol(maxx, offsets) - polynomial.areapol(minx,offsets)) / (maxx - minx)

# Scale is reciprocal of mean value

overall_yscale = 1.0 / meanval

# Subtract the mean value from the first offset so when we subtract that again and then multiply
# back by the scale, we end up with a continuum of 1.

xp = np.linspace(minx, maxx, 200)
yp = polynomial.polyeval(xp, offsets)
xp += spclist.refwavelength
fig = plt.gcf()
fig.canvas.set_window_title('Continuum polynomial prior to scaling')
plt.xlabel('Wavelength Angstroms')
plt.plot(xp, yp, label='Continuum polynomial')
plt.legend()

offsets[0] -= meanval

# OK now write the values up if we are saving them

if save:

    spclist.set_yscale(overall_yscale)
    spclist.set_yoffset(offsets)

    print "Y scale is set to", spclist.yscale
    if indiv:
        dates = resultdict.keys()
        dates.sort()        
        for d in dates:
            rd = resultdict[d]
            rdata = rd.dataarray
            rdata.yoffset = rd.yoffsets
            rdata.yscale = rd.yscale

    try:
        doc, root = xmlutil.init_save(SPC_DOC_NAME, SPC_DOC_ROOT)
        spclist.save(doc, root, "cfile")
        xmlutil.complete_save(sf, doc)
    except xmlutil.XMLError as e:
        print "XML error -", e.args[0]

print "At end of calculation, mean value =", meanval
print "Overall Scale =", overall_yscale
print "Offsets:"
for off in offsets:
    print "%#.16g" % off
plt.show()
sys.exit(0)

