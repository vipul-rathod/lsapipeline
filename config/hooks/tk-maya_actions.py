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
Hook that loads defines all the available actions, broken down by publish type. 
"""
import sgtk
import os, sys, tank
import maya.cmds as cmds
import maya.mel as mel
try:
    from mentalcore import mlib
    from mentalcore import mapi
except:
    cmds.warning('NO MENTAL CORE LOADED!!!')
## Now get the custom tools
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')

import utils as utils
import shader_lib as shd
from debug import debug
import core_archive_lib as coreLib
import maya_asset_MASTERCLEANUPCODE as cleanup


from tank import TankError
HookBaseClass = sgtk.get_hook_baseclass()

class MayaActions(HookBaseClass):
    
    ##############################################################################################################
    # public interface - to be overridden by deriving classes 
    
    def generate_actions(self, sg_publish_data, actions, ui_area):
        """
        Returns a list of action instances for a particular publish.
        This method is called each time a user clicks a publish somewhere in the UI.
        The data returned from this hook will be used to populate the actions menu for a publish.
    
        The mapping between Publish types and actions are kept in a different place
        (in the configuration) so at the point when this hook is called, the loader app
        has already established *which* actions are appropriate for this object.
        
        The hook should return at least one action for each item passed in via the 
        actions parameter.
        
        This method needs to return detailed data for those actions, in the form of a list
        of dictionaries, each with name, params, caption and description keys.
        
        Because you are operating on a particular publish, you may tailor the output 
        (caption, tooltip etc) to contain custom information suitable for this publish.
        
        The ui_area parameter is a string and indicates where the publish is to be shown. 
        - If it will be shown in the main browsing area, "main" is passed. 
        - If it will be shown in the details area, "details" is passed.
        - If it will be shown in the history area, "history" is passed. 
        
        Please note that it is perfectly possible to create more than one action "instance" for 
        an action! You can for example do scene introspection - if the action passed in 
        is "character_attachment" you may for example scan the scene, figure out all the nodes
        where this object can be attached and return a list of action instances:
        "attach to left hand", "attach to right hand" etc. In this case, when more than 
        one object is returned for an action, use the params key to pass additional 
        data into the run_action hook.
        
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :param actions: List of action strings which have been defined in the app configuration.
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption and description
        """
        app = self.parent
        app.log_debug("Generate actions called for UI element %s. "
                      "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data))
        
        action_instances = []

        if "open" in actions:
            action_instances.append( {"name": "open", 
                                      "params": None,
                                      "caption": "Open maya scene file", 
                                      "description": "This will open the maya publish file."} )

        if "audio" in actions:
            action_instances.append( {"name": "audio", 
                                      "params": None,
                                      "caption": "Create audioNode...", 
                                      "description": "This will add the item to the scene as an audioNode."} )

        if "assemblyReference" in actions:
            action_instances.append( {"name": "assemblyReference", 
                                      "params": None,
                                      "caption": "Create assemblyReference", 
                                      "description": "This will add the item to the scene as an assembly reference."} )

        if "openLayout" in actions:
            action_instances.append( {"name": "openLayout", 
                                      "params": None,
                                      "caption": "Load published layout scene...", 
                                      "description": "This will load a published layout scene for Animation."} )

        if "reference" in actions:
            action_instances.append( {"name": "reference", 
                                      "params": None,
                                      "caption": "Create Reference...", 
                                      "description": "This will add the item to the scene as a standard reference."} )

        if "import" in actions:
            action_instances.append( {"name": "import", 
                                      "params": None,
                                      "caption": "Import into Scene...", 
                                      "description": "This will import the item into the current scene."} )

        if "texture_node" in actions:        
            action_instances.append( {"name": "texture_node",
                                      "params": None, 
                                      "caption": "Create Texture Node...", 
                                      "description": "Creates a file texture node for the selected item.."} )        

        if "coreArchive" in actions:        
            action_instances.append( {"name": "coreArchive",
                                      "params": None, 
                                      "caption": "Create MC coreArchive...", 
                                      "description": "Creates a mentalCore coreArchive"} )

        if "importENV" in actions:
            action_instances.append( {"name": "importENV", 
                                      "params": None,
                                      "caption": "Import ENV into Scene...",
                                      "description": "This will import the item into the current scene."} )

        if "importDGSHD" in actions:
            action_instances.append( {"name": "importDGSHD", 
                                      "params": None,
                                      "caption": "Import downgraded shaders...", 
                                      "description": "This will import the published down graded shaders onto the current asset geo.."} )

        if "loadSurfVar" in actions:
            action_instances.append( {"name": "loadSurfVar", 
                                      "params": None,
                                      "caption": "Load published SRFVar XML...", 
                                      "description": "This will load published SRF XML for a surface variation onto geo in lighting scene."} )

        if "loadANIMForFX" in actions:
            action_instances.append( {"name": "loadANIMForFX", 
                                      "params": None,
                                      "caption": "Load published animation scene...", 
                                      "description": "This will load a published animation scene for FX."} )
            
#         if "openLayout" in actions:
#             action_instances.append( {"name": "openLayout", 
#                                       "params": None,
#                                       "caption": "Load published layout scene...", 
#                                       "description": "This will load a published layout scene for Animation."} )

        if "assetXML" in actions:        
            action_instances.append( {"name": "assetXML",
                                      "params": None, 
                                      "caption": "Load published SHD xml...", 
                                      "description": "Create shaders for lighting asset from published xml.."} )        

        if "lib_world_loader" in actions:        
            action_instances.append( {"name": "lib_world_loader",
                                      "params": None, 
                                      "caption": "Import Lighting elements...", 
                                      "description": "Create LIBWORLD for lighting asset from publishes.."} )  

        if "static_world_loader" in actions:        
            action_instances.append( {"name": "static_world_loader",
                                      "params": None, 
                                      "caption": "Import STATIC ENV...", 
                                      "description": "Import a static env file into a lighting shot..."} )

        if "fx_ATOM" in actions:
            action_instances.append( {"name": "fx_ATOM",
                                      "params": None,
                                      "caption": "Import ATOM...",
                                      "description": "Import the latest animation via ATOM into fx shot..."} )

        return action_instances
                
    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.
        
        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """
        app = self.parent
        app.log_debug("Execute action called for action %s. "
                      "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data))
        
        # resolve path
        path = self.get_publish_path(sg_publish_data)

        if name == "assemblyReference":
            self._create_assemblyReference(path, sg_publish_data)

        if name == "reference":
            self._create_reference(path, sg_publish_data)

        if name == "import":
            self._importAssetToMaya(path, sg_publish_data)
        
        if name == "importENV":
            self._importAssetToMaya(path, sg_publish_data, env = True)

        if name == "texture_node":
            self._create_texture_node(path, sg_publish_data)
                        
        if name == "audio":
            self._create_audio_node(path, sg_publish_data)

        if name == "open":
            self._openScene(path, sg_publish_data)

        if name == "coreArchive":
            self._add_coreArchive(path, sg_publish_data)

        if name == "importDGSHD":
            self._importDGSHD(path, sg_publish_data)

        if name == "loadSurfVar":
            self._loadSurfVar(path, sg_publish_data)
        
        if name == "loadANIMForFX":
            self._loadANIMScene_ForFX(path, sg_publish_data)
            
        if name == "openLayout":
            self._loadLayoutScene_ForANIM(path, sg_publish_data)

        if name == "assetXML":
            self._fetchAssetXML(path, sg_publish_data)
            
        if name == "lib_world_loader":
            self._fetchLIBWORLD(path, sg_publish_data)
            
        if name == "static_world_loader":
            self._fetch_STATICENV(path, sg_publish_data)

        if name == "fx_ATOM":
            self._fetch_fx_ATOM(path, sg_publish_data)
    ##############################################################################################################
    ## Fetch ATOM for FX Iteration
    def _fetch_fx_ATOM(self, path, sg_publish_data):
        ## Back to frame 1
        minFrame = cmds.playbackOptions(min = True, q = True)
        [cmds.currentTime(minFrame) for i in range(2)]

        ## First get all the dags from atom file...
        with open(path, 'r') as fileData:
            dagObjects = [next(fileData).split(' ')[2] for line in fileData if 'dagNode {' in line]
        dagObjects = [cmds.ls(obj, l = True)[0] for obj in dagObjects if cmds.ls(obj, l = True) and cmds.objExists(cmds.ls(obj, l = True)[0])] if dagObjects else None

        ## Delete all the non-referenced animated curves of referenced related objects (preserve whatever the fx's curves)
        animCurves = [crv for crv in cmds.ls(type = 'animCurve') if not cmds.referenceQuery(crv, isNodeReferenced = True) if cmds.listConnections(crv) for each in cmds.listConnections(crv) if cmds.ls(each, long = True)[0] in dagObjects] if dagObjects else None
        cmds.delete(animCurves) if animCurves else None

        ## Force ATOM UI...
        mel.eval('ImportAnimOptions;')

        ## Include shotCam in selection before importing by selecting first...
        shotCam = [mel.eval('rootOf("%s");' % each.split('.')[0]) for each in cmds.ls('*.type', long = True) if cmds.getAttr(each) == 'shotCam']
        dagObjects.extend(shotCam) if shotCam else None
        cmds.select(dagObjects, replace = True)

        ## Perform ATOM import
        cmds.file(	path,
                    i = True,
                    type = 'atomImport',
                    renameAll = True,
                    options = ';;targetTime=3;option=insert;match=string;;selected=childrenToo;search=;replace=;prefix=;suffix=;mapFile=I:/bubblebathbay/episodes/training/training_sh007/FX/work/maya/data;',
                    )

        ## Force delete ATOM UI...
        if cmds.window('OptionBoxWindow', exists = True):
            cmds.deleteUI('OptionBoxWindow', window = True)

    # helper methods which can be subclassed in custom hooks to fine tune the behaviour of things
    def _fetch_STATICENV(self, path, sg_publish_data):
        ## Do the import
        self._doSTATIC_import(path, sg_publish_data)
    
    def _fetchLIBWORLD(self, path, sg_publish_data):
        print 'STILL GOT SOME STUFF TO ADD IN HERE!!...such as;'
        print 'Waterfall handling into render layers setup'
        print 'BG Hills render layers setup'
        
        ## Do the import
        self._do_import(path, sg_publish_data)
        
        ## Check for the clouds import and setup those correctly
        if 'cloud' in path:
            self.setCloudsToCloudLayer()
        ## Check for the waterfall import and setup those correctly
        elif 'waterfall' in path:
            pass
        elif 'bghills' in path:
            pass
        else:
            pass
        
        ## Now try to clean the duplicate cores that may exist
        #self._cleanFnCores()

    def _fetchAssetXML(self, path, sg_publish_data):
        #print path, sg_publish_data
        ## I:\bubblebathbay\assets\Environment\BBB_JBDDUMMY_LND\SRF\publish\uvxml\BBBJBDDUMMYLND.xml 
        ## {'version.Version.sg_status_list': None, 'task.Task.due_date': None, 'version_number': 53, 'code': 'BBBJBDDUMMYLND.xml', 'description': None, 'task.Task.sg_status_list': 'wtg', 'image': 'https://sg-media-usor-01.s3.amazonaws.com/ea241984334a6d66408726328553b1baecf5f5f9/49d59fec2908edc8a73bfe3eb0fc776de1058770/no_preview_t.jpg?AWSAccessKeyId=AKIAIFHY52V77FIVWKLQ&Expires=1401237658&Signature=lkCn8kdlHILUj16W%2FTqnagQWBQ4%3D', 'published_file_type': {'type': 'PublishedFileType', 'id': 1, 'name': 'Maya Scene'}, 'entity': {'type': 'Asset', 'id': 1768, 'name': 'BBB_JBDDUMMY_LND'}, 'task.Task.content': 'Surface', 'task': {'type': 'Task', 'id': 24841, 'name': 'Surface'}, 'version': None, 'path': {'local_path_windows': 'I:\\bubblebathbay\\assets\\Environment\\BBB_JBDDUMMY_LND\\SRF\\publish\\uvxml\\BBBJBDDUMMYLND.xml', 'name': 'BBBJBDDUMMYLND.xml', 'local_path_linux': None, 'url': 'file://I:\\bubblebathbay\\assets\\Environment\\BBB_JBDDUMMY_LND\\SRF\\publish\\uvxml\\BBBJBDDUMMYLND.xml', 'local_storage': {'type': 'LocalStorage', 'id': 1, 'name': 'primary'}, 'local_path': 'I:\\bubblebathbay\\assets\\Environment\\BBB_JBDDUMMY_LND\\SRF\\publish\\uvxml\\BBBJBDDUMMYLND.xml', 'content_type': None, 'local_path_mac': '/Volumes/bubblebathbay3D/bubblebathbay/assets/Environment/BBB_JBDDUMMY_LND/SRF/publish/uvxml/BBBJBDDUMMYLND.xml', 'type': 'Attachment', 'id': 46475, 'link_type': 'local'}, 'type': 'PublishedFile', 'id': 24964, 'name': 'BBBJBDDUMMYLNDXML'}
        ## Find the assets parent group in the scene now..
        parentGrp = cmds.listRelatives('%s_hrc' % sg_publish_data['entity']["name"], p = True) or ''
            
        if 'uvxml' in path:
            cmds.warning('This is not a valid SHD XML try again....')
        else:
            shd.createAll(XMLPath = path, parentGrp = parentGrp, Namespace = '', Root = 'MaterialNodes', selected = False, selectedOrigHrcName = '')
            shd.connectAll(XMLPath = path, parentGrp= parentGrp, Namespace = '', Root = 'MaterialNodes', selected = False, selectedOrigHrcName = '')             

    def _openScene(self, path, sg_publish_data):
        """
        Create a reference with the same settings Maya would use
        if you used the create settings dialog.
        
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        import maya.cmds as cmds

        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)
                
        cmds.file(path, o = True, f = True)

    def _create_audio_node(self, path, sg_publish_data):
        """
        Load file into Maya.
        This implementation creates a standard maya audio node.
        """
        
        import pymel.core as pm
        import maya.cmds as cmds
        
        # get the slashes right
        path = path.replace(os.path.sep, "/")
        
        (path, ext) = os.path.splitext(path)
        if os.path.isfile(path):      
            if ext in [".ma", ".mb"]:
                # maya file - load it as a reference
                getEntity = sg_publish_data.get('entity')
                namespace = getEntity.get('name')
                print 'Namespace: %s' % namespace
                print 'Path: %s' % path
                
                if not cmds.objExists(namespace):
                    cmds.file('%s.ma' % path, i = True, f = True)
                    ## Clean out any imported namespaces
                    for eachNode in cmds.ls(ap= True):
                        if ':' in eachNode:
                            try:
                                cmds.rename(eachNode, '%s' % eachNode.split(':')[-1])
                            except RuntimeError:
                                pass
                else:
                    cmds.warning('Audio already exists in the scene. Use the scene breakdown to update your audio.')
                
            else:
                self.parent.log_error("Unsupported file extension for %s! Nothing will be loaded." % file_path)
        else:
            cmds.warning('File not found! Please contact a co-ord to fix this for you now.')

    def _create_assemblyReference(self, path, sg_publish_data):
        """
        Create an assembly reference with the same settings Maya would use
        if you used the create settings dialog.
        
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        print 'path: %s' % path
        import maya.cmds as cmds

        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)
        
        # make a name space out of entity name + publish name
        # e.g. bunny_upperbody                
        #namespace = "%s %s" % (sg_publish_data.get("entity").get("name"), sg_publish_data.get("name"))
        namespace = "%s_ADef_ARef" % sg_publish_data.get("entity").get("name").replace('_', '')
        #namespace = namespace.replace(" ", "_")
        print 'namespace: %s' % namespace
        
        ## Make sure the scene assembly plugins are loaded
        utils.loadSceneAssemblyPlugins(TankError)
        
        # maya file - load it as an assembly reference
        assemblyDefPath = 'assemblyDef'.join(path.split('maya'))
        print 'assemblyDefPath: %s' % assemblyDefPath
        
        if not cmds.objExists(namespace):
            cmds.container(type = 'assemblyReference',  name = namespace)
            cmds.setAttr('%s.definition' % namespace,  assemblyDefPath, type = 'string')
        else:
            cmds.warning('Asset %s already exists in scene, try using the sceneBreakdown tool to update instead....' % namespace)     
        
    def _create_reference(self, path, sg_publish_data):
        """
        Create a reference with the same settings Maya would use
        if you used the create settings dialog.
        
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        import pymel.core as pm
        import maya.cmds as cmds

        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)
        
        # make a name space out of entity name + publish name
        # e.g. bunny_upperbody                
        # namespace = "%s %s" % (sg_publish_data.get("entity").get("name"), sg_publish_data.get("name"))
        namespace = sg_publish_data.get("entity").get("name")
        namespace = namespace.replace(" ", "_")
                
        # pm.system.createReference(path,
        #                           loadReferenceDepth= "all",
        #                           mergeNamespacesOnClash=False,
        #                           namespace=namespace)
        cmds.file(path, r = True, loadReferenceDepth = "all", options = 'v=0', ns = namespace, f = True)
    
    def _doSTATIC_import(self, path, sg_publish_data):
        """       
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        import pymel.core as pm
        import maya.cmds as cmds

        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)
                
        # make a name space out of entity name + publish name
        # e.g. bunny_upperbody                
        namespace = "%s %s" % (sg_publish_data.get("entity").get("name"), sg_publish_data.get("name"))
        namespace = namespace.replace(" ", "_")
        
        # perform a more or less standard maya import, putting all nodes brought in into a specific namespace
        cmds.file(path, i = True)

        if '_Addon' not in path:
            ## Clean any bad build grps just incase the person in cahrge of the static env rebuilt the cores but didn't clean the geo_hrc core groups out..
            ## This helps stop a full scene rebuild from failing if the lighter needs to do this..
            self._removeCoreGrps()

            ## Clean general namespaces from the import ignoring the core archive names...
            getAllNameSpaces = cmds.namespaceInfo(listOnlyNamespaces = True)
            for eachNS in getAllNameSpaces:
                if namespace in eachNS and 'CORE' not in eachNS:
                    try:
                        cmds.namespace(removeNamespace = eachNS, mergeNamespaceWithRoot = True)
                    except RuntimeError:
                        pass


            ## Now try to clean the duplicate cores that may exist
            self._cleanFnCores()
            self._removeCoreGrps()
    
    def _do_import(self, path, sg_publish_data):
        """       
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        import pymel.core as pm
        import maya.cmds as cmds

        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)
                
        # make a name space out of entity name + publish name
        # e.g. bunny_upperbody                
        namespace = "%s %s" % (sg_publish_data.get("entity").get("name"), sg_publish_data.get("name"))
        namespace = namespace.replace(" ", "_")
        
        # perform a more or less standard maya import, putting all nodes brought in into a specific namespace
        cmds.file(path, i=True, renameAll=True, namespace=namespace, loadReferenceDepth="all", preserveReferences=True)
        getAllNameSpaces = cmds.namespaceInfo(listOnlyNamespaces = True)
        for eachNS in getAllNameSpaces:
            if namespace in eachNS and 'CORE' not in eachNS:
                try:
                    cmds.namespace(removeNamespace = eachNS, mergeNamespaceWithRoot = True)
                except RuntimeError:
                    pass
                    
    def _create_texture_node(self, path, sg_publish_data):
        """
        Create a file texture node for a texture
        
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        import pymel.core as pm
        import maya.cmds as cmds        
                
        x = cmds.shadingNode('file', asTexture=True)
        cmds.setAttr( "%s.fileTextureName" % x, path, type="string" )

####################################################################################################        
############# BUBBLE BATH BAY SPECIFIC LOADERS
####################################################################################################

    def _importAssetToMaya(self, path, sg_publish_data, group = True, env = False):
        """
        Import file into Maya
        """
        
        import pymel.core as pm
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = path.replace(os.path.sep, "/")
        
        ignoreAsset = 'ENV_WORLDMAP_ANIM'
        
        (path, ext) = os.path.splitext(file_path)
        groupName = ''
        
        if ext in [".ma", ".mb"]:
            if ignoreAsset not in file_path:
                assetName = '%s_hrc' % file_path.split('.')[0].split('/')[-1]
                if group:
                    if env:
                        groupName = assetName
                    else:
                        groupName = '%s_importgroupdeleteme' % assetName
    
                ## Set model panel to show None before import
                modelPanels = cmds.getPanel(type = 'modelPanel')
                if modelPanels:
                    [cmds.modelEditor(mp, edit = True, allObjects = False) for mp in modelPanels]
    
                ## Now doe the import
                cmds.file(file_path, i =True, gr = group, gn = groupName, loadReferenceDepth="all", preserveReferences=True)
    
                ## Set all AD to None
    #             [cmds.assembly(each, edit = True, active = '') for each in cmds.ls(type = 'assemblyReference')]
    
                ## Set all AD to Full
                [cmds.assembly(each, edit = True, active = 'gpuCache') for each in cmds.ls(type = 'assemblyReference')]
    
                ## Set model panel to show All
                if modelPanels:
                    [cmds.modelEditor(mp, edit = True, allObjects = True) for mp in modelPanels]
    
                for eachNode in cmds.ls(ap = True):
                    if ':' in eachNode:
                        try:
                            cmds.rename(eachNode, '%s' % eachNode.split(':')[-1])
                        except RuntimeError:
                            pass
                ## Now look for and try to connect the Library assets that were previously shaded 
                shd.reconnectLIBSHD(rootGrp = groupName, freshImport = True)
                
                if env:
                    if cmds.objExists('ENVS_hrc'):
                        try:cmds.parent(assetName, 'ENVS_hrc')
                        except:pass
            else:
                cmds.confirmDialog(t='Cannot load WORLD_MAP_ANIM', m="Cannot load WORLD_MAP_ANIM Environment from this loader.\nKindly use Full Loader", button="Ok")
        else:
            raise Exception("Unsupported file extension for %s! Nothing will be loaded." % file_path)
        
    def _add_coreArchive(self, path, sg_publish_data):
        """
        Load file into Maya as an assembly reference
        """      
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = path.replace(os.path.sep, "/")
        
        (path, ext) = os.path.splitext(file_path)
        
        debug(None, method = 'add_coreArchive_to_maya', message = 'file_path:%s' % file_path, verbose = False)
        if ext in [".mi", ".gz"]:
           ## For some reason the publish of the secondary is DROPPING the .gz
           ## So we're adding it back in on the load! And using the base mentalCore loader as this is the only one that works, ripping it out doens't load properly.
           
           mapi.load_archive(path = file_path)
           debug(None, method = 'add_coreArchive_to_maya', message = 'Archive loaded successfully...', verbose = False)

           coreLib._setAllBBoxUpdatesOff()

           coreLib._setAllToHold()
           debug(None, method = 'add_coreArchive_to_maya', message = '_setAllToHold successfully...', verbose = False)
           
           coreLib.cleanupCoreArchiveImports()
           debug(None, method = 'add_coreArchive_to_maya', message = 'cleanupCoreArchiveImports successfully...', verbose = False)
           
           coreLib.cleanMaterialNS()
           debug(None, method = 'add_coreArchive_to_maya', message = 'cleanMaterialNS successfully...', verbose = False)
           
           coreLib.tagRootArchive()
           debug(None, method = 'add_coreArchive_to_maya', message = 'Tag Root Archives complete...', verbose = False)
           
        else:
            raise Exception("Unsupported file extension for %s! Nothing will be loaded." % file_path)
    
    def _importDGSHD(self, path, sg_publish_data):
        """
        Load dg shader xml file
        """        
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = path.replace(os.path.sep, "/")
        
        (path, ext) = os.path.splitext(file_path)
        
        if ext in [".xml"]:
            if not cmds.objExists('dgSHD'):
                cmds.scriptNode(n ='dgSHD')
            debug(None, method = 'add_file_to_maya', message = 'Cleaning shaders...', verbose = False)
            cleanup.cleanUpShaders()

            debug(None, method = 'add_file_to_maya', message = 'Creating shaders...', verbose = False)
            shd.createAll(XMLPath = file_path, Namespace = '', Root = 'MaterialNodes')
            
            debug(None, method = 'add_file_to_maya', message = 'Connect all shaders...', verbose = False)
            shd.connectAll(XMLPath = file_path, Namespace = '', Root = 'MaterialNodes')

            debug(None, method = 'add_file_to_maya', message = 'Downgrading shaders now...', verbose = False)
            shd.downgradeShaders()
            
            debug(None, method = 'add_file_to_maya', message = 'Downgrade complete!', verbose = False)

            ####TAG geo_hrc with DGSHD XML VERSION NUMBER
            ##################
            versionNumber = file_path.split('.')[-2]
            if not cmds.objExists('geo_hrc.version'):
                cmds.addAttr('geo_hrc', ln = 'version', dt = 'string')
                cmds.setAttr('geo_hrc.version', versionNumber, type = 'string')

    def _loadSurfVar(self, path, sg_publish_data):
        """
        Load file into Maya as an assembly reference
        """
        
        import pymel.core as pm
        import maya.cmds as cmds
        scene_path = os.path.abspath(cmds.file(query=True, sn= True))
        
        # get the slashes right
        file_path = path.replace(os.path.sep, "/")
        
        (path, ext) = os.path.splitext(file_path)
        debug(None, method = 'add_surfVarfile_to_maya', message = 'Creating shaders for surface variation...', verbose = False)
        
        curSel = cmds.ls(sl = True)
        if curSel:
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
                        #sg_publish_data.get("entity").get("name")
                        entity      = sg_publish_data.get("entity")
                        assetName   = '%s_hrc' % entity.get("name")
                        getParent   = '|%s' % cmds.listRelatives(assetName, parent  = True)[0]          
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
        else:
            cmds.warning('You must have a valid selection to assign the surfVar to!!!')
    
    def _loadANIMScene_ForFX(self, path, sg_publish_data):
        """
        Load file into Maya.
        
        This implementation opens a maya animation scene for FX and saves this newly opened scene in the right workspace with 
        a new version number appropriate to the FX files.
        """
        
        import pymel.core as pm
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = path.replace(os.path.sep, "/")
        debug(app = None, method = 'add_file_to_maya', message = 'file_path: %s' % file_path, verbose = False)
        #file_path: I:/bubblebathbay/episodes/eptst/eptst_sh2000/Anm/publish/maya/eptstsh2000.v002.mb
        
                
        file_version = int(file_path.split('.')[1].split('v')[-1])
        debug(app = None, method = 'add_file_to_maya', message = 'file_version: %s' % file_version, verbose = False)
        
        (path, ext) = os.path.splitext(file_path)
              
        if ext in [".ma", ".mb"]:
            ## Open the blocking file
            cmds.file(file_path, o = True, f = True)
            
            ## Cleanup unknown nodes to make sure we can save from mb back to ma
            for each in cmds.ls():
                if cmds.nodeType(each) == 'unknown':
                    cmds.delete(each)
                    
            ## Build the script node for the FX app.py to use as the current version number of the oceanPreset
            if not cmds.objExists('fxNugget'):
                cmds.scriptNode(n ='fxNugget')
                cmds.addAttr('fxNugget', ln = 'animVersion', at = 'long')
                cmds.setAttr('fxNugget.animVersion', file_version)
            ## Save the animation file as the next working file in the FX folder
            tk              = sgtk.sgtk_from_path("T:/software/bubblebathbay")
            getEntity       = sg_publish_data.get("entity")
            shotName        = getEntity.get("name")
            work_template   = tk.templates['shot_work_area_maya']
            pathToWorking   = r'%s' % tk.paths_from_template(work_template, {"Shot" : shotName, "Step":'FX'})[0]
            pathToWorking.replace('\\\\', '\\')
            debug(app = None, method = 'add_file_to_maya', message = 'pathToWorking: %s' % pathToWorking, verbose = False)
            ## Scan the folder and find the highest version number
            fileShotName = "".join(shotName.split('_'))
            padding = ''
            versionNumber = ''
            
            if os.path.exists(pathToWorking):
               getfiles = os.listdir(pathToWorking)

               ## Remove the stupid Keyboard folder if it exists.. thx autodesk.. not
               if 'Keyboard' in getfiles:
                   getfiles.remove('Keyboard')
               
               ## Process a clean list now.. trying to remove from the current list is giving me grief and I'm too fn tired to care...
               finalFiles = []
               for each in getfiles:
                   if each.split('.')[0] == fileShotName:
                       finalFiles.append(each)
                   else:
                       pass

               if finalFiles:
                   highestVersFile = max(finalFiles)
                   versionNumber  = int(highestVersFile.split('.')[1].split('v')[1]) + 1
               else:
                   versionNumber  = 1
            
               ## Now pad the version number
               if versionNumber < 10:
                   padding = '00'
               elif versionNumber < 100:
                   padding = '0'
               else:
                   padding = ''
               
            ## Rename the file
            #print 'FinalFilePath: %s\%s.v%s%s' % (pathToWorking, fileShotName, padding, versionNumber)  
            renameTo = '%s\%s.v%s%s' % (pathToWorking, fileShotName, padding, versionNumber)
            ## Now rename the file
            cmds.file(rename = renameTo)
            ## Now save this as a working version in the animation working folder
            cmds.file(save = True, force = True, type = 'mayaAscii')
            cmds.workspace(pathToWorking, openWorkspace = True)
            cleanup.turnOnModelEditors()
            
        else:
            self.parent.log_error("Unsupported file extension for %s! Nothing will be loaded." % file_path)

    def _loadLayoutScene_ForANIM(self, path, sg_publish_data):
        """
        Load file into Maya.
        
        This implementation opens a maya animation scene for Animation and saves this newly opened scene in the right workspace with 
        a new version number appropriate to the Animation files.
        """
        import pymel.core as pm
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = path.replace(os.path.sep, "/")
        debug(app = None, method = 'add_file_to_maya', message = 'file_path: %s' % file_path, verbose = False)
        #file_path: I:/bubblebathbay/episodes/eptst/eptst_sh2000/Anm/publish/maya/eptstsh2000.v002.mb

        file_version = int(file_path.split('.')[1].split('v')[-1])
        debug(app = None, method = 'add_file_to_maya', message = 'file_version: %s' % file_version, verbose = False)
        
        (path, ext) = os.path.splitext(file_path)
              
        if ext in [".ma", ".mb"]:
            ## Open the blocking file
            cmds.file(file_path, o = True, f = True)

            ## Cleanup unknown nodes to make sure we can save from mb back to ma
            for each in cmds.ls():
                if cmds.nodeType(each) == 'unknown':
                    cmds.delete(each)

            ## Save the animation file as the next working file in the FX folder
            tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
            getEntity = sg_publish_data.get("entity")
            shotName = getEntity.get("name")
            work_template = tk.templates['shot_work_area_maya']
            pathToWorking = r'%s' % tk.paths_from_template(work_template, {"Shot" : shotName, "Step":'Anm'})[0]
            pathToWorking.replace('\\\\', '\\')
            debug(app = None, method = 'add_file_to_maya', message = 'pathToWorking: %s' % pathToWorking, verbose = False)
            ## Scan the folder and find the highest version number
            fileShotName = "".join(shotName.split('_'))
            padding = ''
            versionNumber = ''
            
            if os.path.exists(pathToWorking):
               getfiles = os.listdir(pathToWorking)

               ## Remove the stupid Keyboard folder if it exists.. thx autodesk.. not
               if 'Keyboard' in getfiles:
                   getfiles.remove('Keyboard')
               
               ## Process a clean list now.. trying to remove from the current list is giving me grief and I'm too fn tired to care...
               finalFiles = []
               for each in getfiles:
                   if each.split('.')[0] == fileShotName:
                       finalFiles.append(each)
                   else:
                       pass

               if finalFiles:
                   highestVersFile = max(finalFiles)
                   versionNumber  = int(highestVersFile.split('.')[1].split('v')[1]) + 1
               else:
                   versionNumber  = 1
            
               ## Now pad the version number
               if versionNumber < 10:
                   padding = '00'
               elif versionNumber < 100:
                   padding = '0'
               else:
                   padding = ''
               
            ## Rename the file
            #print 'FinalFilePath: %s\%s.v%s%s' % (pathToWorking, fileShotName, padding, versionNumber)  
            renameTo = '%s\%s.v%s%s' % (pathToWorking, fileShotName, padding, versionNumber)
            ## Now rename the file
            cmds.file(rename = renameTo)
            ## Now save this as a working version in the animation working folder
            cmds.file(save = True, force = True, type = 'mayaAscii')
            cmds.workspace(pathToWorking, openWorkspace = True)
            cleanup.turnOnModelEditors()
            
        else:
            self.parent.log_error("Unsupported file extension for %s! Nothing will be loaded." % file_path)

############### WORLD ELEMENTS STUFF

    def setCloudsToCloudLayer(self):
        ## Create cloudLayer
        if not cmds.objExists('cloud_LYR'):
            cmds.createRenderLayer(name = 'cloud_LYR')

        # Function to add clouds to cloud layer        
        if cmds.objExists('LIB_WORLD_Sunnycloud_hrc'):
            cmds.editRenderLayerGlobals(currentRenderLayer='defaultRenderLayer')
            cmds.setAttr('LIB_WORLD_Sunnycloud_hrc.visibility',False)
            cmds.editRenderLayerGlobals(currentRenderLayer='cloud_LYR')
            cmds.setAttr('LIB_WORLD_Sunnycloud_hrc.visibility',True)
            cmds.editRenderLayerMembers('cloud_LYR','LIB_WORLD_Sunnycloud_hrc',noRecurse=True)
            cmds.warning('Clouds successfully linked to render layer.....')
        else:
            cmds.warning("# Error: 'LIB_WORLD_Sunnycloud_hrc' not found! #")

    def _reconnectDuplicates(self, eachGeo = '', core_archive = ''):
        """
        used to renumber the transforms in a duplicate group
        @param baseGrp: Name of the duplicate group to renumber the children of
        @type baseGrp: String
        """
        ## Fetch the Geo Shaders
        ## Now reconnect
        try:
            getCoreConnections = cmds.listConnections('%s.message' % core_archive, plugs = True)
        except:
            cmds.warning('No object matches name: %s.message' % core_archive)
            pass
            
        if not cmds.objExists(core_archive):
            cmds.warning('_reconnectDuplicates needs a valid core_archive to work!!\n\t%s is invalid!' % core_archive)
        else:
            if '%s.miGeoShader' % eachGeo not in getCoreConnections:
                #print 'Reconnected %s to %s' % (eachGeo, core_archive)
                cmds.connectAttr('%s.message' % core_archive, '%s.miGeoShader' % eachGeo, force = True)
    
    def _cleanFnCores(self, ):    
        removedNameSpaces = []
        ## Remove duplicate root core namespaces
        getAllNameSpaces = cmds.namespaceInfo(listOnlyNamespaces = True)
    
        for eachNS in getAllNameSpaces:
            if eachNS.endswith('1'):
                print 'Merging %s to %s' % (eachNS, eachNS[:-1])
                #cmds.namespace(moveNamespace = [eachNS, eachNS[:-1]], f= True)
                cmds.namespace(removeNamespace = eachNS, mergeNamespaceWithRoot = True)
                print 'Removed:  %s' % eachNS
                removedNameSpaces.append(eachNS.replace('1', '').replace('_CORE', ''))
        
        ## Make the final core groups
        self._makeFinalShotBaseCoreGroups()
        getAllPlacementGrps = cmds.ls('*placements_hrc*', l = True)
        getAllUniqueGrps = cmds.ls('*unique_geo_hrc*', l = True)
        coreHRCS = {}
        rootCores = []
        duplicateCores = []
        for eachCoreGrp in getAllUniqueGrps:
            getChildren = cmds.listRelatives(eachCoreGrp, children = True, f = True)
            
            for eachChild in getChildren:
                ## Process the cores
                if 'CORE_ARCHIVES_hrc' in eachChild:
                    getHRCS = cmds.listRelatives(eachChild, children = True, f = True)
                    for eachHRC in getHRCS:
                        if eachHRC.split("|")[-1] not in coreHRCS.keys():
                            coreHRCS[eachHRC.split("|")[-1]] = cmds.listRelatives(eachHRC, children = True, f = True)
                        else:
                            #print 'Duplicate core hrc found in %s. Appending children now to %s' % (eachHRC.split("|")[-1], eachHRC.split("|")[-1])
                            coreHRCS[eachHRC.split("|")[-1]].append(cmds.listRelatives(eachHRC, children = True, f = True))
        
                ## Process the root cores
                elif 'ROOT_ARCHIVES_DNT_hrc' in eachChild:
                    getCores = cmds.listRelatives(eachChild, children = True)
                    for eachCore in getCores:
                        if eachCore not in rootCores:
                            rootCores.append(eachCore)
                        else:
                            duplicateCores.append(eachCore)
                            #print 'Duplicate rootcore found: %s ' % eachCore
                else:
                    pass
            
        ## Make new base grps and clean up the old ones
        for key, var in coreHRCS.items():
            ## first check to see if the group is in the MASTERCORES if so use that
            if not cmds.objExists('|MASTER_COREARCHIVES_hrc|%s' % key):
                ## now check if the root hrc exists
                if not cmds.objExists('|%s' % key):
                    cmds.group(n = '|%s' % key, em = True)
                    grpPath = '|%s' % key
                else:
                    grpPath = '|%s' % key
            else:
                grpPath = '|MASTER_COREARCHIVES_hrc|%s' % key
            
            ## Figure out the core_archive name from the hrc group
            coreName = '%s_CORE_Geoshader' % grpPath.replace('_Archives_hrc', '')
            if cmds.objExists(coreName):
                getCoreGeo = [eachGeo for eachGeo in cmds.listConnections(coreName) if cmds.nodeType(eachGeo) != 'expression']
            else:
                getCoreGeo = []
            ## Now parent each of the archives to the right hrc group
            for eachCore in var:
                try:
                    cmds.parent(eachCore, grpPath)
                except RuntimeError:
                    pass
                ##Now check if the core archive already exists in the scene.
                if cmds.objExists(coreName):
                    if eachCore not in getCoreGeo:
                        ## Now try to reconnect them to the working core_root
                        self._reconnectDuplicates(eachCore, coreName)

        ## Now try to parent these groups under the final MASTER_COREARCHIVES_hrc group  
        for key in coreHRCS.keys():
            try:
                cmds.parent('|%s' % key, 'MASTER_COREARCHIVES_hrc')
            except:
                pass
                
        ## Now clean the placements
        for eachPlc in getAllPlacementGrps:
            try:
                for eachChild in cmds.listRelatives(eachPlc, children = True, f = True):
                    try:
                        cmds.parent(eachChild, 'MASTER_COREPLACEMENTS_hrc')
                    except RuntimeError:
                        pass
            except:
                pass #no children to parent
        
        ## Now parent valid cores to the root core group
        getAllNameSpaces = cmds.namespaceInfo(listOnlyNamespaces = True)
        for eachNS in getAllNameSpaces:
            if '_CORE' in eachNS:
                try:
                    cmds.parent(cmds.listRelatives(cmds.namespaceInfo(eachNS, r = True, dp = True, listNamespace = True)[1], parent = True, f = True), 'MASTER_ROOTCOREARCHIVES_hrc')
                except RuntimeError:
                    pass

        ## Now try to delete any existing core groups from import
        grps = ['ENV_THEHEADS_STATIC_Core_Archives_hrc', 'ENV_MIDDLEHARBOUR_STATIC_Core_Archives_hrc', 'ENV_MIDDLEHARBOUR_EAST_STATIC_Core_Archives_hrc',
                'ENV_WESTHARBOUR_STATIC_Core_Archives_hrc',  'ENV_BIGTOWN_STATIC_Core_Archives_hrc']
        for each in grps:
            try:
                cmds.delete(each)
            except:
                pass
        
        ## now check for a stupid name from import
        for each in cmds.ls(type = 'core_archive'):
            if 'ep000' in each:
                coreName = '_'.join(each.split('_')[2:])
                for eachGeo in cmds.listConnections(each):
                    if cmds.nodeType(eachGeo) != 'expression':
                        cmds.connectAttr('%s.message' % coreName, '%s.miGeoShader' % eachGeo, force = True)
                
        ## Just in case lets make sure we get rid of any dead cores now
        coreLib.cleanupDeadCoreArchives()
          
    def _makeFinalShotBaseCoreGroups(self):
        grps = ['MASTER_COREARCHIVES_hrc', 'MASTER_ROOTCOREARCHIVES_hrc', 'MASTER_COREPLACEMENTS_hrc']
        for each in grps:
            if not cmds.objExists(each):
                cmds.group(n = each, em = True)
        
    def _removeCoreGrps(self, ):
        """
        Exposing function for operator to cleanup after a rebuild
        """
        ## Step one after import
        ## Clean the fucking left over grps first if they exist
        ENVLIST = ['ENV_MIDDLEHARBOUR_STATIC_ABC_STATIC_CACHES_hrc', 'ENV_MIDDLEHARBOUR_EAST_STATIC_ABC_STATIC_CACHES_hrc', 'ENV_WESTHARBOUR_STATIC_ABC_STATIC_CACHES_hrc', 
                    'ENV_THEHEADS_STATIC_ABC_STATIC_CACHES_hrc', 'ENV_BIGTOWN_STATIC_ABC_STATIC_CACHES_hrc']    
        getHRCS = [[eachGrp for eachGrp in cmds.listRelatives(eachENV, children = True, f= True) if 'LND' in eachGrp] for eachENV in ENVLIST if cmds.objExists(eachENV) ]
        for eachList in getHRCS:
            [[cmds.delete(eachChild) for eachChild in cmds.listRelatives(eachHrc, ad = True, f = True) if '_CORE_' in eachChild] for eachHrc in eachList]