# Scale and offsets dialog

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path
import math
import copy

import ui_scaleoffdlg

class ScaleOffDlg(QDialog, ui_scaleoffdlg.Ui_scaleoffdlg):

    def __init__(self, parent = None):
        super(ScaleOffDlg, self).__init__(parent)
        self.setupUi(self)
        self.xminv = 0.0
        self.xmaxv = 1e9
        self.yminv = 0.0
        self.ymaxv = 1e9

    def set_xscales(self):
        """Reset spin box parameters to something sensible after we've fiddled"""
        rang = self.xmaxv - self.xminv
        predigs = int(math.floor(math.log10(rang))) + 1
        postdigs = 8 - predigs
        step = 10**(2-postdigs)
        mx = 10**predigs
        
