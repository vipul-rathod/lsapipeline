'''
Created on May 21, 2014

@author: bernard
'''
from PyQt4 import QtGui

def Icon(iconName):
    """
    adding name of Icon and merging it with path
    @param iconName: Name of Icon
    @type objectName: String
    --------------------------------------------
    @return: 0-fullpath of icon
    """
    iconPath = "T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean/splashTool/icon/"

    fullPath = '%s%s' % (iconPath, iconName)
    return QtGui.QIcon(fullPath)