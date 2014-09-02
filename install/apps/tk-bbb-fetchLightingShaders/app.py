"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db
"""
import os, getpass, sys, sgtk
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
import pymel.core as pm
## Now get the custom tools
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import core_archive_lib as coreLib
import maya_genericSettings as settings
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
import ProgressBarUI as pbui
import shader_lib as shd
import CONST as CONST
import uv_readXML as uv_readXML
#reload(coreLib)
#reload(settings)
#reload(pbui)
#reload(cleanup)
#reload(shd)
#reload(CONST)
#reload(uv_readXML)


class FetchLightingShaders(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the FetchLightingShaders application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'FetchLightingShaders Loaded...', verbose = False)

    def run_app(self):
        debug(self, method = 'run_app', message = 'FetchLightingShaders...', verbose = False)
        getDisplayName = self.get_setting('display_name')
        self.engine.show_dialog(getDisplayName, self, MainUI, self)
        
        
class BB_Widget_hr(QtGui.QFrame):
    def __init__(self, parent = None):
        """ Builds a horizontal line for uis to use"""
        QtGui.QFrame.__init__(self, parent)
        self.setFrameShape(QtGui.QFrame.HLine) 
        self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setContentsMargins(0, 0, 0, 0)


class MainUI(QtGui.QWidget):
    def __init__(self, app):
        """
        main UI for the playblast options
        NOTE: This currenlty playblasts directly into the publish folder.. it'd be great to avoid this and do the move of the file on register...
        """
        QtGui.QWidget.__init__(self)
            
        self.app = app   
        self.mcLoaded = False
        
        ## Instantiate the API
        tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        debug(self.app, method = 'MainUI __init__', message = 'API instanced...\n%s' % tk, verbose = False)
        
        debug(self.app, method = 'MainUI __init__', message = 'Checking for valid context...', verbose = False)
        context = self.app.context ## To get the step
        debug(self.app, method = 'run_app', message = 'Context Step...\n%s' % context.step['name'], verbose = False)
        
        # if context.step['name'] != 'Light':
        #     raise tank.TankError("You are not in a valid lighting step!")
        #     cmds.warning("Current context is not a valid Lighting context. Please make sure you are under a valid shotgun Lighting context!")
        #     pass
        # else:
        ## Current step is a valid lighting context step.
        try:
            from mentalcore import mapi
            self.mcLoaded = True
            debug(self.app, method = 'MainUI __init__', message = 'self.mcLoaded True....', verbose = False)
        except:
            raise tank.TankError("Mentalcore can not be loaded :( Please fix this!!")

        self.mainLayout = QtGui.QVBoxLayout(self)
        debug(self.app, method = 'MainUI __init__', message = 'self.mainLayout built successfully....', verbose = False)

        self.fetchOceanShaders = QtGui.QPushButton('Fetch Ocean Shader', self)
        self.fetchOceanShaders.released.connect(partial(shd.oceanAttach, self.app))
        self.fetchOceanShaders.setStyleSheet("QPushButton {text-align: center; background: rgb(153, 204, 255); color: black}")
        debug(self.app, method = 'MainUI __init__', message = 'self.fetchOceanShaders built successfully....', verbose = False)

        self.getAllShaders = QtGui.QPushButton('Fetch All Geometry Shaders', self)
        self.getAllShaders.released.connect(partial(self.fetchAllShaders, tk))
        #self.getAllShaders.setStyleSheet("QPushButton {text-align: center; background: dark gray}")
        debug(self.app, method = 'MainUI __init__', message = 'self.getAllShaders built successfully....', verbose = False)

        self.sep01 = BB_Widget_hr()
        debug(self.app, method = 'MainUI __init__', message = 'self.sep01 built successfully....', verbose = False)

        self.getSelShaders = QtGui.QPushButton('Fetch Shaders for Selected Only', self)
        self.getSelShaders.released.connect(partial(self.fetchShadersForSelected, tk))
        self.getSelShaders.setStyleSheet("QPushButton {text-align: center; background: gray}")
        debug(self.app, method = 'MainUI __init__', message = 'self.getSelShaders built successfully....', verbose = False)

        self.mainLayout.addWidget(self.fetchOceanShaders)
        self.mainLayout.addWidget(self.getAllShaders)
        self.mainLayout.addWidget(self.sep01)
        self.mainLayout.addWidget(self.getSelShaders)
        self.mainLayout.addStretch(1)
        self.resize(50,120)

        ## Now just do a delete for any imagePlanes on load
        cleanup.delAllImagePlanes()

    def fetchShadersForSelected(self, tk):
        """
        Function to handle fetching the shaders for selected _hrc groups only.
        """
        inprogressBar = pbui.ProgressBarUI(title = 'Building Shaders For Selected Assets:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 5, doingWhat = 'Processing scene info...')      
        if self.mcLoaded:
            ## ASSSIGN DEFAULT LAMBERT AND CLEAN THE HYERPSHADE!
            for each in cmds.ls(sl = True):
                try:
                    cmds.sets(each, e = True , forceElement = 'initialShadingGroup')
                except:
                    cmds.warning('FAILED to set initial Shading group for %s' % each)
                    pass
            [cmds.lockNode(cp, lock = True) for cp in cmds.ls(type = 'core_renderpass')] ## Lock all the core_renderpasses before deleting unused to preserve...
            mel.eval("MLdeleteUnused();")
            
            scene_path = '%s' % os.path.abspath(cmds.file(query=True, sn= True))
            debug(self.app, method = 'fetchShadersForSelected', message = 'scene_path... %s' % scene_path, verbose = False)
            
            ## Build an entity type to get some values from.
            entity = self.app.context.entity                                                                                    ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
            debug(self.app, method = 'fetchShadersForSelected', message = 'entity... %s' % entity, verbose = False)
                        
            ## Filter for the matching ID for the shot
            sg_filters = [["id", "is", entity["id"]]]
            debug(self.app, method = 'fetchShadersForSelected', message = 'sg_filters... %s' % sg_filters, verbose = False)
            
            ## Build an entity type to get some values from.
            sg_entity_type = self.app.context.entity["type"]                                                                   ## returns Shot
            debug(self.app, method = 'fetchShadersForSelected', message = 'sg_entity_type...\n%s' % sg_entity_type, verbose = False)
            
            ## DATA
            ## NOTES SO HERE WE DON'T NEED TO CALL THE ASSETS FIELD FROM SHOTGUN
            ## WE CAN JUST GRAB THE LATEST PUBLISH FILE FROM EACH OF THE TEMPLATE STEPS
            inprogressBar.updateProgress(percent = 10, doingWhat = 'Processing scene info...')
            shadersTemplate = tk.templates[self.app.get_setting('maya_asset_SHD_XML_template')]
            debug(self.app, method = 'fetchShadersForSelected', message = 'shadersTemplate...\n%s' % shadersTemplate, verbose = False)
            
            texturesTemplate = tk.templates[self.app.get_setting('maya_asset_textures_template')]
            debug(self.app, method = 'fetchShadersForSelected', message = 'texturesTemplate...\n%s' % texturesTemplate, verbose = False)
    
            ## Now get a list of assets in the scene
            inprogressBar.updateProgress(percent = 15, doingWhat = 'Processing assets...')
            inprogressBar.updateProgress(percent = 20, doingWhat = 'Processing xml...')
            assetDict = {} ## key: shotgunName  var: inSceneName
            for grp in cmds.ls(sl= True):
                if cmds.ls(grp, dag=True, type="mesh"):
                    getParent = cmds.listRelatives(grp, parent = True)
                    if getParent:
                        assetDict[grp.split('_hrc')[0]] = [cmds.listRelatives(grp, parent = True)[0], grp]
                    else:
                        assetDict[grp.split('_hrc')[0]] = ['', grp] ##make the parentGroup nothing so it paths to a root asset in the scene correctly

            debug(self.app, method = 'fetchShadersForSelected', message = 'Assets... %s' % assetDict, verbose = False)

            ## Now process XML
            debug(self.app, method = 'fetchShadersForSelected', message = 'Processing template... %s' % shadersTemplate, verbose = False)
            self.processSHDTemplate(tk = tk, templateFile = shadersTemplate, assetDict = assetDict, selected = True)
            
            self.finalBuildStuff(True, inprogressBar)

        else:
            inprogressBar.close()
            cmds.warning("NO MENTAL CORE FOUND!")
            pass
      
    def fetchAllShaders(self, tk):        
        """
        Function to handle fetching the shaders
        """
        inprogressBar = pbui.ProgressBarUI(title = 'Building Shaders for All Assets:')
        inprogressBar.show()
        if self.mcLoaded:
            inprogressBar.updateProgress(percent = 5, doingWhat = 'Processing scene info...')      
            scene_path = '%s' % os.path.abspath(cmds.file(query=True, sn= True))
            debug(self.app, method = 'fetchAllShaders', message = 'scene_path... %s' % scene_path, verbose = False)
            
            ## Build an entity type to get some values from.
            entity = self.app.context.entity                                                                                    ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
            debug(self.app, method = 'fetchAllShaders', message = 'entity... %s' % entity, verbose = False)
                        
            ## Filter for the matching ID for the shot
            sg_filters = [["id", "is", entity["id"]]]
            debug(self.app, method = 'fetchAllShaders', message = 'sg_filters... %s' % sg_filters, verbose = False)
            
            ## Build an entity type to get some values from.
            sg_entity_type = self.app.context.entity["type"]                                                                   ## returns Shot
            debug(self.app, method = 'fetchAllShaders', message = 'sg_entity_type...\n%s' % sg_entity_type, verbose = False)
            
            ## DATA
            ## NOTES SO HERE WE DON'T NEED TO CALL THE ASSETS FIELD FROM SHOTGUN
            ## WE CAN JUST GRAB THE LATEST PUBLISH FILE FROM EACH OF THE TEMPLATE STEPS
            inprogressBar.updateProgress(percent = 10, doingWhat = 'Processing scene info...')
            shadersTemplate = tk.templates[self.app.get_setting('maya_asset_SHD_XML_template')]
            debug(self.app, method = 'fetchAllShaders', message = 'shadersTemplate...\n%s' % shadersTemplate, verbose = False)
            
            texturesTemplate = tk.templates[self.app.get_setting('maya_asset_textures_template')]
            debug(self.app, method = 'fetchAllShaders', message = 'texturesTemplate...\n%s' % texturesTemplate, verbose = False)

            ## Now get a list of assets in the scene
            inprogressBar.updateProgress(percent = 15, doingWhat = 'Processing assets...')
            inprogressBar.updateProgress(percent = 20, doingWhat = 'Processing UV and SHD XML files...')
            assetDict = {} ## key: shotgunName  var: inSceneName
            dupAssets = {}
            for parentGrp in cmds.ls(assemblies = True, long = True):
                if cmds.ls(parentGrp, dag=True, type="mesh"):
                    for each in cmds.listRelatives(parentGrp, children = True):
                        ## Check for duplicate or base assets
                        if not cmds.objExists('%s.dupAsset' % each):
                            assetDict[each.split('_hrc')[0]] = parentGrp
                            #{assetName: parentGrpName}
                        else: # handle the duplicate naming
                            origAssetName = each.split('_hrc')[0]
                            dupAssets[each] = [origAssetName, parentGrp]
                            #{duplicateGrName : [origAssetName, parentGrpName]}
                            debug(self.app, method = 'fetchAllShaders', message = 'DUPLICATE FOUND... origAssetName: %s' % origAssetName, verbose = False)

            debug(self.app, method = 'fetchAllShaders', message = 'Assets... %s' % assetDict, verbose = False)
            debug(self.app, method = 'fetchAllShaders', message = 'Duplicate Assets... %s' % dupAssets, verbose = False)
                                      
            ## Now process SHD XML
            debug(self.app, method = 'fetchAllShaders', message = 'Processing template... %s' % shadersTemplate, verbose = False)
            self.processSHDTemplate(tk = tk, templateFile = shadersTemplate, assetDict = assetDict, selected = False)
            
            self.finalBuildStuff(False, inprogressBar)
        else:
            inprogressBar.close()
            cmds.warning("NO MENTAL CORE FOUND!")

    def finalBuildStuff(self, selected, inprogressBar):
        """
        Generic build stuff both selected and all rebuilds should do
        """
        inprogressBar.updateProgress(percent = 85, doingWhat = 'Shaders Rebuild Complete...')          
        inprogressBar.updateProgress(percent = 90, doingWhat = 'Attaching ocean shaders...')
        ## Exposure now rebuilds in Setup Lighting
        ## Ocean now rebuilds in a separate rebuild ocean button
        # if not selected:
        #     debug(self.app, method = 'finalBuildStuff', message = 'oceanAttach...', verbose = False)
        #     shd.oceanAttach(self.app)
        #
        #     debug(self.app, method = 'finalBuildStuff', message = 'exposure setup...', verbose = False)
        #     shd.buildExposure()

        # inprogressBar.updateProgress(percent = 92, doingWhat = 'Removing duplicate fileIn nodes.....')
        # shd.fixDuplicateFileInNodes()
        
        inprogressBar.updateProgress(percent = 85, doingWhat = 'Removing bump2 fileIn nodes.....')
        shd.replaceBump2WithCoreNormalmap()
        
        inprogressBar.updateProgress(percent = 95, doingWhat = 'Removing unused shaders that were published.....')
        mel.eval("MLdeleteUnused();")
        [cmds.lockNode(cp, lock = False) for cp in cmds.ls(type = 'core_renderpass')] ## Unlock all the core_renderpasses like original after deleting unused to avoid future messed up...

        inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished...')
        inprogressBar.close()
        
    def processSHDTemplate(self, tk, templateFile = '', assetDict = {}, selected = False):
        """
        Used to fetch most recent publishes
        @param tk : tank instance
        @param templateFile: the tank template file specified in the shot_step.yml
        #param assetDict: dict in format assetName, assetParent
        @type templateFile: template
        """
        debug(self.app, method = 'processTemplates', message = 'assetDict:    %s' % assetDict, verbose = False)

        myFinalAssetDict = {}
        
        ## Now fetch all the SRF template paths from shotgun
        getTemplatePaths = tk.paths_from_template(templateFile, {'Step' : 'SRF'})
        #debug(self.app, method = 'processTemplates', message = 'getTemplatePaths: %s' % getTemplatePaths, verbose = False)
        
        ## Now look for each assets template path:        
        for key, var in assetDict.items():
            debug(self.app, method = 'processTemplates', message = 'Processing asset %s now' % key, verbose = False)
            versions = []
            
            for eachPath in getTemplatePaths:
                ### IN scene we get CHAR_Zip_hrc
                ### then we break this back to the publish names that are NOT allowed to have _'s
                ### The publish file names are then CHARZip
                ### BUT a really intelligent Co-Ord decided to make ad asset called CHAR_ZIP_RustryPropeller... that broke the code looking for CharZip as now we have more than one 
                ### So we have to be able to;
                ## Accomodate the following... Char_Zip_hrc  Char_Zip_hrc1 Char_Zip_RustryPropellor_hrc
                
                #'I:\\bubblebathbay\\assets\\CharacterA\\CHAR_Zip_RustyPropeller\\SRF\\publish\\xml\\CHARZip.v001.xml'
                #'I:\\bubblebathbay\\assets\\CharacterA\\CHAR_Zip_RustyPropeller\\SRF\\publish\\xml\\CHARZipRustyPropeller.v001.xml'
                splitPathToAssetName = eachPath.split('\\')[4]
                #debug(self.app, method = 'processTemplates', message = 'splitPathToAssetName: %s' % splitPathToAssetName, verbose = False)
                if key.lower() == splitPathToAssetName.lower():
                    versions.append(eachPath)
            
           # debug(self.app, method = 'processTemplates', message = 'versions.... %s' % versions, verbose = False)

            ## Now if versions has stuff in it..
            if versions:
                if selected:
                    myFinalAssetDict[key] = [max(versions), var[0], var[1]]
                else:
                    myFinalAssetDict[key] = [max(versions), var]
            else:
                debug(self.app, method = 'processTemplates', message = '%s does not have an xml file published.' % key, verbose = False)
                pass
                
        debug(self.app, method = 'processTemplates', message = 'myFinalAssetDict:   %s' % myFinalAssetDict, verbose = False)
        # {u'CHAR_Sydney': ['I:\\bubblebathbay\\assets\\CharacterA\\CHAR_Sydney\\SRF\\publish\\xml\\CHARSydney.v056.xml', u'|ABC_ANIM_CACHES_hrc']}

        allNodes = {}
        for key, var in myFinalAssetDict.items():
            XMLPath = var[0].replace(os.path.sep, "/")
            root = xml.parse(XMLPath).getroot()

            nodes = [each for each in root.getchildren()[0] if each.tag == 'Nodes'][0]
            shadingEngines = [each for each in root.getchildren()[0] if each.tag == 'ShadingEngine'][0]

            for each in nodes.getchildren():
                allNodes.setdefault(each.tag, [])
                allNodes[each.tag].append(key)

            for each in shadingEngines.getchildren():
                sgName = each.attrib['value'].split(',')[0]
                allNodes.setdefault(sgName, [])
                allNodes[sgName].append(key)

        ## Create .txt for modelers as reference
        rebuildShader = 'Continue anyway...'
        shadingDupeCheck = [dupe for dupe in allNodes.itervalues() if len(dupe) > 1]
        if shadingDupeCheck:
            import datetime
            currentDateTime = datetime.datetime.now().strftime("%Y%m%d.%H%M")
            _filePath = 'C:/Temp/shadingNodeNameClash.%s.txt' % currentDateTime
            _file = open(_filePath, 'w')
            for k, v in allNodes.iteritems():
                if len(v) > 1:
                    _file.writelines('%s:\r\n' % k)
                    for dupe in v:
                        _file.writelines('\t%s\r\n' % dupe)
                    _file.writelines('\r\n')
            _file.close()

            ## Give warning to the artist that there's shading node name clashes
            dupeString = 'Shading node name clashes found across multiple assets. Please be advised that this process probably won\'t rebuild 100% as SRF file due to name clashes, a republish of unique shading node name is needed! A Reference .txt of what\'s clashing was compiled at below path.\r\n\r\n'
            #dupeString += _filePath
            #rebuildShader = cmds.confirmDialog(title = 'SHADER REBUILD', message = dupeString, button = ['Continue anyway...', 'Cancel'], defaultButton = 'Continue anyway...', cancelButton = 'Cancel', dismissString = 'Cancel')
            cmds.warning(dupeString)
        #if rebuildShader == 'Continue anyway...':
        for key, var in myFinalAssetDict.items():
            debug(self.app, method = 'processTemplates', message = 'key %s ...' % key, verbose = False)
            debug(self.app, method = 'processTemplates', message = 'var[0] %s ...' % var[0], verbose = False)
            debug(self.app, method = 'processTemplates', message = 'var[1] %s ...' % var[1], verbose = False)

            if os.path.isfile(var[0].replace(os.path.sep, "/")):
                debug(self.app, method = 'processTemplates', message = 'Creating shaders for %s now with path %s ...' % (key, var[0].replace(os.path.sep, "/")), verbose = False)
                debug(self.app, method = 'processTemplates', message = 'parentGrp: %s' % var[1], verbose = False)

                if selected:
                    shd.createAll(XMLPath = var[0].replace(os.path.sep, "/"), parentGrp = var[1], Namespace = '', Root = 'MaterialNodes', selected = True, selectedOrigHrcName = var[2])
                    debug(self.app, method = 'processTemplates', message = 'Connecting shaders for %s now with path %s ...' % (key, var[0].replace(os.path.sep, "/")), verbose = False)
                    versionNumber = var[0].replace(os.path.sep, "/").split('.')[-2].split('v')[-1]
                    shd.connectAll(XMLPath = var[0].replace(os.path.sep, "/"), parentGrp= var[1], Namespace = '', Root = 'MaterialNodes', selected = True, selectedOrigHrcName = var[2], xmlVersionNumber = versionNumber)
                    # ## Now add the version tag to the selected _hrc asset group
                    # versionNumber = var[0].replace(os.path.sep, "/").split('.')[-2].split('v')[-1]
                    # debug(self.app, method = 'processTemplates', message = 'JAMES SHD VERS NUMBER!!!! %s' % versionNumber, verbose = False)
                    # self._addVersionTag(var[2], versionNumber)
                else:
                    shd.createAll(XMLPath = var[0].replace(os.path.sep, "/"), parentGrp = var[1], Namespace = '', Root = 'MaterialNodes')
                    debug(self.app, method = 'processTemplates', message = 'Connecting shaders for %s now with path %s ...' % (key, var[0].replace(os.path.sep, "/")), verbose = False)
                    versionNumber = var[0].replace(os.path.sep, "/").split('.')[-2].split('v')[-1]
                    shd.connectAll(XMLPath = var[0].replace(os.path.sep, "/"), parentGrp= var[1], Namespace = '', Root = 'MaterialNodes', xmlVersionNumber = versionNumber)
            else:
                debug(self.app, method = 'processTemplates', message = 'FAILED: No valid published xml file found for %s ...' % (key, var[0].replace(os.path.sep, "/")), verbose = False)
                pass

    # def _addVersionTag(self, assetName, versionNumber):
    #     if cmds.objExists('%s.SRFversion' % assetName):
    #         cmds.deleteAttr('%s.SRFversion' % assetName)
    #     try:
    #         cmds.addAttr(assetName, ln = 'SRFversion', at = 'long', min = 0, max  = 50000, dv = 0)
    #     except:
    #         pass
    #     cmds.setAttr('%s.SRFversion' % assetName, int(versionNumber))

    def destroy_app(self):
        self.log_debug("Destroying FetchLightingShaders")
