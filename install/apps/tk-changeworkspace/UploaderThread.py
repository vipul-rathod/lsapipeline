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
from debug import debug
 
class UploaderThread(QtCore.QThread):
    """
    Simple worker thread that encapsulates uploading to shotgun.
    Broken out of the main loop so that the UI can remain responsive
    even though an upload is happening
    """
    def __init__(self, app, version, path_to_movie, upload_to_shotgun):
        QtCore.QThread.__init__(self)
        self._app = app
        self._version = version
        self._path_to_movie = path_to_movie
        self._upload_to_shotgun = upload_to_shotgun
        self._errors = []

    def get_errors(self):
        """
        can be called after execution to retrieve a list of errors
        """
        return self._errors

    def run(self):
        """
        Thread loop
        """
        upload_error = False

        if self._upload_to_shotgun:
            try:
                #print 'UploaderThread: Uploading to shotgun now..'
                self._app.tank.shotgun.upload("Version", self._version["id"], self._path_to_movie, "sg_uploaded_movie")
            except Exception, e:
                #print 'UploaderThread: Movie upload to Shotgun failed: %s' % e
                self._errors.append("Movie upload to Shotgun failed: %s" % e)
                upload_error = True