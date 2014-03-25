#! /local/home/jcollins/lib/anaconda/bin/python

# Integrate the continuum to give an overall value for normalising the intensity of a spectrum

import argparse
import os.path
import sys

import specdatactrl
import datarange
import xmlutil
import meanval

parsearg = argparse.ArgumentParser(description='Calculate continuum')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data controlfile')
parsearg.add_argument('--renorm', action='store_true', help='Rescale intensity to normalise')

SPC_DOC_ROOT = "spcctrl"

res = vars(parsearg.parse_args())
rf = res['rangefile']
sf = res['specfile']
renorm = res['renorm']

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
n = 0
for dataset in spclist.datalist:
    try:
        xvalues = dataset.get_xvalues(False)
        yvalues = dataset.get_yvalues(False)
    except specdatactrl.SpecDataError:
        continue
    n += 1
    totred += meanval.mean_value(contr, xvalues, yvalues)
    totblue += meanval.mean_value(contb, xvalues, yvalues)

print "Av red=",totred/float(n),"Av blue=",totblue/float(n),"overall=",(totred+totblue)/float(n*2)


