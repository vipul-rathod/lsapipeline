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
from mentalcore import mlib
from mentalcore import mapi
## Now get the custom tools
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
from debug import debug
import core_archive_lib as coreLib
import maya_asset_MASTERCLEANUPCODE as cleanup

class AddFileToScene(tank.Hook):
    
    def execute(self, engine_name, file_path, shotgun_data, **kwargs):
        """
        Hook entry point and app-specific code dispatcher
        """
                
        if engine_name == "tk-maya":
            self.add_coreArchive_to_maya(file_path, shotgun_data)
        else:
            raise Exception("Don't know how to load file into unknown engine %s" % engine_name)
        
    ###############################################################################################
    # app specific implementations
    
    def add_coreArchive_to_maya(self, file_path, shotgun_data):
        """
        Load file into Maya as an assembly reference
        """      
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = file_path.replace(os.path.sep, "/")
        
        (path, ext) = os.path.splitext(file_path)
        
        debug(None, method = 'add_coreArchive_to_maya', message = 'file_path:%s' % file_path, verbose = False)
        if ext in [".mi", ".gz"]:
           ## For some reason the publish of the secondary is DROPPING the .gz
           ## So we're adding it back in on the load! And using the base mentalCore loader as this is the only one that works, ripping it out doens't load properly.
           
           mapi.load_archive(path = file_path)
           debug(None, method = 'add_coreArchive_to_maya', message = 'Archive loaded successfully...', verbose = False)
           
           coreLib._setAllToHold()
           debug(None, method = 'add_coreArchive_to_maya', message = '_setAllToHold successfully...', verbose = False)
           
           coreLib.cleanupCoreArchiveImports()
           debug(None, method = 'add_coreArchive_to_maya', message = 'cleanupCoreArchiveImports successfully...', verbose = False)
           
           coreLib.cleanMaterialNS()
           debug(None, method = 'add_coreArchive_to_maya', message = 'cleanMaterialNS successfully...', verbose = False)
           
           coreLib.tagRootArchive()
           debug(None, method = 'add_coreArchive_to_maya', message = 'Tag Root Archives complete...', verbose = False)
           
        else:
            self.parent.log_error("Unsupported file extension for %s! Nothing will be loaded." % file_path)