import os, sys, shutil, re
sys.path.append('//192.168.5.253/BBB_main/bbb/t/software/lsapipeline/defaultMayaEnv/site-packages/')
from PyQt4 import QtCore, QtGui
sys.path.append('//192.168.5.253/BBB_main/bbb/t/software/studio/install/core/python/')
if 'T:/software/python-api/' not in sys.path:
    sys.path.append('T:/software/python-api/')
from shotgun_api3 import Shotgun
import sgtk

class GenericPlayblastPublish(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(GenericPlayblastPublish, self).__init__(parent)
        self.path = 'I:/lsapipeline/episodes'
        self.tk = sgtk.sgtk_from_path('T:/software/bubblebathbay')
        self.initUi()

    def initUi(self):
        #    Text edit for source path
        self.textEdit           =   QtGui.QTextEdit()
        self.listShotsBttn      =   QtGui.QPushButton('List Mov\'s')
        browseLayout            =   QtGui.QHBoxLayout()        
        self.createPalettes(self)
        self.createPalettes(self.textEdit)

        #    Create task interface
        taskLabel               =   QtGui.QLabel("Task")
        self.comboBox           =   QtGui.QComboBox()
        self.createPalettes(self.comboBox)
        #    Layout task interface
        taskLayout              =   QtGui.QHBoxLayout()

        #    Create tree widget interface for populating shots
        self.shotTreeWidget     =   QtGui.QTreeWidget()
        self.createPalettes(self.shotTreeWidget)
        self.shotTreeWidget.setColumnCount(5)

        #    Layout treeWidget interface
        shotTreeWidgetLayout    =   QtGui.QHBoxLayout()

        #    Publish button
        self.publishBttn        =   QtGui.QPushButton('Publish')
        self.createPalettes(self.publishBttn)

        #    Set Main Layout and add all child layouts
        mainLayout              =   QtGui.QVBoxLayout()

        #    Connections and settings

        self.textEdit.setFixedHeight(20)
        self.textEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.listShotsBttn.clicked.connect(self._listShots)
        browseLayout.addWidget(self.textEdit)
        browseLayout.addWidget(self.listShotsBttn)

        taskLayout.addWidget(taskLabel)
        taskLayout.addWidget(self.comboBox)

        self.shotTreeWidget.setHeaderLabels(["List of Shots", "Episode", "Shot", "Version", "Task"])
        self.shotTreeWidget.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)
#         self.shotTreeWidget.itemChanged.connect(self._itemChangedSignal())

        shotTreeWidgetLayout.addWidget(self.shotTreeWidget)

        self.publishBttn.clicked.connect(self._pubBttn)

#         self.plainTextEdit = QtGui.QPlainTextEdit()
#         self.plainTextEdit.setReadOnly(1)
#         self.plainTextEdit.setFocusPolicy(QtCore.Qt.NoFocus)
#         self._palette(self.plainTextEdit)

        #    Set layout
        mainLayout.addLayout(taskLayout)
        mainLayout.addLayout(browseLayout)
        mainLayout.addLayout(shotTreeWidgetLayout)
        mainLayout.addWidget(self.publishBttn)
#         mainLayout.addWidget(self.plainTextEdit)
        self.setLayout(mainLayout)
        self.setWindowTitle("Dump all the shit on Shotgun!!!!!")
        self.resize(435, 500)
        self.shotTreeWidget.header().resizeSection(0, 175)
        self.shotTreeWidget.header().resizeSection(1, 55)
        self.shotTreeWidget.header().resizeSection(2, 52)
        self.shotTreeWidget.header().resizeSection(3, 55)
        self.shotTreeWidget.header().resizeSection(4, 55)
        self.createPalettes(self.shotTreeWidget.header())
        self._populateComboBox()
        
#    List of Tasks to add in comboBox
    def _populateComboBox(self):
        tasks = ["Anm", "FX", "Layout", "AdditionalFX"]
        self.comboBox.addItems(tasks)

#    List of shots from the given Mov
    def _listShots(self):
        path = str(self.textEdit.toPlainText())
        self.shotTreeWidget.clear()
        self.shotTreeWidgetItems = []
        self.srcPath = {}
        if os.path.exists(path):
            files = sorted(os.listdir(path))
            for file in files:
                ext = os.path.splitext(file)[-1]
                if ext == '.mov' or ext == '.MOV':
                    if 'ep' in file and 'sh' in file and '.v' in file :
                        shotTreeWidgetItem = QtGui.QTreeWidgetItem([os.path.splitext(file)[0]])
                        shotTreeWidgetItem.setCheckState(0, QtCore.Qt.Checked)
                        self.shotTreeWidgetItems.append(shotTreeWidgetItem)
                        shotTreeWidgetItem.setText(1, self._getEpisodeName(episode=file))
                        shotTreeWidgetItem.setText(2, self._getShotName(episode=file))
                        shotTreeWidgetItem.setText(4, self._getTaskFolderName())
                        shotTreeWidgetItem.setText(3, self._getVersionNumber(episode=file))
                        self.srcPath[os.path.splitext(file)[0]] = os.path.join(path, file)
                else:
                    pass
        if self.shotTreeWidgetItems:
            self.shotTreeWidget.addTopLevelItems(self.shotTreeWidgetItems)
            return self.srcPath
        else:
            QtGui.QMessageBox.information(None, "Aborting....", "Invalid path!!!!!!!!")

    def _getTaskFolderName(self):
        folderName = None
        if self.comboBox.currentText() == "FX":
            folderName = "FX"
        elif self.comboBox.currentText() == "Anm":
            folderName = "Anm"
#         elif self.comboBox.currentText() == "Light":
#             folderName = "Light"
#         elif self.comboBox.currentText() == "Comp":
#             folderName = "Comp"
        elif self.comboBox.currentText() == "Layout":
            folderName = "Blck"
        elif self.comboBox.currentText() == "AdditionalFX":
            folderName = "AFX"
        return folderName

    def _getEpisodeName(self, episode):
        if '_' in episode:
            episode     =   episode.replace('_', "")
        else:
            pass
        if episode:
            return episode.split('sh')[0]

    def _getShotName(self, episode):
        epName          =     episode.split('.')[0]
        shName          =    'sh%s' % epName.split('sh')[1]
        shNumberList    =    re.split('\\D', shName)
        self.shNum      =    ''
        for shNum in shNumberList:
            if shNum:
                self.shNum  =   'sh%s' % shNum
        return self.shNum

    def _getVersionNumber(self, episode):
        self.versionNum =   0
        if '.v' in episode:
            for each in episode.split('.'):
                if each.startswith('v0'):
                    versionNum      =   int(each.split('v')[1])
                    self.versionNum =   '%03d' % versionNum
        return self.versionNum

    def _getExt(self, episode):
        self.ext = os.path.splitext(episode)[-1]
        print self.ext

    def _getPublishPath(self, episode):
        epName  =    self._getEpisodeName(episode)
        shName  =    '%s_%s' % (epName,self._getShotName(episode))
        task    =    self._getTaskFolderName()
        path    =    os.path.join(self.path, str(epName), str(shName), str(task), 'publish', 'review')
        if os.path.exists(path):
            return path.replace('\\', '/')
        else:
            return 0

#     def _itemChangedSignal(self, shot):
#         if shot.checkState(0):
#             shot.setCheckState(0, QtCore.Qt.Unchecked)
#             print "Checked"
#         else:
#             print "Unchecked"
#             shot.setCheckState(0, QtCore.Qt.Checked)

    def _pubBttn(self):
        base_url    = "http://bubblebathbay.shotgunstudio.com"
        script_name = 'playBlastPublisher'
        api_key     = '718daf67bfd2c7e974f24e7cbd55b86bb101c4e5618e6d5468bc4145840e4558'

        sgsrv = Shotgun(base_url = base_url , script_name = script_name, api_key = api_key, ensure_ascii=True, connect=True)

        selectedShots = sorted([item.text(0) for item in self.shotTreeWidgetItems if item.checkState(0)])
        for shot in selectedShots:
            if shot in self.srcPath.keys():
                destPath = self._getPublishPath(shot)
                srcPath = self.srcPath[str(shot)]
                ext = os.path.splitext(srcPath)[-1]
#                 print os.path.basename(srcPath)
#                 while os.path.exists(os.path.join(str(destPath), os.path.basename(srcPath))):
#                     print "In Loop"
#                     print os.path.basename(srcPath)
#                     allFiles= os.listdir(destPath)
#                     publishFiles = []
#                     if allFiles:
#                         for allFile in allFiles:
#                             if allFile.endswith(ext):
#                                 print allFile
#                                 publishFiles.append(allFile)
#                     versionNumber = int(sorted(publishFiles)[-1].split('.v')[1].split(ext)[0])
#                     versionNumber += 1
#                     if versionNumber < 10:
#                         publishFileName = '%sLayout.v%03d%s' % (shotName.replace('_', ''), versionNumber, ext)
#                         self.publishPath = os.path.join(self.publishPath, publishFileName)
#                         self.playblastName = os.path.basename(self.publishPath)
#                     else:
#                         publishFileName = '%sLayout.v%02d%s' % (shotName.replace('_', ''), versionNumber, ext)
#                         self.publishPath = os.path.join(self.publishPath, publishFileName)
#                         self.playblastName = os.path.basename(self.publishPath)
#                 shutil.copy2(srcPath, destPath)

                shotName = '%s_%s' % (self._getEpisodeName(shot), self._getShotName(shot))
                getShotTasks =  self.tk.shotgun.find_one('Shot',  filters = [["code", "is", shotName]], fields=['id', 'tasks'])
                taskName = self.comboBox.currentText()
                self.playblastName = os.path.basename(srcPath)
                publishMovPath = os.path.join(destPath, self.playblastName).replace('\\', '/')
                shutil.copy2(srcPath, destPath)
                for task in getShotTasks['tasks']:
                    if task['name'] == taskName:
                        taskId = task['id']
                        data = { 'project': {'type':'Project','id': 66},
                             'code':  self.playblastName,
                             'description': 'Playblast published',
                             'sg_path_to_movie': publishMovPath,
                             'sg_status_list': 'rev',
                             'entity': {'type':'Shot', 'id':getShotTasks['id']},
                             'sg_task': {'type':'Task', 'id':taskId},
                             'user': {'type':'HumanUser', 'id':92} }
                        result = sgsrv.create('Version', data)
                        result2 = sgsrv.upload("Version", result['id'], publishMovPath, "sg_uploaded_movie")
                        print "Published %s" % self.playblastName
        

    def createPalettes(self, widget):
        pal = widget.palette()
        pal.setColor(widget.backgroundRole(), QtGui.QColor(125, 125, 125))
        pal.setColor(QtGui.QPalette.All, QtGui.QPalette.Base, QtGui.QColor(100, 100, 100))
        pal.setColor(QtGui.QPalette.All, QtGui.QPalette.Text , QtGui.QColor(0, 0, 0))
        widget.setPalette(pal)

if __name__ == "__main__":
    app     =   QtGui.QApplication(sys.argv)
    genPP   =   GenericPlayblastPublish()
    genPP.show()
    app.exec_()