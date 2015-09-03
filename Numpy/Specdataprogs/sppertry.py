#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse
import threading
import datetime
import numpy as np
from astroML.time_series import lomb_scargle as lsas
from gatspy.periodic import LombScargle
import periodarg
import argmaxmin

TWOPI = 2.0 * np.pi

resultvec = []

def trialfor(p1, p2):
    """Try L-S routine for periods p1 and p2, other parameters given by globals"""
    
    global trialfreqs, trialperiods, usegatspy, obstimes, amp1, amp2, usegatspy, phases, maxnum, errbar, errs
    global resultvec, rounding
    global TWOPI

    rs = set()
    for p in phases:
        sig = amp1 * np.sin(obstimes * TWOPI / p1) + amp2 * np.sin(p + obstimes * TWOPI / p2)
        if usegatspy:
            model = LombScargle().fit(obstimes, sig, errnar)
            pgram = model.periodogram(trialperiods)
        else:
            pgram = lsas(obstimes, sig, errs, trialfreqs)
        maxima = argmaxmin.maxmaxes(trialperiods, pgram)
        if len(maxima) > maxnum:
            maxima = maxima[0:maxnum]
        rs |= set(np.round(trialperiods[maxima], rounding))
    rs = list(rs)
    rs.sort()
    resultvec.append((p1, p2, rs))

class p2thread(threading.Thread):
    def __init__(self, threadID, p1):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = string.replace("p1_%#.6g" % p1, '.', '_')
        self.p1 = p1
    def run(self):
        global periods2
        for p2 in periods2:
            trialfor(self.p1, p2)

parsearg = argparse.ArgumentParser(description='Generate periodic data fitting times')
parsearg.add_argument('ewfile', type=str, help='EW file to take times from', nargs=1)
parsearg.add_argument('--per1', help='First period range', type=str, required=True)
parsearg.add_argument('--per2', help='Second period range', type=str, required=True)
parsearg.add_argument('--amp1', type=float, default=1.0, help='Amplitude first period')
parsearg.add_argument('--amp2', type=float, default=1.0, help='Amplitude second period')
parsearg.add_argument('--pstep', help='Phase step', type=float, default=0.01)
parsearg.add_argument('--periods', type=str, default="20d:.01d:100d", help='Periods to search for as start:step:stop or start:stop/number')
parsearg.add_argument('--error', type=float, default=.01, help='Error bar')
parsearg.add_argument('--gatspy', action='store_true', help='Use gatspy rather than AstroML')
parsearg.add_argument('--outfile', help='Output file prefix to save plot', type=str)
parsearg.add_argument('--maxnum', type=int, default=3, help='Number of maxima to search for')
parsearg.add_argument('--round', type=int, default=6, help='Digits to round to')
parsearg.add_argument('--nice', type=int, default=10, help='Niceness')

resargs = vars(parsearg.parse_args())
ewfile = resargs['ewfile'][0]
usegatspy = resargs['gatspy']

try:
    trialperiods = periodarg.periodrange(resargs['periods'])
    periods1 = periodarg.periodrange(resargs['per1'])
    periods2 = periodarg.periodrange(resargs['per2'])
except ValueError as e:
    print e.args[0]
    sys.exit(10)

trialfreqs = TWOPI / trialperiods

amp1 = resargs['amp1']
amp2 = resargs['amp2']
pstep = resargs['pstep']
errbar = resargs['error']
outfile = resargs['outfile']
maxnum = resargs['maxnum']
rounding = resargs['round']
niceness = resargs['nice']

os.nice(niceness)

try:
    ewf = np.loadtxt(ewfile, unpack = True)
except IOError as e:
    print "Unable to open", ewfile, "error was", e.args[1]
    sys.exit(13)
except ValueError as e:
    print "Conversion error in", ewfile, "error was", e.args[0]
    sys.exit(14)

obstimes = ewf[1]
obstimes -= obstimes[0]
phasesr = np.arange(0.0, 1.0, pstep)
phases = phasesr  * TWOPI
errs = np.zeros_like(obstimes) + errbar

n = 1
tlist = []
for p1 in periods1:
    th = p2thread(n, p1)
    tlist.append(th)
    n += 1

stime = datetime.datetime.now()

for th in tlist:
    th.start()

for th in tlist:
    th.join()

etime = datetime.datetime.now()
tdiff = etime - stime
secs = tdiff.seconds
mins = secs / 60
secs %= 60
hours = mins / 60
mins %= 60
print "Finished after", hours, "hours", mins, "minutes", secs, "seconds"

# Sort results by second then first frequency

resultvec.sort(key=lambda x: x[1])
resultvec.sort(key=lambda x: x[0])

outf = sys.stdout
if outfile is not None:
    outf = open(outfile, "w")

for r in resultvec:
    outf.write("%#.4g:%#.4g:\n" % (r[0], r[1]))
    for p in r[2]:
        outf.write("\t%#.4g\n" % p)
