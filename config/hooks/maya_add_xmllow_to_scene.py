# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook that loads items into the current scene. 

This hook supports a number of different platforms and the behaviour on each platform is
different. See code comments for details.


"""
import tank
from tank.platform.qt import QtCore, QtGui
import os, sys
import xml.etree.ElementTree as xml
import maya.cmds as cmds
import maya.mel as mel
## Now get the custom tools
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
import shader_lib as shd
#reload(shd)
#reload(cleanup)

class AddFileToScene(tank.Hook):
    
    def execute(self, engine_name, file_path, shotgun_data, **kwargs):
        """
        Hook entry point and app-specific code dispatcher
        """
                
        if engine_name == "tk-maya":
            self.add_file_to_maya(file_path, shotgun_data)

        else:
            raise Exception("Don't know how to load file into unknown engine %s" % engine_name)
        
    ###############################################################################################
    # app specific implementations
    
    def add_file_to_maya(self, file_path, shotgun_data):
        """
        Load file into Maya as an assembly reference
        """
        
        import pymel.core as pm
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = file_path.replace(os.path.sep, "/")
        
        (path, ext) = os.path.splitext(file_path)
        
        if ext in [".xml"]:
            if not cmds.objExists('dgSHD'):
                cmds.scriptNode(n ='dgSHD')
            debug(None, method = 'add_file_to_maya', message = 'Cleaning shaders...', verbose = False)
            cleanup.cleanUpShaders()

            debug(None, method = 'add_file_to_maya', message = 'Creating shaders...', verbose = False)
            shd.createAll(XMLPath = file_path, Namespace = '', Root = 'MaterialNodes')
            
            debug(None, method = 'add_file_to_maya', message = 'Connect all shaders...', verbose = False)
            shd.connectAll(XMLPath = file_path, Namespace = '', Root = 'MaterialNodes')

            debug(None, method = 'add_file_to_maya', message = 'Downgrade shaders...', verbose = False)
            shd.downgradeShaders()
            
            debug(None, method = 'add_file_to_maya', message = 'Fixing file nodes and plugging directly into color of lamberts...', verbose = False)
            #shd.fixDGLambertFileNodes()
            #shd.fixDGForGPU()

        else:
            self.parent.log_error("Unsupported file extension for %s! Nothing will be loaded." % file_path)

    
     
