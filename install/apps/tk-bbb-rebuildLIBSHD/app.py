"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db
"""
import os, getpass, sys
import tank.templatekey
import shutil
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
import xml.etree.ElementTree as xml
from xml.etree import ElementTree
from functools import partial
from tank import TankError
import sgtk
import pymel.core as pm
## Now get the custom tools
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import core_archive_lib as coreLib
import maya_genericSettings as settings
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
import ProgressBarUI as pbui
import shader_lib as shd
#reload(coreLib)
#reload(settings)
#reload(pbui)
#reload(cleanup)
#reload(shd)

class RebuildLIBSHD(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the RebuildLIBSHD application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'RebuildLIBSHD Loaded...', verbose = False)

    def run_app(self):
        """
        Callback from when the menu is clicked.
        """
        context = self.context ## To get the step
        debug(app = self, method = 'run_app', message = 'Context Step...\n%s' % context.step['name'], verbose = False)
        if context.step['name'] == 'Surface':
            ## Tell the artist to be patient... eg not genY
            inprogressBar = pbui.ProgressBarUI(title = 'Building Asset Shaders:')
            inprogressBar.show()
            inprogressBar.updateProgress(percent = 5, doingWhat = 'Processing scene info...')
            ## Instantiate the API
            tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
            debug(app = self, method = 'run_app', message = 'API instanced...\n%s' % tk, verbose = False)
            debug(app = self, method = 'run_app', message = 'RebuildLIBSHD launched...', verbose = False)
        
            ## Now process XML
            debug(app = self, method = 'processTemplates', message = 'Looking for LIB assets to rebuild now', verbose = False)
            shd.reconnectLIBSHD(rootGrp = 'geo_hrc', freshImport = False)
    
            inprogressBar.updateProgress(percent = 100, doingWhat = 'COMPLETE...')
            inprogressBar.close()
            inprogressBar = None
        else:
            cmds.warning('Not a valid SRF context step. Try making sure you are in a valid Surfacing step launched from shotgun.')

    def destroy_app(self):
        self.log_debug("Destroying sg_fetchMayaCamera")
        