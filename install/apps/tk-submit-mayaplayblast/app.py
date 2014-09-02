"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
"""

import os, getpass, sys
import tank.templatekey
import shutil
import sgtk
from tank import TankError
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
## Now get the custom tools
# if 'T:/software/DoubleBarrel/' not in sys.path:
#     sys.path.append('T:/software/DoubleBarrel/')
#     
# if 'T:/software/python-api/' not in sys.path:
#     sys.path.append('T:/software/python-api/')

if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')

if 'T:/software/lsapipeline/install/apps/tk-submit-mayaplayblast' not in sys.path:
    sys.path.append('T:/software/lsapipeline/install/apps/tk-submit-mayaplayblast')

from UploaderThread import UploaderThread
import maya_genericSettings as settings
from InputPrompt import InputPrompt
from debug import debug
# from doubleBarrel import DoubleBarrel
# import doubleBarrelWrapper as doubleBarrelWrapper
# #reload(doubleBarrelWrapper)
# #reload(settings)


class PlayBlastGenerator(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the PlayBlastGenerator application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'PlayBlastGenerator Loaded...', verbose = False)

    def run_app(self):
        debug(self, method = 'run_app', message = 'PlayBlastGenerator...', verbose = False)
        getDisplayName = self.get_setting('display_name')    
        self.engine.show_dialog(getDisplayName, self, MainUI, self)
    

class MainUI(QtGui.QWidget):
    def __init__(self, app):
        """
        main UI for the playblast options
        NOTE: This currenlty playblasts directly into the publish folder.. it'd be great to avoid this and do the move of the file on register...
        """
        QtGui.QWidget.__init__(self)
#         import time
#         start = time.time()

        self.app = app
        #self.dbWrap = DoubleBarrel
        #self.sg = doubleBarrelWrapper._getShotgunObject(self.dbWrap, self.app)
        debug(self.app, method = 'Main_UI', message = 'INIT PlayBlastGenerator UI', verbose = False)

        ## Tell the artist to be patient... eg not genY
        cmds.headsUpMessage("Building UI...", time = 1)
        self.upload_to_shotgun = self.app.get_setting("upload_to_shotgun")       
        debug(self.app, method = 'Main_UI', message = 'USER: %s' % tank.util.get_current_user(self.app.tank), verbose = False)
        self.currentEditor = self._getEditor()
        ## These two are used for the os module when doing a os.rename for windows
        self.osPathToWorkFile = ''
        self.osPathToPublishFile = ''
        debug(app = self.app, method = 'MainUI', message= 'Active Editor: %s' % self.currentEditor, verbose = False)
        ## Check to make sure there is a valid context set
        if self.app.context.entity is None:
            debug(app = self.app, message = "Cannot load the PlayBlast application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.", verbose = False)
        debug(app = self.app, method = 'MainUI', message= 'ValidContextFound', verbose = False)
        
        ## Setup the main UI
        debug(app = self.app, method = 'MainUI', message= 'Building MainUI', verbose = False)
        self.mainLayout = QtGui.QVBoxLayout(self)       
        self.infoGroupBox = QtGui.QGroupBox(self)
        self.infoGroupBox.setTitle('Info')
        self.hLayout = QtGui.QHBoxLayout(self.infoGroupBox)
        self.renderWidthLabel = QtGui.QLabel('Width: %s' % self.app.get_setting('movie_width'))
        self.renderHeightLabel = QtGui.QLabel('Height: %s' % self.app.get_setting('movie_height'))
        self.codecLabel = QtGui.QLabel('Codec: MPEG-4 Video')
        self.formatLabel = QtGui.QLabel('Format: mov')
        self.hLayout.addWidget(self.renderWidthLabel)
        self.hLayout.addWidget(self.renderHeightLabel)
        self.hLayout.addWidget(self.codecLabel)
        self.hLayout.addWidget(self.formatLabel)
        
        debug(app = self.app, method = 'MainUI', message= 'Installers Path %s' % self.app.get_setting('installPath'), verbose = False)
        if self.app.get_setting('installPath') != '':
            debug(app = self.app, method = 'MainUI', message= 'Installers Path found', verbose = False)
            self.installCodecButton = QtGui.QPushButton('Install Codec')
            if sys.platform == 'win32':
                debug(app = self.app, method = 'MainUI', message= 'Installers is Win32', verbose = False)
                self.installCodecButton.pressed.connect(partial(self._installCodec, 'LagarithSetup_1327.exe'))
            self.hLayout.addWidget(self.installCodecButton)
            debug(app = self.app, method = 'MainUI', message= 'Install Path Registered', verbose = False)
            
        debug(app = self.app, method = 'MainUI', message= 'Building cameraSettings', verbose = False)
        self.cameraSettingsGroupBox = QtGui.QGroupBox(self)
        self.cameraSettingsGroupBox.setTitle('Camera Settings')
        self.camGridLayout = QtGui.QGridLayout(self.cameraSettingsGroupBox)
        self.maxColumns = 4
        ## Process all the stupid maya options for the camera settings for the playblast.
        self.optionsList = ['NURBS Curves', 'NURBS Surfaces', 'Polygons', 'Subdiv Surfaces', 'Planes', 'Lights', 'Cameras', 'Joints', 'IK Handles', 'Deformers', 'Dynamics',
                                        'Fluids', 'nParticles', 'nRigids', 'Dynamic Constraints', 'Locators', 'Dimensions', 'Pivots', 'Handles', 'Texture Placements', 'Strokes', 'Motion Trails', 
                                        'Plugin Shapes', 'Manipulators', 'Clip Ghosts', 'GPU Caches', 'Nurbs CVs', 'NURBS Hulls', 'Grid', 'HUD', 'Image Planes']
        self.renderOptions = ['WireFrame', 'SmoothShade All', 'Manipulators']
        self.defaultOn = ['Polygons', 'HUD', 'NURBS Surfaces', 'GPU Caches', 'Plugin Shapes', 'Image Planes']
        self.camRadioButtons = []
        self.row = 0
        self.col = 0
        for eachRButton in self.optionsList:
            self.myButton = QtGui.QRadioButton(eachRButton)
            self.myButton.setAutoExclusive(False)
            self.camRadioButtons.append(self.myButton)
            ## Now add the radio button to the layout
            self.camGridLayout.addWidget(self.myButton, self.row, self.col)
            if eachRButton in self.defaultOn:
                self.myButton.setChecked(True)
            ## Now increase column by 1
            self.col = self.col + 1
            ## Check to see if at last column, if so reset columns and add one to row.
            if self.col == self.maxColumns:
                self.row = self.row + 1
                self.col = 0
            self.myButton.toggled.connect(self._processRadioButtons)
        debug(app = self.app, method = 'MainUI', message= 'Building viewportSettings', verbose = False)
        self.viewportSettingsGroupBox = QtGui.QGroupBox(self)
        self.viewportSettingsGroupBox.setTitle('Viewport Settings')
        self.viewportGridLayout = QtGui.QGridLayout(self.viewportSettingsGroupBox)
        self.viewportOptions = ['WireFrame', 'SmoothShade All', 'Bounding Box', 'Use Default Mat', 'X-Ray', 'X-Ray Joints', 'Hardware Texturing', 'Wireframe on Shaded']
        self.defaultOn = ['SmoothShade All', 'Viewport 2.0']
        self.viewportRadioButtons = []
        self.row = 0
        self.col = 0
        for eachRButton in self.viewportOptions:
            self.myButton = QtGui.QRadioButton(eachRButton)
            if eachRButton == 'WireFrame' or eachRButton == 'SmoothShade All' or eachRButton == 'Bounding Box':
                self.myButton.setAutoExclusive(True)
            else:
                self.myButton.setAutoExclusive(False)
            self.viewportRadioButtons.append(self.myButton)
            ## Now add the radio button to the layout
            self.viewportGridLayout.addWidget(self.myButton, self.row, self.col)
            if eachRButton in self.defaultOn:
                self.myButton.setChecked(True)
            ## Now increase column by 1
            self.col = self.col + 1
            ## Check to see if at last column, if so reset columns and add one to row.
            if self.col == self.maxColumns:
                self.row = self.row + 1
                self.col = 0
            self.myButton.toggled.connect(self._processRadioButtons)

        debug(app = self.app, method = 'MainUI', message= 'Building renderSettings', verbose = False)
        self.rendererSettingsGroupBox = QtGui.QGroupBox(self)
        self.rendererSettingsGroupBox.setTitle('Renderer Settings')
        self.rendererGridLayout = QtGui.QGridLayout(self.rendererSettingsGroupBox)
        self.rendererOptions = ['Default Renderer', 'Viewport 2.0']
        self.defaultOn = [ 'Default Renderer']
        self.rendererRadioButtons = []
        self.row = 0
        self.col = 0
        for eachRButton in self.rendererOptions:
            self.myButton = QtGui.QRadioButton(eachRButton)
            self.myButton.setAutoExclusive(True)
            self.rendererRadioButtons.append(self.myButton)
            ## Now add the radio button to the layout
            self.rendererGridLayout.addWidget(self.myButton, self.row, self.col)
            if eachRButton in self.defaultOn:
                self.myButton.setChecked(True)
            ## Now increase column by 1
            self.col = self.col + 1
            ## Check to see if at last column, if so reset columns and add one to row.
            if self.col == self.maxColumns:
                self.row = self.row + 1
                self.col = 0
            self.myButton.toggled.connect(self._processRadioButtons)

        debug(app = self.app, method = 'MainUI', message= 'Building extra settings', verbose = False)
        self.extraSettingsGroupBox = QtGui.QGroupBox(self)
        self.extraSettingsGroupBox.setTitle('Extra Settings')
        self.extraGridLayout = QtGui.QGridLayout(self.extraSettingsGroupBox)
        self.extraOptions = ['Shaded Eyes on Hardware Texturing']
        self.defaultOn = ['Shaded Eyes on Hardware Texturing']
        self.rendererRadioButtons = []
        self.row = 0
        self.col = 0
        for eachRButton in self.extraOptions:
            self.myButton = QtGui.QRadioButton(eachRButton)
            self.myButton.setAutoExclusive(True)
            self.rendererRadioButtons.append(self.myButton)
            ## Now add the radio button to the layout
            self.extraGridLayout.addWidget(self.myButton, self.row, self.col)
            if eachRButton in self.defaultOn:
                self.myButton.setChecked(True)
            ## Now increase column by 1
            self.col = self.col + 1
            ## Check to see if at last column, if so reset columns and add one to row.
            if self.col == self.maxColumns:
                self.row = self.row + 1
                self.col = 0
            self.myButton.toggled.connect(self._processRadioButtons)

        self.extraGridLayout.setColumnStretch (self.maxColumns + 1,1)

        if self.app.get_setting('isAsset'):
            debug(app = self.app, method = 'MainUI', message= 'Showing Asset UI', verbose = False)
            self._buildAssetTurntableUI()
        else:
            debug(app = self.app, method = 'MainUI', message= 'Skipping Asset UI', verbose = False)
        
        debug(app = self.app, method = 'MainUI', message= 'Building Comment Layout', verbose = False)
        ## Now the comment layout
        self.commentGroupBox = QtGui.QGroupBox(self)
        self.commentGroupBox.setTitle('Comment -- required!')
        self.hLayout = QtGui.QHBoxLayout(self.commentGroupBox)
        self.commentLabel = QtGui.QLabel('Set Comment:')
        self.comment = QtGui.QLineEdit(self)
        self.hLayout.addWidget(self.commentLabel)
        self.hLayout.addWidget(self.comment)
        
        debug(app = self.app, method = 'MainUI', message= 'Building Submission Layout', verbose = False)
        
        ## Now the submission area
        self.submissionGroupBox = QtGui.QGroupBox(self)
        self.submissionGroupBox.setTitle('Submission')
        self.submissionlayout = QtGui.QHBoxLayout(self.submissionGroupBox)
        debug(app = self.app, method = 'MainUI', message= 'self.submissionlayout built...', verbose = False)
        ## Quality Spinbox
        self.qualityPercentage = 75
        self.qualityLabel = QtGui.QLabel('Quality:')
        self.qualityPercent = QtGui.QSpinBox(self)
        debug(app = self.app, method = 'MainUI', message= 'self.qualityPercent built...', verbose = False)
        self.qualityPercent.setRange(0, 100)
        debug(app = self.app, method = 'MainUI', message= 'self.qualityPercent setRange...', verbose = False)
        self.qualityPercent.setValue(75)
        debug(app = self.app, method = 'MainUI', message= 'self.qualityPercent built...', verbose = False)
        ## Quality Spinbox
        self.sizePercentage = 75
        self.sizeLabel = QtGui.QLabel('Scale:')
        self.sizePercent = QtGui.QSpinBox(self)
        debug(app = self.app, method = 'MainUI', message= 'self.sizePercent built...', verbose = False)
        self.sizePercent.setRange(0, 100)
        debug(app = self.app, method = 'MainUI', message= 'self.sizePercent setRange...', verbose = False)
        self.sizePercent.setValue(75)
        debug(app = self.app, method = 'MainUI', message= 'self.sizePercent built...', verbose = False)
        ## Build the upload button
        self.upload = QtGui.QRadioButton('Submit to shotgun?')
        self.upload.setAutoExclusive(False)
        self.upload.setChecked(False)
        self.upload.toggled.connect(self._uploadToggle)
        ## Build the main go button
        self.goButton = QtGui.QPushButton('Playblast...')
        self.goButton.setMinimumWidth(350)
        self.goButton.released.connect(self.doPlayblast)
        
        self.submissionlayout.addWidget(self.qualityLabel)
        self.submissionlayout.addWidget(self.qualityPercent)
        self.submissionlayout.addWidget(self.sizeLabel)
        self.submissionlayout.addWidget(self.sizePercent)
        ## Check to see if the attr in the _step.yml is looking to upload to shotgun or not.
        ## If it is show the upload options and set the button to true
        if self.upload_to_shotgun:
            self.submissionlayout.addWidget(self.upload)
            self.upload.setChecked(True)

        ## Check if we are an asset or a shot, and show the option to delete the turnTable group after playblasting
        if self.app.get_setting('isAsset'):
            debug(app = self.app, method = 'MainUI', message= 'Adding Asset Submission Stuff', verbose = False)
            self.deleteHrcGrp = QtGui.QRadioButton('Delete Turntable Grp?')
            self.deleteHrcGrp.setAutoExclusive(False)
            self.submissionlayout.addWidget(self.deleteHrcGrp)
        else:
            debug(app = self.app, method = 'MainUI', message= 'Skipping Asset Submission Stuff', verbose = False)
        
        
        ## Now add the go button regardless of shot or asset step
        self.submissionlayout.addWidget(self.goButton)
        self.submissionlayout.addStretch(1)
        debug(app = self.app, method = 'MainUI', message= 'Adding All to mainLayout now..', verbose = False)

        
        ## Now add to the mainLayout
        self.mainLayout.addWidget(self.infoGroupBox)
        self.mainLayout.addWidget(self.cameraSettingsGroupBox)
        self.mainLayout.addWidget(self.viewportSettingsGroupBox)
        self.mainLayout.addWidget(self.rendererSettingsGroupBox)
        self.mainLayout.addWidget(self.extraSettingsGroupBox)
        if self.app.get_setting('isAsset'):
            debug(app = self.app, method = 'MainUI', message= 'Adding Asset TurnTable to mainLayout now..', verbose = False)
            self.mainLayout.addWidget(self.turnTableGroupBox)
        else:
            debug(app = self.app, method = 'MainUI', message= 'Looking for shot camera now..', verbose = False)
            self._setupShotCamera()
        self.mainLayout.addWidget(self.commentGroupBox)
        self.mainLayout.addWidget(self.submissionGroupBox)
        self.mainLayout.addStretch(1)

        ## Process all the radio button options
        self._processRadioButtons()
        debug(app = self.app, method = 'MainUI', message= '_processRadioButtons successful...', verbose = False)
        
        ## Now set the render globals again
        if self.app.get_setting('isAsset'):
            self._setRenderGlobals(animation = False)
        else:
            self._setRenderGlobals(animation = True)

        ## Turn on certain HUD during playblast UI build
        mel.eval('setFocalLengthVisibility(on);')
        mel.eval('setCurrentFrameVisibility(on);')
        mel.eval('setCameraNamesVisibility(on);')
        mel.eval('setSceneTimecodeVisibility(on);')

        ## Force the color to white
        cmds.displayColor('headsUpDisplayLabels', 16)
        cmds.displayColor('headsUpDisplayValues', 16)

        debug(app = self.app, method = 'MainUI', message= 'UI Built Successfully...', verbose = False)
        #print 'TIME: %s' % (time.time()-start)

    def _uploadToggle(self):
        if self.upload.isChecked():
             self.commentGroupBox.show()
        else:
            self.commentGroupBox.hide()

    def _installCodec(self, codec):
        installerPath = self.app.get_setting('installPath')
        if sys.platform == 'win32':
            os.system('%s\\%s' % (installerPath, codec))
         
    def _getEditor(self):
        currentPanel = cmds.getPanel(withFocus = True)
        if 'modelPanel' not in currentPanel:
            QtGui.QMessageBox.information(None, "Aborted...", 'You must have active a current 3D viewport! \nRight click the viewport you wish to playblast from.')
            return -1
        else:
            currentEditor = cmds.modelPanel(currentPanel, q = True, modelEditor = True)
            debug(app = self.app, method = '_getEditor', message= 'Current Editor is: %s' % currentEditor, verbose = False)
            self.currentEditor = currentEditor
            return currentEditor

    def _setupShotCamera(self):
        """
        Shot camera setup
        """
        cameraSuffix = self.app.get_setting('cameraSuffix')
        camera = []
        debug(app = self.app, method = '_setupShotCamera', message= 'Finding camera..', verbose = False)
        for each in cmds.ls(type = 'camera'):
            getCamTransform = cmds.listRelatives(each, parent = True)[0]
            debug(app = self.app, method = '_setupShotCamera', message= 'getCamTransform.. %s' % getCamTransform, verbose = False)
            if cmds.objExists('%s.type' % getCamTransform):
                camera.append(each)

        debug(app = self.app, method = '_setupShotCamera', message= 'List of cameras found: %s' % camera, verbose = False)
        
        if not camera:
            debug(app = self.app, method = '_setupShotCamera',  message ="No shotCam found!", verbose = False)
            QtGui.QMessageBox.information(None, "Aborted...", 'No shotCam found!!')
            return -1
        else:
            if len(camera) > 1:
                debug(app = self.app, method = '_setupShotCamera',  message ="More than one camera found. Please make sure you only have one shot camera in your scene!", verbose = False)
                QtGui.QMessageBox.information(None, "Aborted...", 'Make sure you have only ONE shot camera in the scene!')
                return -1
            else:
                cam = camera[0]
                cmds.modelEditor(self.currentEditor, edit = True, camera = cam)
                getCamTransform = cmds.listRelatives(cam, parent = True)[0] ## need to send the camera transform to this function
                settings._setCameraDefaults(getCamTransform)

    def _buildAssetTurntableUI(self):
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'Entering _buildAssetTurntableUI now....', verbose = False)
        self.turnTableGroupBox = QtGui.QGroupBox(self)
        self.turnTableGroupBox.setTitle('Turn Table Setup')
        self.turnTableGridLayout = QtGui.QGridLayout(self.turnTableGroupBox)
        self.buildTurnTableButton = QtGui.QPushButton('BuildTurnTable')
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'Building InputPrompt now....', verbose = False)
        self.inputPromptUI = InputPrompt(self, label = 'TurnTableGroup', defaultText = '', getSelected = True)
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'self.inputPromptUI .... %s' % self.inputPromptUI, verbose = False)
        
        self.frameRangeLayout = QtGui.QHBoxLayout(self)
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'Building frameRange layout now....', verbose = False)
        self.startFrameLabel = QtGui.QLabel('Start Frame:')
        ## Start Frame
        self.startFrame = QtGui.QSpinBox(self)
        self.startFrame.setRange(-10000000, 100000000)
        self.startFrame.setValue(1)
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'self.startFrame Done....', verbose = False)
        ## Frame count
        self.totalFramesLabel = QtGui.QLabel('Total # of Frames:')
        self.totalFrames = QtGui.QSpinBox(self)
        self.totalFrames.setRange(0, 100000000)
        self.totalFrames.setValue(100)
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'self.totalFrames Done....', verbose = False)
        self.frameRangeLayout.addWidget(self.startFrameLabel)
        self.frameRangeLayout.addWidget(self.startFrame)
        self.frameRangeLayout.addWidget(self.totalFramesLabel)
        self.frameRangeLayout.addWidget(self.totalFrames)
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'frameRangeLayout widgets Done....', verbose = False)
        ## Now the go button
        self.buildTurnTableButton = QtGui.QPushButton('Setup Turn Table')
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'self.buildTurnTableButton Done....', verbose = False)
        self.buildTurnTableButton.pressed.connect(partial(self._setupTurnTable, self.inputPromptUI, self.startFrame, self.totalFrames))
        ## Now add the ui elements back to the layout
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'self.turnTableGridLayout building now....', verbose = False)
        self.turnTableGridLayout.addWidget(self.inputPromptUI, 0,0)
        self.turnTableGridLayout.addLayout(self.frameRangeLayout, 1,0)
        self.turnTableGridLayout.addWidget(self.buildTurnTableButton, 2,0)
        debug(app = self.app, method = '_buildAssetTurntableUI', message= 'self.turnTableGridLayout Done....', verbose = False)

    def _setRenderGlobals(self, animation):
        debug(app = self.app, method = '_setRenderGlobals', message= 'Setting render globals now..', verbose = False)
        self.renderWidth = self.app.get_setting('movie_width')
        self.renderHeight = self.app.get_setting('movie_height')
        debug(app = self.app, method = '_setRenderGlobals', message= 'self.renderWidth.. %s' %  self.renderWidth, verbose = False)
        debug(app = self.app, method = '_setRenderGlobals', message= 'self.renderHeight.. %s' %  self.renderHeight, verbose = False)
        
        ## Now push that info through to the render globals setup
        settings._setRenderGlobals(self.renderWidth, self.renderHeight, animation)
        debug(app = self.app, method = '_setRenderGlobals', message= 'DONE setting render globals..', verbose = False)

    def _setupTurnTable(self, geoGroup = '', start = '', frames = ''):
        """
        Builds a camera for turn table
        """
        debug(app = self.app, message = '_setupTurnTable run...', verbose = False)
        geoGroup = geoGroup.getText()
        start = start.value()
        frames = frames.value()
        
        ## Now check for existing and delete it.
        if cmds.objExists('turnTable_hrc'):
            debug(app = self.app, message = 'Removed existing turnTable...', verbose = False)
            cmds.delete('turnTable_hrc')
        
        ## Build the camera for the turnTable
        cameraName = 'turnTable%s' % self.app.get_setting('cameraSuffix')
        cmds.camera()
        cmds.rename('camera1', cameraName)
        ## Now change the settings of the camera to the default settings
        settings._setCameraDefaults(cameraName)
        
        ## Setup the group
        cmds.group(cameraName, n = 'turnTable_hrc')
        cmds.pointConstraint(geoGroup, 'turnTable_hrc', mo = False, n = 'tmpPoint')
        cmds.orientConstraint(geoGroup, 'turnTable_hrc', mo = False, n = 'tmpOrient')
        cmds.delete(['tmpPoint', 'tmpOrient'])

        ## Now set the camera into the modelEditor that was selected by the artist
        cmds.modelEditor(self.currentEditor, e = True, camera = cameraName)
        cmds.viewFit(cameraName, allObjects = False, animate = False,  f=0.80)
        #cmds.xform(cameraName, translation = [0,0,25])
        
        ## Now keyframe the turntable group
        cmds.currentTime(start)
        getStartRotY = cmds.getAttr('turnTable_hrc.rotateY')
        cmds.setKeyframe('turnTable_hrc', at = 'rotateY')
        cmds.currentTime(start + frames/2)
        cmds.playbackOptions(animationStartTime = start, animationEndTime = start + frames, minTime = start, maxTime = start + frames)
        cmds.setAttr('turnTable_hrc.rotateY', 360 + getStartRotY)
        cmds.setKeyframe('turnTable_hrc', at = 'rotateY')
        cmds.setKeyframe('turnTable_hrc', at = 'rotateX')
        
        cmds.currentTime(start + frames)
        cmds.setAttr('turnTable_hrc.rotateX', -360)
        cmds.setKeyframe('turnTable_hrc', at = 'rotateX')
        
        cmds.select(clear = True)
   
    def _processRadioButtons(self):
        self.editor = self.currentEditor
        radioButtons = [self.camRadioButtons, self.viewportRadioButtons, self.rendererRadioButtons]
        debug(app = self.app, method = '_processRadioButtons', message= 'Processing the radioButtonStates', verbose = False)
        debug(app = self.app, method = '_processRadioButtons', message= 'CurrentEditor is: %s' % self.currentEditor, verbose = False)
        for eachSettingList in radioButtons:
            for eachSetting in eachSettingList:
                if eachSetting.text() == 'NURBS Curves':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, nc = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, nc = False)
                if eachSetting.text() == 'NURBS Surfaces':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, ns = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, ns = False)
                if eachSetting.text() == 'Polygons':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, polymeshes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, polymeshes = False)
                if eachSetting.text() == 'Subdiv Surfaces' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, subdivSurfaces = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, subdivSurfaces = False)
                if eachSetting.text() == 'Planes' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, planes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, planes = False)
                if eachSetting.text() == 'Lights' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, lights = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, lights = False)
                if eachSetting.text() == 'Cameras' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, cameras = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, cameras = False)
                if eachSetting.text() == 'Joints' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, joints = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, joints = False)
                if eachSetting.text() == 'IK Handles' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, ikHandles = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, ikHandles = False)
                if eachSetting.text() == 'Deformers' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, deformers = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, deformers = False)
                if eachSetting.text() == 'Dynamics':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, dynamics = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, dynamics = False)
                if eachSetting.text() == 'Fluids':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, fluids = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, fluids = False)
                if eachSetting.text() == 'Hair Systems':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, hairSystems = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, hairSystems = False)
                if eachSetting.text() == 'Follicles':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, follicles = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, follicles = False)
                if eachSetting.text() == 'nCloths':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, nCloths = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, nCloths = False)
                if eachSetting.text() == 'nParticles':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, nParticles = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, nParticles = False)
                if eachSetting.text() == 'nRigids':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, nRigids = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, nRigids = False)
                if eachSetting.text() == 'Dynamic Constraints':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, dynamicConstraints = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, dynamicConstraints = False)
                if eachSetting.text() == 'Locators':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, locators = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, locators = False)
                if eachSetting.text() == 'Dimensions':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, dimensions = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, dimensions = False)
                if eachSetting.text() == 'Pivots':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, pivots = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, pivots = False)
                if eachSetting.text() == 'Handles':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, handles = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, handles = False)
                if eachSetting.text() == 'Textures':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, textures = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, textures = False)
                if eachSetting.text() == 'Strokes':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, strokes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, strokes = False)  
                if eachSetting.text() == 'Motion Trails':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, motionTrails = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, motionTrails = False)
                if eachSetting.text() == 'Manipulators':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, manipulators = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, manipulators = False)
                if eachSetting.text() == 'Clip Ghosts':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, clipGhosts = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, clipGhosts = False)
                if eachSetting.text() == "NURBS CV's":
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, controlVertices = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, controlVertices = False)                
                if eachSetting.text() == 'NURBS Hulls':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, hulls = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, hulls = False)                 
                if eachSetting.text() == 'Grid' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, grid = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, grid = False)
                if eachSetting.text() == 'HUD' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, headsUpDisplay = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, headsUpDisplay = False)
                if eachSetting.text() == 'Image Planes' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, imagePlane = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, imagePlane = False)
                if eachSetting.text() == 'Selection Highlighting' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, selectionHiliteDisplay = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, selectionHiliteDisplay = False)
                if eachSetting.text() ==  'Texture Placements' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, textures = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, textures = False)
                if eachSetting.text() ==  'Plugin Shapes' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, pluginShapes = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, pluginShapes = False)
                if eachSetting.text() ==  'GPU Caches' :
                    try:## Extension only
                        if eachSetting.isChecked():
                            cmds.modelEditor(self.editor, edit = True,  pluginObjects = ['gpuCacheDisplayFilter', True])
                        else:
                            cmds.modelEditor(self.editor, edit = True, pluginObjects = ['gpuCacheDisplayFilter', False])
                    except:
                        pass
                if eachSetting.text() ==  'Nurbs CVs' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, cv = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, cv = False)
                if eachSetting.text() ==  'Nurbs CVs' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, cv = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, cv = False)
                if eachSetting.text() == 'Use Default Mat':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, useDefaultMaterial = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, useDefaultMaterial = False)
                if eachSetting.text() == 'X-Ray':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, xray = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, xray = False)
                if eachSetting.text() == 'X-Ray Joints':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, jointXray = True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, jointXray = False)
                if eachSetting.text() == 'Hardware Texturing':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayTextures = True, displayAppearance='smoothShaded', displayLights = "default")
                        for eachSetting in self.viewportRadioButtons:
                            if eachSetting.text() ==  'SmoothShade All' :
                                eachSetting.setChecked(True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, displayTextures = False)
                if eachSetting.text() ==  'WireFrame' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "wireframe")
                if eachSetting.text() ==  'SmoothShade All' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "smoothShaded")
                if eachSetting.text() ==  'Bounding Box' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "boundingBox")
                if eachSetting.text() ==  'Wireframe on Shaded' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, displayAppearance = "smoothShaded", activeOnly = False, wireframeOnShaded = True)
                        for eachSetting in self.viewportRadioButtons:
                            if eachSetting.text() ==  'SmoothShade All' :
                                eachSetting.setChecked(True)
                    else:
                        cmds.modelEditor(self.editor, edit = True, wireframeOnShaded = False)
                if eachSetting.text() ==  'Default Renderer' :
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, rendererName =  'base_OpenGL_Renderer')
                if eachSetting.text() == 'Viewport 2.0':
                    if eachSetting.isChecked():
                        cmds.modelEditor(self.editor, edit = True, rendererName = 'ogsRenderer')
                        cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
                        #cmds.optionMenuGrp('VP20multisampleMenu', e = True,  value = 16)
                        #cmds.attrFieldSliderGrp('attrFieldSliderGrp21', e = True, en = True)
                        #cmds.setAttr("hardwareRenderingGlobals.textureMaxResolution", 128)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", 1)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoAmount", 1.5)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoRadius", 10)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoFilterRadius", 10)
                        cmds.setAttr("hardwareRenderingGlobals.ssaoSamples", 32)
                        cmds.setAttr("hardwareRenderingGlobals.consolidateWorld", 1)
                if eachSetting.text() == 'Shaded Eyes on Hardware Texturing':
                    if eachSetting.isChecked():
                        cmds.polyOptions(colorShadedDisplay = False, gl = True)
                    else:
                        cmds.polyOptions(colorShadedDisplay = True, gl = True)

        debug(app = self.app, method = '_processRadioButtons', message= 'Done processing each radio setting', verbose = False)
        
    def doPlayblast(self):
        """
        Double check the comment. Then grab some settings and do the main thread.
        """
        comment = self.comment.text() 
        if self.upload.isChecked():
            if comment == '':
                debug(app = self.app, message = 'You must set a valid comment for review!', verbose = False)
                QtGui.QMessageBox.information(None, "Aborted...", 'Please put a valid comment.')
                return -1
            
        work_template = self.app.get_template('template_work')
        width =  self.app.get_setting("movie_width")
        height  =  self.app.get_setting("movie_height")
        isAsset = self.app.get_setting("isAsset")
        user = tank.util.get_current_user(self.app.tank)
        
        self._setupPlayblast(work_template, width, height, comment, isAsset, user)
            
    def _setupPlayblast(self, work_template, width, height, comment, isAsset, user):
        """
        This is the main method to processs the playblast
        """       
        # Is the app configured to do anything?
        store_on_disk = self.app.get_setting("store_on_disk")
        if not self.upload_to_shotgun and not store_on_disk:
            debug(app = self.app, message ="App is not configured to store playblast on disk nor upload to shotgun! Check the shot_step.yml to fix this.", verbose = False)
            return None
        
        ## Double check the artist wants to playblast.
        self.reply = QtGui.QMessageBox.question(None, 'Continue with playblast?', "Do you wish to playblast now? \nNow is a good time to save a new vers scene if you haven't already...", QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
        if self.reply == QtGui.QMessageBox.Ok:
            ## Check the playblast ranged against shotguns cut in and out.
            debug(app = self.app, method = '_setupPlayblast', message = 'QtGui.QMessageBox.Ok accepted', verbose = False)
            self._setFrameRanges(isAsset)
            debug(app = self.app, method = '_setupPlayblast', message = '_setFrameRanges finished', verbose = False)
            ## Now setup the output path for the mov
            scene_path = os.path.abspath(cmds.file(query=True, sn= True))
            try:
                fields = work_template.get_fields(scene_path)
            except:
                QtGui.QMessageBox.information(None, "Aborted...", 'Please save your scene first before continuing. And relaunch the playblast tool...')
            publish_path_template = self.app.get_template("movie_path_template")
            publish_path = publish_path_template.apply_fields(fields)
            work_path_template = self.app.get_template("movie_workpath_template")
            work_path = work_path_template.apply_fields(fields)
            debug(app = self.app, message = 'work_path: %s' % work_path, verbose = False)
            
            if sys.platform == 'win32':
                self.osPathToWorkFile = r'%s' % work_path
                self.osPathToPublishFile = r'%s' % publish_path
                
            ## Now query the first and last frames of the animation
            getFirstFrame = cmds.playbackOptions(query = True, animationStartTime = True)
            getLastFrame = cmds.playbackOptions(query = True, animationEndTime = True)

            ## Debugging Info
            debug(app = self.app, method = '_setupPlayblast', message = 'Width: \t\t%s' % width, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'Height: \t%s' % height, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'Comment: \t%s' % comment, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'isAsset: \t%s' % isAsset, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'UserName: \t%s' % user, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'scene_path: \t%s' % scene_path, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'fields: \t%s' % fields, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'WorkTemplate: \t%s' %  work_template, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'publish_path_template: \t%s' % publish_path_template, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'publish_path: \t%s' % publish_path, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'work_path_template: \t%s' % work_path_template, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'work_path: \t%s' % work_path, verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'osPathToWorkFile: \t%s' % self.osPathToWorkFile.replace('\\', '/'), verbose = False)
            debug(app = self.app, method = '_setupPlayblast', message = 'osPathToPublishFile: \t%s' % self.osPathToPublishFile.replace('\\', '/'), verbose = False)
            
            ## Now check for existing playblast. We check the publish folder because the working file gets moved into publish on upload.
            ## The playblast tool overwrites any playblasts it does with the same version name in the working directory.
            if os.path.exists(publish_path):
                debug(app = self.app, message = "Existing published playblast found with same version number....", verbose = False)
                self.reply = QtGui.QMessageBox.question(None, 'IMPORTANT!!!!!', "Existing published playblast found!!!!\nIf for some reason the previous blast didn't upload click okay to redo the playblast now.\nOtherwise CANCEL NOW and save a new version of your scene or you will end up with duplicates in shotgun!", QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
                if self.reply == QtGui.QMessageBox.Ok:
                    ################################################
                    ## CHECK PERMS AT KL FOR THIS IT MIGHT NOT WORK !!
                    ################################################
                    try:
                        os.remove(self.osPathToPublishFile.replace('\\', '/'))
                        self._finishPlayblast(publish_path, width, height, store_on_disk, getFirstFrame, getLastFrame, comment, user, work_path)
                    except:
                        debug(app = self.app, method = '_setupPlayblast', message = 'FAILED: \tTo remove osPathToPublishFile', verbose = False)
                        return -1
                else:
                    return -1
            else:
                self._finishPlayblast(publish_path, width, height, store_on_disk, getFirstFrame, getLastFrame, comment, user, work_path)
                
    def _finishPlayblast(self, publish_path, width, height, store_on_disk, getFirstFrame, getLastFrame, comment, user, work_path):
        ## Now do the playblast if the user selected okay or there wasn't a duplicate found.
        debug(app = self.app, method = '_finishPlayblast', message = 'Duplicate check passed. Playblasting...', verbose = False)
        
        ## Now render the playblast
        self._render_pb_in_maya(getFirstFrame, getLastFrame, publish_path, work_path, width, height)
        debug(app = self.app, method = '_finishPlayblast', message = 'PlayBlast finished..', verbose = False)
        
        ## Check if uploading is enabled in the UI and do the uploading if it is, else we will finish up here.
        if self.upload.isChecked():
            debug(app = self.app, method = '_finishPlayblast', message = 'Upload is turned on.. processing version to sg now..', verbose = False)
            
            ## Move the working file to the publish path
            try:
                debug(app = self.app, method = '_finishPlayblast', message = 'RENAMING: osPathToWorkFile to osPathToPublishFile', verbose = False)
                os.rename(self.osPathToWorkFile.replace('\\', '/'), self.osPathToPublishFile.replace('\\', '/'))
            except:
                debug(app = self.app, method = '_setupPlayblast', message = 'FAILED: \tTo rename osPathToWorkFile to osPathToPublishFile', verbose = False)
                ## This could fail because the process is in use, and not the fact a freaking published file exists, due to maya trying to open the playblast once it's done!
                ## So a quick check here to make sure it doesn't exist.. if it doesn't and it failed COPY it instead. Fucking maya...
                if not os.path.exists(publish_path):
                    debug(app = self.app, method = '_setupPlayblast', message = 'FAILED: \tTo rename because file is IN USE. Using shutil to copy instead.', verbose = False)
                    shutil.copyfile(self.osPathToWorkFile.replace('\\', '/'), self.osPathToPublishFile.replace('\\', '/'))
                else:
                    debug(app = self.app, method = '_setupPlayblast', message = 'FAILED: \tTo rename because file already exists.. how the heck the remove previously failed.. who knows.. but try again now..', verbose = False)
                    os.remove(self.osPathToPublishFile.replace('\\', '/'))
                    os.rename(self.osPathToWorkFile.replace('\\', '/'), self.osPathToPublishFile.replace('\\', '/'))
            
            ## Now submit the version to shotgun
            debug(app = self.app, method = '_finishPlayblast', message = 'Submitting vesion info to shotgun...', verbose = False)
            sg_version = self._submit_version(
                                              path_to_movie = publish_path, 
                                              store_on_disk = store_on_disk,
                                              first_frame = getFirstFrame, 
                                              last_frame = getLastFrame,
                                              comment = comment,
                                              user = user
                                              )
            debug(app = self.app, method = '_finishPlayblast', message = 'Version Submitted to shotgun successfully', verbose = False)
            ## Uploading...
            ## Now upload in a new thread and make our own event loop to wait for the thread to finish.
            debug(app = self.app, method = '_finishPlayblast', message = 'Uploading mov to shotgun for review.', verbose = False)
            cmds.headsUpMessage("Uploading playblast to shotgun for review this may take some time! Be patient...", time = 2)
            event_loop = QtCore.QEventLoop()
            debug(app = self.app, method = '_finishPlayblast', message = 'event_loop set...', verbose = False)
            thread = UploaderThread(self.app, sg_version, publish_path, self.upload_to_shotgun)
            debug(app = self.app, method = '_finishPlayblast', message = 'thread set...', verbose = False)
            thread.finished.connect(event_loop.quit)
            thread.start()
            debug(app = self.app, method = '_finishPlayblast', message = 'thread started set...', verbose = False)
            event_loop.exec_()
            debug(app = self.app, method = '_finishPlayblast', message = 'event_loop.exec_...', verbose = False)
            ## log any errors generated in the thread
            for e in thread.get_errors():
                self.app.log_error(e)
                print e
            ## Remove from file system if required
            if not store_on_disk and os.path.exists(publish_path):
                os.unlink(publish_path)
                
            ## Remove turntable if option is selected
            if self.app.get_setting('isAsset'):
                if self.deleteHrcGrp.isChecked():
                    cmds.delete('turnTable_hrc')
            debug(app = self.app, method = '_finishPlayblast', message = 'Upload to shotgun finished.', verbose = False)
            cmds.headsUpMessage("Playblast upload to shotgun complete!", time = 2)
            cmds.warning('UPLOAD COMPLETE!')
                    
    def _setFrameRanges(self, isAsset):
        """
        STOLEN FROM tk-multi-setframerange v0.1.7
        Sets the in and out according to shotgun
        Requires a valid cut in and cut out to be set in the shotgun db
        """
        if isAsset:
                getFirstFrame = cmds.playbackOptions(query = True, animationStartTime = True)
                getLastFrame = cmds.playbackOptions(query = True, animationEndTime = True)
                self.set_frame_range(self.app.engine.name, getFirstFrame, getLastFrame)
        else:
            (new_in, new_out) = self.get_frame_range_from_shotgun()
            (current_in, current_out) = self.get_current_frame_range(self.app.engine.name)
            if new_in is None or new_out is None:
                # lazy import so that this script still loads in batch mode
                message =  "Shotgun has not yet been populated with \n"
                message += "in and out frame data for this Shot."    
                # present a pyside dialog
                QtGui.QMessageBox.information(None, "ERROR", message)
            elif int(new_in) != int(current_in) or int(new_out) != int(current_out):
                # change!
                message =  "Your scene has been updated with the \n"
                message += "latest frame ranges from shotgun.\n\n"
                message += "Previous start frame: %d\n" % current_in
                message += "New start frame: %d\n\n" % new_in
                message += "Previous end frame: %d\n" % current_out
                message += "New end frame: %d\n\n" % new_out
                print  message## Print the message so we can continue without user prompting....
                self.set_frame_range(self.app.engine.name, new_in, new_out)
                return
            else:
                pass
       
    def get_frame_range_from_shotgun(self):
        """
        STOLEN FROM tk-multi-setframerange v0.1.7
        Returns (in, out) frames from shotgun.
        """
        # we know that this exists now (checked in init)
        entity = self.app.context.entity

        sg_entity_type = self.app.context.entity["type"]
        sg_filters = [["id", "is", entity["id"]]]

        sg_in_field = self.app.get_setting("sg_in_frame_field")
        sg_out_field = self.app.get_setting("sg_out_frame_field")
        fields = [sg_in_field, sg_out_field]

        #import time
        #start = time.time()
        data = self.app.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=fields)
        #data = self.dbWrap.find_one(self.sg, sg_entity_type, sg_filters, fields)
        #print 'TIME: %s' % (time.time()-start)
        # check if fields exist!
        if sg_in_field not in data:
            raise tank.TankError("Configuration error: Your current context is connected to a Shotgun "
                                 "%s. This entity type does not have a "
                                 "field %s.%s!" % (sg_entity_type, sg_entity_type, sg_in_field))

        if sg_out_field not in data:
            raise tank.TankError("Configuration error: Your current context is connected to a Shotgun "
                                 "%s. This entity type does not have a "
                                 "field %s.%s!" % (sg_entity_type, sg_entity_type, sg_out_field))

        return ( data[sg_in_field], data[sg_out_field] )

    def get_current_frame_range(self, engine):
        """
        STOLEN FROM tk-multi-setframerange v0.1.7
        """
        if engine == "tk-maya":
            current_in = cmds.playbackOptions(query=True, minTime= True)
            current_out = cmds.playbackOptions(query=True, maxTime= True)
        else:
            raise tank.TankError("Don't know how to get current frame range for engine %s!" % engine)
        return (current_in, current_out)

    def set_frame_range(self, engine, in_frame, out_frame):
        """
        STOLEN FROM tk-multi-setframerange v0.1.7
        """
        if engine == "tk-maya":
            import pymel.core as pm
            # set frame ranges for plackback
            pm.playbackOptions(minTime=in_frame, 
                               maxTime=out_frame,
                               animationStartTime=in_frame,
                               animationEndTime=out_frame)
            # set frame ranges for rendering
            defaultRenderGlobals=pm.PyNode('defaultRenderGlobals')
            defaultRenderGlobals.startFrame.set(in_frame)
            defaultRenderGlobals.endFrame.set(out_frame)
        else:
            raise tank.TankError("Don't know how to set current frame range for engine %s!" % engine)

    def _submit_version(self, path_to_movie, store_on_disk, first_frame, last_frame, comment, user):
        """
        Create a version in Shotgun for this path and linked to this publish.
        """
        # get current shotgun user
        current_user = user
        name = os.path.splitext(os.path.basename(path_to_movie))[0]
        # create a name for the version based on the file name grab the file name, strip off extension
        # do some replacements
        name = name.replace("_", " ")
        # and capitalize
        name = name.capitalize()
        data = {
            "code": name,
            "entity": self.app.context.entity,
            "sg_task":  self.app.context.task,
            "user": current_user,
            "created_by": current_user,
            "project": self.app.context.project,
            "description": comment
        }
        if store_on_disk:
            data["sg_path_to_movie"] = path_to_movie        
        sg_version = self.app.tank.shotgun.create("Version", data)
        return sg_version

    def _render_pb_in_maya(self, first_frame, last_frame, publish_path, work_path, width, height):
        """
        Method to handle the playblast in maya
        NOTE: May need to add an active viewport update here in case the operator had a different window selected.
        """
        debug(self.app, method = '_render_pb_in_maya', message = 'self.qualityPercent.value: %s' % self.qualityPercent.value() , verbose = False)
        ## Clear selection in case the operator had something selected.
        cmds.select(clear = True)
        ## Now set the current editor to be the currently active view
        cmds.modelEditor(self.currentEditor, e = True, activeView = True)
        soundFiles = cmds.ls(type = 'audio')
        if soundFiles:
            sound =  soundFiles[0]
            if len(soundFiles) > 1:
                cmds.warning('More than one audio track in scene, using the first found in the list: \n\t\AUDIO: %s' % soundFiles[0])
        else:
            cmds.warning('No sound files found...')
            sound  = None
            
        debug(self.app, method = '_render_pb_in_maya', message = 'sound: %s' % sound ,verbose = False)
        ## Now do the main playblast
        ## Ginyih's addon where force current time to frame 1 as there's popping sometimes
        [cmds.currentTime(first_frame) for i in range(2)]
        cmds.playblast(
        filename = work_path,
        activeEditor = False,
        clearCache = True,
        combineSound = True,
        compression = 'h.264',
        startTime = first_frame,
        endTime = last_frame + 1,
        forceOverwrite = True,
        format = 'qt',
        framePadding = 4,
        offScreen = True,
        options = False,
        percent = self.sizePercent.value(),
        quality = self.qualityPercent.value(),
        sequenceTime = False,
        showOrnaments = True,
        viewer = True,
        widthHeight=[width, height],
        sound = sound
        )