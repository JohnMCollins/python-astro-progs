#! /usr/bin/env python

import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import argparse
import string
import re

import lutdata

parsearg = argparse.ArgumentParser(description='Display flux profile file(s)', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('profile', type=str, nargs='+', help='Flux profile files')
parsearg.add_argument('--outfile', type=str, help='Output file if required')
parsearg.add_argument('--width', type=float, help='Width of figure', default=8.0)
parsearg.add_argument('--height', type=float, help='Height of figure', default=6.0)

resargs = vars(parsearg.parse_args())

args = resargs['profile']

plt.rcParams['figure.figsize'] = (resargs['width'], resargs['height'])

outf = resargs['outfile']
outpref = outsuff = None
outn = 0
if outf is not None and len(args) > 1:
    mtchs = re.match('(.*)\.(png|jpe?g)', outf)
    if not mtchs:
        print "Do not understand output file format expecting *.png or *.jpg"
        sys.exit(5)
    outpref = mtchs.group(1)
    outsuff = mtchs.group(2)
    outn = 1

for arg in args:
    try:
        pf = np.loadtxt(arg, unpack=True)
    except IOError as e:
        print "Could not open", lutf, "error was", e.args[1]
        if outn != 0: outn += 1
        continue
    if outf is None and os.fork() != 0:
        continue
    f = plt.figure()
    f.canvas.set_window_title(arg)
    plt.xlabel('Wavelength offset')
    plt.ylabel('Intensity')
    plt.plot(pf[0], pf[1])
    if outf is not None:
        if outn == 0:
            figname = outf
        else:
            figname = "%s_%.2d.%s" % (outpref, outn, outsuff)
            outn += 1
        try:
            plt.savefig(figname)
        except IOError as e:
            print "Could not save to", figname, "error was", e.args[1]
    else:
        plt.show()
