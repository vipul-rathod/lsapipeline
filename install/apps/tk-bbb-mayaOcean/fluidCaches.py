import os, getpass, sys, shutil, sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError
import xml.etree.cElementTree as et

## Custom stuff
if 'T:/software/lsapipeline/custom' not in sys.path:
	sys.path.append('T:/software/lsapipeline/custom')
import oceanNurbsPreviewPlane as oceanNPP
import nParticleSetup as npart
import fluids_lib as fluidsLib
from debug import debug
import utils as utils
import CONST as CONST
import maya_asset_MASTERCLEANUPCODE as cleanup
#reload(CONST)
#reload(utils)
#reload(oceanNPP)
#reload(npart)
#reload(cleanup)

def _filter_fluids_on_selection(type = "fluidTexture3D"):

	fluids = []

	selected = cmds.ls(selection = 1, long = 1)
	if selected:
		for each in selected:
			if cmds.nodeType(each) == type:
				if each not in fluids:
					fluids.append(each)
			else:
				shape = cmds.listRelatives(each, allDescendents = 1, fullPath = 1)
				if shape:
					for x in shape:
						if cmds.nodeType(x) == type:
							if x not in fluids:
								fluids.append(x)

	return fluids

def _filter_cache_on_fluids(fluids = []):
	"""
	Function to filter any cache linked to fluid node
	"""
	if not fluids:
		fluids = _filter_fluids_on_selection()

	if fluids:
		cache_files = []

		for sel in fluids:
			cache = cmds.listConnections(sel, type = "cacheFile")
			if cache:
				cache = list( set(cache) )
				for chc in cache:
					if chc not in cache_files:
						cache_files.append(chc)

		return cache_files
	else:
		mel.eval(r'print "Fluid(s) not in selection...\n";')

def delete_caches_on_selection():
	"""
	Function to delete any existing caches on currently selected fluids
	"""
	debug(None, method = 'fluidCaches.delete_caches_on_selection', message = 'Deleting...', verbose = False)
	fluidsCache = _filter_cache_on_fluids()
	debug(None, method = 'fluidCaches.delete_caches_on_selection', message = 'fluidsCache(): %s' % fluidsCache, verbose = False)
	if fluidsCache:
		for cache in fluidsCache:
			try:
				cmds.delete(cache)
				mel.eval(r'print "Deleted \"%s\".\n";' %cache)
			except:
				pass
	debug(None, method = 'fluidCaches.delete_caches_on_selection', message = 'Finished...', verbose = False)

def _cacheWake(cachepath = '', oceanFluidTextures = [], fluids = []):
	"""
	Internal used by _publish_fx_caches_for_item
	"""

	cleanup.turnOffModelEditors()

	debug(None, method = 'fluidCaches._cacheWake', message = 'cachepath: %s' % cachepath, verbose = False)
	debug(None, method = 'fluidCaches._cacheWake', message = 'oceanFluidTextures: %s' % oceanFluidTextures, verbose = False)
	debug(None, method = 'fluidCaches._cacheWake', message = 'fluids: %s' % fluids, verbose = False)

	## Setup various vars
	output = r'%s' % cachepath
	debug(None, method = 'fluidCaches._cacheWake', message = 'output: %s' % output, verbose = False)

	## Start/end = 0 / Render settings = 1 / Time slider = 2
	time_range_mode        = 2

	start_frame            = cmds.playbackOptions(min = 1, q = 1)
	end_frame              = cmds.playbackOptions(max = 1, q = 1)

	debug(None, method = 'fluidCaches._cacheWake', message = 'start_frame: %s' % start_frame, verbose = False)
	debug(None, method = 'fluidCaches._cacheWake', message = 'end_frame: %s' % end_frame, verbose = False)

	### OneFilePerFrame / OneFile
	file_Distribution      = "OneFilePerFrame"

	refresh_during_caching = 1
	directory              = output.replace('\\', '/')
	# One file per object
	cache_per_geometry     = 1
	cache_name             = "" # We're not specifying any fluid name here as we enabled "One File Per Object" which automatically set the name on selected fluids
	cache_name_as_prefix   = 0

	## add / replace / merge / mergeDelete
	cache_method           = "replace"

	force_save             = 0
	evaluation             = 1
	evaluation_multiplier  = 1
	inherit_modification   = 0
	store_double_as_floats = 1
	caching_format         = "mcc"
	cache_density          = 1
	cache_velocity         = 1
	cache_temperature      = 1
	cache_fuel             = 1
	cache_color            = 1
	cache_texture_coord    = 1
	cache_falloff          = 1

	if not fluids:
		## Now select the fluid for caching as this is required by maya
		cmds.select(oceanFluidTextures, r = True)
		debug(None, method = 'fluidCaches._cacheWake', message = 'cur Selection is now: %s' % cmds.ls(sl= True), verbose = False)
		selection = _filter_fluids_on_selection()
	else:
		debug(None, method = 'fluidCaches._cacheWake', message = 'Fluids True: fluids: %s' % fluids, verbose = False)
		selection = fluids

	if selection:
		# check for existing cache file and delete then select fluids for new caching
		cmds.select(selection, replace = True)
		delete_caches_on_selection()
		debug(None, method = 'fluidCaches._cacheWake', message = 'cur Selection after cache deletion is now: %s' % cmds.ls(sl= True), verbose = False)

		print 'doCreateFluidCache 5 { "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s" } ;' % (time_range_mode, start_frame, end_frame, file_Distribution, refresh_during_caching, directory,cache_per_geometry,cache_name,cache_name_as_prefix,cache_method,force_save,evaluation,evaluation_multiplier,inherit_modification,store_double_as_floats,caching_format,cache_density,cache_velocity,cache_temperature,cache_fuel,cache_color,cache_texture_coord,cache_falloff)

		# Perform some clean-up (with fluids selected)
		debug(None, method = 'fluidCaches._cacheWake', message = 'Clearing inital state', verbose = False)
		mel.eval("ClearInitialState;")
		debug(None, method = 'fluidCaches._cacheWake', message = 'performDeleteFluidsIC', verbose = False)
		mel.eval("performDeleteFluidsIC 0;")

		debug(None, method = 'fluidCaches._cacheWake', message = 'Performing fluid caching now...', verbose = False)
		mel.eval('doCreateFluidCache 5 { "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s" } ;'
		%(  time_range_mode,
			start_frame,
			end_frame,
			file_Distribution,
			refresh_during_caching,
			directory,
			cache_per_geometry,
			cache_name,
			cache_name_as_prefix,
			cache_method,
			force_save,
			evaluation,
			evaluation_multiplier,
			inherit_modification,
			store_double_as_floats,
			caching_format,
			cache_density,
			cache_velocity,
			cache_temperature,
			cache_fuel,
			cache_color,
			cache_texture_coord,
			cache_falloff
		))

	else:
		debug(None, method = 'fluidCaches._cacheWake', message = 'FAILED: No fluids in selection!', verbose = False)
		mel.eval(r'print "Fluid(s) not in selection...\n";')

	cleanup.turnOnModelEditors()

def _connectAttr(src, dst, **kwargs):
	"""
	Helper function used in the rebuild_cache_from_xml function
	"""
	src = str(src)
	dst = str(dst)

	if cmds.objExists(src) and cmds.objExists(dst):
		if not cmds.isConnected(src, dst):
			try:
				cmds.connectAttr(src, dst, **kwargs)
			except:
				mel.eval( r'warning "Failed to connect \"%s\" to \"%s\"...";' %(src, dst) )

def rebuild_cache_from_xml(xmlPath, fluidShape = ''):
	"""
	Based off Autodesk cache's xml file structure to get and set
	*.tag / *.attrib / *.text / *.tail

	NOTE: Interactive cache attachments;
	IF the interactive master boat is found in the scene
	These caches need to be attached to the interactive wake and foam 3D fluid textures for the purposes of previewing the caches.
	Later on during publish we cache the base wake and foam, then attach these caches back to the ocean_dispShader and then perform a merge caches and output that to the publish folder.
	"""
	debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'Rebuilding Caches', verbose = False)
	debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'xmlPath: %s' % xmlPath, verbose = False)
	if os.path.exists(xmlPath):
		debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'GOOD! Path to xml exists: %s' % xmlPath, verbose = False)

		# Create a new cache node
		cache = cmds.cacheFile(createCacheNode = True, fileName = xmlPath)
		debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'Cache node: %s' % cache, verbose = False)

		# Parse xml file
		xml  = et.parse(xmlPath)
		root = xml.getroot()

		# By default, Autodesk's xml structure has all the attributes and value set in the <extra> tag.
		# Therefore, we have to go through all of them and set them in maya because cache only works
		# properly with all the same settings or it'll show some warning stating some values aren't the same.
		for tag in root.findall("extra"):
			try:
				attr, tag = tag.text.split("=")
				# debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'attr: %s' % attr, verbose = False)
				# debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'tag: %s' % tag, verbose = False)
			except:
				attr = None

			if attr is not None:
				if cmds.objExists(attr):
					try:
						cmds.setAttr( attr, eval(tag) )
					except:
						debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'Failed to set %s' % attr , verbose = False)
						mel.eval( r'warning "Failed to set \"%s\"...";' %attr )

		# Get exactly the same slot number of the cache and fluid's connection hook-ups or cache won't work properly.
		fluids = []
		for x in root.findall("Channels"):
			for y in x.getchildren():
				channelName = y.get("ChannelName")
				debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'channelName: %s' % channelName, verbose = False)
				debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'y.get("ChannelName").split("_"): %s' % y.get("ChannelName").split("_"), verbose = False)

				if 'interactive' in y.get("ChannelName"): ## Note the split here was separating the interactive_oceanFoam naming badly so this gets handled differently here for interactive
					fluid = '_'.join(y.get("ChannelName").split("_")[0:-1])
					attr = y.get("ChannelName").split("_")[-1]
				else:
					fluid, attr = y.get("ChannelName").split("_")

				if cmds.objExists(fluidShape):
					fluid = fluidShape

				index = y.tag.strip("channel")
				src = "%s.outCacheData[%s]" %(cache, index)
				dst = "%s.in%s" %( fluid, attr.title() )

				cmds.setAttr("%s.ch[%s]" %(cache, index), channelName, type = "string")
				_connectAttr(src, dst, force = 1)

				if fluid not in fluids:
					fluids.append(fluid)

		# More connections to hook up...
		for fluid in fluids:
			src = "time1.outTime"
			dst = "%s.currentTime" %fluid
			_connectAttr(src, dst, force = 1)

			src = "%s.inRange" %cache
			dst = "%s.playFromCache" %fluid
			_connectAttr(src, dst, force = 1)

		debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'SUCCESS', verbose = False)
		return cache
	else:
		debug(app = None, method = 'fluidCaches.rebuild_cache_from_xml', message = 'FAILED TO FIND PATH TO CACHE', verbose = False)
		return None

def mergeFluidCaches(interactiveFoamXML = '', interactiveWakeXML = ''):
	"""
	Creates blendcaches for the fluid containers....
	"""
	###########################################
	## IS THIS AN INTERACTIVE SETUP FX SCENE???
	## IF SO BLEND THE CACHES
	###########################################
	## Now that we have cached the fluids we have to merge the cache files together
	## Animation publishes these caches with the SAME name as the base wake caches, so these can actually blend!
	debug(app = None, method = 'mergeFluidCaches', message = 'Creating cache blends now...', verbose = False)

	foamCache = cmds.cacheFile(createCacheNode = True, fileName = interactiveFoamXML.replace('\\', '/'))
	foamCache = cmds.rename(foamCache, '%s_cacheFile' % CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE)
	debug(app = None, method = '_publish_fx_caches_for_item', message = 'foamCache: \t\t%s' % foamCache, verbose = False)

	wakeCache = cmds.cacheFile(createCacheNode = True, fileName = interactiveWakeXML.replace('\\', '/'))
	wakeCache = cmds.rename(wakeCache, '%s_cacheFile' % CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE)
	debug(app = None, method = '_publish_fx_caches_for_item', message = 'wakeCache: %s' % wakeCache, verbose = False)

	cmds.select(CONST.FOAM_FLUID_SHAPENODE, r = True)
	foamBlend = cmds.cacheFileCombine()
	debug(app = None, method = 'mergeFluidCaches', message = 'foamBlend: %s' % foamBlend, verbose = False)

	cmds.cacheFileCombine(foamBlend[0], e = True, cc = foamCache)
	debug(app = None, method = 'mergeFluidCaches', message = 'CacheBlend for foam made successfully', verbose = False)

	cmds.select(CONST.WAKE_FLUID_SHAPENODE, r = True)
	wakeBlend = cmds.cacheFileCombine()
	debug(app = None, method = 'mergeFluidCaches', message = 'wakeBlend: %s' % wakeBlend, verbose = False)

	cmds.cacheFileCombine(wakeBlend[0], e = True, cc = wakeCache)
	debug(app = None, method = 'mergeFluidCaches', message = 'CacheBlend for wake made successfully', verbose = False)

	## Now hard set all the inputs to a weight of 1
	for each in cmds.ls(type = 'cacheBlend'):
		cmds.setAttr("%s.cacheData[0].weight" % each, 1)
		cmds.setAttr("%s.cacheData[1].weight" % each, 1)

def _getPathFromSceneName():
	sceneName = cmds.file(sceneName = True, q = True)
	if sceneName:
		if '/'.join( sceneName.split('/')[:3] ) == 'I:/lsapipeline/episodes':
			currentVersion = os.path.basename(sceneName).split('.')[1]
			path = os.path.join('C:\\Temp', '/'.join( os.path.dirname(sceneName).split('/')[1:-3] ), 'FX/publish', currentVersion).replace('\\', '/')
			if not os.path.exists(path):
				try:	os.makedirs(path)
				except:	cmds.warning('Failed to create directory for "%s"...' % path)

			return path
		else:
			cmds.warning('Working directory not in "I:/lsapipeline/episodes"...')
	else:
		cmds.warning('Please save your scene first!')

def cacheFluidsToCTemp():
	if cmds.objExists(CONST.FOAM_FLUID_SHAPENODE) and cmds.objExists(CONST.WAKE_FLUID_SHAPENODE):
		## Get default non-cached wake and foam
		fluidsToCache = []
		for cache in [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE]:
			fluidConnection = cmds.listConnections(cache, type = 'cacheFile') or cmds.listConnections(cache, type = 'cacheBlend')
			if fluidConnection:
				if cmds.nodeType(fluidConnection[0]) == 'cacheFile' or cmds.nodeType(fluidConnection[0]) == 'cacheBlend':
					cmds.confirmDialog(title = 'CACHE FLUIDS', message = 'Cache already exist for "%s". You should cleanup your caches if you want to re-cache a newer one!' % cache, button = 'OK')
				else:
					fluidsToCache.append(cache)
			else:
				fluidsToCache.append(cache)

		## Cache em fluids at one go to save time
		if fluidsToCache:
			cachePath = _getPathFromSceneName()
			if cachePath:
				if os.path.exists(cachePath):
					_cacheWake(cachepath = cachePath, fluids = fluidsToCache)

					## Set time to min
					[cmds.currentTime( cmds.playbackOptions(q = True, min = True) ) for x in range(2)]
	else:
		cmds.confirmDialog(title = 'CACHE FLUIDS', message = 'Both "%s" and "%s" fluids don\'t exist in your scene!' % (CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE), button = 'OK')

def fetchWakesFromFX(fx_publish_path = ''):
	"""
	Function to help preview the wakes from FX publishes
	"""
	if fx_publish_path:
		## Get the highest version
		highestVersion = max(fx_publish_path)

		## Cleanup whatever that will be stopping from rebuilding
		deleteCaches()
		deleteInteractiveCaches()
		if cmds.objExists('fluids_hrc'):
			cmds.delete('fluids_hrc')

		for each in os.listdir(highestVersion):
			## Get fluids_hrc mb file
			if each.startswith('fluids_hrc') and each.endswith('.mb'):
				try:
					## Import the fluids_hrc group mb file now...
					fluids_hrc = os.path.join(highestVersion, each).replace('\\', '/')
					fluids_hrc_nodes = cmds.file(fluids_hrc, i = True, returnNewNodes = True)

					## Group fluids_hrc under OCEAN_hrc
					cmds.parent('fluids_hrc', 'OCEAN_hrc')
					for each in fluids_hrc_nodes:
						try:	cmds.delete(each)
						except:	pass

					## Set ocean into correct placement base off .mb fluids_hrc
					_setOceanLocation()
				except:
					cmds.warning('Failed to load FX file, file is corrupt or somehow!')

		for each in os.listdir(highestVersion):
			## Rebuild Foam from XML
			if each.startswith(CONST.FOAM_FLUID_SHAPENODE) and each.endswith('.xml'):
				foam_xml = os.path.join(highestVersion, each).replace('\\', '/')
				try:
					rebuild_cache_from_xml(foam_xml)
				except:
					cmds.warning('Failed to connect cache %s' % foam_xml)
			## Rebuild Wake from XML
			elif each.startswith(CONST.WAKE_FLUID_SHAPENODE) and each.endswith('.xml'):
				wake_xml = os.path.join(highestVersion, each).replace('\\', '/')
				try:
					rebuild_cache_from_xml(wake_xml)
				except:
					cmds.warning('Failed to connect cache %s' % wake_xml)

		## Some ocean connections...
		if cmds.objExists(CONST.OCEANDISPSHADER) and cmds.objExists(CONST.WAKE_FLUID_SHAPENODE) and cmds.objExists(CONST.FOAM_FLUID_SHAPENODE):
			try:    cmds.connectAttr("%s.outAlpha" % CONST.WAKE_FLUID_SHAPENODE, "%s.waveHeightOffset" % CONST.OCEANDISPSHADER, force = True)
			except: pass
			try:    cmds.connectAttr("%s.outAlpha" % CONST.FOAM_FLUID_SHAPENODE, "%s.foamOffset" % CONST.OCEANDISPSHADER, force = True)
			except: pass
	else:
		cmds.warning('THERE ARE NO FLUID CONTAINERS PUBLISHED FROM FX FOR THIS SHOT! Please see your cg supervisor now...')

def _setOceanLocation():
	"""
	Exposing a tool to help push the ocean into the right location based off the FX published fluid containers fluids_hrc
	"""
	## If the fluids_hrc exists
	if cmds.objExists('fluids_hrc'):
		if cmds.objExists('oceanPreviewPlane_prv'):
			cmds.setAttr( 'oceanPreviewPlane_prv.translateX', cmds.getAttr('fluids_hrc.translateX') )
			cmds.setAttr( 'oceanPreviewPlane_prv.translateZ', cmds.getAttr('fluids_hrc.translateZ') )
		else:
			cmds.warning('MISSING oceanPreviewPlane_prv node from scene....')

		if cmds.objExists('ocean_srf'):
			if not cmds.isConnected('oceanPreviewPlane_prv.translateX', 'ocean_srf.translateX'):
				cmds.connectAttr('oceanPreviewPlane_prv.translateX', 'ocean_srf.translateX', f = True)
			if not cmds.isConnected('oceanPreviewPlane_prv.translateZ', 'ocean_srf.translateZ'):
				cmds.connectAttr('oceanPreviewPlane_prv.translateZ', 'ocean_srf.translateZ', f = True)
		else:
			cmds.warning('MISSING ocean_srf node from scene....')
	else:
		cmds.warning('NO fluids_hrc FOUND! Can not move the ocean into final position. PLEASE CHECK FX PUBLISH NOW!')

def previewInteractiveCaches():
	"""
	Function to help preview the interactive caches in the FX step
	"""
	## Check if this shot has any interactive
	interactiveScene = False
	if cmds.objExists(CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE) and cmds.objExists(CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE):
		interactiveScene = True

	if interactiveScene:
		if cmds.objExists(CONST.FOAM_FLUID_SHAPENODE) and cmds.objExists(CONST.WAKE_FLUID_SHAPENODE):
			## First, we clean up any interactive cache files or blend as we can re-attach from anim/publish to save some troubles...
			deleteInteractiveCaches()

			## Check for non-cached fluids as they are required for cache blending
			uncachedFluids = []
			for cache in [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE]:
				fluidConnection = cmds.listConnections(cache, type = 'cacheFile') or cmds.listConnections(cache, type = 'cacheBlend')
				if fluidConnection:
					if cmds.nodeType(fluidConnection[0]) == 'cacheFile' or cmds.nodeType(fluidConnection[0]) == 'cacheBlend':
						pass
					else:
						uncachedFluids.append(cache)
				else:
					uncachedFluids.append(cache)

			if not uncachedFluids:
				interactive_publishDir = '%s/Anm/publish/fx' % '/'.join( os.path.dirname( cmds.file(sceneName = True, q = True) ).split('/')[:-3] )
				interactive_publishes = [os.path.join(interactive_publishDir, x).replace('\\', '/') for x in os.listdir(interactive_publishDir) if os.path.isdir( os.path.join(interactive_publishDir, x).replace('\\', '/') ) and x.startswith('v')]
				interactive_foam_xml = ''
				interactive_wake_xml = ''
				if interactive_publishes:
					highestVersion = max(interactive_publishes)
					for each in os.listdir(highestVersion):
						if each.endswith('xml'):
							if each.split('.')[0] in CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE:
								interactive_foam_xml = os.path.join(highestVersion, each).replace('\\', '/')
							elif each.split('.')[0] in CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE:
								interactive_wake_xml = os.path.join(highestVersion, each).replace('\\', '/')
				else:
					cmds.confirmDialog(title = 'Interactive Publish', message = 'Couldn\'t find interactive publish in\n%s,\n please check with the animators!' % interactive_publishDir, button = 'OK')

				## If anim publish's both wake and foam .xml exist, perform blend else don't do shit
				if os.path.exists(interactive_foam_xml) and os.path.exists(interactive_wake_xml):
					mergeFluidCaches(interactiveFoamXML = interactive_foam_xml, interactiveWakeXML = interactive_wake_xml)

				## Final clean-up (Delete Unused cache files
				[cmds.delete(cache) for cache in cmds.ls(type = 'cacheFile') if not cmds.listConnections(cache, type = 'fluidTexture3D') and not cmds.listConnections(cache, type = 'cacheBlend')]

				## Set time to min
				[cmds.currentTime( cmds.playbackOptions(q = True, min = True) ) for x in range(2)]
			else:
				cmds.confirmDialog(title = 'Interactive Scene', message = 'Please cache your "%s" and "%s" fluids first!' % (CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE), button = 'OK')
		else:
			cmds.confirmDialog(title = 'Interactive Scene', message = 'Both "%s" and "%s" fluids don\'t exist in your scene!' % (CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE), button = 'OK')
	else:
		cmds.confirmDialog(title = 'Interactive Scene', message = 'Both "%s" and "%s" fluids don\'t exist in your scene!' % (CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE, CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE), button = 'OK')

def deleteCaches():
	[ cmds.delete(cache) for cache in cmds.ls(type = 'cacheFile') if cache.split('Cache')[0] in [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE] ]

def deleteInteractiveCaches():
	[cmds.delete(cache) for cache in cmds.ls(type = 'cacheFile') if cache.split('_')[0] in 'interactive']
	[cmds.delete(cache) for cache in cmds.ls(type = 'cacheBlend')]