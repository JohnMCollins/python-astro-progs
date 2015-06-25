# Plot functions using GNUplot

import Gnuplot
import string
import copy

import datarange

class Plotter_error(Exception):
    """Throw this class if something goes wrong with the plot"""
    pass

class Plotter:
    """Class to run GNUplot"""

    def __init__(self, opts):
        self.xrange = copy.copy(opts.xrange)
        self.yrange = copy.copy(opts.yrange)
        self.bgirange = copy.copy(opts.intparams.background)
        self.pkrange = copy.copy(opts.intparams.peak)
        self.gp = Gnuplot.Gnuplot()
        self.gp("set term x11 size %d,%d" % (opts.gpwidth, opts.gpheight))

    def reset(self):
        """Reset stuff before plotting again"""
        self.gp("reset")
        self.gp("unset arrow")

    def clear(self):
        """Clear plot usually on error"""
        self.gp("clear")

    def set_xrange(self, minx, maxx):
        """Set X display range"""
        if minx >= maxx:
            raise Plotter_error("Invalid X display range %d,%d" % (opts.gpwidth, opts.gpheight))
        self.xrange = datarange.DataRange(minx, maxx)
        self.gp("set xrange [%.3f:%.3f]" % (minx, maxx))

    def set_yrange(self, miny, maxy):
        """Set Y display range"""
        if miny >= maxy:
            raise Plotter_error("Invalid Y display range")
        self.yrange = datarange.DataRange(miny, maxy)
        self.gp("set yrange [%.1f:%.1f]" % (miny, maxy))

    def set_bgirange(self, minr, maxr):
        """Set Background integration range"""
        if minr >= maxr:
            raise Plotter_error("Invalid Background integration range")
        self.bgirange = datarange.DataRange(minr, maxr)
        self.gp("set arrow from %.3f,%.1f to %.3f,%.1f nohead ls 6" % (minr, self.yrange.lower, minr, self.yrange.upper))
        self.gp("set arrow from %.3f,%.1f to %.3f,%.1f nohead ls 6" % (maxr, self.yrange.lower, maxr, self.yrange.upper))

    def set_pkrange(self, minr, maxr):
        """Set Peak integration range"""
        if minr >= maxr:
            raise Plotter_error("Invalid Peak integration range")
        self.pkrange = datarange.DataRange(minr, maxr)
        self.gp("set arrow from %.3f,%.1f to %.3f,%.1f nohead ls 6" % (minr, self.yrange.lower, minr, self.yrange.upper))
        self.gp("set arrow from %.3f,%.1f to %.3f,%.1f nohead ls 6" % (maxr, self.yrange.lower, maxr, self.yrange.upper))

    def set_plot(self, plotfiles):
        """Create plot from list of plot files"""
        if len(plotfiles) == 0:
            self.clear()
            return
        plotcmds = [ "'%s' w l notitle" % p for p in plotfiles]
        self.gp("plot " + string.join(plotcmds, ','))

class Resultplot:
    """Run GNUplot to display results file"""

    def __init__(self, opts):
        self.gp = Gnuplot.Gnuplot()
        self.gp("set term x11 size %d,%d" % (opts.gpwidth, opts.gpheight))

    def display(self, filelist):
        """Display results filelist assumed in format (filename, starting_time)"""

        plotcmds = [ "'%s' w l title '%g'" % x for x in filelist ]
        self.gp("plot " + string.join(plotcmds, ','))


