# Integration ranges

import xmlutil

class  IntRange:
    """Class for integration ranges, including save options"""

    def __init__(self, bg, pk):
        self.background = bg
        self.peak = pk
        self.apply_doppler = True

    def load(self, node):
        """Load ranges from XML file"""
        self.apply_doppler = False
        child = node.firstChild()
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "bg":
                self.background.load(child)
            elif tagn == "pk":
                self.peak.load(child)
            elif tagn == "doppler":
                self.apply_doppler = True
            child = child.nextSibling()

    def save(self, doc, pnode, name):
        """Save ranges to XML file"""
        node = doc.createElement(name)
        pnode.appendChild(node)
        self.background.save(doc, node, "bg")
        self.peak.save(doc, node, "pk")
        xmlutil.savebool(doc, node, "doppler", self.apply_doppler)


