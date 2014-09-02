from functools import partial
import sys, os, time, subprocess, sip, getpass
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
import cPickle as pickle
import Widget_vr as VR
import toolsCONST as CONST
import platform

class BBBSyncWidget(QWidget):
    def __init__(self, winName = 'I AM A WINDOW', defaultSource = '', defaultDest = '', defaultPort = 22,  stepsLabel = '', steps = [], stepsDefaultChecked = [], 
                       stepTypeLabelName = 'Episodes', globalSystemIgnores = [], stepFolderIgnores = [], workFolderIgnores = [], publishFolderIgnores = [], epFolderIgnores =[], 
                       fileTypeIgnores = [], excludesSuffix = '', parent = None):
        """
        @param winName: The name of the sync window
        @param defaultSource: The path to the source folder on the server you are transferring from.
        @param defaultDest: The path to the destination folder on the server you are transferring to. Note for local transfers drop the last directory.
        @param defaultPort: The ssh port to use
        @param stepsLabel: The label for the shotGun steps
        @param steps: The list of steps to consider eg: Anm, LGHT etc
        @param stepTypeLabelName: The name of what we're sourcing, such as Assets, Episodes
        @param globalSystemIgnores: The list of names of global system files to add to the excludes text file.
        @param stepFolderIgnores: The list of names of step folders to add to the excludes text file eg: Anm Blck.
        @param workFolderIgnores: The list of names of work subFolders etc to add to the excludes text fileeg: oceanPresets.
        @param publishFolderIgnores: The list of publish folder names to add to the excludes text file eg: alembic_anim.
        @param epFolderIgnores: The list of bad folder names to add to the excludes text file eg: eptst106.
        @param fileTypeIgnores: The list of bad file types to add to the excludes text file eg: '*.iff' .
        @param excludesSuffix: The suffix to use for the excludes file so it doesn't clash with another rSync session already running.
        @type winName: String
        @type defaultSource: String
        @type defaultDest: String
        @type defaultPort: Int
        @type stepsLabel: String
        @type steps: List
        @type stepTypeLabelName: String
        @type globalSystemIgnores: List of strings
        @type stepFolderIgnores: List of strings
        @type workFolderIgnores: List of strings
        @type publishFolderIgnores: List of strings
        @type epFolderIgnores: List of strings
        @type fileTypeIgnores: List of strings
        @type excludesSuffix: String
        """
             
        QWidget.__init__(self, parent)
        
        ############################
        ### DEFINE STUFF
        self.winName                = winName
        self.setWindowTitle(self.winName)
        self.stepsLabel             = stepsLabel
        self.steps                  = steps
        self.stepsDefaultChecked    = stepsDefaultChecked
        self.stepTypeLabelName      = stepTypeLabelName
        self.globalSystemIgnores    = globalSystemIgnores
        self.stepFolderIgnores      = stepFolderIgnores
        self.workFolderIgnores      = workFolderIgnores
        self.publishFolderIgnores   = publishFolderIgnores
        self.fileTypeIgnores        = fileTypeIgnores
        self.epFolderIgnores        = epFolderIgnores
        self.excludesSuffix         = excludesSuffix
        ## Set the ignores that should be used...
        self.globalIgnores          = []
        self.excludeList            = []
        ## Get the user name
        self.user                   = getpass.getuser()       
        ## Define the variable for the source folder and destination folder (local and remote as it were)
        self.sourceFolder           = defaultSource
        self.destinationFolder      = defaultDest
        ## Set the default path for the rSync saves and loads...
        if sys.platform == 'win32':
            self.filePaths = CONST.WIN_RSYNCFILES
            if self.user == 'jamesd':
                if 'Windows-7' in platform.platform():
                    self.cygDriveLetter = 'e'
                    self.cygWin         = 'cygwin'
                    self.driveLetter    = 'E:'
                else:
                    self.cygDriveLetter = 'c'
                    self.driveLetter    = 'C:'
                    self.cygWin         = 'cygwin32'
            else:
                self.cygDriveLetter = 'c'
                self.driveLetter    = 'C:'
                self.cygWin         = 'cygwin32'
            ## Setup the folder path for the excludes text file.
            self.excludePathRoot    = '/cygdrive/%s/%s/home/%s/tmp' % (self.cygDriveLetter, self.cygWin, self.user)
            self.excludeFile        = '%s/excludes_%s.txt' % (self.excludePathRoot, self.excludesSuffix)       
            ## Setup a windows based version of the path for the os lib to use properly.
            self.excludeWinDirPath  = os.path.abspath('%s/%s' % (self.driveLetter, self.excludePathRoot.split( '/cygdrive/%s/' % self.cygDriveLetter)[-1]))
            self.excludeWinFilePath = os.path.abspath('%s/%s' % (self.driveLetter, self.excludeFile.split( '/cygdrive/%s/' % self.cygDriveLetter)[-1]))
            ## Check to see if this directory actually exists and if it doesn't make it.
            if not os.path.isdir(self.excludeWinDirPath):
                os.mkdir(self.excludeWinDirPath)
        else:
            self.filePaths = CONST.MAC_RSYNCFILES
            self.excludePathRoot    = '/_development/Temp'
            self.excludeFile        = '/_development/Temp/excludes.txt'
       
        ##################################
        ### BUILD THE MAIN UI       
        ## Set the main layout for the UI
        self.mainLayout = QVBoxLayout(self)
        self.notes = QLabel('Sync stuff...')
        ## Here we define a horizontal layout for the buttons load and save.
        self.buttonsLayout = QHBoxLayout(self)
        ## Now we define the buttons for the horizontal layout
        self.saveButton = QPushButton('Save Paths')
        ## Connect the signals and slots for the button save
        self.saveButton.released.connect(self._saveLayout)
        self.loadButton = QPushButton('Load Paths')
        ## Connect the signals and slots for the button load
        self.loadButton.released.connect(self._loadLayout)
        ## Now we add the buttons to the layout
        self.buttonsLayout.addWidget(self.saveButton)
        self.buttonsLayout.addWidget(self.loadButton)

        self.portLayout = QHBoxLayout(self)
        ###Set the port number for the ssh here
        self.portLabel = QLabel('ssh Port')
        self.portNumber = QDoubleSpinBox()
        self.portNumber.setDecimals(0)
        self.portNumber.setFixedSize(100, 25)
        self.portNumber.setRange(-5000, 5000)
        self.portNumber.setSingleStep(1)
        self.portNumber.setValue(defaultPort)
        
        self.portLayout.addWidget(self.portLabel)
        self.portLayout.addWidget(self.portNumber)
        self.portLayout.addStretch(1)
        
        ## Set the layout for the source text input and browse button        
        self.pathLayout = QHBoxLayout(self)
        ## Define the widgets for this layout
        self.sourceInput = QLineEdit(self)
        self.sourceInput.textChanged.connect(partial(self._updateDestText, dest = False))
        self.browseButton = QPushButton('setSRC')
        self.browseButton.released.connect(partial(self._browseDialog, dest = False))
        ## Add the widgets to the layout
        self.pathLayout.addWidget(self.sourceInput)       
        self.pathLayout.addWidget(self.browseButton)
        
        ## Set the layout for the destination  text input and browse button
        self.destLayout = QHBoxLayout(self)
        self.destInput = QLineEdit(self)
        self.destInput.textChanged.connect(partial(self._updateDestText, dest = True))
        ## Define the widgets for this layout
        self.destBrowseButton = QPushButton('setDest')
        self.destBrowseButton.released.connect(partial(self._browseDialog, dest = True))
        ## Add the widgets to the layout
        self.destLayout.addWidget(self.destInput)       
        self.destLayout.addWidget(self.destBrowseButton)
        
        ## Make a nice groupbox layout for the options
        self.optionsGroupBox = QGroupBox(self)
        self.optionsGroupBox.setTitle('RSync Options')
        ## Define a layout for the groupbox and make sure to set the parent of this to the groupbox now.
        self.optionsLayout = QHBoxLayout(self.optionsGroupBox)
        ## Now define the widgets for the groupbox
        self.showProgress = QCheckBox(self)
        self.showProgress.setChecked(True)
        self.showProgress.setText('Show % Progress?')
        self.showProgress.setToolTip('Turns on rSync progress reporting.')
        self.verbose = QCheckBox(self)
        self.verbose.setChecked(True)
        self.verbose.setText('Verbose?')
        self.verbose.setToolTip('Turns on rSyncs verbose setting.')
        self.localXfer = QCheckBox(self)
        self.localXfer.setChecked(False)
        self.localXfer.setToolTip('Used for LAN transfers. Make sure this is off for transfers over the internet.')
        self.localXfer.setText('Local Xfer?')
        self.listOnly = QCheckBox(self)
        self.listOnly.setChecked(False)
        self.listOnly.setText('List Server Only?')
        self.listOnly.setToolTip('This will return a listing of the servers files, and do nothing else.')
        self.compress = QCheckBox(self)
        self.compress.setChecked(True)
        self.compress.setText('Compress?')
        self.compress.setToolTip('Turns on the compression for transfers')
        self.dryRun = QCheckBox(self)
        self.dryRun.setChecked(False)
        self.dryRun.setText('dryRun?')
        self.dryRun.setToolTip('Will do a test of the setup without doing the actual transfers.')
        self.inclWorkFolders = QCheckBox(self)
        self.inclWorkFolders.setChecked(False)
        self.inclWorkFolders.setText('Include Working Files?')
        self.inclWorkFolders.setToolTip('Include all the working files in the transfer?')
        self.inclWorkFolders.toggled.connect(self._setIncludeWorkFiles)
        self.removeExclude = QCheckBox(self)
        self.removeExclude.setChecked(True)
        self.removeExclude.setText('removeExcludeFile?')
        self.removeExclude.setToolTip('This will delete the txt file after the transfer is done. \nTurn this off for debugging exclude issues.')
        self.playFinishSound = QCheckBox(self)
        self.playFinishSound.setChecked(False)
        self.playFinishSound.setText('playFinishSound?')
        self.playFinishSound.setToolTip('This a sound when transfers are complete.')
        ## Now add the widgets to the groupbox layout
        self.optionsLayout.addWidget(self.localXfer)
        self.optionsLayout.addWidget(self.inclWorkFolders)
        self.optionsLayout.addWidget(self.removeExclude)
        self.optionsLayout.addWidget(self.showProgress)
        self.optionsLayout.addWidget(self.verbose)
        self.optionsLayout.addWidget(self.compress)
        self.optionsLayout.addWidget(self.listOnly)
        self.optionsLayout.addWidget(self.dryRun)
        self.optionsLayout.addWidget(self.playFinishSound)
        self.optionsLayout.addStretch(1)
        
        ## Make a nice groupbox layout for the steps
        self.stepsGroupBox = QGroupBox(self)
        self.stepsGroupBox.setTitle('%s Steps' % self.stepsLabel)
        ## Define a layout for the groupbox and make sure to set the parent of this to the groupbox now.
        self.stepLayout = QHBoxLayout(self.stepsGroupBox)
        ## Here we short cut the checkbox making by defining a list of checkbox names and we then use this list to build the boxes.
        ## This empty list is to hold all the QCheckBoxes as they are made so we can call on them later as the iteration through the build below
        ## will just keep creating the same self.stepCheckBox over and over and destroy the previous, but we can keep this by adding it into a new list of 
        ## the actual QCheckBoxes as they are in memory.
        self.stepBoxes = []
        ## Iterate and build the checkboxes now.
        for eachstep in self.steps:
            self.stepCheckBox = QCheckBox(self)
            if eachstep in self.stepsDefaultChecked:
                self.stepCheckBox.setChecked(True)
            else:
                self.stepCheckBox.setChecked(False)
            if eachstep == 'ALL':
                self.separator = VR.Widget_vr(self)
                self.stepCheckBox.toggled.connect(self._toggleAllSteps)
                self.stepLayout.addWidget(self.stepCheckBox)
                self.stepLayout.addWidget(self.separator)
            else:
                self.stepLayout.addWidget(self.stepCheckBox)
            self.stepCheckBox.setText(eachstep)
            self.stepBoxes.append(self.stepCheckBox)
        self.stepLayout.addStretch(1)
        ## Similar approach for the types, but because this folder is based on shotgun folders I'm calling the directory list here to keep up with anything new added from
        ## shotgun.
        self.typesGroupBox = QGroupBox(self)
        self.typesGroupBox.setTitle(self.stepTypeLabelName)        
        self.typeLayout = QGridLayout(self.typesGroupBox)
        self.types = []
        self.typeBoxes = []
        self._cleanCheckboxes()
        self.doTypeCheckboxes()

        ## Define the button to do the sync.
        self.goButton = QPushButton('SYNC NOW..')
        self.goButton.released.connect(self.doSync)
        self.goButton.setStyleSheet('QPushButton {background-color: green; border: 2px solid 1 ; border-radius: 6px;}')
        
        ## Now add all the widgets to the main layout in the order we want them represented
        #self.mainLayout.addWidget(self.notes)
        self.mainLayout.addLayout(self.buttonsLayout)
        self.mainLayout.addLayout(self.portLayout)
        self.mainLayout.addLayout(self.pathLayout)
        self.mainLayout.addLayout(self.destLayout)
        self.mainLayout.addWidget(self.optionsGroupBox)
        self.mainLayout.addWidget(self.stepsGroupBox)
        self.mainLayout.addWidget(self.typesGroupBox)
        self.mainLayout.addWidget(self.goButton)
        self.sourceInput.setText(self.sourceFolder)
        self.destInput.setText(self.destinationFolder)
        self.resize(500,200)
        
    def _setIncludeWorkFiles(self):
        """
        Used to set up the additional ingores to add to the excludes file
        """
        if not self.inclWorkFolders.isChecked():
            self.globalIgnores.append('work')

        ### GlobalSystemIgnores
        for each in self.globalSystemIgnores:
            if each not in self.globalIgnores:
                self.globalIgnores.append(each)
        
        ### EpFolderIgnores
        for each in self.epFolderIgnores:
            if each not in self.globalIgnores:
                self.globalIgnores.append(each)
        
        ### StepFolderIgnores
        for each in self.stepFolderIgnores:
            if each not in self.globalIgnores:
                self.globalIgnores.append(each)
        
        ### PublishFolderIgnores
        for each in self.publishFolderIgnores:
            if each not in self.globalIgnores:
                self.globalIgnores.append(each)

        ### FileTypeIgnores
        for each in self.fileTypeIgnores:
            if each not in self.globalIgnores:
                self.globalIgnores.append(each)

    def doTypeCheckboxes(self):
        self.types = []
        self.typeBoxes = []
        ## First add the ALL checkbox
        self.typesAll = QCheckBox(self)
        self.typesAll.setChecked(False)
        self.typesAll.setText('ALL')
        self.typesAll.toggled.connect(self._toggleAllTypes)
        self.typeLayout.addWidget(self.typesAll)
        self.typeBoxes.append(self.typesAll)
        self.typeLayout.addWidget(self.typesAll, 0, 0)
        ## Now process the folder and add the folders found as checkboxes.
        try:
            for eachDir in os.listdir(self.sourceFolder):
                if '.' not in eachDir and eachDir not in self.epFolderIgnores:
                    self.types.append(eachDir)
        except :
            self.types =  ['No folders found']

        self.colCount = 6
        r = 1
        c = 1
        for eachType in sorted(self.types):
            self.typeCheckBox = QCheckBox(self)
            self.typeCheckBox.setChecked(False)
            self.typeCheckBox.setText(eachType)
            self.typeBoxes.append(self.typeCheckBox)
            if c == self.colCount:
                r = r + 1
                c = 1
            self.typeLayout.addWidget(self.typeCheckBox, r, c)
            c = c + 1

        self.resize(500,200)
        
    def _cleanCheckboxes(self):
        """
        Remove the checkboxes from the layout
        """
        if len(self.typeBoxes) != 0:
            for eachCheckbox in self.typeBoxes:
                eachCheckbox.hide()
                self.typeLayout.removeWidget(eachCheckbox)
        self.typeBoxes = []

        return self.typeBoxes

    def _updateDestText(self, dest = True):
        """
        Used for the textChanged on the input or dest input boxes
        """
        if not dest:
            self.sourceFolder = str(self.sourceInput.text())
            self._cleanCheckboxes()
            self.doTypeCheckboxes()
        else:
            self.destinationFolder = str(self.destInput.text())

    def _toggleAllSteps(self):
        """
        A quick toggle for all the step checkboxes to on or off
        """
        for eachStep in self.stepBoxes:
            if eachStep.text() == 'ALL':
                if eachStep.isChecked():
                    for eachSubStep in self.stepBoxes:
                        if eachSubStep.text() != 'ALL':
                            eachSubStep.setChecked(True)
                else:
                    for eachSubStep in self.stepBoxes:
                        if eachSubStep.text() != 'ALL':
                            eachSubStep.setChecked(False)

    def _toggleAllTypes(self):
        """
        A quick toggle for all the type checkboxes to on or off
        """
        for eachType in self.typeBoxes:
            if eachType.text() == 'ALL':
                if eachType.isChecked():
                    for eachSubType in self.typeBoxes:
                        if eachSubType.text() != 'ALL':
                            eachSubType.setChecked(True)
                else:
                    for eachSubType in self.typeBoxes:
                        if eachSubType.text() != 'ALL':
                            eachSubType.setChecked(False)
        
    def _browseDialog(self, dest = True):
        """
        This opens up a QFileDialog hard set to browse into the bubblebathbay folder by default. 
        @param dest: To set if you are setting the destination input or the source input
        @type dest: Boolean 
        """
        try:
            myPath = QFileDialog(self, 'rootDir', 'I:/lsapipeline/').getExistingDirectory().replace('\\', '/')
        except :
            myPath = QFileDialog(self, 'rootDir', '').getExistingDirectory().replace('\\', '/')
        if not dest:
            self.sourceInput.setText(myPath)
            self.sourceFolder = str(myPath)
        else:
            self.destInput.setText(myPath)
            self.destinationFolder = str(myPath)

    def _getsteps(self):
        """
        Internal used to return the checked steps in the form of a list for the exclude list.
        """
        steps = []
        for each in self.stepBoxes:
            if 'ALL' not in each.text():
                if each.isChecked():
                    steps.append(str(each.text()))
        return steps

    def _getOffsteps(self):
        """
        Internal used to return the checked steps in the form of a list for the exclude list.
        """
        steps = []
        for each in self.stepBoxes:
            if 'ALL' not in each.text():
                if not each.isChecked():
                    steps.append(str(each.text()))
        return steps
 
    def _getInvalidTypes(self):
        """
        Internal used to return the invalid types for the exclude list.
        """
        types = []
        for each in self.typeBoxes:
            if not each.isChecked():
                if str(each.text()) not in types:
                    types.append(str(each.text()))
        return types
                         
    def doSync(self):
        """
        Main func to do the sync
        """
        self._setIncludeWorkFiles()
        self.allsteps = self._getsteps()
        self.invalidTypes = self._getInvalidTypes()

        self._processPaths(self.allsteps, self.invalidTypes)
        self._syncNow()
        if not self.dryRun.isChecked():
            pass

    def _processPaths(self, steps, invalidTypes):
        """
        Internal to process the invalid paths into the exclude list
        Some of these are hard set in the self.globalIgnores.
        It then writes out the excludeFile and will sync any path from there.
        """

        for each in self._getOffsteps():
            self.globalIgnores.append(each)
        #print 'Ignores set to: \n%s' % self.globalIgnores
        if sys.platform == 'win32':
            outfile = open(self.excludeWinFilePath, "w")
        else:
            outfile = open(self.excludeFile, "w")
            
        for eachIgnore in self.globalIgnores:
            outfile.write('%s\n' % eachIgnore)
        for eachInvalidType in invalidTypes:
            outfile.write('%s\n' % eachInvalidType)
        for eachExclude in self.excludeList:
            eachExclude = '/'.join(eachExclude.split('/')[1:])
            outfile.write('%s\n' % eachExclude)
        outfile.close()

    def _checkTypes(self):
        """
        Internal method to fail the sync button push if no type is selected at all.
        """
        self.numTypesOn = []
        for eachType in self.typeBoxes:
            if eachType.isChecked():
                self.numTypesOn.append(eachType)
        if len(self.numTypesOn) == 0:
            return False
        else:
            return True

    def _syncNow(self):
        """
        The main method to process the sync
        """
        self.goButton.setText('SYNC IN PROGRESS...')
        self.goButton.setStyleSheet('QPushButton {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
        if not self._checkTypes():
            self.goButton.setText('SYNC NOW..')
            self.goButton.setStyleSheet('QPushButton {background-color: green; border: 2px solid 1 ; border-radius: 6px;}')
            self.reply = QMessageBox.question(self, 'Nope!', "No types are selected. Try again", QMessageBox.Ok)
        else:
            if sys.platform == 'win32':
                self.src        = '\"/cygdrive/%s\"' % ''.join(self.sourceFolder.replace('\\', '/').split(':')).lower()
                if self.localXfer.isChecked():
                    self.local  = '/cygdrive/'
                    self.dest   = '\"%s%s\"' % (self.local, ''.join(self.destinationFolder.replace('\\', '/').split(':')).lower())
                else:
                    self.local  = ''
                    self.dest   = '\"%s%s\"' % (self.local, self.destinationFolder.replace('\\', '/').lower())
            else: ## Darwin
                self.local      = ''
                self.dest       = self.destinationFolder.lower()
                self.src        = self.sourceFolder.lower()

            ## now setup the extra user selected flags
            ## http://linux.about.com/library/cmd/blcmdl1_rsync.htm
            ## Defaults;
            ## r = recurse into directories
            ## a = archive mode
            ## L =  copy the referent of symlinks
            ## l = copy symlinks as symlinks
            ## t = preserve times
            ## x = don't cross filesystem boundaries
            ## P = equivalent to --partial --progress
            ## u = update only (don't overwrite newer files)
            
            self.extraOptions = '-update -ratxLluP'
            if self.verbose.isChecked():
                self.extraOptions = '%sv' % self.extraOptions
            if self.compress.isChecked():
                self.compressOn = '%sz' % self.extraOptions
            if self.showProgress.isChecked():
                self.extraOptions = '--progress %s' % self.extraOptions
    
            self.extraOptions = '%s --force ' % self.extraOptions
            if self.dryRun.isChecked():
                self.extraOptions = '%s --dry-run' % self.extraOptions        
                
            ## Now for final bit. If list only we have to make sure we don't put a path for the source. 
            if self.listOnly.isChecked():
                self.src = ''
                ## lemonskys admin needs a Capital A
                if 'administrator' in self.dest:
                    self.dest = self.dest.replace('administrator', 'Administrator')
                #print self.rsyncLineDebugger
                self.rsyncLineDebugger = "rsync %s --exclude-from=\"%s\" -e \"ssh -p %s\" %s %s" % (self.extraOptions, self.excludeFile, int(self.portNumber.value()),'LIST SERVER ONLY', self.dest)
            else:
                ## lemonskys admin needs a Capital A
                if 'administrator' in self.dest:
                    self.dest = self.dest.replace('administrator', 'Administrator')
                #print self.rsyncLineDebugger
                self.rsyncLineDebugger = "rsync %s --exclude-from=\"%s\" -e \"ssh -p %s\" %s %s" % (self.extraOptions, self.excludeFile, int(self.portNumber.value()), self.src, self.dest)

            self.reply = QMessageBox.question(self, 'Continue?', "Are you sure you want to sync:\n%s" % self.rsyncLineDebugger, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if self.reply == QMessageBox.Yes:
                
                ## start a subprocess so we can use the mainUI window for all syn processes
                print 'Starting sync now....'
                if sys.platform == 'darwin':
                    cmd = "/usr/local/bin/rsync %s --exclude-from=\"%s\" -e \"ssh -p %s\" \"%s\" \"%s\"" % (self.extraOptions, self.excludeFile, int(self.portNumber.value()), self.src, self.dest)
                else:
                    cmd = "rsync %s --exclude-from=\"%s\" -e \"ssh -p %s\" \"%s\" \"%s\"" % (self.extraOptions, self.excludeFile, int(self.portNumber.value()), self.src, self.dest)
                p = subprocess.Popen(cmd, cwd=None, shell=True, bufsize=4096)
                
                # Wait until process terminates
                while p.poll() is None:
                    time.sleep(0.5)
                
                # It's done
                print "Finished transfer...., ret code:", p.returncode
                self.goButton.setText('SYNC COMPLETED... click to resync')
                self.goButton.setStyleSheet('QPushButton {background-color: yellow; border: 2px solid 1 ; border-radius: 6px;}')
                             
            else:
                self.goButton.setText('SYNC NOW..')
                self.goButton.setStyleSheet('QPushButton {background-color: green; border: 2px solid 1 ; border-radius: 6px;}')
                print 'User cancelled sync...'
            
            if self.removeExclude.isChecked():
                if sys.platform == 'win32':
                    os.remove(self.excludeWinFilePath)
                else:
                    os.remove(self.excludeFile)

            if self.playFinishSound.isChecked():
                os.system("start T:/software/lsapipeline/tools/itsdone.wma")

    def _pickleWriteFile(self, filePath, data):
        """
        Will write out the dictionary provided using cpickle
        @parm writeDict: the dictionary to write out
        @type writeDict: dictionary
        """
        if not '.txt' in filePath:
            filePath = '%s.txt' % filePath
            
        with open(filePath, "w") as fp:
            pickle.dump(data, fp)

    def _saveDialog(self):
        """
        Creates a save dialog window and returns the path of the save file name.
        Note this is just another way of doing this as an example
        """
        self.myDiag = QFileDialog()
        if not os.path.isdir(self.filePaths):
            os.mkdir(self.filePaths)
        self.myDiag.setDirectory(self.filePaths)
        self.myDiag.setNameFilters("Text files (*.txt)")
        self.myDiag.setDefaultSuffix('.txt')
        self.myDiag.setAcceptMode(QFileDialog.AcceptSave)
        
        return self.myDiag.getSaveFileName()

    def _openDialog(self):
        """
        Creates a save dialog window and returns the path of the save file name.
        Note this is just another way of doing this as an example
        """
        if not os.path.isdir(self.filePaths):
            os.mkdir(self.filePaths)
        self.myDiag = QFileDialog()
        self.myDiag.setDirectory(self.filePaths)
        self.myDiag.setNameFilters("Text files (*.txt)")
        
        return self.myDiag.getOpenFileName()

    def _pickleReadFile(self, filePath):
        """
        The cpickle reader to handle reading the cpickled file.
        This checks the dictionary keys returned from the read in the the data and sets the QLineInputs as needed.
        """
        with open(filePath, "rb") as fp:
            self.data = pickle.load(fp)
        for key,var in self.data.items():
            if key == 'source':
                self.sourceInput.setText(var)
                self._cleanCheckboxes()
                self.doTypeCheckboxes()
            if key == 'local':
                if var  =='True':
                    self.localXfer.setChecked(True)
                else:
                    self.localXfer.setChecked(False)
            if key == 'destination':
                self.destInput.setText(var)
            if key == 'port':
                self.portNumber.setValue(int(var))

    def _saveLayout(self):
        """
        The cpickle writer. This writes out the dictionary correctly for loading back in as a dictionary.
        This avoids having to scan the entire text file for data and makes it easier to handle the data
        """
        self.writeConfig = {}       
        self.writeConfig['source'] = str(self.sourceInput.text())
        self.writeConfig['destination'] = str(self.destInput.text())
        self.writeConfig['port'] = str(int(self.portNumber.value()))
        if self.localXfer.isChecked(): ## Doing this because it wasn't returning true or false so querying it and then hard setting the dict value.
            self.writeConfig['local'] = 'True'
        else:
            self.writeConfig['local'] = 'False'
        self.getSavePath = self._saveDialog()
        self.write = self._pickleWriteFile(self.getSavePath, self.writeConfig)

    def _loadLayout(self):
        """
        The loader which calls the _pickleReadFile method
        """
        self.getOpenPath = self._openDialog()
        self.open = self._pickleReadFile(self.getOpenPath)
