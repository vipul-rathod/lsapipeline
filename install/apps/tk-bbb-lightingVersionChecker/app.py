"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
"""

import sys
if 'T:/software/lsapipeline/tools' not in sys.path:
	sys.path.append('T:/software/lsapipeline/tools')

if 'T:/software/python-api/' not in sys.path:
	sys.path.append('T:/software/python-api/')

if 'T:/software/lsapipeline/custom' not in sys.path:
	sys.path.append('T:/software/lsapipeline/custom')

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

class LightingVersionChecker(Application):
	def init_app(self):
		# make sure that the context has an entity associated - otherwise it wont work!
		if self.context.entity is None:
			raise tank.TankError("Cannot load the lightingVersionChecker application! "
								 "Your current context does not have an entity (e.g. "
								 "a current Shot, current Asset etc). This app requires "
								 "an entity as part of the context in order to work.")
		getDisplayName = self.get_setting('display_name')
		self.engine.register_command(getDisplayName, self.run_app)
		debug(self, method = 'init_app', message = 'lightingVersionChecker Loaded...', verbose = False)

	def run_app(self):
		debug(self, method = 'run_app', message = 'lightingVersionChecker...', verbose = False)
		getDisplayName = self.get_setting('display_name')
		self.engine.show_dialog(getDisplayName, self, MainUI, self)

class MainUI(QtGui.QWidget):
	def __init__(self, app):
		"""
		"""
		QtGui.QWidget.__init__(self)
		self.app = app
		debug(self.app, method = 'MainUI.__init__', message = 'Running app...', verbose = False)

		self.context = self.app.context
		debug(self.app, method = 'MainUI.__init__', message = 'Context Step: %s' % self.context.step['name'], verbose = False)

		if self.context.step['name'] != 'Light':
			tank.TankError("Cannot load, not a valid Light step.")
		else:
			debug(app = self.app, method = 'MainUI.__init__', message = 'Valid Light step...', verbose = False)
			### PROCESS ALL THE SCENE STUFF
			## Load the API
			self.tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
			debug(app = self.app, method = 'MainUI.__init__', message = 'tk: %s' % self.tk, verbose = False)

			## Working scene path
			scene_path = cmds.file(query = True, sn = True)
			debug(app = self.app, method = 'MainUI.__init__', message = 'scene_path: %s' % scene_path, verbose = False)

			if not scene_path:
				cmds.warning("Not a valid scene file...")
			else:
				## Build an entity type to get some values from.
				self.entity = self.context.entity ## returns {'type': 'Shot', 'name': 'ep100_sh010', 'id': 1166}
				debug(app = self.app, method = 'MainUI.__init__', message = 'self.entity: %s' % self.entity, verbose = False)

				## Filter for the matching ID for the shot
				sg_filters = [["id", "is", self.entity["id"]]]
				debug(app = self.app, method = 'MainUI.__init__', message = 'sg_filters: %s' % sg_filters, verbose = False)

				## Build an entity type to get some values from.
				sg_entity_type = self.entity["type"] ## returns Shot
				debug(app = self.app, method = 'MainUI.__init__', message = 'sg_entity_type: %s' % sg_entity_type, verbose = False)

				## Get template path
				## primary_publish_template: maya_shot_publish
				## maya_shot_publish = '@shot_root/publish/maya/{name}.v{version}.mb'
				self.staticAlembicFolder = self.tk.templates[self.app.get_setting('static_alembic_cache_version')] ## returns <Sgtk TemplatePath maya_shot_publish: episodes/{Sequence}/{Shot}/{Step}/publish/maya/{name}.v{version}.mb>
# 				print self.staticAlembicFolder
				debug(app = self.app, method = 'MainUI.__init__', message = 'template_path: %s' % self.staticAlembicFolder, verbose = False)

				self.animAlembicFolder = self.tk.templates[self.app.get_setting('anim_alembic_cache_version')] ## returns <Sgtk TemplatePath maya_shot_publish: episodes/{Sequence}/{Shot}/{Step}/publish/maya/{name}.v{version}.mb>
# 				print self.animAlembicFolder
				debug(app = self.app, method = 'MainUI.__init__', message = 'template_path: %s' % self.animAlembicFolder, verbose = False)

				self.oceanPreset = self.tk.templates[self.app.get_setting('ocean_preset')] ## returns <Sgtk TemplatePath maya_shot_publish: episodes/{Sequence}/{Shot}/{Step}/publish/maya/{name}.v{version}.mb>
# 				print self.oceanPreset
				debug(app = self.app, method = 'MainUI.__init__', message = 'template_path: %s' % self.oceanPreset, verbose = False)

				self.camVersion = self.tk.templates[self.app.get_setting('cam_version')] ## returns <Sgtk TemplatePath maya_shot_publish: episodes/{Sequence}/{Shot}/{Step}/publish/maya/{name}.v{version}.mb>
# 				print self.camVersion
				debug(app = self.app, method = 'MainUI.__init__', message = 'template_path: %s' % self.camVersion, verbose = False)

				self.fxCacheVersion = self.tk.templates[self.app.get_setting('ocean_preset')] ## returns <Sgtk TemplatePath maya_shot_publish: episodes/{Sequence}/{Shot}/{Step}/publish/maya/{name}.v{version}.mb>
# 				print self.fxCacheVersion
				debug(app = self.app, method = 'MainUI.__init__', message = 'template_path: %s' % self.fxCacheVersion, verbose = False)


				## Shot name
				self.shotNum = self.entity["name"]
				debug(app = self.app, method = 'MainUI.__init__', message = 'shotName: %s' % self.shotNum, verbose = False)

				## Shot ID
				self.id = self.entity["id"]
				debug(app = self.app, method = 'MainUI.__init__', message = 'shotId: %s' % self.id, verbose = False)

				## Published animation  cache version
# 				getStaticAlembicVersionFolders = self.tk.paths_from_template(self.staticAlembicFolder, {'Step' : 'Anm', 'id' : self.id, 'Shot' : self.shotNum}) # returns ['I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v003.mb', 'I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v001.mb', 'I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v002.mb']
# 				if getStaticAlembicVersionFolders:
# 					debug(app = self.app, method = 'MainUI.__init__', message = 'latestPublishedAnimVerFile: %s' % max(getStaticAlembicVersionFolders), verbose = False)
# # 					print max(getStaticAlembicVersionFolders).split('\\')[-1].split('v')[-1]

				#######################################
				################### UI LOAD / BUILD NOW
				#######################################
				## Now build the UI
				self.mainLayout = QtGui.QVBoxLayout(self)

				## Setup the layout and buttons
				self.fetchingGroupBox = QtGui.QGroupBox(self)
				self.fetchingGroupBox.setTitle(self.shotNum)
				self.buttonLayout = QtGui.QVBoxLayout(self.fetchingGroupBox)
				
				if cmds.objExists('ABC_ANIM_CACHES_hrc'):
					self.animVersionCheckerButton = QtGui.QPushButton( 'ANIM_CACHES WORK FILE ----------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % ( self._getAnimCacheSceneVersion(), self._getLatestAnimCacheVersion() ) )
					self.animVersionCheckerButton.clicked.connect(self._compareAnimCacheVersion)
					self._compareAnimCacheVersion()
					self.buttonLayout.addWidget(self.animVersionCheckerButton)

				if cmds.objExists('ABC_STATIC_CACHES_hrc'):
					self.staticVersionCheckerButton = QtGui.QPushButton( 'STATIC_CACHES WORK FILE ----------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % ( self._getStaticCacheSceneVersion(), self._getLatestStaticCacheVersion() ) )
					self.staticVersionCheckerButton.clicked.connect(self._compareStaticCacheVersion)
					self._compareStaticCacheVersion()
					self.buttonLayout.addWidget(self.staticVersionCheckerButton)

				if cmds.objExists('BAKE_CAM_hrc'):
					self.camVersionCheckerButton = QtGui.QPushButton( 'CAM WORK FILE ----------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % ( self._getCamSceneVersion(), self._getLatestCamVersion() ) )
					self.camVersionCheckerButton.clicked.connect(self._compareCamVersion)
					self._compareCamVersion()
					self.buttonLayout.addWidget(self.camVersionCheckerButton)

				if cmds.objExists('FX_CACHES_hrc'):
					self.oceanPresetVersionCheckerButton = QtGui.QPushButton( 'OCEAN PRESET WORK FILE ----------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % ( self._getOceanPresetSceneVersion(), self._getLatestOceanPresetVersion() ) )
					self.oceanPresetVersionCheckerButton.clicked.connect(self._compareOceanPresetVersion)
					self._compareOceanPresetVersion()
					self.buttonLayout.addWidget(self.oceanPresetVersionCheckerButton)

				if cmds.objExists('FX_CACHES_hrc'):
					self.fxCacheVersionCheckerButton = QtGui.QPushButton( 'FX CACHES WORK FILE ----------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % ( self._getFXCacheSceneVersion(), self._getLatestFXCacheVersion() ) )
					self.fxCacheVersionCheckerButton.clicked.connect(self._compareFXCacheVersion)
					self._compareFXCacheVersion()
					self.buttonLayout.addWidget(self.fxCacheVersionCheckerButton)

				## Add the buttons to their layout widget
# 				self.buttonLayout.addWidget(self.versionCheckerButton)
				self.mainLayout.addWidget(self.fetchingGroupBox)
				self.mainLayout.addStretch(1)
				self.resize(300, 20)

########################################################################################################################################################

########################################################################################################################################################
	def _compareFXCacheVersion(self):
		currentWorkingVer = self._getFXCacheSceneVersion()
		publishedLatestVer = self._getLatestFXCacheVersion()
		self.fxCacheVersionCheckerButton.setText('FX CACHES WORK FILE ---------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % (currentWorkingVer, publishedLatestVer) )
		if currentWorkingVer != publishedLatestVer:
			self.fxCacheVersionCheckerButton.setStyleSheet("QPushButton{background-color: red}")
		else:
			self.fxCacheVersionCheckerButton.setStyleSheet("QPushButton{background-color: green}")

	def _getFXCacheSceneVersion(self):
		## If FX_CACHES_hrc exist...
		if cmds.objExists('FX_CACHES_hrc.version'):
			currentWorkingVer = cmds.getAttr('FX_CACHES_hrc.version')
			print currentWorkingVer
			return currentWorkingVer
		else:
			print "Eror"
			sys.stderr.write('Kindly fetch the published OCEAN PRESET to use this tool and check for latest version!!!')

	def _getLatestFXCacheVersion(self):
		## Published animation version files
		getFXCacheVersionFolders = self.tk.paths_from_template(self.fxCacheVersion, {'Step' : 'FX', 'id' : self.id, 'Shot' : self.shotNum})
		print getFXCacheVersionFolders
		if getFXCacheVersionFolders:
			latestFXCacheVersionFolders = max(getFXCacheVersionFolders).split('\\')[-1]
			return latestFXCacheVersionFolders
########################################################################################################################################################

########################################################################################################################################################

	def _compareOceanPresetVersion(self):
		currentWorkingVer = self._getOceanPresetSceneVersion()
		publishedLatestVer = self._getLatestOceanPresetVersion()
		self.oceanPresetVersionCheckerButton.setText('OCEAN PRESET WORK FILE ---------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % (currentWorkingVer, publishedLatestVer) )
		if currentWorkingVer != publishedLatestVer:
			self.oceanPresetVersionCheckerButton.setStyleSheet("QPushButton{background-color: red}")
		else:
			self.oceanPresetVersionCheckerButton.setStyleSheet("QPushButton{background-color: green}")

	def _getOceanPresetSceneVersion(self):
		## If FX_CACHES_hrc exist...
		if cmds.objExists('FX_CACHES_hrc.presetVersion'):
			currentWorkingVer = cmds.getAttr('FX_CACHES_hrc.presetVersion')
			return currentWorkingVer
		else:
			sys.stderr.write('Kindly fetch the published OCEAN PRESET to use this tool and check for latest version!!!')

	def _getLatestOceanPresetVersion(self):
		## Published animation version files
		getOceanPresetVersionFolders = self.tk.paths_from_template(self.oceanPreset, {'Step' : 'Anm', 'id' : self.id, 'Shot' : self.shotNum})
		if getOceanPresetVersionFolders:
			latestOceanPresetVersionFolders = max(getOceanPresetVersionFolders).split('\\')[-1]
			return latestOceanPresetVersionFolders
########################################################################################################################################################

########################################################################################################################################################
	def _compareCamVersion(self):
		currentWorkingVer = self._getCamSceneVersion()
		publishedLatestVer = self._getLatestCamVersion()
		self.camVersionCheckerButton.setText('CAM WORK FILE ---------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % (currentWorkingVer, publishedLatestVer) )
		if currentWorkingVer != publishedLatestVer:
			self.camVersionCheckerButton.setStyleSheet("QPushButton{background-color: red}")
		else:
			self.camVersionCheckerButton.setStyleSheet("QPushButton{background-color: green}")

	def _getCamSceneVersion(self):
		## If BAKE_CAM_hrc exist...
		if cmds.objExists('BAKE_CAM_hrc.version'):
			currentWorkingVer = cmds.getAttr('BAKE_CAM_hrc.version')
			return currentWorkingVer
		else:
			sys.stderr.write('Kindly fetch the published CAMERA to use this tool and check for latest version!!!')

	def _getLatestCamVersion(self):
		## Published animation version files
		getCamVersionFolders = self.tk.paths_from_template(self.camVersion, {'Step' : 'Anm', 'id' : self.id, 'Shot' : self.shotNum}) # returns ['I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v003.mb', 'I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v001.mb', 'I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v002.mb']
		if getCamVersionFolders:
			latestCamVersionFolders = max(getCamVersionFolders).split('\\')[-1]
			return latestCamVersionFolders
########################################################################################################################################################

########################################################################################################################################################

	def _compareAnimCacheVersion(self):
		currentWorkingVer = self._getAnimCacheSceneVersion()
		publishedLatestVer = self._getLatestAnimCacheVersion()
		self.animVersionCheckerButton.setText('ANIM_CACHES WORK FILE ---------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % (currentWorkingVer, publishedLatestVer) )
		if currentWorkingVer != publishedLatestVer:
			self.animVersionCheckerButton.setStyleSheet("QPushButton{background-color: red}")
		else:
			self.animVersionCheckerButton.setStyleSheet("QPushButton{background-color: green}")

	def _getAnimCacheSceneVersion(self):
		## If ABC_ANIM_CACHES_hrc exist...
		if cmds.objExists('ABC_ANIM_CACHES_hrc.version'):
			currentWorkingVer = cmds.getAttr('ABC_ANIM_CACHES_hrc.version')
			return currentWorkingVer
		else:
			sys.stderr.write('Kindly fetch the published ANIM CACHES to use this tool and check for latest version!!!')

	def _getLatestAnimCacheVersion(self):
		## Published animation version files
		getAnimAlembicVersionFolders = self.tk.paths_from_template(self.animAlembicFolder, {'Step' : 'Anm', 'id' : self.id, 'Shot' : self.shotNum}) 
		if getAnimAlembicVersionFolders:
			latestAnimAlembicVersionFolders = max(getAnimAlembicVersionFolders).split('\\')[-1]
			return latestAnimAlembicVersionFolders
#########################################################################################################################################################

#########################################################################################################################################################
	def _compareStaticCacheVersion(self):
		currentWorkingVer = self._getStaticCacheSceneVersion()
		publishedLatestVer = self._getLatestStaticCacheVersion()
		self.staticVersionCheckerButton.setText('STATIC_CACHES WORK FILE ---------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % (currentWorkingVer, publishedLatestVer) )
		if currentWorkingVer != publishedLatestVer:
			self.staticVersionCheckerButton.setStyleSheet("QPushButton{background-color: red}")
		else:
			self.staticVersionCheckerButton.setStyleSheet("QPushButton{background-color: green}")

	def _getStaticCacheSceneVersion(self):
		## If ABC_STATIC_CACHES_hrc exist...
		if cmds.objExists('ABC_STATIC_CACHES_hrc.version'):
			currentWorkingVer = cmds.getAttr('ABC_STATIC_CACHES_hrc.version')
			return currentWorkingVer
		else:
			sys.stderr.write('Kindly fetch the published STATIC CACHES to use this tool and check for latest version!!!')

	def _getLatestStaticCacheVersion(self):
		## Published animation version files
		getStaticAlembicVersionFolders = self.tk.paths_from_template(self.staticAlembicFolder, {'Step' : 'Anm', 'id' : self.id, 'Shot' : self.shotNum})
		if getStaticAlembicVersionFolders:
			latestStaticAlembicVersionFolders = max(getStaticAlembicVersionFolders).split('\\')[-1]
			return latestStaticAlembicVersionFolders
#########################################################################################################################################################
