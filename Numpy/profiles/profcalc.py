# Profile calculations

import math
import numpy as np

Gaussdiv = 2.0 * math.sqrt(2.0 * math.log(2.0))
Lorentzdiv = 2.0 * math.sqrt(2.0)

def calcgauss(xvals, offset, scale, fhwm):
    """Calculate Gaussian profile"""
    sigma = fhwm / Gaussdiv
    return  scale * np.exp(-0.5 * ((xvals - offset) / sigma)**2)

def calclorentz(xvals, offset, scale, fhwm):
    """Calculate Lorentzian profile"""
    sigma = fhwm / Lorentzdiv
    return  scale / (1.0 + 0.5 * ((offset - xvals) / sigma) ** 2)

