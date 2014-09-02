# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.


import os, sys, time
import maya.cmds as cmds
import maya.mel as mel
## Custom stuff
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
import maya_asset_MASTERCLEANUPCODE as cleanup
import core_archive_lib as coreLib
import shader_lib as shd
import utils as utils
#reload(cleanup)
#reload(coreLib)
#reload(shd)
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
      
        # look for root level groups that have meshes as children:
        for grp in cmds.ls(assemblies=True, long= True):
            if cmds.ls(grp, dag=True, type="mesh"):
                # include this group as a 'mesh_group' type
                if '_hrc' in grp and 'SRF' not in grp:###SRF is used for rebuilding of archives etc and sits outside the main asset Group
                    items.append({"type":"mesh_group", "name":grp})
                    

        ## DO MAIN CHECKING NOW
        #############################
        ## HARD FAILS
        ## Duplicate name check
        if not cleanup.duplicateNameCheck():
            raise TankError("Duplicate names found please fix before publishing.\nCheck the outliner for the duplicate name set.")
        ## Incorrect Suffix check
        checkSceneGeo = cleanup._geoSuffixCheck(items)
        if not checkSceneGeo:
            raise TankError("Incorrect Suffixes found! Fix suffixes before publishing.\nCheck the outliner for the duplicate name set.")
        #############################
        if shd.sceneCheck():## note this returns TRUE if there ARE errors
            raise TankError("You have errors in your scene, please fix.. check the script editor for details.")

        cleanup.cleanUp(items = items, checkShapes = True, history = False, pivots = False, freezeXFRM = False, smoothLvl = False, tagSmoothed = False, checkVerts = False, 
        renderflags = False, deleteIntermediate = False, turnOffOpposite = False, instanceCheck = False, shaders = False, removeNS = False, defaultRG = False, lightingCleanup = True)

        ## CORES
        start = time.time()
        coreLib.cleanPaintedArchives()
        print 'Total time to %s: %s' % ('coreLib.cleanPaintedArchives()', time.time()-start)
        
        start = time.time()
        coreLib._tagDuplicateCoreArchives()
        print 'Total time to %s: %s' % ('coreLib._tagDuplicateCoreArchives()', time.time()-start)
        
        start = time.time()
        coreLib.prepArchivesForPublish()
        print 'Total time to %s: %s' % ('coreLib.prepArchivesForPublish()', time.time()-start)
        
        start = time.time()
        coreLib.deleteAllCores()
        print 'Total time to %s: %s' % ('coreLib.deleteAllCores()', time.time()-start)

        start = time.time()
        shd.deleteDeadFileInNodes()
        print 'Total time to %s: %s' % ('shd.deleteDeadFileInNodes()', time.time()-start)

        ## Fix pathing from work to publish for export
        start = time.time()
        shd.repathFileNodesForPublish()
        print 'Total time to %s: %s' % ('shd.repathFileNodesForPublish()', time.time()-start)
        
        ## Now do the smartConn
        start = time.time()
        shd.smartConn()
        print 'Total time to %s: %s' % ('shd.smartConn()', time.time()-start)
        
        ## Fix remap and ramps color entry plugs and any incorrect ordering
        ## Leads to bad plugs being inserted when the XML recreates all the values. Querying also creates which makes black colour entry plugs.
        start = time.time()
        shd.fixRamps(cmds.ls(type = 'remapValue'))
        shd.fixRamps(cmds.ls(type = 'ramp'))
        print 'Total time to %s: %s' % ('shd.fixRamps()', time.time()-start)

        ## Removed duplicate dgSHD nodes...
        shd.deleteDGSHD()

        ## Delete empty UV Sets
        start = time.time()
        cleanup.deleteEmptyUVSets()
        print 'Total time to %s: %s' % ('cleanup.deleteEmptyUVSets()', time.time() - start)
        ## NOW MOVE ON TO PUBLISHING
        return items    