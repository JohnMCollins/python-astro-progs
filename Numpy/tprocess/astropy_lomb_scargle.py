#! /usr/bin/env python

"""Run LS on a list of times and amplitudes"""

import sys
import argparse
import numpy as np
import numpy.random as random
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.timeseries import LombScargle
import remgeom
import argmaxmin
import miscutils

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Generate a LS periodogram', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Data files to process or use stdin')
parsearg.add_argument('--precentre', action='store_true', help='Precentre to maan')
parsearg.add_argument('--minperiod', type=float, help='Minimum period to accept')
parsearg.add_argument('--maxperiod', type=float, help='Maximum period to accept')
parsearg.add_argument('--npowers', type=int, default=1, help='Number of powers to highlight')
parsearg.add_argument('--nfit', type=int, default=1, help='Number of peaks fo combine for fit')
parsearg.add_argument('--powermin', type=float, default=0.1, help='Minimum power to highlight')
parsearg.add_argument('--toffset', type=float, default=0.1, help='Offset to add to peak labels')
parsearg.add_argument('--dprec', type=int, default=3, help='Precision for days')
parsearg.add_argument('--xlabel', type=str, default='Period (days)', help='Label for X axis')
parsearg.add_argument('--ylabel', type=str, default='Power', help='Label for Y axis')
parsearg.add_argument('--nophase', action='store_false', help='Do not plot phase fold')
parsearg.add_argument('--scxlabel', type=str, default='Days into period', help='Label for scatter X axis')
parsearg.add_argument('--scylabel', type=str, default='Flux', help='Label for scatter Y axis')
parsearg.add_argument('--marker', type=str, default='.', help='Marker on scatter plot')
parsearg.add_argument('--sccolour', type=str, default='b', help='Scatter colour')
parsearg.add_argument('--scalpha', type=float, default=1.0, help='Alpha for scatter')
parsearg.add_argument('--sctrim', type=float, help='Number of std devs to trim points in scatter')
parsearg.add_argument('--fitcolour', type=str, default='k', help='Colour for fit')
parsearg.add_argument('--fitalpha', type=float, default=1.0, help='Alpha for fit')
parsearg.add_argument('--multi', action='store_true', help='Use multi file names always')
parsearg.add_argument('--winfunc', action='store_true', help='Generate window functionj')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
input_files = resargs['files']
precentre = resargs['precentre']
minperiod = resargs['minperiod']
maxperiod = resargs['maxperiod']
npowers = resargs['npowers']
nfit=resargs['nfit']
powermin = resargs['powermin']
toffset = resargs['toffset'] * u.day
dprec = resargs['dprec']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
scxlab = resargs['scxlabel']
scylab = resargs['scylabel']
marker = resargs['marker']
sccolour = resargs['sccolour']
scalpha = resargs['scalpha']
fitcolour = resargs['fitcolour']
fitalpha = resargs['fitalpha']
sctrim = resargs['sctrim']
winfunc = resargs['winfunc']
nophase = resargs['nophase'] or winfunc
multi = resargs['multi'] or len(input_files) > 1
figout = rg.disp_getargs(resargs)

if len(input_files) == 0:
    input_files = ('/dev/fd/0', )

file_number = errors = 0

for input_file in input_files:
    file_number += 1
    try:
        inarray = np.loadtxt(input_file, unpack=True)
    except OSError as e:
        print("Could not open", input_file, "error was", e.args[-1], file=sys.stderr)
        errors += 1
        continue
    if inarray.shape[0] == 3:
        times, amps, errs = inarray
    else:
        times, amps = inarray
        errs = None

    times_day = times * u.day
    lskws = dict()
    
    if winfunc:
        amps = np.full_like(amps, 1.0) + random.normal(size=amps.size, scale=1e-6)
        errs = None #np.zeros_like(errs) + random.normal(size=errs.size, scale=1e-7)
    else:    
        if precentre:
            if errs is None:
                lskws['fit_mean'] = True
            else:
                lskws['center_data'] = True

    Lomb = LombScargle(times_day, amps, errs, **lskws)

    lskws = dict()
    if minperiod is not None:
        lskws['maximum_frequency'] = 1.0 / (minperiod * u.day)
    if maxperiod is not None:
        lskws['minimum_frequency'] = 1.0 / (maxperiod * u.day)

    freq, power = Lomb.autopower(method='slow', **lskws)
    periods = 1 / freq
    power_peak_locs = argmaxmin.maxmaxes(periods.value, power)
    pltfig = rg.plt_figure()
    plt.plot(periods, power)
    n = 0
    for loc in power_peak_locs:
        if n >= npowers:
            break
        n += 1
        plt.text((periods[loc] + toffset).value, power[loc], "{val:.{prec}g}".format(val=periods[loc].value, prec=dprec))
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.tight_layout()
    if nophase:
        remgeom.end_figure(pltfig, figout, file_number, multi)
    else:
        fout = figout
        if fout is not None:
            fout = miscutils.removesuffix(figout) + "_pg"
        remgeom.end_figure(pltfig, fout, file_number, multi)
        pltfig2 = rg.plt_figure()
        topperiod = periods[power_peak_locs[0]]
        best_frequency = 1.0 / topperiod
        sc_x = times % topperiod.value
        sc_amps = amps
        if sctrim is not None:
            w = np.abs(sc_amps - sc_amps.mean()) < sctrim * sc_amps.std()
            sc_x = sc_x[w]
            sc_amps = sc_amps[w]
        plt.scatter(sc_x, sc_amps, marker=marker, color=sccolour, alpha=scalpha)
        plt.gca().get_yaxis().get_major_formatter().set_scientific(False)
        if nfit > 0 and fitalpha > 0.0:
            t_fit = np.linspace(0, 1) * topperiod
            # y_fit = Lomb.model(t_fit, best_frequency)
            # theta = Lomb.model_parameters(best_frequency)
            offset = Lomb.offset()
            y_fit = np.zeros(shape = t_fit.shape)
            for n, fr in enumerate(power_peak_locs):
                if n >= nfit:
                    break
                per = 1.0 /periods[fr]
                theta = Lomb.model_parameters(per)
                design_matrix = Lomb.design_matrix(per, t_fit)
                y_fit += np.array(design_matrix.dot(theta))
            plt.plot(t_fit, offset + y_fit, color=fitcolour, alpha=fitalpha)
        plt.xlabel(scxlab)
        plt.ylabel(scylab)
        plt.tight_layout()
        if fout is not None:
            fout = miscutils.removesuffix(figout) + "_pfold"
        remgeom.end_figure(pltfig2, fout, file_number, multi)

remgeom.end_plot(figout)
