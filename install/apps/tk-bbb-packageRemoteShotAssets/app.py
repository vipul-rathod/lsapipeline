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
from subprocess import Popen
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

import ProgressBarUI as pbui
import maya_genericSettings as settings
from debug import debug
import CONST as CONST
#reload(settings)
#reload(pbui)
#reload(CONST)
   
class PackageRemoteShotAssets(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the PackageRemoteShotAssets application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'PackageRemoteShotAssets Loaded...', verbose = False)

    def run_app(self):
        """
        Callback from when the menu is clicked.
        """
        ## Tell the artist to be patient... eg not genY
        inprogressBar = pbui.ProgressBarUI(title = 'Archiving all shot assets:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 5, doingWhat = 'Processing scene info...')

        ## Instantiate the API
        tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        debug(app = self, method = 'run_app', message = 'API instanced...\n%s' % tk, verbose = False)
        debug(app = self, method = 'run_app', message = 'Archiving Shot Assets launched...', verbose = False)

        context = self.context ## To get the step
        debug(app = self, method = 'run_app', message = 'context: %s' % context, verbose = False)
        debug(app = self, method = 'run_app', message = 'context Step...%s' % context.step['name'], verbose = False)
        
        if context.step['name'] == 'Anm' or context.step['name'] == 'Blocking':
            
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
            batPath = CONST.BATPATH
            archiveName = r'%s_assets.tar' % entity['name']
            archivePath = '%s/%s' % (batPath.replace('\\', '/'), archiveName)
            
            ## Delete existing archive...
            if os.path.isfile(archivePath):
                try:
                    os.remove(archivePath)
                    debug(app = self, method = 'run_app', message = 'Looping assets now...', verbose = False)
                    for eachAsset in data['assets']:
                        ## Turn this into the shotgun friendly name for the fileNames as underscores are not permitted in shotgun filenames for some obscure reason.
                        debug(app = self, method = 'run_app', message = 'eachAsset[name]...\n%s' % eachAsset['name'], verbose = False)
            
                        inprogressBar.updateProgress(percent = 50, doingWhat = 'Fetching Assets...')
                        x = 50
                        if 'CHAR' in eachAsset["name"]:
                            x = x + 5
                            inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Char Assets...')
                            self.processAsset(tk = tk, eachAsset = eachAsset, RIG = True, MDL = False, ENV = False, CHAR = True, PROP = False, templateFile = maya_assetRootTemplate)
                        elif 'PROP' in eachAsset["name"]:
                            x = x + 5
                            inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Prop Assets...')
                            self.processAsset(tk = tk, eachAsset = eachAsset, RIG = True, MDL = False, ENV = False, CHAR = False, PROP = True, templateFile = maya_assetRootTemplate)                
                        elif 'ENV' in eachAsset["name"]:
                            x = x + 5
                            inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Env Assets...')
                            self.processAsset(tk = tk, eachAsset = eachAsset, RIG = False, MDL = True, ENV = True, CHAR = False, PROP = False, templateFile = maya_assetRootTemplate)
                        else:
                            debug(app = self, method = 'run_app', message = 'Invalid Asset Type...\n%s' % eachAsset['name'], verbose = False)
                            pass
                    
                    debug(app = self, method = 'run_app', message = 'Moving on to save working scene...', verbose = False)
                    cmds.headsUpMessage("Assets archived successfully...", time = 1)
                    inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
                    inprogressBar.close()
                except:
                    inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
                    inprogressBar.close()
                    cmds.warning('Failed to remove existing archive. Do you have it opened??? Close it!')
                    raise tank.TankError("Failed to remove existing archive. Do you have it opened??? Close it!")
                    return - 1
            else:
                debug(app = self, method = 'run_app', message = 'Looping assets now...', verbose = False)
                for eachAsset in data['assets']:
                    ## Turn this into the shotgun friendly name for the fileNames as underscores are not permitted in shotgun filenames for some obscure reason.
                    debug(app = self, method = 'run_app', message = 'eachAsset[name]...\n%s' % eachAsset['name'], verbose = False)
        
                    inprogressBar.updateProgress(percent = 50, doingWhat = 'Fetching Assets...')
                    x = 50
                    if 'CHAR' in eachAsset["name"]:
                        x = x + 5
                        inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Char Assets...')
                        self.processAsset(tk = tk, eachAsset = eachAsset, RIG = True, MDL = False, ENV = False, CHAR = True, PROP = False, templateFile = maya_assetRootTemplate)
                    elif 'PROP' in eachAsset["name"]:
                        x = x + 5
                        inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Prop Assets...')
                        self.processAsset(tk = tk, eachAsset = eachAsset, RIG = True, MDL = False, ENV = False, CHAR = False, PROP = True, templateFile = maya_assetRootTemplate)                
                    elif 'ENV' in eachAsset["name"]:
                        x = x + 5
                        inprogressBar.updateProgress(percent = x, doingWhat = 'Fetching Env Assets...')
                        self.processAsset(tk = tk, eachAsset = eachAsset, RIG = False, MDL = True, ENV = True, CHAR = False, PROP = False, templateFile = maya_assetRootTemplate)
                    else:
                        debug(app = self, method = 'run_app', message = 'Invalid Asset Type...\n%s' % eachAsset['name'], verbose = False)
                        pass
                
                debug(app = self, method = 'run_app', message = 'Moving on to save working scene...', verbose = False)
                cmds.headsUpMessage("Assets archived successfully...", time = 1)
                inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
                inprogressBar.close()
            
        else:
            inprogressBar.close()
            cmds.headsUpMessage("Current context is not a valid Shot context. Please make sure you are under a valid shotgun Shot context!", time = 2)

    def processAsset(self, tk, eachAsset, RIG = False, MDL = False, ENV = False, CHAR = False, PROP = False, templateFile = ''):
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
        @type CHAR: Boolean
        @type PROP: Boolean
        @type templateFile: template
        """      
        debug(app = self, method = 'processAsset', message = 'FOUND %s processing now...' % eachAsset["name"], verbose = False)
        step = 'MDL'   
        assetType = ''
        if RIG:
            step = 'RIG'
       
        if CHAR:
            assetType = 'CHAR'
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
            getENV = tk.paths_from_template(templateFile, {"Asset": "ENV_MIDDLEHARBOUR", 'Step' : 'MDL'})
            debug(app = self, method = 'processAsset', message = 'Asset Files for %s...\n%s' % (eachAsset['name'], getAssetFiles), verbose = False)
            debug(app = self, method = 'processAsset', message = 'Asset Files for MIDDLEHARBOUR: %s' % getENV, verbose = False)
        except:
            debug(app = self, method = 'processAsset', message = 'FAILED: getAssetFiles for %s' % eachAsset['name'], verbose = False)
        
        if getAssetFiles != []:
            entity = self.context.entity    ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
            latestVer =  r'%s' % max(getAssetFiles)
            debug(app = self, method = 'processAsset', message = 'Lastest Publish Ver Num...\n%s' % latestVer, verbose = False)
            
            batPath = CONST.BATPATH
            debug(app = self, method = 'processAsset', message = 'batPath: %s' % batPath, verbose = False)
            
            batFile = CONST.BATFILENAME
            debug(app = self, method = 'processAsset', message = 'batFile: %s' % batFile, verbose = False)
            
            archiveName = r'%s_assets.tar' % entity['name']
            
            if not assetType == 'ENV':    
                debug(app = self, method = 'processAsset', message = 'archiveName: %s' % archiveName, verbose = False)
                
                archiveLine = r"C:\\\"Program Files (x86)\"\GnuWin32\bin\tar -rvf %s %s" % (archiveName, latestVer.replace('\\','/'))
                debug(app = self, method = 'processAsset', message = 'archiveLine: %s' % archiveLine, verbose = False)
                
                ## Now write the bat file out since we can't use tar as a os.system command
                debug(app = self, method = 'processAsset', message = r'NonENV... Writing bat file to: %s/%s' % (batPath.replace('\\', '/'), batFile), verbose = False)
                outfile = open(r'%s/%s' % (batPath.replace('\\', '/'), batFile), "w")
                outfile.write('cd %s\n' % batPath)
                outfile.write('\n')
                outfile.write(archiveLine)
                outfile.close()
    
                debug(app = self, method = 'processAsset', message = 'Popen: %s cwd = %s' % (batFile, batPath.replace('\\', '/')), verbose = False)
                p = Popen(batFile, cwd = batPath.replace('\\', '/'), shell=True)
                debug(app = self, method = 'processAsset', message = 'p made successfully..', verbose = False)
                stdout, stderr = p.communicate()
                
                debug(app = self, method = 'processAsset', message = 'Removing bat file now....', verbose = False)
                os.remove('%s/%s' % (batPath.replace('\\', '/'), batFile))
                
            else:
                ## Now write the bat file out since we can't use tar as a os.system command
                debug(app = self, method = 'processAsset', message = r'ENV... Writing bat file to: %s/%s' % (batPath.replace('\\', '/'), batFile), verbose = False)
                
                archiveLine = r"C:\\\"Program Files (x86)\"\GnuWin32\bin\tar -rvf %s %s" % (archiveName, latestVer.replace('\\','/'))
                debug(app = self, method = 'processAsset', message = r'ENV... archiveLine: %s' % archiveLine, verbose = False)
                          
                ## FIRST process the path to the env file into the tar
                debug(app = self, method = 'processAsset', message = r'ENV... processing base ENV: %s' % latestVer, verbose = False)
                outfile = open(r'%s/%s' % (batPath.replace('\\', '/'), batFile), "w")
                outfile.write('cd %s\n' % batPath)
                outfile.write('\n')
                outfile.write(archiveLine)
                outfile.close()
                ## Now write the core ENV to archive
                debug(app = self, method = 'processAsset', message = 'Popen: %s cwd = %s' % (batFile, batPath.replace('\\', '/')), verbose = False)
                p = Popen(batFile, cwd = batPath.replace('\\', '/'), shell=True)
                debug(app = self, method = 'processAsset', message = 'p made successfully..', verbose = False)
                stdout, stderr = p.communicate()
                
                ## NOW DO THE ASSEMBLY REFERENCES INSIDE THE ENV FILE!!!
                ## Note env files have nested assembly definitions so these need to be found with their versions and paths to each version added to the archive correctly
                renderPath = r'C:\\"Program Files\"\Autodesk\Maya2013.5\bin\Render.exe'
                renderOptions = r'-r hw -s 1 -e 1 -rd'
                renderOuputPath = CONST.RENDERPATH
                preMel = r"python(\"import sys\nsys.path.append('T:/software/lsapipeline/tools')\nimport envWrite\n#reload(envWrite)\nenvWrite.writeSubAssets()\")"
                postMel = r"python(\"import sys\nsys.path.append('T:/software/lsapipeline/tools')\nimport envWrite\n#reload(envWrite)\nenvWrite.quitCMD()\")"
                writeString = '%s %s %s -preRender \"%s\" -postRender \"%s\" %s' % ( renderPath, renderOptions, renderOuputPath, preMel, postMel, latestVer)
                ## Now run the darn thing
                os.system('%s' % writeString)
                
                ## Now read the processed paths and archive those files.
                pathToPaths = CONST.PATHTOPATHSTEXTFILE
                readFile = open(pathToPaths, "r").readlines()
                for line in readFile:
                    archiveLine = r"C:\\\"Program Files (x86)\"\GnuWin32\bin\tar -rvf %s %s" % (archiveName, line.replace('\\','/'))
                    ## Now write the bat file out since we can't use tar as a os.system command
                    debug(app = self, method = 'processAsset', message = r'Writing bat file to: %s\%s' % (batPath, batFile), verbose = False)
                    outfile = open(r'%s/%s' % (batPath.replace('\\', '/'), batFile), "w")
                    outfile.write('cd %s\n' % batPath)
                    outfile.write('\n')
                    outfile.write(archiveLine)
                    outfile.close()
                    ## Now run the bat file from python
                    debug(app = self, method = 'processAsset', message = 'Popen: %s cwd = %s' % (batFile, batPath.replace('\\', '/')), verbose = False)
                    p = Popen(batFile, cwd = batPath.replace('\\', '/'), shell=True)
                    debug(app = self, method = 'processAsset', message = 'p made successfully..', verbose = False)
                    stdout, stderr = p.communicate()
                
                debug(app = self, method = 'processAsset', message = 'Removing bat file now....', verbose = False)
                os.remove('%s/%s' % (batPath.replace('\\', '/'), batFile))
                
                debug(app = self, method = 'processAsset', message = 'Removing paths file now....', verbose = False)
                os.remove(pathToPaths)

                debug(app = self, method = 'processAsset', message = 'Removing %s.iff.1' % latestVer.split('\\')[-1].split('.mb')[0], verbose = False)
                os.remove('%s/%s.iff.1' % (CONST.RENDERPATH.replace('\\', '/'), latestVer.split('\\')[-1].split('.mb')[0]))
        else:
            cmds.warning('FAILED: To find published files for %s' % eachAsset['name'])

    def destroy_app(self):
        self.log_debug("Destroying archive application")
