'''
Created on May 1, 2013

@author: jamesd
'''
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Widget_vr(QFrame):
    def __init__(self, parent = None):
        """ Builds a horizontal line for uis to use"""
        QFrame.__init__(self, parent)
        self.setFrameShape(QFrame.VLine) 
        self.setFrameShadow(QFrame.Sunken)
        self.setContentsMargins(1,1,1,1)