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
Hook that loads animation shot into the current FX scene. 

This hook supports a number of different platforms and the behaviour on each platform is
different. See code comments for details.


"""
import tank, os, sgtk, sys
## Custom stuff
import maya.mel as mel
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
if 'T:/software/bubblebathbay/install/apps/tk-bbb-mayaOcean' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/install/apps/tk-bbb-mayaOcean')
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
#reload(cleanup)

class AddFileToScene(tank.Hook):
    
    def execute(self, engine_name, file_path, shotgun_data, **kwargs):
        """
        Hook entry point and app-specific code dispatcher
        """
                
        if engine_name == "tk-maya":
            self.add_file_to_maya(file_path, shotgun_data)

        else:
            raise Exception("Don't know how to load file into unknown engine %s" % engine_name)
        
    ###############################################################################################
    # app specific implementations
    
    def add_file_to_maya(self, file_path, shotgun_data):
        """
        Load file into Maya.
        
        This implementation creates a standard maya reference file for any item.
        """
        
        import pymel.core as pm
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = file_path.replace(os.path.sep, "/")
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
            tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
            getEntity = shotgun_data['entity']
            shotName = getEntity['name']
            work_template = tk.templates['shot_work_area_maya']
            pathToWorking = r'%s' % tk.paths_from_template(work_template, {"Shot" : shotName, "Step":'FX'})[0]
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
