# Module to generate a trial of a periodic signal with assorted noise, run L-S on the result
# and determine the percentage error.

import siggen
import noise
import numpy as np
from gatspy.periodic import LombScargle
import argmaxmin

def gen_recover_period(prange, ntimes, npers, randtimes = 0.0, rantnormp = 0.0, snrnoise = 0.0, normpropnoise = 0.0, samples = 100):
    """Generate some periodic data and then try to recover the maximum period under various conditions.
    
    prange = period to analyse (kicking off with a single period) with lower bound and upper bound for search
    ntimes number of times to generate signal for
    npers number of periods (possibly fractional) to scan for
    randtimes whether we vary the sample times 0.0 none, 1 probably max
    rantnormp variation in times proortion between uniform (0.0) and gaussian (1.0)
    snr signal to noise ration of noise to add 0 for None
    normpropnoise proportion of noise uniform (0.0) or gaussian (1.0)
    samples is the number of samples for the periodogram
    
    Return fractional error"""
    
    lbound, period, ubound = prange
    
    timelist, amps = siggen.siggen(period, ntimes=ntimes, npers=npers, randv=randtimes, unorm=rantnormp, randphase=True)
    
    if snrnoise > 0.0:
        amps = noise.noise(amps, snrnoise, normpropnoise)
    
    # OK now lets do our stuff
    
    model = LombScargle().fit(timelist, amps, 0.001)
    periods = np.linspace(lbound, ubound, samples)
    pgram = model.periodogram(periods)
    
    # Find maximum
    
    maxes = argmaxmin.maxmaxes(periods, pgram)
    if len(maxes) == 0:
        return  1.0
    
    maxp = periods[maxes[0]]
    return abs(maxp - period) / period
