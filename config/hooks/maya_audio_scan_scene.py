# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os, sys
import maya.cmds as cmds
import maya.mel as mel
import tank
from tank import Hook
from tank import TankError
## Custom imports
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
#reload(cleanup)

class ScanSceneHook(Hook):
    """
    Hook to scan scene for items to publish
    """
    
    def execute(self, **kwargs):
        """
        Main hook entry point
        :returns:       A list of any items that were found to be published.  
                        Each item in the list should be a dictionary containing 
                        the following keys:
                        {
                            type:   String
                                    This should match a scene_item_type defined in
                                    one of the outputs in the configuration and is 
                                    used to determine the outputs that should be 
                                    published for the item
                                    
                            name:   String
                                    Name to use for the item in the UI
                            
                            description:    String
                                            Description of the item to use in the UI
                                            
                            selected:       Bool
                                            Initial selected state of item in the UI.  
                                            Items are selected by default.

                            required:       Bool
                                            Required state of item in the UI.  If True then
                                            item will not be deselectable.  Items are not
                                            required by default.
                                            
                            other_params:   Dictionary
                                            Optional dictionary that will be passed to the
                                            pre-publish and publish hooks
                        }
        """   
                
        items = []
        
        # get the main scene:
        scene_name = cmds.file(query=True, sn= True)
        if not scene_name:
            raise TankError("Please Save your file before Publishing")
      
        scene_path = os.path.abspath(scene_name)
        name = os.path.basename(scene_path)

        # create the primary item - this will match the primary output 'scene_item_type':            
        items.append({"type": "work_file", "name": name})
        
        ## Check the naming convention for the audio in the scene....
        debug(app = None, method = 'execute', message = 'scene_path: %s' % scene_path, verbose = False)
        debug(app = None, method = 'execute', message = 'name: %s' % name, verbose = False)
        debug(app = None, method = 'execute', message = 'Checking for audio files now...', verbose = False)
        if not cmds.ls(type = 'audio'):
            raise TankError("No audio files found?!")
        else:
            if len(cmds.ls(type = 'audio')) > 1:
                raise TankError('You have more than one audio file in your scene! Publish only one audio file!')
            audioName = scene_name.split('/')[4]
            myAudioFile = cmds.ls(type = 'audio')[0]
            debug(app = None, method = 'execute', message = 'audioName: %s' % audioName, verbose = False)
            debug(app = None, method = 'execute', message = 'myAudioFile: %s' % myAudioFile, verbose = False)
            if audioName not in myAudioFile:
                raise TankError("This audio file name is incorrect please rectify this immediately: [episode]_[shot]_AUD.v[###].wav")
            else:
                pass
        
        ## make sure the default maya renderer is set for clean referencing of audio files later on...
        cmds.setAttr('defaultRenderGlobals.currentRenderer','mayaSoftware', type = 'string')
        
        ## NOW MOVE ON TO PUBLISHING STEPS
        return items