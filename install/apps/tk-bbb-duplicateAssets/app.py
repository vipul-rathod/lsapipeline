"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
I am a dead change
"""
import os, getpass, sys, shutil, sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError

## Custom stuff
if 'T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean' not in sys.path:
    sys.path.append('T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean')
    
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')

import maya_asset_MASTERCLEANUPCODE as cleanup
import oceanBuilder as oceanBuilder
from debug import debug
import connectOceanHeights as connOH
import boat_FX as bfx
import utils as utils
import fluids_lib as fluidLib
import ProgressBarUI as pbui
import CONST as CONST
import maya_genericSettings as settings
import nParticleSetup as npart
from icon import Icon as Icon
#reload(fluidLib)
#reload(utils)
#reload(bfx)
#reload(connOH)
#reload(oceanBuilder)
#reload(CONST)
#reload(settings)
#reload(npart)

CHARSGRP = 'CHARS_hrc'
PROPSGRP = 'PROPS_hrc'

class DuplicateShotAssets(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the OceanGenerator application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'DuplicateShotAssets Loaded...', verbose = False)

    def run_app(self):
        debug(self, method = 'run_app', message = 'DuplicateShotAssets...', verbose = False)
        getDisplayName = self.get_setting('display_name')
        self.engine.show_dialog(getDisplayName, self, MainUI, self)

class ShowItem(QtGui.QWidget):
    def __init__(self, name = '', color = '', parent = None):
        """
        main UI for DuplicateShotAssets
        """
        QtGui.QWidget.__init__(self, parent)       
        self.itemName = name
        self.mainLayout = QtGui.QGridLayout(self)
        self.assetName = QtGui.QLabel(self.itemName)

        self.radioBox = QtGui.QRadioButton()
        self.radioBox.setChecked(False)
        self.radioBox.setText('Duplicate Asset?')

        self.duplicateNumber = QtGui.QSpinBox()
        self.duplicateNumber.setRange(0, 100)
        self.duplicateNumber.setValue(0)
        self.duplicateNumber.setMinimumWidth(15)

        self.mainLayout.addWidget(self.assetName, 0, 0)
        self.mainLayout.addWidget(self.radioBox, 0, 1)
        self.mainLayout.addWidget(self.duplicateNumber, 0, 2)
        self.mainLayout.setColumnStretch(0, 3)
        self.setStyleSheet("QWidget{background-color: #%s;}" % color)

    def duplicateMe(self):
        return self.radioBox.isChecked()

    def numDuplicates(self):
        return self.duplicateNumber.value()
    
    def getAssetName(self):
        return self.assetName.text()

class MainUI(QtGui.QWidget):
    def __init__(self, app):
        """
        main UI for DuplicateShotAssets
        """
        QtGui.QWidget.__init__(self)       
        self.app = app
        self.charMaxChars = 0
        self.propMaxChars = 0
        ## To get the step
        context = self.app.context 
        debug(self.app, method = 'MainUI', message = 'Context Step: %s' % context.step['name'], verbose = False)
        
        self.chars = []
        self.props = []
        
        ## Now build the UI
        self.mainLayout = QtGui.QHBoxLayout(self)
        debug(self.app, method = 'MainUI', message = 'self.mainLayout built...', verbose = False)
        
        ###############
        ## CHARS LAYOUT
        self.charParent = QtGui.QGroupBox(self)
        self.charParent.setTitle('CHARS:')
        #self.charParent.setMinimumWidth(600)
        self.charParentLayout = QtGui.QVBoxLayout(self.charParent)
        
        self.charScrollLayout = QtGui.QScrollArea(self)
        debug(self.app, method = 'MainUI', message = 'self.charScrollLayout built...', verbose = False)
        
        self.charGroupBox = QtGui.QGroupBox(self.charScrollLayout)
        self.charGroupBox.setFlat(True)
        
        self.charScrollLayout.setWidget(self.charGroupBox)
        self.charScrollLayout.setWidgetResizable(True)
        debug(self.app, method = 'MainUI', message = 'self.charGroupBox built...', verbose = False)
        
        self.charLayout = QtGui.QVBoxLayout(self.charGroupBox)
        debug(self.app, method = 'MainUI', message = 'self.charLayout built...', verbose = False)
      
        ###############
        ## PROPS LAYOUT
        self.propParent = QtGui.QGroupBox(self)
        self.propParent.setTitle('PROPS:')
        #self.propParent.setMinimumWidth(600)
        self.propParentLayout = QtGui.QVBoxLayout(self.propParent)
        
        self.propScrollLayout = QtGui.QScrollArea(self)
        debug(self.app, method = 'MainUI', message = 'self.propScrollLayout built...', verbose = False)

        self.propsGroupBox = QtGui.QGroupBox(self.propScrollLayout)
        self.propsGroupBox.setFlat(True)
        
        self.propScrollLayout.setWidget(self.propsGroupBox)
        self.propScrollLayout.setWidgetResizable(True)
        debug(self.app, method = 'MainUI', message = 'self.propsGroupBox built...', verbose = False)
        
        self.propsLayout = QtGui.QVBoxLayout(self.propsGroupBox)
        debug(self.app, method = 'MainUI', message = 'self.propsLayout built...', verbose = False)
        
        ####################
        ## The Button layout
        self.buttonLayout = QtGui.QVBoxLayout(self)
        ## The buttons
        ## The duplicate button
        self.duplicateButton = QtGui.QPushButton(Icon('plus.png'), 'Duplicate Assets', self)
        self.duplicateButton.clicked.connect(self._duplicateAssets)

        ## Add buttons to layout
        self.buttonLayout.addWidget(self.duplicateButton)
        self.buttonLayout.addStretch(1)

        self.charParentLayout.addWidget(self.charScrollLayout)
        self.propParentLayout.addWidget(self.propScrollLayout)
        ## Now do the final layout bits
        self.mainLayout.addWidget(self.charParent)
        self.mainLayout.addWidget(self.propParent)
        self.mainLayout.addLayout(self.buttonLayout)

        debug(self.app, method = 'MainUI', message = 'self.mainLayout addWidgets success...', verbose = False)
        
        self._popChars()
        debug(self.app, method = 'MainUI', message = 'self._popChars()...', verbose = False)
        self._popProps()
        debug(self.app, method = 'MainUI', message = 'self._popProps()...', verbose = False)
        
        if not self.props:
            self.propScrollLayout.hide()
        if not self.chars:
            self.charScrollLayout.hide()
            
        self.charGroupBox.resize(self.charGroupBox.sizeHint())
        self.propsGroupBox.resize(self.propsGroupBox.sizeHint())
        
        debug(self.app, method = 'MainUI', message = 'self.charMaxChars: %s' % self.charMaxChars, verbose = False)
        self.charParent.setMinimumWidth(self.charMaxChars + 500)
        self.propParent.setMinimumWidth(self.propMaxChars + 500)
        self.resize(self.sizeHint())
        
    def _popChars(self):
        """
        Function to populate the chars lists
        """
        ## Look for the CHARS grp if it exists get the children...
        charLen = []
        debug(self.app, method = 'MainUI', message = 'charLen: %s' % charLen, verbose = False)
        bg = True
        if cmds.objExists(CHARSGRP):
            for each in cmds.listRelatives(CHARSGRP, children = True):
                if not cmds.listRelatives(each, shapes = True) and '_hrc' in each:
                    if not cmds.objExists('%s.dupAsset' % each):
                        if bg:
                            color = 505050
                        else:
                            color = 383838

                        self.rowItem = ShowItem(name = each, color = color)
                        self.chars.append(self.rowItem)
                        if bg:
                            bg = False
                        else:
                            bg = True
                        ## Now add them to the CHAR Layout
                        self.charLayout.addWidget(self.rowItem)
                        debug(self.app, method = '_popChars', message = 'len(each): %s' % len(each), verbose = False)
                        charLen.append(len(each))

        if charLen:
            debug(self.app, method = '_popChars', message = 'charLen: %s' % max(charLen), verbose = False)
            self.charMaxChars = max(charLen)
        
    def _popProps(self):
        """
        Function to populate the props lists
        """
        propLen = []
        debug(self.app, method = 'MainUI', message = 'propLen: %s' % propLen, verbose = False)
        bg = True
        if cmds.objExists(PROPSGRP):
            for each in cmds.listRelatives(PROPSGRP, children = True):
                if not cmds.listRelatives(each, shapes = True) and '_hrc' in each:
                    if not cmds.objExists('%s.dupAsset' % each):
                        if bg:
                            color = 505050
                        else:
                            color = 383838

                        self.rowItem = ShowItem(name = each, color = color)
                        self.props.append(self.rowItem)
                        if bg:
                            bg = False
                        else:
                            bg = True
                        ## Now add them to the PROP Layout
                        self.propsLayout.addWidget(self.rowItem)
                        debug(self.app, method = '_popProps', message = 'len(each): %s' % len(each), verbose = False)
                        propLen.append(len(each))

        if propLen:
            debug(self.app, method = '_popProps', message = 'propLen: %s' % max(propLen), verbose = False)
            self.propMaxChars = max(propLen)

    def _duplicateAssets(self):
        """
        Method for handling the reference duplicates
        This method finds the base assets file path and creates new references for them using the name space '%s_dup' % each and lets maya handle the numbering.
        """
        self._doDuplicate(self.chars)
        self._doDuplicate(self.props)
        
    def _doDuplicate(self, listOfAssets = []):
        report = {}
        for each in listOfAssets:
            if each.duplicateMe():
                assetName = each.getAssetName()
                isReference = cmds.referenceQuery(assetName, isNodeReferenced = True)
                if isReference:
                    file_path = cmds.referenceQuery(each.getAssetName(), f= True)
                    numDups = each.numDuplicates()
                    if numDups != 0:
                        for x in range(0, numDups):
                            if x < 10:
                                padding = '00'
                            elif x < 100:
                                padding = '0'
                            else:
                                padding = ''  
                            mynewDup = cmds.file(file_path, r = True, loadReferenceDepth = "all", options = 'v=0', ns = '%s_dup' % assetName.split(':')[-1].split('_hrc')[0], f = True)
                            debug(self.app, method = 'MainUI', message = 'mynewDup: %s' % mynewDup, verbose = False)
                            
                            myTopHrcGroup = cmds.referenceQuery(mynewDup, n = True)[0] ## this should return the top hrc group
                            
                            ## Add the dupAsset attr to avoid this being listed in the tool again
                            if cmds.objExists('%s.dupAsset' % myTopHrcGroup):
                                cmds.deleteAttr('%s.dupAsset' % myTopHrcGroup)
                            try:
                                cmds.addAttr(myTopHrcGroup, ln = 'dupAsset', at = 'bool')
                                cmds.setAttr('%s.dupAsset' % myTopHrcGroup, 1)
                            except:
                                pass
                            
                            ## parent the asset to the right groups.
                            if 'CHAR' in myTopHrcGroup:
                                try:
                                    cmds.parent(myTopHrcGroup, 'CHARS_hrc')
                                except:
                                    pass
                            elif 'PROP' in myTopHrcGroup:
                                try:
                                    cmds.parent(myTopHrcGroup, 'PROPS_hrc')
                                except:
                                    pass

                    else:
                        cmds.warning('0 Duplicates set for %s, skipping...' % each.getAssetName())
                report[each.getAssetName()] = 'Duplicated %s times.' % numDups

        if report:
            for key, var in report.items():
                print '%s: \t %s' % (key, var)
