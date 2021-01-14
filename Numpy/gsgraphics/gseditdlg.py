# Scale and offsets dialog

from PyQt5 import QtCore, QtGui, QtWidgets
import string
import os
import os.path
import math
import copy
import numpy as np
import numpy.random as rn
import matplotlib.pyplot as plt
from matplotlib import colors
import sys

import remgeom
import fixdups

import ui_gseditdlg


class GsEditDlg(QtWidgets.QDialog, ui_gseditdlg.Ui_gseditdlg):

    def __init__(self, parent=None):
        super(GsEditDlg, self).__init__(parent)
        self.setupUi(self)
        self.gs = None
        self.imagearray = None
        self.imagetitle = None
        self.numcols = 2
        self.colspins = (self.shade1, self.shade2, self.shade3, self.shade4,
                         self.shade5, self.shade6, self.shade7, self.shade8,
                         self.shade9, self.shade10, self.shade11, self.shade12,
                         self.shade13, self.shade14, self.shade15, self.shade16,
                         self.shade17, self.shade18, self.shade19, self.shade20,
                         self.shade21, self.shade22, self.shade23, self.shade24,
                         self.shade25, self.shade26, self.shade27, self.shade28,
                         self.shade29, self.shade30, self.shade31, self.shade32)
        self.pcspins = (self.pc1, self.pc2, self.pc3, self.pc4,
                        self.pc5, self.pc6, self.pc7, self.pc8,
                        self.pc9, self.pc10, self.pc11, self.pc12,
                        self.pc13, self.pc14, self.pc15, self.pc16,
                        self.pc17, self.pc18, self.pc19, self.pc20,
                        self.pc21, self.pc22, self.pc23, self.pc24,
                        self.pc25, self.pc26, self.pc27, self.pc28,
                        self.pc29, self.pc30, self.pc31, self.pc32)
        self.nsspins = (self.nsd1, self.nsd2, self.nsd3, self.nsd4,
                        self.nsd5, self.nsd6, self.nsd7, self.nsd8,
                        self.nsd9, self.nsd10, self.nsd11, self.nsd12,
                        self.nsd13, self.nsd14, self.nsd15, self.nsd16,
                        self.nsd17, self.nsd18, self.nsd19, self.nsd20,
                        self.nsd21, self.nsd22, self.nsd23, self.nsd24,
                        self.nsd25, self.nsd26, self.nsd27, self.nsd28,
                        self.nsd29, self.nsd30, self.nsd31, self.nsd32)
        self.vspins = (self.v1, self.v2, self.v3, self.v4,
                        self.v5, self.v6, self.v7, self.v8,
                        self.v9, self.v10, self.v11, self.v12,
                        self.v13, self.v14, self.v15, self.v16,
                        self.v17, self.v18, self.v19, self.v20,
                        self.v21, self.v22, self.v23, self.v24,
                        self.v25, self.v26, self.v27, self.v28,
                        self.v29, self.v30, self.v31, self.v32)
        self.currentshades = None
        self.currentpercents = None
        self.currentnsigs = None
        self.currentvalues = None
        self.performingupdate = False
        self.meanvalue = 0.0
        self.stdvalue = 0.0
        self.minvalue = -100.0
        self.maxvalue = 70000.0
        self.minstdd = -100.0
        self.maxstdd = 100.0
        self.plotfigure = None

    def plotmap(self):
        """Okit the display as specified at present"""
        if self.plotfigure is None: return

        self.plotfigure.clf()
        collist = ["#%.2x%.2x%.2x" % (i, i, i) for i in self.currentshades]
        cmap = colors.ListedColormap(collist)
        if self.gs.isfixed:
            crange = [self.minvalue] + self.currentvalues
        elif self.gs.isperc:
            crange = np.percentile(self.imagearray, [0.0] + self.currentpercents)
        else:
            crange = np.array([self.minstdd] + self.currentnsigs) * self.stdvalue + self.meanvalue
        norm = colors.BoundaryNorm(crange, cmap.N)
        img = plt.imshow(self.imagearray, cmap=cmap, norm=norm, origin='lower')
        plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
        if self.imagetitle is not None:
            plt.title(self.imagetitle)

    def setupshades(self):
        """Put in current set of colours and dsable unused ones"""

        for n in range(0, self.numcols):
            sb = self.colspins[n]
            sb.setEnabled(True)
            sb.setValue(self.currentshades[n])
        for n in range(self.numcols, len(self.colspins)):
            sb = self.colspins[n]
            sb.setValue(self.currentshades[-1])
            sb.setEnabled(False)
        # Remember to unset this if we change the number of colours
        self.colspins[self.numcols - 1].setReadOnly(True)

    def createrest(self):
        """This routine fills in the 'other' lists after we've set up one of
        percent/values/nstddevs. The main problem is getting percentiles different"""

        if self.imagearray is None:
            return

        if self.gs.isfixed:
            vallist = self.currentvalues
            self.currentnsigs = list(np.round((np.array(vallist) - self.meanvalue) / self.stdvalue, 3))
        elif self.gs.isperc:
            vallist = np.percentile(self.imagearray, self.currentpercents)
            self.currentnsigs = list(np.round((np.array(vallist) - self.meanvalue) / self.stdvalue, 3))
            self.currentvalues = list(np.round(vallist, 2))
            return
        else:
            vallist = np.array(self.currentnsigs) * self.stdvalue + self.meanvalue
            self.currentvalues = list(np.round(vallist, 2))

        pcarray = np.round(np.array([ np.count_nonzero(self.imagearray <= x) for x in vallist ]) * 100.0 / self.imagearray.size, 3)
        pcarray[-1] = 100.0
        self.currentpercents = list(pcarray)

    def fillinpercent(self, n):
        """Fill in a percent field and also appropriately set setingle step"""
        sp = self.pcspins[n]
        v = self.currentpercents[n]
        sp.setValue(v)
        st = 1.0
        diff = round(100.0 - v, 3)
        for p in (0.1, 0.01, 0.001):
            if diff > st: break
            st = p
        sp.setSingleStep(st)

    def fillingrid(self):
        """Set up grid of numbers after changes. Don't worry about making things read only
        or disabled, we do that separately. Assumes currentpercents etc all set up if image
        or just the active one if not"""

        if self.imagearray is None:
            if self.gs.isfixed:
                for n in range(0, self.numcols):
                    self.vspins[n].setValue(self.currentvalues[n])
            elif self.gs.isperc:
                for n in range(0, self.numcols):
                    self.fillinpercent(n)
            else:
                for n in range(0, self.numcols):
                    self.nsspins[n].setValue(self.currentnsigs[n])
        else:
            for n in range(0, self.numcols):
                self.vspins[n].setValue(self.currentvalues[n])
                self.nsspins[n].setValue(self.currentnsigs[n])
                self.fillinpercent(n)

    def setupenabled(self):
        """Set up grid as to what's enabled/readonly or not depending on what we are doing"""

        if self.imagearray is None:
            if self.gs.isfixed:
                for n in range(0, self.numcols):
                    self.vspins[n].setEnabled(True)
                    self.vspins[n].setReadOnly(False)
                    self.pcspins[n].setEnabled(False)
                    self.nsspins[n].setEnabled(False)
                self.vspins[self.numcols - 1].setReadOnly(False)
            elif self.gs.isperc:
                for n in range(0, self.numcols):
                    self.pcspins[n].setEnabled(True)
                    self.pcspins[n].setReadOnly(False)
                    self.vspins[n].setEnabled(False)
                    self.nsspins[n].setEnabled(False)
                self.pcspins[self.numcols - 1].setReadOnly(False)
            else:
                for n in range(0, self.numcols):
                    self.nsspins[n].setEnabled(True)
                    self.nsspins[n].setReadOnly(False)
                    self.pcspins[n].setEnabled(False)
                    self.vspins[n].setEnabled(False)
                self.nsspins[self.numcols - 1].setReadOnly(False)
        else:
            if self.gs.isfixed:
                for n in range(0, self.numcols):
                    self.vspins[n].setEnabled(True)
                    self.vspins[n].setReadOnly(False)
                    self.pcspins[n].setEnabled(True)
                    self.nsspins[n].setEnabled(True)
                    self.pcspins[n].setReadOnly(True)
                    self.nsspins[n].setReadOnly(True)
                self.vspins[self.numcols - 1].setReadOnly(False)
            elif self.gs.isperc:
                for n in range(0, self.numcols):
                    self.pcspins[n].setEnabled(True)
                    self.pcspins[n].setReadOnly(False)
                    self.vspins[n].setEnabled(True)
                    self.nsspins[n].setEnabled(True)
                    self.vspins[n].setReadOnly(True)
                    self.nsspins[n].setReadOnly(True)
                self.pcspins[self.numcols - 1].setReadOnly(False)
            else:
                for n in range(0, self.numcols):
                    self.nsspins[n].setEnabled(True)
                    self.nsspins[n].setReadOnly(False)
                    self.pcspins[n].setEnabled(True)
                    self.vspins[n].setEnabled(True)
                    self.pcspins[n].setReadOnly(True)
                    self.vspins[n].setReadOnly(True)
                self.nsspins[self.numcols - 1].setReadOnly(False)

        for n in range(self.numcols, len(self.vspins)):
            self.vspins[n].setEnabled(False)
            self.nsspins[n].setEnabled(False)
            self.pcspins[n].setEnabled(False)

    def copyin(self, greyscale, mw):
        """Copy in and set up parameters"""
        self.gs = greyscale
        self.imagearray = mw.currentimage
        self.imagetitle = mw.currentimage_title
        self.gsname.setText(self.gs.name)
        collist = self.gs.shades + [0, 255]
        collist.sort(reverse=not self.gs.inverse)
        self.currentshades = collist
        self.numcols = len(collist)

        # Set up dialog box appropriately

        self.performingupdate = True

        self.numscales.setValue(self.numcols)
        self.setupshades()

        vallist = self.gs.values

        if self.imagearray is None:
            self.meanvalue = 0
            self.stdvalue = 1
            self.minvalue = -100.0
            self.maxvalue = 70000.0
            self.minstdd = -100.0
            self.maxstdd = 100.0
        else:
            self.plotfigure = plt.figure(figsize=(mw.imwidth, mw.imheight))
            self.meanvalue = self.imagearray.mean()
            self.stdvalue = self.imagearray.std()
            self.minvalue = self.imagearray.min()
            self.maxvalue = self.imagearray.max()
            self.minstdd = (self.minvalue - self.meanvalue) / self.stdvalue
            self.maxstdd = (self.maxvalue - self.meanvalue) / self.stdvalue
            self.meanv.setText("%.2f" % self.meanvalue)
            self.medianv.setText("%.2f" % np.median(self.imagearray))
            self.sigmav.setText("%.2f" % self.stdvalue)

        if self.gs.isfixed:
            self.fixedcount.setChecked(True)
            vallist.append(self.maxvalue)
            vallist.sort()
            self.currentvalues = vallist
        elif self.gs.isperc:
            self.percentile.setChecked(True)
            vallist.append(100.0)
            vallist.sort()
            self.currentpercents = vallist
        else:
            self.nstddevs.setChecked(True)
            vallist.append(self.maxstdd)
            vallist.sort()
            self.currentnsigs = vallist

        # Initialise minimum value fields (don't need zero percent)

        self.nsd0.setValue(self.minstdd)
        self.v0.setValue(self.minvalue)

        # Create other two lists and display

        self.createrest()
        self.fillingrid()
        self.setupenabled()
        self.performingupdate = False
        self.plotmap()

    def get_gs_name(self):
        """Get greyscale name, checking it's OK"""
        name = str(self.gsname.text())
        if len(name) == 0:
            QtWidgets.QMessageBox.warning(self, "Name error", "Greyscale name cannot be zero length")
            return None
        if not name.isalnum():
            QtWidgets.QMessageBox.warning(self, "Name error", "Greyscale name '" + name + "' should be alphanumeric")
            return None
        return name

    def copyout(self):
        """Return greyscale instance based on current dialog"""

        self.gs.setname(str(self.gsname.text()))
        if self.gs.isfixed:
            values = self.currentvalues
        elif self.gs.isperc:
            values = self.currentpercents
        else:
            values = self.currentnsigs
        values.pop()
        shades = self.currentshades
        shades.pop()
        shades.pop(0)
        self.gs.values = values
        self.gs.shades = shades
        return self.gs

    def on_shade1_valueChanged(self, value): self.shadechanged(0, value)

    def on_shade2_valueChanged(self, value): self.shadechanged(1, value)

    def on_shade3_valueChanged(self, value): self.shadechanged(2, value)

    def on_shade4_valueChanged(self, value): self.shadechanged(3, value)

    def on_shade5_valueChanged(self, value): self.shadechanged(4, value)

    def on_shade6_valueChanged(self, value): self.shadechanged(5, value)

    def on_shade7_valueChanged(self, value): self.shadechanged(6, value)

    def on_shade8_valueChanged(self, value): self.shadechanged(7, value)

    def on_shade9_valueChanged(self, value): self.shadechanged(8, value)

    def on_shade10_valueChanged(self, value): self.shadechanged(9, value)

    def on_shade11_valueChanged(self, value): self.shadechanged(10, value)

    def on_shade12_valueChanged(self, value): self.shadechanged(11, value)

    def on_shade13_valueChanged(self, value): self.shadechanged(12, value)

    def on_shade14_valueChanged(self, value): self.shadechanged(13, value)

    def on_shade15_valueChanged(self, value): self.shadechanged(14, value)

    def on_shade16_valueChanged(self, value): self.shadechanged(15, value)

    def on_shade17_valueChanged(self, value): self.shadechanged(16, value)

    def on_shade18_valueChanged(self, value): self.shadechanged(17, value)

    def on_shade19_valueChanged(self, value): self.shadechanged(18, value)

    def on_shade20_valueChanged(self, value): self.shadechanged(19, value)

    def on_shade21_valueChanged(self, value): self.shadechanged(20, value)

    def on_shade22_valueChanged(self, value): self.shadechanged(21, value)

    def on_shade23_valueChanged(self, value): self.shadechanged(22, value)

    def on_shade24_valueChanged(self, value): self.shadechanged(23, value)

    def on_shade25_valueChanged(self, value): self.shadechanged(24, value)

    def on_shade26_valueChanged(self, value): self.shadechanged(25, value)

    def on_shade27_valueChanged(self, value): self.shadechanged(26, value)

    def on_shade28_valueChanged(self, value): self.shadechanged(27, value)

    def on_shade29_valueChanged(self, value): self.shadechanged(28, value)

    def on_shade30_valueChanged(self, value): self.shadechanged(29, value)

    def on_shade31_valueChanged(self, value): self.shadechanged(30, value)

    def on_shade32_valueChanged(self, value): self.shadechanged(31, value)

    def shadechanged(self, shadenum, newshade):
        """Deal with shade changes, adjusting neighbours if need be"""

        if self.performingupdate or shadenum >= self.numcols or type(newshade) != int:
            return

        diff = newshade - self.currentshades[shadenum]
        if diff == 0:
            return

        incr = 1
        if diff < 0:
            incr = -1

        while newshade in self.currentshades:
            newshade += incr

        # If we've run off either end, we'll have to go back to where we were

        if newshade < 0 or newshade > 255:
            self.colspins[shadenum].setValue(self.currentshades[shadenum])
            return

        self.performingupdate = True
        self.currentshades[shadenum] = newshade
        self.currentshades.sort(reverse=not self.gs.inverse)
        for n in range(0, self.numcols):
            self.colspins[n].setValue(self.currentshades[n])
        self.performingupdate = False
        self.plotmap()

    def on_invert_stateChanged(self, b=None):
        if b is None or self.performingupdate: return
        nowchecked = b != 0
        if nowchecked == self.gs.inverse: return
        self.gs.inverse = nowchecked
        self.currentshades.sort(reverse=not self.gs.inverse)
        self.performingupdate = True
        for c in range(0, self.numcols):
            self.colspins[c].setValue(self.currentshades[c])
        for c in range(self.numcols, len(self.colspins)):
            self.colspins[c].setValue(self.currentshades[-1])  # Whatever last colour is might be 0 or 255
        self.performingupdate = False
        self.plotmap()

    def on_numscales_valueChanged(self, value):
        if self.performingupdate or type(value) != int or value == self.numcols:
            return
        self.performingupdate = True
        # Fix old readonly setting
        self.colspins[self.numcols - 1].setReadOnly(False)
        self.numcols = value
        newcollist = [int(x) for x in np.linspace(0, 255, value).round()]
        if not self.gs.inverse:
            newcollist.reverse()
        self.currentshades = newcollist
        self.setupshades()
        if self.gs.isfixed:
            vallist = list(np.linspace(self.minvalue, self.maxvalue, value + 1))
            vallist.pop(0)
            self.currentvalues = vallist
        elif self.gs.isperc:
            vallist = list(np.linspace(0, 100, value + 1))
            vallist.pop(0)
            self.currentpercents = vallist
        else:
            vallist = list(np.linspace(self.minstdd, self.maxstdd, value + 1))
            vallist.pop(0)
            self.currentnsigs = vallist

        self.createrest()
        self.fillingrid()
        self.setupenabled()
        self.performingupdate = False
        self.plotmap()

    def on_percentile_toggled(self, newstate):
        if self.performingupdate or not newstate: return
        if not self.gs.isfixed and self.gs.isperc: return
        self.gs.isfixed = False
        self.gs.isperc = True
        self.performingupdate = True

        if self.imagearray is None:
            newarray = list(np.linspace(0.0, 100.0, self.numcols + 1))
            newarray.pop(0)
        else:
            newarray = list(fixdups.fixdups(self.currentpercents))
        self.currentpercents = newarray
        self.fillingrid()
        self.setupenabled()
        self.performingupdate = False
        self.plotmap()

    def on_fixedcount_toggled(self, newstate):
        if self.performingupdate or not newstate: return
        if self.gs.isfixed: return
        self.gs.isfixed = True
        self.performingupdate = True

        if self.imagearray is None:
            newarray = list(np.linspace(self.minvalue, self.maxvalue, self.numcols + 1))
            newarray.pop(0)
        else:
            newarray = list(fixdups.fixdups(self.currentvalues, division=0.01, minimum=self.minvalue, maximum=self.maxvalue))

        self.currentvalues = newarray
        self.fillingrid()
        self.setupenabled()
        self.performingupdate = False
        self.plotmap()

    def on_nstddevs_toggled(self, newstate):
        if self.performingupdate or not newstate: return
        if not self.gs.isfixed and not self.gs.isperc: return
        self.gs.isfixed = False
        self.gs.isperc = False
        self.performingupdate = True

        if self.imagearray is None:
            newarray = list(np.linspace(self.minstdd, self.maxstdd, self.numcols + 1))
            newarray.pop(0)
        else:
            newarray = list(fixdups.fixdups(self.currentnsigs, division=0.001, minimum=self.minstdd, maximum=self.maxstdd))

        self.currentnsigs = newarray
        self.fillingrid()
        self.setupenabled()
        self.performingupdate = False
        self.plotmap()

    def on_pc1_valueChanged(self, value): self.pcchanged(0, value)

    def on_pc2_valueChanged(self, value): self.pcchanged(1, value)

    def on_pc3_valueChanged(self, value): self.pcchanged(2, value)

    def on_pc4_valueChanged(self, value): self.pcchanged(3, value)

    def on_pc5_valueChanged(self, value): self.pcchanged(4, value)

    def on_pc6_valueChanged(self, value): self.pcchanged(5, value)

    def on_pc7_valueChanged(self, value): self.pcchanged(6, value)

    def on_pc8_valueChanged(self, value): self.pcchanged(7, value)

    def on_pc9_valueChanged(self, value): self.pcchanged(8, value)

    def on_pc10_valueChanged(self, value): self.pcchanged(9, value)

    def on_pc11_valueChanged(self, value): self.pcchanged(10, value)

    def on_pc12_valueChanged(self, value): self.pcchanged(11, value)

    def on_pc13_valueChanged(self, value): self.pcchanged(12, value)

    def on_pc14_valueChanged(self, value): self.pcchanged(13, value)

    def on_pc15_valueChanged(self, value): self.pcchanged(14, value)

    def on_pc16_valueChanged(self, value): self.pcchanged(15, value)

    def on_pc17_valueChanged(self, value): self.pcchanged(16, value)

    def on_pc18_valueChanged(self, value): self.pcchanged(17, value)

    def on_pc19_valueChanged(self, value): self.pcchanged(18, value)

    def on_pc20_valueChanged(self, value): self.pcchanged(19, value)

    def on_pc21_valueChanged(self, value): self.pcchanged(20, value)

    def on_pc22_valueChanged(self, value): self.pcchanged(21, value)

    def on_pc23_valueChanged(self, value): self.pcchanged(22, value)

    def on_pc24_valueChanged(self, value): self.pcchanged(23, value)

    def on_pc25_valueChanged(self, value): self.pcchanged(24, value)

    def on_pc26_valueChanged(self, value): self.pcchanged(25, value)

    def on_pc27_valueChanged(self, value): self.pcchanged(26, value)

    def on_pc28_valueChanged(self, value): self.pcchanged(27, value)

    def on_pc29_valueChanged(self, value): self.pcchanged(28, value)

    def on_pc30_valueChanged(self, value): self.pcchanged(29, value)

    def on_pc31_valueChanged(self, value): self.pcchanged(30, value)

    def on_pc32_valueChanged(self, value): self.pcchanged(31, value)

    def pcchanged(self, whichpc, newvalue):
        """Deal with percent values"""
        if self.performingupdate or whichpc >= self.numcols or type(newvalue) != float:
            return

        # print("Update percent", whichpc, "current value", self.currentpercents[whichpc], "new value", newvalue, file=sys.stderr)

        diff = newvalue - self.currentpercents[whichpc]
        if abs(diff) < 0.001:
            # print("Difference too small returning", file=sys.stderr)
            return

        incr = 0.001
        if diff < 0.0:
            incr = -.001

        while newvalue in self.currentpercents:
            newvalue = round(newvalue + incr, 3)
            # print("Incrementing new value to", newvalue, file=sys.stderr)

        # If we've run off either end, we'll have to go back to where we were

        if newvalue < 0.0 or newvalue > 100.0:
            self.performingupdate = True
            self.pcspins[whichpc].setValue(self.currentpercents[whichpc])
            self.performingupdate = False
            # print("Reset to previous value of", self.currentpercents[whichpc], file=sys.stderr)
            return

        self.performingupdate = True
        self.currentpercents[whichpc] = newvalue
        self.currentpercents.sort()
        self.createrest()
        self.fillingrid()
        self.performingupdate = False
        self.plotmap()

    def on_nsd1_valueChanged(self, value): self.nsdchanged(0, value)

    def on_nsd2_valueChanged(self, value): self.nsdchanged(1, value)

    def on_nsd3_valueChanged(self, value): self.nsdchanged(2, value)

    def on_nsd4_valueChanged(self, value): self.nsdchanged(3, value)

    def on_nsd5_valueChanged(self, value): self.nsdchanged(4, value)

    def on_nsd6_valueChanged(self, value): self.nsdchanged(5, value)

    def on_nsd7_valueChanged(self, value): self.nsdchanged(6, value)

    def on_nsd8_valueChanged(self, value): self.nsdchanged(7, value)

    def on_nsd9_valueChanged(self, value): self.nsdchanged(8, value)

    def on_nsd19_valueChanged(self, value): self.nsdchanged(9, value)

    def on_nsd11_valueChanged(self, value): self.nsdchanged(10, value)

    def on_nsd12_valueChanged(self, value): self.nsdchanged(11, value)

    def on_nsd13_valueChanged(self, value): self.nsdchanged(12, value)

    def on_nsd14_valueChanged(self, value): self.nsdchanged(13, value)

    def on_nsd15_valueChanged(self, value): self.nsdchanged(14, value)

    def on_nsd16_valueChanged(self, value): self.nsdchanged(15, value)

    def on_nsd17_valueChanged(self, value): self.nsdchanged(16, value)

    def on_nsd18_valueChanged(self, value): self.nsdchanged(17, value)

    def on_nsd19_valueChanged(self, value): self.nsdchanged(18, value)

    def on_nsd20_valueChanged(self, value): self.nsdchanged(19, value)

    def on_nsd21_valueChanged(self, value): self.nsdchanged(20, value)

    def on_nsd22_valueChanged(self, value): self.nsdchanged(21, value)

    def on_nsd23_valueChanged(self, value): self.nsdchanged(22, value)

    def on_nsd24_valueChanged(self, value): self.nsdchanged(23, value)

    def on_nsd25_valueChanged(self, value): self.nsdchanged(24, value)

    def on_nsd26_valueChanged(self, value): self.nsdchanged(25, value)

    def on_nsd27_valueChanged(self, value): self.nsdchanged(26, value)

    def on_nsd28_valueChanged(self, value): self.nsdchanged(27, value)

    def on_nsd29_valueChanged(self, value): self.nsdchanged(28, value)

    def on_nsd30_valueChanged(self, value): self.nsdchanged(29, value)

    def on_nsd31_valueChanged(self, value): self.nsdchanged(30, value)

    def on_nsd32_valueChanged(self, value): self.nsdchanged(31, value)

    def nsdchanged(self, whichns, newvalue):
        """Deal with num stddev values"""

        if self.performingupdate or whichns >= self.numcols or type(newvalue) != float:
            return

        diff = newvalue - self.currentnsigs[whichns]
        if abs(diff) < 0.001:
            return

        incr = 0.001
        if diff < 0.0:
            incr = -.001

        while newvalue in self.currentnsigs:
            newvalue = round(newvalue + incr, 3)

        # If we've run off either end, we'll have to go back to where we were

        if newvalue < self.minstdd or newvalue > self.maxstdd:
            self.performingupdate = True
            self.pcspins[whichns].setValue(self.currentnsigs[whichns])
            self.performingupdate = False
            return

        self.performingupdate = True
        self.currentnsigs[whichns] = newvalue
        self.currentnsigs.sort()
        self.createrest()
        self.fillingrid()
        self.performingupdate = False
        self.plotmap()

    def on_v1_valueChanged(self, value): self.vcjamged(0, value)

    def on_v2_valueChanged(self, value): self.vcjamged(1, value)

    def on_v3_valueChanged(self, value): self.vcjamged(2, value)

    def on_v4_valueChanged(self, value): self.vcjamged(3, value)

    def on_v5_valueChanged(self, value): self.vcjamged(4, value)

    def on_v6_valueChanged(self, value): self.vcjamged(5, value)

    def on_v7_valueChanged(self, value): self.vcjamged(6, value)

    def on_v8_valueChanged(self, value): self.vcjamged(7, value)

    def on_v9_valueChanged(self, value): self.vcjamged(8, value)

    def on_v19_valueChanged(self, value): self.vcjamged(9, value)

    def on_v11_valueChanged(self, value): self.vcjamged(10, value)

    def on_v12_valueChanged(self, value): self.vcjamged(11, value)

    def on_v13_valueChanged(self, value): self.vcjamged(12, value)

    def on_v14_valueChanged(self, value): self.vcjamged(13, value)

    def on_v15_valueChanged(self, value): self.vcjamged(14, value)

    def on_v16_valueChanged(self, value): self.vcjamged(15, value)

    def on_v17_valueChanged(self, value): self.vcjamged(16, value)

    def on_v18_valueChanged(self, value): self.vcjamged(17, value)

    def on_v19_valueChanged(self, value): self.vcjamged(18, value)

    def on_v20_valueChanged(self, value): self.vcjamged(19, value)

    def on_v21_valueChanged(self, value): self.vcjamged(20, value)

    def on_v22_valueChanged(self, value): self.vcjamged(21, value)

    def on_v23_valueChanged(self, value): self.vcjamged(22, value)

    def on_v24_valueChanged(self, value): self.vcjamged(23, value)

    def on_v25_valueChanged(self, value): self.vcjamged(24, value)

    def on_v26_valueChanged(self, value): self.vcjamged(25, value)

    def on_v27_valueChanged(self, value): self.vcjamged(26, value)

    def on_v28_valueChanged(self, value): self.vcjamged(27, value)

    def on_v29_valueChanged(self, value): self.vcjamged(28, value)

    def on_v30_valueChanged(self, value): self.vcjamged(29, value)

    def on_v31_valueChanged(self, value): self.vcjamged(30, value)

    def on_v32_valueChanged(self, value): self.vcjamged(31, value)

    def vcjamged(self, whichval, newvalue):
        """Deal with num stddev values"""

        if self.performingupdate or whichval >= self.numcols or type(newvalue) != float:
            return

        diff = newvalue - self.currentvalues[whichval]
        if abs(diff) < 0.01:
            return

        incr = 0.01
        if diff < 0.0:
            incr = -.01

        while newvalue in self.currentvalues:
            newvalue = round(newvalue + incr, 2)

        # If we've run off either end, we'll have to go back to where we were

        if newvalue < self.minvalue or newvalue > self.maxvalue:
            self.performingupdate = True
            self.vspins[whichval].setValue(self.currentvalues[whichval])
            self.performingupdate = False
            return

        self.performingupdate = True
        self.currentvalues[whichval] = newvalue
        self.currentvalues.sort()
        self.createrest()
        self.fillingrid()
        self.performingupdate = False
        self.plotmap()
