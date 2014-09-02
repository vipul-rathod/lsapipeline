####PYTHON IMPORTS###########################################
from functools import partial

import sys, os, time, subprocess, sip, getpass, math, shutil

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

import Widget_hr as HR
##############################################################

#I:/lsapipeline/XFER/LemonSky/OUT TO LEMONSKY/EPISODE DELIVERY/EP106/ANIMATIC/AUDIO/SHOTS/DELIVERY/04APR14

class AudioFileManagement(QWidget):
    def __init__(self, defaultSource = '', parent = None):
        QWidget.__init__(self, parent)
        self.setWindowTitle('Audio File Processing')
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
        self.fileBoxes = []
        
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
        self.sourceInput.textChanged.connect(self.doFileCheckboxes)
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
        
        self.goButton = QPushButton('Transfer Audio Files To Episode Folders')
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
            self.goButton.setText('Transfer Audio Files To Episode Version Folders')
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
        Process all the folders/files found into checkboxes for processing
        """ 
        ## try to get the epNumber from a file
        epNum = str(os.listdir(self.sourceInput.text())[0].split('_')[0])
        if epNum == '.DS' or epNum == '.DS_Store':
            getFiles = os.listdir(self.sourceInput.text())
            #print getFiles
            
            for each in getFiles:
                if ".wav" in each:
                    epNum = each.split('_')[0]
        #print 'I AM A BAD NAUGHTY VARIABLE!: %s' % epNum

        if epNum:
            self.epNumber.setText(epNum)
            
        if self.fileBoxes != []:
            for each in self.fileBoxes:
                each.setParent(None)
                sip.delete(each)
                each = None

        self.files = []
        self.fileBoxes = []
       
        ## First add the ALL checkbox
        self.ALL = QCheckBox(self)
        self.ALL.setChecked(False)
        self.ALL.setText('ALL') 
        self.ALL.toggled.connect(self._toggleAll)
        
        self.fileBoxes.append(self.ALL)
        self.fileLayout.addWidget(self.ALL, 0, 0)
        
        ## Now process the folder and add the folders found as checkboxes.
        try:
            if myPath:
                if sys.platform == 'win32':
                    self.sourceFolder = myPath.replace('/', '\\')
                else:
                    self.sourceFolder = myPath
            else:
                self.sourceFolder = str(self.sourceInput.text())
                
            for eachFile in os.listdir(self.sourceFolder):
                if eachFile.endswith('.wav'):
                    self.files.append(eachFile)
        except :
            self.files =  ['No wav files found...']

        self.colCount = 10
        r = 1
        c = 1
        for eachType in sorted(self.files):
            self.fileCheckBox = QCheckBox(self)
            self.fileCheckBox.setChecked(False)
            self.fileCheckBox.setText(eachType)
            self.fileBoxes.append(self.fileCheckBox)
            if c == self.colCount:
                r = r + 1
                c = 1
            self.fileLayout.addWidget(self.fileCheckBox, r, c)
            c = c + 1

    def _browseDialog(self, dest = False):
        """
        This opens up a QFileDialog hard set to browse into the assets folder by default. 
        @param dest: To set if you are setting the destination input or the source input
        @type dest: Boolean 
        """
        try:
            if sys.platform == 'win32':
                myPath = QFileDialog(self, 'rootDir', 'O:/EPISODE DELIVERY').getExistingDirectory().replace('\\', '/')
            else:
                myPath = QFileDialog(self, 'rootDir', '/Volumes/LemonSky/OUT TO LEMONSKY/EPISODE DELIVERY').getExistingDirectory().replace('\\', '/')
        except :
            myPath = QFileDialog(self, 'rootDir', '').getExistingDirectory().replace('\\', '/')

        ## try to get the epNumber from a file
        epNum = os.listdir(myPath)[0].split('_')[0]
        if epNum:
            self.epNumber.setText(epNum)
        self.sourceInput.setText(myPath)
        self.sourceFolder = str(myPath)
        self.doFileCheckboxes(myPath)
                 
    def _versionUp(self, path):
        return int(max(os.listdir(path)).split('.v')[-1].split('.wav')[0]) + 1 
    
    def addAudioToShotgun(self, epName, shotName):
        """
        Function to add the audio asset to shotgun correctly for tasks etc and the pipeline to see it
        """
        self.epName     = epName
        self.shotName   = shotName
        self.audioName  = "%s" % (self.shotName)
        self.exists     =  self.sgsrv.find_one('CustomEntity03',  filters = [["code", "is", self.audioName]], fields=['code', 'tasks'])
        if not self.exists:
            self.sgsrv.create('CustomEntity03', 
                            {'project': {'type':'Project','id':66},
                             'code': self.audioName, 
                             'task_template' : {'type':'TaskTemplate', 'id' : 44},
                             'sg_status_list' : 'snd',
                             'updated_by' : {'type' : 'HumanUser', 'id' : 53}
                             })
        else:
            self.sgsrv.update('CustomEntity03', 
                            self.exists['id'],
                            {'project': {'type':'Project','id':66},
                             'code': self.audioName, 
                             'sg_status_list' : 'rkdip'
                             })
            ## Now update the task asssociate with it to be republished!
            task_id = self.exists['tasks'][0]['id']
            data = {
                    'sg_status_list':'artkup' 
                    }
            asset = self.sgsrv.update("Task", task_id, data)

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
                self.processAudioFolder()
    
    def processAudioFolder(self):
        """
        Function to copy over all the audio files from a single output folder into the correct locations for
        the bubblebathbay IDrive audios folders
        @param epNum: The episode name  
        @param pathToFolder: The path to the folder full of wav files you want to copy over.
        @type pathToFolder: String
        @type epNum: String
        NOTE: this tool has been written around the following audio output naming convention from TOONBOOM
        ep106_sh001.wav
        ep106_sh002.wav
        ep106_sh002_A.wav
        """
    
        if self.epNumber.text() !=  'ep':
            for each in self.fileBoxes:
                if each.isChecked() and each.text() != 'ALL':
                    ## We will always start with a base version number of 0 as the audio files from Toonboom
                    ## Do NOT have any versioning...Therefore iteration folders from toonboom can be correctly versioned into
                    ## the publish wav folders without freaking out....
                    self.vNum = '000'
                    self.epName = self.epNumber.text()
                    self.shotNum = each.text().split('.wav')[0]
                    
                    if sys.platform == 'win32':
                        self.shotWavDir = 'I:/lsapipeline/audios/%s/%s/WAV/publish/wav/' % ( self.epName, self.shotNum)
                    else:
                        self.shotWavDir = '/Volumes/lsapipeline/audios/%s/%s/WAV/publish/wav/' % ( self.epName, self.shotNum)
                        
                    self.shotWavFileName = '%s_AUD.v%s.wav'  %  (self.shotNum, self.vNum)
                    self.finalPath = '%s%s' % (self.shotWavDir, self.shotWavFileName)       
                    
                    ## Check for folder, if it doesn't exist make it
                    if not os.path.isdir(self.shotWavDir):
                        os.makedirs(self.shotWavDir)
                    
                    if self.makeSGEntries.isChecked():
                        print 'Adding audio to shotgun... %s: ' % self.shotWavFileName
                        self.addAudioToShotgun(self.epName, self.shotNum)
                    
                    ## Now check for existing file, if so version it up just in case so we don't even delete.
                    if os.path.isfile(self.finalPath):
                        newVersNum =  self._versionUp(self.shotWavDir)
                        if newVersNum <= 10:
                            self.vNum = '00%s' %newVersNum
                        elif newVersNum <= 100:
                            self.vNum = '0%s' %newVersNum
                        else:
                            self.vNum = '%s' %newVersNum
                        ## Now update the name and path vars as final.
                        self.shotWavFileName = '%s_AUD.v%s.wav'  %  (self.shotNum, self.vNum)
                        self.finalPath = '%s%s' % (self.shotWavDir, self.shotWavFileName)
                    
                    ## Now get the original path for the audio file we are copying.
                    originalPath = '%s\\%s' % (self.sourceFolder, each.text())
                
                    ## Now perform the copy.
                    shutil.copyfile(originalPath, self.finalPath)
                    #p = subprocess.Popen(cmd, cwd=None, shell=True, bufsize=4096)
                    # Wait until process terminates
                    #while p.poll() is None:
                     #   time.sleep(0.5)
                    print 'Copied file: %s  to \t%s' % (each.text(), self.finalPath)
            
            print 'Finished processing files'
            self.goButton.setText('COMPLETED... click to do over...')
            self.goButton.setStyleSheet('QPushButton {background-color: yellow; border: 2px solid 1 ; border-radius: 6px;}')
        else:
            self.goButton.setText('Invalid Ep Number... click to do over...')
            self.goButton.setStyleSheet('QPushButton {background-color: blue; border: 2px solid 1 ; border-radius: 6px;}')
            print 'You must set a valid episode number!!!'