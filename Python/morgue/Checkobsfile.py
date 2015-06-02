#! /local/home/jcollins/lib/anaconda/bin/python

# Integrate the H alpha peaks to get figures for the total values,
# assume continuum is normalised at 1 unless otherwise specified

import argparse
import os.path
import os
import sys
import glob
import re
import string
import datetime

import jdate

def disptime(dt):
    """Generate a time as a string"""
    return "%.2d:%.2d:%g" % (dt.hour, dt.minute, dt.second + dt.microsecond/1e6)

def dispdate(dt):
    """Generate a date as a string"""
    return "%.2d/%.2d/%.4d" % (dt.day, dt.month, dt.year)

parsearg = argparse.ArgumentParser(description='Confirm obs times file lines up with dates in file names')
parsearg.add_argument('--obsfile', type=str, help='Observation time file')
parsearg.add_argument('--specprefix', type=str, help='Spectrum file prefix', default='HARPS')
parsearg.add_argument('--directory', type=str, help='Directory to look in if not in obs file or current')
parsearg.add_argument('--okdays', type=float, default=1.5, help='Number of days out to winge about')
parsearg.add_argument('--column', type=int, default=1, help='Column number in obs file to find dates in (starting 1)')

res = vars(parsearg.parse_args())
obsfile = res['obsfile']
specprefix = res['specprefix']
direc = res['directory']
okdays = res['okdays']
column = res['column']-1

if obsfile is None:
    print "No observation times file given"
    sys.exit(100)

if okdays <= 0:
    print "Must have at least 1 for okdays"
    sys.exit(101)

if column < 0:
    print "Must have positive column number"
    sys.exit(102)

if os.path.isabs(obsfile):
    direc, obsfile = os.path.split(obsfile)
if direc is not None:
    try:
        os.chdir(direc)
    except OSError as e:
        print "Cannot select", direc, "error was", e.args[1]
        sys.exit(103)

try:
    obsf = open(obsfile)
except IOError as e:
    print "Cannot open obs file", obsfile, "error was", e.args[1]
    sys.exit(104)

fields = re.compile("\s+")

times = []

for line in obsf:
    bits = fields.split(string.strip(line))
    try:
        times.append(float(bits[column]))
    except IndexError:
        print "Cannot find column", column, "in obs file"
        sys.exit(105)
    except ValueError:
        print "Cannot convert", bits[column], "in obs file to float"
        sys.exit(106)

obsf.close()

if len(times) == 0:
    print "Nothing found in times file"
    sys.exit(107)

fnamedfull = re.compile("((?:19|20)\d\d)\D+(\d\d)\D+(\d\d)(?:\D+(\d\d)\D+(\d\d)\D+(\d\d)(\.\d+)?)?")

fnames = glob.glob(specprefix + "*")

if len(fnames) != len(times):
    print "Mismatch between files", len(fnames), "and obs times", len(times)
    sys.exit(108)

modified = times[0] < 1e6

fnames.sort()
errors = 0
for f,t in zip(fnames,times):
    fmatch = fnamedfull.search(f)
    if not fmatch:
        print "Cannot match file name", f, "with date"
        sys.exit(109)
    grps = fmatch.groups("0")
    dt = datetime.datetime(int(grps[0]), int(grps[1]), int(grps[2]), int(grps[3]), int(grps[4]), int(grps[5]), int(float(grps[6])*1e6))
    jd = jdate.datetime_to_jdate(dt, modified)
    if abs(t-jd) > okdays:
        if errors == 0:
            print "File\tTime\tObs\tTime"
        errors += 1
        jdt = jdate.jdate_to_datetime(t)
        print dispdate(dt) + "\t" + disptime(dt) + "\t" + dispdate(jdt) + "\t" + disptime(jdt)

if errors != 0:
    st = "errors"
    if errors == 1: st = "error"
    print errors, st
    sys.exit(1)

