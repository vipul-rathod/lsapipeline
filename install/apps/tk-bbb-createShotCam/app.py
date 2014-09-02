"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun dbs
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
## Now get the custom tools
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import maya_genericSettings as settings
from debug import debug
import ProgressBarUI as pbui
#reload(settings)
#reload(pbui)

class CreateShotCam(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the CreateShotCam application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'CreateShotCam Loaded...', verbose = False)

    def run_app(self):
        """
        Callback from when the menu is clicked.
        """
        ## Tell the artist to be patient... eg not genY
        cmds.headsUpMessage("Building shotCam...", time = 1)
        inprogressBar = pbui.ProgressBarUI(title = 'Building Shotcam:')
        inprogressBar.show()
        ## Instantiate the API
        tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        debug(app = self, method = 'run_app', message = 'API instanced...\n%s' % tk, verbose = False)
        debug(app = self, method = 'run_app', message = 'Fetch Shot Assets launched...', verbose = False)
               
        context = self.context ## To get the step
        debug(app = self, method = 'run_app', message = 'Context Step...\n%s' % context.step['name'], verbose = False)
        if context.step['name'] == 'Anm' or context.step['name'] == 'Blocking':
            inprogressBar.updateProgress(percent = 10, doingWhat = 'processing scene info...')
            cmds.cycleCheck(e = 1)
            ## Build an entity type to get some values from.
            entity = self.context.entity                                                                                    ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
            debug(app = self, method = 'run_app', message = 'entity... %s' % entity, verbose = False)

            ## Set the template to the maya publish folder
            shot_root_template = tk.templates[self.get_setting('shot_root_template')]
            debug(app = self, method = 'run_app', message = 'shot_root_template...\n%s' % shot_root_template, verbose = False)

            ## Now build the camera
            shotName = entity['name']
            cameraName = '%s_shotCam' % shotName
            if self.doesAssetAlreadyExistInScene(cameraName):
                inprogressBar.updateProgress(percent = 100, doingWhat = 'Camera found...')
                inprogressBar.close()
                cmds.warning("Scene currently has a valid shotCamera in it! Aborting ...")
                QtGui.QMessageBox.information(None, "Scene currently has a valid shotCamera in it! Aborting ...")
                raise tank.TankError("Scene currently has a valid shotCamera in it! Aborting ...")
            else:
                inprogressBar.updateProgress(percent = 50, doingWhat = 'Building camera...')
                cmds.camera()
                cmds.rename('camera1', cameraName)
                self.tagShotCam(cameraName)
                
                ## Now set the default camera stuff up
                settings._setCameraDefaults(cameraName)
                settings._createCamGate(cameraName)
                ## Now set the renderGlobals up
                width = self.get_setting('movie_width')
                height = self.get_setting('movie_height')
                inprogressBar.updateProgress(percent = 90, doingWhat = 'Setting render globals...')
                settings._setRenderGlobals(width = width, height = height, animation = True)

            inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished...')
            inprogressBar.close()
            cmds.headsUpMessage("shotCam built successfully...", time = 1)
        else:
            cmds.headsUpMessage("Current context is not a valid Shot context. Please make sure you are under a valid shotgun Shot context!", time = 2)
            cmds.warning("Current context is not a valid Shot context. Please make sure you are under a valid shotgun Shot context!")
            QtGui.QMessageBox.information(None, "Current context is not a valid Shot context. Please make sure you are under a valid shotgun Shot context!")
            raise tank.TankError("Current context is not a valid Shot context. Please make sure you are under a valid shotgun Shot context!")

    def tagShotCam(self, cameraName):
        mySel = cameraName
        if mySel:
            if cmds.nodeType(cmds.listRelatives(mySel, shapes = True)[0]) == 'camera':
                try:
                    cmds.addAttr(mySel, ln = 'type', dt = 'string')
                except:
                    pass
                cmds.setAttr('%s.type' % mySel, 'shotCam',  type = 'string')
            print 'Tagged %s with type:shotCam' % mySel

    def doesAssetAlreadyExistInScene(self, assetName):
        debug(app = self, method = 'doesAssetAlreadyExistInScene', message = 'assetName...\n%s' % assetName, verbose = False)
        assetExists = False
        for each in cmds.ls(type = 'transform'):
            if assetName in each:
                assetExists = True
        return assetExists

    def destroy_app(self):
        self.log_debug("Destroying sg_fetchMayaCamera")