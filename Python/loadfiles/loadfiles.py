#! /usr/bin/python

import os
import os.path
import sys
import string
import glob
import argparse
import re
import cPickle

import specarray
import xmlutil

# If we don't have a filename, remember to plug it into the data

Had_filename = False

# These functions are invoked by looking up option keywords

def parse_fn(val, fn):
    """Parse file name, checking it corresponds to the one we are looking at"""
    global Had_filename
    Had_filename = True
    if val != fn:
        print "Files out of sync, expecting", fn, "but found", val
        sys.exit(50)
    return val

def parse_jd(val, fn):
    """Parse Julian date, checking it looks right"""
    if val[0:2] != "24":
        print "Do not believe", val, "is Julian date"
        sys.exit(51)
    return float(val[2:]) - 0.5

def parse_mjd(val, fn):
    """Parse Modified Julian date, checking it looks right"""
    d = float(val)
    if d >= 2400000.0:
        print "Do not believe", val, "is modified Julian date"
        sys.exit(52)
    return d

def parse_float(val, fn):
    """Parse a float with no checks"""
    return float(val)

# Lookup routine for field names in input files giving field name in constructor and parse routine
# The field names in "--obsfields" and "--specfields" arguments are the key to the dictionary
# The two-valued results are the parameter name in the constructors in specarray for Specdatum or
# Specarray and the function to be used to parse them

Funclookup = dict(fn=('filename', parse_fn),
                  jd=('modjdate', parse_jd),
                  mjd=('modjdate', parse_mjd),
                  bd=('baryjdate', parse_jd),
                  mbd=('baryjdate', parse_mjd),
                  rv=('radialvel', parse_float),
                  x=('xval', parse_float),
                  y=('yval', parse_float),
                  yerr=('yerr', parse_float))

parsearg = argparse.ArgumentParser(description='Convert HRAJ data, adding in JD corrections')

parsearg.add_argument('--src', type=str, help='Source Directory')
parsearg.add_argument('--obsfile', type=str, help='Observation times file')
parsearg.add_argument('--obsfields', type=str, help='Fields in observation times file')
parsearg.add_argument('--specprefix', type=str, help='Prefix of spectrum data files')
parsearg.add_argument('--specfields', type=str, help='Fields in spectrum data files')
parsearg.add_argument('--output', type=str, help='Output data file', default='Output')
parsearg.add_argument('--xmlfmt', action='store_true', help='Store in XML format (as opposed to pickle)')

# Check we can read everything etc

res = vars(parsearg.parse_args())

srcdir = res['src']
outputfile = res['output']
if res['xmlfmt']:
    suffix = '.xml'
else:
    suffix = '.pick'
try:
    if outputfile[outputfile.rindex(suffix):] != suffix:
        raise ValueError('x')
except ValueError:
    outputfile += suffix

if os.path.isfile(outputfile):
    print "Not overwriting previous output file"
    sys.exit(10)

# If we provided a source directory, switch to it, but if the output file is
# relative (no leading /) we assume that the results should go to the current
# directory

if srcdir is not None and len(srcdir) != 0:
    if not os.path.isabs(outputfile):
        outputfile = os.path.join(os.getcwd(), outputfile)
    try:
        os.chdir(srcdir)
    except OSError:
        print srcdir, "is not a valid directory"
        sys.exit(10)

# Open the observation times file

obsfile = res['obsfile']
if obsfile is None or len(obsfile) == 0:
    print "No observation times file given"
    sys.exit(11)

try:
    obsfin = open(obsfile)        
except IOError:
    print "Could not open obs times file", obsfile
    sys.exit(12)

# Decode the observation fields argument

obsfields = res['obsfields']
if obsfields is None or len(obsfields) == 0:
    print "No obeservation file fields given"
    sys.exit(13)
try:
    obsfields = [Funclookup[k] for k in string.split(obsfields, ',')]
except KeyError as k:
    print "Invalid field name", k.args[0], "in observation file fields"
    sys.exit(14)

# Repeat for the spectral data files, for which we provide a prefix

flistname = res['specprefix']
if flistname is None or len(flistname) == 0:
    print "No spectrum data prefix given"
    sys.exit(15)

Flist = glob.glob(flistname + '*')
if len(Flist) == 0:
    print "Cannot find files beginning", flistname
    sys.exit(16)
Flist.sort()

specfields = res['specfields']
if specfields is None or len(specfields) == 0:
    print "No spectrum data fields given"
    sys.exit(17)
try:
    specfields = [Funclookup[k] for k in string.split(specfields, ',')]
except KeyError as k:
    print "Invalid field name", k.args[0], "in spectrum data file fields"
    sys.exit(18)

# OK do the business
# Build up a vector of Specarrays in "Results"

Results = specarray.Specarraylist()
fieldparser = re.compile('\s*')

# Loop over each line in observation times

for line in obsfin:
    line = string.strip(line)
    if len(line) == 0: continue

    # Pull the next file off the list

    try:
        specfile = Flist.pop(0)
    except IndexError:
        print "Too few spectrum files found"
        sys.exit(19)

    # Build a vector of fields checking that we've got the right number

    parts = fieldparser.split(line)
    if len(obsfields) != len(parts):
        print "Unexpected number of fields in obs data, expected", len(obsfields), "read", len(parts)
        sys.exit(20)

    # Tricky code warning!
    # This builds up a function call of the form argname=xyz by construction of a dictionary and using the syntax
    # fn(**dict) to generate the call

    dkw = dict()
    for fn, arg in zip(obsfields, parts):
        kw, parsefn = fn
        dkw[kw] = parsefn(arg, specfile)
    if not Had_filename: dkw['filename'] = specfile
    sa = specarray.Specarray(**dkw)

    # Basically repeat all that for the spectral data file selected

    try:
        specfin = open(specfile)
    except IOError:
        print "Could not open spectral data file", specfile
        sys.exit(21)

    for sline in specfin:
        sline = string.strip(sline)
        if len(sline) == 0: continue
        parts = fieldparser.split(sline)
        if len(specfields) != len(parts):
            print "Unexpected number of fields in spectral data file", specfile, "expected", len(specfields), "read", len(parts)
            sys.exit(22)
        skw = dict()
        for fn, arg in zip(specfields, parts):
            kw, parsefn = fn
            skw[kw] = parsefn(arg, specfile)
        sa.append(specarray.Specdatum(**skw))

    # Finished, close spectral data file, append results to Specarray
    specfin.close()
    Results.append(sa)

# All done, close file

obsfin.close()

if res['xmlfmt']:
    # Generate XML file

    (doc, root) = xmlutil.init_save("SPECDATA", "specdata")
    Results.save(doc, root, "speclist")

    try:
        xmlutil.complete_save(outputfile, doc)
    except xmlutil.XMLerror as e:
        print e.args[0]
        sys.exit(200)
else:
    try:
        outf = open(outputfile, 'w')
        cPickle.dump(Results, outf)
    except IOError as e:
        print e.args[0]
        sys.exit(200)



