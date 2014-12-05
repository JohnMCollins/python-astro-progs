#! /usr/bin/python

import sys
import os.path
import string
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class PWidget(QWidget):
	"""Class for drawing the thing"""
	
	def __init__(self):
		super(PWidget, self).__init__(None)
		pal = QPalette()
		pal.setColor(QPalette.Background, Qt.white)
		self.setAutoFillBackground(True)
		self.setPalette(pal)

	def paintEvent(self, ev):
		im1 = QImage(800,500,QImage.Format_RGB888)
		im1.fill(Qt.white)
		p1 = QPainter()
		p1.begin(im1)
		p1.setRenderHint(QPainter.Antialiasing, True)
		p1.setPen(QPen(Qt.black, 3, Qt.SolidLine, Qt.RoundCap))
		p1.setBrush(QBrush(QColor(255,255,0), Qt.SolidPattern))
		p1.drawEllipse(150,50,500,500)
		p1.setClipRegion(QRegion(150,50,500,500,QRegion.Ellipse))
		p1.setBrush(QBrush(Qt.green, Qt.SolidPattern))
		p1.rotate(-20.0)
		p1.drawEllipse(100,80,200,140)
		p1.end()
		painter = QPainter(self)
		
		painter.drawImage(0, 0, im1)
		
	def closeEvent(self, ev = None):
		if ev is None: return
		if not os.path.exists('outfile.png'):
			id = self.winId()
			QPixmap.grabWindow(id).save('outfile.png')

app = QApplication(sys.argv)

mywid = PWidget()
mywid.show()
app.exec_()

sys.exit(0)
