"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db

NOTE THIS IMPORTS THE CACHES AND REBULDS THE OCEAN
THE OCEAN IS REATTACHED TO MARKS SHADED OCEAN WHEN THE SHADERS ARE REBUILT!

"""
import os, getpass, sys, sgtk, types, time
import tank.templatekey
import shutil
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError
import xml.etree.cElementTree as ET

if 'T:/software/lsapipeline/custom' not in sys.path:
## Now get the custom tools
	sys.path.append('T:/software/lsapipeline/custom')
import core_archive_readXML as readXML
import utils as utils
import maya_genericSettings as settings
import maya_asset_MASTERCLEANUPCODE as cleanup
from debug import debug
import ProgressBarUI as pbui
import CONST as CONST
import fluidCaches as fluidCaches
import fx_lib as fxLib
#reload(settings)
#reload(pbui)
#reload(CONST)
#reload(fluidCaches)
#reload(readXML)
#reload(fxLib)

###########################################################################
### NOTE I HAVE MOVED THE CONNECT CACHE METHODS INTO THE fluidCaches py!!!!!
class FetchCaches(Application):
	def init_app(self):
		# make sure that the context has an entity associated - otherwise it wont work!
		if self.context.entity is None:
			raise tank.TankError("Cannot load the FetchCaches application! "
								 "Your current context does not have an entity (e.g. "
								 "a current Shot, current Asset etc). This app requires "
								 "an entity as part of the context in order to work.")
		getDisplayName = self.get_setting('display_name')
		self.engine.register_command(getDisplayName, self.run_app)
		debug(self, method = 'init_app', message = 'FetchCaches Loaded...', verbose = False)

	def run_app(self):
		debug(self, method = 'run_app', message = 'FetchCaches...', verbose = False)
		getDisplayName = self.get_setting('display_name')
		debug(self, method = 'run_app', message = 'getDisplayName: %s' % getDisplayName, verbose = False)
		self.engine.show_dialog(getDisplayName, self, MainUI, self)

### NOTES:
### FX PUBLISHES THE FLUIDS GROUP WITH THE FLUID CONTAINERS IN IT
### WE REBUILD A MAYA OCEAN FROM SCRATCH, APPLY THE OCEAN PRESET FROM THE ANIMATION PUBLISH TO THIS OCEAN
### THEN WE MOVE THIS OCEAN TO THE FLUIDS GROUP FROM THE FX PUBLISH TO LINE IT UP TO THE FLUID CONTAINERS

class MainUI(QtGui.QWidget):
	def __init__(self, app):
		"""
		"""
		QtGui.QWidget.__init__(self)
		self.app = app
		debug(self.app, method = 'MainUI.__init__', message = 'Running app...', verbose = False)

		## Make sure the scene assembly plugins are loaded
		utils.loadSceneAssemblyPlugins(TankError)
		debug(self.app, method = 'MainUI.__init__', message = 'Scene assembly plugins loaded...', verbose = False)

		self.staticVersionNumber    = ''
		self.gpuVersionNumber       = ''

		self.context = self.app.context
		debug(self.app, method = 'MainUI.__init__', message = 'Context Step: %s' % self.context.step['name'], verbose = False)

		if self.context.step['name'] != 'Light':
			tank.TankError("Cannot load, not a valid lighting step.")
		else:
			debug(app = self.app, method = 'MainUI.__init__', message = 'Valid lighting step...', verbose = False)
			### PROCESS ALL THE SCENE STUFF
			## load the api
			self.tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
			debug(app = self.app, method = 'MainUI.__init__', message = 'tk: %s' % self.tk, verbose = False)

			scene_path = '%s' % os.path.abspath(cmds.file(query=True, sn= True))
			debug(app = self.app, method = 'MainUI.__init__', message = 'scene_path: %s' % scene_path, verbose = False)

			## Build an entity type to get some values from.
			self.entity = self.context.entity                                                                                    ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
			debug(app = self.app, method = 'MainUI.__init__', message = 'self.entity: %s' % self.entity, verbose = False)

			## Filter for the matching ID for the shot
			sg_filters = [["id", "is", self.entity["id"]]]
			debug(app = self.app, method = 'MainUI.__init__', message = 'sg_filters: %s' % sg_filters, verbose = False)

			## Build an entity type to get some values from.
			sg_entity_type = self.entity["type"]                                                                   ## returns Shot
			debug(app = self.app, method = 'MainUI.__init__', message = 'sg_entity_type...\n%s' % sg_entity_type, verbose = False)

			## DATA
			## NOTES SO HERE WE DON'T NEED TO CALL THE ASSETS FIELD FROM SHOTGUN
			## WE CAN JUST GRAB THE LATEST PUBLISH FILE FROM EACH OF THE TEMPLATE STEPS
			self.static_alembic = self.tk.templates[self.app.get_setting('static_alembic_publish_template')]
			debug(app = self.app, method = 'MainUI.__init__', message = 'self.static_alembic template...\n%s' % self.static_alembic, verbose = False)

			self.anim_alembic = self.tk.templates[self.app.get_setting('anim_alembic_publish_template')]
			debug(app = self.app, method = 'MainUI.__init__', message = 'self.anim_alembic template...\n%s' % self.anim_alembic, verbose = False)

			self.shotfx = self.tk.templates[self.app.get_setting('shotfx_publish_template')]
			debug(app = self.app, method = 'MainUI.__init__', message = 'self.shotfx_publish_template...\n%s' % self.shotfx, verbose = False)

			self.shot_gpu_alembic = self.tk.templates[self.app.get_setting('shot_gpu_publish_template')]
			debug(app = self.app, method = 'MainUI.__init__', message = 'self.shot_gpu_alembic template...\n%s' % self.shot_gpu_alembic, verbose = False)

			self.camera = self.tk.templates[self.app.get_setting('camera_publish_template')]
			debug(app = self.app, method = 'MainUI.__init__', message = 'self.camera...\n%s' % self.camera, verbose = False)

			self.coreTemplate = self.tk.templates[self.app.get_setting('corearchive_template')]
			debug(app = self.app, method = 'MainUI.__init__', message = 'self.coreTemplate...\n%s' % self.coreTemplate, verbose = False)

			self.creaseXML = self.tk.templates[self.app.get_setting('creaseXML_template')]
			debug(app = self.app, method = 'MainUI.__init__', message = 'self.creaseXML...\n%s' % self.creaseXML, verbose = False)

			#######################################
			################### UI LOAD / BUILD NOW
			#######################################
			## Now build the UI
			self.mainLayout = QtGui.QVBoxLayout(self)

			## Setup the layout and buttons
			self.fetchingGroupBox = QtGui.QGroupBox(self)
			self.fetchingGroupBox.setTitle('Lighting Assets Loaders:')
			debug(self.app, method = 'MainUI.__init__', message = 'fxCachesGroupBox built successfully...', verbose = False)

			self.buttonLayout = QtGui.QHBoxLayout(self.fetchingGroupBox)

			#############################################################
			self.fetchAnimCachesButton = QtGui.QToolButton(self)
			self.fetchAnimCachesButton.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
			self.fetchAnimCachesButton.setFixedWidth(150)
			self.fetchAnimCachesButton.setText('Fetch All Publishes')
			self.fetchAnimCachesButton.setMenu( QtGui.QMenu(self.fetchAnimCachesButton) )
			self.fetchAnimCachesButton.clicked.connect(self._fetchAnimationCaches)

			self.fetchAnimCachesListWidget = QtGui.QListWidget()
			self.fetchAnimCachesListWidget.setFixedWidth(150)
			self.fetchAnimCachesListWidget.setFixedHeight(75)
			self.fetchAnimCachesListWidget.addItem('Anim Publish')
			self.fetchAnimCachesListWidget.addItem('Static Publish')
			self.fetchAnimCachesListWidget.addItem('Camera Publish')
			self.fetchAnimCachesListWidget.addItem('All Publishes')
			self.fetchAnimCachesListWidget.clicked.connect(self.fetchAnimCachesButtonText)

			self.fetchAnimCachesAction = QtGui.QWidgetAction(self.fetchAnimCachesButton)
			self.fetchAnimCachesAction.setDefaultWidget(self.fetchAnimCachesListWidget)
			self.fetchAnimCachesButton.menu().addAction(self.fetchAnimCachesAction)
			#############################################################

			self.fetchFXCachesButton = QtGui.QPushButton('2. Fetch FX Publishes')
			self.fetchFXCachesButton.clicked.connect(self._fetchFXCaches)

			self.fetchCoresButton = QtGui.QPushButton('3. Fetch Core Archive XML Publishes')
			self.fetchCoresButton.clicked.connect(self._fetchCores)

			self.fetchOceanButton = QtGui.QPushButton('4. Rebuild Ocean')
			self.fetchOceanButton.clicked.connect(self._fetchOeanPublishes)

			self.cleanupButton = QtGui.QPushButton('5. Connect FX and Ocean')
			self.cleanupButton.clicked.connect(self._connectFXToOCean)

			self.creaseXMLButton = QtGui.QPushButton('6. Fetch Crease XML Publishes')
			self.creaseXMLButton.clicked.connect( partial(self._getCreaseFromXML, rootPrefix = 'ABC_ANIM_CACHES_hrc') )
			debug(self.app, method = 'MainUI.__init__', message = 'All buttons built successfully', verbose = False)

			## Add the buttons to their layout widget
			self.buttonLayout.addWidget(self.fetchAnimCachesButton)
			self.buttonLayout.addWidget(self.fetchFXCachesButton)
			self.buttonLayout.addWidget(self.fetchCoresButton)
			self.buttonLayout.addWidget(self.fetchOceanButton)
			self.buttonLayout.addWidget(self.cleanupButton)
			self.buttonLayout.addWidget(self.creaseXMLButton)

			### OPTIONS
			## Setup the layout and buttons
			self.OptionsGroupBox = QtGui.QGroupBox(self)
			self.OptionsGroupBox.setTitle('Optional Stuff:')

			self.optionsButtonLayout = QtGui.QHBoxLayout(self.OptionsGroupBox)

			self.setOceanLocButton = QtGui.QPushButton('Fix Ocean Location (Requires FX publish)')
			self.setOceanLocButton.clicked.connect(self._setOceanLocation)
			self.optionsButtonLayout.addWidget(self.setOceanLocButton)

			## Delete ocean setup
			self.OceanGroupBox = QtGui.QGroupBox(self)
			self.OceanGroupBox.setTitle('Ocean Stuff:')

			self.oceanButtonLayout = QtGui.QHBoxLayout(self.OceanGroupBox)

			self.deleteOceanButton = QtGui.QPushButton('Delete Ocean Setup!')
			self.deleteOceanButton.setStyleSheet("QPushButton {text-align: center; background: dark red}")
			self.deleteOceanButton.clicked.connect(fxLib.removeOceanSetup)
			self.oceanButtonLayout.addWidget(self.deleteOceanButton)

			self.mainLayout.addWidget(self.fetchingGroupBox)
			self.mainLayout.addWidget(self.OptionsGroupBox)
			self.mainLayout.addWidget(self.OceanGroupBox)

			self.mainLayout.addStretch(1)
			self.resize(300, 20)

	def _getCreaseFromXML(self, rootPrefix = ''):
		xmlPath = self._crease_XML_latest_publish(tk = self.tk, templateFile = self.creaseXML, id = self.entity["id"], shotNum = self.entity["name"])
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

	def _crease_XML_latest_publish(self, tk, templateFile = '', id = '', shotNum = ''):
		"""
		Fetch latest crease xml from animation publish folder...
		"""
		debug(app = self.app, method = '_crease_XML_latest_publish', message = 'Looking for crease xml now...', verbose = False)

		getCreaseXMLPublishFolder = tk.paths_from_template( templateFile, {'Step' : 'Anm', 'id' : id, 'Shot' : shotNum} )
		debug(app = self.app, method = '_crease_XML_latest_publish', message = 'getCreaseXMLPublishFolder: %s' % getCreaseXMLPublishFolder, verbose = False)

		if getCreaseXMLPublishFolder:
			getCreaseXMLVersion = os.listdir(getCreaseXMLPublishFolder[0])
			debug(app = self.app, method = '_crease_XML_latest_publish', message = 'getCreaseXMLVersion: %s' % getCreaseXMLVersion, verbose = False)

			## now find the highest version folder number
			highestCreaseXMLVersion = r'%s' % max(getCreaseXMLVersion)
			debug(app = self.app, method = '_crease_XML_latest_publish', message = 'highestCreaseXMLVersion...%s' % highestCreaseXMLVersion, verbose = False)

			highestCreaseXMLVersion = os.path.join(getCreaseXMLPublishFolder[0], highestCreaseXMLVersion)
			highestCreaseXMLVersion = highestCreaseXMLVersion.replace('\\', '/')

			## Return latest crease xml publish file...
			return highestCreaseXMLVersion if highestCreaseXMLVersion else ''

	def fetchAnimCachesButtonText(self):
		text = 'Fetch %s' % self.fetchAnimCachesListWidget.currentItem().text()
		self.fetchAnimCachesButton.setText(text)
		self.fetchAnimCachesButton.menu().hide()

	def _fetchOeanPublishes(self):
		templates = [self.shotfx]
		inprogressBar = pbui.ProgressBarUI(title = 'Fetching Ocean:')
		inprogressBar.show()
		prog = 40
		for each in templates:
			debug(app = self.app, method = 'MainUI._fetchOeanPublishes', message = 'Processing template: %s' % each, verbose = False)
			inprogressBar.updateProgress(percent = prog, doingWhat = 'ProcessAsset for template %s' % each)
			self._rebuildOcean(tk = self.tk, templateFile = each, id = self.entity["id"], shotNum = self.entity["name"], inprogressBar = inprogressBar)
			prog = prog + 10

		inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
		inprogressBar.close()
		# self._saveFile()

	def _fetchAnimationCaches(self):
		## Update the button to show proper text
		filteredPublish = self.fetchAnimCachesButton.text()

		templates = [self.static_alembic, self.anim_alembic, self.shot_gpu_alembic, self.camera]
		inprogressBar = pbui.ProgressBarUI(title = 'Fetching Animation Caches:')
		inprogressBar.show()
		prog = 40
		for each in templates:
			debug(app = self.app, method = 'MainUI._fetchAnimationCaches', message = 'Processing template: %s' % each, verbose = False)
			inprogressBar.updateProgress(percent = prog, doingWhat = 'ProcessAsset for template %s' % each)
			self._fetchAnimPublish(tk = self.tk, templateFile = each, id = self.entity["id"], shotNum = self.entity["name"], inprogressBar = inprogressBar, filteredPublish = filteredPublish)
			prog = prog + 10

		inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
		inprogressBar.close()
		# self._saveFile()

	def _fetchFXCaches(self):
		templates = [self.shotfx]
		inprogressBar = pbui.ProgressBarUI(title = 'Fetching Animation Caches:')
		inprogressBar.show()
		prog = 40
		for each in templates:
			debug(app = self.app, method = 'MainUI._fetchFXCaches', message = 'Processing template: %s' % each, verbose = False)
			inprogressBar.updateProgress(percent = prog, doingWhat = '_fetchFXPublish for template %s' % each)
			self._fetchFXPublish(tk = self.tk, templateFile = each, id = self.entity["id"], shotNum = self.entity["name"], inprogressBar = inprogressBar)
			prog = prog + 10

		inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
		inprogressBar.close()
		# self._saveFile()

	def _fetchCores(self):
		## Now get the Core Archives
		inprogressBar = pbui.ProgressBarUI(title = 'Fetching Core Archives:')
		inprogressBar.show()
		inprogressBar.updateProgress(percent = 20, doingWhat = 'Fetching coreArchive xmls now...')
		if 1:#try:
			self.coreLoader(tk = self.tk, templateFile = self.coreTemplate, inprogressBar = inprogressBar)
		else:#except:
			cmds.warning('Failed to fetch cores check line 841 for the ENV list as your ENV may be missing from Gins hardcoded list... grrrr hardcoding!')
			inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
			inprogressBar.close()

		inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
		inprogressBar.close()

	def _connectFXToOCean(self):
		inprogressBar = pbui.ProgressBarUI(title = 'Cleanup:')
		inprogressBar.show()
		## Cleanup
		inprogressBar.updateProgress(percent = 10, doingWhat = 'Cleaning up scene now...')
		self._cleanupShit()

		## Now connect the ocean to the fluid textures
		## Note also looking for here any anim interactive caches and connecting those in this function too
		inprogressBar.updateProgress(percent = 25, doingWhat = 'Connecting ocean to fluid textures...')
		self._connectWakeAndFoamToOcean(tk = self.tk, templateFile = self.shotfx, id = self.entity["id"], shotNum = self.entity["name"], inprogressBar = inprogressBar)

		## Now delete any Imageplanes
		inprogressBar.updateProgress(percent = 50, doingWhat = 'Deleting Image Planes...')
		cleanup.delAllImagePlanes()

		## Now make sure the scene is set to pal and cm and renderglobals
		inprogressBar.updateProgress(percent = 80, doingWhat = 'Setting Render Globals...')
		settings._setRenderGlobals()

		inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
		inprogressBar.close()
		# self._saveFile()

	def _saveFile(self):
		##################################################
		## FILE SAVE
		## Now save the working scene
		inprogressBar = pbui.ProgressBarUI(title = 'Saving File:')
		inprogressBar.show()
		inprogressBar.updateProgress(percent = 15, doingWhat = 'Cleaning name...')
		shotName = self.entity['name']
		debug(app = self.app, method = 'MainUI._saveFile', message = 'shotName...\n%s' % shotName, verbose = False)

		work_template = self.tk.templates['shot_work_area_maya']
		debug(app = self.app, method = 'MainUI._saveFile', message = 'work_template...\n%s' % work_template, verbose = False)

		pathToWorking = r'%s' % self.tk.paths_from_template(work_template, {"Shot" : shotName, "Step":self.context.step['name']})[0]
		pathToWorking.replace('\\\\', '\\')
		debug(app = self.app, method = 'MainUI._saveFile', message = 'pathToWorking...\n%s' % pathToWorking, verbose = False)

		## Scan the folder and find the highest version number
		fileShotName = "".join(shotName.split('_'))
		padding = ''
		versionNumber = ''
		if os.path.exists(pathToWorking):
			getfiles = os.listdir(pathToWorking)
			debug(app = self.app, method = 'MainUI._saveFile', message = 'getfiles...\n%s' % getfiles, verbose = False)
			if 'Keyboard' in getfiles:
				getfiles.remove('Keyboard')

			## Process a clean list now.. trying to remove from the current list is giving me grief and I'm too fn tired to care...
			finalFiles = []
			for each in getfiles:
				if each.split('.')[0] == fileShotName:
					finalFiles.append(each)
				else:
					pass
			debug(app = self.app, method = 'MainUI._saveFile', message = 'finalFiles...\n%s' % finalFiles, verbose = False)

			if finalFiles:
				highestVersFile = max(finalFiles)
				debug(app = self.app, method = 'MainUI._saveFile', message = 'highestVersFile...\n%s' % highestVersFile, verbose = False)
				versionNumber  = int(highestVersFile.split('.')[1].split('v')[1]) + 1
				debug(app = self.app, method = 'MainUI._saveFile', message = 'versionNumber...\n%s' % versionNumber, verbose = False)
			else:
				versionNumber  = 1

			## Now pad the version number
			if versionNumber < 10:
				padding = '00'
			elif versionNumber < 100:
				padding = '0'
			else:
				padding = ''
			debug(app = self.app, method = 'MainUI._saveFile', message = 'padding...\n%s' % padding, verbose = False)

		inprogressBar.updateProgress(percent = 50, doingWhat = 'Renaming scene...')
		## Rename the file
		renameTo = '%s/%s.v%s%s' % (pathToWorking.replace('\\', '/'), fileShotName, padding, versionNumber)
		debug(app = self.app, method = 'MainUI._saveFile', message = 'renameTo...\n%s' % renameTo, verbose = False)

		## Now save the file
		cmds.file(rename = renameTo)
		inprogressBar.updateProgress(percent = 50, doingWhat = 'Saving scene...')
		cmds.file(save = True, force = True, type = 'mayaAscii')

		inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished')
		inprogressBar.close()
		inprogressBar = None

	def _removeFX(self):
		"""
		Func to cleanup the FX aspects of an ocean setup for a clean rebuild
		"""
		nodesToClean = [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE, 'fluids_hrc']
		for eachNode in nodesToClean:
			try:
				cmds.delete(each)
			except:
				pass

		for eachCache in cmds.ls(type = 'cacheFile'):
			cmds.delete(eachCache)

	def _removeOcean(self):
		"""
		Func to clean up all the related ocean stuff for a full clean rebuild.
		"""
		nodesToClean = [CONST.OCEANDISPSHADER, CONST.OCEANANIMSHADER,  CONST.OCEAN_ANIM_PREVIEWPLANENAME]
		for eachNode in nodesToClean:
			try:
				cmds.delete(each)
			except:
				pass

	def _fetchFXPublish(self, tk, templateFile = '', fields = '', id = '', shotNum = '', inprogressBar = ''):
		"""
		Fetches all the latest published fluid containers and their caches for lighting
		"""

		## First clean up any existing caches and fluids
		self._removeFX()

		## CHECK FOR FX PUBLISHES NOW
		getFXVersionFolders = tk.paths_from_template(templateFile, {'Step' : 'FX', 'id' : id, 'Shot' : shotNum})
		## FX PUBLISH FLUID CONTAINERS
		if getFXVersionFolders:
			## now find the highest version folder number
			highestVersionFolder = r'%s' % max(getFXVersionFolders)
			debug(app = self.app, method = '_fetchFXPublish', message = 'highestVersionFolder...%s' % highestVersionFolder, verbose = False)

			highestVersionFolder = highestVersionFolder.replace('\\', '/')
			debug(app = self.app, method = '_fetchFXPublish', message = 'highestVersionFolder replaced \\ with /...\n%s' % highestVersionFolder, verbose = False)

			versionNumber = highestVersionFolder.split('/')[-1]
			debug(app = self.app, method = '_fetchFXPublish', message = 'versionNumber: %s' % versionNumber, verbose = False)

			getCacheFiles = os.listdir(highestVersionFolder)
			debug(app = self.app, method = '_fetchFXPublish', message = 'getCacheFiles...\n%s' % getCacheFiles, verbose = False)
			##################################################################################################################
			## FX FLUID TEXTURE CONTAINER CACHES
			if 'publish/fx' in highestVersionFolder:
				debug(app = self.app, method = '_fetchFXPublish', message = 'Loading fx cache files now...', verbose = False)

				## Build the group if it doesn't already exist
				self._buildGroup('FX_CACHES_hrc', versionNumber)

				if not cmds.objExists('fluids_hrc'):
					debug(None, method = '_fetchFXPublish', message = 'FETCHING FLUID TEXTURE CONTAINERS NOW!', verbose = False)

					if getCacheFiles: ## A PUBLISH EXISTS
						## IMPORT FLUIDS_HRC FROM MB FILE
						for each in getCacheFiles:
							if each.endswith('.mb'):
								fluidsNode = '%s/%s' % (highestVersionFolder, each)
								debug(app = self.app, method = '_fetchFXPublish', message = 'fluidsNode: %s.' % fluidsNode, verbose = False)
								## Import the fluids_hrc group mb file now...
								try:
									cmds.file(fluidsNode, i = True)
									debug(app = self.app, method = '_fetchFXPublish', message = 'Fluids_hrc.mb imported successfully.. fluidsNode:%s.' % fluidsNode, verbose = False)

									## Now assign the fluid presets again! Or the caches DO NOT WORK!!!
									## Apply foam preset
									pathToFoamPreset = '%s%s' % (CONST.OCEANTEXTURE_PRESETPATH, CONST.OCEAN_FOAMTEXTURE_PRESET)
									mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(CONST.FOAM_FLUID_SHAPENODE, pathToFoamPreset) )
									debug(None, method = '_fetchFXPublish', message = 'Mel preset applied: %s' % pathToFoamPreset, verbose = False)

									## Apply wake preset
									pathToWakePreset = '%s%s' % (CONST.OCEANTEXTURE_PRESETPATH, CONST.OCEAN_WAKETEXTURE_PRESET)
									mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(CONST.WAKE_FLUID_SHAPENODE, pathToWakePreset) )
									debug(None, method = '_fetchFXPublish', message = 'Mel preset applied: %s' % pathToWakePreset, verbose = False)
								except:
									cmds.warning('Failed to load FX file, file is corrupt.')

						### NOW ATTACH THE CACHE TO THE FLUID TEXTURES!
						### Changed export to single file altered this to accommodate the single file exported.
						debug(None, method = '_fetchFXPublish', message = 'ATTACHING CACHES NOW...', verbose = False)
						for each in getCacheFiles:## THERE SHOULD ONLY BE ONE NOW!??
							if each.endswith('.xml'):
								cachePath = '%s/%s' % (highestVersionFolder, each)
								debug(app = self.app, method = '_fetchFXPublish', message = 'cachePath:%s' % cachePath, verbose = False)
								debug(app = self.app, method = '_fetchFXPublish', message = 'getCacheFiles each: %s' % each, verbose = False)
								try:
									#mel.eval("doImportFluidCacheFile(\"%s\", {}, {\"%s\"}, {});" % (cachePath, CONST.FOAM_FLUID_SHAPENODE))
									fluidCaches.rebuild_cache_from_xml(cachePath)
								except:
									cmds.warning('Failed to connect cache %s' % cachePath)
						debug(app = self.app, method = '_fetchFXPublish', message = 'Fluid caches imported successfully...', verbose = False)
					else:
						cmds.warning('THERE ARE NO FLUID CONTAINERS PUBLISHED FROM FX FOR THIS SHOT! Please see your cg supervisor now...')
				else:
					debug(app = self.app, method = '_fetchFXPublish', message = 'fluids_hrc ALREADY IN SCENE SKIPPING....', verbose = False)
		else:
			cmds.confirmDialog(title = 'FX PUBLISH', message = "No FX publishes found. Please confirm with the FX artists whether this shot requires any FX publish and if not, proceed to rebuild and move the ocean manually as long as it covers the camera view!", button = 'OK')

	def _setOceanLocation(self):
		"""
		Exposing a tool to help push the ocean into the right location based off the FX published fluid containers fluids_hrc
		"""
		## If the fluids_hrc exists
		if cmds.objExists('fluids_hrc'):
			if cmds.objExists('ocean_srf'):
				cmds.connectAttr('fluids_hrc.translateX', 'ocean_srf.translateX', f = True)
				cmds.connectAttr('fluids_hrc.translateZ', 'ocean_srf.translateZ', f = True)
			else:
				cmds.warning('MISSING ocean_srf node from scene....')

			if cmds.objExists('oceanPreviewPlane_prv'):
				cmds.connectAttr('fluids_hrc.translateX', 'oceanPreviewPlane_prv.translateX', f = True)
				cmds.connectAttr('fluids_hrc.translateZ', 'oceanPreviewPlane_prv.translateZ', f = True)
			else:
				cmds.warning('MISSING oceanPreviewPlane_prv node from scene....')
		else:
			cmds.warning('NO fluids_hrc FOUND! Can not move the ocean into final position. PLEASE CHECK FX PUBLISH NOW!')

	def _rebuildOcean(self, tk, templateFile = '', fields = '', id = '', shotNum = '', inprogressBar = ''):
		"""
		Split out as requested by lighting to just fetch the latest ocean
		"""
		debug(app = self.app, method = '_rebuildOcean', message = 'Deleting current Ocean now....', verbose = False)
		self._removeOcean()

		## Get all the publishes from shotgun now for the blocking or animation step as required..
		if self.app.get_setting('shotStep') == 'Blocking':
			getAnimVersionFolders = tk.paths_from_template(templateFile, {'Step' : 'Blck', 'id' : id, 'Shot' : shotNum})
		elif self.app.get_setting('shotStep') == 'Animation':
			getAnimVersionFolders = tk.paths_from_template(templateFile, {'Step' : 'Anm', 'id' : id, 'Shot' : shotNum})

		debug(app = self.app, method = '_rebuildOcean', message = 'getAnimVersionFolders...%s' % getAnimVersionFolders, verbose = False)

		## Fix path for maya to read in properly
		if getAnimVersionFolders:
			## now find the highest version folder number
			highestVersionFolder = r'%s' % max(getAnimVersionFolders)
			debug(app = self.app, method = '_rebuildOcean', message = 'highestVersionFolder...%s' % highestVersionFolder, verbose = False)

			highestVersionFolder = highestVersionFolder.replace('\\', '/')
			debug(app = self.app, method = '_rebuildOcean', message = 'highestVersionFolder replaced \\ with /...\n%s' % highestVersionFolder, verbose = False)

			versionNumber = highestVersionFolder.split('/')[-1]
			debug(app = self.app, method = '_rebuildOcean', message = 'versionNumber: %s' % versionNumber, verbose = False)

			getCacheFiles = os.listdir(highestVersionFolder)
			debug(app = self.app, method = '_rebuildOcean', message = 'getCacheFiles...\n%s' % getCacheFiles, verbose = False)
			##################################################################################################################
			## APPLY OCEAN PRESET TO A NEW OCEAN
			if 'publish/fx' in highestVersionFolder: ## The ocean preset.mel is saved out to the fx folder in the animation/publish/fx folders
				debug(app = self.app, method = '_rebuildOcean', message = 'Loading ocean files now...', verbose = False)

				## Build the group if it doesn't already exist
				self._buildGroup('FX_CACHES_hrc', versionNumber)

				## No maya ocean in scene? Build a new one...
				if not cmds.objExists('oceanShader1'):
					mel.eval("CreateOcean;")

					## Clean up the names
					## NOTE we are not renaming the actual OCEAN SHADER here because in Marks scripts we are reconnecting like so
					## cmds.disconnectAttr('oceanShader1.outColor', 'oceanShader1SG.surfaceShader')
					heightField = cmds.listRelatives(cmds.ls(selection = True)[0], parent = True, fullPath = True)[0]
					cmds.rename(heightField, 'oceanPreviewPlane_prv')
					cmds.rename('oceanPlane1', 'ocean_srf')
					cmds.rename('oceanPreviewPlane1', 'oceanPreviewPlane_heightF')
					cmds.parent('ocean_srf', 'FX_CACHES_hrc')
					cmds.parent('oceanPreviewPlane_prv', 'FX_CACHES_hrc')
					cmds.rename('oceanShader1', CONST.OCEANDISPSHADER)
					cmds.rename('oceanShader1SG', '%sSG' % CONST.OCEANDISPSHADER)

					## Lock translateY and rotation so that monkeys don't mess up with the ocean level
					toLock = ['translateY', 'rotateX', 'rotateY', 'rotateZ']
					for attr in toLock:
						cmds.setAttr('ocean_srf.%s' % attr, lock = True)

					## Hard set the render tesselation
					cmds.setAttr("ocean_srfShape.numberU", 200)
					cmds.setAttr("ocean_srfShape.numberV", 200)

					allOceans = cmds.ls(type= 'oceanShader')
					debug(app = self.app, method = '_rebuildOcean', message = 'allOceans: %s' % allOceans, verbose = False)

					## now put the ocean in the right position
					if cmds.objExists('fluids_hrc'):
						self._setOceanLocation()
					else:
						if cmds.objExists('ocean_srf') and cmds.objExists('oceanPreviewPlane_prv'):
							if not cmds.isConnected('oceanPreviewPlane_prv.translateX', 'ocean_srf.translateX'):
								cmds.connectAttr('oceanPreviewPlane_prv.translateX', 'ocean_srf.translateX', f = True)
							if not cmds.isConnected('oceanPreviewPlane_prv.translateZ', 'ocean_srf.translateZ'):
								cmds.connectAttr('oceanPreviewPlane_prv.translateZ', 'ocean_srf.translateZ', f = True)
						else:
							cmds.warning('MISSING ocean_srf or oceanPreviewPlane_prv node from scene...')

				for each in getCacheFiles:
					## Now attach the preset to the maya ocean build a new one if it doesn't already exist
					if each.endswith('.mel'): ## the ocean shader preset saved out
						pathToPreset = '%s/%s' % (highestVersionFolder, each)
#                         presetVersion = each.split('/')

						## Now apply the exported preset to each ocean in the scene. There really should only be ONE
						for eachOcean in allOceans:
							debug(app = self.app, method = '_rebuildOcean', message = 'Add version number for ocean preset on Ocean_Hrc', verbose = False)
							if cmds.objExists('FX_CACHES_hrc'):
								if not cmds.objExists('FX_CACHES_hrc.presetVersion'):
									cmds.addAttr('FX_CACHES_hrc', ln='presetVersion', dt='string')
									cmds.setAttr('FX_CACHES_hrc.presetVersion' , versionNumber, type='string')
							debug(app = self.app, method = '_rebuildOcean', message = 'Applying ocean preset: %s to %s' % (pathToPreset, eachOcean), verbose = False)
							mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(eachOcean, pathToPreset) )
							debug(app = self.app, method = '_rebuildOcean', message = 'Ocean and presets assigned successfully...', verbose = False)

					## Import ATOM
					if each.endswith('.atom'):
						pathToPreset = '%s/%s' % (highestVersionFolder, each)
						debug(app = self.app, method = '_rebuildOcean', message = 'Transferring ocean shader\'s animation from %s' % pathToPreset, verbose = False)

						mel.eval('performImportAnim 1;')
						cmds.select(allOceans, replace = True)

						cmds.file(pathToPreset,
						type = 'atomImport',
						i = True,
						ra = True,
						namespace = 'oceanDisp_shader',
						options = '; ; targetTime = 3; option = insert; match = hierarchy; selected = selectedOnly; search = ; replace = ; prefix = ; suffix = ; mapFile = ;',
						)

						if cmds.window('OptionBoxWindow', exists = True):
							cmds.deleteUI('OptionBoxWindow', window = True)

						debug(app = self.app, method = '_rebuildOcean', message = 'Ocean shader\'s animation transferred successfully.', verbose = False)

				debug(app = self.app, method = '_rebuildOcean', message = 'Ocean imported successfully...', verbose = False)

	def _fetchAnimPublish(self, tk, templateFile = '', fields = '', id = '', shotNum = '', inprogressBar = '', filteredPublish = ''):
		"""
		Used to fetch most recent cache files

		@param tk : tank instance
		@param templateFile: the tank template file specified in the shot_step.yml
		@type templateFile: template
		"""
		debug(app = self.app, method = '_fetchAnimPublish', message = 'Fetching latest caches now....', verbose = False)
		debug(app = self.app, method = '_fetchAnimPublish', message = 'Template....%s' % templateFile, verbose = False)
		debug(app = self.app, method = '_fetchAnimPublish', message = 'id....%s' % id, verbose = False)

		## Get all the publishes from shotgun now..
		if self.app.get_setting('shotStep') == 'Blocking':
			getAnimVersionFolders = tk.paths_from_template(templateFile, {'Step' : 'Blck', 'id' : id, 'Shot' : shotNum})
		elif self.app.get_setting('shotStep') == 'Animation':
			getAnimVersionFolders = tk.paths_from_template(templateFile, {'Step' : 'Anm', 'id' : id, 'Shot' : shotNum})

		if getAnimVersionFolders:
			## now find the highest version folder number
			highestVersionFolder = r'%s' % max(getAnimVersionFolders)
			debug(app = self.app, method = '_fetchAnimPublish', message = 'highestVersionFolder...%s' % highestVersionFolder, verbose = False)

			highestVersionFolder = highestVersionFolder.replace('\\', '/')
			debug(app = self.app, method = '_fetchAnimPublish', message = 'highestVersionFolder replaced \\ with /...\n%s' % highestVersionFolder, verbose = False)

			versionNumber = highestVersionFolder.split('/')[-1]
			debug(app = self.app, method = '_fetchAnimPublish', message = 'versionNumber: %s' % versionNumber, verbose = False)

			getCacheFiles = os.listdir(highestVersionFolder)
			debug(app = self.app, method = '_fetchAnimPublish', message = 'getCacheFiles...\n%s' % getCacheFiles, verbose = False)


			##################################################################################################################
			## GPU CACHE LOADER
			# if 'publish/gpu' in highestVersionFolder:
			#     if filteredPublish == 'Fetch GPU Publish' or filteredPublish == 'Fetch All Publishes':
			#
			#         debug(app = self.app, method = '_fetchAnimPublish', message = 'Loading gpu cache files now...', verbose = False)
			#         ## Build the group if it doesn't already exist
			#         if not self._buildGroup('GPU_CACHES_hrc', versionNumber):
			#             if versionNumber >=  self.staticVersionNumber:
			#                 ## Now process the caches
			#                 for each in getCacheFiles:
			#                     nodeName = each.split('_')[0]
			#                     if not cmds.objExists(nodeName):
			#                         gpuNode = '%s/%s' % (highestVersionFolder, each)
			#                         debug(app = self.app, method = '_fetchAnimPublish', message = 'gpuNode...\n%s' % gpuNode, verbose = False)
			#
			#                         cmds.createNode('gpuCache', n = nodeName)
			#                         debug(app = self.app, method = '_fetchAnimPublish', message = 'gpuNode... created..', verbose = False)
			#
			#                         cmds.rename("transform1", "%s_gpu" % nodeName)
			#                         debug(app = self.app, method = '_fetchAnimPublish', message = 'Rename for %s sucessful...' % nodeName, verbose = False)
			#
			#                         try:
			#                             cmds.setAttr('%s.cacheFileName' % nodeName, gpuNode, type = "string")
			#                             cmds.setAttr("%s.cacheGeomPath" % nodeName, "|", type = "string")
			#                             cmds.parent(cmds.listRelatives(nodeName, parent = True)[0], 'GPU_CACHES_hrc')
			#                         except RuntimeError:
			#                             cmds.warning('FAILED TO SET GPU PATHS FOR %s CORRECTLY PLEASE CHECK YOUR PUBLISH!' % nodeName)
			#
			#                         debug(app = self.app, method = '_fetchAnimPublish', message = 'GPU cache  %s succesfully loaded and parented...' % nodeName, verbose = False)
			#                     else:
			#                         cmds.warning("FAILED: %s already exists in the scene" % nodeName)
			#                 else:
			#                     debug(app = self.app, method = '_fetchAnimPublish', message = 'GPU Caches older than current publish version, no gpus were export on publish for this version thus we are skipping GPU import', verbose = False)
			#                     pass
			#         else:
			#             debug(app = self.app, method = '_fetchAnimPublish', message = 'GPU_CACHES_hrc ALREADY SETUP SKIPPING....', verbose = False)
			#             pass

			##################################################################################################################
			## STATIC CACHE LOADER
			if 'publish/alembic_static' in highestVersionFolder:
				if filteredPublish == 'Fetch Static Publish' or filteredPublish == 'Fetch All Publishes':

					hrc = 'ABC_STATIC_CACHES_hrc'
					debug(app = self.app, method = '_fetchAnimPublish', message = 'Loading alembic_static cache files now...', verbose = False)

					## Build the group if it doesn't already exist
					proceedFetch = True
					if cmds.objExists(hrc):
						proceedFetch = cmds.confirmDialog(title = 'Fetch Static Publish', message = '"%s" already exist! Press OK to re-fetch a latest publish.' % hrc, button = ['OK', 'Cancel'], defaultButton = 'OK', cancelButton = 'Cancel', dismissString = 'Cancel')
						proceedFetch = True if proceedFetch == 'OK' else False

					## Now process the caches
					if proceedFetch:
						if cmds.objExists(hrc):
							try:
								cmds.delete(hrc)
							except:
								cmds.warning('Failed to delete "%s"...' % hrc)
								proceedFetch = False

						if not cmds.objExists(hrc):
							try:
								self._buildGroup(hrc, versionNumber)
							except:
								cmds.warning('Failed to create "%s"...' % hrc)
								proceedFetch = False

						if proceedFetch:
							for each in getCacheFiles:
								abcNode = '%s/%s' % (highestVersionFolder, each)
								debug(app = self.app, method = '_fetchAnimPublish', message = 'abcNode %s' % abcNode, verbose = False)
								try:
									cmds.AbcImport(abcNode, reparent  = "|%s" % hrc, setToStartFrame = True)#, createIfNotFound = True, removeIfNoUpdate = True)
								except:
									debug(app = self.app, method = '_fetchAnimPublish', message = 'StaticCache: %s import FAILED!' % abcNode, verbose = False)
									inprogressBar.close()
							debug(app = self.app, method = '_fetchAnimPublish', message = '"%s" imported successfully...' % hrc, verbose = False)
						else:
							debug(app = self.app, method = '_fetchAnimPublish', message = 'FAILED TO SETUP "%s", PLEASE CHECK WITH YOUR SUPERVISOR!!!' % hrc, verbose = False)
					else:
						debug(app = self.app, method = '_fetchAnimPublish', message = '"%s" ALREADY SETUP SKIPPING...' % hrc, verbose = False)

			##################################################################################################################
			## ANIMATED CACHE LOADER
			elif 'publish/alembic_anim' in highestVersionFolder:
				if filteredPublish == 'Fetch Anim Publish' or filteredPublish == 'Fetch All Publishes':

					hrc = 'ABC_ANIM_CACHES_hrc'
					debug(app = self.app, method = '_fetchAnimPublish', message = 'Loading alembic_anim cache files now...', verbose = False)

					## Build the group if it doesn't already exist
					proceedFetch = True
					if cmds.objExists(hrc):
						proceedFetch = cmds.confirmDialog(title = 'Fetch Anim Publish', message = '"%s" already exist! Press OK to re-fetch a latest publish.' % hrc, button = ['OK', 'Cancel'], defaultButton = 'OK', cancelButton = 'Cancel', dismissString = 'Cancel')
						proceedFetch = True if proceedFetch == 'OK' else False

					## Now process the caches
					if proceedFetch:
						if cmds.objExists(hrc):
							try:
								cmds.delete(hrc)
							except:
								cmds.warning('Failed to delete "%s"...' % hrc)
								proceedFetch = False

						if not cmds.objExists(hrc):
							try:
								self._buildGroup(hrc, versionNumber)
							except:
								cmds.warning('Failed to create "%s"...' % hrc)
								proceedFetch = False

						if proceedFetch:
							for each in getCacheFiles:
								abcNode = '%s/%s' % (highestVersionFolder, each)
								debug(app = self.app, method = '_fetchAnimPublish', message = 'abcNode %s' % abcNode, verbose = False)
								cmds.AbcImport(abcNode, reparent  = "|%s" % hrc, setToStartFrame = True)
							debug(app = self.app, method = '_fetchAnimPublish', message = '"%s" imported successfully...' % hrc, verbose = False)
						else:
							debug(app = self.app, method = '_fetchAnimPublish', message = 'FAILED TO SETUP "%s", PLEASE CHECK WITH YOUR SUPERVISOR!!!' % hrc, verbose = False)
					else:
						debug(app = self.app, method = '_fetchAnimPublish', message = '"%s" ALREADY SETUP SKIPPING...' % hrc, verbose = False)

			##################################################################################################################
			## CAMERA LOADER
			elif 'publish/cam' in highestVersionFolder:
				if filteredPublish == 'Fetch Camera Publish' or filteredPublish == 'Fetch All Publishes':

					hrc = 'BAKE_CAM_hrc'
					debug(app = self.app, method = '_fetchAnimPublish', message = 'Loading camera files now...', verbose = False)

					## Build the group if it doesn't already exist
					proceedFetch = True
					if cmds.objExists(hrc):
						proceedFetch = cmds.confirmDialog(title = 'Fetch Camera Publish', message = '"%s" already exist! Press OK to re-fetch a latest publish.' % hrc, button = ['OK', 'Cancel'], defaultButton = 'OK', cancelButton = 'Cancel', dismissString = 'Cancel')
						proceedFetch = True if proceedFetch == 'OK' else False

					## Now process the caches
					if proceedFetch:
						if cmds.objExists(hrc):
							try:
								cmds.delete(hrc)
							except:
								cmds.warning('Failed to delete "%s"...' % hrc)
								proceedFetch = False

						if proceedFetch:
							for each in getCacheFiles:
								camNode = '%s/%s' % (highestVersionFolder, each)
								debug(app = self.app, method = '_fetchAnimPublish', message = 'camera %s' % camNode, verbose = False)
								cmds.file(camNode, i = True)
								debug(app = self.app, method = '_fetchAnimPublish', message = 'Camera imported successfully...', verbose = False)
								for each in cmds.listRelatives(hrc, children = True):
									channels = ['tx', 'ty', 'tz', 'rx', '    ry', 'rz', 'sx', 'sy', 'sz']
									for eachChan in channels:
										cmds.setAttr('%s.%s' %(each, eachChan), lock = True)
										if not cmds.objExists('%s.version' % hrc):
											cmds.addAttr(('%s' % hrc), ln='version', dt='string')
											cmds.setAttr('%s.version' % hrc, versionNumber, type='string')
						else:
							debug(app = self.app, method = '_fetchAnimPublish', message = 'FAILED TO SETUP "%s", PLEASE CHECK WITH YOUR SUPERVISOR!!!' % hrc, verbose = False)
					else:
						debug(app = self.app, method = '_fetchAnimPublish', message = '"%s" ALREADY SETUP SKIPPING...' % hrc, verbose = False)
			else:
				pass
		else:
			debug(app = self.app, method = '_fetchAnimPublish', message = 'No Versions found for %s...' % templateFile, verbose = False)

	def coreLoader(self, tk, templateFile = '', fields = '', id = '', shotNum = '', inprogressBar = ''):
		## Filter for the matching ID for the shot
		sg_filters = [["id", "is", self.entity["id"]]]## returns [['id', 'is', 1201]]
		debug(app = self.app, method = 'coreLoader', message = 'sg_filters: %s' % sg_filters, verbose = False)

		## Build an entity type to get some values from.
		sg_entity_type = self.entity["type"]## returns Shot
		debug(app = self.app, method = 'coreLoader', message = 'sg_entity_type...\n%s' % sg_entity_type, verbose = False)

		data = self.app.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=['assets'])
		debug(app = self.app, method = 'coreLoader', message = 'data: %s' % data, verbose = False)

		maya_assetRootTemplate = tk.templates[self.app.get_setting('corearchive_template')]
		debug(app = self.app, method = 'coreLoader', message = 'maya_assetRootTemplate: %s' % maya_assetRootTemplate, verbose = False)

		envName = ''

		## work out if we are in a freaking STATIC ENV scene or not and ignore all the darn stuff we don't need to fetch...
		## Need to cater for the new ep00 shots here because these have different ABC Cache names now
		self.workSpace = cmds.workspace(q = True, fn = True)

		debug(app = self.app, method = 'coreLoader', message = 'self.workSpace: %s' % self.workSpace, verbose = False)
		if 'ep000_sh010' in self.workSpace:
			envName = 'ENV_MIDDLEHARBOUR_STATIC_ABC_STATIC_CACHES_hrc'
		elif 'ep000_sh020' in self.workSpace:
			envName = 'ENV_WESTHARBOUR_STATIC_ABC_STATIC_CACHES_hrc'
		elif 'ep000_sh030' in self.workSpace:
			envName = 'ENV_BIGTOWN_STATIC_ABC_STATIC_CACHES_hrc'
		elif  'ep000_sh040' in self.workSpace:
			envName = 'ENV_THEHEADS_STATIC_ABC_STATIC_CACHES_hrc'
		elif  'ep000_sh050' in self.workSpace:
			envName = 'ENV_MIDDLEHARBOUR_EAST_STATIC_ABC_STATIC_CACHES_hrc'
		else:
			if cmds.objExists('ABC_STATIC_CACHES_hrc'):
				envName = 'ABC_STATIC_CACHES_hrc'
			else:
				envName = None

		debug(app = self.app, method = 'coreLoader', message = 'envName: %s' % envName, verbose = False)
		if envName:
			self._fetchCoreXMLS(tk, maya_assetRootTemplate, envName, inprogressBar)
		else:
			## check for STATIC environments to process because we are in a shot for an episode.
			if cmds.objExists('ENV_MIDDLEHARBOUR_STATIC_ABC_STATIC_CACHES_hrc'):
				self._fetchCoreXMLS(tk, maya_assetRootTemplate, 'ENV_MIDDLEHARBOUR_STATIC_ABC_STATIC_CACHES_hrc', inprogressBar)

			if cmds.objExists('ENV_WESTHARBOUR_STATIC_ABC_STATIC_CACHES_hrc'):
				self._fetchCoreXMLS(tk, maya_assetRootTemplate, 'ENV_WESTHARBOUR_STATIC_ABC_STATIC_CACHES_hrc', inprogressBar)

			if cmds.objExists('ENV_BIGTOWN_STATIC_ABC_STATIC_CACHES_hrc'):
				self._fetchCoreXMLS(tk, maya_assetRootTemplate, 'ENV_BIGTOWN_STATIC_ABC_STATIC_CACHES_hrc', inprogressBar)

			if cmds.objExists('ENV_THEHEADS_STATIC_ABC_STATIC_CACHES_hrc'):
				self._fetchCoreXMLS(tk, maya_assetRootTemplate, 'ENV_THEHEADS_STATIC_ABC_STATIC_CACHES_hrc', inprogressBar)

			if cmds.objExists('ENV_MIDDLEHARBOUR_EAST_STATIC_ABC_STATIC_CACHES_hrc'):
				self._fetchCoreXMLS(tk, maya_assetRootTemplate, 'ENV_MIDDLEHARBOUR_EAST_STATIC_ABC_STATIC_CACHES_hrc', inprogressBar)

	def _fetchCoreXMLS(self, tk, maya_assetRootTemplate, envName, inprogressBar):
		baseNum = 20
		finalProcessIncrement = 1

		## Get list of assets under static caches:
		getStaticChildren = cmds.listRelatives(envName, children = True)

		debug(app = self.app, method = 'coreLoader', message = 'getStaticChildren: %s' % getStaticChildren, verbose = False)
		for eachChild in getStaticChildren:
			debug(app = self.app, method = 'coreLoader', message = 'eachChild: %s' % eachChild, verbose = False)

			getAssetFiles = tk.paths_from_template(maya_assetRootTemplate, {"Asset": "%s" % eachChild.split('_hrc')[0], 'Step' : 'MDL'})
			debug(app = self.app, method = 'coreLoader', message = 'Asset Files for %s | %s' % (eachChild, getAssetFiles), verbose = False)

			if getAssetFiles:
				latestVer =  max(getAssetFiles)
				#################################################################################################################
				# CORE XML LOADER
				debug(app = self.app, method = 'coreLoader', message = 'Loading core archive xml file now...', verbose = False)
				try:
					parentGrp = cmds.listRelatives(eachChild, parent = True)[0]
				except:
					parentGrp = ''

				debug(app = self.app, method = 'coreLoader', message = 'parentGrp: %s' % parentGrp, verbose = False)
				debug(app = self.app, method = 'coreLoader', message = 'xmlPath: %s' % latestVer, verbose = False)

				inprogressBar.updateProgress(percent = baseNum + finalProcessIncrement, doingWhat = 'Fetching %s coreArchive xmls now...' % eachChild)
				readXML.readCoreData(pathToUVXML = latestVer, parentGrp = parentGrp)
			else:
				cmds.warning('Skipping core load for %s as this has no core xml file...' % eachChild)

	def _buildGroup(self, groupName, versionNumber):
		debug(app = self.app, method = '_buildGroup', message = 'Building group..', verbose = False)
		## Build the group if it doesn't already exist
		if not cmds.objExists(groupName):
			cmds.group(n = groupName, em = True)
			debug(app = self.app, method = '_buildGroup', message = '%s built successfully...' % groupName, verbose = False)
			## Add the version attr if it doesn't already exits
			if not cmds.objExists('%s.version' % groupName):
				debug(app = self.app, method = '_buildGroup', message = 'Adding ver to group...', verbose = False)
				cmds.addAttr(groupName, ln = 'version', dt = 'string')
				cmds.setAttr('%s.version' % groupName, versionNumber, type = 'string')
				debug(app = self.app, method = '_buildGroup', message = '%s attr successfully...' % versionNumber, verbose = False)
			#print
			return False
		else:
			debug(app = self.app, method = '_buildGroup', message = '%s Group exists already in scene' % groupName, verbose = False)
			return True

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

		### CLEAN UP THE OCEAN SETUP
		debug(app = self.app, method = '_cleanup', message = 'Cleaning Ocean load now...', verbose = False)
		if cmds.objExists('OCEAN_hrc') and cmds.objExists('fluids_hrc'):
			try:
				cmds.parent('fluids_hrc', 'FX_CACHES_hrc')
			except RuntimeError:
				pass
			try:
				cmds.delete('OCEAN_hrc')
			except:
				pass
		elif cmds.objExists('fluids_hrc'):
			try:
				cmds.parent('fluids_hrc', 'FX_CACHES_hrc')
			except RuntimeError:
				pass
		else:
			pass

		### CLEAN UP THE FX IMPORT ETC
		debug(app = self.app, method = '_cleanup', message = 'Cleaning fx fluid container load now...', verbose = False)
		if cmds.objExists('OCEAN_hrc') and cmds.objExists('fluids_hrc'):
			try:
				cmds.parent('fluids_hrc', 'FX_CACHES_hrc')
			except:
				pass
			try:
				cmds.delete('OCEAN_hrc')
			except:
				pass

		elif cmds.objExists('fluids_hrc'):
			try:
				cmds.parent('fluids_hrc', 'FX_CACHES_hrc')
			except:
				pass

		else:
			pass

		## Cleanup old camera grp
		if cmds.objExists('SHOTCAM_hrc'):
			cmds.delete('SHOTCAM_hrc')
		debug(app = self.app, method = '_cleanup', message = 'Cleanup Finished.', verbose = False)

	def _connectWakeAndFoamToOcean(self, tk, templateFile = '', id = '', shotNum = '', inprogressBar = ''):
		"""
		Final pass to connect existing ocean caches to the ocean shader if they exist in the scene
		"""
		debug(app = self.app, method = '_connectWakeAndFoamToOcean', message = 'Connecting fluid textures to ocean shader....', verbose = False)

		####################################################
		## Straight up connection if no interactive is found.
		if cmds.objExists(CONST.OCEANDISPSHADER) and cmds.objExists(CONST.WAKE_FLUID_SHAPENODE) and cmds.objExists(CONST.FOAM_FLUID_SHAPENODE):
			try:
				cmds.connectAttr("%s.outAlpha" % CONST.WAKE_FLUID_SHAPENODE, "%s.waveHeightOffset" % CONST.OCEANDISPSHADER, force = True)
			except:
				pass
			try:
				cmds.connectAttr("%s.outAlpha" % CONST.FOAM_FLUID_SHAPENODE, "%s.foamOffset" % CONST.OCEANDISPSHADER, force = True)
			except:
				pass

		###########################################
		####### INTERACTIVE STUFFF ################
		### Now check for interactive caches and blend these
		debug(app = self.app, method = '_connectWakeAndFoamToOcean', message = 'Looking for interactive anim fluids now...', verbose = False)
		inprogressBar.updateProgress(percent = 76, doingWhat = 'Looking for interactive caches..')

		getAnimVersionFolders = tk.paths_from_template(templateFile, {'Step' : 'Anm', 'id' : id, 'Shot' : shotNum})
		debug(app = self.app, method = '_connectWakeAndFoamToOcean', message = 'getAnimVersionFolders: %s' % getAnimVersionFolders, verbose = False)

		## now find the highest version folder number
		highestVersionFolder = r'%s' % max(getAnimVersionFolders)
		debug(app = self.app, method = '_connectWakeAndFoamToOcean', message = 'highestVersionFolder...%s' % highestVersionFolder, verbose = False)

		highestVersionFolder = highestVersionFolder.replace('\\', '/')
		debug(app = self.app, method = '_connectWakeAndFoamToOcean', message = 'highestVersionFolder replaced \\ with /...\n%s' % highestVersionFolder, verbose = False)

		versionNumber = highestVersionFolder.split('/')[-1]
		debug(app = self.app, method = '_connectWakeAndFoamToOcean', message = 'versionNumber: %s' % versionNumber, verbose = False)

		listCacheFiles = os.listdir(highestVersionFolder)
		debug(app = self.app, method = '_connectWakeAndFoamToOcean', message = 'listCacheFiles...\n%s' % listCacheFiles, verbose = False)

		interactiveCaches = {}
		for each in listCacheFiles:
			if each.endswith('.xml'): ## the ocean shader preset saved out
				if CONST.WAKE_FLUID_SHAPENODE in each:
					interactiveCaches[CONST.WAKE_FLUID_SHAPENODE] = '%s/%s' % (highestVersionFolder, each)
				else:
					interactiveCaches[CONST.FOAM_FLUID_SHAPENODE] = '%s/%s' % (highestVersionFolder, each)

		if interactiveCaches:
			fluidCaches.mergeFluidCaches(interactiveFoamXML = interactiveCaches[CONST.FOAM_FLUID_SHAPENODE], interactiveWakeXML = interactiveCaches[CONST.WAKE_FLUID_SHAPENODE])

		debug(app = self.app, method = '_connectWakeAndFoamToOcean', message = 'Ocean connected....', verbose = False)

	def destroy_app(self):
		self.log_debug("Destroying sg_fetchLightingAssets")
