# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os, sys, tank
import maya.cmds as cmds
import maya.mel as mel
from tank import Hook
from tank import TankError
## Custom stuff
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import maya_asset_MASTERCLEANUPCODE as cleanup
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

        ## ANIM CURVES
        ## If shot step is animation only not layout
        if 'Anm' in scene_name.split('/'):
            ## ATOM
            items.append({"type":"anim_atom", "name":"Animation Curves"})

            ## CREASE XML
            items.append({"type":"crease_xml", "name":"Crease XML"})

        ## Delete any stack .type hrc children of those roots that already have .type
        caches_type = [each for each in cmds.ls(type = 'transform') if cmds.objExists('%s.type' % each) if 'anim' in str(cmds.getAttr('%s.type' % each)) or 'static' in str(cmds.getAttr('%s.type' % each))]
        for each in caches_type:
            descendents_hrc = cmds.listRelatives(each, allDescendents = True, type = 'transform', fullPath = True)
            stack = [x for x in descendents_hrc if cmds.objExists('%s.type' % x) if 'anim' in str(cmds.getAttr('%s.type' % x)) or 'static' in str(cmds.getAttr('%s.type' % x))] if descendents_hrc else None
            [cmds.deleteAttr('%s.type' % hrc) for hrc in stack] if stack else None

        ## Make sure all definitions necessary are at FULL RES for alembic exporting!
        for each in cmds.ls(transforms = True):
            myType = ''
            if cmds.nodeType(each) == 'assemblyReference':         
                ## FIRST Check to see what the active state is of the assembly reference node
                ## If it is still on GPU add this for gpu rendering
                ## Else look for what type of building it is for the alembic caching

                ## GPU CACHES
                if cmds.assembly(each, query = True, active = True) == 'gpuCache':
                    if 'Anm' in scene_name.split('/'):
                        cmds.assembly(each, edit = True, active = 'full')
                        if cmds.getAttr( '%s.type' % cmds.listRelatives(each, children = True, fullPath = True)[0] ) == 'animBLD':
                            items.append( {"type":"anim_caches", "name":each} )
                        else:
                            items.append( {"type":"static_caches", "name":each} )
                else:
                    ## FULL GEO RIGGED OR STATIC
                    ## Check what type is its. Static or Animated
                    try:
                        for eachChild in cmds.listRelatives(each, children = True):
                            try:
                                myType = cmds.getAttr('%s.type' % eachChild)
                            except ValueError:
                                print '%s is not set to a valid assemblyReference type to query for export...' % eachChild
                                pass
                            ## RIGGED BLD -- Now get the rigged buildings
                            if myType == 'animBLD':
                                ## Now put the Assembly References into items, remember the type is set to match the shot_step.yml secondary output type!
                                items.append({"type":"anim_caches", "name":each})
                            ## STATIC BLD -- Now get the static buildings
                            elif myType == 'staticBLD':
                                 ## Now put the Assembly References into items, remember the type is set to match the shot_step.yml secondary output type!
                                items.append({"type":"static_caches", "name":each})
                            elif myType == 'staticLND':
                                 ## Now put the Assembly References into items, remember the type is set to match the shot_step.yml secondary output type!
                                items.append({"type":"static_caches", "name":each})
                            else:
                                pass
                    except:
                        pass
            else:
                try:
                    myType = cmds.getAttr('%s.type' % each)
                    ## FLUIDS -- Now get the fluid containers
                    ## caches = [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE, CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE, CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE]
                    if 'oceanWakeFoamTexture' in myType or 'oceanWakeTexture' in myType:
                         items.append({"type":"fluid_caches", "name":'%sShape' % each})
                    if myType == 'fx':
                        items.append({"type":"fx_caches", "name":each})
                    ## CAMERA -- Now get the camera
                    elif myType == 'shotCam' or myType == 'shotcam':
                        items.append({"type":"camera", "name":each})
                    ## REFERENCES -- Now process the references to get their types
                    elif myType == 'animCHAR' or myType == 'char':
                        items.append({"type":"anim_caches", "name":each})
                    elif myType == 'animPROP':
                        items.append({"type":"anim_caches", "name":each})
                    elif myType == 'animBLD' and '_ADef_' not in each:
                        items.append({"type":"anim_caches", "name":each})
                    elif myType == 'staticPROP':
                        items.append({"type":"static_caches", "name":each})
                    elif myType == 'staticCHAR':
                        items.append({"type":"static_caches", "name":each})
                    else:
                        pass
                except:
                    pass


        ## Check if the ocean exists..if it does do some work...
        if cmds.objExists('OCEAN_hrc'):
            ## Hide the preview planes
            cmds.setAttr('oceanPreviewPlane_prv.visibility', 1)
            cmds.setAttr('animPreviewPlane_prv.visibility', 0)
            ## Now make sure the wakes are calculating
            #cmds.setAttr('OCEAN_hrc.oceanCalcOnOff', 0)
            ## Now set the ocean preview plane res to something very low and fast to calc
            cmds.setAttr('OCEAN_hrc.oceanRes', 1)
        else:
            raise TankError("MAYA OCEAN IS MISSING FROM YOUR SHOT!!! YOU SHOULD FIX THIS BEFORE PUBLISHING TO LIGHTING!!!!!!")
            cleanup.turnOnModelEditors()
        
        ## Now delete any groups from the parenting tool
        for each in cmds.ls(transforms = True):
            if 'tmXML' in each:
                cmds.delete(each)
        
        ## NOW ADD THE TAGS FOR CREASES TO BE EXPORTED CORRECTLY
        ## NEED TO DO THIS LONG WAY IN CASE THE ATTR ALREADY EXISTS AND FAILS>.
        for each in cmds.ls(type = 'mesh', l = True):
            if not cmds.objExists('%s.SubDivisionMesh' % each):
                try:
                    cmds.addAttr('%s' % each, ln = 'SubDivisionMesh', at = 'bool')
                    cmds.setAttr("%s.SubDivisionMesh" % each, 1)
                except:
                    pass

        ## Check if cacheFiles exist and if yes, delete all of those.
        [cmds.delete(cache) for cache in cmds.ls(type = 'cacheFile')]
        [cmds.delete(cache) for cache in cmds.ls(type = 'cacheBlend')]
        
        ## remove unknown nodes from scene
        cleanup.cleanupUnknown()

        ## NOW MOVE ON TO PUBLISHING STEPS
        check_static_caches = [each['name'] for each in items if each['type'] == 'static_caches']
        if not check_static_caches:
            return items
        else:
            setName = 'static_caches_set'
            cmds.delete(setName) if cmds.objExists(setName) else None ## Delete sets first
            cmds.sets(check_static_caches, name = setName) if check_static_caches else None ## Attach statics into newly created set

            cmds.confirmDialog(title = 'STATIC CACHES DETECTED!', message = 'All the statics are stored inside the "%s" set inside the outliner.\n\n1. Use the BBB Tool "CleanOut Static ENV"\n2. Check if animated building is tagged wrongly as static\n\nIf 2, scene breakdown or ask rigger to republish!' % setName, button = 'OK!', backgroundColor = [1, 0.3, 0.3])