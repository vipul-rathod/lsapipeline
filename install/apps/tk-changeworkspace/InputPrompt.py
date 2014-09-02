"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
"""

import os, getpass, sys
import tank.templatekey
import shutil
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError
import sgtk
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import maya_genericSettings as settings

class InputPrompt(QtGui.QWidget):
    """
    QInputDialog with a custom input that will try to use the currently selected item to populate the textValue
    """
    def __init__(self, parent = None, label = '', defaultText = '', getSelected = True):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.hLayout = QtGui.QHBoxLayout(self)
        self.inputLabel = QtGui.QLabel('Turn Table Group:')
        self.selInput = QtGui.QLineEdit(self)
        self.getSelButton = QtGui.QPushButton('Update From Selected')
        self.getSelButton.pressed.connect(self.updateTextFromSelected)
        self.hLayout.addWidget(self.inputLabel)
        self.hLayout.addWidget(self.selInput)
        self.hLayout.addWidget(self.getSelButton)
        
        try:
            self.selInput.setText('%s' % cmds.ls(sl= True)[0])
        except IndexError:
            pass
        self.mainLayout.addLayout(self.hLayout)
                   
    def updateTextFromSelected(self):
        try:
            self.selInput.setText('%s' % cmds.ls(sl= True)[0])
        except IndexError:
            self.selInput.setText('Select something first and try again')
            
    def getText(self):
        return str(self.selInput.text())                    