"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db
"""
import os, getpass, sys
import tank.templatekey
import shutil
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
import xml.etree.ElementTree as xml
from xml.etree import ElementTree
from functools import partial
from tank import TankError
import sgtk
import pymel.core as pm
## Now get the custom tools
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import core_archive_lib as coreLib
import maya_genericSettings as settings
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
import ProgressBarUI as pbui
#reload(coreLib)
#reload(settings)
#reload(pbui)
#reload(cleanup)

class RebuildPublishedSurfacing(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the RebuildPublishedSurfacing application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'RebuildPublishedSurfacing Loaded...', verbose = False)

    def run_app(self):
        """
        Callback from when the menu is clicked.
        """
        ## Tell the artist to be patient... eg not genY
        inprogressBar = pbui.ProgressBarUI(title = 'Rebuilding Surfacing Scene From Publish:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 1, doingWhat = 'Processing scene info...')
        ## Instantiate the API
        tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        debug(app = self, method = 'run_app', message = 'API instanced...\n%s' % tk, verbose = False)
        debug(app = self, method = 'run_app', message = 'Fetch Surface Shaders launched...', verbose = False)
        
        context = self.context ## To get the step
        debug(app = self, method = 'run_app', message = 'Context Step...\n%s' % context.step['name'], verbose = False)
        if context.step['name'] != 'Surface':
            cmds.warning("Current context is not a valid Surfacing context. Please make sure you are under a valid shotgun Surfacing context!")
            QtGui.QMessageBox.information(None, "Current context is not a valid Surfacing context. Please make sure you are under a valid shotgun Surfacing context!")
            raise tank.TankError("Current context is not a valid Surfacing context. Please make sure you are under a valid shotgun Surfacing context!")
        
        scene_path = '%s' % os.path.abspath(cmds.file(query=True, sn= True))
        debug(app = self, method = 'run_app', message = 'scene_path... %s' % scene_path, verbose = False)
        
        ## Build an entity type to get some values from.
        entity = self.context.entity                                                                                    ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
        debug(app = self, method = 'run_app', message = 'entity... %s' % entity, verbose = False)
                    
        ## Filter for the matching ID for the shot
        sg_filters = [["id", "is", entity["id"]]]
        debug(app = self, method = 'run_app', message = 'sg_filters... %s' % sg_filters, verbose = False)
        
        ## Build an entity type to get some values from.
        sg_entity_type = self.context.entity["type"]                                                                   ## returns Shot
        debug(app = self, method = 'run_app', message = 'sg_entity_type...\n%s' % sg_entity_type, verbose = False)
        
        ## DATA
        ## NOTES SO HERE WE DON'T NEED TO CALL THE ASSETS FIELD FROM SHOTGUN
        ## WE CAN JUST GRAB THE LATEST PUBLISH FILE FROM EACH OF THE TEMPLATE STEPS
        inprogressBar.updateProgress(percent = 3, doingWhat = 'Processing scene info...')
        shadersTemplate = tk.templates[self.get_setting('maya_asset_SHD_XML_template')]
        debug(app = self, method = 'run_app', message = 'shadersTemplate...\n%s' % shadersTemplate, verbose = False)

        ## PROCESS TEMPLATE NOW
        inprogressBar.updateProgress(percent = 5, doingWhat = 'Processing shaders xml...')                     
        debug(app = self, method = 'run_app', message = 'Processing template... %s' % shadersTemplate, verbose = False)
        ## SHADERS
        self.processTemplates(tk = tk, templateFile = shadersTemplate, id = entity["id"], shotNum = entity["name"], inprogressBar = inprogressBar, lighting = False)
               
        ############################################
        ## CORE ACHIVES        
        ## Now process the assembly References
        debug(app = self, method = 'run_app', message = 'Processing mentalCore assemblies..', verbose = False)
        inprogressBar.updateProgress(percent = 50, doingWhat = 'Processing core archives...')
        if cmds.objExists('CORE_ARCHIVES_hrc') or cmds.objExists('CORE_ARCHIVES_hrc'):
            inprogressBar.updateProgress(percent = 100, doingWhat = 'Complete...')
            inprogressBar.close()
            inprogressBar = None
        else:
            ## Get the assembly paths from the transforms in the scene with the correct tags to load now..
            self.getAssemblyPaths = coreLib.getCorePaths()
            debug(app = self, method = 'run_app', message = 'self.getAssemblyPaths.. %s' % self.getAssemblyPaths, verbose = False)
            
            ## Now load the assemblies from the paths
            coreLib.loadCoreArchives(paths = self.getAssemblyPaths)
            debug(app = self, method = 'run_app', message = 'self.loadCoreArchives Successful all assemblies loaded moving on to reconnect now...', verbose = False)
            inprogressBar.updateProgress(percent = 70, doingWhat = 'Core archives loaded...')
            
            ## Now connect the assemblies.
            inprogressBar.updateProgress(percent = 80, doingWhat = 'Reconnecting core archives...')
            coreLib.doReconnect(postPublish = False)
            debug(app = self, method = 'run_app', message = 'Ahh core archive assemblies reconnected successfully!!...', verbose = False)
           
            ## Now cleanup
            inprogressBar.updateProgress(percent = 90, doingWhat = 'Cleaning...')
            ## Group the placements
            cleanup.shotCleanupPlacements()           
            ## Group the lights
            cleanup.shotCleanupLights()
            ## Put all the coreRebuild under Lighting_hrc group
            coreLib._cleanupCoreArchiveRebuildGrps('LIGHTING_hrc')
        
        
            inprogressBar.updateProgress(percent = 100, doingWhat = 'COMPLETE...')
            inprogressBar.close()
            inprogressBar = None
          
    def processTemplates(self, tk, templateFile = '', id = '', shotNum = '', inprogressBar = ''):
        """
        Used to fetch most recent publishes
        @param tk : tank instance
        @param templateFile: the tank template file specified in the shot_step.yml
        #param assetDict: dict in format assetName, assetParent
        @type templateFile: template
        """
        ## Now fetch all the template paths from shotgun
        getTemplatePaths = tk.paths_from_template(templateFile, {'Step' : 'Light', 'id' : id, 'Shot' : shotNum})
        debug(app = self, method = 'processTemplates', message = 'getTemplatePaths:    %s' % getTemplatePaths, verbose = False)
        
        ## Now look for each assets template path:        
        xmlFile = max(getTemplatePaths)       
        debug(app = self, method = 'processTemplates', message = 'Max Version xmlFile.... %s' % xmlFile, verbose = False)
        
        ## Now if versions has stuff in it..
        if not xmlFile:
            debug(app = self, method = 'processTemplates', message = 'Can not find any xml files for %s' % shotNum, verbose = False)
            pass
        else:
            
            debug(app = self, method = 'processTemplates', message = 'PathTo: %s' % os.path.isfile(xmlFile.replace(os.path.sep, "/")), verbose = False)
            if os.path.isfile(xmlFile.replace(os.path.sep, "/")):## is this a valid xml file!?
                inprogressBar.updateProgress(percent = 10, doingWhat = 'createAll shaders...')
                self._createAllShaders(XMLPath = xmlFile.replace(os.path.sep, "/"), Namespace = '', Root = 'MaterialNodes')
                
                inprogressBar.updateProgress(percent = 30, doingWhat = 'connectAll shaders...')
                self._connectAllShaders(XMLPath = xmlFile.replace(os.path.sep, "/"), Namespace = '', Root = 'MaterialNodes')
            else:
                debug(app = self, method = 'processTemplates', message = 'FAILED Can not find a valid published xml file for %s ...' % os.path.isfile(xmlFile.replace(os.path.sep, "/")), verbose = False)
                pass

    def _createAllShaders(self, XMLPath = '', Namespace = '', Root = 'MaterialNodes', inprogressBar = ''):
        debug(app = self, method = '_createAllShaders', message = 'XMLPath... %s' % XMLPath, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'Namespace... %s' % Namespace, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'Root... %s' % Root, verbose = False)

        # If the namespace doesn't exist, the objects wont get named correctly
        # create the namespace
        if Namespace != "" and Namespace != ":":
            if not cmds.namespace( exists= Namespace[:-1] ):
                cmds.namespace( add = Namespace[:-1])
    
        debug(app = self, method = '_createAllShaders', message = 'Namespace check successful...', verbose = False)
        
        typeShader      = cmds.listNodeTypes( 'shader' ) or []
        typeTexture     = cmds.listNodeTypes( 'texture' )  or []
        typeUtility     = cmds.listNodeTypes( 'utility' )  or []
        typeMRTexture   = cmds.listNodeTypes( 'rendernode/mentalray/texture' )  or []
        typeMRDisp      = cmds.listNodeTypes( 'rendernode/mentalray/displace' )  or []
        typeMREnv       = cmds.listNodeTypes( 'rendernode/mentalray/environment' )  or []
        typeMRLightMaps = cmds.listNodeTypes( 'rendernode/mentalray/lightmap' )  or []
        typeMRMisc      = cmds.listNodeTypes( 'rendernode/mentalray/misc' )  or []
        typeMRConv      = cmds.listNodeTypes( 'rendernode/mentalray/conversion') or []
        typeMRInternal  = cmds.listNodeTypes( 'rendernode/mentalray/internal')  or []

        debug(app = self, method = '_createAllShaders', message = 'typeShader %s' % typeShader, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'typeTexture %s' % typeTexture, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'typeUtility %s' % typeUtility, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'typeMRTexture %s' % typeMRTexture, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'typeMRDisp %s' % typeMRDisp, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'typeMREnv %s' % typeMREnv, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'typeMRLightMaps %s' % typeMRLightMaps, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'typeMRMisc %s' % typeMRMisc, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'typeMRConv %s' % typeMRConv, verbose = False)
        debug(app = self, method = '_createAllShaders', message = 'typeMRInternal %s' % typeMRInternal, verbose = False)

        # get the root of the XMLPath argument
        debug(app = self, method = '_createAllShaders', message = 'XMLPath...%s' % XMLPath, verbose = False)
        root = xml.parse(XMLPath).getroot()
        debug(app = self, method = '_createAllShaders', message = 'Root XML.parse successful...', verbose = False)
        
        # Create an iterator based on the the root argument
        shaderIterator = root.getiterator(Root)
        # Iterate on shader level
        for levelOne in shaderIterator:
            debug(app = self, method = '_createAllShaders', message = 'Entering levelOne in shaderIterator...', verbose = False)
            # Iterate on parent tag level
            if levelOne.getchildren():
                for levelTwo in levelOne:
                    if levelTwo.tag == 'Nodes':
                        debug(app = self, method = '_createAllShaders', message = 'Processing Nodes...', verbose = False)
                        for levelThree in levelTwo.getchildren():
                            node_name = levelThree.tag
                            if '_cCc_' in node_name:
                                node_name = node_name.replace('_cCc_', ':')
                            node_name = '%s%s' % (Namespace, node_name)
                            node_type = levelThree.attrib['value']
                            
                            debug(app = self, method = '_createAllShaders', message = 'Creating all node types and sorting them into correct hypershade tabs...', verbose = False)
                            # Create all node types and sort them into correct hypershade tabs
                            if node_type in typeShader or node_type in typeMRInternal:
                                if not self.doesAssetAlreadyExistInScene(node_name):
                                    cmds.shadingNode(node_type, asShader = True , name = node_name)
                            if node_type in typeTexture or node_type in typeMRInternal:
                                if not self.doesAssetAlreadyExistInScene(node_name):
                                    cmds.shadingNode(node_type, asTexture = True , name = node_name)
                            if node_type in typeUtility or node_type in typeMRTexture or node_type in typeMREnv or node_type in typeMRLightMaps or node_type in typeMRMisc or node_type in typeMRConv or node_type in typeMRDisp or node_type in typeMRInternal:
                                if not self.doesAssetAlreadyExistInScene(node_name):
                                    cmds.shadingNode(node_type, asUtility = True , name = node_name)
    
                    if levelTwo.tag == 'ShadingEngine':
                        debug(app = self, method = '_createAllShaders', message = 'Processing ShadingEngine...', verbose = False)
                        for levelThree in levelTwo.getchildren():
                            node_name  = levelThree.tag
                            if '_cCc_' in node_name:
                                node_name = node_name.replace('_cCc_', ':')
                            node_type  = levelThree.attrib['value']
                            node_split = node_type.split(', ')
                            node_name  = node_split[0]
                            node_name  = Namespace + node_name
                            node_type  = node_split[1]
    
                            if node_type == 'shadingEngine':
                                if not self.doesAssetAlreadyExistInScene(node_name):
                                    cmds.sets(renderable = True, noSurfaceShader = True, empty = True, name = node_name)
        
                    if levelTwo.tag == 'Attributes':
                        debug(app = self, method = '_createAllShaders', message = 'Processing Attributes...', verbose = False)
                        for attributes in levelTwo.getchildren():
                            attrNode = attributes.tag
                            attrNode = Namespace + attrNode
                            if '_aAa_' in attrNode:
                                attrNode = attrNode.replace('_aAa_', '[')
                                attrNode = attrNode.replace('_zZz_', ']')
                            if '_cCc_' in attrNode:
                                attrNode = attrNode.replace('_cCc_', ':')
    
                            attrValue =  attributes.attrib['value']
                            if not attrValue.startswith('[('):
                                try:
                                    cmds.setAttr(attrNode, float(attrValue), lock = False)
                                except:
                                    pass
                                try:
                                    cmds.setAttr(attrNode, str(attrValue), type = 'string', lock = False)
                                except:
                                    pass
                                try:
                                    cmds.setAttr(attrNode, str(attrValue), type = 'double3', lock = False)
                                except:
                                    pass
                        for attributes in levelTwo.getchildren():
                            attrNode = attributes.tag
                            attrNode = Namespace + attrNode
                            if '_aAa_' in attrNode:
                                attrNode = attrNode.replace('_aAa_', '[')
                                attrNode = attrNode.replace('_zZz_', ']')
                            if '_cCc_' in attrNode:
                                attrNode = attrNode.replace('_cCc_', ':')
    
                            attrValue =  attributes.attrib['value']
                            if attrValue.startswith('[('):
                                #convert to list
                                evalList = eval(attrValue)
                                evalList = evalList[0]
                                if len(evalList) == 2:
                                    try:
                                        cmds.setAttr(attrNode, evalList[0], evalList[1], type = 'double2', lock = False)
                                    except:
                                        debug(app = self, method = '_createAllShaders', message = '%s failed..' % attrNode, verbose = False)
    
                                if len(evalList) == 3:
                                    try:
                                        cmds.setAttr(attrNode, evalList[0], evalList[1], evalList[2], type = 'double3', lock = False)
                                    except:
                                        debug(app = self, method = '_createAllShaders', message = '%s failed..' % attrNode, verbose = False)
        
        debug(app = self, method = 'createAll', message = 'FINSHED for %s...' % XMLPath, verbose = False)
    
    def _connectAllShaders(self, XMLPath = '', Namespace = '', Root = 'MaterialNodes'):
        debug(app = self, method = 'connectAll', message = 'XMLPath... %s' % XMLPath, verbose = False)
        debug(app = self, method = 'connectAll', message = 'Namespace... %s' % Namespace, verbose = False)
        debug(app = self, method = 'connectAll', message = 'Root... %s' % Root, verbose = False)

        # If the namespace doesn't exist, the objects wont get named correctly
        # create the namespace
        if Namespace != "" and Namespace != ":":
            if not cmds.namespace( exists= Namespace[:-1] ):
                cmds.namespace( add = Namespace[:-1])
    
        # get the root of the XMLPath argument
        root = xml.parse(XMLPath).getroot()
        debug(app = self, method = 'connectAll', message = 'root XML.parse connected successfully...', verbose = False)
        
        # Create an iterator based on the the root argument
        shaderIterator = root.getiterator(Root)
        # Iterate on shader level
        for levelOne in shaderIterator:
            debug(app = self, method = 'connectAll', message = 'Entering levelOne in shaderIterator...', verbose = False)
            # Iterate on parent tag level
            if levelOne.getchildren():
                for levelTwo in levelOne:
                    # For every node, set each attribute
                    if levelTwo.tag == 'Connections':
                        debug(app = self, method = 'connectAll', message = 'Processing Connections...', verbose = False)
                        for connections in levelTwo.getchildren():                            
                            direction = connections.tag
                            connData = connections.attrib['value'].split(', ')
                            conn_srce = '%s%s' % (Namespace, connData[0])
                            conn_dest = '%s%s' % (Namespace, connData[1])
                            
                            debug(app = self, method = 'connectAll', message = 'Connections: connData: %s' % connData, verbose = False)
                            debug(app = self, method = 'connectAll', message = 'Connections: conn_srce: %s' % conn_srce, verbose = False)
                            debug(app = self, method = 'connectAll', message = 'Connections: conn_dest: %s' % conn_dest, verbose = False)

                            if direction == 'DownStream':
                                try:
                                    cmds.connectAttr(conn_srce, conn_dest, force = True)
                                    debug(app = self, method = 'connectAll', message = 'Connecting %s to %s now..' % (conn_srce, conn_dest), verbose = False)
                                except:
                                    pass
                            else:
                                try:
                                    cmds.connectAttr(conn_dest, conn_srce, force = True)
                                    debug(app = self, method = 'connectAll', message = 'Connecting %s to %s now..' % (conn_dest, conn_srce), verbose = False)
                                except:
                                    pass
    
                    if levelTwo.tag == 'ShadingEngine':
                        debug(app = self, method = 'connectAll', message = 'Processing ShadingEngine...', verbose = False)
                        for sg in levelTwo.getchildren():
                            nodeData  = sg.attrib['value'].split(', ')
                            node_name = '%s%s' % (Namespace, nodeData[0])
                            node_type = nodeData[1]
                            
                            debug(app = self, method = 'connectAll', message = 'ShadingEngine: nodeData: %s' % nodeData, verbose = False)
                            debug(app = self, method = 'connectAll', message = 'ShadingEngine: node_name: %s' % node_name, verbose = False)
                            debug(app = self, method = 'connectAll', message = 'ShadingEngine: node_type: %s' % node_type, verbose = False)
                            
                            if sg.getchildren():
                                debug(app = self, method = 'connectAll', message = 'ShadingEngine: sg.getchildren(): %s' % sg.getchildren(), verbose = False)
                                for geo in sg.getchildren():
                                    if geo.tag == 'Geo':
                                        origName = '|%s' % geo.attrib['value']
                                        debug(app = self, method = 'connectAll', message = 'ShadingEngine: origName: %s' % origName, verbose = False)
                                        try:
                                            cmds.sets(origName, edit=True, forceElement = node_name)
                                        except ValueError:
                                            debug(app = self, method = 'connectAll', message = 'ShadingEngine: Failed Connection %s %s' % (origName, node_name), verbose = False)

#########################LIGHTING RECONNECTION  
    def _createAllLights(self, XMLPath = '', Namespace = '' , Root = ''):
        debug(app = self, method = '_createAllLights', message = '_createAllLights...', verbose = False)
        
        # If the namespace doesn't exist, the objects wont get named correctly create the namespace
        if Namespace != "" and Namespace != ":":
            if not cmds.namespace( exists= Namespace[:-1] ):
                cmds.namespace( add = Namespace[:-1])

        typeShader      = cmds.listNodeTypes( 'shader' ) or []
        typeTexture     = cmds.listNodeTypes( 'texture' ) or []
        typeUtility     = cmds.listNodeTypes( 'utility' ) or []
        typeMRTexture   = cmds.listNodeTypes( 'rendernode/mentalray/texture' ) or []
        typeMRDisp      = cmds.listNodeTypes( 'rendernode/mentalray/displace' ) or []
        typeMREnv       = cmds.listNodeTypes( 'rendernode/mentalray/environment' ) or []
        typeMRLightMaps = cmds.listNodeTypes( 'rendernode/mentalray/lightmap' ) or []
        typeMRMisc      = cmds.listNodeTypes( 'rendernode/mentalray/misc' ) or []
        typeMRConv      = cmds.listNodeTypes( 'rendernode/mentalray/conversion') or []
        typeMRInternal  = cmds.listNodeTypes( 'rendernode/mentalray/internal') or []
        typeMRGeometry  = cmds.listNodeTypes( 'rendernode/mentalray/geometry') or []
    
        typeLights      = cmds.listNodeTypes( 'light' ) or []
        typeMRLights    = cmds.listNodeTypes( 'rendernode/mentalray/light' ) or []
        typeMRLens      = cmds.listNodeTypes( 'rendernode/mentalray/lens' ) or []
    
        debug(app = self, method = '_createAllLights', message = 'Processed lists...', verbose = False)
        # get the root of the XMLPath argument
        root = xml.parse(XMLPath).getroot()
    
        # Create an iterator based on the the root argument
        shaderIterator = root.getiterator(Root)
        # Iterate on shader level
        for levelOne in shaderIterator:
            # Iterate on parent tag level
            if levelOne.getchildren():
                for levelTwo in levelOne:
                    if levelTwo.tag == 'Nodes':
                        debug(app = self, method = '_createAllLights', message = 'Building Nodes...', verbose = False)

                        for levelThree in levelTwo.getchildren():
                            node_name = levelThree.tag
                            debug(app = self, method = '_createAllLights', message = 'node_name:%s' % node_name, verbose = False)

                            if '_cCc_' in node_name:
                                node_name = node_name.replace('_cCc_', ':')
                            node_name = Namespace + node_name
                            node_type = levelThree.attrib['value']
                            debug(app = self, method = '_createAllLights', message = 'node_type:%s' % node_type, verbose = False)
    
                            # Create all node types and sort them into correct hypershade tabs
                            try:
                                if node_type in typeLights or node_type in typeMRLights:
                                    debug(app = self, method = '_createAllLights', message = 'node_type:%s is in typeLights or typeMRLights' % node_type, verbose = False)
                                    if not self.doesAssetAlreadyExistInScene(node_name):
                                        cmds.shadingNode(node_type, asLight = True , name = node_name)
                            except:
                                pass
    
                            try:
                                if node_type in typeTexture or node_type in typeMRTexture:
                                    debug(app = self, method = '_createAllLights', message = 'node_type:%s is in typeTexture or typeMRTexture' % node_type, verbose = False)
                                    if not self.doesAssetAlreadyExistInScene(node_name):
                                        cmds.shadingNode(node_type, asTexture = True , name = node_name)
                            except:
                                pass
    
                            try:
                                if node_type in typeUtility:
                                    debug(app = self, method = '_createAllLights', message = 'node_type:%s is in typeUtility' % node_type, verbose = False)
                                    if not self.doesAssetAlreadyExistInScene(node_name):
                                        cmds.shadingNode(node_type, asUtility = True , name = node_name)
                            except:
                                pass
    
                            try:
                                if node_type in typeMREnv or node_type in typeMRLightMaps or node_type in typeMRMisc or node_type in typeMRConv or node_type in typeMRDisp or node_type in typeMRInternal or node_type in typeMRGeometry or node_type in typeMRLens:
                                    debug(app = self, method = '_createAllLights', message = 'node_type:%s is in typeMREnv, typeMRLightMaps, typeMRMisc, typeMRConv, typeMRDisp, typeMRInternal, typeMRGeometry, typeMRLens' % node_type, verbose = False)
                                    if not self.doesAssetAlreadyExistInScene(node_name):
                                        cmds.createNode( node_type, ss=True, name = node_name)
                            except:
                                pass
    
    
                    if levelTwo.tag == 'Attributes':
                        debug(app = self, method = '_createAllLights', message = 'levelTwo.tag: Assigning Attributes...', verbose = False)

                        for attributes in levelTwo.getchildren():
                            attrNode = attributes.tag
                            attrNode = Namespace + attrNode
                            if '_aAa_' in attrNode:
                                attrNode = attrNode.replace('_aAa_', '[')
                                attrNode = attrNode.replace('_zZz_', ']')
                            if '_cCc_' in attrNode:
                                attrNode = attrNode.replace('_cCc_', ':')
                            if '_tTt_' in attrNode:
                                attrNode = attrNode.replace('_tTt_', '+')
                            if '_mMm_' in attrNode:
                                attrNode = attrNode.replace('_mMm_', '-')
                            attrValue =  attributes.attrib['value']
    
                            if '.illuminatesDefault' in attrNode:
                                if attrValue == '0.0':
                                    lightName = attrNode.split('.')
                                    lightName = lightName[0]
                                    lightParent = cmds.listRelatives(lightName, parent = True)
                                    lightParent = lightParent[0]
                                    for x in range(30):
                                        try:
                                            cmds.disconnectAttr(lightParent + '.instObjGroups[0]','defaultLightSet.dagSetMembers[%i]' %x)
                                        except:
                                            pass
    
    
                            try:
                                cmds.setAttr(attrNode, float(attrValue), lock = False)
                            except:
                                pass
                            try:
                                cmds.setAttr(attrNode, str(attrValue), type = 'string', lock = False)
                            except:
                                pass
                            try:
                                cmds.setAttr(attrNode, str(attrValue), type = 'double3', lock = False)
                            except:
                                pass
    
                    if levelTwo.tag == 'LightLinking':
                        debug(app = self, method = '_createAllLights', message = 'levelTwo.tag: Light Linking Objects...', verbose = False)

                        cmds.select(clear = True)
                        for levelThree in levelTwo.getchildren():
                            set_name = levelThree.tag
                            cmds.select(clear = True)
                            createSet = cmds.sets( name = set_name )
                            LightName = set_name.split('LightLink_')
                            LightName = LightName[1]
                            for levelFour in levelThree.getchildren():
                                objectName = levelFour.tag
                                objectName = objectName.replace('_cCc_', ':')
                                try:
                                    cmds.select(objectName, replace = True)
                                    cmds.sets(objectName, edit = True, addElement = createSet)
                                except:
                                    debug(app = self, method = '_createAllLights', message = 'MISSING OBJECT: %s' % objectName, verbose = False)
#                                     cmds.warning('\nSome objects not present in the scene, cannot light link.\n')
#                                     print '* Missing Object * : \t' + objectName
                                    pass
                            cmds.select(clear = True)
                            cmds.select(LightName, createSet, noExpand = True, replace = True)
                            cmds.lightlink(make = True, useActiveLights = True, useActiveObjects = True)
                            debug(app = self, method = '_createAllLights', message = 'Success light linking something...', verbose = False)
        debug(app = self, method = '_createAllLights', message = 'FINISHED', verbose = False)
    
    def _connectAllLights(self, XMLPath = '', Namespace = '', Root = ''):
        debug(app = self, method = '_connectAllLights', message = '_connectAllLights...', verbose = False)
        # If the namespace doesn't exist, the objects wont get named correctly
        # create the namespace
        if Namespace != "" and Namespace != ":":
            if not cmds.namespace( exists= Namespace[:-1] ):
                cmds.namespace( add = Namespace[:-1])
    
        # get the root of the XMLPath argument
        root = xml.parse(XMLPath).getroot()
    
        # Create an iterator based on the the root argument
        shaderIterator = root.getiterator(Root)
        # Iterate on shader level
        for levelOne in shaderIterator:
            # Iterate on parent tag level
            if levelOne.getchildren():
                for levelTwo in levelOne:
                    # For every node, set each attribute
                    if levelTwo.tag == 'Connections':
                        debug(app = self, method = '_connectAllLights', message = 'levelTwo.tag Creating Node Connections...', verbose = False)

                        for connections in levelTwo.getchildren():
                            direction = connections.tag
                            connData = connections.attrib['value']
                            connSplit = connData.split(', ')
                            conn_srce = connSplit[0]
                            conn_srce = Namespace + conn_srce
                            if '_iIi_' in conn_srce:
                                conn_srce = conn_srce.replace('_iIi_', '-')
                            debug(app = self, method = '_connectAllLights', message = 'levelTwo.tag conn_srce: %s' % conn_srce, verbose = False)
    
                            conn_dest = connSplit[1]
                            conn_dest = Namespace + conn_dest
                            if '_iIi_' in conn_dest:
                                conn_dest = conn_dest.replace('_iIi_', '-')
                            debug(app = self, method = '_connectAllLights', message = 'levelTwo.tag conn_dest: %s' % conn_dest, verbose = False)
                            debug(app = self, method = '_connectAllLights', message = 'levelTwo.tag direction: %s' % direction, verbose = False)
                            if direction == 'DownStream':
                                try:
                                    cmds.connectAttr(conn_srce, conn_dest, force = True)
                                except:
                                    pass
                            else:
                                try:
                                    cmds.connectAttr(conn_dest, conn_srce, force = True)
                                except:
                                    pass
        debug(app = self, method = '_connectAllLights', message = 'FINISHED', verbose = False)
    
    def _lightLinkSets(self):
        debug(app = self, method = '_lightLinkSets', message = 'Light Linking Sets...', verbose = False)

        conn = cmds.listConnections('lightLinker1', connections= True, plugs = True)
        allConn = zip(conn[::2], conn[1::2])
        for each in allConn:
            if 'initialParticleSE' not in each[1] and 'defaultLightSet' not in each[1] and 'initialShadingGroup' not in each[1]:
                cmds.disconnectAttr(each[1],each[0])
    
    
        cmds.select(clear = True)
        allSets = cmds.listSets(allSets= True)
        for each in allSets:
            if each[:10] == 'LightLink_':
                lightName = each[10:]
                lightSet  = each
                cmds.select(lightName, lightSet, replace = True, noExpand = True)
                cmds.lightlink(make =True, useActiveLights = True, useActiveObjects = True)
    
        cmds.select(clear = True)

    def doesAssetAlreadyExistInScene(self, assetName):
        debug(app = self, method = 'doesAssetAlreadyExistInScene', message = 'assetName...\n%s' % assetName, verbose = False)
        assetExists = False
        if cmds.ls(assetName) != []:
            assetExists = True
        
        return assetExists
        
    def destroy_app(self):
        self.log_debug("Destroying sg_fetchMayaCamera")
        
