#! /usr/bin/env python

# See what the error is on part periods for various S/N and a set observation time rate.

import sys
import argparse
import numpy as np
import periodtrial
import threading

class ProcessColumn(threading.Thread):
    
    # Thread to run all the SNRs over the given period fraction
    
    def __init__(self, colnum):
        threading.Thread.__init__(self)
        self.colnum = colnum
    
    def run(self):
        
        global X, Y, Z, tlock
        
        rowresult = []
        
        for row in xrange(0, nsnr):
            snr = 10.0 ** (Y[self.colnum][row] / 10.0)
            err = periodtrial.gen_recover_period(pqrange, nobs,
                                                 X[self.colnum][row], randtimes = 0.5,
                                                 snrnoise = snr, normpropnoise = 0.5, samples = searchn)
            rowresult.append(err)
        
        tlock.acquire()
        Z[self.colnum] = rowresult
        tlock.release()

parsearg = argparse.ArgumentParser(description='Track recovery of periods for given number of obs')
parsearg.add_argument('out', type=str, nargs=1, help='Output file name')
parsearg.add_argument('--period', type=float, default=10.0, help='Basic period')
parsearg.add_argument('--spread', type=float, default=5.0, help='Spread of periods for L-S search')
parsearg.add_argument('--searchn', type=int, default=1000, help='Number of periods in search')
parsearg.add_argument('--nobs', type=int, default=100, help='Number of observations')
parsearg.add_argument('--loper', type=float, default=1.0, help='Low multiple of number of periods')
parsearg.add_argument('--hiper', type=float, default=10.0,  help='High multiple of number of periods')
parsearg.add_argument('--nmults', type=int, default=100, help='Number of multiples of periods')
parsearg.add_argument('--losnr', type=float, default=0, help='Low SNR in dB')
parsearg.add_argument('--hisnr', type=float, default=30, help='High SNR in db')
parsearg.add_argument('--nsnr', type=int, default=100, help='Number of SNRs to try')

resargs = vars(parsearg.parse_args())

period = resargs['period']
spread = resargs['spread']
searchn = resargs['searchn']
nobs = resargs['nobs']
loper = resargs['loper']
hiper = resargs['hiper']
nmults = resargs['nmults']
losnr = resargs['losnr']
hisnr = resargs['hisnr']
nsnr = resargs['nsnr']

pqrange = (period-spread, period, period+spread)

partperrange = np.linspace(loper, hiper, nmults)
snrrange = np.linspace(losnr, hisnr, nsnr)

X, Y = np.meshgrid(partperrange, snrrange)
Z = np.zeros_like(X)

tlock = threading.Lock()

threadlist = []

for p in xrange(0, nmults):
    t = ProcessColumn(p)
    threadlist.append(t)
    t.start()

for t in threadlist:
    t.join()

np.save(resargs['out'][0], np.array((X,Y,Z)))
