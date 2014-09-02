import os, sys, types, time
import shutil
import maya.cmds as cmds
import maya.mel as mel
import tank
from tank import Hook
from tank import TankError
import xml.etree.cElementTree as ET

## Now get the custom tools
if 'T:/software/lsapipeline/custom' not in sys.path:
	sys.path.append('T:/software/lsapipeline/custom')
if 'T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean' not in sys.path:
	sys.path.append('T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean')
import utils as utils
import CONST as CONST
from debug import debug
import maya_asset_MASTERCLEANUPCODE as cleanup
import fluidCaches as fluidCaches
#reload(CONST)
#reload(cleanup)
#reload(fluidCaches)

class PublishHook(Hook):
	"""
	Single hook that implements publish functionality for secondary tasks
	"""
	def execute(self, tasks, work_template, comment, thumbnail_path, sg_task, primary_publish_path, progress_cb, **kwargs):
		"""
		Main hook entry point
		:tasks:         List of secondary tasks to be published.  Each task is a
						dictionary containing the following keys:
						{
							item:   Dictionary
									This is the item returned by the scan hook
									{
										name:           String
										description:    String
										type:           String
										other_params:   Dictionary
									}

							output: Dictionary
									This is the output as defined in the configuration - the
									primary output will always be named 'primary'
									{
										name:             String
										publish_template: template
										tank_type:        String
									}
						}

		:work_template: template
						This is the template defined in the config that
						represents the current work file

		:comment:       String
						The comment provided for the publish

		:thumbnail:     Path string
						The default thumbnail provided for the publish

		:sg_task:       Dictionary (shotgun entity description)
						The shotgun task to use for the publish

		:primary_publish_path: Path string
						This is the path of the primary published file as returned
						by the primary publish hook

		:progress_cb:   Function
						A progress callback to log progress during pre-publish.  Call:

							progress_cb(percentage, msg)

						to report progress to the UI

		:returns:       A list of any tasks that had problems that need to be reported
						in the UI.  Each item in the list should be a dictionary containing
						the following keys:
						{
							task:   Dictionary
									This is the task that was passed into the hook and
									should not be modified
									{
										item:...
										output:...
									}

							errors: List
									A list of error messages (strings) to report
						}
		"""
		## Make sure the scene assembly plugins are loaded
		utils.loadSceneAssemblyPlugins(TankError)

		results = []
		gpuCaches = []
		staticCaches = []
		animCaches = []
		fxCaches = []
		fluidCaches = []

		## Clean the animation alembic bat now for a fresh publish
		pathToBatFile = CONST.PATHTOANIMBAT
		if os.path.isfile(pathToBatFile):
			os.remove(pathToBatFile)

		## PROCESS THE ITEMS into lists so we can compress down the alembic export into selected items.
		## This saves a bunch of time because we won't be running the animated stuff over the full range of the time line for EACH item, we can do it on
		## a larger selection.
		for task in tasks:
			item = task["item"]
			output = task["output"]
			errors = []

			##DEBUGG
			# report progress:
			geoGrp = ''
			progress_cb(0, "Processing Scene Secondaries now...", task)

			## STATIC CACHES LIST
			if item["type"] == "static_caches":
				try:
					## Now process the assembly definition files as these have a difference hrc to normal references as they exist without a top level ns in the scene.
					if '_ADef_' in item['name']:
						geoGrp = [geoGrp for geoGrp in cmds.listRelatives(item['name'], children = True) if '_hrc' in geoGrp][0]
						if geoGrp not in staticCaches:
							staticCaches.append(geoGrp)
					elif 'PROP' in item['name']:
						if item['name'] not in staticCaches:
							staticCaches.append(item['name'])
					else:
						pass
				except Exception, e:
					errors.append("Publish failed - %s" % e)

			## ANIM CACHES LIST
			elif item["type"] == "anim_caches":
				try:
					## Now process the assembly definition files as these have a difference hrc to normal references as they exist without a top level ns in the scene.
					if '_ADef_' in item['name']:
						geoGrp = [geoGrp for geoGrp in cmds.listRelatives(item['name'], children = True) if '_hrc' in geoGrp][0]
						if geoGrp not in animCaches:
							animCaches.append(geoGrp)

					if 'CHAR' in item['name']:
						if item['name'] not in animCaches:
							animCaches.append(item['name'])

					elif 'PROP' in item['name']:
						if item['name'] not in animCaches:
							animCaches.append(item['name'])

					elif 'BLD' in item['name'] and '_ADef_' not in item['name']:
						if item['name'] not in animCaches:
							animCaches.append(item['name'])
					else:
						pass
				except Exception, e:
					errors.append("Publish failed - %s" % e)

			## GPU CACHES
			elif item["type"] == "gpu_caches":
				if item['name'] not in gpuCaches:
					gpuCaches.append(item['name'])

			## CAMERA
			elif item["type"] == "camera":
				self._publish_camera_for_item(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)

			## FX CACHES
			elif item["type"] == "fx_caches":
				progress_cb(25, "Processing Ocean Preset %s now..." % item['name'], task)
				self._publish_oceanPreset(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)
				progress_cb(50, "DONE Processing Fluid Cache %s" % item['name'], task)

			## FLUIDS CACHES
			elif item["type"] == "fluid_caches":
				progress_cb(25, "Processing Fluid Cache %s now..." % item['name'], task)
				fluidCaches.append(item['name'])
				progress_cb(50, "DONE Processing Fluid Cache %s" % item['name'], task)

			## ANIMATION CURVES
			elif item["type"] == "anim_atom":
				debug(app = None, method = '_publish_animation_curves_for_item', message =  "Processing Animation Curves now...", verbose = False)
				self._publish_animation_curves_for_item(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)

			## CREASE XML
			elif item["type"] == "crease_xml":
				debug(app = None, method = '_publish_crease_xml_for_item', message =  "Processing Crease XML now...", verbose = False)
				self._publish_crease_xml_for_item(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)

			else:
				# don't know how to publish this output types!
				errors.append("Don't know how to publish this item! Contact your supervisor to build a hook for this type.")

			## if there is anything to report then add to result
			if len(errors) > 0:
				## add result:
				results.append({"task":task, "errors":errors})

			progress_cb(100, "Done Processing Inital Secondaries, moving to final caching....", task)

		staticDone = False
		animDone = False
		gpuDone = False
		fluidDone = False
		cachesToExport = False
		## Because we don't want to continually iter through the tasks and do the same shit over and over we're setting a quick Done true or false here because I'm tired and can't
		## think of a better way at the moment....
		progress_cb(0, "Processing Static, Anim, GPU and Fluid caches now...")

		debug(app = None, method = '_publish_fx_caches_for_item', message =  "Processing DONE. Performing Cache exports now...", verbose = False)
		debug(app = None, method = '_publish_fx_caches_for_item', message =  "gpuCaches: %s" % gpuCaches, verbose = False)
		debug(app = None, method = '_publish_fx_caches_for_item', message =  "fluidCaches: %s" % fluidCaches, verbose = False)
		debug(app = None, method = '_publish_fx_caches_for_item', message =  "animCaches: %s" % animCaches, verbose = False)
		debug(app = None, method = '_publish_fx_caches_for_item', message =  "staticCaches: %s" % staticCaches, verbose = False)

		if gpuCaches or fluidCaches or animCaches or staticCaches:
			for task in tasks:
				item    = task["item"]
				output  = task["output"]
				errors  = []

				##DEBUGG
				# report progress:
				geoGrp  = ''
				## STATIC CACHES
				if item["type"] == "static_caches":
					if not staticDone:
						## Now process the publishing of the lists so we can bulk export the appropriate assets to avoid hundreds of alembic files.
						## STATIC CACHES
						static = True
						groupName = 'staticCaches'
						if len(staticCaches) <= 0:
							print 'Static cache list empty, skipping...'
						else:
							progress_cb(25, "Processing Static Caches now...")
							debug(app = None, method = '_publish_fx_caches_for_item', message =  "Processing Static Caches now...", verbose = False)
							cmds.select(staticCaches, r = True) # Select the cache objects for static export now and replace the current selection with this list.

							## Do a quick check that every assembly reference marked for export as alembic is at full res
							for each in cmds.ls(sl= True):
								self._upResAssemblyRefs(each)

							for x in groupName:
								print x

							self._publish_alembic_cache_for_item(groupName, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb, static)
							staticDone = True
							cachesToExport = True
							progress_cb(35, "Done processing Static Caches!")

				## ANIMATED CACHES
				elif item["type"] == "anim_caches":
					if not animDone:
						static = False
						groupName = 'animCaches'
						if len(animCaches) <= 0:
							print 'Animated cache list empty, skipping...'
						else:
							progress_cb(45, "Processing Anim Caches now...")
							debug(app = None, method = '_publish_fx_caches_for_item', message =  "Processing Anim Caches now...", verbose = False)
							cmds.select(animCaches, r = True) # Select the cache objects for static export now and replace the current selection with this list.

							## Do a quick check that every assembly reference marked for export as alembic is at full res
							for each in cmds.ls(sl= True):
								self._upResAssemblyRefs(each)

							self._publish_alembic_cache_for_item(groupName, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb, static)
							animDone = True
							cachesToExport = True
							progress_cb(50, "Done processing Anim Caches!")

				## GPU CACHES
				elif item["type"] == "gpu_caches":
					if not gpuDone:
						if len(gpuCaches) <= 0:
							print 'GPU caches list empty, skipping...'
						else:
							progress_cb(55, "Processing GPU Caches now...")
							allItems = gpuCaches
							debug(app = None, method = '_publish_fx_caches_for_item', message =  "Processing GPU Caches now...", verbose = False)
							cmds.select(gpuCaches, r = True)# Select the cache objects for gpu export now and replace the current selection with this list.
							self._publish_gpu_cache_for_item(allItems, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)
							gpuDone = True
							cachesToExport = True

				## FLUID CACHES
				elif item["type"] == "fluid_caches":
					if not fluidDone:
						if len(fluidCaches) <= 0:
							print 'Fluid caches list empty, skipping...'
						else:
							progress_cb(55, "Processing Fluid Caches now...")
							debug(app = None, method = '_publish_fx_caches_for_item', message =  "Processing Fluid Caches now...", verbose = False)
							allItems = fluidCaches ## not actually using these
							debug(app = None, method = '_publish_fx_caches_for_item', message =  "allItems: %s" % allItems, verbose = False)
							self._publish_fluid_caches_for_item(allItems, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)
							fluidDone = True
							cachesToExport = True

				else:
					pass

		## Set all AD to gpuCache
		progress_cb(75)
		[cmds.assembly(each, edit = True, active = 'gpuCache') for each in cmds.ls(type = 'assemblyReference')]

		progress_cb(100)
		debug(app = None, method = '_publish_fx_caches_for_item', message =  "Cache exports finished... moving cache files now if appropriate", verbose = False)
		### COPY THE CACHE FILES TO THE SERVER NOW
		### Subprocess to copy files from the temp folder to the server
		if cachesToExport:
			import subprocess
			CTEMP = CONST.CTMP
			BATCHNAME = CONST.PATHTOANIMBAT
			p = subprocess.Popen(BATCHNAME, cwd=CTEMP, shell=True, bufsize=4096, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			stdout, stderr = p.communicate()
			# if p.returncode == 0:
			#     return results
			# else:
			#     results.append({"task":'File Copy', "errors":['Publish failed - could not copy files to the server!']})
			#     return results
			return results
		else:
			return results

	def _publish_fluid_caches_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
		"""
		Export the Fluid Texture Caches
		"""
		## Do the regular Shotgun processing now
		debug(app = None, method = '_publish_fluid_caches_for_item', message =  'Processing now...', verbose = False)
		group_name = 'Fluids'
		debug(app = None, method = '_publish_fluid_caches_for_item', message =  'group_name: %s' % group_name, verbose = False)

		tank_type = 'Alembic Cache'
		debug(app = None, method = '_publish_fluid_caches_for_item', message =  'tank_type: %s' % tank_type, verbose = False)

		publish_template = output["publish_template"]
		debug(app = None, method = '_publish_fluid_caches_for_item', message =  'publish_template: %s' % publish_template, verbose = False)

		# get the current scene path and extract fields from it
		# using the work template:
		scene_path = os.path.abspath(cmds.file(query = True, sn = True))
		debug(app = None, method = '_publish_fx_caches_for_item', message =  'scene_path: %s' % scene_path, verbose = False)

		fields = work_template.get_fields(scene_path)

		publish_version = fields["version"]

		# update fields with the group name:
		fields["grp_name"] = group_name

		## create the publish path by applying the fields
		## with the publish template:
		publish_path = publish_template.apply_fields(fields)
		debug(app = None, method = '_publish_fluid_caches_for_item', message =  'publish_path: %s' % publish_path, verbose = False)

		tempFolder = r"C:\Temp%s" % publish_path.split("I:")[-1]
		debug(app = None, method = '_publish_fluid_caches_for_item', message = 'tempFolder: %s' % tempFolder, verbose = False)

		#print 'CHECKING IF DIR %s EXISTS' % publish_path
		if not os.path.isdir(publish_path):
			os.mkdir(publish_path)
		## If the temp folder doesn't exist make one now
		if not os.path.isdir(os.path.dirname(tempFolder)):
			os.makedirs(os.path.dirname(tempFolder))

		print '====================='
		print 'Exporting %s now to %s' % (group_name, publish_path)

		## Now cache the fluids.
		## Here we rename the fluids so during FX these will blend properly.
		## Rename wakes transforms
		cmds.rename(CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE.split('Shape')[0], CONST.WAKE_FLUID_SHAPENODE.split('Shape')[0])
		debug(app = None, method = '_publish_fluid_caches_for_item', message = 'Renamed %s to %s' % (CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE.split('Shape')[0], CONST.WAKE_FLUID_SHAPENODE.split('Shape')[0]), verbose = False)

		## Rename foams transforms
		cmds.rename(CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE.split('Shape')[0], CONST.FOAM_FLUID_SHAPENODE.split('Shape')[0])
		debug(app = None, method = '_publish_fluid_caches_for_item', message = 'Renamed %s to %s' % (CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE.split('Shape')[0], CONST.FOAM_FLUID_SHAPENODE.split('Shape')[0]), verbose = False)

		## Rename the oceanDispShader to temp
		cmds.rename(CONST.OCEANDISPSHADER, '%s_temp' % CONST.OCEANDISPSHADER)
		debug(app = None, method = '_publish_fluid_caches_for_item', message = 'Renamed %s to %s_temp' % (CONST.OCEANDISPSHADER, CONST.OCEANDISPSHADER), verbose = False)

		## Rename the interactive to ocean displacement
		cmds.rename(CONST.OCEANINTERACTIVESHADER, CONST.OCEANDISPSHADER)
		debug(app = None, method = '_publish_fluid_caches_for_item', message = 'Renamed %s to %s' % (CONST.OCEANINTERACTIVESHADER, CONST.OCEANDISPSHADER), verbose = False)

		## Do the caches
		caches = [CONST.WAKE_FLUID_SHAPENODE, CONST.FOAM_FLUID_SHAPENODE]
		debug(app = None, method = '_publish_fluid_caches_for_item', message = 'Caching fluids: %s' % caches, verbose = False)
		fluidCaches._cacheWake(cachepath = tempFolder, fluids = caches)

		## add to bat file
		## Now write the bat file out for the file copy
		pathToBatFile = CONST.PATHTOANIMBAT
		if not os.path.isfile(pathToBatFile):
			outfile = open(pathToBatFile, "w")
		else:
			outfile = open(pathToBatFile, "a")
		# for each in caches:
			# outfile.write('copy %s\%s.mc %s\%s.mc\n' % (tempFolder, each, publish_path, each))
			# outfile.write('copy %s\%s.xml %s\%s.xml\n' % (tempFolder, each, publish_path, each))
		outfile.write( 'robocopy "%s" "%s" /e /move\n' % (tempFolder, publish_path) )
		outfile.close()

		## Put the naming back to interactive for claritys sake
		cmds.rename(CONST.WAKE_FLUID_SHAPENODE.split('Shape')[0], CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE.split('Shape')[0])
		cmds.rename(CONST.FOAM_FLUID_SHAPENODE.split('Shape')[0], CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE.split('Shape')[0])
		cmds.rename(CONST.OCEANDISPSHADER, CONST.OCEANINTERACTIVESHADER)
		cmds.rename('%s_temp' % CONST.OCEANDISPSHADER, CONST.OCEANDISPSHADER)

		self._register_publish(publish_path,
							   '%s_INTERACTIVEFLUIDS' % group_name,
							   sg_task,
							   publish_version,
							   tank_type,
							   comment,
							   thumbnail_path,
							   [primary_publish_path])
		print 'DONE exporting %s' % group_name
		print '====================='
		cmds.currentTime(1)

	def _upResAssemblyRefs(self, aRef):
		if cmds.nodeType(aRef) == 'assemblyReference':
			## Check to see what isn't loaded to full res for exporting. Those that are not turn them to full res now for cache exporting.
			if not cmds.assembly(aRef, query = True, active = True) == 'full':
				cmds.assembly(aRef, edit = True, active = 'full')

	def _publish_alembic_cache_for_item(self, groupName, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb, static):
		"""
		Export an Alembic cache for the specified item and publish it to Shotgun.
		NOTE:
		Because we are not processing tasks which would give us 500 bazillion caches we have to hardset some of the naming and pathing here for the exporting.
		This way we can select the entire list of static or animated groups / meshes in the scene and use ONE alembic export for selected command instead of massive data
		through put for ALL the individual parts.
		NOTE 2:
		GroupName is handled differently than normal here because we are processing the item[] as a list after the initial task iter see the execution for this
		"""
		group_name = groupName
		tank_type = 'Alembic Cache'
		publish_template = output["publish_template"]

		# get the current scene path and extract fields from it
		# using the work template:
		scene_path = os.path.abspath(cmds.file(query=True, sn= True))
		fields = work_template.get_fields(scene_path)
		publish_version = fields["version"]
		# update fields with the group name:
		fields["grp_name"] = group_name
		## create the publish path by applying the fields
		## with the publish template:
		publish_path = publish_template.apply_fields(fields)
		debug(app = None, method = 'PublishHook', message = 'publish_path: %s' % publish_path, verbose = False)

		tempFolder = r"C:\Temp%s" % publish_path.split("I:")[-1]
		debug(app = None, method = 'PublishHook', message = 'tempFolder: %s' % tempFolder, verbose = False)

		pathToVersionDir = '\\'.join(publish_path.split('\\')[0:-1])
		## build and execute the Alembic export command for this item:
		if static:
			frame_start = 1
			frame_end = 1
		else:
			frame_start = cmds.playbackOptions(query = True, animationStartTime = True)
			frame_end = cmds.playbackOptions(query = True, animationEndTime = True)

		## Exporting on selection requires the entire selection to be added with their full paths as -root flags for the export command
		## Do this now by setting up a string and processing the selection into that string.
		rootList = ''
		for eachRoot in cmds.ls(sl= True):
			rootList = '-root %s %s' % (str(cmds.ls(eachRoot, l = True)[0]), rootList)

		## If the publish dir doesn't exist make one now.
		if not os.path.isdir(pathToVersionDir):
			os.mkdir(pathToVersionDir)
		## If the temp folder doesn't exist make one now
		if not os.path.isdir(os.path.dirname(tempFolder)):
			os.makedirs(os.path.dirname(tempFolder))

		## Now build the final export command to use with the python AbcExport
		abc_export_cmd = "preRollStartFrame -15 -attr SubDivisionMesh -attr smoothed -attr dupAsset -attr mcAssArchive -attr version -ro -uvWrite -wholeFrameGeo -worldSpace -writeVisibility -fr %d %d %s -file %s" % (frame_start, frame_end, rootList, tempFolder)

		## add to bat file
		## Now write the bat file out for the file copy
		pathToBatFile = CONST.PATHTOANIMBAT
		if not os.path.isfile(pathToBatFile):
			outfile = open(pathToBatFile, "w")
		else:
			outfile = open(pathToBatFile, "a")
		outfile.write('copy %s %s\n' % (tempFolder, publish_path))
		outfile.close()

		try:
			self.parent.log_debug("Executing command: %s" % abc_export_cmd)
			print '====================='
			print 'Exporting %s to alembic cache now to %s' % (group_name, publish_path)
			[cmds.currentTime(frame_start) for i in range(2)] ## Just to make sure current time is at start of timeslider to prevent frame 1 popping issue...
			cmds.AbcExport(verbose = False, j = abc_export_cmd)
		except Exception, e:
			raise TankError("Failed to export Alembic Cache!!")

		## Finally, register this publish with Shotgun
		self._register_publish(publish_path,
							   '%sABC' % group_name,
							   sg_task,
							   publish_version,
							   tank_type,
							   comment,
							   thumbnail_path,
							   [primary_publish_path])
		print 'Finished alembic export...'
		print '====================='

	def _publish_gpu_cache_for_item(self, items, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
		"""
		"""
		group_name = 'gpuCaches'
		items = items
		tank_type = 'Alembic Cache'
		publish_template = output["publish_template"]

		# get the current scene path and extract fields from it
		# using the work template:
		scene_path = os.path.abspath(cmds.file(query=True, sn= True))
		fields = work_template.get_fields(scene_path)
		publish_version = fields["version"]
		# update fields with the group name:
		fields["grp_name"] = group_name
		## create the publish path by applying the fields
		## with the publish template:
		publish_path = publish_template.apply_fields(fields)
		#'@asset_root/publish/gpu/{name}[_{grp_name}].v{version}.abc'
		fileName = os.path.splitext(publish_path)[0].split('\\')[-1]
		fileDir = '/'.join(publish_path.split('\\')[0:-1])
		pathToVersionDir = '\\'.join(publish_path.split('\\')[0:-1])
		if not os.path.isdir(pathToVersionDir):
			os.mkdir(pathToVersionDir)

		try:
			self.parent.log_debug("Executing GPU Cache export now to: \n\t\t%s" % publish_path)
			print '====================='
			print 'Exporting gpu now to %s\%s' % (fileDir, fileName)
			print items

			#===================================================================
			# ###Try to do a recursive gpu export.
			# getGPUS = [eachItem for eachItem in items if cmds.assembly(eachItem, query = True, active = True) == 'gpuCache']
			# cmds.select(getGPUS, r = True)
			# ## Now do the gpu cache export for each of the items
			# try:
			#     #print 'GPU STRING IS: \n%s' % 'gpuCache -startTime 1 -endTime 1 -optimize -optimizationThreshold 40000 -directory \"%s\" \"%s\";' % (fileDir, each)
			#     mel.eval("gpuCache -startTime 1 -endTime 1 -optimize -optimizationThreshold 40000 -directory \"%s\" -fileName \"%s\" - allDagObjects;" % (fileDir, group_name))
			# except:
			#     #print 'GPU STRING IS: \n%s' % 'gpuCache -startTime 1 -endTime 1 -optimize -optimizationThreshold 40000 -directory \"%s\" \"%s\";' % (fileDir, each)
			#     cmds.warning('FAILED TO PUBLISH GPU CACHE: %s' %  each)
			#===================================================================
			for each in items:
				## Now do the gpu cache export for each of the items
				try:
					#print 'GPU STRING IS: \n%s' % 'gpuCache -startTime 1 -endTime 1 -optimize -optimizationThreshold 40000 -directory \"%s\" \"%s\";' % (fileDir, each)
					mel.eval("gpuCache -startTime 1 -endTime 1 -optimize -optimizationThreshold 40000 -directory \"%s\" \"%s\";" % (fileDir, each))
				except:
					#print 'GPU STRING IS: \n%s' % 'gpuCache -startTime 1 -endTime 1 -optimize -optimizationThreshold 40000 -directory \"%s\" \"%s\";' % (fileDir, each)
					cmds.warning('FAILED TO PUBLISH GPU CACHE: %s' %  each)

		except Exception, e:
			raise TankError("Failed to export gpu cache file.. check for corrupt assembly references!")

		## Finally, register this publish with Shotgun
		self._register_publish(publish_path,
							   '%sGPU' % group_name,
							   sg_task,
							   publish_version,
							   tank_type,
							   comment,
							   thumbnail_path,
							   [primary_publish_path])
		print 'Finished gpu export...'
		print '====================='

	def _publish_camera_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
		"""
		Export the camera
		"""
		## Do the regular Shotgun processing now
		cam_name = item['name']
		tank_type = 'Maya Scene'
		publish_template = output["publish_template"]

		# get the current scene path and extract fields from it
		# using the work template:
		scene_path = os.path.abspath(cmds.file(query=True, sn= True))
		fields = work_template.get_fields(scene_path)
		publish_version = fields["version"]
		# update fields with the group name:
		fields["cam_name"] = cam_name
		## create the publish path by applying the fields
		## with the publish template:
		publish_path = publish_template.apply_fields(fields)
		pathToVersionDir = '\\'.join(publish_path.split('\\')[0:-1])
		if not os.path.isdir(pathToVersionDir):
			os.mkdir(pathToVersionDir)

		if cmds.objExists('BAKE_CAM_hrc'):
			cmds.delete('BAKE_CAM_hrc')
		debug(app = None, method = '_publish_camera_for_item', message =  "Baking %s now..." % cam_name, verbose = False)
		utils._bakeCamera(cam_name)
		cmds.select('BAKE_CAM_hrc', r = True)
		cmds.file(publish_path, options = "v=0;", typ = "mayaAscii", es = True, force= True)
		## Finally, register this publish with Shotgun
		self._register_publish(publish_path,
							   '%sCAM' % cam_name,
							   sg_task,
							   publish_version,
							   tank_type,
							   comment,
							   thumbnail_path,
							   [primary_publish_path])

	def _publish_oceanPreset(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
		"""
		Export the Fluid Texture Caches
		"""
		## Do the regular Shotgun processing now
		group_name = item['name']
		tank_type = 'Alembic Cache'
		publish_template = output["publish_template"]

		# get the current scene path and extract fields from it
		# using the work template:
		scene_path = os.path.abspath(cmds.file(query=True, sn= True))
		fields = work_template.get_fields(scene_path)
		publish_version = fields["version"]
		# update fields with the group name:
		fields["grp_name"] = group_name
		## create the publish path by applying the fields
		## with the publish template:
		publish_path = publish_template.apply_fields(fields)

		#print 'CHECKING IF DIR %s EXISTS' % publish_path
		if not os.path.isdir(publish_path):
			os.mkdir(publish_path)

		print '====================='
		## Now save the dispShader Preset .. this should be the exact same setup as the animation ocean shader and if it isn't shoot the animator now..
		dispShaderPreset = mel.eval("saveAttrPreset ocean_dispShader ocean_dispShader.v%s 0" %  publish_version)

		## Now move this to the publish folder so we can assign it back to a new maya ocean when we setup the lighting caches..
		if os.path.isfile('%s/%s.v%s.mel'% (publish_path, 'ocean_dispShader', publish_version)):
			os.remove('%s/%s.v%s.mel'% (publish_path, 'ocean_dispShader', publish_version))

		os.rename(dispShaderPreset, '%s/%s.v%s.mel'% (publish_path, 'ocean_dispShader', publish_version))

		## Get ocean_dispShader's keyframe curves for animation transfer if there's any
		## Export ATOM
		oceanKeyframes = []
		oceanShaders = [x for x in cmds.ls(type = 'oceanShader')]
		if oceanShaders:
			for ocShader in oceanShaders:
				connections = cmds.listConnections(ocShader, type = 'animCurve')
				if connections:
					oceanKeyframes.append(ocShader)

			if oceanKeyframes:
				min = cmds.playbackOptions(min = True, q = True)
				max = cmds.playbackOptions(max = True, q = True)

				cmds.select(oceanKeyframes, replace = True)

				mel.eval('performImportAnim 1;')

				outputPath = '%s/%s.v%s.atom' % (publish_path.replace('\\', '/'), 'ocean_dispShader', publish_version)
				cmds.file(  outputPath,
							force = True,
							options = 'precision = 8; statics = 1; baked = 1; sdk = 1; constraint = 1; animLayers = 1; selected = selectedOnly; whichRange = 2; range = %s:%s; hierarchy = none; controlPoints = 0; useChannelBox = 1; options = keys; copyKeyCmd = -animation objects -time >%s:%s> -float >%s:%s> -option keys -hierarchy none -controlPoints 0' % (min, max, min, max, min, max),
							type = 'atomExport',
							exportSelected = True,
							)

				if cmds.window('OptionBoxWindow', exists = True):
					cmds.deleteUI('OptionBoxWindow', window = True)

		## Now register this with shotgun
		self._register_publish(publish_path,
							   'ocean_dispShader_OceanPreset',
							   sg_task,
							   publish_version,
							   tank_type,
							   comment,
							   thumbnail_path,
							   [primary_publish_path])
		print 'DONE exporting %s' % group_name
		print '====================='
		cmds.currentTime(1)

	def _publish_animation_curves_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
		"""
		Method for publishing animation curves...
		"""
		# Get the current scene path and extract fields from it
		# Using the work template:
		scene_path = os.path.abspath(cmds.file(query=True, sn = True)) # I:\bubblebathbay\episodes\ep106\ep106_sh030\FX\work\maya\ep106sh030.v025.ma
		debug(app = None, method = '_publish_animation_curves_for_item', message =  'scene_path: %s' % scene_path, verbose = False)

		fields = work_template.get_fields(scene_path) # {'Shot': u'ep106_sh030', 'name': u'ep106sh030', 'Sequence': u'ep106', 'Step': u'FX', 'version': 25, 'group_name': u'spriteSpray_nParticle_T_RShape'}

		############################################################

		## Do the regular Shotgun processing now
		group_name = '%s_ATOM' % fields['name'] # ep106sh030_animCurves_XML
		debug(app = None, method = '_publish_animation_curves_for_item', message =  'group_name: %s' % group_name, verbose = False)

		tank_type = 'Maya Scene' # Maya Scene
		debug(app = None, method = '_publish_animation_curves_for_item', message =  'tank_type: %s' % tank_type, verbose = False)

		publish_template = output["publish_template"] # <Sgtk TemplatePath maya_shot_fxRenderFinal: episodes/{Sequence}/{Shot}//FxLayers/R{version}>
		debug(app = None, method = '_publish_animation_curves_for_item', message =  'publish_template: %s' % publish_template, verbose = False)

		############################################################

		publish_version = fields["version"]

		## Update fields with the group_name
		fields["group_name"] = group_name

		## Get episode and shot name from field directly
		epShotName = fields["name"]

		## create the publish path by applying the fields
		## with the publish template:
		publish_path = '%s.atom' % publish_template.apply_fields(fields) # K:\bubblebathbay\episodes\ep106\ep106_sh030\FxLayers\R025

		################################################################################################################
		## Get all loaded references, get all objects from reference nodes, filter out transform only so we can avoid stuffs like joints, ikHandles, constraints etc etc...
		top_hrc = [each for ref in cmds.ls(references = True) if cmds.referenceQuery(ref, isLoaded = True) for each in cmds.referenceQuery(ref, nodes = True) if cmds.objectType(each) == 'transform']
		shotCam = [mel.eval('rootOf("%s");' % each.split('.')[0]) for each in cmds.ls('*.type', long = True) if cmds.getAttr(each) == 'shotCam']
		top_hrc.extend(shotCam) if shotCam else None
		shotCam = [each.split('.')[0] for each in cmds.ls('*.type', long = True) if cmds.getAttr(each) == 'shotCam']
		top_hrc.extend(shotCam) if shotCam else None

		if top_hrc:
			## ATOM EXPORT
			## Get min/max time
			min = cmds.playbackOptions(min = True, q = True)
			max = cmds.playbackOptions(max = True, q = True)
			[cmds.currentTime(min) for i in range(2)]

			## Force ATOM UI to pop out
			mel.eval('ExportAnimOptions;')

			## Fucking maya's atom need seletion to import animation grrr...
			cmds.select(top_hrc, replace = True)

			## Perform ATOM Export
			cmds.file(	publish_path,
						force = True,
						type = 'atomExport',
						exportSelected = True,
						options = 'precision=8;statics=1;baked=1;sdk=0;constraint=0;animLayers=1;selected=selectedOnly;whichRange=2;range=%s:%s;hierarchy=none;controlPoints=0;useChannelBox=1;options=keys;copyKeyCmd=-animation objects -time >%s:%s> -float >%s:%s> -option keys -hierarchy none -controlPoints 0 ' % (min, max, min, max, min, max),
						)

			## Delete ATOM UI after export
			if cmds.window('OptionBoxWindow', exists = True):
				cmds.deleteUI('OptionBoxWindow', window = True)
			################################################################################################################

			## Finally, register publish to shotgun...
			self._register_publish(publish_path,
								   group_name,
								   sg_task,
								   publish_version,
								   tank_type,
								   comment,
								   thumbnail_path,
								   [primary_publish_path])
			print 'Successfully rendered Animation Curves to %s...' % publish_path
			print '=================================================='

	def _publish_crease_xml_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
		"""
		Method for publishing animation curves...
		"""
		# Get the current scene path and extract fields from it
		# Using the work template:
		scene_path = os.path.abspath( cmds.file(query=True, sn = True) ) # I:\bubblebathbay\episodes\ep106\ep106_sh030\FX\work\maya\ep106sh030.v025.ma
		debug(app = None, method = '_publish_animation_curves_for_item', message =  'scene_path: %s' % scene_path, verbose = False)

		fields = work_template.get_fields(scene_path) # {'Shot': u'ep106_sh030', 'name': u'ep106sh030', 'Sequence': u'ep106', 'Step': u'FX', 'version': 25, 'group_name': u'spriteSpray_nParticle_T_RShape'}

		############################################################

		## Do the regular Shotgun processing now
		group_name = '%s_CREASEXML' % fields['name'] # ep106sh030_CREASEXML
		debug(app = None, method = '_publish_crease_xml_for_item', message =  'group_name: %s' % group_name, verbose = False)

		tank_type = 'Maya Scene' # Maya Scene
		debug(app = None, method = '_publish_crease_xml_for_item', message =  'tank_type: %s' % tank_type, verbose = False)

		publish_template = output["publish_template"] # <Sgtk TemplatePath maya_shot_fxRenderFinal: episodes/{Sequence}/{Shot}//FxLayers/R{version}>
		debug(app = None, method = '_publish_crease_xml_for_item', message =  'publish_template: %s' % publish_template, verbose = False)

		############################################################

		publish_version = fields["version"]

		## Update fields with the group_name
		fields["group_name"] = group_name

		## Get episode and shot name from field directly
		epShotName = fields["name"]

		## create the publish path by applying the fields
		## with the publish template:
		publish_path = '%s.xml' % publish_template.apply_fields(fields) # K:\bubblebathbay\episodes\ep106\ep106_sh030\FxLayers\R025

		################################################################################################################
		self._writeCreaseToXML(xmlPath = publish_path)

		## Finally, register publish to shotgun...
		self._register_publish(publish_path,
							   group_name,
							   sg_task,
							   publish_version,
							   tank_type,
							   comment,
							   thumbnail_path,
							   [primary_publish_path])
		print 'Successfully rendered Animation Curves to %s...' % publish_path
		print '=================================================='

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

	def _writeCreaseToXML(self, xmlPath = ''):
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

	def _register_publish(self, path, name, sg_task, publish_version, tank_type, comment, thumbnail_path, dependency_paths = None):
		"""
		Helper method to register publish using the
		specified publish info.
		"""
		# construct args:
		args = {
			"tk": self.parent.tank,
			"context": self.parent.context,
			"comment": comment,
			"path": path,
			"name": name,
			"version_number": publish_version,
			"thumbnail_path": thumbnail_path,
			"task": sg_task,
			"dependency_paths": dependency_paths,
			"published_file_type":tank_type,
		}

		# register publish;
		sg_data = tank.util.register_publish(**args)
		return sg_data