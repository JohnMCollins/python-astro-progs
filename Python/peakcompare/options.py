# Options to save

HOMED_CONFIG_DIR = "~/.jmc"

import os
import os.path
from PyQt4.QtCore import *
from PyQt4.QtXml import *

import datarange
import xmlutil
import plotter

class OptError(Exception):
    pass

def check_homed_configdir():
    """Check that we've got the tools config save options handy

    In any case return the expanded directory"""

    name = os.path.expanduser(HOMED_CONFIG_DIR)
    if not os.path.isdir(name):
        try:
            os.mkdir(name)
        except OSError:
            raise OptError("Cannot create config file directory " + name)
    return  name   

def get_full_config_path(fname):
    """Get full path for config file"""
    if os.path.isabs(fname): return fname
    return  os.path.join(check_homed_configdir(), fname)

class Options:
    """Class for saving program options in"""

    def __init__(self):
        self.indexfile = ""
        self.tempdir = os.getcwd()
        self.plotopts = plotter.Plotter_options()
        self.ranges = datarange.RangeList()
        # Initialise range names and values
        self.ranges.setrange(datarange.DataRange(lbound = 6500.0, ubound = 6650.0, descr = "X axis display range", shortname = "xrange"))
        self.ranges.setrange(datarange.DataRange(lbound = 0.0, ubound = 3.0, descr = "Y axis display range", shortname = "yrange"))
        self.ranges.setrange(datarange.DataRange(lbound = 6510.0, ubound = 6520.0, descr = "Background av lower range", shortname = "bglower", red=128, green=128))
        self.ranges.setrange(datarange.DataRange(lbound = 6600.0, ubound = 6620.0, descr = "Background av upper range", shortname = "bgupper", red=128, green=128))
        self.ranges.setrange(datarange.DataRange(lbound = 6570.0, ubound = 6570.5, descr = "Lower peak range", shortname = "lpeak", blue=200))
        self.ranges.setrange(datarange.DataRange(lbound = 6590.0, ubound = 6590.5, descr = "Upper peak range", shortname = "upeak", blue=200))
        self.apply_doppler = True

    def load(self, node):
        """Load options from XML doc"""
        child = node.firstChild()
        self.indexfile = ""
        self.apply_doppler = False
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "indfile":
                self.indexfile = xmlutil.gettext(child)
            elif tagn == "tempdir":
                self.tempdir = xmlutil.gettext(child)
            elif tagn == "plotopts":
                self.plotopts.load(child)
            elif tagn == "ranges":
                self.ranges.load(child)
            elif tagn == "doppler":
                self.apply_doppler = True
            child = child.nextSibling()

    def save(self, doc, pnode, name):
        """Save options to XML doc"""
        node = doc.createElement(name)
        pnode.appendChild(node)
        xmlutil.savedata(doc, node, "indfile", self.indexfile)
        xmlutil.savedata(doc, node, "tempdir", self.tempdir)
        self.plotopts.save(doc, node, "plotopts")
        self.ranges.save(doc, node, "ranges")
        xmlutil.savebool(doc, node, "doppler", self.apply_doppler)
    
    def loadfile(self, filename, rootname):
        """Open config file name (off home directory) and load options from it"""

        # Get ourselves a full path name to the thing

        fullpath = get_full_config_path(filename)
        if not os.path.isfile(fullpath): return

        # Go through the exercise of opening the file and loading the DOM

        fh = None
        try:
            fh = QFile(fullpath)
            if not fh.open(QIODevice.ReadOnly):
                raise IOError(unicode(fh.errorString()))
            doc = QDomDocument()
            if not doc.setContent(fh):
                raise OptError("Could not parse file '" + fullpath + "' as XML");
        except IOError as e:
            raise OptError("IO error on config file '" + fullpath + "' " + e.args[0])
        finally:
            if fh is not None:
                fh.close()

        try:
            root = doc.documentElement()
            if root.tagName() != rootname:
                raise OptError("Unexpected document root tagname, expected " + rootname + " got " + str(root.tagName()))
            self.load(root)
        except xmlutil.XMLError as err:
            raise OptError("Document XML error - " + err.args[0])

    def savefile(self, filename, rootname):
        """Save options to config file (off home directory)"""
    
        fullpath = get_full_config_path(filename)
        doc = QDomDocument("SPECOPTS")
        self.save(doc, doc, rootname)
        xmlstr = doc.toString()
        fh = None
        try:
            fh = QFile(fullpath)
            if not fh.open(QIODevice.WriteOnly):
                raise IOError(unicode(fh.errorString()))
            fh.write(str(xmlstr))
        except IOError as e:
            raise OptError("IO error on config file '" + fullpath + "' " + e.args[0])
        finally:
            if fh is not None:
                fh.close()           

