# Dialog for manipulation of observation file

from PyQt5 import QtCore, QtGui, QtWidgets

import ui_obsfileseldlg
import specdatactrl

class ObsFileDlg(QtWidgets.QDialog, ui_obsfileseldlg.Ui_obsfileseldlg):

    def __init__(self, parent = None):
        super(ObsFileDlg, self).__init__()
        self.setupUi(self)

        # Set up combo boxes with possible fields in

        for fn, descr in specdatactrl.Obsfields:
            self.selobsfield.addItem(descr, QtCore.QVariant(fn))

        for fn, descr in specdatactrl.Specfields:
            self.selspecfield.addItem(descr, QtCore.QVariant(fn))

    def default_fields(self):
        """Initialise default fields for new files"""

        # First set up obs times default

        for fnum in (0,2,4,5):
            fn, descr = specdatactrl.Obsfields[fnum]
            item = QListWidgetItem(descr)
            item.setData(Qt.UserRole, QtCore.QVariant(fn))
            self.obsfields.addItem(item)

        # Now for spec data

        for fnum in (0,1,2):
            fn, descr = specdatactrl.Specfields[fnum]
            item = QListWidgetItem(descr)
            item.setData(Qt.UserRole, QtCore.QVariant(fn))
            self.specfields.addItem(item)

    def copyin_fields(self, listw, namelist, flist):
        """Function to copy existing fields into one of the list widgets"""

        dlu = dict()
        for p in namelist:
            dlu[p[0]] = p[1]
        for fn in flist:
            try:
                descr = dlu[fn]
                item = QListWidgetItem(descr)
                item.setData(Qt.UserRole, QtCore.QVariant(fn))
                listw.addItem(item)
            except KeyError:
                pass

    def copyin_specfields(self, oflist, sflist):
        """Copy in existing fields to dialog"""
        self.copyin_fields(self.obsfields, specdatactrl.Obsfields, oflist)
        self.copyin_fields(self.specfields, specdatactrl.Specfields, sflist)

    def extract_fields(self):
        """Return pair with lists of selected fields for spec data and obs"""
        obslst = [str(self.obsfields.item(fnum).data(Qt.UserRole).toString()) for fnum in range(0, self.obsfields.count())]
        speclst = [str(self.specfields.item(fnum).data(Qt.UserRole).toString()) for fnum in range(0, self.specfields.count())]
        return (obslst, speclst)

    def on_selobsfile_clicked(self, b = None):
        if b is None: return
        fname = QtWidges.QFileDialog.getOpenFileName(self, self.tr("Select observation time file"), self.obsfile.text())
        if len(fname) == 0: return
        self.obsfile.setText(fname)

    def on_addobsfield_clicked(self, b = None):
        if b is None: return
        itemn = self.selobsfield.currentIndex()
        if itemn < 0: return
        descr = self.selobsfield.itemText(itemn)
        fn = self.selobsfield.itemData(itemn)
        witem = QListWidgetItem(descr)
        witem.setData(Qt.UserRole, fn)
        self.obsfields.addItem(witem)

    def on_delobsfield_clicked(self, b = None):
        if b is None: return
        selitem = self.obsfields.currentRow()
        if selitem < 0: return
        self.obsfields.takeItem(selitem)

    def on_addspecfield_clicked(self, b = None):
        if b is None: return
        itemn = self.selspecfield.currentIndex()
        if itemn < 0: return
        descr = self.selspecfield.itemText(itemn)
        fn = self.selspecfield.itemData(itemn)
        witem = QListWidgetItem(descr)
        witem.setData(Qt.UserRole, fn)
        self.specfields.addItem(witem)

    def on_delspecfield_clicked(self, b = None):
        if b is None: return
        selitem = self.specfields.currentRow()
        if selitem < 0: return
        self.specfields.takeItem(selitem)

