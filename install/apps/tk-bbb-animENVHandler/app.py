"""
Copyright (c) 2013 Kok Gin Yih
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
import xml.etree.cElementTree as ET

if 'T:/software/lsapipeline/tools' not in sys.path:
	sys.path.append('T:/software/lsapipeline/tools')

if 'T:/software/python-api/' not in sys.path:
	sys.path.append('T:/software/python-api/')

if 'T:/software/lsapipeline/custom' not in sys.path:
	sys.path.append('T:/software/lsapipeline/custom')
import maya_asset_MASTERCLEANUPCODE as cleanup
#reload(cleanup)

class AnimENVHandler(Application):
	def init_app(self):
		# make sure that the context has an entity associated - otherwise it wont work!
		if self.context.entity is None:
			raise tank.TankError("Cannot load the OceanGenerator application! "
								 "Your current context does not have an entity (e.g. "
								 "a current Shot, current Asset etc). This app requires "
								 "an entity as part of the context in order to work.")
		getDisplayName = self.get_setting('display_name')
		self.engine.register_command(getDisplayName, self.run_app)
		debug(self, method = 'init_app', message = 'Anim ENV Handler Loaded...', verbose = False)

	def run_app(self):
		debug(self, method = 'run_app', message = 'Anim ENV Handler...', verbose = False)
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
		context = self.app.context
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
		self.lightAlembicFolder = 'I:/lsapipeline/episodes/ep000/%s/Light/publish/alembic_anim' % self.shotNum

		## Now build the UI
		self.mainLayout     = QtGui.QHBoxLayout(self)
		self.leftSideLayout = QtGui.QVBoxLayout(self)
		debug(self.app, method = 'MainUI', message = 'self.mainLayout built...', verbose = False)

		##########################
		### ENV SELECTION PULLDOWN
		self.envLayout      = QtGui.QVBoxLayout(self)
		self.envPulldown    = QtGui.QComboBox()

		getENVS = self.sgsrv.find('Asset',  filters = [["code", "contains", 'ENV_'], ["code", "not_contains", '_ENV_'], ["code", "not_contains", 'WORLDMAP'], ["code", "not_contains", 'TSETbuild']], fields=['code'])
		debug(self.app, method = 'MainUI', message = 'getENVS: %s' % getENVS, verbose = False)

		if self.shotNum:
			for each in getENVS:
				if each['code'] == self.currentENV:
					self.envPulldown.addItem(each['code'])
					self.lightAlembicFolder = 'I:/lsapipeline/episodes/ep000/%s/Light/publish/alembic_anim' % self.shotNum

			self.envPulldown.setCurrentIndex(self.envPulldown.findText(self.currentENV))
			debug(self.app, method = 'MainUI', message = 'self.envPulldown setCurrentIndex...', verbose = False)
		else:
			for each in getENVS:
				if 'ANIM' in each['code']:
					self.envPulldown.addItem(each['code'])

		self.fetchAssetListButton = QtGui.QPushButton(Icon('refresh.png'), 'Fetch Asset List')
		self.fetchAssetListButton.setStyleSheet("QPushButton {text-align : left}")
		self.fetchAssetListButton.released.connect(self._fetchAssetList)
		debug(self.app, method = 'MainUI', message = 'self.fetchAssetListButton built...', verbose = False)

		self.importAssetButton = QtGui.QPushButton(Icon('alembic.png'), 'Import latest Pub ABC')
		self.importAssetButton.setStyleSheet("QPushButton {text-align : left}")
		self.importAssetButton.released.connect(self._fetchMDLAlembicPublish)
		debug(self.app, method = 'MainUI', message = 'self.importAssetButton built...', verbose = False)

		self.checkMDLButton = QtGui.QPushButton(Icon('refresh.png'), 'Check For RIG Publishes')
		self.checkMDLButton.setStyleSheet("QPushButton {text-align : left}")
		self.checkMDLButton.released.connect(self._checkVersionsAgainstPublishes)
		debug(self.app, method = 'MainUI', message = 'self.checkMDLButton built...', verbose = False)

		self.checkSRFXMLButton = QtGui.QPushButton(Icon('refresh.png'), 'Check For SRF Publishes')
		self.checkSRFXMLButton.setStyleSheet("QPushButton {text-align : left}")
		self.checkSRFXMLButton.released.connect(self._checkSRFVersionsAgainstPublishes)

		self.lambert1Button = QtGui.QPushButton(Icon('refresh.png'), 'Check lambert1 objects')
		self.lambert1Button.setStyleSheet("QPushButton {text-align : left}")
		self.lambert1Button.released.connect(self._lambert1Object)

		self.checkFileInPathButton = QtGui.QPushButton(Icon('refresh.png'), 'Check Invalid FileIn Path')
		self.checkFileInPathButton.setStyleSheet("QPushButton {text-align : left}")
		self.checkFileInPathButton.released.connect(self.checkFileInPath)

		self.checkNonManifoldButton = QtGui.QPushButton(Icon('refresh.png'), 'Check Non-Manifold Geometry')
		self.checkNonManifoldButton.setStyleSheet("QPushButton {text-align : left}")
		self.checkNonManifoldButton.released.connect(self.cleanupNonManifoldGeometry)

		if context.step['name'] == 'Anm':
			self.creaseXMLButton = QtGui.QPushButton('Create crease XML')
			self.creaseXMLButton.released.connect(self._writeCreaseToXML)
			self.creaseXMLButton.setEnabled(True)

		if context.step['name'] == 'Light':
			self.fetchCreaseXMLButton = QtGui.QPushButton('Fetch latest published crease XML')
			self.fetchCreaseXMLButton.released.connect( partial(self._getCreaseFromXML, rootPrefix = 'ENV_DOCKS_STATICANIM_ABC_ANIM_CACHES_hrc') )
			self.fetchCreaseXMLButton.setEnabled(True)

		self.republishALL = QtGui.QPushButton('Publish ABC from ANM')
		self.republishALL.released.connect(self._republishAllAlembicsForENV)
		self.republishALL.setEnabled(True)

		## Add stuff to the env layout
		self.envLayout.addWidget(self.envPulldown)
		self.envLayout.addWidget(self.fetchAssetListButton)
		self.envLayout.addWidget(self.importAssetButton)
		self.envLayout.addWidget(self.checkMDLButton)
		self.envLayout.addWidget(self.checkSRFXMLButton)
		self.envLayout.addWidget(self.lambert1Button)
		self.envLayout.addWidget(self.checkFileInPathButton)
		self.envLayout.addWidget(self.checkNonManifoldButton)
		self.envLayout.addWidget(self.republishALL)
		if context.step['name'] == 'Anm':
			self.envLayout.addWidget(self.creaseXMLButton)
		if context.step['name'] == 'Light':
			self.envLayout.addWidget(self.fetchCreaseXMLButton)

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
		self.envPulldown.currentIndexChanged.connect( partial(self._getShotNumFromMenuName) )
		self.envPulldown.currentIndexChanged.connect( partial(self._fetchAssetList) )

	def _prettyPrintXML(self, elem, level = 0):
		i = '\n' + level * '	'
		if len(elem):
			if not elem.text or not elem.text.strip():
				elem.text = i + '	'
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
			for elem in elem:
				self._prettyPrintXML(elem, level + 1)
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
		else:
			if level and ( not elem.tail or not elem.tail.strip() ):
				elem.tail = i

	def _getCreaseFromXML(self, rootPrefix = ''):
		scene_path = os.path.abspath( cmds.file(query = True, sn = True) )
		xmlPath = '%s/Anm/publish/crease_xml/ep000_Docks_Addon.xml' % '/'.join( os.path.abspath( cmds.file(query = True, sn = True) ).replace('\\', '/').split('/')[:5] ) if scene_path else ''

		print xmlPath

		if os.path.isfile(xmlPath):
			tree = ET.parse(xmlPath)
			root = tree.getroot()
			if root.tag == 'CreaseXML':

				for mesh in root.getchildren():
					mesh_name = mesh.attrib.get('name')
					mesh_name = '|'.join( [x.split(':')[-1] for x in mesh_name.split('|')] )
					mesh_name = '%s%s' % (rootPrefix, mesh_name) if rootPrefix else mesh_name

					if cmds.objExists(mesh_name):
						for edge in mesh.getchildren():
							vertexA 	= int( edge.attrib.get('vertexA') )
							vertexB 	= int( edge.attrib.get('vertexB') )
							creaseValue = edge.attrib.get('creaseValue')
							edgeID 		= cmds.polyListComponentConversion('%s.vtx[%d]' % (mesh_name, vertexA), '%s.vtx[%d]' % (mesh_name, vertexB), fromVertex = 1, toEdge = 1, internal = 1)[0].split('.')[-1]

							if '-inf' not in creaseValue:
								cmds.polyCrease( '%s.%s' % (mesh_name, edgeID), value = float(creaseValue) )
					else:
						cmds.warning('%s doesn\'t exist, skipping...' % mesh_name)
			else:
				cmds.warning('Not a valid xml...')
		else:
			cmds.warning('Not a valid crease xml path...')

	def _writeCreaseToXML(self):
		scene_path = os.path.abspath( cmds.file(query = True, sn = True) ) # I:\bubblebathbay\episodes\ep106\ep106_sh030\FX\work\maya\ep106sh030.v025.ma
		xmlPath = '%s/publish/crease_xml/ep000_Docks_Addon.xml' % '/'.join( os.path.abspath( cmds.file(query = True, sn = True) ).replace('\\', '/').split('/')[:6] ) if scene_path else ''

		if os.path.isdir( os.path.dirname(xmlPath) ):
			## Get all mesh in scene with all their edges intact i.e. |pCube1|pCubeShape1.e[0:11] (Filter out intermediate object as well as they don't get cache out)
			meshes = ['%s.e[0:%s]' % ( mesh, cmds.polyEvaluate(mesh, edge = True) - 1 ) for mesh in cmds.ls(type = 'mesh', long = True) if not cmds.getAttr('%s.intermediateObject' % mesh) if cmds.polyEvaluate(mesh, edge = True)]
			if meshes:
				edge_creases = []

				for mesh in meshes:
					mesh_name = mesh.split('.')[0]
					edges = cmds.polyCrease(mesh, value = True, q = True)

					if edges:
						crease_edges = []
						for edge, value in enumerate(edges, start = 0):
							if value > 0: ## 0 means no crease, more than 0 means crease...

								## 2 vertices = 1 edge. Therefore, get edge's vertices id...
								crease_edges.append(
														(
															filter( None, cmds.polyInfo('%s.e[%s]' % (mesh_name, edge), edgeToVertex = True)[0].split(':')[-1].replace('Hard', '').replace('\n', '').split(' ') )[0], ## Vertex A
															filter( None, cmds.polyInfo('%s.e[%s]' % (mesh_name, edge), edgeToVertex = True)[0].split(':')[-1].replace('Hard', '').replace('\n', '').split(' ') )[1], ## Vertex B
															str(value), ## Crease value (Reason why we put it as string is because somehow maya sometimes return value "-inf" which's going to be troublesome when applying crease to poly later...
														)
													)
						edge_creases.append((mesh_name, crease_edges)) if crease_edges else None

				if edge_creases:
					## Process root
					root = ET.Element('CreaseXML')

					for each in edge_creases:
						mesh = '|'.join( [x.split(':')[-1] for x in each[0].split('|')] ) ## Get rid of object names that has ":" in it as it will be stripped out during alembic cache anyways...
						if 'geo_hrc' in mesh:
							mesh = '|%s' % '|'.join( mesh.split('|')[([i for (i, x) in enumerate(mesh.split('|'), start = 0) if x == 'geo_hrc'][0] - 1):] ) ## Get full name until root of geo_hrc

						meshElem = ET.SubElement(root, 'Mesh')
						meshElem.set('name', mesh)

						for child in each[1]:
							vertexA		= child[0]
							vertexB		= child[1]
							creaseValue	= child[2]

							edgeElem = ET.SubElement(meshElem, 'Edge')
							edgeElem.set('vertexA', vertexA)
							edgeElem.set('vertexB', vertexB)
							edgeElem.set('creaseValue', creaseValue)

					## Make directory if it doesn't exist
					if not os.path.exists( os.path.dirname(xmlPath) ):
						os.makedirs( os.path.dirname(xmlPath) )

					## Process XML to output nicely so it's human readable i.e. not everything in 1 line
					self._prettyPrintXML(root)
					tree = ET.ElementTree(root)

					## Output .xml into directory
					tree.write(xmlPath, encoding = 'utf-8')

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

		if 'ep000_Docks_Addon' in self.workSpace:
			envName = 'ENV_DOCKS_STATICANIM'
			shotNum = 'ep000_Docks_Addon'
		else:
			envName = None
			shotNum = None

		return shotNum, envName

	def _getShotNumFromMenuName(self, index = ''):
		self.workSpace = cmds.workspace(q = True, fn = True)
		envName = ''
		shotNum = ''

		if self.envPulldown.currentText() == 'ENV_DOCKS_STATICANIM':
			shotNum = 'ep000_Docks_Addon'
		else:
			shotNum = None

		return shotNum

	def _addVersionTag(self, assetName, versionNumber):
		if cmds.objExists('%s.rigVersion' % assetName):
			cmds.deleteAttr('%s.rigVersion' % assetName)
		try:
			cmds.addAttr(assetName, ln = 'rigVersion', at = 'long', dv = 0)
		except:
			pass

		cmds.setAttr( '%s.rigVersion' % assetName, int(versionNumber) )

	def _checkVersionsAgainstPublishes(self):
		## Path to the assets folder
		pathToAssets = "I:/lsapipeline/assets"
		character_rootdirs = [os.path.join(pathToAssets, dir).replace('\\', '/') for dir in os.listdir(pathToAssets) if 'Character' in dir or 'Building' in dir]
		character_subdirs = [os.path.join(rootDir, subDir).replace('\\', '/') for rootDir in character_rootdirs for subDir in os.listdir(rootDir) if 'CHAR_' in subDir or '_BLD' in subDir]
		RIGVersNum = ''

		## Fetch the subAssets for the ENV
		getData = self.sgsrv.find('Asset', filters = [["code", "is", self.envPulldown.currentText()]], fields = ['code', 'id', 'assets'])

		## Now can the checkboxes and see which assets arechecked
		if self.fileBoxes:
			for eachAsset in self.fileBoxes:
				if eachAsset.isChecked():
					for eachSGAsset in getData[0]['assets']:
						if eachSGAsset['name'] == eachAsset.text():

							assetFolder = [ subDir for subDir in character_subdirs if os.path.basename(subDir) in eachSGAsset['name'] ][0]
							assetPublishFolder = '%s/RIG/publish/maya' % assetFolder if assetFolder else None

							if os.path.isdir(assetPublishFolder):
								try:    getLatestPublish = max( os.listdir(assetPublishFolder) )
								except: getLatestPublish = []

								if getLatestPublish and getLatestPublish.endswith('.mb'):
									RIGVersNum = int(getLatestPublish.split('.')[-2].split('v')[-1])

							try:
								getAssetVersion = cmds.getAttr( '%s_hrc.rigVersion' % eachAsset.text() )
							except ValueError:
								getAssetVersion = None

							if getAssetVersion:
								if not getAssetVersion == RIGVersNum:
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
		pathToAssets = "I:/lsapipeline/assets"
		character_rootdirs = [os.path.join(pathToAssets, dir).replace('\\', '/') for dir in os.listdir(pathToAssets) if 'Character' in dir or 'Building' in dir]
		character_subdirs = [os.path.join(rootDir, subDir).replace('\\', '/') for rootDir in character_rootdirs for subDir in os.listdir(rootDir) if 'CHAR_' in subDir or '_BLD' in subDir]
		XMLVersNum = ''

		## Fetch the subAssets for the ENV
		getData = self.sgsrv.find('Asset', filters = [["code", "is", self.envPulldown.currentText()]], fields = ['code', 'id', 'assets'])

		## Now can the checkboxes and see which assets are checked
		if self.fileBoxes:
			for eachAsset in self.fileBoxes:
				if eachAsset.isChecked():
					#print 'Checking %s ...' % eachAsset.text()
					for eachSGAsset in getData[0]['assets']:
						if eachSGAsset['name'] == eachAsset.text():

							assetFolder = [ subDir for subDir in character_subdirs if os.path.basename(subDir) in eachSGAsset['name'] ][0]
							assetPublishFolder = '%s/SRF/publish/xml' % assetFolder if assetFolder else None

							if os.path.isdir(assetPublishFolder):
								try:    getLatestPublish = max(os.listdir(assetPublishFolder))
								except: getLatestPublish = []

								if getLatestPublish and getLatestPublish.endswith('.xml'):
									XMLVersNum = int(getLatestPublish.split('.')[-2].split('v')[-1])

							try:
								getAssetSRFVersion = cmds.getAttr('%s_hrc.SRFversion' % eachAsset.text())
							except ValueError:
								getAssetSRFVersion = None

							if getAssetSRFVersion:
								if not getAssetSRFVersion == XMLVersNum:
									print '!!HIGHER VER EXISTS: %s_hrc:%s \t %s' % (eachAsset.text(), getAssetSRFVersion, getLatestPublish)
									eachAsset.setStyleSheet("QCheckBox{background-color: red}")
								else:
									eachAsset.setStyleSheet("QCheckBox{background-color: green}")
									eachAsset.setChecked(False)
									print 'PASSED: version match %s' % (getLatestPublish)
							else:
								eachAsset.setStyleSheet("QCheckBox{background-color: red}")
								cmds.warning( '%s IS MISSING VERSION INFORMATION! PLEASE FIX!!!' % eachAsset.text() )

			for eachAsset in self.fileBoxes:
				if eachAsset.isChecked() and eachAsset.text() == 'ALL':
					eachAsset.setChecked(False)
					eachAsset.setStyleSheet("QCheckBox{background-color: green}")

	def _checkVersionNumber(self, assetName, versionNumber, attrType):
		"""
		Returns if the version number for an asset in the scene matches that of the asset in the static_folder
		"""
		foundVersion = False

		## Path to the assets folder
		pathToAssets = "I:/lsapipeline/assets"
		character_rootdirs = [os.path.join(pathToAssets, dir).replace('\\', '/') for dir in os.listdir(pathToAssets) if 'Character' in dir or 'Building' in dir]
		character_subdirs = [os.path.join(rootDir, subDir).replace('\\', '/') for rootDir in character_rootdirs for subDir in os.listdir(rootDir) if 'CHAR_' in subDir or '_BLD' in subDir]

		assetFolder = [subDir for subDir in character_subdirs if os.path.basename(subDir) in assetName][0]
		assetPublishFolder = ''
		if attrType == 'RIG':
			assetPublishFolder = '%s/RIG/publish/maya' % assetFolder if assetFolder else None
		elif attrType == 'SRF':
			assetPublishFolder = '%s/SRF/publish/xml' % assetFolder if assetFolder else None

		if os.path.isdir(assetPublishFolder):
			try:    getLatestPublish = max( os.listdir(assetPublishFolder) )
			except: getLatestPublish = []

			if getLatestPublish:
				getlatestVersionNum = int( getLatestPublish.split('.')[-2].split('v')[-1] )
				if int(versionNumber) == int(getlatestVersionNum):
					foundVersion = True
			else:
				cmds.warning('There is no asset for %s found in the lighting anim alembic folder.' % assetName)

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

					## Now check the version of RIG and SRF
					if cmds.objExists('%s_hrc.rigVersion' % eachAsset['name']):
						if not self._checkVersionNumber(eachAsset['name'], cmds.getAttr('%s_hrc.rigVersion' % eachAsset['name']), attrType = 'RIG'):
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

	def _cleanupShit(self):
		try:
			cmds.delete(cmds.ls('rig_hrc'))
		except:
			pass
		try:
			cmds.delete(cmds.ls('parts_hrc'))
		except:
			pass
		try:
			cmds.delete(cmds.ls('collisionNurbsHulls'))
		except:
			pass

		for each in cmds.ls(type = 'transform'):
			if 'Constraint' in each:
				cmds.delete(each)

	def _fetchMDLAlembicPublish(self):
		"""
		This function will find the checked assets, and then go off and get the latest published alembic asset from the asset folder
		None of this is done off the database btw..
		"""
		pathToAssets        = 'I:/lsapipeline/assets'
		if self.shotNum:
			moveTo          = 'I:/lsapipeline/episodes/ep000/%s/Light/publish/alembic_anim' % self.shotNum
		elif self._getShotNumFromMenuName():
			moveTo          = 'I:/lsapipeline/episodes/ep000/%s/Light/publish/alembic_anim' % self._getShotNumFromMenuName()
		else:
			cmds.warning('This ENV is not a valid for processing using this tool!')
			return -1

		if os.path.isdir(moveTo):
			getData = self.sgsrv.find('Asset', filters = [["code", "is", self.envPulldown.currentText()]], fields = ['code', 'id', 'assets'])
			subAssets = [ '%s_hrc' % eachAsset['name'] for eachAsset in getData[0]['assets'] if cmds.objExists('%s_hrc' % eachAsset['name']) ]

			reimport_cache = True

			## Prompt to continue here
			if subAssets:
				self.reply = cmds.confirmDialog(title = 'Remove all sub assets?', message = 'Warning you are about to remove all the sub assets!', button = ['Continue...', 'Skip Import'])
				if self.reply == 'Continue...':
					## Go through all the _hrc asset and delete the fuck off the scene ya go...
					[cmds.delete(subAsset) for subAsset in subAssets]
				elif self.reply == 'Skip Import':
					reimport_cache = False

			## Find latest .abc alembic anim cache in ENV's published directory...
			if reimport_cache:
				try:    findLatest = max( os.listdir(moveTo) )
				except: findLatest = []
				if findLatest:
					## Create base group name template according to ENV's name...
					if self.currentENV:
						groupName = '%s_ABC_ANIM_CACHES_hrc' % self.currentENV
					else:
						groupName = '%s_ABC_ANIM_CACHES_hrc' % self.envPulldown.currentText()
					## Create the group if it doesn't exist...
					if not cmds.objExists(groupName):
						cmds.group(n = groupName, em = True)

					try:
						cmds.AbcImport('%s/%s' % (moveTo, findLatest), reparent  = groupName, setToStartFrame = True)
						self._cleanupShit()
						self._fetchAssetList()
					except RuntimeError:
						cmds.warning( 'Failed to import cache! %s/%s' % (moveTo, findLatest) )
				else:
					cmds.warning('Nothing published for %s !' % self.shotNum)

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

	def _importSingleCache(self, folderPath, parentGrp, cacheName):
		"""
		Function to import the alembics and parent them to the right group
		@param folderPath: Path to the folder for the caches to import
		@param parentGrp: The name of the group to parent the alembics to.
		@type folderPath: String
		@type parentGrp: String
		"""
		try:    findLatest = max(os.listdir(folderPath))
		except: findLatest = []

		if findLatest:
			try:
				cmds.AbcImport('%s/%s' % (folderPath, findLatest), reparent  = parentGrp, setToStartFrame = True)
			except RuntimeError:
				cmds.warning('Failed to import cache! %s/%s' % (folderPath, findLatest))
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

	def _republishAllAlembicsForENV(self):
		"""
		This helper will republish all the MDL alembic files from the most recently published mb files found in the assets folders
		for every asset associated to the ENV.

		getData = self.sgsrv.find('Asset',  filters = [["code", "is", eachENV]], fields=['code', 'id', 'assets'])
		Finds the ENV name and then gets a list of Sub Assets associated with it from the assets field.

		This is why we want every ENV to be the parent of an asset in the system appropriately.
		"""
		## Path to the assets folder
		assetWorkFolder = 'I:/lsapipeline/episodes/ep000/%s/Anm/work/maya' % self.shotNum

		if os.path.isdir(assetWorkFolder):
			getLatestScene = [each for each in os.listdir(assetWorkFolder) if each.endswith('.ma')]
			getLatestScene = max(getLatestScene)
			if getLatestScene:
				latestScene = '%s/%s' % (assetWorkFolder, getLatestScene)
				latestScene.replace("/", os.sep)
				alembicPath = latestScene.replace('Anm', 'Light').replace('work', 'publish').replace('.ma', '.abc').replace('maya', 'alembic_anim').replace('.v', '_ABC.v')
				## Remove current alembic
				if os.path.isfile(alembicPath):
					os.remove(alembicPath)

				## Import the file so we don't have to display anything due to the files prob being saved with textures on etc
				sceneName = cmds.file(sceneName = True, q = True)
				if not sceneName == latestScene:
					try:    cmds.file(latestScene, o = True, f = True)
					except: cmds.warning('Failed to open %s...' % latestScene)
					cleanup.removeAllNS()

				## Now export back out a new alembic with the version name that should exist in the assembly reference.
				roots = cmds.ls(type = 'transform')
				rootHrc = [root for root in roots if cmds.referenceQuery(root, isNodeReferenced = True) if cmds.objExists('%s.type' % root) if str(cmds.getAttr('%s.type' % root)).startswith('anim')] if roots else None
				rootName = ' -root '.join( rootHrc ) if rootHrc else None

				if rootName:
					## Change uv set map1 if the mesh has multiple uv sets for alembic cache
					[cmds.polyUVSet(each, currentUVSet = True, uvSet = 'map1') for each in cmds.ls(type = 'mesh')]

					## Now scan the geo in the scene and preserve the crease information
					for each in cmds.ls(type = 'mesh', l = True):
						if not cmds.objExists('%s.SubDivisionMesh' % each):
							try:
								cmds.addAttr('%s' % each, ln = 'SubDivisionMesh', at = 'bool')
								cmds.setAttr("%s.SubDivisionMesh" % each, 1)
							except:
								pass

					## Add custom attribute tag to check rig version if it doesn't exist...
					for root in rootHrc:
						rigVersion = int( os.path.basename(cmds.referenceQuery(root, filename = True)).split('.')[1].split('v')[-1] )

						if not cmds.objExists('%s.rigVersion' % root):
							cmds.addAttr(root, longName = 'rigVersion', attributeType = 'long', dv = 0)

						cmds.setAttr('%s.rigVersion' % root, rigVersion)

					minTime = cmds.playbackOptions(min = True, q = True)
					maxTime = cmds.playbackOptions(max = True, q = True)
					abc_export_cmd = "-attr smoothed -attr SubDivisionMesh -attr rigVersion -ro -uvWrite -wholeFrameGeo -worldSpace -writeVisibility -fr %d %d -root %s -file %s" % (minTime, maxTime, rootName, alembicPath)
					try:
						[cmds.currentTime(minTime) for i in range(2)]
						cmds.AbcExport(verbose = False, j = abc_export_cmd)
						# cmds.file(new = True, force = True)
					except:
						cmds.warning("Failed to export Alembic Cache!!")
				else:
					cmds.warning('Cannot find any proper _hrc with anim tag in this scene...')