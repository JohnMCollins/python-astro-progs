# Generalised load datafile routines

import os
import os.path
import re
import string

class Datafile_error(Exception):
    """Exceptions for data files"""

    def __init__(self, msg, dfile, v = ""):
        super(Datafile_error, self).__init__(msg)
        self.filename = dfile.filename
        self.linenumber = dfile.current_line
        self.colnumber = dfile.current_col
        self.value = v

class DFcolumn(object):
    """Specify a column"""

    def __init__(self, ign = False):
        self.ignored = ign

class DFcolumn_float(DFcolumn):
    """Specify a column of floating-point numbers"""

    def __init__(self, ign = False, sorted = False, sortdesc = False):
        super(DFcolumn_float, self).__init__(ign = ign)
        self.sortedcol = sorted
        self.sorteddesc = sortdesc

    def parse(self, strarg, df):
        """Parse float and check if required"""
        try:
            val = float(strarg)
        except ValueError:
            raise Datafile_error("Invalid floating point value", df, strarg)
        if not self.sortedcol: return val
        prev = df.previous[df.current_col]
        if prev is None: return val
        if self.sorteddesc:
            if val >= prev: raise Datafile_error("Fields not descending", df, strarg)
        else:
            if val <= prev: raise Datafile_error("Fields not ascenting", df, strarg)
        return  val

    def format(self):
        """Generate a format code for this"""
        return "%20.6f"

class DFcolumn_filename(DFcolumn):
    """Specify a filename found in a column"""

    def __init__(self, ign = False, mustexist = True):
        super(DFcolumn_filename, self).__init__(ign = ign)
        self.colmexist = mustexist

    def parse(self, strarg, df):
        """Parse filename and check if exists if required"""
        if not self.colmexist: return strarg
        fullp = strarg
        if not os.path.isabs(fullp): fullp = os.path.join(df.workdir, fullp)
        if not os.path.isfile(fullp):
            raise Datafile_error("File not found - " + fullp, df, strarg)
        return strarg

    def format(self):
        """Generate a format code for this"""
        return "%-20s"


class Datafile(object):
    """Class to specify the contents of a datafile"""

    def __init__(self):
        self.columns = []
        self.previous = []
        self.filename = ""
        self.workdir = ""
        self.current_line = 0
        self.current_col = 0

    def addfilecol(self, mustexist = True, ignored = False):
        """Specify that next column is a file name.

        Filename must exist unless arg is false"""

        self.columns.append(DFcolumn_filename(ign = ignored, mustexist = mustexist))

    def addfloatcol(self, ignored = False, sorted = False, sortdesc = False):
        """Specify that next column is a float.

        Specify if it must be sorted and if descending"""
    
        self.columns.append(DFcolumn_float(ign = ignored, sorted = sorted, sortdesc = sortdesc))

    def parsefile(self, file):
        """Parse file according to description"""

        # Tack CWD in front and then split it again
        # This manoeuvre makes sure we set workdir correctly in cases
        # where we call the function with a path which isn't an absolute path

        if not os.path.isabs(file):
            file = os.path.join(os.getcwd(), file)
        self.workdir, self.filename = os.path.split(file)

        # Set up vector of previous results. We do this even for columns we are ignoring

        ncols = len(self.columns)
        self.previous = [None for x in xrange(0, ncols)]

        try:
            infile = open(file)
        except IOError as e:
            raise Datafile_error("IO error: " + e.args[0], self)

        parsp = re.compile('\s+')
        result = []
        self.current_line = 0
        try:
            for line in infile:
                self.current_line += 1
                line = string.strip(line)
                if len(line) == 0: continue
                lparts = parsp.split(line)
                if len(lparts) != ncols:
                    raise Datafile_error("unexpected number of columns read " + str(len(lparts)) + " expected " + str(ncols), self)
                self.current_col = 0
                row = []
                for pc in self.columns:
                    if not pc.ignored:
                        val = pc.parse(lparts[self.current_col], self)
                        self.previous[self.current_col] = val
                        row.append(val)
                    self.current_col += 1
                result.append(row)
        except Datafile_error:
            raise
        finally:
            infile.close()
        return  result

    def writefile(self, file, dataarray):
        """Write out file"""
        format = string.join([pc.format() for pc in self.columns if not pc.ignored], " ") + "\n"     
        outfile = None
        try:
            outfile = open(file, 'w')
            for row in dataarray:
                outfile.write(format % tuple(row))
        except IOError as e:
            raise Datafile_error("IO error: " + e.args[0], self)            
        finally:
            if outfile is not None: outfile.close()

 # Let's have some common classes for things we do

class IndexDataFile(Datafile):

    """Parser for index data files"""

    def __init__(self):
        super(IndexDataFile, self).__init__()
        self.addfilecol()
        self.addfloatcol(sorted = True)
        self.addfloatcol(sorted = True)
        self.addfloatcol(sorted = False)

class SpecDataFile(Datafile):

    """Parser for spectrum data files"""

    def __init__(self):
        super(SpecDataFile, self).__init__()
        self.addfloatcol(sorted = True)
        self.addfloatcol(sorted = False)
        self.addfloatcol(ignored = True)

class IntResult(Datafile):

    """Parser for integration results"""

    def __init__(self):
        super(IntResult, self).__init__()
        self.addfloatcol(sorted = True)
        self.addfloatcol(sorted = True)
        self.addfloatcol(sorted = False)
        self.addfloatcol(sorted = False)

class DispResult(Datafile):

    """Parser for displaying results"""

    def __init__(self):
        super(DispResult, self).__init__()
        self.addfloatcol(sorted = True)
        self.addfloatcol(sorted = False)



