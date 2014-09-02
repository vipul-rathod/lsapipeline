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
from shotgun_api3 import Shotgun
import urlparse
import urllib2, os


class DownloadPlaylist(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.setWindowTitle('Check Playlist local files...')
        
        ## Set base vars
        self.missingLocalFiles      = []
        self.missingLocalFilesDict  = {}
        self.onlineFilesDict        = {}
        self.tempSGFiles            = []
        self.badfiles               = []
        self.badfileBoxes           = []
        self.tempFileCheckBoxes     = []
        self.localFileCheckBoxes    = []
        self.playlist               = []
        
        ## Start the UI Build
        self.mainLayout = QVBoxLayout(self)
        
        self.allPlayLists = ''
        ## Instance the api for talking directly to shotgun. 
        base_url    = "http://bubblebathbay.shotgunstudio.com"
        script_name = 'audioUploader'
        api_key     = 'bbfc5a7f42364edd915656d7a48d436dc864ae7b48caeb69423a912b930bc76a'
        self.sgsrv  = Shotgun(base_url = base_url , script_name = script_name, api_key = api_key, ensure_ascii=True, connect=True)
        self.allPlayLists = []
        
        ### Now find the playlists from shotgun to use.
        self._populatePlaylists()

        self.playListLayout = QHBoxLayout(self)
        self.playListDropDown = QComboBox(self)
        self.playListDropDown.setMinimumWidth(200)
        self.playListDropDown.setMaximumHeight(25)
        
        self.playListSearchLabel = QLabel('Search')
        self.playListSearchInput = QLineEdit(self)
        self.playListSearchInput.textChanged.connect(self._searchDropDown)
        
        self.playListLayout.addWidget(self.playListDropDown)
        self.playListLayout.addWidget(self.playListSearchLabel)
        self.playListLayout.addWidget(self.playListSearchInput)
        
        self.checkForLocal = QPushButton('Check Local Files Exist...')
        self.checkForLocal.clicked.connect(self._checkFiles)
        self.checkForLocal.setStyleSheet("QPushButton {background-color: green}")
        
        self.downloadFilesButton = QPushButton('Click to download missing files...')
        self.downloadFilesButton.clicked.connect(self._processDownload)
        self.downloadFilesButton.setStyleSheet("QPushButton {background-color: green}")
        
        self.updateList()
        self.mainLayout.addLayout(self.playListLayout)
        self.mainLayout.addWidget(self.checkForLocal)
        self.mainLayout.addWidget(self.downloadFilesButton)

        self.downloadFilesButton.hide()

        
        ### Now do the check boxes for files....
        ### FILES TO LOCAL PROJECT FOLDER
        self.scrollLayout = QScrollArea(self)
        self.scrollLayout.setMinimumHeight(50)
        
        self.filesGroupBox = QGroupBox(self.scrollLayout)
        self.filesGroupBox.setTitle('Files to download to local drive')
        self.filesGroupBox.setFlat(True)
        
        self.scrollLayout.setWidget(self.filesGroupBox)
        self.scrollLayout.setWidgetResizable(True)
        
        self.fileLayout = QGridLayout(self.filesGroupBox)

        ### FILES TO LOCAL PROJECT FOLDER
        self.scrollLayout2 = QScrollArea(self)
        self.scrollLayout2.setMinimumHeight(50)
        
        self.filesGroupBox2 = QGroupBox(self.scrollLayout2)
        self.filesGroupBox2.setTitle('Files to download to temp folder')
        self.filesGroupBox2.setFlat(True)
        
        self.scrollLayout2.setWidget(self.filesGroupBox2)
        self.scrollLayout2.setWidgetResizable(True)
        
        self.tempFilesLayout = QGridLayout(self.filesGroupBox2)

        ### FILES TO LOCAL PROJECT FOLDER
        self.scrollLayout3 = QScrollArea(self)
        self.scrollLayout3.setMinimumHeight(50)
        
        self.filesGroupBox3 = QGroupBox(self.scrollLayout3)
        self.filesGroupBox3.setTitle('BAD FILES! Contact Co-Ord to fix.')
        self.filesGroupBox3.setFlat(True)
        
        self.scrollLayout3.setWidget(self.filesGroupBox3)
        self.scrollLayout3.setWidgetResizable(True)
        
        self.badFileCheckBoxLayout = QGridLayout(self.filesGroupBox3)

        self.mainLayout.addWidget(self.scrollLayout)
        self.mainLayout.addWidget(self.scrollLayout2)
        self.mainLayout.addWidget(self.scrollLayout3)

    def _populatePlaylists(self):
        self.pendingReview = self.sgsrv.find('Playlist', filters = [["sg_status", "is", 'rev']], fields=['code', 'created_at', 'versions'])
        self.delivered = self.sgsrv.find('Playlist', filters = [["sg_status", "is", 'dlvr']], fields=['code', 'created_at', 'versions'])
        
        if self.pendingReview:
            for eachPL in self.pendingReview:
                self.allPlayLists.append(eachPL)
        if self.delivered:
            for eachPL in self.delivered:
                self.allPlayLists.append(eachPL)

    def _clearLists(self):
        #os.system('echo clearing lists now...')
        if self.localFileCheckBoxes != []:
            for each in self.localFileCheckBoxes:
                try:
                    each.setParent(None)
                    sip.delete(each)
                    each = None
                except RuntimeError:
                    pass

        if self.tempFileCheckBoxes != []:
            for each in self.tempFileCheckBoxes:
                try:
                    each.setParent(None)
                    sip.delete(each)
                    each = None
                except RuntimeError:
                    pass
                
        if self.badfileBoxes != []:
            for each in self.badfileBoxes:
                try:
                    each.setParent(None)
                    sip.delete(each)
                    each = None
                except RuntimeError:
                    pass

    def _doFileCheckboxes(self):
        """
        Process all the files found into check boxes for processing
        """ 
        self._clearLists()
        self.badfileBoxes           = []
        self.tempFileCheckBoxes     = []
        self.localFileCheckBoxes    = []

        ## LOCAL DOWNLOAD
        ## First add the ALL checkbox
        self.ALL_Local = QCheckBox(self)
        self.ALL_Local.setChecked(False)
        self.ALL_Local.setText('Toggle All') 
        self.ALL_Local.toggled.connect(self._toggleAllLocal)
        self.fileLayout.addWidget(self.ALL_Local, 0, 0)
        
        self.colCount = 5
        r = 1
        c = 1
        for eachType in sorted(self.missingLocalFiles):
            self.fileCheckBox = QCheckBox(self)
            self.fileCheckBox.setChecked(True)
            self.fileCheckBox.setText(eachType)
            self.localFileCheckBoxes.append(self.fileCheckBox)
            if c == self.colCount:
                r = r + 1
                c = 1
            self.fileLayout.addWidget(self.fileCheckBox, r, c)
            c = c + 1

        ## TEMP FILES
        ## First add the ALL checkbox
        self.ALL_Temp = QCheckBox(self)
        self.ALL_Temp.setChecked(False)
        self.ALL_Temp.setText('Toggle All') 
        self.ALL_Temp.toggled.connect(self._toggleAllTemp)
        self.tempFilesLayout.addWidget(self.ALL_Temp, 0, 0)
        
        self.colCount = 5
        r = 1
        c = 1
        for eachType in sorted(self.tempSGFiles):
            self.fileCheckBox = QCheckBox(self)
            self.fileCheckBox.setChecked(True)
            self.fileCheckBox.setText(eachType)
            self.tempFileCheckBoxes.append(self.fileCheckBox)
            if c == self.colCount:
                r = r + 1
                c = 1
            self.tempFilesLayout.addWidget(self.fileCheckBox, r, c)
            c = c + 1
        
        ## BAD FILES
        self.colCount = 5
        r = 1
        c = 1
        for eachType in sorted(self.badfiles):
            self.fileCheckBox = QLabel(self)
            self.fileCheckBox.setText(eachType)
            self.fileCheckBox.setStyleSheet("QLabel {background-color:red; text-align:center;}")
            self.badfileBoxes.append(self.fileCheckBox)
            if c == self.colCount:
                r = r + 1
                c = 1
            self.badFileCheckBoxLayout.addWidget(self.fileCheckBox, r, c)
            c = c + 1
            
        self.repaint()

    def _toggleAllTemp(self):
        for eachBox in self.tempFileCheckBoxes:
            if self.ALL_Temp.isChecked():
                eachBox.setChecked(True)
            else:
                eachBox.setChecked(False)

    def _toggleAllLocal(self):
        for eachBox in self.localFileCheckBoxes:
            if self.ALL_Local.isChecked():
                eachBox.setChecked(True)
            else:
                eachBox.setChecked(False)       

    def _searchDropDown(self):
        self.playListDropDown.clear() 
        for eachPlayList in sorted(self.allPlayLists):
            if str(self.playListSearchInput.text()) in eachPlayList['code']:
                self.playListDropDown.addItem(eachPlayList['code'])

    def updateList(self):
        self.playListDropDown.clear()        

        for eachPlayList in sorted(self.allPlayLists):
            self.playListDropDown.addItem(eachPlayList['code'])

    def _setPlaylist(self):
        """
        Set the playlist from the current pulldown
        """
        for eachPlayList in self.allPlayLists:
            if eachPlayList['code'] == self.playListDropDown.currentText():
                print 'Fetching versions for %s now..' % eachPlayList['code']
                self.playlist       = eachPlayList
            else:
                pass

    def _getVersionInfo(self, versionData):
        """
        Function to process the version data from shotgun
        If we are under darwin osx change the path to local to match our project drives so the path to local is correct for osx
        """
        getVersInfo = self.sgsrv.find_one('Version', filters = [["id", "is", versionData['id']]], fields = ['code', 'sg_path_to_movie', 'sg_uploaded_movie'])
        pathToLocal = getVersInfo['sg_path_to_movie']    
        
        ## Process the osx pathToLocal
        if sys.platform == 'darwin':
            if pathToLocal:
                pathToLocal = pathToLocal.replace('I:', '/_projects').replace("\\", "/")
                getVersInfo['sg_path_to_movie'] = pathToLocal 
        
        ## Now process the URL
        try:
            url = getVersInfo['sg_uploaded_movie']['url']
        except TypeError:
            url = None

        return getVersInfo['code'], pathToLocal, url, getVersInfo

    def _checkFiles(self):
        self._clearLists()
        os.system('cls')
        #os.system('echo Checking Playlist: %s \n' % self.playListDropDown.currentText())
        os.system('echo Looking for files on local drive....\n')
        self.tempSGFiles            = []
        self.missingLocalFiles      = []
        
        self.missingLocalFilesDict  = {}
        self.onlineFilesDict        = {}

        self.badfiles               = []
        self.getVersions            = []
        self.playList               = []
        self.missingUploadedMoveMsg = 'MISSING UPLOADED MOVIE. THIS NEEDS TO BE FIXED. PLEASE CONTACT CO-ORD ABOUT THIS!'
        ######################################################
        ## Set the state for the UI into checking for files...
        self.checkForLocal.setText('Checking files...')
        self.checkForLocal.setStyleSheet("QPushButton {background-color: yellow}")
        self.downloadFilesButton.hide()
        self.repaint()
        ######################################################
        
        ######################################################
        ## Scan each path to local and then check for existing files.
        self._setPlaylist()
        self.getVersions    = self.playlist['versions']
        
        if self.getVersions:
            for eachVer in self.playlist['versions']:
                ######################################################
                ## Fetch the version information from shotgun
                versionName, pathToLocal, url, getVersInfo = self._getVersionInfo(eachVer)
                print 'Checking \t%s now...' % versionName
                
                ######################################################
                ## If we have a valid path to local in shotgun....
                if pathToLocal and 'B:' not in pathToLocal and 'Shotgun' not in pathToLocal:
                    print 'Path: \t\t%s' % pathToLocal
                    
                    ## Now check to see if the path to the file is true or not. 
                    pathExists = os.path.isfile(pathToLocal)
                    os.system('echo EXISTS?: \t%s' % pathExists)
                    
                    ## If it doesn't exist mark this file for download to local path
                    if not pathExists:
                        ## Check if we can download this file from an uploaded movie!?!
                        if url:
                            os.system('echo DL: \t\t%s\n' % versionName)
                            os.system('echo .')
                            
                            ## Add the file to the list for the check-boxes, and the dictionary used for download info
                            if eachVer['name'] not in self.missingLocalFiles:
                                self.missingLocalFiles.append(versionName)## For the check-boxes
                            self.missingLocalFilesDict[versionName] = getVersInfo ## For the down loader
                        else:
                            os.system('echo %s %s' % (versionName, self.missingUploadedMoveMsg))
                            os.system('echo .')
                            
                            ## Add the file to the bad list of files as we are missing an online uploaded file to download.
                            if eachVer['name'] not in self.badfiles:
                                self.badfiles.append(eachVer['name'])
                        
                    ## If the file does exist on the local HD, check to see if we have to resume it or not.
                    ## Check the file sizes match if they don't add to missing files..
                    else: 
                        if url:
                            ## Find the online file size and compare it against the local file size on disk
                            u               = urllib2.urlopen(url)
                            meta            = u.info()
                            onlinefileSize  = int(meta.getheaders("Content-Length")[0])
                            localmeta       = os.stat('%s' % pathToLocal)
                            
                            if not localmeta.st_size == onlinefileSize:
                                os.system('echo Filesize mismatch for %s marking for download again..\n' % pathToLocal.split(os.sep)[-1])
                                os.system('echo Size On Disk: %.8f \tSize On SGun: %.8f' % (float(localmeta.st_size)/1000000, float(onlinefileSize)/1000000))
                                #print localmeta.st_size #17,892,757 bytes
                                os.system('echo .')
                                
                                ## Add the file to the list for the check-boxes, and the dictionary used for download info
                                if eachVer['name'] not in self.missingLocalFiles:
                                    self.missingLocalFiles.append(versionName)## For the check-boxes
                                
                                self.missingLocalFilesDict[versionName] = getVersInfo ## For the down loader
                        
                        else:
                            os.system('echo %s %s' % (versionName, self.missingUploadedMoveMsg))
                            os.system('echo .')
                            if eachVer['name'] not in self.badfiles:
                                self.badfiles.append(eachVer['name'])
                else:
                    ## We don't have a valid path in shotgun to a local file!
                    if url:
                        ## But we do have a url to an uploaded movie...
                        os.system('echo No local path found in shotgun field for %s. File will be saved to Temp folder...' % versionName)
                        os.system('echo .')
                        
                        ## Add the file to the list for the check-boxes, and the dictionary used for download info
                        
                        if eachVer['name'] not in self.tempSGFiles:
                            self.tempSGFiles.append(getVersInfo['code']) ## for the check-boxes
                        self.onlineFilesDict[getVersInfo['code']] = getVersInfo ## For the down loader
                    else:
                        ## OOPS this is missing both a local path and uploaded movie in shotgun :( :( :( 
                        os.system('echo %s MISSING UPLOADED MOVIE AND LOCAL PATH!!!! THIS NEEDS TO BE FIXED. PLEASE CONTACT CO-ORD ABOUT THIS!' % versionName)
                        os.system('echo .')
                        
                        ## Add the file to the list of bad files.
                        self.badfiles.append(eachVer['name'])
        else:
            print '%s has NO versions! This playlist is empty! PLEASE CONTACT CO-ORD ABOUT THIS!' % self.playlist['code']
        
        ########################################
        ## NOW CHECK THE FINAL LISTS AND SET THE UI INTO THE CORRECT STATE
        ## EITHER READY FOR DOWNLOAD OR START A NEW CHECK                                         
        if self.missingLocalFiles or self.tempSGFiles or self.badfiles:
           self.downloadFilesButton.show()
           self.checkForLocal.setText('Check Complete...click to check again...')
           self.checkForLocal.setStyleSheet("QPushButton {background-color: orange}")
           
           ## Now process the check box lists...
           self._doFileCheckboxes()
                       
        else:
            os.system('echo CHECKS OUT OKAY!! ALL FILES EXIST FOR THIS PLAYLIST.....\n')
            self.checkForLocal.setText('Check Local File Exist...')
            self.checkForLocal.setStyleSheet("QPushButton {background-color: green}")
           
            ## Now clear out all the checkboxes.           
            self._clearLists()       

    def _downloadFile(self, pathToLocal, url):
        """
        Main download function
        """
        fileName    = pathToLocal.split(os.sep)[-1]
        u           = urllib2.urlopen(url)
        meta        = u.info()
        file_size   = int(meta.getheaders("Content-Length")[0])

        #os.system('cls')
        os.system('echo Downloading: %s \tSize: %.2f MB\n' % (fileName, float(file_size)/1000000))
        
        f               = open(pathToLocal, 'wb')
        file_size_dl    = 0
        block_sz        = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break                                 
            file_size_dl += len(buffer)
            f.write(buffer)
            status = r".........%20s: %34.2f MB [%3.2f%%]" % (fileName, float(file_size_dl)/1000000, file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
            print status,
        f.close()
        os.system('echo \n')
        os.system('echo Download Complete....')

    def _resumeDownload(self, pathToLocal, url, localSize, totalSGFileSize):
        """
        Resume download function
        """
        fileName    = pathToLocal.split(os.sep)[-1]
        req         = urllib2.Request(url)
        remainingB  = totalSGFileSize - localSize
                
        ## Now set the header for the range
        req.headers["Range"] = "bytes=%s-%s" % (localSize, totalSGFileSize)
        
        u           = urllib2.urlopen(req) #create the connection
        meta        = u.info()
        file_size   = int(meta.getheaders("Content-Length")[0])

        #os.system('cls')
        os.system('echo Resuming: %s \tSize: %.2f MB \tRemaining: %.2f MB\n' % (fileName, float(totalSGFileSize)/1000000, float(remainingB)/1000000))
        
        f               = open(pathToLocal, 'ab')
        file_size_dl    = 0
        block_sz        = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break                                 
            file_size_dl += len(buffer)
            ## Now write to the file..
            f.write(buffer)
            
            ## Now print the satus
            status = r".........%20s: %34.2f Mb [%3.2f%%]" % (fileName, float(file_size_dl)/1000000, file_size_dl * 100. / totalSGFileSize)
            status = status + chr(8)*(len(status)+1)
            print status,
        f.close()
        os.system('echo \n')
        os.system('echo Download Complete....')         
        
    def _preDownload(self, pathToLocal, url):
        """
        Function to check if the file exists on the local hd
        if it doesn't match that of the online file
        """
        
        ## First check to see if the file exists!
        if not os.path.isfile(pathToLocal):
            ## Do a full download of the file now.
            self._makeDirectories(pathToLocal)
            self._downloadFile(pathToLocal, url)
        else:
            ## The file exists, lets check to resume or skip it.
            u               = urllib2.urlopen(url)
            meta            = u.info()
            onlinefileSize  = int(meta.getheaders("Content-Length")[0])
            localmeta       = os.stat(pathToLocal)
            
            if localmeta.st_size == onlinefileSize:                           
                os.system('echo %s already down-loaded skipping...\n' % pathToLocal)
                return
            elif localmeta.st_size > onlinefileSize:
                ## Delete it, it's a bad download....
                print 'Removing %s ...' % pathToLocal.split(os.sep)[-1]
                os.remove(pathToLocal)                
                try:
                    self._downloadFile(pathToLocal, url)
                except IOError, e:
                    os.system('echo OH NO!: %s' % e)
                    os.system('echo Try a restart of the application and check the files again to solve this problem...')
            else:
                ## Resume file download
                try:
                    self._resumeDownload(pathToLocal, url, localmeta.st_size, onlinefileSize)
                except IOError, e:
                    os.system('echo OH NO!: %s' % e)
                    os.system('echo Try a restart of the application and check the files again to solve this problem...')

    def _makeDirectories(self, pathToLocal):
        """
        Function to make the folders required to download to
        """
        if not os.path.isdir(os.path.dirname(pathToLocal)):
            os.makedirs(os.path.dirname(pathToLocal))

    def _setUIDownloading(self):
        ### SET THE UI TO BE IN A STATE OF DOWNLOADING....
        self.downloadFilesButton.setText('Downloading Files Now....')
        self.downloadFilesButton.setStyleSheet("QPushButton {background-color: yellow}")
        self.repaint()

    def _setUIFinished(self):
        self.checkForLocal.setText('Check Local Files Exist...')
        self.checkForLocal.setStyleSheet("QPushButton {background-color: green}")
        
        self.downloadFilesButton.setText('Click to download missing files...')
        self.downloadFilesButton.setStyleSheet("QPushButton {background-color: green}")
        self.downloadFilesButton.hide()
        self.repaint()

    def _processDownload(self):
        os.system('echo Downloading files to local drives now....')
        failed = []
        
        self._setUIDownloading()
        #####################################################
        ## LOCAL PATH EXISTS
        ## First process the files with a valid local path to.
        if self.missingLocalFilesDict:
            for key, var in self.missingLocalFilesDict.items():
                ## Check through the check boxes for the file name and see if it is checked for download or not.
                for eachCBx in self.localFileCheckBoxes:
                    if eachCBx.text() == key:
                        if eachCBx.isChecked():
                            os.system('echo Downloading %s now..' % key)
                            
                            pathToLocal = var['sg_path_to_movie']
                            url         = var['sg_uploaded_movie']['url']
                            
                            self._preDownload(pathToLocal, url)
                            eachCBx.setChecked(False)
                            self.repaint()

        #####################################################
        ## NO LOCAL PATH EXISTS
        ## Download the valid files that have an uploaded movie only to the temp folder.
        if self.onlineFilesDict:
            if sys.platform == 'win32':
                dir = 'C:\\Temp\\%s' % self.playlist['code'].replace("'", '').replace(' ', '_').replace("/", "_").replace("\\", '_')
            else: ## Assume only Darwin here as no linux is being used.
                dir = '/_projects/Temp/%s' % self.playlist['code'].replace("'", '').replace(' ', '_').replace("/", "_").replace("\\", '_')
            
            for key, var in self.onlineFilesDict.items():
                for eachCBx in self.tempFileCheckBoxes:                    
                    if eachCBx.text() == key:
                        if eachCBx.isChecked():
                            url         = var['sg_uploaded_movie']['url']
                            pathToLocal = os.path.join(dir, var['sg_uploaded_movie']['name'])
                            
                            self._preDownload(pathToLocal, url)
                            
                            eachCBx.setChecked(False)
                            self.repaint()
                
        ### SET THE UI TO BE IN A STATE FINISHED....
        self._setUIFinished()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = DownloadPlaylist()
    myWin.show()
    sys.exit(app.exec_())
