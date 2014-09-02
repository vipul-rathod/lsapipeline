####PYTHON IMPORTS###########################################
from functools import partial

import sys, os, time, subprocess, sip, getpass, math, shutil, getopt

print sys.platform
try:
    if sys.platform == 'win32':
        if 'T:/software/python-api' not in sys.path:
            sys.path.append('T:/software/python-api/')
        if 'T:/software/studio/install/core/python' not in sys.path:
            sys.path.append('T:/software/studio/install/core/python')
        if 'C:/cygwin32/bin/' not in sys.path:
            sys.path.append('C:/cygwin32/bin/')
        if 'C:/cygwin/bin/' not in sys.path:
            sys.path.append('C:/cygwin/bin/')
        if 'E:/cygwin/bin/' not in sys.path:
            sys.path.append('E:/cygwin/bin/')
        if '/cygdrive/t/software/lsapipeline/tools' not in sys.path:
            sys.path.append('/cygdrive/t/software/lsapipeline/tools')
        if '/cygdrive/t/software/python-api' not in sys.path:
            sys.path.append('/cygdrive/t/software/python-api')
        if '/cygdrive/t/software/bubblebathbay' not in sys.path:
            sys.path.append('/cygdrive/t/software/bubblebathbay')
        if '/cygdrive/t/software/studio/install/core/python' not in sys.path:
            sys.path.append('/cygdrive/t/software/studio/install/core/python')
        if '/cygdrive/c/Python27/Lib/site-packages' not in sys.path:
            sys.path.append('/cygdrive/c/Python27/Lib/site-packages')
        if '/cygdrive/c/cygwin32/bin' not in sys.path:
            sys.path.append('/cygdrive/c/cygwin32/bin')
    elif sys.platform == 'cygwin':
        if 'T:/software/python-api' not in sys.path:
            sys.path.append('T:/software/python-api/')
        if 'T:/software/studio/install/core/python' not in sys.path:
            sys.path.append('T:/software/studio/install/core/python')
        if 'C:/cygwin32/bin/' not in sys.path:
            sys.path.append('C:/cygwin32/bin/')
        if 'C:/cygwin/bin/' not in sys.path:
            sys.path.append('C:/cygwin/bin/')
        if 'E:/cygwin/bin/' not in sys.path:
            sys.path.append('E:/cygwin/bin/')
        if '/cygdrive/t/software/lsapipeline/tools' not in sys.path:
            sys.path.append('/cygdrive/t/software/lsapipeline/tools')
        if '/cygdrive/t/software/python-api' not in sys.path:
            sys.path.append('/cygdrive/t/software/python-api')
        if '/cygdrive/t/software/bubblebathbay' not in sys.path:
            sys.path.append('/cygdrive/t/software/bubblebathbay')
        if '/cygdrive/t/software/studio/install/core/python' not in sys.path:
            sys.path.append('/cygdrive/t/software/studio/install/core/python')
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

import Widget_hr as HR
try:
    import sgtk
except:
    print'FAILED TO IMPORT sgtk !!!! NOT GOOD !!!'
    pass
##############################################################

#I:/lsapipeline/XFER/LemonSky/OUT TO LEMONSKY/EPISODE DELIVERY/EP106/ANIMATIC/AUDIO/SHOTS/DELIVERY/04APR14

class PublishMayaAudio(QWidget):
    def __init__(self, defaultSource = 'I:/lsapipeline/audios/', parent = None):
        QWidget.__init__(self, parent)
        self.setWindowTitle('Audio Publishing Tool')
        self.parent = parent
        ## Connect to shotgun
    
        from shotgun_api3 import Shotgun

        ## Instance the api for talking directly to shotgun. 
        base_url    = "http://bubblebathbay.shotgunstudio.com"
        script_name = 'audioUploader'
        api_key     = 'bbfc5a7f42364edd915656d7a48d436dc864ae7b48caeb69423a912b930bc76a'
        
        self.sgsrv = Shotgun(base_url = base_url , script_name = script_name, api_key = api_key, ensure_ascii=True, connect=True)
        
        ## Get the user name
        self.user = getpass.getuser()

        ## Define the variable for the source folder and destination folder (local and remote as it were)
        self.sourceFolder = defaultSource or ''
        self.fileBoxes = {}
        
        ## Build the UI
        self.mainLayout = QVBoxLayout(self)
        
        self.epNumLayout = QHBoxLayout()
        self.epNumLabel = QLabel('EpNum:')
        self.epNumber = QLineEdit('', self)
        self.epNumber.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
        self.epNumber.textChanged.connect(self.epTextChange)   
        self.epNumber.setText('ep')
        
        self.epNumLayout.addWidget(self.epNumLabel)
        self.epNumLayout.addWidget(self.epNumber)

        ## Set the layout for the source text input and browse button        
        self.pathLayout = QHBoxLayout(self)
        self.sourceLabel = QLabel('Set Src Path:')
        ## Define the widgets for this layout
        self.sourceInput = QLineEdit(self)
        if self.sourceFolder:
            self.sourceInput.setText(self.sourceFolder)
        self.sourceInput.textChanged.connect(partial(self.doFileCheckboxes))
        self.browseButton = QPushButton('Browse')
        self.browseButton.released.connect(partial(self._browseDialog, dest = False))
        ## Add the widgets to the layout
        self.pathLayout.addWidget(self.sourceLabel)
        self.pathLayout.addWidget(self.sourceInput)       
        self.pathLayout.addWidget(self.browseButton)        
        
        self.optionsLayout = QHBoxLayout(self)
        self.makeSGEntries = QCheckBox(self)
        self.makeSGEntries.setChecked(True)
        self.makeSGEntries.setText('Make SGun Entries?')
        
        self.goButton = QPushButton('Publish Audio Files')
        self.goButton.setStyleSheet('QPushButton {background-color: green; border: 2px solid 1 ; border-radius: 6px;}')   
        self.goButton.clicked.connect(self._doit)
        
        self.optionsLayout.addWidget(self.makeSGEntries)
        self.optionsLayout.addWidget(self.goButton)
        
        self.split = HR.Widget_hr()
        self.mainLayout.addWidget(self.split)

        self.mainLayout.addLayout(self.epNumLayout)
        self.mainLayout.addLayout(self.pathLayout)
        self.mainLayout.addLayout(self.optionsLayout)
        
        ### Now do the check boxes for files....
        self.scrollLayout = QScrollArea(self)
        self.scrollLayout.setMinimumHeight(300)
        
        self.filesGroupBox = QGroupBox(self.scrollLayout)
        self.filesGroupBox.setFlat(True)
        
        self.scrollLayout.setWidget(self.filesGroupBox)
        self.scrollLayout.setWidgetResizable(True)
        
        self.fileLayout = QGridLayout(self.filesGroupBox)
        self.mainLayout.addWidget(self.scrollLayout)

    def epTextChange(self):
        if len(self.epNumber.text()) > 5:
            self.epNumber.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
            self.goButton.setStyleSheet('QPushButton {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')   
            self.goButton.setText('BAD EP NUMBER')
            self.goButton.setEnabled(False)
        elif self.epNumber.text() != 'ep' and len(self.epNumber.text()) == 5:
            self.epNumber.setStyleSheet('QLineEdit {background-color: green; border: 2px solid 1 ; border-radius: 6px;}')
            self.goButton.setStyleSheet('QPushButton {background-color: green; border: 2px solid 1 ; border-radius: 6px;}')   
            self.goButton.setText('Publish Audio Files')
            self.goButton.setEnabled(True)
        else:
            self.epNumber.setStyleSheet('QLineEdit {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
            self.goButton.setStyleSheet('QPushButton {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')   
            self.goButton.setText('BAD EP NUMBER')
            self.goButton.setEnabled(False)

    def _toggleAll(self):
        """
        A quick toggle for all the type checkboxes to on or off
        """
        for eachType in self.fileBoxes:
            if eachType.text() == 'ALL':
                if eachType.isChecked():
                    for eachSubType in self.fileBoxes:
                        if eachSubType.text() != 'ALL':
                            eachSubType.setChecked(True)
                else:
                    for eachSubType in self.fileBoxes:
                        if eachSubType.text() != 'ALL':
                            eachSubType.setChecked(False)
                
    def doFileCheckboxes(self, myPath = ''):
        """
        Process all the folders/files found into check boxes for processing
        """ 
        ## try to get the epNumber from a file
        epNum = os.listdir(self.sourceInput.text())[0].split('_')[0]
        if epNum:
            self.epNumber.setText(epNum)
            
        if self.fileBoxes != {}:
            for key, var in self.fileBoxes.items():
                key.setParent(None)
                sip.delete(key)
                key = None
        
        self.repaint()
        self.files      = []
        self.fileBoxes  = {}
       
        ## First add the ALL checkbox
        self.ALL = QCheckBox(self)
        self.ALL.setChecked(False)
        self.ALL.setText('ALL') 
        self.ALL.toggled.connect(self._toggleAll)
        
        self.fileBoxes[self.ALL] =  None
        self.fileLayout.addWidget(self.ALL, 0, 0)
        
        self.colCount = 10
        r = 1
        c = 1
        
        ## Now process the folder and add the folders found as check boxes.
        try:
            ## Scan the entire folder structure for audio files to publish
            if self.isRootFolderThere(rootFolder = self.sourceFolder):
                print '%s found processing now...' % self.sourceFolder
                for dirname, dirnames, filenames in os.walk(self.sourceFolder):
                    if dirname.endswith('\\wav'):
                        print  'Scanning %s now..' % dirname
                        print 'Files: %s' % os.listdir(dirname)
                        getMaxFile = max(os.listdir(dirname))
                        if getMaxFile: ## we have a folder with files in it...
                            if getMaxFile.endswith(".wav"):
                                pathToWav = os.path.join(dirname, getMaxFile)
                                self.fileCheckBox = QCheckBox(self)
                                self.fileCheckBox.setChecked(False)
                                self.fileCheckBox.setText(getMaxFile)
                                self.fileBoxes[self.fileCheckBox] = pathToWav.replace('\\', '/')
                                 
                                if c == self.colCount:
                                    r = r + 1
                                    c = 1
                                self.fileLayout.addWidget(self.fileCheckBox, r, c)
                                c = c + 1
                                print 'Adding %s to layout now..' % pathToWav
                        else:
                            print '%s is emtpy...' % dirname
            else:
                self.files =  ['No root folder found...']
        except:
            self.files =  ['No wav files found...']

    def _browseDialog(self, dest = False):
        """
        This opens up a QFileDialog hard set to browse into the assets folder by default. 
        @param dest: To set if you are setting the destination input or the source input
        @type dest: Boolean 
        """

        if sys.platform == 'win32':
            print 'OPENING WIN BROWSE DIALOG NOW...'
            myPath = QFileDialog(self, 'rootDir', self.sourceFolder).getExistingDirectory().replace('\\', '/')
        else:
            print 'OPENING %s BROWSE DIALOG NOW...' % sys.platform
            myPath = QFileDialog(self, 'rootDir', self.sourceFolder).getExistingDirectory().replace('\\', '/')

        ## try to get the epNumber from a file
        epNum = os.listdir(myPath)[0].split('_')[0]
        
        if epNum:
            self.epNumber.setText(epNum)
        
        self.sourceFolder = str(myPath)

        os.system('echo epNum: %s' % self.epNumber)
        os.system('echo sourceFolder: %s' % self.sourceFolder)
        os.system('echo final myPath: %s' % myPath)
        self.sourceInput.setText(myPath)
        
        #self.doFileCheckboxes(myPath)
        
            
                 
    def _versionUp(self, path):
        return int(max(os.listdir(path)).split('.v')[-1].split('.wav')[0]) + 1 
    
    def _writeMaFile(self, fileName, pathToWav, wavName, publishPath):
        ## Check the folder exists, if not make one now.
        if not os.path.isdir(os.path.dirname(self.publishPath)):
            os.makedirs(os.path.dirname(self.publishPath))
        
        self.header = [
        r'//Maya ASCII 2013ff10 scene',
        r'//Name: %s' % fileName,
        r'//Last modified: Tue, Jun 17, 2014 10:41:32 AM',
        r'//Codeset: 1252',
        r'requires maya "2013ff10";',
        r'requires "Mayatomr" "2013.0 - 3.10.1.11 ";',
        r'currentUnit -l centimeter -a degree -t film;',
        r'fileInfo "application" "maya";',
        r'fileInfo "product" "Maya 2013";',
        r'fileInfo "version" "2013 x64";',
        r'fileInfo "cutIdentifier" "201301140020-856945";',
        r'fileInfo "osv" "Microsoft Windows 7 Ultimate Edition, 64-bit Windows 7 Service Pack 1 (Build 7601)\n";',
        ]
        
        self.audioNode = [
                        '\n%s' % r'createNode audio -n "%s";' % wavName.replace('.', '_'),
                            '\t%s' % r'setAttr ".ef" 1000;',
                            '\t%s' % r'setAttr ".se" 1000;',
                            '\t%s' % r'setAttr ".f" -type "string" "%s";' % pathToWav,
                          ]
        
        self.footer = [
                       '\n%s' % r'// End of %s.ma' % fileName]
        
        ## Now write the ma file
        ## Fail if the version already exists
        pathToTextFile = publishPath
        if not os.path.isfile(pathToTextFile):
            outfile = open(pathToTextFile, "w")
            for eachLine in self.header:
                outfile.write('%s\n' % eachLine)
            for eachLine in self.audioNode:
                outfile.write('%s\n' % eachLine)
            for eachLine in self.footer:
                outfile.write('%s\n' % eachLine)
            
            outfile.close()
        else:
            ## Remove it because we are republishing the same version again.
            os.remove(pathToTextFile)
            ## Note we can just delete this file already and move on if needed.
            outfile = open(pathToTextFile, "w")
            for eachLine in self.header:
                outfile.write('%s\n' % eachLine)
            for eachLine in self.audioNode:
                outfile.write('%s\n' % eachLine)
            for eachLine in self.footer:
                outfile.write('%s\n' % eachLine)
            
            outfile.close()
    
    def _createPublish(self, publishPath, fileName, pathToWav, wavName, version_number, localPath, localPathMac, wavSGName, ctx):
        self.pathToWav      = pathToWav
        self.publishPath    = publishPath
        self.localPath      = localPath
        self.localPathMac   = localPathMac
        self.fileName       = fileName
        self.wavName        = wavName
        self.wavSGName      = wavSGName
        self.version_number = version_number


        data = {
                "code"          : self.wavSGName,
                "description"   : None,
                "name"          : self.wavSGName,
                "project"       : ctx.project,
                "entity"        : {'id': self.exists['id'], 'name': self.wavSGName, 'type': 'CustomEntity03'},
                "version_number": self.version_number,
                'path_cache'    : self.publishPath.replace('/', '\\'),
                'published_file_type' : {'type' : 'PublishedFileType', 'id': 1},
                'updated_by'    : {
                               'type' : 'HumanUser', 'id' : 53
                               },
                'path'         : {
                              'content_type': None,
                              'link_type': 'local',
                              'url': 'file:///%s' % self.publishPath.replace('/', '\\'),
                              "local_path": self.publishPath.replace('/', '\\'),
                              'local_path_linux': '',
                              'local_path_mac': '%s' % self.localPathMac,
                              'local_path_windows': '%s' % self.publishPath.replace('/', '\\'),
                              'local_storage': {'id': 1, 'name': 'primary', 'type': 'LocalStorage'},
                              'name': self.fileName,
                                }
                }
        
        self.sgsrv.create('PublishedFile', data)
        print 'Publish file created for %s' % self.wavSGName
    
    def _publishAudio(self):
        """
        Function to add the publish a maya audio file both making a maya file with an audio node and publishing this to shotgun as a version
        """
        for key, var in self.fileBoxes.items():
            if var:
                if key.isChecked():
                    ## Work out what we need for the creation of the ma file 
                    ## and the publish for shotgun
                    self.pathToWav      = var
                    if sys.platform == 'win32':
                        self.publishPath = var.replace('/publish/wav', '/publish/maya').replace('.wav', '.ma').replace('/', '\\')
                    self.localPath      = self.publishPath.split('I:')[-1]
                    self.localPathMac   = self.publishPath.replace('I:', '/_projects')
                    self.fileName       = str(key.text()).replace('.wav', '.ma')
                    self.wavName        = str(key.text())
                    self.wavSGName      = str(key.text().replace('_AUD', '').split('.')[0])
                    self.version_number = int(str(key.text()).split('.')[-2].split('v')[-1])
                    
                    ## Now register the publish with Shotgun
                    ## First find the audio on shotgun for processing. 
                    self.exists         =  self.sgsrv.find_one('CustomEntity03',  filters = [["code", "is", self.wavSGName]], fields=['code', 'tasks', 'id'])

                    if not self.exists:
                        print '%s has no shotgun entry! You should make sure this has been processed correctly before proceeding!!' % self.wavName

                    else:
                        ## now publish
                        tk = sgtk.sgtk_from_path("I:/lsapipeline/")
                        ctx = tk.context_from_path(self.publishPath)
                        
                        ## For existing check
                        ## CHECK FOR EXISTING PUBLISH WITH THE SAME VERSION NUMBER!!!!
                        findExisting = self.sgsrv.find_one('PublishedFile', filters = [["code", "is", self.wavSGName]], fields=['code', 'id', 'version_number', 'created_at', 'entity'])
                        if findExisting:
                            if findExisting['version_number'] == self.version_number:
                                print 'A PUBLISHED FILE FOR THIS VERSION ALREADY EXISTS SKIPPING! VERSION UP OR DELETE EXISTING SHOTGUN PUBLISH ENTRIES IF YOU NEED TO YOU SHOULDNT BUT YOU MIGHT!'
                                ## WRITE THE MA
                                ## Now write the ma file we are going to publish with the audio node created.
                                ## Note this will delete and re-make any ma files with the same name in the folder if they exist
                                self._writeMaFile(self.fileName, self.pathToWav, self.wavName, self.publishPath)
                            else:## This is a new version number
                                ## WRITE THE MA
                                ## Now write the ma file we are going to publish with the audio node created.
                                ## Note this will delete and re-make any ma files with the same name in the folder if they exist
                                self._writeMaFile(self.fileName, self.pathToWav, self.wavName, self.publishPath)
                                self._createPublish(publishPath = self.publishPath, fileName = self.fileName, pathToWav = self.pathToWav, wavName = self.wavName, version_number = self.version_number,
                                               localPath = self.localPath, localPathMac = self.localPathMac, wavSGName = self.wavSGName, ctx = ctx)
                        else:## nothing already exists so build a fresh publish
                            ## WRITE THE MA
                            ## Now write the ma file we are going to publish with the audio node created.
                            ## Note this will delete and re-make any ma files with the same name in the folder if they exist
                            self._writeMaFile(self.fileName, self.pathToWav, self.wavName, self.publishPath)
                            self._createPublish(publishPath = self.publishPath, fileName = self.fileName, pathToWav = self.pathToWav, wavName = self.wavName, version_number = self.version_number,
                                           localPath = self.localPath, localPathMac = self.localPathMac, wavSGName = self.wavSGName, ctx = ctx)
                        
        print 'Complete'
        self.goButton.setText('COMPLETE.. click to run again')
        self.goButton.setStyleSheet('QPushButton {background-color: green; border: 2px solid 1 ; border-radius: 6px;}')
        self.repaint()
        
    def _checkTypes(self):
        anythingChecked = False
        if self.fileBoxes:
            for each in self.fileBoxes:
                if each.isChecked():
                    anythingChecked = True
        return anythingChecked

    def _setINPROG(self):
        self.goButton.setText('IN PROGRESS...')
        self.goButton.setStyleSheet('QPushButton {background-color: red; border: 2px solid 1 ; border-radius: 6px;}')
        self.repaint()
        return True
        
    def _doit(self):
        if self._setINPROG():
            if not self._checkTypes():
                self.goButton.setText('OOPS..')
                self.goButton.setStyleSheet('QPushButton {background-color: darkred; border: 2px solid 1 ; border-radius: 6px;}')
                self.reply = QMessageBox.question(self, 'Nope!', "Nothing to transfer. Try selecting something and try again", QMessageBox.Ok)
            else:
                self._publishAudio()

    def isRootFolderThere(self, rootFolder):
        """
        Method used to check if root folder is valid or not
        """
        if not os.path.isdir(rootFolder):
            print 'No such root folder found.'
            return -1
        else:
            return 1


if __name__ == "__main__":
    app     = QApplication(sys.argv)
    myWin   = PublishMayaAudio()
    myWin.show()
    sys.exit(app.exec_())