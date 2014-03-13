#! /usr/bin/python

import sys
import os.path
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
import ui_configdlg
import Gnuplot

def xmlgetfloat(node):
  """Extract text field from XML node and make a float out of it"""
  return float(str(node.firstChild().toText().data()))

def savexmlfloat(doc, pnode, name, value):
  """Encode a floating point number to an XML file"""
  item = doc.createElement(name)
  pnode.appendChild(item)
  item.appendChild(doc.createTextNode(str(value)))

class OptError(Exception):
  pass

class Options:
  """Class for saving parameters across invocations"""
  
  def __init__(self):
    self.xrangemin = 6500.0
    self.xrangemax = 6700.0
    self.yrangemin = 0.0
    self.yrangemax = 3.0
    self.bgimin = 6530.0
    self.bgimax = 6600.0
    self.hamin = 6560.0
    self.hamax = 6573.0

  def load(self, node):
    """Load options from XML file"""
    child = node.firstChild()
    while not child.isNull():
      tagn = child.toElement().tagName()
      if tagn == "xrmin":
        self.xrangemin = xmlgetfloat(child)
      elif tagn == "xrmax":
        self.xrangemax = xmlgetfloat(child)
      elif tagn == "yrmin":
        self.yrangemin = xmlgetfloat(child)
      elif tagn == "yrmax":
        self.yrangemax = xmlgetfloat(child)
      elif tagn == "bgimin":
        self.bgimin = xmlgetfloat(child)
      elif tagn == "bgimax":
        self.bgimax = xmlgetfloat(child)
      elif tagn == "hamin":
        self.hamin = xmlgetfloat(child)
      elif tagn == "hamax":
        self.hamax = xmlgetfloat(child)
      child = child.nextSibling()

  def save(self, doc, pnode, name):
    """Save options to XML file"""
    node = doc.createElement(name)
    savexmlfloat(doc, node, "xrmin", self.xrangemin)
    savexmlfloat(doc, node, "xrmax", self.xrangemax)
    savexmlfloat(doc, node, "yrmin", self.yrangemin)
    savexmlfloat(doc, node, "yrmax", self.yrangemax)
    savexmlfloat(doc, node, "bgimin", self.bgimin)
    savexmlfloat(doc, node, "bgimax", self.bgimax)
    savexmlfloat(doc, node, "hamin", self.hamin)
    savexmlfloat(doc, node, "hamax", self.hamax)
    pnode.appendChild(node)

  def loadfile(self, filename):
    """Open config file name and load options from it"""
    doc = QDomDocument()
    try:
      fh = QFile(filename)
      if not fh.open(QIODevice.ReadOnly):
         raise IOError(unicode(fh.errorString()))
      if not doc.setContent(fh):
         raise OptError("Could not parse XML file " + filename)
    except IOError:
      return
    finally:
      fh.close()
    try:
      root = doc.documentElement()
      if root.tagName() != "SELHA":
        raise OptError("Unexpected document tagname" + root.tagName())
      self.load(root)
    except ValueError as err:
      raise OptError("Document load error " + err.args[0])  

  def savefile(self, filename):
    """Save config file options"""
    doc = QDomDocument("SELHA")
    self.save(doc, doc, "SELHA")
    xmlstr = doc.toString()
    try:
      fh = QFile(filename)
      if not fh.open(QIODevice.WriteOnly):
        raise OptError(unicode(fh.errorString()))
      fh.write(str(xmlstr))
    except (OSError, ValueError) as s:
      raise OptError(s.args[0])
    finally:
      fh.close()
  def on_xrangemin_valueChanged(self, value):
    self.updateplot()

  def on_xrangemax_valueChanged(self, value):
    self.updateplot()

class Cseldlg(QDialog, ui_configdlg.Ui_configdlg):

  global Plot

  def __init__(self, parent = None):
    super(Cseldlg, self).__init__(parent)
    self.setupUi(self)
    self.workdir = QString("/home/jcollins/Documents/Halpha")

  def optinit(self, opts):
    """Copy in options"""
    self.xrangemin.setValue(opts.xrangemin)
    self.xrangemax.setValue(opts.xrangemax)
    self.yrangemin.setValue(opts.yrangemin)
    self.yrangemax.setValue(opts.yrangemax)
    self.bgintmin.setValue(opts.bgimin)
    self.bgintmax.setValue(opts.bgimax)
    self.halphamin.setValue(opts.hamin)
    self.halphamax.setValue(opts.hamax)

  def optsave(self, opts):
    """Copy back options"""
    opts.xrangemin = self.xrangemin.value()
    opts.xrangemax = self.xrangemax.value()
    opts.yrangemin = self.yrangemin.value()
    opts.yrangemax = self.yrangemax.value()
    opts.bgimin = self.bgintmin.value()
    opts.bgimax = self.bgintmax.value()
    opts.hamin = self.halphamin.value()
    opts.hamax = self.halphamax.value()

  def updateplot(self):
    fname = str(self.datafile.text())
    fullname = os.path.join(str(self.workdir), fname)
    Plot("reset")
    if len(fname) == 0: return
    rangemin = self.xrangemin.value()
    rangemax = self.xrangemax.value()
    ymin = self.yrangemin.value()
    ymax = self.yrangemax.value()
    if rangemin >= rangemax: return
    halfmin = self.halphamin.value()
    halfmax = self.halphamax.value()
    if halfmin >= halfmax: return
    bgimin = self.bgintmin.value()
    bgimax = self.bgintmax.value()
    if bgimin > bgimax: return
    Plot("set xrange [%.3f:%.3f]" % (rangemin, rangemax))
    Plot("set yrange [%.1f:%.1f]" % (ymin, ymax))
    if rangemin < bgimin and bgimin < halfmin: Plot("set arrow from %.3f,%.1f to %.3f,%.1f nohead ls 3" % (bgimin,ymin,bgimin,ymax))
    if rangemax > bgimax and bgimax > halfmax: Plot("set arrow from %.3f,%.1f to %.3f,%.1f nohead ls 3" % (bgimax,ymin,bgimax,ymax))
    if rangemin < halfmin: Plot("set arrow from %.3f,%.1f to %.3f,%.1f nohead ls 1" % (halfmin,ymin,halfmin,ymax))
    if rangemax > halfmax: Plot("set arrow from %.3f,%.1f to %.2f,%.1f nohead ls 1" % (halfmax,ymin,halfmax,ymax))
    Plot("plot '%s' using 1:2 w l title '%s' ls 6" % (fullname, fname))

  def on_selfile_clicked(self, b = None):
    if b is None: return
    fname = QFileDialog.getOpenFileName(self, self.tr("Select spectrum file"), self.workdir, self.tr("Spectrum files (*.asc)"))
    (dir, file) = os.path.split(str(fname))
    self.workdir = QString(dir)
    self.datafile.setText(file)
    self.updateplot()

  def on_xrangemin_valueChanged(self, value): self.updateplot()
  def on_xrangemax_valueChanged(self, value): self.updateplot()
  def on_yrangemin_valueChanged(self, value): self.updateplot()
  def on_yrangemax_valueChanged(self, value): self.updateplot()
  def on_bgintmin_valueChanged(self, value): self.updateplot()
  def on_bgintmax_valueChanged(self, value): self.updateplot()
  def on_halphamin_valueChanged(self, value): self.updateplot()
  def on_halphamax_valueChanged(self, value): self.updateplot()

  def incdec_range(self, b, fld, amt):
    if b is None: return
    cval = fld.value()
    nval = cval + amt
    if nval > fld.maximum():
      nval = fld.maximum()
    elif nval < fld.minimum():
      nval = fld.minimum()
    if nval != cval: fld.setValue(nval)

  def incdec_both(self, b, lfld, ufld, amt):
    self.incdec_range(b, lfld, -amt)
    self.incdec_range(b, ufld, amt)

  def on_rlpp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, 0.1)
  def on_rlpp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, 0.5)
  def on_rlmp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, -0.1)
  def on_rlmp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, -0.5)
  def on_rupp1_clicked(self, b = None): self.incdec_range(b, self.xrangemax, 0.1)
  def on_rupp5_clicked(self, b = None): self.incdec_range(b, self.xrangemax, 0.5)
  def on_rump1_clicked(self, b = None): self.incdec_range(b, self.xrangemax, -0.1)
  def on_rump5_clicked(self, b = None): self.incdec_range(b, self.xrangemax, -0.5)
  def on_rbpp1_clicked(self, b = None): self.incdec_both(b, self.xrangemin, self.xrangemax, 0.1)
  def on_rbpp5_clicked(self, b = None): self.incdec_both(b, self.xrangemin, self.xrangemax, 0.5)
  def on_rbmp1_clicked(self, b = None): self.incdec_both(b, self.xrangemin, self.xrangemax, -0.1)
  def on_rbmp5_clicked(self, b = None): self.incdec_both(b, self.xrangemin, self.xrangemax, -0.5)
  def on_bgilpp1_clicked(self, b = None): self.incdec_range(b, self.bgintmin, 0.1)
  def on_bgilpp5_clicked(self, b = None): self.incdec_range(b, self.bgintmin, 0.5)
  def on_bgilmp1_clicked(self, b = None): self.incdec_range(b, self.bgintmin, -0.1)
  def on_bgilmp5_clicked(self, b = None): self.incdec_range(b, self.bgintmin, -0.5)
  def on_bgiupp1_clicked(self, b = None): self.incdec_range(b, self.bgintmax, 0.1)
  def on_bgiupp5_clicked(self, b = None): self.incdec_range(b, self.bgintmax, 0.5)
  def on_bgiump1_clicked(self, b = None): self.incdec_range(b, self.bgintmax, -0.1)
  def on_bgiump5_clicked(self, b = None): self.incdec_range(b, self.bgintmax, -0.5)
  def on_bgibpp1_clicked(self, b = None): self.incdec_both(b, self.bgintmin, self.bgintmax, 0.1)
  def on_bgibpp5_clicked(self, b = None): self.incdec_both(b, self.bgintmin, self.bgintmax, 0.5)
  def on_bgibmp1_clicked(self, b = None): self.incdec_both(b, self.bgintmin, self.bgintmax, -0.1)
  def on_bgibmp5_clicked(self, b = None): self.incdec_both(b, self.bgintmin, self.bgintmax, -0.5)
  def on_halpp1_clicked(self, b = None): self.incdec_range(b, self.halphamin, 0.1)
  def on_halpp5_clicked(self, b = None): self.incdec_range(b, self.halphamin, 0.5)
  def on_halmp1_clicked(self, b = None): self.incdec_range(b, self.halphamin, -0.1)
  def on_halmp5_clicked(self, b = None): self.incdec_range(b, self.halphamin, -0.5)
  def on_haupp1_clicked(self, b = None): self.incdec_range(b, self.halphamax, 0.1)
  def on_haupp5_clicked(self, b = None): self.incdec_range(b, self.halphamax, 0.5)
  def on_haump1_clicked(self, b = None): self.incdec_range(b, self.halphamax, -0.1)
  def on_haump5_clicked(self, b = None): self.incdec_range(b, self.halphamax, -0.5)
  def on_habpp1_clicked(self, b = None): self.incdec_both(b, self.halphamin, self.halphamax, 0.1)
  def on_habpp5_clicked(self, b = None): self.incdec_both(b, self.halphamin, self.halphamax, 0.5)
  def on_habmp1_clicked(self, b = None): self.incdec_both(b, self.halphamin, self.halphamax, -0.1)
  def on_habmp5_clicked(self, b = None): self.incdec_both(b, self.halphamin, self.halphamax, -0.5)

Opts = Options()
Opts.loadfile("Parametersfile")
Plot = Gnuplot.Gnuplot()
app = QApplication(sys.argv)
mw = Cseldlg()
mw.optinit(Opts)
mw.exec_()
mw.optsave(Opts)
Opts.savefile("Parametersfile")
sys.exit(0)





