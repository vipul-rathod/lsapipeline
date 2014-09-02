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
Hook that scans the scene for referenced maya files. Used by the breakdown to 
establish a list of things in the scene.

This implementation supports the following types of references:

* maya references
* texture file input nodes

"""

from tank import Hook
from tank import TankError
import maya.cmds as cmds
import pymel.core as pm
import os, sys
## Now get the custom tools
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
import utils as utils

class ScanScene(Hook):
    
    def execute(self, **kwargs):
        # scan scene for references.
        # for each reference found, return
        # a dict with keys node, type and path
        import pymel.core as pm
        import maya.cmds as cmds
        ## Make sure the scene assembly plugins are loaded
        utils.loadSceneAssemblyPlugins(TankError)
            
        refs = []
        
        # first let's look at maya references        
        for x in pm.listReferences():
            node_name = x.refNode.longName()
            # get the path and make it platform dependent
            # (maya uses C:/style/paths)
            maya_path = x.path.replace("/", os.path.sep)
            
            refs.append( {"node": node_name, "type": "reference", "path": maya_path}) 

        ## Now look for assembly References
        try:
            ref_nodes = cmds.ls(type = 'assemblyReference')
            for eachRef in ref_nodes:
                # get the path:
                ref_path = cmds.getAttr('%s.definition' % eachRef)
                # make it platform dependent
                # (maya uses C:/style/paths)
                maya_path = ref_path.replace("/", os.path.sep)           
                refs.append( {"node": eachRef, "type": "assemblyReference", "path": maya_path}) 
        except:
            pass

        ## Now look for coreArchives
        try:
            core_nodes = cmds.ls(type = 'core_archive')
            for eachCore in core_nodes:
                # get the path:
                core_path = cmds.getAttr('%s.filename' % eachCore)
                # make it platform dependent
                # (maya uses C:/style/paths)
                maya_path = core_path.replace("/", os.path.sep)
                refs.append( {"node": eachCore, "type": "coreArchive", "path": maya_path})
                print refs
        except:
            pass

        #=======================================================================
        # NOTE these do not work because the CustomEnitity03 doesn't have a Sequence in the template, and we're using
        # a sequence folder = broken templates. I've removed the templates for now and shutdown trying to get this to work
        
        ##
        # ## Now look for audioFiles
        # try:
        #     audio_nodes = cmds.ls(type = 'audio')
        #     for eachAudio in audio_nodes:
        #         # get the path:
        #         audio_path = cmds.getAttr('%s.filename' % eachAudio)
        #         # make it platform dependent
        #         # (maya uses C:/style/paths)
        #         maya_path = audio_path.replace("/", os.path.sep)
        #         refs.append({"node": eachAudio, "type": "audio", "path": maya_path})
        # except:
        #     pass
        #=======================================================================

        # now look at file texture nodes
        for file_node in cmds.ls(l=True, type="file"):
            # ensure this is actually part of this scene and not referenced
            if cmds.referenceQuery(file_node, isNodeReferenced= True):
                # this is embedded in another reference, so don't include it in the
                # breakdown
                continue

            # get path and make it platform dependent
            # (maya uses C:/style/paths)
            path = cmds.getAttr("%s.fileTextureName" % file_node).replace("/", os.path.sep)
            
            refs.append( {"node": file_node, "type": "file", "path": path})
        
        print refs
        return refs

    