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
from tank.platform.qt import QtCore, QtGui
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
import maya_asset_MASTERCLEANUPCODE as cleanup
import utils as utils
#reload(cleanup)
#reload(utils)

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
        
        
        ### CLEANUP ################################################################################
        ### NOW DO SCENE CRITICAL CHECKS LIKE DUPLICATE OBJECT NAMES ETC AND FAIL HARD IF THESE FAIL!
        ############################################################################################
        #############################
        ## INITAL HARD FAILS
        ## Do a quick check for geo_hrc and rig_hrc
        ## geo_hrc
        if not cmds.objExists('geo_hrc'):
            raise TankError("Please Group all your geo under a geo_hrc group under the root node.")
        ## rig_hrc
        ## UNCOMMENT FOR MDL STEP
        if cleanup.rigGroupCheck():
            raise TankError('Rig group found!! Please use the RIG menus to publish rigs...')
        
        ## UNCOMMENT FOR RIG STEP
        #  if not cleanup.rigGroupCheck():
        #      raise TankError('No rig group found!! Please make sure your animation controls are under rig_hrc.')
        
        ## Now check it's the right KIND of asset eg CHAR or PROP  
        cleanup.assetCheckAndTag(type = 'CHAR', customTag = 'staticCHAR')
        
        #############################
        ## SECONDARIES FOR PUBLISHING
        ## WE NEED TO FIND THE MAIN GROUP THAT HAS MESHES IN IT NOW AND PUSH THIS INTO THE ITEMS LIST FOR SECONDARY PUBLISHING
        ## Look for root level groups that have meshes as children:
        for grp in cmds.ls(assemblies = True, long = True):
            if cmds.ls(grp, dag=True, type="mesh"):
                # include this group as a 'mesh_group' type
        ### UNCOMMENT FOR PROP CHAR LND ASSETS
                items.append({"type":"mesh_group", "name":grp})                                  
        ### UNCOMMENT FOR BLD MLD ASSET
        #          if cleanup.BLDTransformCheck(grp): ## Check for BLD step only to make sure the transforms are not frozen on the BLD grps
        #              items.append({"type":"mesh_group", "name":grp})
        #              cleanup.assetCheckAndTag(type = 'BLD', customTag = 'staticBLD')
        
        #############################
        ## HARD FAILS
        ## Duplicate name check
        if not cleanup.duplicateNameCheck():
            raise TankError("Duplicate names found please fix before publishing.\nCheck the outliner for the duplicate name set.")
        ## Incorrect Suffix check
        checkSceneGeo = cleanup._geoSuffixCheck(items)
        if not checkSceneGeo:
            raise TankError("Incorrect Suffixes found! Fix suffixes before publishing.\nCheck the outliner for the duplicate name set.")
        ## Incorrect root name
        if not utils.checkRoot_hrc_Naming(items):
            assetName = cmds.file(query=True, sn= True).split('/')[4]
            raise TankError("YOUR ASSET IS NAMED INCORRECTLY! Remember it is CASE SENSITIVE!\nIt should be %s_hrc" % assetName)

        #############################
        ## NOW PREP THE GEO FOR EXPORT!!!
        ## THESE CLEANUPS SHOULD NOT FAIL THEY SHOULD JUST BE PERFORMED
        ## UNCOMMENT FOR MDL STEP
        ## PEFORM MDL CLEANUP
        if cmds.objExists('eye_Ctrl'):
            myWarning = QtGui.QMessageBox.question(None, "WARNING!!!! eye_Ctrl found!", 'You must delete the eye_Ctrl node on final publish and clean up your raidal blendshape!\nIf this is your final publish to SRF and RIG you should delete it before continuing...', buttons = (QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel))
            if myWarning == QtGui.QMessageBox.StandardButton.FirstButton:
                cleanup.cleanUp(items = items, checkShapes = True, history = False, pivots = True, freezeXFRM = False, smoothLvl = True, tagSmoothed = True, checkVerts = True, 
                                renderflags = True, deleteIntermediate = True, turnOffOpposite = True, instanceCheck = True, shaders = True)
            else:
                pass
        else:
            cleanup.cleanUp(items = items, checkShapes = True, history = True, pivots = True, freezeXFRM = True, smoothLvl = True, tagSmoothed = True, checkVerts = True, 
                            renderflags = True, deleteIntermediate = True, turnOffOpposite = True, instanceCheck = True, shaders = True)
        ## UNCOMMENT FOR RIG STEP
        ## PEFORM RIG CLEANUP
        #  cleanup.cleanUp(items = items, checkShapes = False, history = False, pivots = False, freezeXFRM = False, smoothLvl = True, tagSmoothed = True, checkVerts = False, 
        #                  renderflags = True, deleteIntermediate = False, turnOffOpposite = True, instanceCheck = False, shaders = True)
        ############################################################################################   
        ## NOW MOVE ON TO PUBLISHING Pop out the last item in the list as we are not dealing with secondaries for this step
        items.pop()
        return items