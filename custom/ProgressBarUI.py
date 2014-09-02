from PyQt4.QtGui import *
from PyQt4.QtCore import *
import maya.OpenMayaUI as apiUI
import sip

def getMayaWin():
    ptr = apiUI.MQtUtil.mainWindow()
    if ptr is not None:
        return sip.wrapinstance(long(ptr), QObject)
    
class ProgressBarUI(QWidget):

    def __init__(self, parent = getMayaWin(), title = 'Importing:'):
        QWidget.__init__(self, parent)
        self.layout = QVBoxLayout(self)
        #self.myImage = QPixmap(BB_CONST.SPLASH)
        # Create a progress bar and a button and add them to the main layout
        self.labelLayout = QHBoxLayout(self)
        self.mainLabel = QLabel(title)
        self.doingLabel = QLabel('')
        
        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0,100)
        self.progressBar.setValue(0)
        self.progressBarGeo = self.progressBar.rect()
        self.progressBar.setTextVisible(True)
        
        self.labelLayout.addWidget(self.mainLabel)
        self.labelLayout.addWidget(self.doingLabel)
        
        self.layout.addLayout(self.labelLayout)
        self.layout.addWidget(self.progressBar)
        self.setWindowFlags(Qt.SplashScreen)
        self.layout.addStretch(1)

    def updateProgress(self, percent = 0, doingWhat = ''):
        self.progressBar.setValue(percent)
        self.doingLabel.setText(doingWhat)
        self.repaint()
        
    def showEvent(self, e):
        QWidget.showEvent(self, e)
        self.resize(400, 50)        
        #self.move(QDesktopWidget().availableGeometry().center())
        self.move(QApplication.desktop().screen().rect().center()- self.rect().center())