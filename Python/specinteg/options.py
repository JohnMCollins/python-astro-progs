# Options to save

HOMED_CONFIG_DIR = "~/.jmc"

import os
import os.path
from PyQt4.QtCore import *
from PyQt4.QtXml import *

import datarange
import intrange
import xmlutil

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
        self.gpwidth = 600
        self.gpheight = 400
        self.xrange = datarange.DataRange(6500.0, 6650.0, "X display range (Angstrom)")
        self.yrange = datarange.DataRange(0.0, 3.0, "Y display range")
        self.intparams = intrange.IntRange(datarange.DataRange(6530.0, 6600.0, "Background Int"), datarange.DataRange(6560.0, 6573.0, "Peak"))

    def load(self, node):
        """Load options from XML doc"""
        child = node.firstChild()
        self.indexfile = ""
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "indfile":
                self.indexfile = xmlutil.gettext(child)
            elif tagn == "tempdir":
                self.tempdir = xmlutil.gettext(child)
            elif tagn == "gpwid":
                self.gpwidth = xmlutil.getint(child)
            elif tagn == "gpht":
                self.gpheight = xmlutil.getint(child)
            elif tagn == "xrange":
                self.xrange.load(child)
            elif tagn == "yrange":
                self.yrange.load(child)
            elif tagn == "intp":
                self.intparams.load(child)
            child = child.nextSibling()

    def save(self, doc, pnode, name):
        """Save options to XML doc"""
        node = doc.createElement(name)
        pnode.appendChild(node)
        if len(self.indexfile) != 0: xmlutil.savedata(doc, node, "indfile", self.indexfile)
        xmlutil.savedata(doc, node, "tempdir", self.tempdir)
        xmlutil.savedata(doc, node, "gpwid", self.gpwidth)
        xmlutil.savedata(doc, node, "gpht", self.gpheight)
        self.xrange.save(doc, node, "xrange")
        self.yrange.save(doc, node, "yrange")
        self.intparams.save(doc, node, "intp")
    
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

