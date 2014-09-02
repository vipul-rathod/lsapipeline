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
Hook that contains the logic for updating a reference from one version to another.
Coupled with the scene scanner hook - for each type of reference that the scanner
hook can detect, a piece of upgrade logic should be provided in this file.

"""

from tank import Hook
import maya.cmds as cmds
import pymel.core as pm
mc = False
try:
    from mentalcore import mapi
    mc  = True
except:
    pass

class MayaBreakdownUpdate(Hook):
    
    def execute(self, items, **kwargs):

        # items is a list of dicts. Each dict has items node_type, node_name and path

        for i in items:
            print i
            node = i["node_name"]
            node_type = i["node_type"]
            new_path = i["path"]
        
            engine = self.parent.engine
            engine.log_debug("%s: Updating reference to version %s" % (node, new_path))
    
            if node_type == "reference":
                # maya reference            
                rn = pm.system.FileReference(node)
                rn.replaceWith(new_path)
                
            elif node_type == "file":
                # file texture node
                file_name = cmds.getAttr("%s.fileTextureName" % node)
                cmds.setAttr("%s.fileTextureName" % node, new_path, type="string")

            elif node_type == "assemblyReference":
                cmds.setAttr("%s.definition" % node, new_path, type="string")

            elif node_type == 'coreArchive':
                if mc:
                    mapi.load_archive(path = new_path, archive_node = node)

            #=======================================================================
            # NOTE these do not work because the CustomEnitity03 doesn't have a Sequence in the template, and we're using
            # a sequence folder = broken templates. I've removed the templates for now and shutdown trying to get this to work
            
            # elif node_type == 'audio':
            #     ## TO DO: This is not updating audio paths.
            #     cmds.setAttr("%s.filename" % node, new_path, type="string")
            #===================================================================

            else:
                raise Exception("Unknown node type %s" % node_type)

