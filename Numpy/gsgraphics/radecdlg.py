# Scale and offsets dialog

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QColor, QPalette, QBrush
from PyQt5.QtWidgets import QColorDialog
import string
import os
import os.path
import copy

import ui_radecdlg

# colournames = dict(black='#000000', white='#ffffff',
#                   red='#ff0000', green='#00ff00', blue='#0000ff', magenta='#ff00ff', yellow='#ffff00', cyan='#00ffff')


def decode_colour(st):
    """Decord a colour, return something half sensible if it does not make sense"""
    return QColor(st)


def inverse_colour(c):
    """Get complement of colour"""
    return QColor(255 - c.red(), 255 - c.green(), 255 - c.blue())


def set_text_colours(widget, colour):
    """Set text colours with background to colour and text to inverse"""
    palette = widget.palette()
    palette.setColor(QPalette.Active, QPalette.Text, inverse_colour(colour))
    palette.setColor(QPalette.Active, QPalette.Base, colour)
    widget.setPalette(palette)


class RaDecDlg(QtWidgets.QDialog, ui_radecdlg.Ui_radecdlg):

    def __init__(self, parent=None):
        super(RaDecDlg, self).__init__(parent)
        self.setupUi(self)
        self.config = None
        self.objcolours.itemDoubleClicked.connect(self.on_resetobjcolour_clicked)

    def copyin(self, config):
        """Copy in and set up parameters"""
        self.config = config
        self.divisions.setValue(config.divspec.divisions)
        self.threshold.setValue(config.divspec.divthresh)
        self.prec.setValue(config.divspec.divprec)
        self.divalpha.setValue(config.divspec.divalpha)
        set_text_colours(self.Racolour, decode_colour(config.divspec.racol))
        set_text_colours(self.DECcolour, decode_colour(config.divspec.deccol))
        self.objalpha.setValue(config.objdisp.objalpha)
        self.objfontsz.setValue(config.objdisp.objtextfs)
        self.objdispl.setValue(config.objdisp.objtextdisp)
        self.objfill.setChecked(config.objdisp.objfill)
        # self.Racolour.mouseDoubleClickEvent.connect(self.on_resetracol_clicked)
        # self.DECcolour.mouseDoubleClickEvent.connect(self.on_resetdeccol_clicked)
        for c in config.objdisp.objcolour:
            it = QtWidgets.QListWidgetItem("")
            cs = QColor(c)
            it.setBackground(QBrush(cs))
            it.setForeground(QBrush(inverse_colour(cs)))
            it.setText(c)
            self.objcolours.addItem(it)

    def copyout(self):
        """Copy date out of dialog. We already set a copy in self.config"""
        config = self.config
        divspec = config.divspec
        divspec.divisions = self.divisions.value()
        divspec.divthresh = self.threshold.value()
        divspec.divprec = self.prec.value()
        divspec.divalpha = self.divalpha.value()
        divspec.racol = str(self.Racolour.palette().color(QPalette.Active, QPalette.Base).name())
        divspec.deccol = str(self.DECcolour.palette().color(QPalette.Active, QPalette.Base).name())
        objdisp = config.objdisp
        objdisp.objalpha = self.objalpha.value()
        objdisp.objtextfs = self.objfontsz.value()
        objdisp.objtextdisp = self.objdispl.value()
        objdisp.objfill = self.objfill.isChecked()
        objc = []
        for row in range(0, self.objcolours.count()):
            objc.append(str(self.objcolours.item(row).background().color().name()))
        objdisp.objcolour = objc

    def select_text_colour(self, widget, label):
        """Possible select new text colour"""
        palette = widget.palette()
        oldc = palette.color(QPalette.Active, QPalette.Base)
        nc = QColorDialog.getColor(oldc, self, "Select new colour for " + label)
        if not nc.isValid(): return
        set_text_colours(widget, nc)

    def on_resetracol_clicked(self, b=None):
        if b is None: return
        self.select_text_colour(self.Racolour, "Right Ascension grid lines")

    def on_resetdeccol_clicked(self, b=None):
        if b is None: return
        self.select_text_colour(self.DECcolour, "Declination grid lines")

    def on_newobjcolour_clicked(self, b=None):
        if b is None: return
        newc = QColorDialog.getColor(QColor("white"), self, "Pick a new object colour")
        if not newc.isValid(): return
        it = QtWidgets.QListWidgetItem("")
        it.setBackground(QBrush(newc))
        it.setForeground(QBrush(inverse_colour(newc)))
        it.setText(newc.name())
        self.objcolours.addItem(it)

    def on_resetobjcolour_clicked(self, b=None):
        if b is None: return
        it = self.objcolours.currentItem()
        if it is None: return
        newc = QColorDialog.getColor(it.background().color(), self, "Select a replacement object colour")
        if not newc.isValid(): return
        it.setBackground(QBrush(newc))
        it.setForeground(QBrush(inverse_colour(newc)))
        it.setText(newc.name())
        self.objcolours.setCurrentItem(it)

    def on_delobjcolour_clicked(self, b=None):
        if b is None: return
        if self.objcolours.count() < 2:
            QtWidgets.QMessageBox.warning(self, "Cannot delete", "Must have one object colour")
            return
        self.objcolours.takeItem(self.objcolours.currentRow())
