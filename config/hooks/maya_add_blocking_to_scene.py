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
import os, sys
import sgtk

if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
from debug import debug
import utils as utils
import maya_genericSettings as settings
import CONST as CONST
#reload(utils)
#reload(CONST)

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
        
        (path, ext) = os.path.splitext(file_path)
              
        if ext in [".ma", ".mb"]:
            ## Open the blocking file
            cmds.file(file_path, i = True, pr = True, f = True)

            ## Now set the renderglobals for the animation scene
            settings._setCameraDefaults()
            settings._setRenderGlobals()
            settings._createCamGate()
            
            ## Save the blocking file as the next working file in the ANM folder
            tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
            getEntity = shotgun_data['entity']
            shotName = getEntity['name']
            work_template = tk.templates['shot_work_area_maya']
            pathToWorking = r'%s' % tk.paths_from_template(work_template, {"Shot" : shotName, "Step":'ANM'})[0]
            print 'PATHTOWORKING: %s' % pathToWorking
            pathToWorking.replace('\\\\', '\\')
            
            
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
            renameTo = '%s/%s.v%s%s' % (pathToWorking.replace('\\', '/'), fileShotName, padding, versionNumber)
            ## Now rename the file
            cmds.file(rename = renameTo)
            ## Now save this as a working version in the animation working folder
            cmds.file(save = True, force = True, type = 'mayaAscii')
            cmds.workspace(pathToWorking, openWorkspace = True)
        else:
            self.parent.log_error("Unsupported file extension for %s! Nothing will be loaded." % file_path)
