"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db

NOTE THIS IMPORTS THE CACHES AND REBULDS THE OCEAN
THE OCEAN IS REATTACHED TO MARKS SHADED OCEAN WHEN THE SHADERS ARE REBUILT!

"""
import os, getpass, sys, sgtk
import tank.templatekey
import shutil
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError
import pymel.core as pm

if 'T:/software/lsapipeline/custom' not in sys.path:
## Now get the custom tools
    sys.path.append('T:/software/lsapipeline/custom')

## Append custome script path to import the custom modules
if 'T:/software/lsapipeline/install/apps/tk-bbb-splitLayoutShots/splitLayoutShots' not in sys.path:
    sys.path.append('T:/software/lsapipeline/install/apps/tk-bbb-splitLayoutShots/splitLayoutShots')
## Custom modules for layout shot info
import shotFrameRange
import shiftAnimCurves
import core_archive_readXML as readXML
import utils as utils
import maya_genericSettings as settings
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
import ProgressBarUI as pbui
import CONST as CONST

#reload(settings)
#reload(pbui)
#reload(CONST)
#reload(readXML)
#reload(shotFrameRange)
#reload(shiftAnimCurves)

###########################################################################
### NOTE I HAVE MOVED THE CONNECT CACHE METHODS INTO THE fluidCaches py!!!!!
class FetchStoryBoard(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the FetchStoryBoard application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'FetchStoryBoard Loaded...', verbose = False)

    def run_app(self):
        debug(self, method = 'run_app', message = 'FetchStoryBoard...', verbose = False)
        getDisplayName = self.get_setting('display_name')
        debug(self, method = 'run_app', message = 'getDisplayName: %s' % getDisplayName, verbose = False)
        self.engine.show_dialog(getDisplayName, self, MainUI, self)

class MainUI(QtGui.QWidget):
    def __init__(self, app):
        """
        """
        QtGui.QWidget.__init__(self)
        self.app = app
#         debug(self.app, method = 'MainUI.__init__', message = 'Running app...', verbose = False)

        self.context = self.app.context ## To get the step
#         debug(app = self.app, method = 'MainUI.__init__', message = 'context: %s' % self.context, verbose = False)

        if self.context.step['name'] == 'Blocking':
            self.tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")

        ################### UI LOAD / BUILD NOW
        ## Now build the UI
        self.mainLayout = QtGui.QVBoxLayout(self)

        ## Setup the layout and buttons
        self.buttonLayout = QtGui.QHBoxLayout()
        self.shotBasedSBoardButton = QtGui.QPushButton('Fetch StoryBoard')
        self.shotBasedSBoardButton.clicked.connect(self._singleShotSBoard)
        ## Add the buttons to their layout widget
        self.buttonLayout.addWidget(self.shotBasedSBoardButton)
        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addStretch(1)
        self.resize(300, 20)

    def _singleShotSBoard(self):
        if len(cmds.ls('*_shotCam')) <2:
            camName = cmds.ls('*_shotCam')
            if camName:
                shotName = camName[0].split('_shotCam')[0]
                rootPath = 'I:/lsapipeline/episodes/'
                epName = shotName.split('_')[0]
                epPath = os.path.join(rootPath, epName)
                subFolderPath = 'SBoard/publish/review/'
                path = os.path.join(os.path.join(epPath, shotName), subFolderPath)              #    Path: I:/lsapipeline/episodes/ep122\ep122_sh035\SBoard/publish/review/
#                 print "Path: %s" % path
                if os.path.exists(path):
                    listOfMovs = os.listdir(path)                                               #    ['ep122_sh031_BOARD.v000', 'ep122_sh031_BOARD.v000.mov', 'ep122_sh031_BOARD.v001', 'ep122_sh031_BOARD.v001.mov']
                    if listOfMovs:
                        listOfMovies = []
                        for mov in sorted(listOfMovs):
                            if mov.endswith('mov') or mov.endswith('MOV'):
                                listOfMovies.append(mov)
                                newFolderName = os.path.splitext(mov)[0]                        #    New Folder Name: ep122_sh035_BOARD.v000
#                                 print "New Folder Name: %s" % newFolderName
                                movPaths = os.path.join(path, mov)                              #    Mov Paths: I:/lsapipeline/episodes/ep122\ep122_sh035\SBoard/publish/review/ep122_sh035_BOARD.v000.mov
#                                 print "Mov Paths: %s" % movPaths
                                frameFolderPath = os.path.join(path, newFolderName)             #    frameFolderPath: I:/lsapipeline/episodes/ep122\ep122_sh035\SBoard/publish/review/ep122_sh035_BOARD.v000
#                                 print "frameFolderPath: %s" % frameFolderPath
                                framePath = os.path.join(frameFolderPath, newFolderName)        #    Frame Path: I:/lsapipeline/episodes/ep122\ep122_sh035\SBoard/publish/review/ep122_sh035_BOARD.v000\ep122_sh035_BOARD.v000
#                                 print "Frame Path: %s" % framePath
                                if not os.path.exists(os.path.join(path, newFolderName)):
                                    os.mkdir(frameFolderPath)
                                    ffmpegPath = '//192.168.5.253/BBB_main/bbb/t/dev_installers/ffmpeg/bin/ffmpeg.exe -i ' + "\"%s\"" % (movPaths) + ' -vf scale=480:270 -r 25' + ' %s' % framePath + '.%03d.jpg'
                                    os.system(ffmpegPath)
                                else:
                                    ffmpegPath = '//192.168.5.253/BBB_main/bbb/t/dev_installers/ffmpeg/bin/ffmpeg.exe -i ' + "\"%s\"" % (movPaths) + ' -vf scale=480:270 -r 25' + ' %s' % framePath + '.%03d.jpg'
                                    os.system(ffmpegPath)
                        frameFolderName = os.path.splitext(sorted(listOfMovies)[-1])[0]         #    Frame Folder Name: ep122_sh035_BOARD.v001
        #                     print "Frame Folder Name: %s" % frameFolderName
                        latestFramePath = os.path.join(path, frameFolderName, '%s.001.jpg' % frameFolderName)   #    Latest Frame Path: I:/lsapipeline/episodes/ep122\ep122_sh035\SBoard/publish/review/ep122_sh035_BOARD.v001\ep122_sh035_BOARD.v001.001.jpg
        #                     print "Latest Frame Path: %s" % latestFramePath 
                        self._createCamForSBoard(shotName, latestFramePath)
                    else:
                        sys.stderr.write("No movs found")
                else:
                    sys.stderr.write("Path doesn't exists.\n%s" % path)
                    sys.stderr.write("\nDone\n")

        else:
            sys.stderr.write("There are multiple cameras in the scene. Tool cannot be executed in this shot")

    def _createCamForSBoard(self, shotName, framePath):
        camName = '%s_shotCam' % shotName
        if cmds.objExists(camName):
            if not cmds.objExists('%s_animaticsCam' % shotName):
                dupCamList = cmds.duplicate(camName)
                for each in dupCamList:
                    if 'shotCam' in each:
                        animCam = cmds.rename(each, '%s_animaticsCam' % shotName)
                        imagePlaneShape = cmds.imagePlane(n = '%s_ip' % shotName, c='%sShape' % animCam)[-1]
                        cmds.setAttr('%s.imageName' % imagePlaneShape, '%s' % framePath, type='string')
                        cmds.setAttr('%s.useFrameExtension' % imagePlaneShape, 1)
            else:
                imagePlanes = cmds.listConnections('%s_animaticsCamShape' % shotName, s=1)
                if imagePlanes:
                    imagePlaneShape = [each for each in imagePlanes if 'camGate' not in each][0]
                    cmds.setAttr('%s.imageName' % imagePlaneShape, '%s' % framePath, type='string')
                    cmds.setAttr('%s.useFrameExtension' % imagePlaneShape, 1)

    def destroy_app(self):
        self.log_debug("Destroying SplitLayoutShots")