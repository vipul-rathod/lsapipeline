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
import shader_lib as shd
import maya_genericSettings as settings
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
import ProgressBarUI as pbui
import renderGlobals_readXML as readXML
import light_ReadXML as read_light_xml
#reload(readXML)
#reload(coreLib)
#reload(settings)
#reload(pbui)
#reload(cleanup)
#reload(shd)
#reload(read_light_xml)

class RebuildPublishedLighting(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the RebuildPublishedLighting application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'RebuildPublishedLighting Loaded...', verbose = False)

    def run_app(self):
        """
        Callback from when the menu is clicked.
        """
        ## Tell the artist to be patient... eg not genY
        inprogressBar = pbui.ProgressBarUI(title = 'Rebuilding Lighting Scene:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 1, doingWhat = 'Processing scene info...')
        ## Instantiate the API
        tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        debug(app = self, method = 'run_app', message = 'API instanced...\n%s' % tk, verbose = False)
        debug(app = self, method = 'run_app', message = 'Fetch Lighting Assets launched...', verbose = False)
        
        context = self.context ## To get the step
        debug(app = self, method = 'run_app', message = 'Context Step...\n%s' % context.step['name'], verbose = False)
        if context.step['name'] != 'Light':
            inprogressBar.close()
            cmds.warning("Current context is not a valid Lighting context. Please make sure you are under a valid shotgun Lighting context!")
        
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
        shadersTemplate = tk.templates[self.get_setting('maya_shot_SHD_XML_template')]
        debug(app = self, method = 'run_app', message = 'shadersTemplate...\n%s' % shadersTemplate, verbose = False)

        lightingTemplate = tk.templates[self.get_setting('maya_shot_lighting_template')]
        debug(app = self, method = 'run_app', message = 'lightingTemplate...\n%s' % lightingTemplate, verbose = False)

        renderglobalsTemplate = tk.templates[self.get_setting('maya_shot_renderglobals_template')]
        debug(app = self, method = 'run_app', message = 'renderglobalsTemplate...\n%s' % lightingTemplate, verbose = False)

        ## PROCESS TEMPLATE NOW
        inprogressBar.updateProgress(percent = 5, doingWhat = 'Processing shaders xml...')                     
        debug(app = self, method = 'run_app', message = 'Processing template... %s' % shadersTemplate, verbose = False)
        
        ## SHADERS
        self.processTemplates(tk = tk, templateFile = shadersTemplate, id = entity["id"], shotNum = entity["name"], inprogressBar = inprogressBar, type = 'shaders')
        ## Attach ocean shader now...
        shd.oceanAttach(self)
        
        ## LIGHTS
        inprogressBar.updateProgress(percent = 32, doingWhat = 'Processing lights xml...')       
        self.processTemplates(tk = tk, templateFile = lightingTemplate, id = entity["id"], shotNum = entity["name"], inprogressBar = inprogressBar, type = 'lighting')

        ## Render globals
        inprogressBar.updateProgress(percent = 40, doingWhat = 'Processing renderglobals xml...')       
        self.processTemplates(tk = tk, templateFile = renderglobalsTemplate, id = entity["id"], shotNum = entity["name"], inprogressBar = inprogressBar, type = 'renderglobals')
                
        ## Attach subDiv
        settings.attachMentalRaySubDiv()
        
        ## Now cleanup
        inprogressBar.updateProgress(percent = 90, doingWhat = 'Cleaning...')
        cleanup.shotCleanupLights()
                
        inprogressBar.close()
        inprogressBar = None
        ############################################
        ## CORE ACHIVES        
        ## Now process the assembly References
        debug(app = self, method = 'run_app', message = 'Processing mentalCore assemblies..', verbose = False)
        inprogressBar = pbui.ProgressBarUI(title = 'Rebuilding Core Archives:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 0, doingWhat = 'Processing core archives...')
        if cmds.objExists('CORE_ARCHIVES_hrc') or cmds.objExists('CORE_ARCHIVES_hrc'):
            inprogressBar.updateProgress(percent = 100, doingWhat = 'Complete...')
            inprogressBar.close()
            inprogressBar = None
        else:
            ## Get the assembly paths from the transforms in the scene with the correct tags to load now..
            self.getAssemblyPaths = coreLib.getCorePaths()
            debug(app = self, method = 'run_app', message = 'self.getAssemblyPaths.. %s' % self.getAssemblyPaths, verbose = False)
            
            if self.getAssemblyPaths:
                ## Now load the assemblies from the paths
                coreLib.loadCoreArchives(paths = self.getAssemblyPaths)
                debug(app = self, method = 'run_app', message = 'self.loadCoreArchives Successful all assemblies loaded moving on to reconnect now...', verbose = False)
                inprogressBar.updateProgress(percent = 40, doingWhat = 'Core archives loaded...')
                
                ## Now connect the assemblies.
                inprogressBar.updateProgress(percent = 60, doingWhat = 'Reconnecting core archives...')
                coreLib.doReconnect()
                debug(app = self, method = 'run_app', message = 'Ahh core archive assemblies reconnected successfully!!...', verbose = False)
               
                cleanup.shotCleanupPlacements()
                
                cmds.group(['CORE_ARCHIVES_hrc', 'REBUILT_CORE_ARCHIVES_hrc', 'placements_hrc', 'LIGHTS_hrc'] , n = 'LIGHTING_hrc', em = False)
            else:
                pass
            
            inprogressBar.updateProgress(percent = 100, doingWhat = 'COMPLETE...')
            inprogressBar.close()
            inprogressBar = None
          
    def processTemplates(self, tk, templateFile = '', id = '', shotNum = '', inprogressBar = '', type = ''):
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
            debug(app = self, method = 'processTemplates', message = 'Valid Xml Path?: %s' % os.path.isfile(xmlFile.replace(os.path.sep, "/")), verbose = False)
            
            if os.path.isfile(xmlFile.replace(os.path.sep, "/")):## is this a valid xml file!?
                if type == 'lighting':
                    inprogressBar.updateProgress(percent = 35, doingWhat = 'Rebuilding Lights XML...')
                    debug(app = self, method = 'processTemplates', message = 'Loading Lighting XML NOW...', verbose = False)
                    read_light_xml.actionLightXML(pathToXML = xmlFile.replace(os.path.sep, "/"))
                    
                    debug(app = self, method = 'processTemplates', message = 'Lighting XML Load Complete...', verbose = False)

                elif type == 'shaders':
                    inprogressBar.updateProgress(percent = 20, doingWhat = 'createAll shaders...')

                    shd.createAll(XMLPath = xmlFile.replace(os.path.sep, "/"), parentGrp = '', Namespace = '', Root = 'MaterialNodes')
                    
                    inprogressBar.updateProgress(percent = 30, doingWhat = 'connectAll shaders...')

                    shd.connectAll(XMLPath = xmlFile.replace(os.path.sep, "/"), parentGrp ='', Namespace = '', Root = 'MaterialNodes')
                
                elif type == 'renderglobals':## this render globals
                    inprogressBar.updateProgress(percent = 45, doingWhat = 'recreating renderglobals and render passes now.....')

                    readXML.readCoreData(pathToXML = xmlFile.replace(os.path.sep, "/"))
                    
                    inprogressBar.updateProgress(percent = 50, doingWhat = 'renderglobals and render passes recreated.....')
                else:
                    pass
            else:
                debug(app = self, method = 'processTemplates', message = 'FAILED Can not find a valid published xml file for %s ...' % os.path.isfile(xmlFile.replace(os.path.sep, "/")), verbose = False)
                pass
        
    def doesAssetAlreadyExistInScene(self, assetName):
        debug(app = self, method = 'doesAssetAlreadyExistInScene', message = 'assetName...\n%s' % assetName, verbose = False)
        assetExists = False
        if cmds.ls(assetName) != []:
            assetExists = True
        
        return assetExists
        
    def destroy_app(self):
        self.log_debug("Destroying RebuildPublishedLighting")
        
