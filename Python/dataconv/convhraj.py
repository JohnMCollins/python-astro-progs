#! /usr/bin/python

import os
import os.path
import sys
import string
import glob
import argparse
import re
import datetime
import astropy.time

def getabsdir(arg, name, envk):
    """Get absolute path from arg directory.

    If none or blank try environment var given"""

    if arg is None or len(arg) == 0:
        try:
            arg = os.environ[envk]
        except KeyError:
            print name, "argument not defined and", envk, " env not set"
            sys.exit(10)
    cdir = os.getcwd()
    try:
        os.chdir(arg)        
    except OSError:
        print name, "argument", arg, "not valid directory"
        sys.exit(11)
    result = os.getcwd()
    os.chdir(cdir)
    return  result

def getabsfile(arg, srcd, name, envk):
    """Get absolute file name from source directory

    Or just use that if not specified"""

    if arg is None or len(arg) == 0:
        try:
            arg = os.environ[envk]
        except KeyError:
            print name, "argument not defined and", envk, " env not set"
            sys.exit(13)
    if not os.path.isabs(arg):
        arg = os.path.join(srcd, arg)
    if not os.path.isfile(arg):
        print name, "argument", arg, "is not a file"
        sys.exit(14)
    return arg

parsearg = argparse.ArgumentParser(description='Convert HRAJ data, adding in JD corrections')

parsearg.add_argument('--src', type=str, help='Source Directory')
parsearg.add_argument('--dest', type=str, help='Dest Directory')
parsearg.add_argument('--obs', type=str, help='Observation times file', default='Proxima.rv')
parsearg.add_argument('--jdc', type=str, help='Date conversion file', default='Corrections.txt')
parsearg.add_argument('--prefix', type=str, help='Prefix for output files', default='Outobs_')
parsearg.add_argument('--suffix', type=str, help='Suffix for output files', default='.asc')
parsearg.add_argument('--otimes', type=str, help='Observations file name', default='observation_times')
parsearg.add_argument('--snum', type=float, help='Y scaling numerator', default=1.0)
parsearg.add_argument('--sden', type=float, help='Y scaling denominator', default=1.0)

res = vars(parsearg.parse_args())

jdc = res['jdc']

srcdir = getabsdir(res['src'], 'Source directory', 'CONVSRCD')
destdir = getabsdir(res['dest'], 'Dest directory', 'CONVDESTD')
if srcdir == destdir:
    print "Cannot have source = dest dir", srcdir
    sys.exit(12)

obsfile = getabsfile(res['obs'], srcdir, "Observation file", 'CONVOBS')
jdcfile = getabsfile(res['jdc'], srcdir, "Date conversion file", 'CONVDATE')

prefix = res['prefix']
suffix = res['suffix']
otimes = res['otimes'] + suffix

# Get Y scaling factor

Yscaling = res['snum'] / res['sden']
print "Y scale =", Yscaling

os.chdir(srcdir)
flist = glob.glob('*.067')
flist.sort()
reparser = re.compile('^.*\.(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)\.(\d+)')

filelist = []
for f in flist:
    mtch = reparser.match(f)
    mg = map(lambda x: int(x), mtch.groups())
    t = datetime.datetime(mg[0], mg[1], mg[2], mg[3], mg[4], mg[5], mg[6]*1000)
    filelist.append((f, t))

# Read in obs data file

inf = open(obsfile,'r')

tparser = re.compile('[\d.]+')

obslist = []

for line in inf:
    line = string.strip(line)
    mtch = tparser.match(line)
    if not mtch: continue
    jdate = float(mtch.group(0))
    t = astropy.time.Time(jdate, format='mjd', scale='utc')
    obslist.append((jdate, t.datetime))

inf.close()

# Read in corrections file

datecorr = dict()

inf = open(jdcfile, 'r')
tparser = re.compile('\s*([\d.]+)\s+([\d.]+)\s+(-?[\d.]+)')
for line in inf:
    mtch = tparser.match(line)
    if not mtch: continue
    # Use char version of jdate to look up though
    datecorr[mtch.groups()[0]] = map(lambda x: float(x), mtch.groups())
inf.close()

# Compare dates

if len(obslist) != len(filelist):
    print "Difference in length, obs file =", len(obslist), "number of files =", len(filelist)
    sys.exit(20)
if len(datecorr) != len(obslist):
    print "Difference in length corrections =", len(datecorr), "obs file =", len(obslist)

for obsd, obsf in zip(obslist, filelist):
    datediff = obsd[1] - obsf[1]
    print "%s: %d days %d hours %d minutes %d seconds diff" % (obsd[1].ctime(), datediff.days, datediff.seconds/3600, (datediff.seconds/60) % 60, datediff.seconds % 60)

# Remove any previous files

os.chdir(destdir)
os.system("rm -f *")

# Create obs data file and set up to write to it

obsdf = open(otimes, 'w')
fnum = 1

tparser = re.compile('\s*([\d.]+)\s+([\d.]+)')

for obsd, obsf in zip(obslist, filelist):
    fname = obsf[0]
    fullname = os.path.join(srcdir, fname)
    jdate = obsd[0]
    fjdate = "%.6f" % jdate
    try:
        rjdate, mjdate, vel = datecorr[fjdate]
    except KeyError:
        print "Could not find JDate", fjdate
        rjdate, mjdate, vel = (jdate, jdate, 0.0)
    outfname = ((prefix + "%.3d") % fnum) + suffix
    fnum += 1
    try:
        inf = open(fullname,'r')
    except IOError:
        print "Could not open",fullname
        continue
    try:
        outf = open(outfname, 'w')
    except IOError:
        print "Could not create", outfname
        inf.close()
        continue
    
    # Write line to index file: file, jdate, modjdate, vel

    obsdf.write("%s %.6f %.6f %.6f\n" % (outfname, rjdate, mjdate, vel))

    # Now copy data to the output file, scaling Y as we go
    # Later we'll worry about error bars

    try:
        for line in inf:
            line = string.strip(line)
            if len(line) == 0: continue
            mtch = tparser.match(line)
            if not mtch:
                raise Exception("match fail in " + fname)
            xvalue, yvalue = map(lambda x: float(x), mtch.groups())
            yvalue *= Yscaling
            outf.write("%.6f %.6f %.6f\n" % (xvalue, yvalue, 0.0))
    except Exception as e:
        print e.args[0]
    inf.close()
    outf.close()

            
    

        
