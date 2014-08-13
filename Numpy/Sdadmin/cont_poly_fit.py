# Polynomial fit for continuum

import scipy.optimize as so
import rangeapply

class PolyFitError(Exception):
    pass

def poly0(x, a):
    """Polynomial of order 0 of x with coeffs a"""
    return  a

def poly1(x, a, b):
    """Polynomial of order 1 of x with coeffs a b a + b*x"""
    return  a + b * x

def poly2(x, a, b, c):
    """Return a + b*x + c*x^2"""
    return  a + (b + c*x) * x

def poly3(x, a, b, c, d):
    """Cubic"""
    return  a + (b + (c + d*x) * x) * x

def poly4(x, a, b, c, d, e):
    """Quartic"""
    return  a + (b + (c + (d + e*x) * x) * x) * x

def poly5(x, a, b, c, d, e, f):
    """Quintic"""
    return  a + (b + (c + (d + (e + f*x) * x) * x) * x) * x

def poly6(x, a, b, c, d, e, f, g):
    """Sextic"""
    return  a + (b + (c + (d + (e + (f + g*x) * x) * x) * x) * x) * x

def poly7(x, a, b, c, d, e, f, g, h):
    """Septic"""
    return  a + (b + (c + (d + (e + (f + (g + h*x) * x) * x) * x) * x) * x) * x

polytypes = (poly0, poly1, poly2, poly3, poly4, poly5, poly6, poly7)

def cont_poly_fit(allxvalues, allyvalues, degree, refwl):
    """Fit polynomial to continuum

    allxvalues/allyvalues give the points
    degree gives the degree of polynomial to fit
    refwl gives the reference wavelength to subtract from x values"""

    offset_xvalues = allxvalues - ctrlfile.refwavelength
    coeffs, errors = so.curve_fit(polytypes[degree], offset_xvalues, allyvalues)
    return coeffs

