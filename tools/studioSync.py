import getpass
from functools import partial
import sys, os, getopt, sip
try:
    if sys.platform == 'win32':
        if 'T:/software/python-api/' not in sys.path:
            sys.path.append('T:/software/python-api/')
        if 'C:/cygwin32/bin/' not in sys.path:
            sys.path.append('C:/cygwin32/bin/')
        if 'C:/cygwin/bin/' not in sys.path:
            sys.path.append('C:/cygwin/bin/')
        if 'E:/cygwin/bin/' not in sys.path:
            sys.path.append('E:/cygwin/bin/')
    elif sys.platform == 'cygwin':
        if '/cygdrive/t/software/lsapipeline/tools' not in sys.path:
            sys.path.append('/cygdrive/t/software/lsapipeline/tools')
        if '/cygdrive/t/software/python-api' not in sys.path:
            sys.path.append('/cygdrive/t/software/python-api')
        if '/cygdrive/t/software/bubblebathbay' not in sys.path:
            sys.path.append('/cygdrive/t/software/bubblebathbay')
        if '/cygdrive/c/Python27/Lib/site-packages' not in sys.path:
            sys.path.append('/cygdrive/c/Python27/Lib/site-packages')
        if '/cygdrive/c/cygwin32/bin' not in sys.path:
            sys.path.append('/cygdrive/c/cygwin32/bin')
    else:
        if '/_development/software/python-api/' not in sys.path:
            sys.path.append('/_development/software/python-api/')
except:
    pass

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import toolsCONST as CONST
import Widget_vr as VR
#reload(VR)
import bbb_audioFileManagement as audF
import bbb_storyboardFileManagement as sbrd
import bbb_playlistDownloader as pldnldr
import bbb_SyncWidget as syncWidget
import bbb_publishMayaAudioFiles as pubAud


class MainMenu(QMenuBar):
    def __init__(self, parent = None):
        """
        The main menu class
        """
        QMenuBar.__init__(self, parent)
        
        self.parent = parent 
        ## Main Menu
        self.optionsMenu    = QMenu(self)
        self.optionsMenu.setTitle('Options')
        self.addMenu(self.optionsMenu)
        self.optionsMenuGrp = QActionGroup(self)
        self.optionsMenuGrp.setExclusive(True)
        
        self.localOption = self.optionsMenu.addAction('Switch to Local Sync')
        self.localOption.toggled.connect(partial(self._toggleMode, 'Local'))
        self.optionsMenuGrp.addAction(self.localOption)
        self.localOption.setCheckable(True)
        self.localOption.setChecked(True)

        self.remoteOption = self.optionsMenu.addAction('Switch to Remote Sync')
        self.remoteOption.toggled.connect(partial(self._toggleMode, 'Remote'))
        self.optionsMenuGrp.addAction(self.remoteOption)
        self.remoteOption.setCheckable(True)
        self.remoteOption.setChecked(False)


    def _toggleMode(self, mode):
        """
        """
        if mode == 'Remote':
            self.parent.localSync = False
            self.parent._initUITabs()
            self.parent.setWindowTitle('REMOTE SYNC MODE')
        else:
            self.parent.localSync = True
            self.parent._initUITabs()
            self.parent.setWindowTitle('LOCAL SYNC MODE')


class StudioSync(QMainWindow):
    def __init__(self, winName = 'BBBay Studio Sync', localSync = False, parent = None):
        QMainWindow.__init__(self, parent)
        ###START CENTER WIDGET TAB WIDGET
        self.tabWidget = QTabWidget (self)
        self.tabWidget.setObjectName('StudioSync_tabWidget')
        self.tabWidget.setMovable(True)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setTabPosition(QTabWidget.North)
        
        print 'Starting UI Build now...'
        os.system('echo Starting UI BUILD NOW....')
        self.winName                = winName
        self.setWindowTitle(self.winName)
        self.setObjectName(self.winName)
        self.userName = getpass.getuser()
        self.tabWidgets = []
        self.localSync = False
        
        ## Setup some global users just for filtering tabs a loose permissions list if you will...
        self.localSyncIgnores       = []
        self.directorSyncIgnores    = ['carmeltravers', 'bbb1']
        self.audioSync              = ['jamesd']
        self.lskyUsers              = ['Administrator']
        self.storyboardSync         = ['jamesd']
        
        self.directorSync           = ['carmeltravers', 'jamesd', 'bbb1']
        
        ### THE MAIN MENU
        self.myMenu                 = MainMenu(self)
        
        ### PUT THE FINAL UI BITS IN PLACE        
        self.setMenuBar(self.myMenu)
        self.setCentralWidget(self.tabWidget)
        
        
        def showEvent(self, event):
            QMainWindow.showEvent(event)
            ## PROCESS WHAT MODE WE ARE IN....
            #### Local sync seems to be passed in as a str for some reason, too tired to give a shit atm...
            if localSync == 'False':
                self.localSync          = False
            else:
                os.system('echo Setting to local Sync UI....')
                self.localSync          = True
            
            print 'Starting Tab Builds now... self.local is : %s' % self.local
            self._initUITabs()
            
        
    def _initUITabs(self):
        """
        Setup the tabs depending on the mode selected and the User name, which we are using to figure out if we are in KL or Sydney at present
        as the user names are vastely different for now.
        """
        
        ##Cleanup existing for switch
        if self.tabWidgets:
            for each in self.tabWidgets:
                try:
                    each.setParent(None)
                    sip.delete(each)
                    each = None
                except:
                    pass
        ## BUILD THE TABS        
        ########################
        #### ASSET SYNC
        ### TO Lemonsky
        if self.userName not in self.directorSyncIgnores and self.userName not in self.lskyUsers and not self.localSync:
            if sys.platform == 'win32':
                self.assetSyncTab = syncWidget.BBBSyncWidget(
                                                           defaultSource        = CONST.ASSETS_WIN_DEFAULTSOURCE, 
                                                           defaultDest          = CONST.ASSETS_LSKY_DEFAULTDEST,
                                                           defaultPort          = CONST.ASSETS_DEFAULTPORT,
                                                           
                                                           stepsLabel           = CONST.ASSETS_STEPSLABEL, 
                                                           steps                = CONST.ASSETS_STEPS, 
                                                           stepsDefaultChecked  = CONST.ASSETS_STEPSDEFAULTCHECKED,
                                                           stepTypeLabelName    = 'Types',
                                                           globalSystemIgnores  = CONST.ASSETS_GLOBALSYSTEMIGNORES,
                                                           stepFolderIgnores    = CONST.ASSETS_STEPFOLDERIGNORES,
                                                           workFolderIgnores    = CONST.ASSETS_WORKFOLDERINGORES,
                                                           publishFolderIgnores = CONST.ASSETS_PUBLISHFOLDERIGNORES,
                                                           fileTypeIgnores      = CONST.ASSETS_FILETYPEIGNORES,
                                                           epFolderIgnores      = CONST.ASSETS_EPFOLDERIGNORES,
                                                           excludesSuffix       = 'ASSETS'
                                                           )
                self.tabWidget.addTab(self.assetSyncTab, 'TO LSky: Win Asset Sync')
                self.tabWidgets.append(self.assetSyncTab)
            else:
                self.assetSyncTab = syncWidget.BBBSyncWidget(
                                                           defaultSource        = CONST.ASSETS_MAC_DEFAULTSOURCE, 
                                                           defaultDest          = CONST.ASSETS_LSKY_DEFAULTDEST,
                                                           defaultPort          = CONST.ASSETS_DEFAULTPORT,
                                                           
                                                           stepsLabel           = CONST.ASSETS_STEPSLABEL, 
                                                           steps                = CONST.ASSETS_STEPS, 
                                                           stepsDefaultChecked  = CONST.ASSETS_STEPSDEFAULTCHECKED,
                                                           stepTypeLabelName    = 'Types',
                                                           globalSystemIgnores  = CONST.ASSETS_GLOBALSYSTEMIGNORES,
                                                           stepFolderIgnores    = CONST.ASSETS_STEPFOLDERIGNORES,
                                                           workFolderIgnores    = CONST.ASSETS_WORKFOLDERINGORES,
                                                           publishFolderIgnores = CONST.ASSETS_PUBLISHFOLDERIGNORES,
                                                           fileTypeIgnores      = CONST.ASSETS_FILETYPEIGNORES,
                                                           epFolderIgnores      = CONST.ASSETS_EPFOLDERIGNORES,
                                                           excludesSuffix       = 'ASSETS'
                                                           )
                self.tabWidget.addTab(self.assetSyncTab, 'TO LSky: Mac Asset Sync')
                self.tabWidgets.append(self.assetSyncTab)            
        ### TO LACIE
        elif self.userName not in self.directorSyncIgnores and self.userName not in self.lskyUsers and self.userName not in self.localSyncIgnores and self.localSync:
            if sys.platform == 'win32':
                self.assetSyncTab = syncWidget.BBBSyncWidget(
                                                           defaultSource        = CONST.ASSETS_WIN_DEFAULTSOURCE, 
                                                           defaultDest          = CONST.ASSETS_WIN_LOCAL_DEFAULTDEST,
                                                           defaultPort          = CONST.ASSETS_DEFAULTPORT,
                                                           
                                                           stepsLabel           = CONST.ASSETS_STEPSLABEL, 
                                                           steps                = CONST.ASSETS_STEPS, 
                                                           stepsDefaultChecked  = CONST.ASSETS_STEPSDEFAULTCHECKED,
                                                           stepTypeLabelName    = 'Types',
                                                           globalSystemIgnores  = CONST.ASSETS_GLOBALSYSTEMIGNORES,
                                                           stepFolderIgnores    = CONST.ASSETS_STEPFOLDERIGNORES,
                                                           workFolderIgnores    = CONST.ASSETS_WORKFOLDERINGORES,
                                                           publishFolderIgnores = CONST.ASSETS_PUBLISHFOLDERIGNORES,
                                                           fileTypeIgnores      = CONST.ASSETS_FILETYPEIGNORES,
                                                           epFolderIgnores      = CONST.ASSETS_EPFOLDERIGNORES,
                                                           excludesSuffix       = 'ASSETS'
                                                           )
                self.tabWidget.addTab(self.assetSyncTab, 'LACIE: Win Asset Sync')
                if not os.path.isdir(CONST.COMP_WIN_DEFAULTSOURCE):
                    self.assetSyncTab.sourceInput.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
                    self.assetSyncTab.sourceInput.setText('YOU MUST MOUNT THE DRIVE CORRECTLY!')
                self.assetSyncTab.localXfer.setChecked(True)
                self.tabWidgets.append(self.assetSyncTab)
            else:
                self.assetSyncTab = syncWidget.BBBSyncWidget(
                                                           defaultSource        = CONST.ASSETS_MAC_DEFAULTSOURCE, 
                                                           defaultDest          = CONST.ASSETS_MAC_LOCAL_DEFAULTDEST,
                                                           defaultPort          = CONST.ASSETS_DEFAULTPORT,
                                                           
                                                           stepsLabel           = CONST.ASSETS_STEPSLABEL, 
                                                           steps                = CONST.ASSETS_STEPS, 
                                                           stepsDefaultChecked  = CONST.ASSETS_STEPSDEFAULTCHECKED,
                                                           stepTypeLabelName    = 'Types',
                                                           globalSystemIgnores  = CONST.ASSETS_GLOBALSYSTEMIGNORES,
                                                           stepFolderIgnores    = CONST.ASSETS_STEPFOLDERIGNORES,
                                                           workFolderIgnores    = CONST.ASSETS_WORKFOLDERINGORES,
                                                           publishFolderIgnores = CONST.ASSETS_PUBLISHFOLDERIGNORES,
                                                           fileTypeIgnores      = CONST.ASSETS_FILETYPEIGNORES,
                                                           epFolderIgnores      = CONST.ASSETS_EPFOLDERIGNORES,
                                                           excludesSuffix       = 'ASSETS'
                                                           )
                self.tabWidget.addTab(self.assetSyncTab, 'LACIE: Mac Asset Sync')
                self.tabWidgets.append(self.assetSyncTab)
                if not os.path.isdir(CONST.COMP_MAC_DEFAULTSOURCE):
                    self.assetSyncTab.sourceInput.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
                    self.assetSyncTab.sourceInput.setText('YOU MUST MOUNT THE DRIVE CORRECTLY!')
                self.assetSyncTab.localXfer.setChecked(True)                          
        ### TO PPics
        elif self.userName in self.lskyUsers:
            self.assetSyncTab = syncWidget.BBBSyncWidget(
                                                       defaultSource        = CONST.ASSETS_WIN_DEFAULTSOURCE, 
                                                       defaultDest          = CONST.ASSETS_PPICS_DEFAULTDEST,
                                                       defaultPort          = CONST.ASSETS_PPICSPORT,
                                                       
                                                       stepsLabel           = CONST.ASSETS_STEPSLABEL, 
                                                       steps                = CONST.ASSETS_STEPS, 
                                                       stepsDefaultChecked  = CONST.ASSETS_STEPSDEFAULTCHECKED,
                                                       stepTypeLabelName    = 'Types',
                                                       globalSystemIgnores  = CONST.ASSETS_GLOBALSYSTEMIGNORES,
                                                       stepFolderIgnores    = CONST.ASSETS_STEPFOLDERIGNORES,
                                                       workFolderIgnores    = CONST.ASSETS_WORKFOLDERINGORES,
                                                       publishFolderIgnores = CONST.ASSETS_PUBLISHFOLDERIGNORES,
                                                       fileTypeIgnores      = CONST.ASSETS_FILETYPEIGNORES,
                                                       epFolderIgnores      = CONST.ASSETS_EPFOLDERIGNORES,
                                                       excludesSuffix       = 'ASSETS'
                                                       )
            self.tabWidget.addTab(self.assetSyncTab, 'TO PPics: Asset Sync')
            self.tabWidgets.append(self.assetSyncTab)
        else:
            pass
         
        ########################
        #### COMPOSITING DAILIES
        ### TO Lemonsky
        if self.userName not in self.lskyUsers and not self.localSync:
            if sys.platform == 'win32':
                self.compSyncTab = syncWidget.BBBSyncWidget(
                                                               defaultSource        = CONST.COMP_WIN_DEFAULTSOURCE, 
                                                               defaultDest          = CONST.COMP_LSKY_DEFAULTDEST,
                                                               defaultPort          = CONST.COMP_DEFAULTPORT,
                                                               
                                                               stepsLabel           = CONST.COMP_STEPSLABEL, 
                                                               steps                = CONST.COMP_STEPS, 
                                                               stepsDefaultChecked  = CONST.COMP_STEPSDEFAULTCHECKED,
                                                               stepTypeLabelName    = 'Episodes',
                                                               globalSystemIgnores  = CONST.COMP_GLOBALSYSTEMIGNORES,
                                                               stepFolderIgnores    = CONST.COMP_STEPFOLDERIGNORES,
                                                               workFolderIgnores    = CONST.COMP_WORKFOLDERINGORES,
                                                               publishFolderIgnores = CONST.COMP_PUBLISHFOLDERIGNORES,
                                                               fileTypeIgnores      = CONST.COMP_FILETYPEIGNORES,
                                                               epFolderIgnores      = CONST.COMP_EPFOLDERIGNORES,
                                                               excludesSuffix       = 'COMP'
                                                               )
                self.tabWidget.addTab(self.compSyncTab, 'TO LSky: Win Comp Dailies Sync')
                self.tabWidgets.append(self.compSyncTab)
            else:
                self.compSyncTab = syncWidget.BBBSyncWidget(
                                                               defaultSource        = CONST.COMP_MAC_DEFAULTSOURCE, 
                                                               defaultDest          = CONST.COMP_LSKY_DEFAULTDEST,
                                                               defaultPort          = CONST.COMP_DEFAULTPORT,
                                                               
                                                               stepsLabel           = CONST.COMP_STEPSLABEL, 
                                                               steps                = CONST.COMP_STEPS, 
                                                               stepsDefaultChecked  = CONST.COMP_STEPSDEFAULTCHECKED,
                                                               stepTypeLabelName    = 'Episodes',
                                                               globalSystemIgnores  = CONST.COMP_GLOBALSYSTEMIGNORES,
                                                               stepFolderIgnores    = CONST.COMP_STEPFOLDERIGNORES,
                                                               workFolderIgnores    = CONST.COMP_WORKFOLDERINGORES,
                                                               publishFolderIgnores = CONST.COMP_PUBLISHFOLDERIGNORES,
                                                               fileTypeIgnores      = CONST.COMP_FILETYPEIGNORES,
                                                               epFolderIgnores      = CONST.COMP_EPFOLDERIGNORES,
                                                               excludesSuffix       = 'COMP'
                                                               )
                self.tabWidget.addTab(self.compSyncTab, 'TO LSky: Mac Comp Dailies Sync')
                self.tabWidgets.append(self.compSyncTab)
        ### TO LACIE
        elif self.userName not in self.localSyncIgnores and self.userName not in self.lskyUsers and self.localSync:
            if sys.platform == 'win32':
                self.compSyncTab = syncWidget.BBBSyncWidget(
                                                               defaultSource        = CONST.COMP_WIN_DEFAULTSOURCE, 
                                                               defaultDest          = CONST.COMP_WIN_LOCAL_DEFAULTDEST,
                                                               defaultPort          = CONST.COMP_DEFAULTPORT,
                                                               
                                                               stepsLabel           = CONST.COMP_STEPSLABEL, 
                                                               steps                = CONST.COMP_STEPS, 
                                                               stepsDefaultChecked  = CONST.COMP_STEPSDEFAULTCHECKED,
                                                               stepTypeLabelName    = 'Episodes',
                                                               globalSystemIgnores  = CONST.COMP_GLOBALSYSTEMIGNORES,
                                                               stepFolderIgnores    = CONST.COMP_STEPFOLDERIGNORES,
                                                               workFolderIgnores    = CONST.COMP_WORKFOLDERINGORES,
                                                               publishFolderIgnores = CONST.COMP_PUBLISHFOLDERIGNORES,
                                                               fileTypeIgnores      = CONST.COMP_FILETYPEIGNORES,
                                                               epFolderIgnores      = CONST.COMP_EPFOLDERIGNORES,
                                                               excludesSuffix       = 'COMP'
                                                               )
                self.tabWidget.addTab(self.compSyncTab, 'LACIE: Win Comp Dailies Sync')
                self.tabWidgets.append(self.compSyncTab)
                if not os.path.isdir(CONST.COMP_WIN_DEFAULTSOURCE):
                    self.compSyncTab.sourceInput.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
                    self.compSyncTab.sourceInput.setText('YOU MUST MOUNT THE DRIVE CORRECTLY!')
                self.compSyncTab.localXfer.setChecked(True)
            else:
                self.compSyncTab = syncWidget.BBBSyncWidget(
                                                               defaultSource        = CONST.COMP_MAC_DEFAULTSOURCE, 
                                                               defaultDest          = CONST.COMP_MAC_LOCAL_DEFAULTDEST,
                                                               defaultPort          = CONST.COMP_DEFAULTPORT,
                                                               
                                                               stepsLabel           = CONST.COMP_STEPSLABEL, 
                                                               steps                = CONST.COMP_STEPS, 
                                                               stepsDefaultChecked  = CONST.COMP_STEPSDEFAULTCHECKED,
                                                               stepTypeLabelName    = 'Episodes',
                                                               globalSystemIgnores  = CONST.COMP_GLOBALSYSTEMIGNORES,
                                                               stepFolderIgnores    = CONST.COMP_STEPFOLDERIGNORES,
                                                               workFolderIgnores    = CONST.COMP_WORKFOLDERINGORES,
                                                               publishFolderIgnores = CONST.COMP_PUBLISHFOLDERIGNORES,
                                                               fileTypeIgnores      = CONST.COMP_FILETYPEIGNORES,
                                                               epFolderIgnores      = CONST.COMP_EPFOLDERIGNORES,
                                                               excludesSuffix       = 'COMP'
                                                               )
                self.tabWidget.addTab(self.compSyncTab, 'LACIE: Mac Comp Dailies Sync')
                self.tabWidgets.append(self.compSyncTab)
                if not os.path.isdir(CONST.COMP_MAC_DEFAULTSOURCE):
                    self.compSyncTab.sourceInput.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
                    self.compSyncTab.sourceInput.setText('YOU MUST MOUNT THE DRIVE CORRECTLY!')
                self.compSyncTab.localXfer.setChecked(True)
        ### TO PPics
        elif self.userName in self.lskyUsers:
            self.compSyncTab = syncWidget.BBBSyncWidget(
                                                       defaultSource        = CONST.COMP_WIN_DEFAULTSOURCE, 
                                                       defaultDest          = CONST.COMP_PPICS_DEFAULTDEST,
                                                       defaultPort          = CONST.COMP_PPICSPORT,
                                                       
                                                       stepsLabel           = CONST.COMP_STEPSLABEL, 
                                                       steps                = CONST.COMP_STEPS, 
                                                       stepsDefaultChecked  = CONST.COMP_STEPSDEFAULTCHECKED,
                                                       stepTypeLabelName    = 'Episodes',
                                                       globalSystemIgnores  = CONST.COMP_GLOBALSYSTEMIGNORES,
                                                       stepFolderIgnores    = CONST.COMP_STEPFOLDERIGNORES,
                                                       workFolderIgnores    = CONST.COMP_WORKFOLDERINGORES,
                                                       publishFolderIgnores = CONST.COMP_PUBLISHFOLDERIGNORES,
                                                       fileTypeIgnores      = CONST.COMP_FILETYPEIGNORES,
                                                       epFolderIgnores      = CONST.COMP_EPFOLDERIGNORES,
                                                       excludesSuffix       = 'COMP'                                                       
                                                       )
            self.tabWidget.addTab(self.compSyncTab, 'TO PPics: Comp Dailies Sync')
            self.tabWidgets.append(self.compSyncTab)
        else:
            pass
         
        ########################
        #### ANIMATION DAILIES
        ### TO Lemonsky
        if self.userName not in self.lskyUsers and not self.localSync:
            ## WINDOWS
            if sys.platform == 'win32':
                self.animSyncTab = syncWidget.BBBSyncWidget(
                                                               defaultSource        = CONST.ANIMATION_WIN_DEFAULTSOURCE, 
                                                               defaultDest          = CONST.ANIMATION_LSKY_DEFAULTDEST,
                                                               defaultPort          = CONST.ANIMATION_DEFAULTPORT,
                                                               
                                                               stepsLabel           = CONST.ANIMATION_STEPSLABEL, 
                                                               steps                = CONST.ANIMATION_STEPS, 
                                                               stepsDefaultChecked  = CONST.ANIMATION_STEPSDEFAULTCHECKED,
                                                               stepTypeLabelName    = 'Episodes',
                                                               globalSystemIgnores  = CONST.ANIMATION_GLOBALSYSTEMIGNORES,
                                                               stepFolderIgnores    = CONST.ANIMATION_STEPFOLDERIGNORES,
                                                               workFolderIgnores    = CONST.ANIMATION_WORKFOLDERINGORES,
                                                               publishFolderIgnores = CONST.ANIMATION_PUBLISHFOLDERIGNORES,
                                                               fileTypeIgnores      = CONST.ANIMATION_FILETYPEIGNORES,
                                                               epFolderIgnores      = CONST.ANIMATION_EPFOLDERIGNORES,
                                                               excludesSuffix       = 'ANIMATION'
                                                               )
                self.tabWidget.addTab(self.animSyncTab, 'TO LSky: Anim Dailies Sync')
                self.tabWidgets.append(self.animSyncTab)
            ## MAC
            else:
                self.animSyncTab = syncWidget.BBBSyncWidget(
                                                               defaultSource        = CONST.ANIMATION_MAC_DEFAULTSOURCE, 
                                                               defaultDest          = CONST.ANIMATION_LSKY_DEFAULTDEST,
                                                               defaultPort          = CONST.ANIMATION_DEFAULTPORT,
                                                               
                                                               stepsLabel           = CONST.ANIMATION_STEPSLABEL, 
                                                               steps                = CONST.ANIMATION_STEPS, 
                                                               stepsDefaultChecked  = CONST.ANIMATION_STEPSDEFAULTCHECKED,
                                                               stepTypeLabelName    = 'Episodes',
                                                               globalSystemIgnores  = CONST.ANIMATION_GLOBALSYSTEMIGNORES,
                                                               stepFolderIgnores    = CONST.ANIMATION_STEPFOLDERIGNORES,
                                                               workFolderIgnores    = CONST.ANIMATION_WORKFOLDERINGORES,
                                                               publishFolderIgnores = CONST.ANIMATION_PUBLISHFOLDERIGNORES,
                                                               fileTypeIgnores      = CONST.ANIMATION_FILETYPEIGNORES,
                                                               epFolderIgnores      = CONST.ANIMATION_EPFOLDERIGNORES,
                                                               excludesSuffix       = 'ANIMATION'
                                                               )
                self.tabWidget.addTab(self.animSyncTab, 'TO LSky: Mac Anim Dailies Sync')
                self.tabWidgets.append(self.animSyncTab)
        ### TO LACIE
        elif self.userName not in self.localSyncIgnores and self.userName not in self.lskyUsers and self.localSync:
            ## WIN
            if sys.platform == 'win32':
                self.animSyncTab = syncWidget.BBBSyncWidget(
                                                               defaultSource        = CONST.ANIMATION_WIN_DEFAULTSOURCE, 
                                                               defaultDest          = CONST.ANIMATION_WIN_LOCAL_DEFAULTDEST,
                                                               defaultPort          = CONST.ANIMATION_DEFAULTPORT,
                                                               
                                                               stepsLabel           = CONST.ANIMATION_STEPSLABEL, 
                                                               steps                = CONST.ANIMATION_STEPS, 
                                                               stepsDefaultChecked  = CONST.ANIMATION_STEPSDEFAULTCHECKED,
                                                               stepTypeLabelName    = 'Episodes',
                                                               globalSystemIgnores  = CONST.ANIMATION_GLOBALSYSTEMIGNORES,
                                                               stepFolderIgnores    = CONST.ANIMATION_STEPFOLDERIGNORES,
                                                               workFolderIgnores    = CONST.ANIMATION_WORKFOLDERINGORES,
                                                               publishFolderIgnores = CONST.ANIMATION_PUBLISHFOLDERIGNORES,
                                                               fileTypeIgnores      = CONST.ANIMATION_FILETYPEIGNORES,
                                                               epFolderIgnores      = CONST.ANIMATION_EPFOLDERIGNORES,
                                                               excludesSuffix       = 'ANIMATION'
                                                               )
                self.tabWidget.addTab(self.animSyncTab, 'LACIE: Win Anim Dailies Sync')
                self.tabWidgets.append(self.animSyncTab)
                if not os.path.isdir(CONST.COMP_WIN_DEFAULTSOURCE):
                    self.animSyncTab.sourceInput.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
                    self.animSyncTab.sourceInput.setText('YOU MUST MOUNT THE DRIVE CORRECTLY!')
                self.animSyncTab.localXfer.setChecked(True)
            ## MAC
            else:
                self.animSyncTab = syncWidget.BBBSyncWidget(
                                                               defaultSource        = CONST.ANIMATION_MAC_DEFAULTSOURCE, 
                                                               defaultDest          = CONST.ANIMATION_MAC_LOCAL_DEFAULTDEST,
                                                               defaultPort          = CONST.ANIMATION_DEFAULTPORT,
                                                               
                                                               stepsLabel           = CONST.ANIMATION_STEPSLABEL, 
                                                               steps                = CONST.ANIMATION_STEPS, 
                                                               stepsDefaultChecked  = CONST.ANIMATION_STEPSDEFAULTCHECKED,
                                                               stepTypeLabelName    = 'Episodes',
                                                               globalSystemIgnores  = CONST.ANIMATION_GLOBALSYSTEMIGNORES,
                                                               stepFolderIgnores    = CONST.ANIMATION_STEPFOLDERIGNORES,
                                                               workFolderIgnores    = CONST.ANIMATION_WORKFOLDERINGORES,
                                                               publishFolderIgnores = CONST.ANIMATION_PUBLISHFOLDERIGNORES,
                                                               fileTypeIgnores      = CONST.ANIMATION_FILETYPEIGNORES,
                                                               epFolderIgnores      = CONST.ANIMATION_EPFOLDERIGNORES,
                                                               excludesSuffix       = 'ANIMATION'
                                                               )
                self.tabWidget.addTab(self.animSyncTab, 'LACIE: Mac Anim Dailies Sync')
                self.tabWidgets.append(self.animSyncTab)
                if not os.path.isdir(CONST.COMP_MAC_DEFAULTSOURCE):
                    self.animSyncTab.sourceInput.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
                    self.animSyncTab.sourceInput.setText('YOU MUST MOUNT THE DRIVE CORRECTLY!')
                self.animSyncTab.localXfer.setChecked(True)
        ### TO PPics
        elif self.userName in self.lskyUsers:
            self.animSyncTab = syncWidget.BBBSyncWidget(
                                                           defaultSource        = CONST.ANIMATION_WIN_DEFAULTSOURCE, 
                                                           defaultDest          = CONST.ANIMATION_PPICS_DEFAULTDEST,
                                                           defaultPort          = CONST.ANIMATION_PPICSPORT,
                                                           
                                                           stepsLabel           = CONST.ANIMATION_STEPSLABEL, 
                                                           steps                = CONST.ANIMATION_STEPS, 
                                                           stepsDefaultChecked  = CONST.ANIMATION_STEPSDEFAULTCHECKED,
                                                           stepTypeLabelName    = 'Episodes',
                                                           globalSystemIgnores  = CONST.ANIMATION_GLOBALSYSTEMIGNORES,
                                                           stepFolderIgnores    = CONST.ANIMATION_STEPFOLDERIGNORES,
                                                           workFolderIgnores    = CONST.ANIMATION_WORKFOLDERINGORES,
                                                           publishFolderIgnores = CONST.ANIMATION_PUBLISHFOLDERIGNORES,
                                                           fileTypeIgnores      = CONST.ANIMATION_FILETYPEIGNORES,
                                                           epFolderIgnores      = CONST.ANIMATION_EPFOLDERIGNORES,
                                                           excludesSuffix       = 'ANIMATION'
                                                           )
            self.tabWidget.addTab(self.animSyncTab, 'TO PPics: Anim Dailies Sync ')
            self.tabWidgets.append(self.animSyncTab)
        else:
            pass
         
        ########################
        #### AUDIO UPLOADS
        ### TO Lemonsky
        if self.userName in self.audioSync and not self.localSync:
            if sys.platform == 'win32':
                self.audioSyncTab = syncWidget.BBBSyncWidget(
                                                      defaultSource        = CONST.AUDIO_WIN_DEFAULTSOURCE, 
                                                      defaultDest          = CONST.AUDIO_LSKY_DEFAULTDEST,
                                                      defaultPort          = CONST.AUDIO_DEFAULTPORT,
                                                      
                                                      stepsLabel           = CONST.AUDIO_STEPSLABEL, 
                                                      steps                = CONST.AUDIO_STEPS, 
                                                      stepsDefaultChecked  = CONST.AUDIO_STEPSDEFAULTCHECKED,
                                                      stepTypeLabelName    = 'Episodes',
                                                      globalSystemIgnores  = CONST.AUDIO_GLOBALSYSTEMIGNORES,
                                                      stepFolderIgnores    = CONST.AUDIO_STEPFOLDERIGNORES,
                                                      workFolderIgnores    = CONST.AUDIO_WORKFOLDERINGORES,
                                                      publishFolderIgnores = CONST.AUDIO_PUBLISHFOLDERIGNORES,
                                                      fileTypeIgnores      = CONST.AUDIO_FILETYPEIGNORES,
                                                      epFolderIgnores      = CONST.AUDIO_EPFOLDERIGNORES,
                                                      excludesSuffix       = 'AUDIO'
                                                      )
                self.tabWidget.addTab(self.audioSyncTab, 'TO LSky: Win Audio Sync')
                self.tabWidgets.append(self.audioSyncTab)
            else:
                self.audioSyncTab = syncWidget.BBBSyncWidget(
                                                      defaultSource        = CONST.AUDIO_MAC_DEFAULTSOURCE, 
                                                      defaultDest          = CONST.AUDIO_LSKY_DEFAULTDEST,
                                                      defaultPort          = CONST.AUDIO_DEFAULTPORT,
                                                      
                                                      stepsLabel           = CONST.AUDIO_STEPSLABEL, 
                                                      steps                = CONST.AUDIO_STEPS, 
                                                      stepsDefaultChecked  = CONST.AUDIO_STEPSDEFAULTCHECKED,
                                                      stepTypeLabelName    = 'Episodes',
                                                      globalSystemIgnores  = CONST.AUDIO_GLOBALSYSTEMIGNORES,
                                                      stepFolderIgnores    = CONST.AUDIO_STEPFOLDERIGNORES,
                                                      workFolderIgnores    = CONST.AUDIO_WORKFOLDERINGORES,
                                                      publishFolderIgnores = CONST.AUDIO_PUBLISHFOLDERIGNORES,
                                                      fileTypeIgnores      = CONST.AUDIO_FILETYPEIGNORES,
                                                      epFolderIgnores      = CONST.AUDIO_EPFOLDERIGNORES,
                                                      excludesSuffix       = 'AUDIO'
                                                      )
                self.tabWidget.addTab(self.audioSyncTab, 'TO LSky: Mac Audio Sync')
                self.tabWidgets.append(self.audioSyncTab)
        elif self.userName in self.audioSync and self.userName not in self.localSyncIgnores and self.localSync:
            if sys.platform == 'win32':
                self.audioSyncTab = syncWidget.BBBSyncWidget(
                                                      defaultSource        = CONST.AUDIO_WIN_DEFAULTSOURCE, 
                                                      defaultDest          = CONST.AUDIO_WIN_LOCAL_DEFAULTDEST,
                                                      defaultPort          = CONST.AUDIO_DEFAULTPORT,
                                                      
                                                      stepsLabel           = CONST.AUDIO_STEPSLABEL, 
                                                      steps                = CONST.AUDIO_STEPS, 
                                                      stepsDefaultChecked  = CONST.AUDIO_STEPSDEFAULTCHECKED,
                                                      stepTypeLabelName    = 'Episodes',
                                                      globalSystemIgnores  = CONST.AUDIO_GLOBALSYSTEMIGNORES,
                                                      stepFolderIgnores    = CONST.AUDIO_STEPFOLDERIGNORES,
                                                      workFolderIgnores    = CONST.AUDIO_WORKFOLDERINGORES,
                                                      publishFolderIgnores = CONST.AUDIO_PUBLISHFOLDERIGNORES,
                                                      fileTypeIgnores      = CONST.AUDIO_FILETYPEIGNORES,
                                                      epFolderIgnores      = CONST.AUDIO_EPFOLDERIGNORES,
                                                      excludesSuffix       = 'AUDIO'
                                                      )
                self.tabWidget.addTab(self.audioSyncTab, 'TO LACIE: Win Audio Sync')
                self.tabWidgets.append(self.audioSyncTab)
                if not os.path.isdir(CONST.COMP_WIN_DEFAULTSOURCE):
                    self.audioSyncTab.sourceInput.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
                    self.audioSyncTab.sourceInput.setText('YOU MUST MOUNT THE DRIVE CORRECTLY!')
                self.audioSyncTab.localXfer.setChecked(True)
            else:
                self.audioSyncTab = syncWidget.BBBSyncWidget(
                                                      defaultSource        = CONST.AUDIO_MAC_DEFAULTSOURCE, 
                                                      defaultDest          = CONST.AUDIO_MAC_LOCAL_DEFAULTDEST,
                                                      defaultPort          = CONST.AUDIO_DEFAULTPORT,
                                                      
                                                      stepsLabel           = CONST.AUDIO_STEPSLABEL, 
                                                      steps                = CONST.AUDIO_STEPS, 
                                                      stepsDefaultChecked  = CONST.AUDIO_STEPSDEFAULTCHECKED,
                                                      stepTypeLabelName    = 'Episodes',
                                                      globalSystemIgnores  = CONST.AUDIO_GLOBALSYSTEMIGNORES,
                                                      stepFolderIgnores    = CONST.AUDIO_STEPFOLDERIGNORES,
                                                      workFolderIgnores    = CONST.AUDIO_WORKFOLDERINGORES,
                                                      publishFolderIgnores = CONST.AUDIO_PUBLISHFOLDERIGNORES,
                                                      fileTypeIgnores      = CONST.AUDIO_FILETYPEIGNORES,
                                                      epFolderIgnores      = CONST.AUDIO_EPFOLDERIGNORES,
                                                      excludesSuffix       = 'AUDIO'
                                                      )
                self.tabWidget.addTab(self.audioSyncTab, 'TO LACIE: Mac Audio Sync')
                self.tabWidgets.append(self.audioSyncTab)
                if not os.path.isdir(CONST.COMP_MAC_DEFAULTSOURCE):
                    self.audioSyncTab.sourceInput.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
                    self.audioSyncTab.sourceInput.setText('YOU MUST MOUNT THE DRIVE CORRECTLY!')
                self.audioSyncTab.localXfer.setChecked(True)
        else:
            pass

        #######################
        ### AUDIO LOCAL FILE MANAGEMENT
        #######################
        if self.userName in self.audioSync and self.userName not in self.lskyUsers:
            self.audioFileMangementTab = audF.AudioFileManagement(defaultSource = 'O:/EPISODE DELIVERY')
            self.tabWidget.addTab(self.audioFileMangementTab, 'Manage Audio') 
            self.tabWidgets.append(self.audioFileMangementTab)       

        #######################
        ### STORYBOARD LOCAL FILE MANAGEMENT
        #######################
        if self.userName in self.storyboardSync and self.userName not in self.lskyUsers:
            self.storyboardFileMangementTab = sbrd.StoryboardFileManagement(defaultSource = 'O:/EPISODE DELIVERY')
            self.tabWidget.addTab(self.storyboardFileMangementTab, 'Manage Storyboards')   
            self.tabWidgets.append(self.storyboardFileMangementTab)
        
        ########################
        #### PLAYLIST DOWNLOAD MANAGEMENT
        #######################
        if self.userName in self.directorSync and self.userName not in self.lskyUsers:
            ### This one internally handles Mac and PC Paths...
            self.directorDownloadTab = pldnldr.DownloadPlaylist()
            self.tabWidget.addTab(self.directorDownloadTab, 'Playlist Downloader')
            self.tabWidgets.append(self.directorDownloadTab)
        
        ########################
        #### LEMONSKY PUBLISH AUDIO MANAGEMENT
        #######################
        if self.userName in self.lskyUsers :
            ### This one internally handles Mac and PC Paths...
            self.publishAudioTab = pubAud.PublishMayaAudio()
            self.tabWidget.addTab(self.publishAudioTab, 'Publish Episode Audio')
            self.tabWidgets.append(self.publishAudioTab)

def main(argv):
    winName     = ''
    localSync   = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'w:l:')
    except getopt.GetoptError:
        print 'studioSync.py winName <string> localSync <boolean>'
        sys.exit(2)
    #print opts
    for opt, arg in opts:
        if opt == '-h':
            print 'studioSync.py winName = <string> localSync = <boolean>'
            sys.exit()
        elif opt in ("-w"):
            winName = arg
        elif opt in ("-l"):
            localSync = arg
         
    app     = QApplication(sys.argv)
    myWin   = StudioSync(winName, localSync)
    myWin.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
   main(sys.argv[1:])