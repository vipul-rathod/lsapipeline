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
Hook that loads items into the current scene. 

This hook supports a number of different platforms and the behaviour on each platform is
different. See code comments for details.


"""
import tank
from tank.platform.qt import QtCore, QtGui
import os, sys
import xml.etree.ElementTree as xml
import maya.cmds as cmds
import maya.mel as mel
## Now get the custom tools
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
import shader_lib as shd
#reload(shd)
#reload(cleanup)

class AddFileToScene(tank.Hook):
    
    def execute(self, engine_name, file_path, shotgun_data, **kwargs):
        """
        Hook entry point and app-specific code dispatcher
        """
                
        if engine_name == "tk-maya":
            curSel = cmds.ls(sl = True)[0]
            if not curSel:
                raise Exception("You must have a valid [ASSET_NAME]_hrc group selected to assign a surfVar to!!")
            else:
                self.add_surfVarfile_to_maya(file_path, shotgun_data)

        else:
            raise Exception("Don't know how to load file into unknown engine %s" % engine_name)
        
    ###############################################################################################
    # app specific implementations
    
    def add_surfVarfile_to_maya(self, file_path, shotgun_data):
        """
        Load file into Maya as an assembly reference
        """
        
        import pymel.core as pm
        import maya.cmds as cmds
        scene_path = os.path.abspath(cmds.file(query=True, sn= True))
        
        # get the slashes right
        file_path = file_path.replace(os.path.sep, "/")
        
        (path, ext) = os.path.splitext(file_path)
        debug(None, method = 'add_surfVarfile_to_maya', message = 'Creating shaders for surface variation...', verbose = False)
        
        curSel = cmds.ls(sl = True)

        ## Cleanup shaders on selected
        for each in cmds.ls(sl = True):
            cmds.sets(each, e = True, forceElement = 'initialShadingGroup')
        mel.eval("MLdeleteUnused();")
        
        ## Now process the xml
        if ext in [".xml"]:
            if 'Light' in scene_path:
                """
                Example of shotgun_data:
                {
                'version_number': 7, 
                'description': 'Updating for lighting testing', 
                'created_at': datetime.datetime(2014, 3, 3, 12, 46, 31, tzinfo=<tank_vendor.shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x000000002A29BE48>), 
                'published_file_type': {'type': 'PublishedFileType', 'id': 1, 'name': 'Maya Scene'}, 
                'created_by': {'type': 'HumanUser', 'id': 42, 'name': 'James Dunlop'}, 
                'entity': {'type': 'Asset', 'id': 1427, 'name': 'jbd_dummybld_BLD'}, 
                'image': 'https://sg-media-usor-01.s3.amazonaws.com/ea241984334a6d66408726328553b1baecf5f5f9/1dd2116047d57cf945dca0222a43e2ab02a682dc/tanktmpfk17lm_t.jpg?AWSAccessKeyId=AKIAJ2N7QGDWF5H5DGZQ&Expires=1393812258&Signature=Ah5c866A8LJkMQQzaGkjK3E%2F9ag%3D', 
                'path': {'local_path_windows': 'I:\\bubblebathbay\\assets\\Building\\jbd_dummybld_BLD\\SRFVar_01\\publish\\xml\\jbddummybldBLD.v007.xml', 
                'name': 'jbddummybldBLD.v007.xml', 
                'local_path_linux': None, 
                'url': 'file://I:\\bubblebathbay\\assets\\Building\\jbd_dummybld_BLD\\SRFVar_01\\publish\\xml\\jbddummybldBLD.v007.xml', 
                'local_storage': {'type': 'LocalStorage', 'id': 1, 'name': 'primary'}, 
                'local_path': 'I:\\bubblebathbay\\assets\\Building\\jbd_dummybld_BLD\\SRFVar_01\\publish\\xml\\jbddummybldBLD.v007.xml', 
                'content_type': None, 
                'local_path_mac': '/Volumes/bubblebathbay3D/bubblebathbay/assets/Building/jbd_dummybld_BLD/SRFVar_01/publish/xml/jbddummybldBLD.v007.xml', 
                'type': 'Attachment', 'id': 6202, 'link_type': 'local'}, 
                'type': 'PublishedFile', 
                'id': 4752, 
                'name': 'jbddummyBLDXML_SurfVar01'
                }
                """
                debug(None, method = 'add_surfVarfile_to_maya', message = 'Create all shaders for surface variation for lighting step...', verbose = False)
                
                for each in curSel:
                    shd.createAll(XMLPath = file_path, Namespace = '', Root = 'MaterialNodes', selected = True, selectedOrigHrcName = each)
                
                    ## Find the parent group
                    entity = shotgun_data['entity']
                    assetName = '%s_hrc' % entity["name"]
                    getParent = '|%s' % cmds.listRelatives(assetName, parent  = True)[0]          
                    debug(None, method = 'add_surfVarfile_to_maya', message = 'getParent: %s' % getParent, verbose = False)
                    
                    shd.connectAll(XMLPath = file_path, parentGrp = getParent, Namespace = '', Root = 'MaterialNodes', selected = True, selectedOrigHrcName = each)
            else:
                for each in curSel:
                    debug(None, method = 'add_surfVarfile_to_maya', message = 'Create all shaders for surface variation outside lighting step...', verbose = False)
                    shd.createAll(XMLPath = file_path, Namespace = '', Root = 'MaterialNodes', selected = True, selectedOrigHrcName = each)
                    
                    debug(None, method = 'add_surfVarfile_to_maya', message = 'Connect all shaders for surface variation outside lighting step...', verbose = False)
                    shd.connectAll(XMLPath = file_path, parentGrp = '', Namespace = '', Root = 'MaterialNodes', selected = True, selectedOrigHrcName = each)          

        else:
            self.parent.log_error("Unsupported file extension for %s! Nothing will be loaded." % file_path)

    
     
