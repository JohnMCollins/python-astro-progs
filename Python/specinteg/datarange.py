# Class type for ranges

import xmlutil

class  DataRangeError(Exception):
    """Class to report errors concerning ranges"""
    pass

class  DataRange:
    """Class for data ranges, including save options"""

    def __init__(self, l = 0.0, u = 100.0, d = ""):
        self.lower = l
        self.upper = u
        self.description = d

    def inrange(self, value):
        """Report if value is in given range"""
        return  value >= self.lower and value <= self.upper

    def load(self, node):
        """Load range from XML file"""
        self.description = ""
        child = node.firstChild()
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "lower":
                self.lower = xmlutil.getfloat(child)
            elif tagn == "upper":
                self.upper = xmlutil.getfloat(child)
            elif tagn == "descr":
                self.description = xmlutil.gettext(child)
            child = child.nextSibling()

    def save(self, doc, pnode, name):
        """Save range to XML file"""
        node = doc.createElement(name)
        xmlutil.savedata(doc, node, "lower", self.lower)
        xmlutil.savedata(doc, node, "upper", self.upper)
        if len(self.description) != 0:
            xmlutil.savedata(doc, node, "descr", self.description)
        pnode.appendChild(node)

