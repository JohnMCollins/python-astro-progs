# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'xscaleoffdlg.ui'
#
# Created: Wed Mar 19 11:03:51 2014
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_scaleoffdlg(object):
    def setupUi(self, scaleoffdlg):
        scaleoffdlg.setObjectName("scaleoffdlg")
        scaleoffdlg.resize(701, 469)
        self.buttonBox = QtGui.QDialogButtonBox(scaleoffdlg)
        self.buttonBox.setGeometry(QtCore.QRect(440, 410, 221, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.groupBox = QtGui.QGroupBox(scaleoffdlg)
        self.groupBox.setGeometry(QtCore.QRect(60, 40, 551, 171))
        self.groupBox.setObjectName("groupBox")
        self.xmin = QtGui.QLineEdit(self.groupBox)
        self.xmin.setGeometry(QtCore.QRect(80, 40, 141, 27))
        self.xmin.setReadOnly(True)
        self.xmin.setObjectName("xmin")
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(20, 40, 62, 17))
        self.label.setObjectName("label")
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(270, 40, 62, 17))
        self.label_2.setObjectName("label_2")
        self.xmax = QtGui.QLineEdit(self.groupBox)
        self.xmax.setGeometry(QtCore.QRect(340, 40, 141, 27))
        self.xmax.setReadOnly(True)
        self.xmax.setObjectName("xmax")
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(550, 50, 62, 17))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(20, 80, 71, 17))
        self.label_4.setObjectName("label_4")
        self.xscale = QtGui.QDoubleSpinBox(self.groupBox)
        self.xscale.setGeometry(QtCore.QRect(90, 80, 181, 27))
        self.xscale.setDecimals(6)
        self.xscale.setMinimum(1e-06)
        self.xscale.setMaximum(1000000000.0)
        self.xscale.setProperty("value", 1.0)
        self.xscale.setObjectName("xscale")
        self.label_5 = QtGui.QLabel(self.groupBox)
        self.label_5.setGeometry(QtCore.QRect(290, 80, 31, 17))
        self.label_5.setObjectName("label_5")
        self.xlogscale = QtGui.QDoubleSpinBox(self.groupBox)
        self.xlogscale.setGeometry(QtCore.QRect(340, 80, 181, 27))
        self.xlogscale.setDecimals(6)
        self.xlogscale.setMinimum(-5.0)
        self.xlogscale.setMaximum(9.0)
        self.xlogscale.setSingleStep(0.01)
        self.xlogscale.setObjectName("xlogscale")
        self.label_6 = QtGui.QLabel(self.groupBox)
        self.label_6.setGeometry(QtCore.QRect(20, 120, 71, 17))
        self.label_6.setObjectName("label_6")
        self.xoffset = QtGui.QDoubleSpinBox(self.groupBox)
        self.xoffset.setGeometry(QtCore.QRect(90, 120, 181, 27))
        self.xoffset.setDecimals(6)
        self.xoffset.setObjectName("xoffset")
        self.forcethrough = QtGui.QCheckBox(self.groupBox)
        self.forcethrough.setGeometry(QtCore.QRect(340, 120, 141, 22))
        self.forcethrough.setObjectName("forcethrough")
        self.resetx = QtGui.QPushButton(self.groupBox)
        self.resetx.setGeometry(QtCore.QRect(340, 140, 92, 27))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.resetx.setFont(font)
        self.resetx.setObjectName("resetx")
        self.groupBox_2 = QtGui.QGroupBox(scaleoffdlg)
        self.groupBox_2.setGeometry(QtCore.QRect(60, 210, 551, 171))
        self.groupBox_2.setObjectName("groupBox_2")
        self.ymin = QtGui.QLineEdit(self.groupBox_2)
        self.ymin.setGeometry(QtCore.QRect(80, 40, 141, 27))
        self.ymin.setReadOnly(True)
        self.ymin.setObjectName("ymin")
        self.label_7 = QtGui.QLabel(self.groupBox_2)
        self.label_7.setGeometry(QtCore.QRect(20, 40, 62, 17))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtGui.QLabel(self.groupBox_2)
        self.label_8.setGeometry(QtCore.QRect(270, 40, 62, 17))
        self.label_8.setObjectName("label_8")
        self.ymax = QtGui.QLineEdit(self.groupBox_2)
        self.ymax.setGeometry(QtCore.QRect(340, 40, 141, 27))
        self.ymax.setReadOnly(True)
        self.ymax.setObjectName("ymax")
        self.label_9 = QtGui.QLabel(self.groupBox_2)
        self.label_9.setGeometry(QtCore.QRect(550, 50, 62, 17))
        self.label_9.setObjectName("label_9")
        self.label_10 = QtGui.QLabel(self.groupBox_2)
        self.label_10.setGeometry(QtCore.QRect(20, 80, 71, 17))
        self.label_10.setObjectName("label_10")
        self.yscale = QtGui.QDoubleSpinBox(self.groupBox_2)
        self.yscale.setGeometry(QtCore.QRect(90, 80, 181, 27))
        self.yscale.setDecimals(6)
        self.yscale.setMinimum(1e-06)
        self.yscale.setMaximum(1000000000.0)
        self.yscale.setProperty("value", 1.0)
        self.yscale.setObjectName("yscale")
        self.label_11 = QtGui.QLabel(self.groupBox_2)
        self.label_11.setGeometry(QtCore.QRect(290, 80, 31, 17))
        self.label_11.setObjectName("label_11")
        self.ylogscale = QtGui.QDoubleSpinBox(self.groupBox_2)
        self.ylogscale.setGeometry(QtCore.QRect(340, 80, 181, 27))
        self.ylogscale.setDecimals(6)
        self.ylogscale.setMinimum(-5.0)
        self.ylogscale.setMaximum(9.0)
        self.ylogscale.setSingleStep(0.01)
        self.ylogscale.setObjectName("ylogscale")
        self.label_12 = QtGui.QLabel(self.groupBox_2)
        self.label_12.setGeometry(QtCore.QRect(20, 120, 71, 17))
        self.label_12.setObjectName("label_12")
        self.yoffset = QtGui.QDoubleSpinBox(self.groupBox_2)
        self.yoffset.setGeometry(QtCore.QRect(90, 120, 181, 27))
        self.yoffset.setDecimals(6)
        self.yoffset.setObjectName("yoffset")
        self.resety = QtGui.QPushButton(self.groupBox_2)
        self.resety.setGeometry(QtCore.QRect(340, 120, 92, 27))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.resety.setFont(font)
        self.resety.setObjectName("resety")

        self.retranslateUi(scaleoffdlg)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), scaleoffdlg.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), scaleoffdlg.reject)
        QtCore.QMetaObject.connectSlotsByName(scaleoffdlg)
        scaleoffdlg.setTabOrder(self.xmin, self.xmax)
        scaleoffdlg.setTabOrder(self.xmax, self.xscale)
        scaleoffdlg.setTabOrder(self.xscale, self.xlogscale)
        scaleoffdlg.setTabOrder(self.xlogscale, self.xoffset)
        scaleoffdlg.setTabOrder(self.xoffset, self.forcethrough)
        scaleoffdlg.setTabOrder(self.forcethrough, self.resetx)
        scaleoffdlg.setTabOrder(self.resetx, self.ymin)
        scaleoffdlg.setTabOrder(self.ymin, self.ymax)
        scaleoffdlg.setTabOrder(self.ymax, self.yscale)
        scaleoffdlg.setTabOrder(self.yscale, self.ylogscale)
        scaleoffdlg.setTabOrder(self.ylogscale, self.yoffset)
        scaleoffdlg.setTabOrder(self.yoffset, self.resety)
        scaleoffdlg.setTabOrder(self.resety, self.buttonBox)

    def retranslateUi(self, scaleoffdlg):
        scaleoffdlg.setWindowTitle(QtGui.QApplication.translate("scaleoffdlg", "Scaling and Offsets", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("scaleoffdlg", "X Scaling and offset", None, QtGui.QApplication.UnicodeUTF8))
        self.xmin.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "Current minimum X", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("scaleoffdlg", "From", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("scaleoffdlg", "to", None, QtGui.QApplication.UnicodeUTF8))
        self.xmax.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "Current maximum X", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("scaleoffdlg", "to", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("scaleoffdlg", "Scale by", None, QtGui.QApplication.UnicodeUTF8))
        self.xscale.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "This is the scaling factor to be applied to the X values", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("scaleoffdlg", "Log", None, QtGui.QApplication.UnicodeUTF8))
        self.xlogscale.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "This is the base 10 log of the scaling factor to be applied to the X values.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("scaleoffdlg", "Offset by", None, QtGui.QApplication.UnicodeUTF8))
        self.xoffset.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">This is the offset to be applied to the X values <span style=\" font-weight:600;\">after</span> scaling.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.forcethrough.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Force settings throughout data</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600; color:#ff0000;\">Beware!!!!</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.forcethrough.setText(QtGui.QApplication.translate("scaleoffdlg", "Force through", None, QtGui.QApplication.UnicodeUTF8))
        self.resetx.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Cancel all the X scale and offsets and set to 0.0 and 1.0</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt; color:#ff0000;\">Be careful!!!</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.resetx.setText(QtGui.QApplication.translate("scaleoffdlg", "Reset", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("scaleoffdlg", "Y Scaling and offset", None, QtGui.QApplication.UnicodeUTF8))
        self.ymin.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "Current minimum Y", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("scaleoffdlg", "From", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("scaleoffdlg", "to", None, QtGui.QApplication.UnicodeUTF8))
        self.ymax.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "Current maximum Y", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("scaleoffdlg", "to", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("scaleoffdlg", "Scale by", None, QtGui.QApplication.UnicodeUTF8))
        self.yscale.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "This is the scaling factor to be applied to the Y values", None, QtGui.QApplication.UnicodeUTF8))
        self.label_11.setText(QtGui.QApplication.translate("scaleoffdlg", "Log", None, QtGui.QApplication.UnicodeUTF8))
        self.ylogscale.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "This is the base 10 log of the scaling factor to be applied to the Y values.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_12.setText(QtGui.QApplication.translate("scaleoffdlg", "Offset by", None, QtGui.QApplication.UnicodeUTF8))
        self.yoffset.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">This is the offset to be applied to the Y values <span style=\" font-weight:600;\">after</span> scaling.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.resety.setToolTip(QtGui.QApplication.translate("scaleoffdlg", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Cancel all the Y scale and offsets and set to 0.0 and 1.0</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt; color:#ff0000;\">Be careful!!!</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.resety.setText(QtGui.QApplication.translate("scaleoffdlg", "Reset", None, QtGui.QApplication.UnicodeUTF8))

