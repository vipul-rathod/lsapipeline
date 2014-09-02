from tank.platform.qt import QtCore, QtGui

def Icon(icon = ''):
    """
    @param icon: The name of the icon to use eg refresh.png
    @type icon: String  
    """
    iconPath = "T:/software/lsapipeline/config/icons/"

    fullPath = '%s%s' % (iconPath, icon)
    icon = QtGui.QIcon(fullPath)
    return icon