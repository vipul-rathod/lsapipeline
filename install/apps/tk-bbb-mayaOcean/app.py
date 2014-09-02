"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------

Code for a maya playblast creator app that runs in maya
"""
import os, getpass, sys, shutil, sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError
sys.path.append("T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean/splashTool")
import ui.SplashTool_UI as splash
## Custom stuff
if 'T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean' not in sys.path:
	sys.path.append('T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean')

if 'T:/software/lsapipeline/custom' not in sys.path:
	sys.path.append('T:/software/lsapipeline/custom')

import maya_asset_MASTERCLEANUPCODE as cleanup
import oceanBuilder as oceanBuilder
from debug import debug
import connectOceanHeights as connOH
import boat_FX as bfx
import utils as utils
import fluids_lib as fluidLib
import fx_lib as fxLib
import ProgressBarUI as pbui
import CONST as CONST
import maya_genericSettings as settings
import nParticleSetup as npart
import fluidCaches as fc
from icon import Icon
#reload(fc)
#reload(fluidLib)
#reload(fxLib)
#reload(utils)
#reload(bfx)
#reload(connOH)
#reload(oceanBuilder)
#reload(CONST)
#reload(settings)
#reload(npart)
#deadstring

class OceanGenerator(Application):
	def init_app(self):
		# make sure that the context has an entity associated - otherwise it wont work!
		if self.context.entity is None:
			raise tank.TankError("Cannot load the OceanGenerator application! "
								 "Your current context does not have an entity (e.g. "
								 "a current Shot, current Asset etc). This app requires "
								 "an entity as part of the context in order to work.")
		getDisplayName = self.get_setting('display_name')
		self.engine.register_command(getDisplayName, self.run_app)
		debug(self, method = 'init_app', message = 'OceanGenerator Loaded...', verbose = False)

	def run_app(self):
		debug(self, method = 'run_app', message = 'OceanGenerator...', verbose = False)
		getDisplayName = self.get_setting('display_name')
		self.engine.show_dialog(getDisplayName, self, MainUI, self)


class MainUI(QtGui.QWidget):
	def __init__(self, app):
		"""
		main UI for the Maya Create Ocean options
		"""
		QtGui.QWidget.__init__(self)
		self.app = app
		tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
		self.editor = self._getEditor()
		 ## To get the step
		context = self.app.context
		debug(self.app, method = 'run_app', message = 'Context Step: %s' % context.step['name'], verbose = False)

		if context.step['name'] == 'FX' or context.step['name'] == 'Additional FX':
			self.editor = 'modelPanel4'

		if self.editor:
			debug(self.app, method = 'Main_UI', message = 'Lauching UI', verbose = False)

			## Setup the paths for the presets and defaults etc...
			scene_path = os.path.abspath(cmds.file(query=True, sn= True))
			debug(self.app, method = 'Main_UI', message = 'scene_path: %s' % scene_path, verbose = False)

			epName = scene_path.split('\\')[3]

			###NOTE NO UNDERSCORES ARE ALLOWED HERE OR THE FUCKING THING FAILS MISERABLY!!! FOR ***HOURS*** OF YOUR PRECIOUS LIFE!!
			wakePreset =            'newOceanWakeTexture'
			foamPreset =            'newOceanWakeFoamTexture'
			oceanDefaultPreset =    'oceanDefaultPreset'
			wakeEmitterPreset =     'wakeEmitter.mel'
			foamEmitterPreset =     'foamEmitter.mel'
			hullEmitterPreset =     'hullEmitter.mel'

			## Now work out the published animation fx folder to get the ocean preset from for the published animation so our maya ocean matches after rebuild.
			entity = self.app.context.entity
			debug(self.app, method = 'Main_UI', message = 'entity: %s' % entity, verbose = False)
			debug(self.app, method = 'Main_UI', message = 'context.step["name"]: %s' % context.step['name'], verbose = False)

			## Now get the templates from the shot_step.yml
			## ocean_preset_template: maya_shot_oceanPresets
			## ocean_publish_template: maya_shot_publishOceanCache

			oceanPublishTemplate                = self.app.get_template('ocean_publish_template')
			## maya_shot_oceanPresets: '@presetsRoot/ocean/{presetName}.mel'
			oceanWakePresetTemplate             = self.app.get_template('ocean_preset_template')
			oceanFoamPresetTemplate             = self.app.get_template('ocean_preset_template')
			oceanDefaultPresetTemplate          = self.app.get_template('ocean_preset_template')
			animOceanPublishedPresetTemplate    = self.app.get_template('shotfx_publish_template')
			## maya_shot_publishOceanCache: '@shot_root/publish/fluids/{name}.v{version}.abc'
			debug(self.app, method = 'Main_UI', message = 'ocean_publish_template: %s' % oceanPublishTemplate, verbose = False)
			debug(self.app, method = 'Main_UI', message = 'oceanWakePresetTemplate: %s' % oceanWakePresetTemplate, verbose = False)
			debug(self.app, method = 'Main_UI', message = 'oceanFoamPresetTemplate: %s' % oceanFoamPresetTemplate, verbose = False)
			debug(self.app, method = 'Main_UI', message = 'oceanDefaultPresetTemplate: %s' % oceanDefaultPresetTemplate, verbose = False)
			debug(self.app, method = 'Main_UI', message = 'animOceanPublishedPresetTemplate: %s' % animOceanPublishedPresetTemplate, verbose = False)
			print

			## Now get ready to convert these to / pathing using the r approach
			## CONVERT WAKE TO A PROPER PATH
			self.wakePresetPath = r'%s' % oceanWakePresetTemplate.apply_fields({'presetName' : wakePreset})
			debug(self.app, method = 'Main_UI', message = 'self.wakePresetPath: %s' % self.wakePresetPath.replace('\\', '/'), verbose = False)

			## CONVERT FOAM TO A PROPER PATH
			self.foamPresetPath = r'%s' % oceanFoamPresetTemplate.apply_fields({'presetName' : foamPreset})
			debug(self.app, method = 'Main_UI', message = 'self.foamPresetPath: %s' % self.foamPresetPath.replace('\\', '/'), verbose = False)

			##############################################################
			################ Process ocean preset path for Anim or FX step |  Animation will use default preset, FX will use published preset.
			##############################################################
			isFX = False
			if cmds.objExists('fxNugget'):
				debug(self.app, method = 'Main_UI', message = 'fxNugget found...', verbose = False)

				# getAnimVersionFolders = tk.paths_from_template(animOceanPublishedPresetTemplate, {'id' : entity["id"], 'Shot' : entity["name"]})
				getAnimVersionFolders = tk.paths_from_template(animOceanPublishedPresetTemplate, {'Step' : 'Anm', 'id' : entity["id"], 'Shot' : entity["name"]})
				debug(self.app, method = 'Main_UI', message = 'getAnimVersionFolders: %s' % getAnimVersionFolders, verbose = False)

				highestAnimVerFolder = max(getAnimVersionFolders)
				debug(self.app, method = 'Main_UI', message = 'Path to highest oceanPreset AnimVerFolder: %s' % highestAnimVerFolder, verbose = False)
				if not highestAnimVerFolder:
					cmds.warning('THERE IS NO PUBLISHED OCEAN PRESET FROM ANIMAITON! PLEASE FIX THIS NOW!')

				isFX = True
			else:
				cmds.warning('NO FX NUGGET FOUND!')
				getAnimVersNum = None
				isFX = False

			##############################################################
			################ Now set the preset path properly
			##############################################################
			self.oceanPublishedPresetPath = None
			debug(self.app, method = 'Main_UI', message = 'Figuring out the ocean preset path now...', verbose = False)
			debug(self.app, method = 'Main_UI', message = 'isFX: %s' % isFX, verbose = False)
			if context.step['name'] == 'Anm' or context.step['name'] == 'FX' or context.step['name'] == 'Additional FX' or context.step['name'] == 'Blocking':
				if isFX:
					getMelPreset = [eachMel for eachMel in os.listdir(highestAnimVerFolder) if eachMel.endswith('.mel')]
					debug(self.app, method = 'Main_UI', message = 'getMelPreset: %s' % getMelPreset, verbose = False)

					if not getMelPreset:
						cmds.warning('NO ANIMATION OCEAN PRESET FOUND, USING THE DEFAULT.')
						debug(self.app, method = 'Main_UI', message = 'No published animation ocean preset found!!! Using default! NOT GOOD!', verbose = False)
						self.oceanPublishedPresetPath = r'%s' % oceanDefaultPresetTemplate.apply_fields({'presetName' : oceanDefaultPreset})
						debug(self.app, method = 'Main_UI', message = 'self.oceanPublishedPresetPath: %s'  % self.oceanPublishedPresetPath, verbose = False)
					else:
						presetPath = r'%s\%s' % (highestAnimVerFolder, getMelPreset[0])
						debug(self.app, method = 'Main_UI', message = 'Using published ocean preset: %s' % presetPath, verbose = False)
						self.oceanPublishedPresetPath = presetPath
						debug(self.app, method = 'Main_UI', message = 'self.oceanPublishedPresetPath: %s'  % self.oceanPublishedPresetPath, verbose = False)

				else:
					debug(self.app, method = 'Main_UI', message = 'No getAnimVersionFolders found... must be an animation scene or blocking scene setting default ocean preset template now', verbose = False)
					self.oceanPublishedPresetPath = r'%s' % oceanDefaultPresetTemplate.apply_fields({'presetName' : oceanDefaultPreset})
					debug(self.app, method = 'Main_UI', message = 'self.oceanPublishedPresetPath: %s'  % self.oceanPublishedPresetPath, verbose = False)
			else:
				debug(self.app, method = 'Main_UI', message = 'Context step is %s.' % context.step['name'], verbose = False)
				self.oceanPublishedPresetPath = r'%s' % oceanDefaultPresetTemplate.apply_fields({'presetName' : oceanDefaultPreset})
				debug(self.app, method = 'Main_UI', message = 'self.oceanPublishedPresetPath: %s'  % self.oceanPublishedPresetPath, verbose = False)

			## Now build the UI
			self.mainLayout = QtGui.QVBoxLayout(self)
			## High and Low Tide layout
			self.lowhiLayout = QtGui.QHBoxLayout(self)
			self.highTide = QtGui.QRadioButton('High Tide')
			self.highTide.setChecked(True)
			self.highTide.setEnabled(False)
			self.highTide.hide()
			self.lowTide = QtGui.QRadioButton('Low Tide')
			self.lowTide.setChecked(False)
			self.lowTide.setEnabled(False)
			self.lowTide.hide()
			## Now parent these tot the layout
			self.lowhiLayout.addWidget(self.highTide)
			self.lowhiLayout.addWidget(self.lowTide)
			self.lowhiLayout.addStretch(1)
			debug(self.app, method = 'Main_UI', message = 'lowhiLayout built successfully...', verbose = False)

			## Animation ocean setup
			self.animGroupBox = QtGui.QGroupBox(self)
			self.animGroupBox.setTitle('Animation Ocean Setup:')
			debug(self.app, method = 'Main_UI', message = 'animGroupBox built successfully...', verbose = False)

			self.animLayout = QtGui.QVBoxLayout(self.animGroupBox)
			debug(self.app, method = 'Main_UI', message = 'animLayout built successfully...', verbose = False)

			## Build Base Animation Ocean Setup Button
			self.buildOceanButton = QtGui.QPushButton('Setup Animation Ocean')
			self.buildOceanButton.setStyleSheet("QPushButton {text-align: center; background: dark green; color: white}")
			self.buildOceanButton.pressed.connect(partial(oceanBuilder.buildAnimOcean, self.editor, self.oceanPublishedPresetPath,  self.foamPresetPath.replace('\\', '/'), self.wakePresetPath.replace('\\', '/'), self.highTide.isChecked()))
			debug(self.app, method = 'Main_UI', message = 'self.buildOceanButton connected..', verbose = False)

			## Fetch FX Cache for interactive wake referencing
			self.fetchWakeFromFXButton = QtGui.QPushButton('Fetch Cache from FX')
			self.fetchWakeFromFXButton.setStyleSheet("QPushButton {text-align: center; background: dark orange; color: black}")
			self.fetchWakeFromFXButton.pressed.connect(self.get_shotfx_publish_dirs)
			debug(self.app, method = 'Main_UI', message = 'self.fetchWakeFromFXButton connected..', verbose = False)

			# ## Setup Interactive Ocean On Selected world_ctrl button
			# self.buildInteractiveOceanButton = QtGui.QPushButton('Setup Interactive Ocean On Sel world_ctrl')
			# self.buildInteractiveOceanButton.pressed.connect(self.setupInteractionOcean)
			# self.buildInteractiveOceanButton.setEnabled(False)
			# debug(self.app, method = 'Main_UI', message = 'self.buildInteractiveOceanButton connected..', verbose = False)
			#
			# ## Apply Fluid Emitter Presets button
			# self.buildInteractivePresetsButton = QtGui.QPushButton('Apply Fluid Emitter Presets')
			# self.buildInteractivePresetsButton.pressed.connect(partial(fluidLib._setFluidEmitterPresets, wakeEmitterPreset, foamEmitterPreset, hullEmitterPreset))
			# self.buildInteractivePresetsButton.setEnabled(False)
			# debug(self.app, method = 'Main_UI', message = 'self.buildInteractivePresetsButton connected..', verbose = False)

			self.animLayout.addWidget(self.buildOceanButton)
			self.animLayout.addWidget(self.fetchWakeFromFXButton)
			# self.animLayout.addWidget(self.buildInteractiveOceanButton)
			# self.animLayout.addWidget(self.buildInteractivePresetsButton)
			debug(self.app, method = 'Main_UI', message = 'animLayout built successfully...', verbose = False)

			######################################
			##### FX STUFF
			if context.step['name'] == 'FX' or context.step['name'] == 'Additional FX':
				###############################
				## BUILD THE MAIN BUILD BUTTONS
				###############################
				self.FXBuildGroupBox = QtGui.QGroupBox(self)
				self.FXBuildGroupBox.setTitle('FX Build Stuff:')
				self.mainFXBuildLayout = QtGui.QVBoxLayout(self.FXBuildGroupBox)

				self.hLayout = QtGui.QHBoxLayout(self)
				self.buildFXOceanSetupButton = QtGui.QPushButton('1. Setup FX Ocean')
				self.buildFXOceanSetupButton.pressed.connect(partial(self.setupFXOcean, highestAnimVerFolder))
				self.buildFXOceanSetupButton.setStyleSheet("QPushButton {text-align: center; background: dark green}")

				self.buildPresetsButton = QtGui.QPushButton('2. Apply All Fluid Emitter Presets')
				self.buildPresetsButton.pressed.connect(partial(fluidLib._setFluidEmitterPresets, wakeEmitterPreset, foamEmitterPreset, hullEmitterPreset))
				self.buildPresetsButton.setStyleSheet("QPushButton {text-align: center; background: dark green}")

				# self.buildParticlesPresetsButton = QtGui.QPushButton('3. Apply All Particle Presets')
				# self.buildParticlesPresetsButton.pressed.connect(self._setPresets)
				# self.buildParticlesPresetsButton.setStyleSheet("QPushButton {text-align: center; background: dark green}")

				## Add the buttons to the hLayout
				self.hLayout.addWidget(self.buildFXOceanSetupButton)
				self.hLayout.addWidget(self.buildPresetsButton)
				# self.hLayout.addWidget(self.buildParticlesPresetsButton)
				debug(self.app, method = 'Main_UI', message = 'Added widgets to hLayout', verbose = False)
				self.mainFXBuildLayout.addLayout(self.hLayout)

				###############################
				## BUILD THE MAIN VIEW SWITCHING BUTTONS
				###############################
				self.FXViewGroupBox = QtGui.QGroupBox(self)
				self.FXViewGroupBox.setTitle('Change FX Scene Settings:')
				self.mainFXViewLayout = QtGui.QVBoxLayout(self.FXViewGroupBox)

				self.h2Layout = QtGui.QHBoxLayout(self)
				self._setForRenderButton = QtGui.QPushButton('Apply Render View Settings')
				self._setForRenderButton.pressed.connect(partial(self._setForRender))
				self._setForRenderButton.setStyleSheet("QPushButton {text-align: center; background: dark grey}")

				self._setForFluidsButton = QtGui.QPushButton('Apply Fluid View Settings')
				self._setForFluidsButton.pressed.connect(partial(self._setForFluids))
				self._setForFluidsButton.setStyleSheet("QPushButton {text-align: center; background: dark grey}")

				# self._fetchAnimAlembicButton = QtGui.QPushButton(Icon('alembic.png'), 'Fetch Alembic Anim Caches', self)
				# self._fetchAnimAlembicButton.pressed.connect(partial(self._fetchAlembicCaches, highestAnimVerFolder))
				# self._fetchAnimAlembicButton.setStyleSheet("QPushButton {text-align: center; background: dark grey}")

				## Add the buttons to the h2Layout
				self.h2Layout.addWidget(self._setForRenderButton)
				self.h2Layout.addWidget(self._setForFluidsButton)
				# self.h2Layout.addWidget(self._fetchAnimAlembicButton)
				debug(self.app, method = 'Main_UI', message = 'Added widgets to h2Layout', verbose = False)

				self.mainFXViewLayout.addLayout(self.h2Layout)

				##############################
				##### MAIN SETTINGS UI
				##############################
				self.FXSettingsGroupBox = QtGui.QGroupBox(self)
				self.FXSettingsGroupBox.setTitle('FX Build Settings:')
				self.mainFXLayout = QtGui.QVBoxLayout(self.FXSettingsGroupBox)
				self.optionsVBoxLayout = QtGui.QVBoxLayout(self)

				self.nurbsPreviewOptionsLayout = QtGui.QHBoxLayout()
				##xRes of the NURBSPlane
				self.xResLabel = QtGui.QLabel('zRes')
				self.xRes = QtGui.QDoubleSpinBox()
				self.xRes.setRange(0, 100)
				self.xRes.setSingleStep(1)
				self.xRes.setValue(20)
				##zRes of the NURBSPlane
				self.zResLabel = QtGui.QLabel('zRes')
				self.zRes = QtGui.QDoubleSpinBox()
				self.zRes.setRange(0, 100)
				self.zRes.setSingleStep(1)
				self.zRes.setValue(20)
				debug(self.app, method = 'Main_UI', message = 'Nurbs Preview options built...', verbose = False)

				self.mistPresetLabel = QtGui.QLabel('mist_ParticlePreset')
				self.mistPreset_pullDownMenu = QtGui.QComboBox (self)
				self.mistPreset_pullDownMenu.setMinimumWidth(250)
				self.mistPreset_pullDownMenu.setMaximumHeight(25)

				self.sprayPresetLabel = QtGui.QLabel('spray_ParticlePreset')
				self.sprayPreset_pullDownMenu = QtGui.QComboBox (self)
				self.sprayPreset_pullDownMenu.setMinimumWidth(250)
				self.sprayPreset_pullDownMenu.setMaximumHeight(25)

				self.rearPresetLabel = QtGui.QLabel('rear_ParticlePreset')
				self.rearPreset_pullDownMenu = QtGui.QComboBox (self)
				self.rearPreset_pullDownMenu.setMinimumWidth(250)
				self.rearPreset_pullDownMenu.setMaximumHeight(25)

				## Add the res to the layout
				self.nurbsPreviewOptionsLayout.addWidget(self.xResLabel)
				self.nurbsPreviewOptionsLayout.addWidget(self.xRes)
				self.nurbsPreviewOptionsLayout.addWidget(self.zResLabel)
				self.nurbsPreviewOptionsLayout.addWidget(self.zRes)
				self.nurbsPreviewOptionsLayout.addWidget(self.mistPresetLabel)
				self.nurbsPreviewOptionsLayout.addWidget(self.mistPreset_pullDownMenu)
				self.nurbsPreviewOptionsLayout.addWidget(self.sprayPresetLabel)
				self.nurbsPreviewOptionsLayout.addWidget(self.sprayPreset_pullDownMenu)
				self.nurbsPreviewOptionsLayout.addWidget(self.rearPresetLabel)
				self.nurbsPreviewOptionsLayout.addWidget(self.rearPreset_pullDownMenu)
				self.nurbsPreviewOptionsLayout.addStretch(1)
				debug(self.app, method = 'Main_UI', message = 'Added widgets to nurbsPreviewOptionsLayout', verbose = False)

				self.optionsVBoxLayout .addLayout(self.nurbsPreviewOptionsLayout)


				self.mainFXLayout.addLayout(self.optionsVBoxLayout)
				debug(self.app, method = 'Main_UI', message = 'FXSettingsGroupBox built successfully...', verbose = False)

			#################################
			##############################
			##### OPTIONS BOX BUILD
			self.FXOptionsGroupBox = QtGui.QGroupBox(self)
			self.FXOptionsGroupBox.setTitle('FX Ocean Manual Hookups:')
			self.FXOptionsMainLayout = QtGui.QVBoxLayout(self.FXOptionsGroupBox)

			### MANUAL BUILD BUTTONS
			self.optionshLayout = QtGui.QHBoxLayout()

			# self.connectAllWithOceanButton = QtGui.QPushButton('FX / Connect Height Locks To Ocean')
			# self.connectAllWithOceanButton.pressed.connect(partial(connOH.connectAllWithOceanHeightAttr))
			# debug(self.app, method = 'Main_UI', message = 'self.connectAllWithOceanButton built...', verbose = False)

			#############################################################
			self.connectToOceanButton = QtGui.QToolButton(self)
			self.connectToOceanButton.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
			self.connectToOceanButton.setStyleSheet("QToolButton {text-align: center; background: rgb(100, 100, 100); color: white}")
			connectToOceanButtonStretchPolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
			self.connectToOceanButton.setSizePolicy(connectToOceanButtonStretchPolicy)
			self.connectToOceanButton.setText('All Ocean Hookup')
			self.connectToOceanButton.setMenu( QtGui.QMenu(self.connectToOceanButton) )
			self.connectToOceanButton.clicked.connect(self.connectOceanHeights)

			self.connectToOceanListWidget = QtGui.QListWidget()
			self.connectToOceanListWidget.setFixedHeight(60)
			self.connectToOceanListWidget.addItem('Dock')
			self.connectToOceanListWidget.addItem('Boat')
			self.connectToOceanListWidget.addItem('Prop')
			self.connectToOceanListWidget.addItem('All')
			self.connectToOceanListWidget.clicked.connect(self.connectToOceanButtonText)

			self.connectToOceanAction = QtGui.QWidgetAction(self.connectToOceanButton)
			self.connectToOceanAction.setDefaultWidget(self.connectToOceanListWidget)
			self.connectToOceanButton.menu().addAction(self.connectToOceanAction)
			#############################################################

			if context.step['name'] == 'FX' or context.step['name'] == 'Additional FX':
				self.animShaderIntersectButton = QtGui.QPushButton('Anim Intersect')
				self.animShaderIntersectButton.pressed.connect( partial( fluidLib._intersect_animShader_expression ) )
				debug(self.app, method = 'Main_UI', message = 'self.animShaderIntersectButton built...', verbose = False)

				self.dispShaderIntersectButton = QtGui.QPushButton('Disp Intersect')
				self.dispShaderIntersectButton.pressed.connect( partial( fluidLib._intersect_dispShader_expression ) )
				debug(self.app, method = 'Main_UI', message = 'self.dispShaderIntersectButton built...', verbose = False)

				self.linkEmittersButton = QtGui.QPushButton('FX / Link Emitters To Ocean')
				self.linkEmittersButton.pressed.connect(partial(fluidLib._linkWakeEmitters))
				debug(self.app, method = 'Main_UI', message = 'self.linkEmittersButton built...', verbose = False)

			self.optionshLayout.addWidget(self.connectToOceanButton)

			## Add the buttons to the optionshLayout
			if context.step['name'] == 'FX' or context.step['name'] == 'Additional FX':
				self.optionshLayout.addWidget(self.animShaderIntersectButton)
				self.optionshLayout.addWidget(self.dispShaderIntersectButton)
				self.optionshLayout.addWidget(self.linkEmittersButton)

			### Now parent the FXOption layouts to the options main VBoxLayout
			self.FXOptionsMainLayout.addLayout(self.optionshLayout)

			###############################
			## FX INTERACTIVE SECTION
			###############################

			if context.step['name'] == 'FX' or context.step['name'] == 'Additional FX':
				## MAIN SECTION
				self.FXInteractiveGroupBox = QtGui.QGroupBox(self)
				self.FXInteractiveGroupBox.setTitle('FX Interactive:')
				self.FXInteractiveMainLayout = QtGui.QVBoxLayout(self.FXInteractiveGroupBox)

				## MAIN LAYOUT
				self.FXInteractiveLayout = QtGui.QHBoxLayout()

				## SETUP BUTTONS
				self.cacheFluidsButton = QtGui.QPushButton('Cache fluids')
				self.cacheFluidsButton.pressed.connect(fc.cacheFluidsToCTemp)
				self.cacheFluidsButton.setStyleSheet("QPushButton {text-align: center; background: dark orange; color: black}")
				# self.cacheFluidsButton.setEnabled(False)

				self.previewInteractiveButton = QtGui.QPushButton('Preview Interactive')
				self.previewInteractiveButton.pressed.connect(fc.previewInteractiveCaches)
				self.previewInteractiveButton.setStyleSheet("QPushButton {text-align: center; background: dark orange; color: black}")
				# self.previewInteractiveButton.setEnabled(False)

				self.cleanupCacheFilesButton = QtGui.QPushButton('Cleanup fluids caches')
				self.cleanupCacheFilesButton.setStyleSheet("QPushButton {text-align: center; background: dark orange; color: black}")
				self.cleanupCacheFilesButton.pressed.connect(fc.deleteCaches)
				# self.cleanupCacheFilesButton.setEnabled(False)

				self.cleanupICacheFilesButton = QtGui.QPushButton('Cleanup interactive caches')
				self.cleanupICacheFilesButton.setStyleSheet("QPushButton {text-align: center; background: dark orange; color: black}")
				self.cleanupICacheFilesButton.pressed.connect(fc.deleteInteractiveCaches)
				# self.cleanupICacheFilesButton.setEnabled(False)

				## ADD BUTTON TO LAYOUT
				self.FXInteractiveLayout.addWidget(self.cacheFluidsButton)
				self.FXInteractiveLayout.addWidget(self.previewInteractiveButton)
				self.FXInteractiveLayout.addWidget(self.cleanupCacheFilesButton)
				self.FXInteractiveLayout.addWidget(self.cleanupICacheFilesButton)

				## Now parent the FXOption layouts to the options main VBoxLayout
				self.FXInteractiveMainLayout.addLayout(self.FXInteractiveLayout)

			###############################
			## BUILD THE FX LIBRARY STUFFS
			###############################

			if context.step['name'] == 'FX' or context.step['name'] == 'Additional FX':
				self.FXLibGroupBox = QtGui.QGroupBox(self)
				self.FXLibGroupBox.setTitle('FX Library:')
				self.FXLibMainLayout = QtGui.QVBoxLayout(self.FXLibGroupBox)

				### HORIZONTAL BOX LAYOUT
				self.fxLibshLayout = QtGui.QGridLayout()

				j = 0
				pos =   [
						(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
						(1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
						(2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
						(3, 0), (3, 1), (3, 2), (3, 3), (3, 4),
						(4, 0), (4, 1), (4, 2), (4, 3), (4, 4),
						]

				fxNames = [('Boat Splash', fxLib.splashRigger, 'Creates a spherical volumetric emitter that emits sprite as splashes'),
						   ('Splash Tool v1.0', self.openSplashTool,'working'),
						   ('Bubble on selected Mesh(s)', fxLib.bubbleSetup, 'Creates bubble setup on selected mesh'),
						   ('Kill Field', fxLib.nParticle_killField, 'How it works?\n    - Creates a uniform field (change-able) volume shapes that kills any particles when in contact.\n    - LifespanPP expression line added into runtime after dynamics of nParticleShape.\n    - Lifespan mode needs to be changed to lifespanPP in order to work.\n\nUsage\n    - Select nParticle(s) and click button.'),
						   ('Wake / Foam Emitter', fluidLib._addWakeEmitter),
						   ('-', fxLib._underConstruction),
						   ('-', fxLib._underConstruction),
						   ('-', fxLib._underConstruction),
						   ('-', fxLib._underConstruction),
						   ('-', fxLib._underConstruction),
						   ]

				for fxName in fxNames:
					buttonName = fxName[0]
					buttonFunc = fxName[1]
					buttonToolTip = fxName[2] if len(fxName) == 3 else None

					button = QtGui.QPushButton(buttonName)
					button.pressed.connect( partial(buttonFunc) )
					if buttonToolTip:
						button.setToolTip(buttonToolTip)

					self.fxLibshLayout.addWidget(button, pos[j][0], pos[j][1])
					j += 1

				### Now parent the FXOption layouts to the options main VBoxLayout
				self.FXLibMainLayout.addLayout(self.fxLibshLayout)

			###############################

			## Delete Ocean Setup
			self.deleteButton = QtGui.QPushButton('Delete Ocean Setup!')
			self.deleteButton.setFlat(False)
			self.deleteButton.pressed.connect(partial(fxLib.removeOceanSetup, context.step["name"]))
			self.deleteButton.setStyleSheet("QPushButton {text-align: center; background: dark red; color: black}")

			## Now add to the mainLayout
			debug(self.app, method = 'Main_UI', message = 'Parenting widgets....', verbose = False)
			self.mainLayout.addLayout(self.lowhiLayout)
			self.mainLayout.addWidget(self.animGroupBox)

			if context.step['name'] == 'FX' or context.step['name'] == 'Additional FX':
				self.mainLayout.addWidget(self.FXBuildGroupBox)
				self.mainLayout.addWidget(self.FXViewGroupBox)
				self.mainLayout.addWidget(self.FXSettingsGroupBox)
				self.mainLayout.addWidget(self.FXLibGroupBox)
				self.mainLayout.addWidget(self.FXInteractiveGroupBox)
				## Hide the build settings atm because we're not using them
				self.FXSettingsGroupBox.hide()

			self.mainLayout.addWidget(self.FXOptionsGroupBox)
			self.mainLayout.addWidget(self.deleteButton)
			self.mainLayout.addStretch(1)
			self.resize(50,120)

			if context.step['name'] == 'FX' or context.step['name'] == 'Additional FX':
				self.animGroupBox.hide()
				self.populatePulldowns()
				debug(app = self.app, method = 'Main_UI', message= 'self.xRes.value(): %s' % self.xRes.value(), verbose = False)
				debug(app = self.app, method = 'Main_UI', message= 'self.zRes.value(): %s' % self.zRes.value(), verbose = False)
			debug(self.app, method = 'Main_UI', message = 'UI Build SUCCESS.', verbose = False)
		else:
			QtGui.QMessageBox.information(None, "Aborted...", 'You must have active a current 3D viewport! \nRight click the viewport to build from as we need to use the camera information.')
			self.parent.close()

	def connectOceanHeights(self):
		connOH.connectAllWithOceanHeightAttr( object = self.connectToOceanButton.text() )

	def connectToOceanButtonText(self):
		text = '%s Ocean Hookup' % self.connectToOceanListWidget.currentItem().text()
		self.connectToOceanButton.setText(text)
		self.connectToOceanButton.menu().hide()

	def deleteInteractiveTag(self):
		typesToCheck = ['locator', 'nurbsCurve']
		for type in typesToCheck:
			for each in cmds.ls(type = type):
				object = cmds.listRelatives(each, parent = True)[0]
				if cmds.objExists('%s.interactiveMasterBoat' % object):
					try:
						cmds.deleteAttr('%s.interactiveMasterBoat' % object)
					except:
						cmds.warning('Failed to delete interactive master boat tag away from "%s", please consult your supervisor!' % object)

	def openSplashTool(self):
		self.myNewWindow = splash.MainWindow()
		self.myNewWindow.show()

	def _connectToOcean(self):
		"""
		Used as a fresh rebuild of the ocean height locators for an interactive ocean scene in animation
		As the FX button adds the bake and then rebuilds don't work in animation due to this attr existing
		"""
		print 'Connecting animation interactive ocean hooks to the oceans now...'
		connOH._deleteAllBakeAttrsOnLocators()
		connOH.connectAllWithOceanHeightAttr()

	def _fetchAlembicCaches(self, pathToFxPublishFolder):
		rePathToAlembiCaches = r'%s/alembic_anim/%s' % (pathToFxPublishFolder.split('fx')[0], pathToFxPublishFolder.split('fx')[-1])
		if os.path.isdir(rePathToAlembiCaches):
			for each in os.listdir(rePathToAlembiCaches):
				abcNode = '%s/%s' % (rePathToAlembiCaches, each)
				debug(app = self, method = '_fetchAlembicCaches', message = 'abcNode %s' % abcNode, verbose = False)
				cmds.AbcImport(abcNode, reparent  = "|ABC_ANIM_CACHES_hrc", setToStartFrame = True)

	def _setPresets(self):
		pass

	def populatePulldowns(self):
		pathToPresetsFolder = CONST.NPART_PRESETPATH

		for eachPreset in os.listdir(pathToPresetsFolder):
			if not os.path.isdir('%s/%s' % (pathToPresetsFolder, eachPreset)):
				self.mistPreset_pullDownMenu.addItem(eachPreset)
				self.sprayPreset_pullDownMenu.addItem(eachPreset)
				self.rearPreset_pullDownMenu.addItem(eachPreset)

	def _setForRender(self):
		"""
		Switch the viewport for rendering settings for fluids and ocean preview planes
		"""
		cmds.setAttr('oceanPreviewPlane_heightF.resolution', 120)
		cmds.setAttr ("OCEAN_hrc.oceanRes", 120)
		cmds.setAttr ("OCEAN_hrc.oceanCalcOnOff", 1)
		cmds.setAttr("%s.shadedDisplay" % CONST.FOAM_FLUID_SHAPENODE, 0)
		cmds.setAttr("%s.shadedDisplay" % CONST.WAKE_FLUID_SHAPENODE, 0)
		cmds.setAttr("oceanPreviewPlane_prv.visibility", 1)
		settings._setHWRenderGlobals()

	def _setForFluids(self):
		"""
		Switch the viewport to see the denisty and temp on the fluid textures
		"""
		# cmds.setAttr('oceanPreviewPlane_heightF.resolution', 1)
		# cmds.setAttr ("OCEAN_hrc.oceanRes", 1)
		cmds.setAttr ("OCEAN_hrc.oceanCalcOnOff", 1)
		cmds.setAttr("%s.shadedDisplay" % CONST.FOAM_FLUID_SHAPENODE, 3)
		cmds.setAttr("%s.shadedDisplay" % CONST.WAKE_FLUID_SHAPENODE, 2)
		cmds.setAttr("oceanPreviewPlane_prv.visibility", 0)

	def _getEditor(self):
		"""
		Get the modelEditor with focus
		"""
		currentPanel = cmds.getPanel(withFocus = True)
		if 'modelPanel' not in currentPanel:
			return False
		else:
			currentEditor = cmds.modelPanel(currentPanel, q = True, modelEditor = True)
			debug(app = self.app, method = '_getEditor', message= 'Current Editor is: %s' % currentEditor, verbose = False)
			self.currentEditor = currentEditor
			return currentEditor

	def setupFXOcean(self, pathToAnimCaches = ''):
			"""
			used to setup the base FX scene after animation scene loaded in
			"""
			## Setup the progress bar
			inprogressBar = pbui.ProgressBarUI(title = 'FX Ocean Setup:')
			inprogressBar.show()
			inprogressBar.updateProgress(percent = 5, doingWhat = 'Building base ocean fx...')

			## If not interactive scene, boats oceanLoc and world_ctrl shouldn't have any interactiveMasterBoat tag on it
			if not cmds.objExists(CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE) and not cmds.objExists(CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE):
				self.deleteInteractiveTag()

			oceanBuilder.buildFXOcean(self.editor, self.oceanPublishedPresetPath,
									  self.foamPresetPath.replace('\\', '/'),
									  self.wakePresetPath.replace('\\', '/'),
									  self.highTide.isChecked(),
									  xRes = int(self.xRes.value()),
									  zRes = int(self.zRes.value()),
									  inprogressBar = inprogressBar,
									  pathToAnimCaches = pathToAnimCaches,
									  )

			inprogressBar.updateProgress(percent = 100, doingWhat = 'Complete')
			inprogressBar.close()

	def setupInteractionOcean(self):
			"""
			used to setup the base FX scene after animation scene loaded in
			"""
			## Setup the progress bar
			inprogressBar = pbui.ProgressBarUI(title = 'Interactive Ocean Setup:')
			inprogressBar.show()
			inprogressBar.updateProgress(percent = 5, doingWhat = 'Building base ocean fx...')

			mySel = cmds.ls(sl = True)
			if mySel:
				if len(mySel) > 1:
					cmds.warning('You must have only one boat world ctrl selected!')
					inprogressBar.updateProgress(percent = 100, doingWhat = 'Complete')
					inprogressBar.close()
					return -1
				elif 'world_ctrl' not in mySel[0]:
					cmds.warning('You must have a valid master boat world_ctrl curve selected!')
					inprogressBar.updateProgress(percent = 100, doingWhat = 'Complete')
					inprogressBar.close()
					return -1
				else:
					oceanBuilder.buildAnimInteractionOcean(self.editor,
														  self.oceanPublishedPresetPath,
														  self.foamPresetPath.replace('\\', '/'),
														  self.wakePresetPath.replace('\\', '/'),
														  self.highTide.isChecked(),
														  xRes = 20,
														  zRes = 20,
														  inprogressBar = inprogressBar,
														  selected = mySel,
														  interactive = True
														  )
			else:
				cmds.warning('You must have a valid world_ctrl selected!!!')
				inprogressBar.updateProgress(percent = 100, doingWhat = 'Complete')
				inprogressBar.close()

			inprogressBar.updateProgress(percent = 100, doingWhat = 'Complete')
			inprogressBar.close()

	def setInitalState(self):
		"""
		Function to perform the initial state for the fluids.
		"""

	def get_shotfx_publish_dirs(self):
		tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
		shotfx_publishes = tk.paths_from_template(self.app.get_template('shotfx_publish_template'), {'Step' : 'FX', 'id' : id, 'Shot' : self.app.context.entity['name']})

		## Fetch foam.xml/wake.xml/fluids_hrc.mb from fx publish
		fc.fetchWakesFromFX(fx_publish_path = shotfx_publishes)