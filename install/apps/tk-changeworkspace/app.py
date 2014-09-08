"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
"""

import os, getpass, sys
import tank.templatekey
import shutil
import sgtk
from tank import TankError
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial

if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
sys.path.append("T:/software/lsapipeline/install/apps/tk-changeworkspace/")

import maya_genericSettings as settings
from InputPrompt import InputPrompt
from debug import debug


class ChangeWorkSpace(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the PlayBlastGenerator application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'ChangeWorkSpace Loaded...', verbose = False)

    def run_app(self):
        debug(self, method = 'run_app', message = 'ChangeWorkSpace...', verbose = False)
        getDisplayName = self.get_setting('display_name')    
        self.engine.show_dialog(getDisplayName, self, MainUI, self)
    
class MainUI(QtGui.QWidget):
    def __init__(self, app):
        """
        main UI for the playblast options
        NOTE: This currently playblasts directly into the publish folder.. it'd be great to avoid this and do the move of the file on register...
        """
        QtGui.QWidget.__init__(self)
        ## Setup the main UI
        debug(app = None, method = 'MainUI', message= 'Building MainUI', verbose = False)
        debug(app = None, method = 'Main_UI', message = 'INIT ChangeWorkSpace UI', verbose = False)
        self.app = app
        print self.app.context.project
        
        ## Now start the api
        tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        debug(app = self.app, method = 'run_app', message = 'API instanced...\n%s' % tk, verbose = False)

        self.rootFolder = tk.project_path
        debug(app = self.app, method = 'MainUI', message= 'self.rootFolder: %s' % self.rootFolder, verbose = False)
 
        #####
        # Build layouts set widget attrs
        #####
        ## Setup the main base layout for the widget
        self.mainParentLayout = QtGui.QVBoxLayout(self)
        debug(app = self.app, method = 'MainUI', message = 'self.mainParentLayout built.', verbose = False)
        self.typesLayout = QtGui.QHBoxLayout(self)
        debug(app = self.app, method = 'MainUI', message = 'self.typesLayout built.', verbose = False)
        
        self.assetsGroupBox = QtGui.QGroupBox()
        debug(app = self.app, method = 'MainUI', message = 'self.assetsGroupBox built.', verbose = False)
        self.assetsGroupBox.setFlat(True)
        self.assetsGroupBox.setTitle('Asset Type | Name:')
        self.assetsGroupBoxLayout = QtGui.QVBoxLayout(self.assetsGroupBox)
        ## Create a scroll area for the groupBox to go into. Using a groupbox because it inherits from QWidget and you can only 
        ## Add to the scroll area using widgets.
        self.assetsScrollMe = QtGui.QScrollArea(self)
        self.assetsScrollMe.setWidgetResizable(True)
        self.assetsScrollMe.setMinimumWidth(300)
        self.assetsScrollMe.setMinimumHeight(500)
        debug(app = self.app, method = 'MainUI', message = 'self.assetsScrollMe built.', verbose = False)
        
        self.shotsGroupBox = QtGui.QGroupBox()
        debug(app = self.app, method = 'MainUI', message = 'self.shotsGroupBox built.', verbose = False)
        self.shotsGroupBox.setFlat(True)
        self.shotsGroupBox.setTitle('Episode | Shots:')
        self.shotsGroupBoxLayout = QtGui.QVBoxLayout(self.shotsGroupBox)
        ## Create a scroll area for the groupBox to go into. Using a groupbox because it inherits from QWidget and you can only 
        ## Add to the scroll area using widgets.
        self.shotsScrollMe = QtGui.QScrollArea(self)
        self.shotsScrollMe.setWidgetResizable(True)
        self.shotsScrollMe.setMinimumWidth(300)
        self.shotsScrollMe.setMinimumHeight(500)
        debug(app = self.app, method = 'MainUI', message = 'self.shotsScrollMe built.', verbose = False)
        
        ## Now build list viewers and models
        ## ASSETS TREEVIEW
        self.myAssetListView    = QtGui.QTreeView()
        self.myAssetListView.setColumnWidth(0, 200)
        self.myAssetListView.setAlternatingRowColors(True)
        debug(app = self.app, method = 'MainUI', message = 'self.myAssetListView built.', verbose = False)
        self.assetsmodel              = QtGui.QStandardItemModel()
        self.assetsmodel.setHorizontalHeaderLabels(['Name:'])
        debug(app = self.app, method = 'MainUI', message = 'self.assetsmodel built.', verbose = False)
        self.myAssetListView.setModel(self.assetsmodel)
        debug(app = self.app, method = 'MainUI', message = 'self.assetsmodel set to view.', verbose = False)
        ## SHOTS TREEVIEW
        self.myShotListView    = QtGui.QTreeView()
        self.myShotListView.setColumnWidth(0, 200)
        self.myShotListView.setAlternatingRowColors(True)
        debug(app = self.app, method = 'MainUI', message = 'self.myAssetListView built.', verbose = False)
        self.shotmodel              = QtGui.QStandardItemModel()
        self.shotmodel.setHorizontalHeaderLabels(['Name:'])
        debug(app = self.app, method = 'MainUI', message = 'self.assetsmodel built.', verbose = False)
        self.myShotListView.setModel(self.shotmodel)
        debug(app = self.app, method = 'MainUI', message = 'self.assetsmodel set to view.', verbose = False)
        
        ## Now build the types
        assetSteps  = ['MDL', 'RIG', 'SRF']
        shotSteps   = ['Light', 'Anm', 'Blck', 'FX']
        
        self.assetsButtonLayout = QtGui.QHBoxLayout(self)
        self.mdlButton = QtGui.QPushButton('MDL Context')
        self.mdlButton.released.connect(partial(self._setAssetWorkspace, 'MDL'))
        self.rigButton = QtGui.QPushButton('RIG Context')
        self.rigButton.released.connect(partial(self._setAssetWorkspace, 'RIG'))
        self.srfButton = QtGui.QPushButton('SRF Context')
        self.srfButton.released.connect(partial(self._setAssetWorkspace, 'SRF'))
        self.assetsButtonLayout.addWidget(self.mdlButton)
        self.assetsButtonLayout.addWidget(self.rigButton)
        self.assetsButtonLayout.addWidget(self.srfButton)
        
        ## Parent the assetlist view
        self.assetsGroupBoxLayout.addWidget(self.myAssetListView)
        self.assetsGroupBoxLayout.addLayout(self.assetsButtonLayout)

        self.shotsGroupBoxLayout.addWidget(self.myShotListView)
        ## Parent the treeView into the scrollArea
        self.assetsScrollMe.setWidget(self.assetsGroupBox)
        self.shotsScrollMe.setWidget(self.shotsGroupBox)
        debug(app = self.app, method = 'MainUI', message = 'self.assetsScrollMe set widget complete.', verbose = False)
        ## Now parent the groupboxes to the type hbox layout
        self.typesLayout.addWidget(self.assetsScrollMe)
        self.typesLayout.addWidget(self.shotsScrollMe)
        ## Parent the scrollArea to the main VBoxLayout
        self.mainParentLayout.addLayout(self.typesLayout)
        
        debug(app = self.app, method = 'MainUI', message = 'Populating listview...', verbose = False)
        self._addItemsToListView()
        debug(app = self.app, method = 'MainUI', message = 'MainUI built successfully...', verbose = False)
    
    def _getCurrentAssetIndex(self):
        """
        Fetches the name of the currently selected row in the assetView
        Returns name and parent name
        """
        self.selectedRows = self.myAssetListView.selectedIndexes()
        if self.selectedRows:
            self.index = self.selectedRows[0]
            assetName = self.assetsmodel.data(self.index)
            parent = self.assetsmodel.parent(self.index).data()
            return {parent : assetName}
        else:
            cmds.warning('You must have a selected assets before trying to change workspace!')
            return None

    def _setAssetWorkspace(self, step = ''):
        """
        Sets the workspace to the currently selected
        """
        getItems = self._getCurrentAssetIndex()
        if getItems:
            for key, var in getItems.items():
                finalPath = r'%s\assets\%s\%s\%s\work\maya' % (self.rootFolder, key, var, step)
                print finalPath.replace('\\', '/')
                try:
                    cmds.workspace(finalPath.replace('\\', '/'), openWorkspace = True)
                except RuntimeError:
                    cmds.warning('Path does not exist...')
                
    def _isRootFolderThere(self, rootFolder):
        """
        Method used to check if root folder is valid or not
        """
        if not os.path.isdir(rootFolder):
            print 'No such root folder found.'
            return -1
        else:
            return 1
    
    def _findEntities(self, rootFolder = 'I:/bubblebathbay'):
        """
        """
        debug(app = self.app, method = '_findEntities', message= 'Looking for folders...', verbose = False)
        assetTypes = []
        episodes = []
        shotlist = {}
        assetList = {}
        if self._isRootFolderThere(rootFolder = rootFolder):
            subFolders = ['assets', 'episodes']
    
            for eachSubFolder in subFolders:
                if eachSubFolder == 'assets':
                    assetTypes  = [each for each in os.listdir('%s/%s' % (rootFolder, eachSubFolder)) if not '.' in each]
                else:
                    episodes    = [each for each in os.listdir('%s/%s' % (rootFolder, eachSubFolder)) if not '.' in each]
            
            debug(app = self.app, method = '_findEntities', message= 'assetTypes: %s' % assetTypes, verbose = False)
            debug(app = self.app, method = '_findEntities', message= 'episodes: %s' % episodes, verbose = False)
            
            for each in assetTypes:
                for eachAsset in os.listdir('%s/assets/%s' % (rootFolder, each)):
                    assetList[eachAsset]    = each
            for each in episodes:
                for eachShot in os.listdir('%s/episodes/%s' % (rootFolder, each)):
                    shotlist[eachShot]      = each

        debug(app = self.app, method = '_findEntities', message= 'assetList: %s' % assetList, verbose = False)
        debug(app = self.app, method = '_findEntities', message= 'shotlist: %s' % shotlist, verbose = False)

        return assetList, shotlist
        
    def _addItemsToListView(self):
        """
        populate the list view
        """
        debug(app = self.app, method = '_addItemsToListView', message= 'Getting data...', verbose = False)
        
        completedAssetsParents = []
        completedShotParents = []
        debug(app = self.app, method = '_addItemsToListView', message= 'Fetching assets...', verbose = False)
        for key, var in self._findEntities()[0].items():
            if var not in completedAssetsParents:
                parent1 = QtGui.QStandardItem('%s' % var)
                
                ## Now look for all it's children
                for childkey, childvar in self._findEntities()[0].items():
                    if childvar == var:
                        child1 = QtGui.QStandardItem('%s' % childkey)
                        parent1.appendRow([child1])
                self.assetsmodel.appendRow(parent1)
                completedAssetsParents.append(var)
        debug(app = self.app, method = '_addItemsToListView', message= 'Assets Fetched', verbose = False)
        
        debug(app = self.app, method = '_addItemsToListView', message= 'Fetching shots...', verbose = False)
        for key, var in self._findEntities()[1].items():
            if var not in completedShotParents:
                parent1 = QtGui.QStandardItem('%s' % var)
                
                ## Now look for all it's children
                for childkey, childvar in self._findEntities()[1].items():
                    if childvar == var:
                        child1 = QtGui.QStandardItem('%s' % childkey)
                        parent1.appendRow([child1])
                self.shotmodel.appendRow(parent1)
                completedShotParents.append(var)
        debug(app = self.app, method = '_addItemsToListView', message= 'Shots Fetched', verbose = False)
