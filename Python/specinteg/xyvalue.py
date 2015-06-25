# Class for holding X,Y values
# Possibly later expansion

class XYvalue:
    """This class is used to hold (X,Y) data points

Possibly we'll do it another way later."""

    def __init__(self, xval = 0.0, yval = 0.0):
        self.xvalue = float(xval)
        self.yvalue = float(yval)

    def getxy(self):
        """Return tuple of x and y values)"""
        return (self.xvalue, self.yvalue)

    def __str__(self):
        """Return pretty representation of value"""
        return "%#14.8g %#14.8g" % (self.xvalue, self.yvalue)

def convert_to_xy(specarray, xcol, ycol):
    """Convert matrix given columns to list of XY values"""
    return [XYvalue(a[xcol], a[ycol]) for a in specarray]

def convert_to_matrix(specarray):
    """Reverse conversion above"""
    return [(a.xvalue, a.yvalue) for a in specarray]

