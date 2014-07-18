# Mark exceptional data dialog and processing

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path
import math
import copy

import numpy as np
import scipy.integrate as si
import scipy.optimize as so
import matplotlib.pyplot as plt

import ui_markexceptdlg
import ui_markexresdlg

class Markexresdlg(QDialog, ui_markexresdlg.Ui_markexresdlg):

    def __init__(self, parent = None):
        super(Markexresdlg, self).__init__(parent)
        self.setupUi(self)

class Markexceptdlg(QDialog, ui_markexceptdlg.Ui_markexceptdlg):

    def __init__(self, parent = None):
        super(Markexceptdlg, self).__init__(parent)
        self.setupUi(self)

    def init_data(self, ctrlfile, rangefile):
        self.ctrlfile = ctrlfile
        self.rangefile = rangefile


def run_exception_marks(ctrlfile, rangefile):
    """Do the business for marking exceptions"""

    dlg = Markexceptdlg()
    dlg.init_data(ctrlfile, rangefile)
    dlg.exec_()

