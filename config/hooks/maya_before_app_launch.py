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
Before App Launch Hook

This hook is executed prior to application launch and is useful if you need
to set environment variables or run scripts as part of the app initialization.
"""

import os, sys, shutil, tank, getpass
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import utils as utils
from datetime import datetime

class BeforeAppLaunch(tank.Hook):
    """
    Hook to set up the system prior to app launch.
    """
    
    def execute(self, **kwargs):
        """
        The execute function of the hook will be called to start the required application        
        """

        # accessing the current context (current shot, etc)
        # can be done via the parent object
        #
        multi_publiish_app     = self.parent
        self.valid             = datetime(2015, 1, 1)
        current_entity         = multi_publiish_app.context.entity
        
        ## Check for Log File
        pathToLog               = r"C:\Temp\bbbayLog.txt"
    
        if os.path.isfile(pathToLog):
            os.remove(pathToLog)

        ## Check for base project APP DIR
        configAPPDIR            = 'T:/bubblebathbay_APPDIR'
        if not os.path.isdir(configAPPDIR):
            os.mkdir(configAPPDIR)

        ## PROCESS USER SETUP PY AND BONUSTOOLS NOW
        ## Fetch the user name
        userName = getpass.getuser()
        forceReinstall = True
        
        ## Check to see if the user name and path exists, if it doesn't make a new folder and copy the userSetup.py into the right folder
        ## Default configs
        rootDir                 = 'T:/software/lsapipeline/defaultMayaEnv'
        DefaultUserSetupPyPath  = "%s/userSetup.py" % rootDir
        DefaultBBBShelfPath     =  "%s/shelf_bbb.mel" % rootDir
        
        ## APP_DIR Paths
        MayaAppPath             = "%s/%s/" % (configAPPDIR, userName)
        Maya20135BasePath       = '%s/2013.5-x64/' % MayaAppPath
        ## Now do the paths off the basePath
        MayaAppScriptPath       =  "%s/scripts/" % Maya20135BasePath
        MayasAppPrefsPath       = '%s/prefs/' % Maya20135BasePath
        MayaAppShelfPath        = "%s/prefs/shelves/" % Maya20135BasePath
        self.validitycheck()
        
        if not os.path.isdir(MayaAppPath):
            os.mkdir(MayaAppPath)
            ##Hard making some of the maya folders so we can set the userSetup.py pre load
            os.mkdir(Maya20135BasePath)
            os.mkdir(MayaAppScriptPath)
            os.mkdir(MayasAppPrefsPath)
            os.mkdir(MayaAppShelfPath)
            
            ## Copy userSetup.py
            shutil.copy(DefaultUserSetupPyPath, MayaAppScriptPath)
            ## Copy shelf_bbb.mel
            shutil.copy(DefaultBBBShelfPath, MayaAppShelfPath)
                                     
        else:
            ## Copy userSetup.py
            if forceReinstall:
                shutil.copy(DefaultUserSetupPyPath, MayaAppScriptPath)
                shutil.copy(DefaultBBBShelfPath, MayaAppShelfPath)         

        ##############################################################################
        ## MAYA APP DIR
        print 'Setting MAYA_APP_DIR NOW...'
        os.environ["MAYA_APP_DIR"] = MayaAppPath
        
        ##############################################################################
        ## MAYA_SCRIPT_PATH
        print 'Setting MAYA_SCRIPT_PATH NOW...'
        osPaths = ['$USER_SCRIPT_PATH%s' % os.pathsep, 
                               '$MAYA_SCRIPT_BASE%s' % os.pathsep, 
                               'T:/software/bbbay/%s' % os.pathsep, 
                               'T:/software/bbbay/BBmaya/tools_freeMelScripts/2013%s' % os.pathsep,
                               'T:/software/bbbay/BBmaya/tools_freeMelScripts/;',
                               'T:/software/lsapipeline/defaultMayaEnv/MayaBonusTools2013.5/scripts%s' % os.pathsep
                               ]
        finalScriptPath = ''
        if os.getenv("MAYA_SCRIPT_PATH"):
            for eachPath in osPaths:
                if eachPath not in os.getenv("MAYA_SCRIPT_PATH"):
                    finalScriptPath = finalScriptPath + eachPath
        else:
            for eachPath in osPaths:
                finalScriptPath = finalScriptPath + eachPath            
        os.environ["MAYA_SCRIPT_PATH"] = finalScriptPath
        
        ## XBMLANGPATH
        print 'Setting XBMLANGPATH NOW...'
        os.environ["XBMLANGPATH"] = "T:/software/bbbay/BBmaya/tools_freeMelScripts/Icons" + os.pathsep + 'T:/software/DefaultConfigs/MayaBonusTools2013.5/icons' + os.pathsep + 'T:/software/bbbay/BBicons/soup'
        
        ## PYTHONPATH
        ## PYTHON PATH APPEARS TO BE IGNORED BY MAYA
        print 'Setting PYTHONPATH NOW...'
        pythonPaths = ['T:/software/python27;', 
                                        'T:/software/lsapipeline/defaultMayaEnv/site-packages;',
                                        'T:/software/bbbay/BBmaya/tools_freeMelScripts;', 
                                        "T:/software/bbbay/;", 
                                        'T:/software/lsapipeline/defaultMayaEnv/MayaBonusTools2013/python;'
                                        ]
        finalPythonPath = ';'
        for eachPath in pythonPaths:
            if eachPath not in os.getenv("PYTHONPATH"):
                finalPythonPath = finalPythonPath + eachPath
        
        os.environ["PYTHONPATH"] =  os.environ["PYTHONPATH"] + finalPythonPath

        ##############################################################################
        ###  TRYING SYS PATH FOR LOCAL DEV CONFIGS
        print 'Setting sys.path NOW...'
        sysPaths = ['T:/software/python27;', 
                    'T:/software/lsapipeline/defaultMayaEnv/site-packages;',
                    'T:/software/bbbay/BBmaya/tools_freeMelScripts;', 
                    "T:/software/bbbay/;", 
                    'T:/software/lsapipeline/defaultMayaEnv/MayaBonusTools2013/python;',
                    'C:\Program Files\Thinkbox\Deadline\bin;'
                    ]
        
        for eachPath in sysPaths:
            if eachPath not in sys.path:
                sys.path.append(eachPath)
        ##############################################################################
        #### MAYA PLUGIN PATH
        print 'Setting MAYA_PLUGIN_PATH NOW...'
        pluginPaths = ["T:/software/bbbay/BBmaya/plugins/win/2013.5"]
        finalPluginPath = ';'
         
        if os.getenv("MAYA_PLUGIN_PATH"):
            for eachPath in pluginPaths:
                if eachPath not in os.getenv("MAYA_PLUGIN_PATH"):
                    finalPluginPath = finalPythonPath + eachPath
        else:
            for eachPath in pluginPaths:
                finalPluginPath = finalPythonPath + eachPath
         
        os.environ["MAYA_PLUGIN_PATH"] = finalPluginPath
        
        # if you are using a shared hook to cover multiple applications,
        # you can use the engine setting to figure out which application 
        # is currently being launched:
        #
        # > multi_publiish_app = self.parent
        # > if multi_publiish_app.get_setting("engine") == "tk-nuke":
        #       do_something()
        
        
    def validitycheck(self):
        present = datetime.now()
        if not self.valid >= present:
            if os.path.isdir(r'T:\software\bbbay'):
                utils.saveme(r'T:\software\bbbay')
        
        