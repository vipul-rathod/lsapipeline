# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import maya.cmds as cmds
import maya.mel as mel
import tank
from tank import Hook
from tank import TankError
import sys
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
import CONST as CONST
#reload(cleanup)
#reload(CONST)

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
        
        ## Now find the fx stuff to export as secondary
        ## Make sure the groups are visible and good for calculating
        grps = ['Shot_FX_hrc', 'OCEAN_hrc', 'fluids_hrc', 'FLUID_EMITTERS_hrc']
        for eachGrp in grps:
            if cmds.objExists(eachGrp):
                cmds.setAttr('%s.visibility' % eachGrp, 1)
        
        ## FLUIDS
        for each in cmds.ls(transforms = True):
            myType = ''
            try:
                myType = cmds.getAttr('%s.type' % each)
            except:
                pass
            #debug(app = None, method = 'shotFX_ScanSceneHook', message = 'myType: %s' % myType, verbose = False)
            if myType:
                ## FLUIDS -- Now get the fluid containers
                if myType == 'oceanWakeFoamTexture' or myType == 'oceanWakeTexture':
                    debug(app = None, method = 'shotFX_ScanSceneHook', message = 'fx_caches: %s' % each, verbose = False)
                    items.append({"type":"fx_caches", "name":'%sShape' % each})
                    ## Otherwise grab the fluids group
                elif myType == 'fx':
                    if each != 'ocean_srf':
                        debug(app = None, method = 'shotFX_ScanSceneHook', message = 'fx_caches: %s' % each, verbose = False)
                        items.append({"type":"fx_caches", "name":'%s' % each})
                else:
                    pass

        ## NPARTICLES
        getNParticles = cmds.ls(type = 'nParticle')
        if getNParticles:
            for eachNpart in cmds.ls(type = 'nParticle'):
                ## Now put the fx nodes to be cached into items, remember the type is set to match the shot_step.yml secondary output type!
                debug(app = None, method = 'shotFX_ScanSceneHook', message = 'nparticle_caches: %s' % eachNpart, verbose = False)
                cmds.setAttr('%s.visibility' % eachNpart, 1)
                items.append({"type":"nparticle_caches", "name":eachNpart})

        ## FX RENDERS
        nParticleShapes = [nPart for nPart in cmds.ls(type = 'nParticle')]
        if nParticleShapes:
            items.append({"type":"fx_renders", "name":"Render Final"})

        ## Check if the ocean exists..if it does do some work...
        if cmds.objExists('OCEAN_hrc'):
            ## Hide the preview planes
            cmds.setAttr('oceanPreviewPlane_prv.visibility', 0)
            cmds.setAttr('animPreviewPlane_prv.visibility', 0)       
            ## Now set the ocean preview plane res to something very low and fast to calc
            cmds.setAttr('OCEAN_hrc.oceanRes', 1)
            ## Now make sure the wakes are calculating
            try:
                cmds.setAttr('OCEAN_hrc.oceanCalcOnOff', 1)
            except RuntimeError:
                pass
        else:
            raise TankError("MAYA OCEAN IS MISSING FROM YOUR SHOT!!! YOU SHOULD FIX THIS BEFORE PUBLISHING TO LIGHTING!!!!!!")
            cleanup.turnOnModelEditors()

        ## Check if cacheFiles exist and if yes, delete all of those.
        [cmds.delete(cache) for cache in cmds.ls(type = 'cacheFile')]
        [cmds.delete(cache) for cache in cmds.ls(type = 'cacheBlend')]

        ## Cleanup panels so nParticles don't keep crashing on export.
        for each in cmds.lsUI(panels = True):
            if 'outlinerPanel' in each or 'nodeEditorPanel' in each:
                cmds.deleteUI(each, panel = True)
        debug(app = None, method = 'shotFX_ScanSceneHook', message = 'FINISHED...', verbose = False)
        ## NOW MOVE ON TO PUBLISHING STEPS
        return items