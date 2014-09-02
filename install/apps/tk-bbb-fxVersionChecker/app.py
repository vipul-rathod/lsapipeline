"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
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

class StaticENVHandler(Application):
	def init_app(self):
		# make sure that the context has an entity associated - otherwise it wont work!
		if self.context.entity is None:
			raise tank.TankError("Cannot load the fxVersionChecker application! "
								 "Your current context does not have an entity (e.g. "
								 "a current Shot, current Asset etc). This app requires "
								 "an entity as part of the context in order to work.")
		getDisplayName = self.get_setting('display_name')
		self.engine.register_command(getDisplayName, self.run_app)
		debug(self, method = 'init_app', message = 'fxVersionChecker Loaded...', verbose = False)

	def run_app(self):
		debug(self, method = 'run_app', message = 'fxVersionChecker...', verbose = False)
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

		if self.context.step['name'] != 'FX':
			tank.TankError("Cannot load, not a valid FX step.")
		else:
			debug(app = self.app, method = 'MainUI.__init__', message = 'Valid FX step...', verbose = False)
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
				self.templateFile = self.tk.templates[self.app.get_setting('primary_publish_template')] ## returns <Sgtk TemplatePath maya_shot_publish: episodes/{Sequence}/{Shot}/{Step}/publish/maya/{name}.v{version}.mb>
				debug(app = self.app, method = 'MainUI.__init__', message = 'template_path: %s' % self.templateFile, verbose = False)

				## Shot name
				self.shotNum = self.entity["name"]
				debug(app = self.app, method = 'MainUI.__init__', message = 'shotName: %s' % self.shotNum, verbose = False)

				## Shot ID
				self.id = self.entity["id"]
				debug(app = self.app, method = 'MainUI.__init__', message = 'shotId: %s' % self.id, verbose = False)

				## Published animation version files
				getAnimVersionFolders = self.tk.paths_from_template(self.templateFile, {'Step' : 'Anm', 'id' : self.id, 'Shot' : self.shotNum}) # returns ['I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v003.mb', 'I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v001.mb', 'I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v002.mb']
				if getAnimVersionFolders:
					debug(app = self.app, method = 'MainUI.__init__', message = 'latestPublishedAnimVerFile: %s' % max(getAnimVersionFolders), verbose = False)

				#######################################
				################### UI LOAD / BUILD NOW
				#######################################
				## Now build the UI
				self.mainLayout = QtGui.QVBoxLayout(self)

				## Setup the layout and buttons
				self.fetchingGroupBox = QtGui.QGroupBox(self)
				self.fetchingGroupBox.setTitle(self.shotNum)
				self.buttonLayout = QtGui.QHBoxLayout(self.fetchingGroupBox)

				self.versionCheckerButton = QtGui.QPushButton( 'WORK FILE ----------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % ( self._getSceneVersion(), self._getPublishedLatestVersion() ) )
				self.versionCheckerButton.clicked.connect(self._compareAnimVersion)
				self._compareAnimVersion()

				## Add the buttons to their layout widget
				self.buttonLayout.addWidget(self.versionCheckerButton)

				self.mainLayout.addWidget(self.fetchingGroupBox)

				self.mainLayout.addStretch(1)
				self.resize(300, 20)

	def _compareAnimVersion(self):
		currentWorkingVer = self._getSceneVersion()
		publishedLatestVer = self._getPublishedLatestVersion()

		self.versionCheckerButton.setText('WORK FILE ---------------------------------- %s | %s ----------------------------------- PUBLISHED FILE' % (currentWorkingVer, publishedLatestVer) )

		if int(currentWorkingVer) < int(publishedLatestVer):
			self.versionCheckerButton.setStyleSheet("QPushButton{background-color: red}")
		else:
			self.versionCheckerButton.setStyleSheet("QPushButton{background-color: green}")

	def _getSceneVersion(self):
		## If OCEAN_hrc exist...
		if cmds.objExists('OCEAN_hrc.publishVersion'):
			currentWorkingVer = '%03d' % cmds.getAttr('OCEAN_hrc.publishVersion')

			return currentWorkingVer
		else:
			cmds.warning('Couldn\'t find publish version for this shot due to shot published using the old method!!!')

	def _getPublishedLatestVersion(self):
		## Published animation version files
		getAnimVersionFolders = self.tk.paths_from_template(self.templateFile, {'Step' : 'Anm', 'id' : self.id, 'Shot' : self.shotNum}) # returns ['I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v003.mb', 'I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v001.mb', 'I:\\bubblebathbay\\episodes\\ep101\\ep101_sh019\\Anm\\publish\\maya\\ep101sh019.v002.mb']
		if getAnimVersionFolders:
			latestAnimVersionFolder = max(getAnimVersionFolders)

			return latestAnimVersionFolder.split('.')[-2].strip('v')