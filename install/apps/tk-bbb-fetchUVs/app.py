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
import time
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


class FetchUVs(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the FetchUVs application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'FetchUVs Loaded...', verbose = False)

    def run_app(self):
        debug(self, method = 'run_app', message = 'FetchUVs...', verbose = False)
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
        
        ## Instantiate the API
        tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        debug(self.app, method = 'MainUI __init__', message = 'API instanced...\n%s' % tk, verbose = False)
        
        debug(self.app, method = 'MainUI __init__', message = 'Checking for valid context...', verbose = False)
        context = self.app.context ## To get the step
        debug(self.app, method = 'run_app', message = 'Context Step...\n%s' % context.step['name'], verbose = False)
        
        if context.step['name'] != 'Light':
            raise tank.TankError("You are not in a valid lighting step!")
            cmds.warning("Current context is not a valid Lighting context. Please make sure you are under a valid shotgun Lighting context!")
            pass
        else:           
            self.mainLayout = QtGui.QVBoxLayout(self)
            debug(self.app, method = 'MainUI __init__', message = 'self.mainLayout built successfully....', verbose = False)
            
            self.getAllUVs = QtGui.QPushButton('Step 1: Fetch All Published UV XMLs', self)
            self.getAllUVs.released.connect(partial(self.fetchAllUVs, tk))
            debug(self.app, method = 'MainUI __init__', message = 'self.getAllUVs built successfully....', verbose = False)
            
            self.sep01 = BB_Widget_hr()
            
            self.getSelUVs = QtGui.QPushButton('Fetch UVs for Selected Only', self)
            self.getSelUVs.released.connect(partial(self.fetchUVsForSelected, tk))
            self.getSelUVs.setStyleSheet("QPushButton {text-align: center; background: gray}")
            
            self.mainLayout.addWidget(self.getAllUVs)
            self.mainLayout.addWidget(self.sep01)
            self.mainLayout.addWidget(self.getSelUVs)
            self.mainLayout.addStretch(1)
            self.resize(50,120)

    def fetchUVsForSelected(self, tk):
        """
        Function to handle fetching the shaders for selected _hrc groups only.
        """
        start = time.time()
        inprogressBar = pbui.ProgressBarUI(title = 'Building UVs For Selected Assets:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 5, doingWhat = 'Processing scene info...')      
        
        scene_path = '%s' % os.path.abspath(cmds.file(query=True, sn= True))
        #debug(self.app, method = 'fetchShadersForSelected', message = 'scene_path... %s' % scene_path, verbose = False)
        
        ## Build an entity type to get some values from.
        entity = self.app.context.entity                                                                                    ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
        #debug(self.app, method = 'fetchShadersForSelected', message = 'entity... %s' % entity, verbose = False)
                    
        ## Filter for the matching ID for the shot
        sg_filters = [["id", "is", entity["id"]]]
        #debug(self.app, method = 'fetchShadersForSelected', message = 'sg_filters... %s' % sg_filters, verbose = False)
        
        ## Build an entity type to get some values from.
        sg_entity_type = self.app.context.entity["type"]                                                                   ## returns Shot
        #debug(self.app, method = 'fetchShadersForSelected', message = 'sg_entity_type...\n%s' % sg_entity_type, verbose = False)
        
        ## DATA
        ## NOTES SO HERE WE DON'T NEED TO CALL THE ASSETS FIELD FROM SHOTGUN
        ## WE CAN JUST GRAB THE LATEST PUBLISH FILE FROM EACH OF THE TEMPLATE STEPS
        inprogressBar.updateProgress(percent = 10, doingWhat = 'Processing scene info...')
        uvTemplate = tk.templates[self.app.get_setting('maya_asset_uv_template')]
        #debug(self.app, method = 'fetchShadersForSelected', message = 'uvTemplate...\n%s' % uvTemplate, verbose = False)

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
                    
        #debug(self.app, method = 'fetchShadersForSelected', message = 'Assets... %s' % assetDict, verbose = False)
                       
        ## Do the UV XML first
        #debug(self.app, method = 'fetchShadersForSelected', message = 'Processing uv template... %s' % uvTemplate, verbose = False)
        self.processUVTemplate(tk = tk, templateFile = uvTemplate, assetDict = assetDict, selected = True)                           
        
        inprogressBar.updateProgress(percent = 100, doingWhat = 'UV Rebuild Complete...')
        inprogressBar.close()
        print 'Total UV Rebuild Time: %s' % (time.time()-start)

    def fetchAllUVs(self, tk):        
        """
        Function to handle fetching the uvs for all geo
        """
        start = time.time()
        inprogressBar = pbui.ProgressBarUI(title = 'Rebuilding UVs All Published UV XMLs:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 5, doingWhat = 'Processing scene info...')      
        scene_path = '%s' % os.path.abspath(cmds.file(query=True, sn= True))
        #debug(self.app, method = 'fetchAllUVs', message = 'scene_path... %s' % scene_path, verbose = False)
        
        ## Build an entity type to get some values from.
        entity = self.app.context.entity                                                                                    ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
        #debug(self.app, method = 'fetchAllUVs', message = 'entity... %s' % entity, verbose = False)
                    
        ## Filter for the matching ID for the shot
        sg_filters = [["id", "is", entity["id"]]]
        #debug(self.app, method = 'fetchAllUVs', message = 'sg_filters... %s' % sg_filters, verbose = False)
        
        ## Build an entity type to get some values from.
        sg_entity_type = self.app.context.entity["type"]                                                                   ## returns Shot
        #debug(self.app, method = 'fetchAllUVs', message = 'sg_entity_type...\n%s' % sg_entity_type, verbose = False)
        
        ## DATA
        ## NOTES SO HERE WE DON'T NEED TO CALL THE ASSETS FIELD FROM SHOTGUN
        ## WE CAN JUST GRAB THE LATEST PUBLISH FILE FROM EACH OF THE TEMPLATE STEPS
        inprogressBar.updateProgress(percent = 10, doingWhat = 'Processing scene info...')
        
        uvTemplate = tk.templates[self.app.get_setting('maya_asset_uv_template')]
        #debug(self.app, method = 'fetchAllUVs', message = 'uvTemplate...\n%s' % uvTemplate, verbose = False)

        ## Now get a list of assets in the scene
        inprogressBar.updateProgress(percent = 15, doingWhat = 'Processing assets...')
        assetDict = {} ## key: shotgunName  var: inSceneName
        dupAssets = {}
        for grp in cmds.ls(assemblies = True, long = True):
            if cmds.ls(grp, dag=True, type="mesh"):
                for each in cmds.listRelatives(grp, children = True):
                    ## Check for duplicate or base assets
                    if cmds.objExists('%s.origAsset' % each):
                        origAsset = cmds.getAttr('%s.origAsset' % each)
                    else:
                        assetDict[each.split('_hrc')[0]] = grp
                    
        #debug(self.app, method = 'fetchAllUVs', message = 'Assets... %s' % assetDict, verbose = False)
        inprogressBar.updateProgress(percent = 20, doingWhat = 'processUVTemplate...')
        ## Do the UV XML first
        #debug(self.app, method = 'fetchAllUVs', message = 'Processing uv template... %s' % uvTemplate, verbose = False)
        self.processUVTemplate(tk = tk, templateFile = uvTemplate, assetDict = assetDict)                           
        inprogressBar.updateProgress(percent = 100, doingWhat = 'UV Rebuild Complete...')
        inprogressBar.close()
        print 'Total UV Rebuild Time: %s' % (time.time()-start)

    def processUVTemplate(self, tk, templateFile = '', assetDict = {}, selected = False):
        """
        Used to fetch most recent publishes
        @param tk : tank instance
        @param templateFile: the tank template file specified in the shot_step.yml
        #param assetDict: dict in format assetName, assetParent
        @type templateFile: template
        """
        #debug(self.app, method = 'processTemplates', message = 'assetDict:    %s' % assetDict, verbose = False)
        startTime = time.time()
        myFinalAssetDict = {}
       
        inprogressBar2 = pbui.ProgressBarUI(title = 'processUVTemplate:')
        inprogressBar2.show()
        ## Now fetch all the UV template paths from shotgun
        getTemplatePaths = tk.paths_from_template(templateFile, {'Step' : 'SRF'})
        #debug(self.app, method = 'processTemplates', message = 'getTemplatePaths: %s' % getTemplatePaths, verbose = False)
        
        ## Now look for each assets template path:    
        inprogressBar2.updateProgress(percent = 5, doingWhat = 'Looking up published paths from shotgun...')    
        for key, var in assetDict.items():
            #debug(self.app, method = 'processTemplates', message = 'Processing asset %s now' % key, verbose = False)
            versions = []
            
            for eachPath in getTemplatePaths:
                #'I:\\bubblebathbay\\assets\\CharacterA\\CHAR_Zip_RustyPropeller\\SRF\\publish\\xml\\CHARZipRustyPropeller.v001.xml'
                splitPathToAssetName = eachPath.split('\\')[4]
                #debug(self.app, method = 'processTemplates', message = 'splitPathToAssetName: %s' % splitPathToAssetName, verbose = False)
                if key.lower() == splitPathToAssetName.lower():
                    versions.append(eachPath)
            
            #debug(self.app, method = 'processTemplates', message = 'versions.... %s' % versions, verbose = False)
            
            ## Now if versions has stuff in it..
            if versions:
                if selected:
                    myFinalAssetDict[key] = [max(versions), var]
                else:
                    myFinalAssetDict[key] = [max(versions), var]
            else:
                #debug(self.app, method = 'processTemplates', message = '%s does not have an xml file published.' % key, verbose = False)
                pass
        
        inprogressBar2.updateProgress(percent = 15, doingWhat = 'Beginning UV rebuild...')
        #debug(self.app, method = 'processTemplates', message = 'myFinalAssetDict:   %s' % myFinalAssetDict, verbose = False)
        progress = 15
        getDiv = len(myFinalAssetDict)
        if getDiv:
            step = 100 / len(myFinalAssetDict)
        else:
            step = 1

        for key, var in myFinalAssetDict.items():
            #debug(self.app, method = 'processTemplates', message = 'key %s ...' % key, verbose = False)
            #debug(self.app, method = 'processTemplates', message = 'var[0] %s ...' % var[0], verbose = False)
            #debug(self.app, method = 'processTemplates', message = 'var[1] %s ...' % var[1], verbose = False)
            inprogressBar2.updateProgress(percent = progress + step, doingWhat = 'Rebuilding UVs for %s...' % key)
            if os.path.isfile(var[0].replace(os.path.sep, "/")):
                #debug(self.app, method = 'processTemplates', message = 'Creating uvs for %s now with path %s ...' % (key, var[0].replace(os.path.sep, "/")), verbose = False)
                #debug(self.app, method = 'processTemplates', message = 'parentGrp: %s' % var[1], verbose = False)
                
                if selected:
                    #[u'ABC_ANIM_CACHES_hrc', u'CHAR_jbd_dummyChar_hrc']|CHAR_jbd_dummyChar_hrc|geo_hrc|mainDeck_hrc|hook02_hrc|hook02_hook_geo
                    #print key, var
                    parentGrp = '|%s' % var[1][0]
                    pathToXML = var[0].replace(os.path.sep, "/")
                    uv_readXML.readUVData(pathToUVXML = pathToXML, parentGrp = parentGrp, assignUVS = True)
                    progress = progress + step
                else:                
                    if var[1]:
                        parentGrp = '%s' % var[1] ## note we must set the | at the end to sep the full DAG path properly later on in the readUVs 
                        #debug(self.app, method = 'processTemplates', message = 'parentGrp: %s' % var[1], verbose = False)
                        
                    pathToXML = var[0].replace(os.path.sep, "/")
                    uv_readXML.readUVData(pathToUVXML = pathToXML, parentGrp = parentGrp, assignUVS = True)
                    progress = progress + step
            else:
                #debug(self.app, method = 'processTemplates', message = 'FAILED: No valid published xml file found for %s ...' % (key, var[0].replace(os.path.sep, "/")), verbose = False)
                pass
            print 'Time to rebuild %s: %s' % (key, (time.time()-startTime))
        inprogressBar2.updateProgress(percent = 100, doingWhat = 'UV Rebuild Complete...')
        inprogressBar2.close()
        
    def destroy_app(self):
        self.log_debug("Destroying sg_fetchMayaCamera")
