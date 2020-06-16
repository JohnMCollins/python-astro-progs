# Scale and offsets dialog

from PyQt5 import QtCore, QtGui, QtWidgets

import copy
import remgeom
import dbops
import remdefaults

import ui_trimeditdlg
import ui_itrimdlg
import ui_imlimdlg
import ui_ilimdlg


class ITrimDlg(QtWidgets.QDialog, ui_itrimdlg.Ui_itrimdlg):

    def __init__(self, parent=None):
        super(ITrimDlg, self).__init__(parent)
        self.trim = None
        self.setupUi(self)

    def copyin(self, trim):
        """Copy in data at start of dialog"""
        self.trim = trim
        if trim.name is None:
            self.filtername.setText("(Defualt)")
            self.filtername.setReadOnly()(True)
        else:
            self.filtername.setText(trim.name)
        self.ltrim.setValue(trim.left)
        self.rtrim.setValue(trim.right)
        self.ttrim.setValue(trim.top)
        self.btrim.setValue(trim.bottom)
        if trim.afterblank:
            self.afternan.setChecked(True)

    def checkname(self):
        """Check name format is valid return it if it is"""
        if self.filtername.isReadOnly():
            return  ""
        txt = str(self.filtername.text())
        if txt.isalnum():
            return txt
        QtWidgets.QMessageBox.warning(self, "Trim name error", txt + " is not alphanumeric")
        return None

    def copyout(self):
        """Copy result as new trim descr"""
        ret = remgeom.Trims()
        if not self.filtername.isReadOnly():
            ret.name = str(self.filtername.text())
        ret.left = self.ltrim.value()
        ret.right = self.rtrim.value()
        ret.top = self.ttrim.value()
        ret.bottom = self.btrim.value()
        if self.afternan.isChecked():
            ret.afterblank = True
        return  ret


class TrimEditDlg(QtWidgets.QDialog, ui_trimeditdlg.Ui_trimeditdlg):

    def __init__(self, parent=None):
        super(TrimEditDlg, self).__init__(parent)
        self.config = None
        self.setupUi(self)

    def setdisprow(self, trim):
        """Set up displayed row"""
        name = trim.name
        if name is None:
            name = "(Default)"
        rownum = self.trimtab.rowCount()
        self.trimtab.insertRow(rownum)
        self.trimtab.setItem(rownum, 0, QtWidgets.QTableWidgetItem(name))
        self.trimtab.setItem(rownum, 1, QtWidgets.QTableWidgetItem(str(trim.left)))
        self.trimtab.setItem(rownum, 2, QtWidgets.QTableWidgetItem(str(trim.right)))
        self.trimtab.setItem(rownum, 3, QtWidgets.QTableWidgetItem(str(trim.top)))
        self.trimtab.setItem(rownum, 4, QtWidgets.QTableWidgetItem(str(trim.bottom)))
        ab = "no"
        if trim.afterblank:
            ab = "yes"
        self.trimtab.setItem(rownum, 5, QtWidgets.QTableWidgetItem(ab))

    def setdisprows(self):
        """Set up all rows"""
        # self.trimtab.clearContents()
        self.trimtab.setRowCount(0)
        self.setdisprow(self.config.deftrims)
        for f in sorted(self.config.ftrims.keys()):
            self.setdisprow(self.config.ftrims[f])

    def copyin(self, config):
        """Copy in and set up parameters"""
        self.config = config
        self.setdisprows()

    def get_selected_row(self):
        """Find selected row return -1 if none"""
        inds = self.trimtab.selectedIndexes()
        if len(inds) == 0:
            return -1
        return inds[0].row()

    def get_filter_at(self, row):
        """Get filter name at specified row"""
        return str(self.trimtab.item(row, 0).text())

    def check_filter_ok(self, name):
        """Check that filter isn't already defined"""
        if name in self.config.ftrims:
            QtWidgets.QMessageBox.warning(self, "Trim name error", name + " is already defined")
            return True
        if len(name) != 1 or name[0] not in 'girz':
            QtWidgets.QMessageBox.warning(self, "Trim name error", name + " is only used for g r i z")
            # But carry on anyhow
        return False

    def do_edit(self, filter):
        """Work for editing whether from button press or double click"""
        if filter[0] == '(':
            origtrim = self.config.deftrims
            origname = None
        else:
            origtrim = self.config.ftrims[filter]
            origname = origtrim.name
        origtrim = copy.deepcopy(origtrim)
        dlg = ITrimDlg(self)
        dlg.copyin(origtrim)
        while dlg.exec_():
            newname = dlg.checkname()
            if newname is None:
                continue
            if origname is None:
                self.config.deftrims = dlg.copyout()
            else:
                if  origname != newname:
                    if self.check_filter_ok(newname):
                        continue
                    del self.config.ftrims[origname]
                self.config.ftrims[newname] = dlg.copyout()
            self.setdisprows()
            break

    def on_newtrim_clicked(self, b=None):
        if b is None: return
        posstrim = remgeom.Trims()
        posstrim.name = "EditMe"
        dlg = ITrimDlg(self)
        dlg.copyin(posstrim)
        while dlg.exec_():
            newname = dlg.checkname()
            if newname is None:
                continue
            if self.check_filter_ok(newname):
                continue
            newtrim = dlg.copyout()
            self.config.ftrims[newname] = newtrim
            self.setdisprows()
            break

    def on_edittrim_clicked(self, b=None):
        if b is None: return
        row = self.get_selected_row()
        if row < 0:
            return
        self.do_edit(self.get_filter_at(row))

    def on_deltrim_clicked(self, b=None):
        if b is None: return
        row = self.get_selected_row()
        if row < 0:
            return
        filter = self.get_filter_at(row)
        if QtWidgets.QMessageBox.question(self, "Are you sure", "Sure you want to delete " + filter,
            QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No) != QtWidgets.QMessageBox.Yes:
            return
        del self.config.ftrims[filter]
        self.setdisprows()

    def on_trimtab_cellDoubleClicked(self, row, column):
        self.do_edit(self.get_filter_at(row))


class ILimDlg(QtWidgets.QDialog, ui_ilimdlg.Ui_ilimdlg):

    def __init__(self, parent=None):
        super(ILimDlg, self).__init__(parent)
        self.lim = None
        self.setupUi(self)

    def copyin(self, lim):
        """Copy in data at start of dialog"""
        self.lim = lim
        self.filtername.setText(lim.filter)
        self.rows.setValue(lim.rows)
        self.cols.setValue(lim.cols)

    def checkname(self):
        """Check name format is valid return it if it is"""
        txt = str(self.filtername.text())
        if txt.isalnum():
            return txt
        QtWidgets.QMessageBox.warning(self, "Limit name error", txt + " is not alphanumeric")
        return None

    def copyout(self):
        """Copy result as new limit descr"""
        return remgeom.Imlimits(filter=str(self.filtername.text()), rows=self.rows.value(), cols=self.cols.value())


class ImLimDlg(QtWidgets.QDialog, ui_imlimdlg.Ui_imlimdlg):

    def __init__(self, parent=None):
        super(ImLimDlg, self).__init__(parent)
        self.config = None
        self.setupUi(self)

    def setdisprow(self, lim):
        """Set up displayed row"""
        rownum = self.limtab.rowCount()
        self.limtab.insertRow(rownum)
        self.limtab.setItem(rownum, 0, QtWidgets.QTableWidgetItem(lim.filter))
        self.limtab.setItem(rownum, 1, QtWidgets.QTableWidgetItem(str(lim.rows)))
        self.limtab.setItem(rownum, 2, QtWidgets.QTableWidgetItem(str(lim.cols)))

    def setdisprows(self):
        """Set up all rows"""
        # self.limtab.clearContents()
        self.limtab.setRowCount(0)
        for f in sorted(self.config.imlims.keys()):
            self.setdisprow(self.config.imlims[f])

    def copyin(self, config):
        """Copy in and set up parameters"""
        self.config = config
        self.setdisprows()

    def get_selected_row(self):
        """Find selected row return -1 if none"""
        inds = self.limtab.selectedIndexes()
        if len(inds) == 0:
            return -1
        return inds[0].row()

    def get_filter_at(self, row):
        """Get filter name at specified row"""
        return str(self.limtab.item(row, 0).text())

    def check_filter_ok(self, name):
        """Check that filter isn't already defined"""
        if name in self.config.imlims:
            QtWidgets.QMessageBox.warning(self, "Limit name error", name + " is already defined")
            return True
        if len(name) != 1 or name[0] not in 'girz':
            QtWidgets.QMessageBox.warning(self, "Limit name error", name + " is only used for g r i z")
            # But carry on anyhow
        return False

    def do_edit(self, filter):
        """Work for editing whether from button press or double click"""
        origlim = copy.deepcopy(self.config.imlims[filter])
        origname = origlim.filter
        dlg = ILimDlg(self)
        dlg.copyin(origlim)
        while dlg.exec_():
            newname = dlg.checkname()
            if newname is None:
                continue
            if  origname != newname:
                if self.check_filter_ok(newname):
                    continue
                del self.config.imlims[origname]
            self.config.imlims[newname] = dlg.copyout()
            self.setdisprows()
            break

    def on_newlimit_clicked(self, b=None):
        if b is None: return
        posslim = remgeom.Imlimits()
        posslim.name = "EditMe"
        dlg = ILimDlg(self)
        dlg.copyin(posslim)
        while dlg.exec_():
            newname = dlg.checkname()
            if newname is None:
                continue
            if self.check_filter_ok(newname):
                continue
            newlim = dlg.copyout()
            self.config.imlims[newname] = newlim
            self.setdisprows()
            break

    def on_editlimit_clicked(self, b=None):
        if b is None: return
        row = self.get_selected_row()
        if row < 0:
            return
        self.do_edit(self.get_filter_at(row))

    def on_dellimit_clicked(self, b=None):
        if b is None: return
        row = self.get_selected_row()
        if row < 0:
            return
        filter = self.get_filter_at(row)
        if QtWidgets.QMessageBox.question(self, "Are you sure", "Sure you want to delete " + filter,
            QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No) != QtWidgets.QMessageBox.Yes:
            return
        del self.config.imlims[filter]
        self.setdisprows()

    def on_fetchdb_clicked(self, b=None):
        if b is None: return
        try:
            dbase, dbcurs = remdefaults.opendb()
        except dbops.dbopsError as e:
            QtWidgets.QMessageBox.warning(self, "Database error", "Got error " + e.args[0])
            return
        try:
            dbcurs.execute("SELECT MIN(rows),MIN(cols),filter FROM obsinf WHERE rows IS NOT NULL GROUP BY filter")
            dbrows = dbcurs.fetchall()
            obsrows = dict()
            obscols = dict()
            for minr, minc, filt in dbrows:
                obsrows[filt] = minr
                obscols[filt] = minc

            dbcurs.execute("SELECT MIN(rows),MIN(cols),filter FROM iforbinf WHERE rows IS NOT NULL GROUP BY filter")
            dbrows = dbcurs.fetchall()

            for minr, minc, filt in dbrows:
                try:
                    if minr < obsrows[filt]:
                        obsrows[filt] = minr
                    if minc < obscols[filt]:
                        obscols[filt] = minc
                except KeyError:
                    obsrows[filt] = minr
                    obscols[filt] = minc

            dbase.close()
        except pymysql.InternalError as e:
            QtWidgets.QMessageBox.warning(self, "Database error", "Got error " + e.args[1])
            return

        self.config.imlims = dict()
        for f in 'girz':
            try:
                self.config.imlims[f] = remgeom.Imlimits(filter=f, rows=obsrows[f], cols=obscols[f])
            except KeyError:
                pass
        self.setdisprows()

    def on_limtab_cellDoubleClicked(self, row, column):
        self.do_edit(self.get_filter_at(row))
