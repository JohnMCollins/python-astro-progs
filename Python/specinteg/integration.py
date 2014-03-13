# Operations for integration

import xyvalue

class Integration_error(Exception):
    pass

def binary_search(data_array, xval):
    """Look for a given x value using binary search in supplied (X,Y) data array

    Return the (index, true) where it is found if found or
    (where to insert it, false) if not."""

    first = 0
    last = len(data_array)

    while first < last:
        mid = (last + first) / 2
        midx = data_array[mid].xvalue
        if midx == xval:
            return (mid, True)
        if midx < xval:
            first = mid + 1
        else:
            last = mid
    return (first, False)

def linear_interp(frompts, topts, forx):
    """Linearly interpolate between arg point arguments for supplied X value

    Return made-up arg point"""
    
    x0,y0 = frompts.getxy()
    x1,y1 = topts.getxy()
    resy = y0 + (forx - x0) * (y1 - y0) / (x1 - x0)
    return xyvalue.XYvalue(forx, resy)

def insert_interp_value(data_array, forx):
    """This makes up a point in an array of data with X / Y columns.

    The columns are assumed to be sorted on X values.
    If we find the X value the array is unchanged.
    Otherwise we invent a new point using linear interpolation and
    insert it into the array in the appropriate place

    In either case return the place where it went in or was found"""

    place, wasfound = binary_search(data_array, forx)
    
    # If was found, nothing to do

    if wasfound: return place

    # If off the end, we can't do it

    if place == 0 or place >= len(data_array):
        raise Integration_error("Interpolation value out of range")

    # Make up new value to insert

    newvalue = linear_interp(data_array[place-1], data_array[place], forx)

    data_array.insert(place, newvalue)
    return place

def integrate(data_array, fromx, tox):
    """Integrate data array in range given by fromx and tox"""

    # Be careful to insert starting_index first or we might offset ending_index

    starting_index = insert_interp_value(data_array, fromx)
    ending_index = insert_interp_value(data_array, tox)

    result = 0.0

    # Note that we do indeed mean "ending_index" here and not "ending_index+1"

    for ind in xrange(starting_index, ending_index):
        x0, y0 = data_array[ind].getxy()
        x1, y1 = data_array[ind+1].getxy()
        result += (y1 + y0) * (x1 - x0)

    return result / 2.0

