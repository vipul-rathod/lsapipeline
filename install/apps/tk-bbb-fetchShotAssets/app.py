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
from functools import partial
from tank import TankError
import sgtk
## Now get the custom tools
if 'T:/software/DoubleBarrel/' not in sys.path:
    sys.path.append('T:/software/DoubleBarrel/')

if 'T:/software/python-api/' not in sys.path:
    sys.path.append('T:/software/python-api/')

if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')

if 'T:/software/lsapipeline/install/apps/tk-submit-mayaplayblast' not in sys.path:
    sys.path.append('T:/software/lsapipeline/install/apps/tk-submit-mayaplayblast')
#from doubleBarrel import DoubleBarrel
# import doubleBarrelWrapper as doubleBarrelWrapper
# #reload(doubleBarrelWrapper)
import ProgressBarUI as pbui
import maya_genericSettings as settings
from debug import debug
#reload(settings)
#reload(pbui)
   
class FetchShotAssets(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the FetchShotAssets application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'FetchShotAssets Loaded...', verbose = False)

    def run_app(self):
        """
        Callback from when the menu is clicked.
        """
        ## Tell the artist to be patient... eg not genY
        inprogressBar = pbui.ProgressBarUI(title = 'Fetching all shot assets:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 5, doingWhat = 'Processing scene info...')
        #self.dbWrap = DoubleBarrel
        #self.sg = doubleBarrelWrapper._getShotgunObject(self.dbWrap, self)
        ## Instantiate the API
        tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        debug(app = self, method = 'run_app', message = 'API instanced...\n%s' % tk, verbose = False)
        debug(app = self, method = 'run_app', message = 'Fetch Shot Assets launched...', verbose = False)

        context = self.context ## To get the step
        debug(app = self, method = 'run_app', message = 'context: %s' % context, verbose = False)
        debug(app = self, method = 'run_app', message = 'context Step...%s' % context.step['name'], verbose = False)
        
        if context.step['name'] == 'Anm' or context.step['name'] == 'Blocking' or context.step['name'] == 'Light':
            
            ## Build an entity type to get some values from.
            entity = self.context.entity    ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
            debug(app = self, method = 'run_app', message = 'entity... %s' % entity, verbose = False)
            
            ## Filter for the matching ID for the shot
            sg_filters = [["id", "is", entity["id"]]]
            debug(app = self, method = 'run_app', message = 'sg_filters... %s' % sg_filters, verbose = False)
            
            ## Build an entity type to get some values from.
            sg_entity_type = self.context.entity["type"]                                                                   ## returns Shot
            debug(app = self, method = 'run_app', message = 'sg_entity_type...\n%s' % sg_entity_type, verbose = False)
            
            ## DATA
            #import time
            #start = time.time()
            data = self.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=['assets'])
            #data = self.dbWrap.find_one(self.sg, sg_entity_type, sg_filters, ['assets'])
            #print 'TIME: %s' % (time.time()-start)
            debug(app = self, method = 'run_app', message = 'Assets...\n%s' % data['assets'], verbose = False)
    
            ## Set the template to the maya publish folder
            maya_assetRootTemplate = tk.templates[self.get_setting('sg_AssetTemplate')]
            debug(app = self, method = 'run_app', message = 'Asset template...\n%s' % maya_assetRootTemplate, verbose = False)
           
            ### NOTE:
            ### ALL CHARS MUST BE RIGGED
            ### ALL PROPS MUST BE RIGGED
            ### ALL BLDS SHOULD BE PUBLISHED TO AN ENV as well as ALL LND
            ### ALL ROOT_HRC GROUPS SHOULD BE CASE SENSITIVE SUCH AS  CHAR_Sydney_hrc

            ## Set model panel to show None before fetch asset
            modelPanels = cmds.getPanel(type = 'modelPanel')
            if modelPanels:
                [cmds.modelEditor(mp, edit = True, allObjects = False) for mp in modelPanels]

            debug(app = self, method = 'run_app', message = 'Looping assets now...', verbose = False)
            for eachAsset in data['assets']:
                ## Turn this into the shotgun friendly name for the fileNames as underscores are not permitted in shotgun filenames for some obscure reason.
                debug(app = self, method = 'run_app', message = 'eachAsset[name]...\n%s' % eachAsset['name'], verbose = False)
    
                inprogressBar.updateProgress(percent = 50, doingWhat = 'Fetching Assets...')
                x = 50
                if 'CHAR' in eachAsset["name"]:
                    x = x + 5
                    inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Char Assets...')
                    self.processAsset(tk = tk, eachAsset = eachAsset, RIG = True, MDL = False, ENV = False, CHAR = True, BLD = False, PROP = False, templateFile = maya_assetRootTemplate)
                elif 'PROP' in eachAsset["name"]:
                    x = x + 5
                    inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Prop Assets...')
                    self.processAsset(tk = tk, eachAsset = eachAsset, RIG = True, MDL = False, ENV = False, CHAR = False, BLD = False, PROP = True, templateFile = maya_assetRootTemplate)
                elif 'ENV' in eachAsset["name"]:
                    x = x + 5
                    inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Env Assets...')
                    self.processAsset(tk = tk, eachAsset = eachAsset, RIG = False, MDL = True, ENV = True, CHAR = False, BLD = False, PROP = False, templateFile = maya_assetRootTemplate)
                elif 'BLD' in eachAsset["name"]:
                    x = x + 5
                    inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Env Assets...')
                    self.processAsset(tk = tk, eachAsset = eachAsset, RIG = True, MDL = False, ENV = False, CHAR = False, BLD = True, PROP = False, templateFile = maya_assetRootTemplate)
                else:
                    debug(app = self, method = 'run_app', message = 'Invalid Asset Type...\n%s' % eachAsset['name'], verbose = False)
                    pass

            ## Set all AD to None
            [cmds.assembly(each, edit = True, active = '') for each in cmds.ls(type = 'assemblyReference')]

            ## Set model panel to show All
            if modelPanels:
                [cmds.modelEditor(mp, edit = True, allObjects = True) for mp in modelPanels]
            
            debug(app = self, method = 'run_app', message = 'Moving on to save working scene...', verbose = False)
            inprogressBar.updateProgress(percent = 75, doingWhat = 'Setting Render Globals...')
            ## Now make sure the scene is set to pal and cm and renderglobals
            settings._setRenderGlobals(animation = True)
            
            ## Now save the working scene
            inprogressBar.updateProgress(percent = 90, doingWhat = 'Saving vers up scene...')
            shotName = entity['name']
            debug(app = self, method = 'run_app', message = 'shotName...\n%s' % shotName, verbose = False)
            
            work_template = tk.templates['shot_work_area_maya']
            debug(app = self, method = 'run_app', message = 'work_template...\n%s' % work_template, verbose = False)
            
            ## context.step['name'] = Blocking
            try:
                debug(app = self, method = 'run_app', message = "Shot: %s" % shotName, verbose = False)
                debug(app = self, method = 'run_app', message = "context.step: %s" % context.step['name'], verbose = False)
                debug(app = self, method = 'run_app', message = 'Trying to fetch pathToWorking now...', verbose = False)
                pathToWorking = r'%s' % tk.paths_from_template(work_template, {"Shot" : shotName, "Step":context.step['name']})[0]
                pathToWorking.replace('\\\\', '\\')
                debug(app = self, method = 'run_app', message = 'pathToWorking...\n%s' % pathToWorking, verbose = False)
            except: ## There are NO working files yet so we have to handle this propelry
                ## This needs to be the root folder and 000 for version up\
                ## we need to find the sequence from the workspaces index0 of this is default 
                getWorkspace = cmds.workspace( listWorkspaces=True )[1] # Result: [u'default', u'I:/lsapipeline/episodes/eptst/eptst_sh060/Blck/work/maya']
                getSequence = getWorkspace.split('/')[4]
                work_path = work_template.apply_fields({'Sequence' : getSequence, 'Shot': shotName, 'Step': context.step['name']})
                debug(app = self, method = 'run_app', message = 'New work_path: %s' % work_path, verbose = False)
                pathToWorking = r"%s" % work_template
                
            ## Scan the folder and find the highest version number
            fileShotName = "".join(shotName.split('_')) or ''
            debug(app = self, method = 'run_app', message = 'fileShotName...\n%s' % fileShotName, verbose = False)
            padding = ''
            debug(app = self, method = 'run_app', message = 'padding...\n%s' % padding, verbose = False)
            versionNumber = ''
            debug(app = self, method = 'run_app', message = 'versionNumber...\n%s' % versionNumber, verbose = False)
            
            if os.path.exists(pathToWorking):
                debug(app = self, method = 'run_app', message = 'Path to working exists...', verbose = False)
                
                getfiles = os.listdir(pathToWorking)
                debug(app = self, method = 'run_app', message = 'getfiles...\n%s' % getfiles, verbose = False)
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
                debug(app = self, method = 'run_app', message = 'finalFiles...\n%s' % finalFiles, verbose = False)
                   
                if finalFiles:
                    highestVersFile = max(finalFiles)
                    debug(app = self, method = 'run_app', message = 'highestVersFile...\n%s' % highestVersFile, verbose = False)
                    versionNumber  = int(highestVersFile.split('.')[1].split('v')[1]) + 1
                    debug(app = self, method = 'run_app', message = 'versionNumber...\n%s' % versionNumber, verbose = False)
                else:
                    versionNumber  =  1
                    debug(app = self, method = 'run_app', message = 'versionNumber...\n%s' % versionNumber, verbose = False)
                
                ## Now pad the version number
                if versionNumber < 10:
                    padding = '00'
                elif versionNumber < 100:
                    padding = '0'
                else:
                    padding = ''
                debug(app = self, method = 'run_app', message = 'padding...\n%s' % padding, verbose = False)
               
                ## Rename the file
                renameTo = '%s.v%s%s' % (fileShotName, padding, versionNumber)
                debug(app = self, method = 'run_app', message = 'renameTo...\n%s' % renameTo, verbose = False)
                ## Now save the file
                cmds.file(rename = renameTo)
                cmds.file(save = True, force = True, type = 'mayaAscii')
                
                cmds.headsUpMessage("Assets retrieved successfully...", time = 1)
                cmds.cycleCheck(e = 0)
                inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
                inprogressBar.close()
            else:
                debug(app = self, method = 'run_app', message = 'Invalid Path to working, skipping save...',  verbose = False)
                inprogressBar.close()
                cmds.headsUpMessage("Scene not saved. This is most likely due to a first time load of blocking/anim fetch...\nUse Shotgun saveAs now...", time = 2)


        else:
            inprogressBar.close()
            cmds.headsUpMessage("Current context is not a valid Shot context. Please make sure you are under a valid shotgun Shot context!", time = 2)

    def processAsset(self, tk, eachAsset, RIG = False, MDL = False, ENV = False, CHAR = False, BLD = False, PROP = False, templateFile = ''):
        """
        Used to fetch most recent asset and either import if (ENV) or reference it(RIG, PROP)
        
        @param tk : tank instance
        @param eachAsset: The tank dict for the Asset returned in data
        @param RIG: If this is a RIG step or not
        @param MDL: If this is a MDL step or not
        @param ENV: If this is a ENV asset or not
        @param CHAR: If this is a CHAR asset or not
        @param PROP: If this is a PROP asset or not
        @param templateFile: the tank template file specified in the shot_step.yml 
        @type eachAsset: DICT
        @type RIG: Boolean
        @type MDL: Boolean
        @type ENV: Boolean
        @type BLD: Boolean
        @type CHAR: Boolean
        @type PROP: Boolean
        @type templateFile: template
        """      
        debug(app = self, method = 'processAsset', message = 'FOUND %s processing now...' % eachAsset["name"], verbose = False)
        if not self.doesAssetAlreadyExistInScene(eachAsset["name"]):
            step = 'MDL'   
            assetType = ''
            if RIG:
                step = 'RIG'
           
            if CHAR:
                assetType = 'CHAR'
            elif BLD:
                assetType = 'BLD'
            elif ENV:
                assetType = 'ENV'
            else:
                assetType = 'PROP'
            
            debug(app = self, method = 'processAsset', message = 'Fetching getAssetFiles now....', verbose = False)
            debug(app = self, method = 'processAsset', message = 'templateFile: %s' % templateFile, verbose = False)
            debug(app = self, method = 'processAsset', message = 'Asset: %s' % eachAsset['name'], verbose = False)
            debug(app = self, method = 'processAsset', message = 'Step: %s' % step, verbose = False)
            
            ## Now get all the versions of the asset
            try:    
                getAssetFiles = tk.paths_from_template(templateFile, {"Asset": "%s" % eachAsset['name'], 'Step' : step})
                debug(app = self, method = 'processAsset', message = 'Asset Files for %s...\n%s' % (eachAsset['name'], getAssetFiles), verbose = False)
            except:
                debug(app = self, method = 'processAsset', message = 'FAILED: getAssetFiles for %s' % eachAsset['name'], verbose = False)
            
            if getAssetFiles != []:
                latestVer =  max(getAssetFiles)
                debug(app = self, method = 'processAsset', message = 'Lastest Publish Ver Num...\n%s' % latestVer, verbose = False)
                
                ## Namespace here is to try to match this line from the maya_add_rig_to_scene hook
                ## 56             namespace = getEntity['name']
                namespace   = eachAsset["name"]
                assetName   = '%s_hrc' % eachAsset["name"]
                nsAssetName = '%s:%s' % (namespace, assetName)
                debug(app = self, method = 'processAsset', message = 'namespace...\n%s' % namespace, verbose = False)
                debug(app = self, method = 'processAsset', message = 'assetName...\n%s' % assetName, verbose = False)
                debug(app = self, method = 'processAsset', message = 'nsAssetName...\n%s' % nsAssetName, verbose = False)

                ## Check for existing assetType_hrc group adding an S at the end to indicate pural..
                if not cmds.objExists('%sS_hrc' % assetType):
                        TYPEGrp = cmds.group(n = '%sS_hrc' % assetType, em = True)
                        debug(app = self, method = 'processAsset', message = 'Built %s Group' % assetType, verbose = False)
                else:
                    TYPEGrp = '%sS_hrc' % assetType
                
                ## Reference the latest RIG file now
                if CHAR or PROP or BLD:
                    ### RIG REFERENCE
                    myFile = cmds.file(latestVer, r = True, loadReferenceDepth = "all", options = 'v=0', ns = namespace, f = True)
                    for grp in cmds.ls(assemblies=True, long= True):
                        if namespace in grp:
                            cmds.parent(grp, '%sS_hrc' % assetType)
                else:
                    ### ENV IMPORTER
                    ## Check for anim gpu world here
                    if 'ENVWORLDMAPANIM' not in latestVer:
                        cmds.file(latestVer, i =True, gr = True, gn = '%s_hrc' % eachAsset["name"])
                        for eachNode in cmds.ls(ap= True):
                            if ':' in eachNode:
                                try:
                                    cmds.rename(eachNode, '%s' % eachNode.split(':')[-1])
                                except RuntimeError:
                                    pass
                    else:
                        cmds.file(latestVer, r =True, pr = True)                    
                    try:
                        cmds.parent('%s_hrc' % eachAsset["name"], '%sS_hrc' % assetType)
                    except:
                        try:
                            cmds.parent(nsAssetName, '%sS_hrc' % assetType)
                        except:
                            pass
            else:
                cmds.warning('FAILED: To find published files for %s' % eachAsset['name'])
        else:
            cmds.warning('Asset %s already exists in the scene skipping...this may be due to a dirty scene...' % eachAsset['name'])

    def doesAssetAlreadyExistInScene(self, assetName):
        debug(app = self, method = 'doesAssetAlreadyExistInScene', message = 'assetName...\n%s' % assetName, verbose = False)
        assetExists = False
        for each in cmds.ls(type = 'transform'):
            if assetName in each:
                assetExists = True
        return assetExists

    def destroy_app(self):
        self.log_debug("Destroying sg_fetchMayaCamera")