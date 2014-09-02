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

if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import maya_asset_MASTERCLEANUPCODE as cleanup
import core_archive_lib as coreLib
import shader_lib as shd
#reload(cleanup)
#reload(coreLib)
#reload(shd)

import tank
from tank import Hook
from tank import TankError

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
      
        ## DO MAIN CHECKING NOW
        #############################
        ## HARD FAILS
        ## Duplicate name check
        ## geo_hrc
        if not cmds.objExists('geo_hrc'):
             raise TankError("Please Group all your geo under a geo_hrc group under the root node.")
        # rig_hrc
        # UNCOMMENT FOR MDL STEP
        if cleanup.rigGroupCheck():
            raise TankError('Rig group found!! Please use the RIG menus to publish rigs...')
        # UNCOMMENT FOR RIG STEP
        #  if not cleanup.rigGroupCheck():
        #      raise TankError('No rig group found!! Please make sure your animation controls are under rig_hrc.')
        
        ## Now check it's the right KIND of asset eg CHAR or PROP
        #cleanup.assetCheckAndTag(type = 'LIB', customTag = 'staticLIB')
        
        #############################
        ## SECONDARIES FOR PUBLISHING
        ## WE NEED TO FIND THE MAIN GROUP THAT HAS MESHES IN IT NOW AND PUSH THIS INTO THE ITEMS LIST FOR SECONDARY PUBLISHING
        ## Look for root level groups that have meshes as children:
        for grp in cmds.ls(assemblies = True, long = True):
            if cmds.ls(grp, dag=True, type="mesh"):
        ### UNCOMMENT FOR PROP CHAR LND ASSETS
        # include this group as a 'mesh_group' type
                if '_hrc' in grp and 'SRF' not in grp:
                    items.append({"type":"mesh_group", "name":grp})                                  
        ### UNCOMMENT FOR BLD MLD STEP
        #          if cleanup.BLDTransformCheck(grp): ## Check for BLD step only to make sure the transforms are not frozen on the BLD grps
        #              items.append({"type":"mesh_group", "name":grp})
        #              cleanup.assetCheckAndTag(type = 'BLD', customTag = 'staticBLD')
        if not cleanup.duplicateNameCheck():
            raise TankError("Duplicate names found please fix before publishing.\nCheck the outliner for the duplicate name set.")
        ## Incorrect Suffix check
        checkSceneGeo = cleanup._geoSuffixCheck(items)
        if not checkSceneGeo:
            raise TankError("Incorrect Suffixes found! Fix suffixes before publishing.\nCheck the outliner for the duplicate name set.")
        #############################
        if shd.sceneCheck():
            raise TankError("You have errors in your scene, please fix.. check the script editor for details.")

        cleanup.cleanUp(items = items, checkShapes = True, history = False, pivots = False, freezeXFRM = False, smoothLvl = False, tagSmoothed = False, checkVerts = False, 
        renderflags = False, deleteIntermediate = False, turnOffOpposite = False, instanceCheck = False, shaders = False, removeNS = False)

        mel.eval("MLdeleteUnused();")

        ## Fix pathing from work to publish for export
        shd.repathFileNodesForPublish()
        
        ## Now do the smartConn
        shd.smartConn()
        
        ## Fix remap and ramps color entry plugs and any incorrect ordering
        ## Leads to bad plugs being inserted when the XML recreates all the values. Querying also creates which makes black colour entry plugs.
        shd.fixRamps(cmds.ls(type = 'remapValue'))
        shd.fixRamps(cmds.ls(type = 'ramp'))
        
        ## NOW MOVE ON TO PUBLISHING
        return items