#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse
import numpy as np
import noise

TWOPI = 2.0 * np.pi

class sigdets(object):
    
    """Represent parts of a signal"""
    
    def __init__(self):
        self.period = 0.0
        self.amplitude = 0.0
        self.phase = 0.0
        self.col = [False, False, False]
    
    def parse(self, arg):
        """Parse argument of form period:amplitude:phase:column
        
        amplitude is 1 if omitted. Phase is a proportion of 2pi column is 1 2 3 or omitted to mean all"""
        
        bits = string.split(arg, ':')
        if len(bits) > 4:
            print "Cannot understand period arg", arg
            sys.exit(20)
        try:
            self.period = float(bits[0])
            if len(bits) == 4:
                coln = int(bits[3])
                self.col = [False, False, False]
                self.col[coln] = True
            else:
                self.col = [True, True, True]
            if len(bits) > 2:
                self.phase = float(bits[2]) * TWOPI
            else:
                self.phase = 0.0
            if len(bits) > 1:
                self.amplitude = float(bits[1])
            else:
                self.amplitude = 1.0
        except ValueError as e:
            print "Problems with period arg", arg, e.args[0]
            sys.exit(21)
        except IndexError:
            print "Cannot understand column number in", arg
            sys.exit(22)

    def apply(self, times, coln):
        """Actually generate the signal specified for the given column"""
        
        if not self.col[coln] or self.period == 0.0:
            return np.zeros_like(times)
        
        return self.amplitude * np.sin(self.phase + times * TWOPI / self.period)

parsearg = argparse.ArgumentParser(description='Generate periodic data fitting times', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('signals', type=str, help='Period:amplitude:phase[:col]', nargs='+')
parsearg.add_argument('--snr', type=float, default=0.0, help='SNR of noise to add 0=none (default)')
parsearg.add_argument('--gauss', type=float, default=0.0, help='Proportion uniform to gauss noise 0=all uniform 1=all gauss')
parsearg.add_argument('--ewfile', type=str, help='EW file to take times from', required=True)
parsearg.add_argument('--outfile', help='Output file name', type=str, required=True)

res = vars(parsearg.parse_args())

siglist = res['signals']
snr = res['snr']
gauss = res['gauss']
ewfile = res['ewfile']
outfile = res['outfile']

if gauss < 0.0 or gauss > 1.0:
    print "Invalid gauss proportion, should be between 0 and 1"
    sys.exit(10)

try:
    ewf = np.loadtxt(ewfile, unpack = True)
except IOError as e:
    print "Unable to open", ewfile, "error was", e.args[1]
    sys.exit(11)
except ValueError as e:
    print "Conversion error in", ewfile, "error was", e.args[0]
    sys.exit(12)

signals = []
for sig in siglist:
    nsig = sigdets()
    nsig.parse(sig)
    signals.append(nsig)

col2 = np.zeros_like(ewf[1])
col4 = col2 + 1.0
col6 = col2 + 1.0

for sig in signals:
    col2 += sig.apply(ewf[1], 0)
    col4 += sig.apply(ewf[1], 1)
    col6 += sig.apply(ewf[1], 2)

if snr != 0:
    col2 = noise.noise(col2, snr, gauss)
    col4 = noise.noise(col4, snr, gauss)
    col6 = noise.noise(col6, snr, gauss)
ewf[2] = col2
ewf[4] = col4
ewf[6] = col6

np.savetxt(outfile, ewf.transpose())
