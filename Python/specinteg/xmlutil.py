# XML Utility functions

from PyQt4.QtCore import *
from PyQt4.QtXml import *

class XMLError(Exception):
    """Throw these errors if we get some value etc error"""
    pass

def gettext(node):
    """Extract the text child from an XML node"""
    return str(node.firstChild().toText().data())

def getint(node):
    """Extract text field from XML node and make an int out of it"""
    try:
        return int(gettext(node))
    except ValueError:
        raise XMLError("Invalid int value for " + str(node.toElement().tagName()))

def getfloat(node):
    """Extract text field from XML node and make a float out of it"""
    try:   
        return float(gettext(node))
    except ValueError:
        raise XMLError("Invalid float value for " + str(node.toElement().tagName()))

def savedata(doc, pnode, name, value):
    """Encode something to an XML file"""
    item = doc.createElement(name)
    pnode.appendChild(item)
    item.appendChild(doc.createTextNode(str(value)))

def savebool(doc, pnode, name, value):
    """Possibly encode a bool value"""
    if not value: return
    item = doc.createElement(name)
    pnode.appendChild(item)

