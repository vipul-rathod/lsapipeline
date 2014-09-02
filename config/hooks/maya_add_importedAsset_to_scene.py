# Copyright (c) 2013 Shotgun Software Inc.
# fsdfsdfsd
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
import os, sys
## Now get the custom tools
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
import shader_lib as shd
from debug import debug

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
        Import file into Maya
        """
        
        import pymel.core as pm
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = file_path.replace(os.path.sep, "/")
        
        (path, ext) = os.path.splitext(file_path)
        
        if ext in [".ma", ".mb"]:
            assetName =  '%s_hrc' % file_path.split('.')[0].split('/')[-1]
            cmds.file(file_path, i =True, gr = True, gn = '%s_import' % assetName)
            
            for eachNode in cmds.ls(ap= True):
                if ':' in eachNode:
                    try:
                        cmds.rename(eachNode, '%s' % eachNode.split(':')[-1])
                    except RuntimeError:
                        pass
            ## Now look for and try to connect the Library assets that were previously shaded 
            shd.reconnectLIBSHD(rootGrp = assetName, freshImport = True)
        else:
            self.parent.log_error("Unsupported file extension for %s! Nothing will be loaded." % file_path)