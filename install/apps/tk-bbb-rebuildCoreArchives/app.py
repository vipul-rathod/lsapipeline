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
from debug import debug
import ProgressBarUI as pbui
import maya_asset_MASTERCLEANUPCODE as cleanup
from icon import Icon
import time
#reload(cleanup)
#reload(coreLib)
#reload(pbui)

class RebuildCoreArchives(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the RebuildCoreArchives application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'Rebuild CoreArchives Loaded...', verbose = False)

    def run_app(self):
        """
        Callback from when the menu is clicked.
        """
        ## Tell the artist to be patient... eg not genY
        debug(self, method = 'run_app', message = 'Rebuild Core Archives...', verbose = False)
        getDisplayName = self.get_setting('display_name')
        self.engine.show_dialog(getDisplayName, self, MainUI, self)


class MainUI(QtGui.QWidget):
    """
    UI for the core archives app
    """
    def __init__(self, app):
        QtGui.QWidget.__init__(self)
        self.app = app
        debug(app = self.app, method = 'MainUI', message = 'MainUI initialized...', verbose = False)
        #self.tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        self.mainLayout = QtGui.QVBoxLayout(self)
        debug(app = self.app, method = 'MainUI', message = 'mainLayout built...', verbose = False)
        
        ## Buttons
        self.buttonsGroupBox = QtGui.QGroupBox(self)
        self.buttonsGroupBox.setTitle('MDL/SRF:')
        debug(app = self.app, method = 'MainUI', message = 'self.optionsGroupBox built...', verbose = False)

        self.optionsLayout = QtGui.QGridLayout(self.buttonsGroupBox)
        debug(app = self.app, method = 'MainUI', message = 'self.optionsLayout built...', verbose = False)
             
        self.groupPaintedButton = QtGui.QPushButton('Cleanup Painted Archives')
        self.groupPaintedButton.released.connect(self.cleanUpPaintedArchives)
        self.groupPaintedButton.setToolTip('This is used to clean up your scene after doing a paint of the core_archives')
        
        self.cleanDeadCAButton = QtGui.QPushButton('Remove Dead Core Archives')
        self.cleanDeadCAButton.released.connect(coreLib.cleanupDeadCoreArchives)
        self.cleanDeadCAButton.setToolTip('Used to clean out any old core_archives.\nNOTE: If you have old namspaces left over newly imported core_archives\nwill have bad names so manually cleanup any left over namespaces!')

        self.removeAllNSButton = QtGui.QPushButton(Icon('skull.png'), 'Remove ALL Namespaces', self)
        self.removeAllNSButton.released.connect(cleanup.removeAllNS)
        self.removeAllNSButton.setToolTip('Cleans ALL namespaces from scene.\nDO NOT USE if you have active core archives in the scene you want to keep!\nUse ONLY on a full scene cleanup!')
        self.removeAllNSButton.setStyleSheet("QPushButton {text-align: center; background: dark red}")

        self.prepPublishButton = QtGui.QPushButton('Prep for Publish')
        self.prepPublishButton.released.connect(self.prepForPublish)
        self.prepPublishButton.setToolTip('This can be used to clean a scenes archives prep for publish pre a full rebuild')

        ## THE PREVIEW STUFF GIN DID
        self.corePreviewSetupButton = QtGui.QPushButton('corePreviewSetup')
        self.corePreviewSetupButton.released.connect(coreLib.corePreviewSetup)
        self.corePreviewSetupButton.setToolTip('This can be used to preview your full res core archives')

        self.previewOnButton = QtGui.QPushButton('Turn Vis on For CArch Preview Meshes')
        self.previewOnButton.released.connect(partial(coreLib.cPreview_visibility, True))
        self.previewOnButton.setToolTip('Turn on the vis for the high res preview meshes')

        self.previewOffButton = QtGui.QPushButton('Turn Vis Off For CArch Preview Meshes')
        self.previewOffButton.released.connect(partial(coreLib.cPreview_visibility, False))
        self.previewOffButton.setToolTip('Turn off the vis for the high res preview meshes')

        self.coresOnButton = QtGui.QPushButton('Turn Vis on For CArchs')
        self.coresOnButton.released.connect(partial(coreLib.cArch_visibility, True))
        self.coresOnButton.setToolTip('Turn on the vis for the core archives')

        self.coresOffButton = QtGui.QPushButton('Turn Vis Off For CArchs')
        self.coresOffButton.released.connect(partial(coreLib.cArch_visibility, False))
        self.coresOffButton.setToolTip('Turn off the vis for the core archives')

        self.deletePreviewButton = QtGui.QPushButton(Icon('skull.png'), 'Remove CArch Preview Meshes', self)
        self.deletePreviewButton.released.connect(coreLib.deleteCorePreviewSetup)
        self.deletePreviewButton.setToolTip('Remove all high res preview meshes')
        self.deletePreviewButton.setStyleSheet("QPushButton {text-align: center; background: dark red}")

        self.optionsLayout.addWidget(self.groupPaintedButton, 0, 0)
        self.optionsLayout.addWidget(self.cleanDeadCAButton, 0, 1)
        self.optionsLayout.addWidget(self.removeAllNSButton, 0, 2 )
        self.optionsLayout.addWidget(self.prepPublishButton, 0, 3)
        self.optionsLayout.addWidget(self.corePreviewSetupButton, 1, 0)
        self.optionsLayout.addWidget(self.previewOnButton, 1, 1)
        self.optionsLayout.addWidget(self.previewOffButton, 1, 2)
        self.optionsLayout.addWidget(self.coresOnButton, 1, 3)
        self.optionsLayout.addWidget(self.coresOffButton, 1, 4)
        self.optionsLayout.addWidget(self.deletePreviewButton, 1, 5)

        self.lightingGroupBox = QtGui.QGroupBox(self)
        self.lightingGroupBox.setTitle('MDL/SRF/LIGHT:')
        self.lightingLayout = QtGui.QVBoxLayout(self.lightingGroupBox)
        ## The big bad rebuild all button
        self.rebuildAllButton = QtGui.QPushButton('Full Scene Rebuild of Core archives')
        self.rebuildAllButton.released.connect(self.rebuildArchives)
        self.rebuildAllButton.setToolTip('Use this to cleanup all the duplicated archives with a full rebuild of the scene.')
        self.lightingLayout.addWidget(self.rebuildAllButton)
        ## Delete Core Archive button
        self.removeCAButton = QtGui.QPushButton('Full cleanup of Core Archive!')
        self.removeCAButton.released.connect(self.removeCoreArchiveSetup)
        self.removeCAButton.setToolTip('Use this to remove all the core archive related stuffs.')
        self.removeCAButton.setStyleSheet("QPushButton {text-align: center; background: dark red}")
        self.lightingLayout.addWidget(self.removeCAButton)

        self.mainLayout.addWidget(self.buttonsGroupBox)
        self.mainLayout.addWidget(self.lightingGroupBox)
        self.resize(self.sizeHint())

    def prepForPublish(self):
        ## From secondary LND scan scene cleanup
        ## CORES
        start = time.time()
        inprogressBar = pbui.ProgressBarUI(title = 'cleanUp Painted Duplicates:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 10, doingWhat = 'Cleaning painted archives....')
        coreLib.cleanPaintedArchives()
        inprogressBar.updateProgress(percent = 35, doingWhat = 'Taggging duplicated cores....')
        coreLib._tagDuplicateCoreArchives()
        inprogressBar.updateProgress(percent = 75, doingWhat = 'Prepping archives....')
        coreLib.prepArchivesForPublish()
        inprogressBar.updateProgress(percent = 85, doingWhat = 'Deleting all cores archives....')
        coreLib.deleteAllCores()
        inprogressBar.updateProgress(percent = 100, doingWhat = 'Done')
        inprogressBar.close()
        print 'TIME: %s' % (time.time()-start)
        
    def cleanUpPaintedArchives(self):
        """
        Just perform a base cleanup after all the archives are imported
        """       
        ## Run through the scane and cleanup the archives to what it would be after a publish
        start = time.time()
        inprogressBar = pbui.ProgressBarUI(title = 'cleanUp Painted Duplicates:')
        inprogressBar.show()
        inprogressBar.updateProgress(percent = 10, doingWhat = 'Cleaning Core Archives....')
        coreLib.cleanPaintedArchives()
        inprogressBar.updateProgress(percent = 50, doingWhat = 'Tagging cores....')
        coreLib._tagDuplicateCoreArchives()
        inprogressBar.updateProgress(percent = 100, doingWhat = 'Done')
        inprogressBar.close()
        print 'TIME: %s' % (time.time()-start)
        
    def rebuildArchives(self):
        """
        """
        self.reply = QtGui.QMessageBox.question(None, 'WARNING', 'Only Run this if you have duplicated your core_archives!\nIf you dont your imported core_archives will be removed from scene!', QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
        if self.reply == QtGui.QMessageBox.Ok:
            start = time.time()
            inprogressBar = pbui.ProgressBarUI(title = 'Rebuild Scene Core Archives:')
            inprogressBar.show()
            inprogressBar.updateProgress(percent = 1, doingWhat = 'Redoing base cleanups....')        
            debug(self.app, method = 'run_app', message = 'prepArchivesForPublish...', verbose = False)
            
            ## now clean the painted archives just to be sure that's all done
            inprogressBar.updateProgress(percent = 15, doingWhat = 'Cleaning duplicated archives...')
            self.cleanUpPaintedArchives()
    
            ## Delete all the cores. This should just leave the scene with the duplicated 
            coreLib.deleteAllCores()
            
            inprogressBar.updateProgress(percent = 25, doingWhat = 'Prepping the scene for export / rebuild..')
            ## NOTE we prep here for publish to remove the children of the duplicate archives if they exist as a means of cleaning the scene before rebuilding it.
            coreLib.prepArchivesForPublish()
            
            ## Get the assembly paths from the transforms in the scene with the correct tags to load now..
            getAllCorePaths = coreLib.getCorePaths()   
            debug(self.app, method = 'run_app', message = 'getAllCorePaths: %s' % getAllCorePaths, verbose = False)
            
            inprogressBar.updateProgress(percent = 15, doingWhat = 'Removing all namespaces to avoid name clashes...')
            ## Now blow up all the archives by removing ALL the namespaces in the scene so a fresh load of the new archives will be cleanly named.
            cleanup.removeAllNS()
            
            ## Now load the assemblies from the paths
            inprogressBar.updateProgress(percent = 50, doingWhat = 'Loading core_archives now...')
            if not coreLib.loadCoreArchives(paths = getAllCorePaths):
                inprogressBar.close()
            else:
                ## Now remove the old prepped archives as we don't need these anymore
                inprogressBar.updateProgress(percent = 55, doingWhat = 'Removing old core_archives now...')
                coreLib.removePreppedArchives()
        
                ## Now clean up the newly imported archives
                inprogressBar.updateProgress(percent = 60, doingWhat = 'Cleaning freshly imported archives now...')
                coreLib.cleanupCoreArchiveImports()
                
                ## Now Reconnect them
                inprogressBar.updateProgress(percent = 75, doingWhat = 'Reconnecting core archive duplicates to core archives now...')
                coreLib.doReconnect(app = self.app)
                
                ## Now cleanup
                inprogressBar.updateProgress(percent = 90, doingWhat = 'Cleanup...')
                coreLib.cleanupPlacements()
                ## Put all the coreRebuild the correct groups
                coreLib._cleanupCoreArchiveRebuildGrps(parentTO = 'geo_hrc')
                
                inprogressBar.updateProgress(percent = 100, doingWhat = 'Full rebuild complete..')
                inprogressBar.close()
                print 'TIME: %s' % (time.time()-start)
        
    def destroy_app(self):
        self.log_debug("Destroying sg_fetchMayaCamera")

    def _ls(self, nodeType = '', topTransform = True, stringFilter = '', unlockNode = False):
        if nodeType:
            nodes = cmds.ls(type = nodeType)
            if nodes:
                final_nodes = []
                for each in nodes:
                    each = cmds.ls(each, long = True)[0]
                    top_transform = cmds.listRelatives(each, parent = True, fullPath = True) if topTransform else None
                    final_node = top_transform[0] if top_transform else each

                    if unlockNode:
                        try:	cmds.lockNode(final_node, lock = False)
                        except:	mel.eval('warning "Failed to unlock %s, skipping...";' % final_node)

                    if stringFilter:
                        if stringFilter in final_node:
                            if final_node not in final_nodes:
                                final_nodes.append(final_node)
                    else:
                        if final_node not in final_nodes:
                            final_nodes.append(final_node)

                return final_nodes

            return []

    def removeCoreArchiveSetup(self):
        '''
        Do a complete clean-up of Core Archives setup...
        '''
        [cmds.delete(x) for x in cmds.ls('*CORE_ARCHIVES_hrc')]
        [cmds.delete(x) for x in cmds.ls('*placements_hrc')]
        [cmds.delete(x) for x in cmds.ls('*ROOT_ARCHIVES_DNT_hrc')]
        [cmds.delete(x) for x in cmds.ls('*unique_geo_hrc')]

        coreLib.cleanupDeadCoreArchives()
