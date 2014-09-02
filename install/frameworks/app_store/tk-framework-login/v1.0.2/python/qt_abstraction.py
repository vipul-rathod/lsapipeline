# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# This module can not have hard dependencies on the toolkit api since
# it is used to bootstrap the Desktop application.  Use tank if it is
# available, but make sure there is a sensible working default if toolkit
# is not yet available.
try:
    from tank.platform.qt import QtCore, QtGui
except ImportError:
    try:
        # fall back to PySide if tank is not available
        from PySide import QtCore, QtGui
    except ImportError:
        # and finally fall back to PyQt if PySide is not available
        from PyQt4 import QtCore, QtGui
