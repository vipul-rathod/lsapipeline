"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
I am a dead change again...
"""
import os, getpass, sys, shutil, sgtk, math, sip, time
from shotgun_api3 import Shotgun
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError
from debug import debug
from icon import Icon

if 'T:/software/lsapipeline/tools' not in sys.path:
	sys.path.append('T:/software/lsapipeline/tools')

if 'T:/software/python-api/' not in sys.path:
	sys.path.append('T:/software/python-api/')

if 'T:/software/lsapipeline/custom' not in sys.path:
	sys.path.append('T:/software/lsapipeline/custom')
import core_archive_lib as coreLib
import maya_asset_MASTERCLEANUPCODE as cleanup
#reload(cleanup)
#reload(coreLib)

class StaticENVHandler(Application):
	def init_app(self):
		# make sure that the context has an entity associated - otherwise it wont work!
		if self.context.entity is None:
			raise tank.TankError("Cannot load the OceanGenerator application! "
								 "Your current context does not have an entity (e.g. "
								 "a current Shot, current Asset etc). This app requires "
								 "an entity as part of the context in order to work.")
		getDisplayName = self.get_setting('display_name')
		self.engine.register_command(getDisplayName, self.run_app)
		debug(self, method = 'init_app', message = 'StaticENVHandler Loaded...', verbose = False)

	def run_app(self):
		debug(self, method = 'run_app', message = 'StaticENVHandler...', verbose = False)
		getDisplayName = self.get_setting('display_name')
		self.engine.show_dialog(getDisplayName, self, MainUI, self)


class MainUI(QtGui.QWidget):
	def __init__(self, app):
		"""
		main UI for STATIC ENV handling

		I always build my UI in __init__ so suck it up..

		"""
		QtGui.QWidget.__init__(self)
		self.app = app
		self.fileBoxes  = []
		## Instance the api for talking directly to shotgun.
		base_url    = "http://bubblebathbay.shotgunstudio.com"
		script_name = 'audioUploader'
		api_key     = 'bbfc5a7f42364edd915656d7a48d436dc864ae7b48caeb69423a912b930bc76a'
		self.sgsrv  = Shotgun(base_url = base_url , script_name = script_name, api_key = api_key, ensure_ascii=True, connect=True)

		self.shotNum    = self._getShotNum()[0]
		self.currentENV = self._getShotNum()[1]
		debug(self.app, method = 'MainUI', message = 'self.shotNum: %s' % self.shotNum, verbose = False)
		debug(self.app, method = 'MainUI', message = 'self.currentENV: %s' % self.currentENV, verbose = False)
		self.lightAlembicFolder = 'I:/lsapipeline/episodes/ep000/%s/Light/publish/alembic_static' % self.shotNum

		## Now build the UI
		self.mainLayout     = QtGui.QHBoxLayout(self)
		self.leftSideLayout = QtGui.QVBoxLayout(self)
		debug(self.app, method = 'MainUI', message = 'self.mainLayout built...', verbose = False)

		##########################
		### ENV SELECTION PULLDOWN
		self.envLayout      = QtGui.QVBoxLayout(self)
		self.envPulldown    = QtGui.QComboBox()

		getENVS             = self.sgsrv.find('Asset',  filters = [["code", "contains", 'ENV_'], ["code", "not_contains", '_ENV_'], ["code", "not_contains", 'WORLDMAP'], ["code", "not_contains", 'TSETbuild']], fields=['code'])
		debug(self.app, method = 'MainUI', message = 'getENVS: %s' % getENVS, verbose = False)

		if self.shotNum:
			for each in getENVS:
				if each['code'] == self.currentENV:
					self.envPulldown.addItem(each['code'])
					self.lightAlembicFolder = 'I:/lsapipeline/episodes/ep000/%s/Light/publish/alembic_static' % self.shotNum
			self.envPulldown.setCurrentIndex(self.envPulldown.findText(self.currentENV))
			debug(self.app, method = 'MainUI', message = 'self.envPulldown setCurrentIndex...', verbose = False)
		else:
			for each in getENVS:
				if 'STATIC' in each['code']:
					self.envPulldown.addItem(each['code'])


		self.fetchAssetListButton = QtGui.QPushButton(Icon('refresh.png'), 'Fetch Asset List')
		self.fetchAssetListButton.setStyleSheet("QPushButton {text-align : left}")
		self.fetchAssetListButton.released.connect(self._fetchAssetList)
		debug(self.app, method = 'MainUI', message = 'self.fetchAssetListButton built...', verbose = False)

		self.importAssetButton = QtGui.QPushButton(Icon('alembic.png'), 'Import latest Pub ABC for Sel')
		self.importAssetButton.setStyleSheet("QPushButton {text-align : left}")
		self.importAssetButton.released.connect(self._fetchMDLAlembicPublish)
		debug(self.app, method = 'MainUI', message = 'self.importAssetButton built...', verbose = False)

		self.checkMDLButton = QtGui.QPushButton(Icon('refresh.png'), 'Check For MDL ABC Publishes')
		self.checkMDLButton.setStyleSheet("QPushButton {text-align : left}")
		self.checkMDLButton.released.connect(self._checkVersionsAgainstPublishes)
		debug(self.app, method = 'MainUI', message = 'self.checkMDLButton built...', verbose = False)

		self.redoSetsButton = QtGui.QPushButton(Icon('plus.png'), 'ReDo Set Assignments')
		self.redoSetsButton.setStyleSheet("QPushButton {text-align : left}")
		self.redoSetsButton.released.connect(self._createSets)
		debug(self.app, method = 'MainUI', message = 'self.redoSetsButton built...', verbose = False)

		self.checkSRFXMLButton = QtGui.QPushButton(Icon('refresh.png'), 'Check For SRF Publishes')
		self.checkSRFXMLButton.setStyleSheet("QPushButton {text-align : left}")
		self.checkSRFXMLButton.released.connect(self._checkSRFVersionsAgainstPublishes)

		self.cleanDuplicateCoresButton = QtGui.QPushButton(Icon('AssignedFileIt.png'), 'Clean Duplicate Cores')
		self.cleanDuplicateCoresButton.setStyleSheet("QPushButton {text-align : left}")
		self.cleanDuplicateCoresButton.released.connect(self._fixTheFuckingCores)
		self.cleanDuplicateCoresButton.setToolTip('This is performed on every import of an static env via the multiloader.\n Exposed just in case you need to run this manually.\n This will go through a scene with multiple static ENVs in it \nand try to make sure duplicate cores are renering correctly.')

		self.removeCoreGrpsButton = QtGui.QPushButton(Icon('skull.png'), 'Remove old Core Grps under geo_hrc')
		self.removeCoreGrpsButton.setStyleSheet("QPushButton {text-align : left}")
		self.removeCoreGrpsButton.released.connect(self._removeCoreGrps)
		self.removeCoreGrpsButton.setToolTip('You can use this to clean up any old core grps under the geo_hrc grps in a scene\nafer you have done a core archive rebuild from xml...')
		## THIS IS UP TO YOU TO ENABLE. IT SHOULDNT BE REQUIRED AS THE MDL PUBLISH SHOULD NOW BE EXPORTING THE CORRECT ATTRS FOR ALEMBIC
		self.republishALL = QtGui.QPushButton('Republish ALL MDL Alembics for %s' % self.currentENV)
		self.republishALL.released.connect(self._republishAllAlembicsForENV)
		self.republishALL.setEnabled(True)

		self.lambert1Button = QtGui.QPushButton(Icon('refresh.png'), 'Check lambert1 objects')
		self.lambert1Button.setStyleSheet("QPushButton {text-align : left}")
		self.lambert1Button.released.connect(self._lambert1Object)

		self.caNSclashCheckButton = QtGui.QPushButton(Icon('refresh.png'), 'Check Core Archive Namespace')
		self.caNSclashCheckButton.setStyleSheet("QPushButton {text-align : left}")
		self.caNSclashCheckButton.released.connect(self.coreArchiveNSclashCheck)

		self.checkFileInPathButton = QtGui.QPushButton(Icon('refresh.png'), 'Check Invalid FileIn Path')
		self.checkFileInPathButton.setStyleSheet("QPushButton {text-align : left}")
		self.checkFileInPathButton.released.connect(self.checkFileInPath)

		self.checkNonManifoldButton = QtGui.QPushButton(Icon('refresh.png'), 'Check Non-Manifold Geometry')
		self.checkNonManifoldButton.setStyleSheet("QPushButton {text-align : left}")
		self.checkNonManifoldButton.released.connect(self.cleanupNonManifoldGeometry)

		## Add stuff to the env layout
		self.envLayout.addWidget(self.envPulldown)
		self.envLayout.addWidget(self.fetchAssetListButton)
		self.envLayout.addWidget(self.importAssetButton)
		self.envLayout.addWidget(self.checkMDLButton)
		self.envLayout.addWidget(self.checkSRFXMLButton)
		self.envLayout.addWidget(self.redoSetsButton)
		self.envLayout.addWidget(self.cleanDuplicateCoresButton)
		self.envLayout.addWidget(self.removeCoreGrpsButton)
		self.envLayout.addWidget(self.republishALL)
		self.envLayout.addWidget(self.lambert1Button)
		self.envLayout.addWidget(self.caNSclashCheckButton)
		self.envLayout.addWidget(self.checkFileInPathButton)
		self.envLayout.addWidget(self.checkNonManifoldButton)

		######################
		### ENV RELATED ASSETS
		self.assetLayout  = QtGui.QVBoxLayout(self)

		### Now do the check boxes for files....
		self.scrollLayout = QtGui.QScrollArea(self)
		self.scrollLayout.setMinimumHeight(300)

		self.envAssetsGroupBox = QtGui.QGroupBox(self.scrollLayout)
		self.envAssetsGroupBox.setFlat(True)

		self.scrollLayout.setWidget(self.envAssetsGroupBox)
		self.scrollLayout.setWidgetResizable(True)

		self.envAssetsLayout = QtGui.QGridLayout(self.envAssetsGroupBox)

		self.assetLayout.addWidget(self.scrollLayout)

		self.mainLayout.addLayout(self.leftSideLayout)
		## Add stuff to leftSideLayout
		self.leftSideLayout.addLayout(self.envLayout)
		self.leftSideLayout.addStretch(1)

		## Add anything else to the HBox
		self.mainLayout.addLayout(self.assetLayout)
		self.resize(1000, 500)
		debug(self.app, method = 'MainUI', message = 'ui built successfully fetching assets now...', verbose = False)
		debug(self.app, method = 'MainUI', message = 'self.envPulldown.currentText(): %s' % self.envPulldown.currentText(), verbose = False)

		self._fetchAssetList()
		self.envPulldown.currentIndexChanged.connect(partial(self._getShotNumFromMenuName))
		self.envPulldown.currentIndexChanged.connect(partial(self._fetchAssetList))

	def arraysMatch(self, a, b):
		'''
		Utility to compare two string list
		'''
		return True if a == b else False

	def cleanupNonManifoldGeometry(self, normals = True):
		## Get all the mesh that has mentalraySubdivApprox connected and has non-manifold problem
        # subdiv_mesh = [cmds.listRelatives(mesh, parent = True, fullPath = True)[0] for mesh in cmds.ls(type = 'mesh') if cmds.listConnections(mesh, type = 'mentalraySubdivApprox') if cmds.polyInfo(mesh, nme = True) or cmds.polyInfo(nmv = True)]
		subdiv_mesh = [cmds.listRelatives(mesh, parent = True, fullPath = True)[0] for mesh in cmds.ls(type = 'mesh') if cmds.polyInfo(mesh, nme = True) or cmds.polyInfo(nmv = True)]
		subdiv_mesh = list( set( subdiv_mesh ) )

		if subdiv_mesh:
			for each in subdiv_mesh:
				## Make sure we do indeed have nonmanifold geometry
				##
				nonManifold = cmds.polyInfo(each, nmv = True, nme = True)
				if nonManifold:

					proceed = cmds.confirmDialog(title = 'Non-Manifold Geometry!', message = 'Geo Name:\n%s' % each, button = ['Cleanup!', 'Skip...'], defaultButton = 'Skip...', cancelButton = 'Skip...', dismissString = 'Skip...')
					if proceed == 'Cleanup!':

						## Conform the geo and see if that gets rid of all the nonmanifold bits
						##
						if normals:
							cmds.polyNormal('%s.f[*]' % each, normalMode = 2, constructionHistory = True)

						edges			= cmds.polyInfo(each, nme = True) if cmds.polyInfo(each, nme = True) else []
						vertices 		= [] if edges else cmds.polyInfo(each, nmv = True)
						lastEdges		= []
						lastVertices	= []

						while ( not self.arraysMatch(lastEdges, edges) or not self.arraysMatch(lastVertices, vertices) ) and ( edges or vertices ):
							## Remember what was nonmanifold last time
							##
							lastEdges		= edges
							lastVertices	= vertices
							## Split any nonmanifold edges
							##
							if edges:
								cmds.polySplitEdge(edges, constructionHistory = True)
								vertices = cmds.polyInfo(each, nmv = True)
								edges = []

							## Split any remaining nonmanifold vertices
							##
							if vertices:
								cmds.polySplitVertex(vertices, constructionHistory = True)
								vertices = []

							## Now check to see if the object is still nonmanifold
							##
							nonManifold = cmds.polyInfo(each, nmv = True, nme = True)
							if nonManifold:
								## Chip off the faces
								##
								nonManifoldFaces = cmds.polyListComponentConversion(nonManifold, toFace = True)
								cmds.polyChipOff(nonManifoldFaces, kft = 0, dup = 0, constructionHistory = True)
								## And then check for nonmanifold bits again
								##
								edges = cmds.polyInfo(each, nme = True)
								if not edges:
									vertices = cmds.polyInfo(each, nmv = True)

						## Check to see if we failed to cleanup
						if edges or vertices:
							cmds.warning('Failed to cleanup non-manifold geometry of %s...' % each)

	def _lambert1Object(self):
		## Delete sets first
		if cmds.objExists('lambert1_object_set'):
			cmds.delete('lambert1_object_set')

		lambert1 = cmds.ls( cmds.sets('initialShadingGroup', q = True), long = True )
		if lambert1:
			lambert1 = [x.split('.f')[0] for x in lambert1 if cmds.objectType(x) == 'mesh' and 'CArch' not in x]

		## Create sets if bad stuffs detected
		if lambert1:
			cmds.sets(lambert1, name = 'lambert1_object_set')

	def coreArchiveNSclashCheck(self):
		coreArchive_NS = [ns for ns in cmds.namespaceInfo(listOnlyNamespaces = True) if 'CORE' in ns.split('_')[-1]]
		if coreArchive_NS:
			dup_coreArchive_NS = [ns for ns in coreArchive_NS if not ns.endswith('_CORE')]
			if dup_coreArchive_NS:
				cmds.confirmDialog(title = 'Core Archive Namespace', message = 'Core Archive namespace clashes detected, please check the namespace editor!', button = 'OK!')

	def checkFileInPath(self):
		## Delete sets first
		if cmds.objExists('invalid_fileIn_path_set'):
			cmds.delete('invalid_fileIn_path_set')

		fileIn = cmds.ls(type = 'file')
		fileIn.extend( cmds.ls(type = 'mentalrayTexture') )
		if fileIn:
			badFileInPath = [x for x in fileIn if not os.path.exists( cmds.getAttr('%s.fileTextureName' % x) )]

			## Create sets if bad stuffs detected
			if badFileInPath:
				cmds.sets(badFileInPath, name = 'invalid_fileIn_path_set')

	def _removeCoreGrps(self):
		"""
		Exposing function for operator to cleanup after a rebuild
		"""
		## Step one after import
		## Clean the fucking left over grps first if they exist
		ENVLIST = ['ENV_MIDDLEHARBOUR_STATIC_ABC_STATIC_CACHES_hrc', 'ENV_MIDDLEHARBOUR_EAST_STATIC_ABC_STATIC_CACHES_hrc', 'ENV_WESTHARBOUR_STATIC_ABC_STATIC_CACHES_hrc',
					'ENV_THEHEADS_STATIC_ABC_STATIC_CACHES_hrc', 'ENV_BIGTOWN_STATIC_ABC_STATIC_CACHES_hrc']
		getHRCS = [[eachGrp for eachGrp in cmds.listRelatives(eachENV)] for eachENV in ENVLIST if cmds.objExists(eachENV)]
		[[cmds.delete(eachChild) for eachChild in cmds.listRelatives(eachHrc, ad = True, f = True) if '_CORE_' in eachChild] for eachHrc in getHRCS]

	def _toggleCBx(self, chbx = '', wtfami = ''):
		"""
		Function to select on checkbox toggle
		@param chbx: the QCheckbox
		@param wtfami: WHO THE HELL KNOWS!!????!!!!!!!!
		@type chbox: PyQt Object
		:return:
		"""
		if chbx.isChecked():
			cmds.select('%s_hrc' % chbx.text(), add = True)
		else:
			cmds.select('%s_hrc' % chbx.text(), d = True)

	def _getShotNum(self):
		self.workSpace = cmds.workspace(q = True, fn = True)
		debug(self.app, method = '_getShotNum', message = 'self.workSpace: %s' % self.workSpace, verbose = False)
		envName = ''
		shotNum = ''

		if 'ep000_sh010' in self.workSpace:
			envName = 'ENV_MIDDLEHARBOUR_STATIC'
			shotNum = 'ep000_sh010'
		elif 'ep000_sh020' in self.workSpace:
			envName = 'ENV_WESTHARBOUR_STATIC'
			shotNum = 'ep000_sh020'
		elif 'ep000_sh030' in self.workSpace:
			envName = 'ENV_BIGTOWN_STATIC'
			shotNum = 'ep000_sh030'
		elif 'ep000_sh040' in self.workSpace:
			envName = 'ENV_THEHEADS_STATIC'
			shotNum = 'ep000_sh040'
		elif 'ep000_sh050' in self.workSpace:
			envName = 'ENV_MIDDLEHARBOUR_EAST_STATIC'
			shotNum = 'ep000_sh050'
		else:
			envName = None
			shotNum = None

		return shotNum, envName

	def _getShotNumFromMenuName(self, index = ''):
		self.workSpace = cmds.workspace(q = True, fn = True)
		envName = ''
		shotNum = ''

		if self.envPulldown.currentText() == 'ENV_MIDDLEHARBOUR_STATIC':
			shotNum = 'ep000_sh010'
		elif self.envPulldown.currentText() == 'ENV_WESTHARBOUR_STATIC':
			shotNum = 'ep000_sh020'
		elif self.envPulldown.currentText() == 'ENV_BIGTOWN_STATIC':
			shotNum = 'ep000_sh030'
		elif self.envPulldown.currentText() == 'ENV_THEHEADS_STATIC':
			shotNum = 'ep000_sh040'
		elif self.envPulldown.currentText() == 'ENV_MIDDLEHARBOUR_EAST_STATIC':
			shotNum = 'ep000_sh050'
		else:
			shotNum = None

		return shotNum

	def _addVersionTag(self, assetName, versionNumber):
		if cmds.objExists('%s.version' % assetName):
			cmds.deleteAttr('%s.version' % assetName)
		try:
			cmds.addAttr(assetName, ln = 'version', at = 'long', min = 0, max  = 50000, dv = 0)
		except:
			pass
		cmds.setAttr('%s.version' % assetName, int(versionNumber))

	def _checkVersionsAgainstPublishes(self):
		## Path to the assets folder
		pathToAssets = "I:/lsapipeline/assets" ##Hardcoded yuckiness..
		MDLVersNum = ''

		## Fetch the subAssets for the ENV
		getData = self.sgsrv.find('Asset',  filters = [["code", "is", self.envPulldown.currentText()]], fields=['code', 'id', 'assets'])

		## Now can the checkboxes and see which assets arechecked
		if self.fileBoxes:
			for eachAsset in self.fileBoxes:
				if eachAsset.isChecked():
					#print 'Checking %s ...' % eachAsset.text()
					for eachSGAsset in getData[0]['assets']:

						if eachSGAsset['name'] == eachAsset.text():
							## BLD
							if 'BLD' in eachSGAsset['name']:
								assetPublishFolder = "%s/Building/%s/MDL/publish/alembic" % (pathToAssets, eachSGAsset['name'])
							## LND
							elif 'LND' in eachSGAsset['name']:
								assetPublishFolder = "%s/Environment/%s/MDL/publish/alembic" % (pathToAssets, eachSGAsset['name'])

							assetPublishFolder.replace("/", os.sep)
							if os.path.isdir(assetPublishFolder):
								try:
									getLatestPublish = max(os.listdir(assetPublishFolder))
								except:
									getLatestPublish = []

								if getLatestPublish and getLatestPublish.endswith('.abc'):
									MDLVersNum = int(getLatestPublish.split('.')[-2].split('v')[-1])

							try:
								getAssetVersion = cmds.getAttr('%s_hrc.version' % eachAsset.text())
							except ValueError:
								getAssetVersion = None

							if getAssetVersion:
								if not getAssetVersion == MDLVersNum:
									#self.envPulldown.setCurrentIndex(self.envPulldown.findText(self.currentENV))
									print '!!HIGHER VER EXISTS: %s_hrc:%s \t %s' % (eachAsset.text(), getAssetVersion, getLatestPublish)
									eachAsset.setStyleSheet("QCheckBox{background-color: red}")
								else:
									eachAsset.setStyleSheet("QCheckBox{background-color: green}")
									eachAsset.setChecked(False)
									print 'PASSED: version match %s' % (getLatestPublish)
							else:
								eachAsset.setStyleSheet("QCheckBox{background-color: red}")
								cmds.warning('%s IS MISSING VERSION INFORMATION! PLEASE FIX!!!' % eachAsset.text())
			for eachAsset in self.fileBoxes:
				if eachAsset.isChecked() and eachAsset.text() == 'ALL':
					eachAsset.setChecked(False)
					eachAsset.setStyleSheet("QCheckBox{background-color: green}")

	def _checkSRFVersionsAgainstPublishes(self):
		## Path to the assets folder
		pathToAssets = "I:/lsapipeline/assets" ##Hardcoded yuckiness..
		MDLVersNum = ''

		## Fetch the subAssets for the ENV
		getData = self.sgsrv.find('Asset',  filters = [["code", "is", self.envPulldown.currentText()]], fields=['code', 'id', 'assets'])

		## Now can the checkboxes and see which assets are checked
		if self.fileBoxes:
			for eachAsset in self.fileBoxes:
				if eachAsset.isChecked():
					#print 'Checking %s ...' % eachAsset.text()
					for eachSGAsset in getData[0]['assets']:

						if eachSGAsset['name'] == eachAsset.text():
							## BLD
							if 'BLD' in eachSGAsset['name']:
								assetPublishFolder = "%s/Building/%s/SRF/publish/xml" % (pathToAssets, eachSGAsset['name'])
							## LND
							elif 'LND' in eachSGAsset['name']:
								assetPublishFolder = "%s/Environment/%s/SRF/publish/xml" % (pathToAssets, eachSGAsset['name'])

							assetPublishFolder.replace("/", os.sep)
							if os.path.isdir(assetPublishFolder):
								try:
									getLatestPublish = max(os.listdir(assetPublishFolder))
								except:
									getLatestPublish = []

								if getLatestPublish and getLatestPublish.endswith('.xml'):
									XMLVersNum = int(getLatestPublish.split('.')[-2].split('v')[-1])

							try:
								getAssetSRFVersion = cmds.getAttr('%s_hrc.SRFversion' % eachAsset.text())
							except ValueError:
								getAssetSRFVersion = None

							if getAssetSRFVersion:
								if not getAssetSRFVersion == XMLVersNum:
									#self.envPulldown.setCurrentIndex(self.envPulldown.findText(self.currentENV))
									print '!!HIGHER VER EXISTS: %s_hrc:%s \t %s' % (eachAsset.text(), getAssetSRFVersion, getLatestPublish)
									eachAsset.setStyleSheet("QCheckBox{background-color: red}")
								else:
									eachAsset.setStyleSheet("QCheckBox{background-color: green}")
									eachAsset.setChecked(False)
									print 'PASSED: version match %s' % (getLatestPublish)
							else:
								eachAsset.setStyleSheet("QCheckBox{background-color: red}")
								cmds.warning('%s IS MISSING VERSION INFORMATION! PLEASE FIX!!!' % eachAsset.text())
			for eachAsset in self.fileBoxes:
				if eachAsset.isChecked() and eachAsset.text() == 'ALL':
					eachAsset.setChecked(False)
					eachAsset.setStyleSheet("QCheckBox{background-color: green}")

	def _checkVersionNumber(self, assetName, versionNumber):
		"""
		Returns if the version number for an asset in the scene matches that of the asset in the static_folder
		"""

		foundVersion = False
		assetList = []
		for eachAlembic in os.listdir(self.lightAlembicFolder):
			if assetName.replace('_', '') in eachAlembic:
				assetList.append(eachAlembic)

		try:
			getlatest = max(assetList)
		except:
			getlatest = []

		if getlatest:
			getlatestVersionNum = getlatest.split('.')[-2].split('v')[-1]
			if int(versionNumber) == int(getlatestVersionNum):
				foundVersion = True
		else:
			cmds.warning('There is no asset for %s found in the lighting static alembic folder.' % assetName)

		return foundVersion

	def _fetchAssetList(self, index = ''):
		getData = self.sgsrv.find('Asset',  filters = [["code", "is", self.envPulldown.currentText()]], fields=['code', 'id', 'assets'])
		debug(self.app, method = '_fetchAssetList', message = 'getData: %s' % getData, verbose = False)

		if self.fileBoxes:
			for each in self.fileBoxes:
				each.setParent(None)
				each = None

		self.fileBoxes  = []

		## First add the ALL checkbox
		self.ALL = QtGui.QCheckBox(self)
		self.ALL.setChecked(False)
		self.ALL.setText('ALL')
		self.ALL.toggled.connect(self._toggleAll)

		self.fileBoxes.append(self.ALL)
		self.envAssetsLayout.addWidget(self.ALL, 0, 0)

		self.colCount = 5
		r = 1
		c = 1

		if getData:
			for eachAsset in getData[0]['assets']:
				self.assetCheckBox = QtGui.QCheckBox(self)
				self.assetCheckBox.setChecked(False)
				self.assetCheckBox.setText(eachAsset['name'])
				self.assetCheckBox.toggled.connect(partial(self._toggleCBx, self.assetCheckBox))
				self.fileBoxes.append(self.assetCheckBox)
				if cmds.objExists('%s_hrc' % eachAsset['name']):
					self.assetCheckBox.setStyleSheet("QCheckBox{background-color: #0066CC}")
					## Now check the version
					if cmds.objExists('%s_hrc.version' % eachAsset['name']):
						self.lightAlembicFolder = 'I:/lsapipeline/episodes/ep000/%s/Light/publish/alembic_static' % self._getShotNumFromMenuName()
						if not self._checkVersionNumber(eachAsset['name'], cmds.getAttr('%s_hrc.version' % eachAsset['name'])):
							self.assetCheckBox.setStyleSheet("QCheckBox{background-color: red}")
					else:
						self.assetCheckBox.setStyleSheet("QCheckBox{background-color: #990000}")
						cmds.warning('Asset version attr not found on %s_hrc' % eachAsset['name'])
				else:
					self.assetCheckBox.setStyleSheet("QCheckBox{background-color: red}")


				if c == self.colCount:
					r = r + 1
					c = 1
				self.envAssetsLayout.addWidget(self.assetCheckBox, r, c)
				c = c + 1

	def _toggleAll(self):
		"""
		A quick toggle for all the type checkboxes to on or off
		"""
		for each in self.fileBoxes:
			if each.text() == 'ALL':
				each.setStyleSheet("QCheckBox{background-color: grey}")
				if each.isChecked():
					for eachAsset in self.fileBoxes:
						if eachAsset.text() != 'ALL':
							eachAsset.setChecked(True)
							eachAsset.setStyleSheet("QCheckBox{background-color: grey}")

				else:
					for eachAsset in self.fileBoxes:
						if eachAsset.text() != 'ALL':
							eachAsset.setChecked(False)

	def _fetchMDLAlembicPublish(self):
		"""
		This function will find the checked assets, and then go off and get the latest published alembic asset from the asset folder
		None of this is done off the database btw..
		"""
		pathToAssets        = 'I:/lsapipeline/assets'
		if self.shotNum:
			moveTo          = 'I:/lsapipeline/episodes/ep000/%s/Light/publish/alembic_static' % self.shotNum
		elif self._getShotNumFromMenuName():
			moveTo          = 'I:/lsapipeline/episodes/ep000/%s/Light/publish/alembic_static' % self._getShotNumFromMenuName()
		else:
			cmds.warning('This ENV is not a valid for processing using this tool!')
			return -1

		pathTo = ''

		toProcess = []

		for eachAsset in self.fileBoxes:
			if eachAsset.text() != 'ALL':
				if eachAsset.isChecked():
					toProcess.append(eachAsset.text())
		if toProcess:
			for eachAsset in toProcess:
				if cmds.objExists('%s_hrc' % eachAsset):
					###Prompt to continue here
					self.reply = cmds.confirmDialog(title = "Remove Asset? %s" % eachAsset, message = "Warning you are about to remove %s" % eachAsset, button = ['Continue...','Skip Import'])
					if self.reply == 'Continue...':
						cmds.delete('%s_hrc' % eachAsset)
						self._doIt(eachAsset, pathToAssets, moveTo)
					else:
						pass
				else:
					self._doIt(eachAsset, pathToAssets, moveTo)
		else:
			cmds.warning('No assets selected for importing!!')

	def _doIt(self, eachAsset, pathToAssets, moveTo):
		"""
		Func to process eachAsset from the _fetchMDLAlembicPublish function
		"""
		if 'BLD' in eachAsset:
			pathTo = "%s/Building/%s/MDL/publish/alembic" % (pathToAssets, eachAsset)
		## LND
		elif 'LND' in eachAsset:
			pathTo = "%s/Environment/%s/MDL/publish/alembic" % (pathToAssets, eachAsset)

		if self._isRootFolderThere(rootFolder = pathTo):
			if os.path.isdir(pathTo):
				try:
					maxFile = max(os.listdir(pathTo))
				except ValueError:
					maxFile = []
				if maxFile:
					finalPath = '%s/%s' %(pathTo, maxFile)
					moveIT = '%s\\%s' % (moveTo.replace('/', '\\'), maxFile)
					if os.path.isfile(moveIT):
						os.remove(moveIT)
					print 'Copy in progress for %s' % maxFile
					shutil.copyfile(finalPath, '%s/%s' % (moveTo, maxFile))
				else:
					cmds.warning('FAILED!: Nothing has been published for this asset! Talk to the modelling dept.')

		self._createBaseGroups()
		self._importSingleCache(pathTo, '%s_ABC_STATIC_CACHES_hrc' % self.currentENV, '%s_hrc' % eachAsset)
		for eachAssetCBx in self.fileBoxes:
			if eachAssetCBx.text() == eachAsset:
				eachAssetCBx.setChecked(False)
				eachAssetCBx.setStyleSheet("QCheckBox{background-color: green}")

	def _republishAllAlembicsForENV(self):
		"""
		This helper will republish all the MDL alembic files from the most recently published mb files found in the assets folders
		for every asset associated to the ENV.

		getData = self.sgsrv.find('Asset',  filters = [["code", "is", eachENV]], fields=['code', 'id', 'assets'])
		Finds the ENV name and then gets a list of Sub Assets associated with it from the assets field.

		This is why we want every ENV to be the parent of an asset in the system appropriately.
		"""
		start = time.time()

		## Empty the scene first, or BAD THINGS HAPPEN!!!
		cmds.file(new = True, f = True)

		## Path to the assets folder
		pathToAssets = "I:/lsapipeline/assets" ##Hardcoded yuckiness..

		## Fetch the subAssets for the ENV
		getData = self.sgsrv.find('Asset',  filters = [["code", "is", self.envPulldown.currentText()]], fields=['code', 'id', 'assets'])

		for eachAsset in getData[0]['assets']:
			## BLD
			if 'BLD' in eachAsset['name']:
				assetPublishFolder = "%s/Building/%s/MDL/publish/maya" % (pathToAssets, eachAsset['name'])
			## LND
			elif 'LND' in eachAsset['name']:
				assetPublishFolder = "%s/Environment/%s/MDL/publish/maya" % (pathToAssets, eachAsset['name'])

			assetPublishFolder.replace("/", os.sep)
			if os.path.isdir(assetPublishFolder):
				getLatestPublish = max(os.listdir(assetPublishFolder))
				if getLatestPublish and getLatestPublish.endswith('.mb'):
					latestPublish = '%s/%s' % (assetPublishFolder, getLatestPublish)
					latestPublish.replace("/", os.sep)
					alembicPath = latestPublish.replace('.mb', '.abc').replace('maya', 'alembic').replace('.v', '_ABC.v')
					## Remove current alembic
					if os.path.isfile(alembicPath):
						os.remove(alembicPath)
					## Import the file so we don't have to display anything due to the files prob being saved with tesxtures on etc
					print '====================='
					print 'Importing %s now...' % latestPublish
					try:    cmds.file(latestPublish, i = True, f = True)
					except: cmds.warning('Failed to import %s...' % latestPublish)
					cleanup.removeAllNS()
					print 'Import complete'
					print '====================='

					## Change uv set map1 if the mesh has multiple uv sets for alembic cache
					[cmds.polyUVSet(each, currentUVSet = True, uvSet = 'map1') for each in cmds.ls(type = 'mesh')]

					## Now scan the geo in the scene and preserve the crease information
					print '====================='
					print 'Adding crease SubDivisionMesh attr'
					for each in cmds.ls(type = 'mesh', l = True):
						if not cmds.objExists('%s.SubDivisionMesh' % each):
							try:
								cmds.addAttr('%s' % each, ln = 'SubDivisionMesh', at = 'bool')
								cmds.setAttr("%s.SubDivisionMesh" % each, 1)
							except:
								pass
					print 'Complete..'
					print '====================='

					## Now export back out a new alembic with the version name that should exist in the assembly reference.
					rootName = '%s_hrc' % eachAsset['name']
					# abc_export_cmd = "-attr smoothed -attr SubDivisionMesh -ro -uvWrite -wholeFrameGeo -worldSpace -writeVisibility -fr 1 1 -root %s -file %s" % (rootName, alembicPath)
					abc_export_cmd = "-attr smoothed -attr SubDivisionMesh -ro -uvWrite -wholeFrameGeo -worldSpace -writeVisibility -fr %d %d -root %s -file %s" % (1, 1, rootName, alembicPath)
					try:
						print '====================='
						print 'Exporting %s to alembic cache now to %s' % (rootName, alembicPath)
						cmds.AbcExport(verbose = False, j = abc_export_cmd)
						print 'Export Complete...'
						print '====================='
					except:
						print "Failed to export Alembic Cache!!"
			## Now do a new scene with no save
			cmds.file(new = True, f = True)
		# print 'FINISHED FIXING ALL ALEMBIC PUBLISHES FOR ASSETS FOR ENV: %s'  % eachENV
		print 'TIME: %s' % (time.time()-start)

	def _isRootFolderThere(self, rootFolder):
		"""
		Method used to check if root folder is valid or not eg: I:/lsapipeline/assets
		@param rootFolder: The path to the root folder to check for
		@type rootFolder: String
		"""
		if not os.path.isdir(rootFolder):
			print 'No such root folder found: %s' % rootFolder
			return -1
		else:
			return 1

	def findAlembicPublishes(self, envName = '', rootFolder = 'I:/lsapipeline/assets', moveTo = 'I:/lsapipeline/episodes/ep000/ep000_sh010/Light/publish/alembic_static'):
		"""
		Function to find all the LND asset published alembic MDL publishes and move them into the lighting base shot folder.
		Note this will grab every asset parented to the ENV asset in shotgun. If they are missing from this field they won't be pulled in correctly.
		Also note it was originally intended to process the entire world, so the envList is kinda old now as we're just doing the one ENV at a time.

		@param envName: The name of the ENV we're looking for subAssets of
		@param rootFolder: The path of the rootFolder for the assets to scan for
		@param moveTo: The path of the master shot folders alembic_static we are going to copy the files to
		@type envName: String
		@type rootFolder: String
		@type moveTo: String
		"""
		start = time.time()
		pathToAssets = "I:/lsapipeline/assets"

		getData = self.sgsrv.find('Asset',  filters = [["code", "is", envName]], fields=['code', 'id', 'assets'])
		for eachAsset in getData[0]['assets']:
			## BLD
			if 'BLD' in eachAsset['name']:
				pathTo = "%s/Building/%s/MDL/publish/alembic" % (rootFolder, eachAsset['name'])
			## LND
			elif 'LND' in eachAsset['name']:
				pathTo = "%s/Environment/%s/MDL/publish/alembic" % (rootFolder, eachAsset['name'])

			if self._isRootFolderThere(rootFolder = pathTo):
				if os.path.isdir(pathTo):
					try:
						maxFile = max(os.listdir(pathTo))
					except ValueError:
						maxFile = []
					if maxFile:
						finalPath = '%s/%s' %(pathTo, maxFile)
						moveIT = '%s\\%s' % (moveTo.replace('/', '\\'), maxFile)
						if os.path.isfile(moveIT):
							os.remove(moveIT)
						print 'Copy in progress for %s' % maxFile
						shutil.copyfile(finalPath, '%s/%s' % (moveTo, maxFile))

		self._createBaseGroups(envs[0])
		self._importCaches(moveTo, '%s_ABC_STATIC_CACHES_hrc' % self.currentENV)
		self._createSets()

	def _importSingleCache(self, folderPath, parentGrp, cacheName):
		"""
		Function to import the alembics and parent them to the right group
		@param folderPath: Path to the folder for the caches to import
		@param parentGrp: The name of the group to parent the alembics to.
		@type folderPath: String
		@type parentGrp: String
		"""
		try:
			findLatest = max(os.listdir(folderPath))
		except:
			findLatest = []

		if findLatest:
			try:
				cmds.AbcImport('%s/%s' % (folderPath, findLatest), reparent  = parentGrp, setToStartFrame = True)
				self._createSets()
			except RuntimeError:
				cmds.warning('Failed to import cache! %s/%s' % (folderPath, findLatest))

			## Now add the version number to the grp
			versionNumber = findLatest.split('.')[-2].split('v')[-1]
			self._addVersionTag('%s' % cacheName, versionNumber)
		else:
			cmds.warning('Nothing published for %s !' % cacheName)

	def _importCaches(self, folderPath, parentGrp):
		"""
		Function to import the alembics and parent them to the right group
		@param folderPath: Path to the folder for the caches to import
		@param parentGrp: The name of the group to parent the alembics to.
		@type folderPath: String
		@type parentGrp: String
		"""
		for eachCache in os.listdir(folderPath):
			try:
				cmds.AbcImport('%s/%s' % (folderPath, eachCache), reparent  = parentGrp, setToStartFrame = True)
			except RuntimeError:
				cmds.warning('Failed to import cache! %s/%s' % (folderPath, eachCache))
		self._createSets()

	def _createBaseGroups(self):
		"""
		Function to create the base grps for the caches to be parented to.
		@param envName: The name of the enviroment we are importing into.
		@type envName: String
		"""
		envName = self.currentENV
		if envName:
			grps = ['%s_ABC_STATIC_CACHES_hrc' % self.currentENV, '%s_Core_Archives_hrc' % self.currentENV]
		else:
			grps = ['%s_ABC_STATIC_CACHES_hrc' % self.envPulldown.currentText(), '%s_Core_Archives_hrc' % self.envPulldown.currentText()]

		for eachGrp in grps:
			if not cmds.objExists(eachGrp):
				cmds.group(n = eachGrp, em = True)

	def _createSets(self):
		"""
		Function used to put the alembic caches into the right sets for use witht ehlayout tool deved in house at LSky
		The lists were built from the base ENV scenes pre the cleanup. If new buildings are added to the sets they should be added to the lists
		below
		"""

		## Now check for the sets

		## Sets for MIDDLE HARBOUR
		if self.envPulldown.currentText() == 'ENV_MIDDLEHARBOUR_STATIC':
			animBuildList = ['BBB_CanoeBoatHouse_BLD', 'AI_Jetty_Dock_BLD_hrc', 'BBB_BowserBoatHouse_Dock_BLD_hrc','BBB_DockyardPier_Dock_BLD_hrc','BBB_Jetty_Dock_BLD_hrc','BBB_MainStorage_Dock_BLD_hrc','BBB_Office_Dock_BLD_hrc','BBB_TheMarina_Dock_BLD_hrc','BBB_DryDockInterior_BLD_hrc','BBB_Int_TerrysStorageshed_BLD_hrc','BBB_ZipBoatHouse_BLD_hrc', 'BBB_ZipBoathouseInterior_BLD_hrc','BBB_SydneyBoatHouse_BLD_hrc', 'BBB_SydneyBoathouseInterior_BLD_hrc']
			setList = {
					   "BBBEastPointLND"    : ["BBB_Silo_BLD_hrc", "BBB_StorageShed02_BLD_hrc", "BBB_TerrysBoatHouse_BLD_hrc", "BBB_TerrysStorageShed_BLD_hrc", "BBB_DockyardPier_BLD_hrc", "BBB_EastPoint_LND_hrc"],
					   "BBBMidPointLND"     : ["BBB_Storage001_BLD_hrc", "BBB_Storage002_BLD_hrc", "BBB_StorageShed_BLD_hrc", "BBB_TheMarina_BLD_hrc", "BBB_Gen011_BLD_hrc", "BBB_Jetty_BLD_hrc", "BBB_MainStorage_BLD_hrc", "BBB_Office_BLD_hrc", "BBB_PirateShip_BLD_hrc", "BBB_MidPoint_LND_hrc", "BBB_DryDockMainBuilding_BLD_hrc", "BBB_DryDockInterior_BLD_hrc"],
					   "BBBWestPointLND"    : ["BBB_BowserBoatHouse_BLD_hrc", "BBB_Gen002_BLD_hrc", "BBB_Gen008_BLD_hrc", "BBB_Gen009_BLD_hrc", "BBB_Gen010_BLD_hrc", "BBB_Gen007_BLD_hrc", "BBB_Gen003_BLD_hrc", "BBB_Gen004_BLD_hrc", "BBB_Gen001_BLD_hrc", "BBB_Gen005_BLD_hrc", "BBB_Gen006_BLD_hrc", "BBB_WestPoint_LND_hrc", "BBB_ZipBoatHouse_BLD_hrc", "BBB_SydneyBoatHouse_BLD_hrc"],
					   "TWRLND"             : ["TWR_LND_hrc"],
					   }
		## Sets for MIDDLE HARBOUR EAST
		if self.envPulldown.currentText() == 'ENV_MIDDLEHARBOUR_EAST_STATIC':
			animBuildList = []
			setList = {
					   "AILND"              : ["AI_LightHouse_BLD_hrc", "AI_LND_hrc", "AI_Jetty_BLD_hrc"],
					   "FWBSandbarLND"      : ["FWB_Rock001_LND_hrc", "FWB_Rock002_LND_hrc", "FWB_Rock003_LND_hrc", "FWB_Rock004_LND_hrc", "FWB_Rock005_LND_hrc", "FWB_Rock006_LND_hrc", "FWB_Rock007_LND_hrc", "FWB_Rock008_LND_hrc", "FWB_BeachHouse_LND_hrc", "FWB_Sandbar_LND_hrc", "FWB_Fingers_LND_hrc", ],
					   "HCEastLND"          : ["HC_ExtraBlockingRock_LND_hrc", "HC_East_LND_hrc", "HC_Island010_E_LND_hrc", "HC_Island010_F_LND_hrc", "HC_Waterfall001_LND_hrc", "HC_Bridge001_A_LND_hrc", "HC_Bridge001_B_LND_hrc", "HC_Bridge001_C_LND_hrc", "HC_Cave001_LND_hrc", "HC_Island006_A_LND_hrc", "HC_Island006_B_LND_hrc", "HC_Island007_LND_hrc", "HC_Island010_A_LND_hrc", "HC_Island010_B_LND_hrc", "HC_Island010_C_LND_hrc", "HC_Island010_D_LND_hrc"],
					   "HCNorthLND"         : ["HC_North_LND_hrc", "HC_Entrance002_LND_hrc", "HC_Island001_A_LND_hrc", "HC_Island001_B_LND_hrc", "HC_Island001_C_LND_hrc", "HC_Island001_D_LND_hrc", "HC_Island001_E_LND_hrc", "HC_Island001_F_LND_hrc", "HC_Island001_G_LND_hrc", "HC_Island001_H_LND_hrc", "HC_Island001_I_LND_hrc", "HC_Island001_J_LND_hrc", "HC_Island002_A_LND_hrc", "HC_Island002_B_LND_hrc", "HC_Island003_A_LND_hrc", "HC_Island003_B_LND_hrc", "HC_Island004_LND_hrc"],
					   "HCSouthLND"         : ["HC_South_LND_hrc"],
					   "HCWestLND"          : ["HC_Entrance001_LND_hrc", "HC_West_LND_hrc", "HC_ShipWreck_BLD_hrc", "HC_Island008_LND_hrc", "HC_Island009_LND_hrc"],
					   }

		## Sets for WEST HARBOUR
		elif self.envPulldown.currentText() == 'ENV_WESTHARBOUR_STATIC':
			animBuildList = ['BB_PP_JettyDock_01_BLD', 'BB_PP_JettyDock_02_BLD', 'DingleIsland_JettyDock_BLD', 'LittleTown_Dock001_BLD', 'LittleTown_Dock002_BLD', 'MulliganTown_JettyDock_01_BLD', 'MulliganTown_JettyDock_02_BLD', 'BB_OF_Lease_BLD']
			setList = {
					   'AdmiralBridgeLND'       : ["AdmiralBridge_LND_hrc"],
					   'BBOysterFarmLND'        : ["BB_OysterFarm_LND_hrc", "BB_OF_Hut005_BLD_hrc", "BB_OF_Lease_BLD_hrc", "BB_OF_Hut004_BLD_hrc", "BB_OF_Hut003_BLD_hrc", "BB_OF_Hut002_BLD_hrc", "BB_OF_Hut001_BLD_hrc"],
					   'BBPointPeriwinkleLND'   : ["BB_PointPeriwinkle_LND_hrc", "BB_PP_Jetty_BLD_hrc", "BB_PP_Huts_BLD_hrc", "BB_PP_JettyDock_01_BLD_hrc", "BB_PP_JettyDock_02_BLD_hrc"],
					   'DingleIslandLND'        : ["DingleIsland_JettyDock_BLD_hrc", "DingleIsland_LND_hrc"],
					   'LittleTownLND'          : ["LittleTown_EastBuilding_BLD_hrc", "LittleTown_MidBuilding_BLD_hrc", "LittleTown_MidGenBuilding_BLD_hrc", "LittleTown_WestBuilding_BLD_hrc", "LittleTown_East_LND_hrc", "LittleTown_Mid_LND_hrc", "LittleTown_West_LND_hrc"],
					   'MuliganTownLND'         : ["MulliganTown_JettyBuilding_BLD_hrc", "MulliganTown_EastBuilding_BLD_hrc", "MulliganTown_WestBuilding_BLD_hrc", "MulliganTown_EastGenBuilding_BLD_hrc", "MulliganTown_WestGenBuilding_BLD_hrc", "MulliganTown_SateliteHouse_BLD_hrc", "MulliganTown_JettyDock_01_BLD_hrc", "MulliganTown_JettyDock_02_BLD_hrc", "MulliganTown_East_LND_hrc", "MulliganTown_West_LND_hrc"]
					   }

		## Sets for BIG TOWN
		elif self.envPulldown.currentText() == 'ENV_BIGTOWN_STATIC':
			animBuildList = ['BigPort_Shipyard_Dock_BLD']
			setList = {
					   'BigNorthPortLND'        : ["BigNorthPort_LND_hrc", "BigNorthPort_Building_BLD_hrc"],
					   'BigPortLND'             : ["BigPort_LND_hrc", "BigPort_Shipyard_BLD_hrc"],
					   'BigTown01LND'           : ["BigTown_01_LND_hrc", "BigTown_01_Building_BLD_hrc"],
					   'BigTown02LND'           : ["BigTown_02_LND_hrc", "BigTown_02_Building_BLD_hrc"],
					   'BigTownLND'             : ["BigTown_LND_hrc", "BigTown_Building_BLD_hrc"],
					   }

		## Sets for THEHEADS
		elif self.envPulldown.currentText() == 'ENV_THEHEADS_STATIC':
			animBuildList = []
			setList = {
					   'THIrisleLND'        : ['TH_IrisIsle_LND_hrc'],
					   'THMangoShore01LND'  : ["TH_MangoShore01_LND_hrc", "TH_MangoShore02_LND_hrc"],
					   'THRainbowShoreLND'  : ["TH_RainbowCliffs_LND_hrc", "TH_RainbowShore01_LND_hrc", "TH_RainbowShore02_LND_hrc"]
					   }
		cmds.select(clear = True)
		for setName, itemList in setList.items():
			if not cmds.objExists(setName):
				cmds.sets(n = setName)

			for eachHRC in itemList:
				if eachHRC not in animBuildList:
					try:
						cmds.sets(eachHRC, e = True, forceElement = setName)
						print 'Successfully added %s to %s' % (eachHRC, setName)
					except ValueError:
						print 'Failed to add %s' % eachHRC

	def _reconnectDuplicates(self, eachGeo = '', core_archive = ''):
		"""
		Stuff...
		"""
		## Fetch the Geo Shaders
		## Now reconnect
		getCoreConnections = cmds.listConnections('%s.message' % core_archive, plugs = True)
		if not cmds.objExists(core_archive):
			cmds.warning('_reconnectDuplicates needs a valid core_archive to work!!\n\t%s is invalid!' % core_archive)
		else:
			if '%s.miGeoShader' % eachGeo not in getCoreConnections:
				#print 'Reconnected %s to %s' % (eachGeo, core_archive)
				cmds.connectAttr('%s.message' % core_archive, '%s.miGeoShader' % eachGeo, force = True)

	def _fixTheFuckingCores(self):
		"""
		This is used to clean sweep the static scenes and remove the duplicate Namespaces and reconnect the bases to the duplicates
		"""

		removedNameSpaces = []
		## Remove duplicate root core namespaces
		getAllNameSpaces = cmds.namespaceInfo(listOnlyNamespaces = True)
		for eachNS in getAllNameSpaces:
			if eachNS.endswith('1'):
				print 'Removing %s' % eachNS
				cmds.namespace(removeNamespace = eachNS, mergeNamespaceWithRoot = True)
				removedNameSpaces.append(eachNS.replace('1', '').replace('_CORE', ''))

		## Remove duplicate base cores
		for each in cmds.ls(type = 'core_archive'):
			if '1'in each:
				print 'Cleaned rootCore %s from scene...' % each
				cmds.delete(each)

		## Now find all geo with the core name in it and proceess it for reconnection
		for eachCore in removedNameSpaces:
			#print eachCore
			## Check child _hrc grps for processing
			getAllGeo = [eachGeo for eachGeo in cmds.ls('*%s*' % eachCore) if cmds.nodeType(eachGeo) == 'transform']
			for eachGeo in getAllGeo:
				self._reconnectDuplicates(eachGeo, '%s_CORE_Geoshader' % eachCore)

		coreLib.cleanupDeadCoreArchives()

	def _rebuildCoresForSelected(self):
		"""
		Function to help delete all cores and rebuild for selected LND
		"""
		pass

