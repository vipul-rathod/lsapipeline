from maya import cmds, mel
import ProgressBarUI as pbui
import itertools

def nParticle_killField():
	position = _getCam_centerOfInterest()
	opts = {"name":"killField1", "position":position, "magnitude":0.001, "attenuation":0, "directionX":0, "directionY":-1, "directionZ":0, "volumeShape":"cube"}
	_dynamicField(field = "uniform", opts = opts)

def _dynamicField(field = "uniform", opts = {}):
	## Only proceed if nParticle(s) in selection
	selection = _filter_type_on_selection(type = 'nParticle', toShape = True)
	if selection:

		cmds.select(clear = True)
		try:
			## Field creation
			node = eval( 'cmds.%s(**%s)' %(field, opts) )
		except:
			node = None

		if node:
			for each in selection:
				cmds.connectDynamic(each, fields = node[0])

			## Set expression to all nParticle (runtimeAfterDynamics)
			inputForce = cmds.listConnections('%s.outputForce' % node[0], type = 'nParticle', plugs = True)
			if inputForce:
				inputForce = list( set( inputForce ) )

				for each in inputForce:
					## Get expression's current string to add-on inputForce line
					nParticleShape = each.split(".")[0]

					currentStr = cmds.dynExpression(nParticleShape, query = True, rad = True, string = True)
					inputForceStr = 'if (mag(%s) >= 0.001){%s.lifespanPP = 0.0;}\n' %(each, nParticleShape)
					if not currentStr.endswith('\n'):
						currentStr = '%s\n' % currentStr
						currentStr += inputForceStr

					cmds.dynExpression(nParticleShape, edit = True, rad = True, string = currentStr)
		else:
			mel.eval('warning "Failed to create killField!";')
	else:
		mel.eval('warning "Please select proper nParticle(s)!";')

def _filter_type_on_selection(type = '', toShape = False):
	if type:
		selection = cmds.ls(selection = True)
		if selection:
			filtered_selection = []
			for each in selection:

				if toShape:
					try:    each = cmds.listRelatives(each, shapes = True, fullPath = True)[0]
					except: pass

				if cmds.objectType(each, isType = type):
					if each not in filtered_selection:
						filtered_selection.append(each)

			return filtered_selection if filtered_selection else []
		else:
			mel.eval('warning "Nothing was selected!";')
	else:
		mel.eval('warning "No particular type was specified!";')

def _underConstruction():
	mel.eval('print "Not ready yet!\\n"')

def _getCam_centerOfInterest():
	## Get camera from current view
	currentPanel = cmds.getPanel(withFocus= True) or 'modelPanel4'

	## Only works with view port active, else create at default world 0, 0, 0
	panelType = cmds.getPanel(typeOf = currentPanel)
	if panelType !=  "modelPanel":
		return [0, 0, 0]
	else:
		camera = cmds.modelPanel(currentPanel, query = True, camera = True)
		cameraShape = cmds.listRelatives(camera) or camera
		position = cmds.camera(cameraShape, query = True, worldCenterOfInterest = True)

		return [ position[0], 0, position[2] ]

def _fields_hrc_grp():
	if cmds.objExists('Shot_FX_hrc'):
		if not cmds.objExists('FIELDS_hrc'):
			fields_hrc_grp = cmds.group(name = 'FIELDS_hrc', empty = True, parent = 'Shot_FX_hrc')

			return fields_hrc_grp
		else:
			return 'FIELDS_hrc'
	else:
		mel.eval('warning "%s";\n' % "Couldn't find Shot_FX_hrc in this shot, please make sure that exist!")

		return None

def _fx_modelPanel_cleanUp(modelPanel = ''):
	if cmds.modelPanel(modelPanel, exists = True):
		cmds.modelEditor(
						 modelPanel,
						 edit = True,
						 allObjects = False,
						 polymeshes = True,
						 manipulators = True,
						 dynamics = True,
						 fluids = True,
						 nParticles = True,
						 nRigids = True,
						 pluginShapes = True,
						 pluginObjects = ['gpuCacheDisplayFilter', True],
						 displayAppearance = 'smoothShaded',
						)

		for x in cmds.ls(type = 'mesh'):
			smoothnessPreview = cmds.displaySmoothness(x, polygonObject = True, q = True)
			if smoothnessPreview == [3]:
				cmds.displaySmoothness(x, polygonObject = 1)

def _ls(nodeType = '', topTransform = True, stringFilter = '', unlockNode = False):
	if nodeType:
		nodes = cmds.ls(type = nodeType)
		if nodes:
			final_nodes = []
			for each in nodes:
				each = cmds.ls(each, long = True)[0]
				top_transform = cmds.listRelatives(each, parent = True, fullPath = True) if topTransform else None
				final_node = top_transform[0] if top_transform else each

				if unlockNode:
					try:    cmds.lockNode(final_node, lock = False)
					except: mel.eval('warning "Failed to unlock %s, skipping...";' % final_node)

				if stringFilter:
					if stringFilter in final_node:
						if final_node not in final_nodes:
							final_nodes.append(final_node)
				else:
					if final_node not in final_nodes:
						final_nodes.append(final_node)

			return final_nodes

		return []

def removeOceanSetup(step = ''):
	"""
	Function to blow away anything related to an ocean setup.
	USE WITH CARE
	"""
	## Setup the progress bar
	inprogressBar = pbui.ProgressBarUI(title = 'DELETE FX Ocean Setup:')
	inprogressBar.show()
	inprogressBar.updateProgress(percent = 20, doingWhat = 'Deleting setup')
	toDel = ['OCEAN_hrc', 'BOAT_OceanLocators_hrc', 'ocean_dispShader', 'ocean_animShader', 'ocean_srf', 'oceanPreviewPlane_prv',
			 'wakesOnOfMultiDiv', 'wakesOnOffMultiDiv', 'FLUID_EMITTERS_hrc', 'nPARTICLE_EMITTERS_hrc']

	attrsToDel = ['startFrame', 'buoyancy', 'waterDamping', 'airDamping', 'objectHeight', 'gravity', 'sceneScale', 'boatLength', 'boatWidth', 'roll', 'pitch', 'oceanYDamp']

	if step == 'Rig':
		debug(app = self.app, method = 'Main_UI', message= 'RIG CONTEXT STEP, DELETING WORLDCTRL ATTRS NOW', verbose = False)
		for eachAttr in attrsToDel:
			try:cmds.deleteAttr('world_ctrl.%s' % eachAttr)
			except:pass

	inprogressBar.updateProgress(percent = 40, doingWhat = 'Deleting nurbs intersection planes...')
	## Clean the _NurbsIntersect_geo out of the scene
	for each in cmds.ls('*_NurbsIntersect_geo'):
		cmds.delete(each)

	x = 12
	for each in toDel:
		try:
			inprogressBar.updateProgress(percent = x, doingWhat = 'Deleting %s' % each)
			cmds.delete(each)
			x = x + 5
		except ValueError:  ## each doesn't exist
			pass

	## Clean up the shot_FX_hrc group
	try:
		cmds.delete('Shot_FX_hrc')
		#if not cmds.listRelatives('Shot_FX_hrc', children = True):
			#inprogressBar.updateProgress(percent = 50, doingWhat = 'Deleting Shot_FX_hrc group...')
			#cmds.delete('Shot_FX_hrc')
	except: ## grp doesn't exist
		pass

	##  Now clean up the expressions
	inprogressBar.updateProgress(percent = 60, doingWhat = 'Deleting expressions...')
	for eachExp in cmds.ls(type = 'expression'):
		if 'oceanLock' in eachExp:
			cmds.delete(eachExp)
		elif 'IntersectionPlane' in eachExp:
			cmds.delete(eachExp)
		else:
			pass

	## Now clean the shaders out
	inprogressBar.updateProgress(percent = 75, doingWhat = 'Deleting oceanShaders...')
	for each in cmds.ls(type = 'shadingEngine'):
		if 'ocean' in each:
			try:
				cmds.delete(each)
			except:
				pass

	## Delete any fluid emitters in the scene
	inprogressBar.updateProgress(percent = 80, doingWhat = 'Deleting fluidEmitters...')
	for each in cmds.ls(type = 'fluidEmitter'):
		try:
			cmds.delete(each)
		except:
			pass

	## Delete any fluidTexture3D
	inprogressBar.updateProgress(percent = 85, doingWhat = 'Deleting fluidEmitters...')
	for each in cmds.ls(type = 'fluidTexture3D'):
		try:
			cmds.delete(each)
		except:
			pass

	inprogressBar.updateProgress(percent = 90, doingWhat = 'Deleting fluidEmitters...')
	try:    cmds.delete('FX_CACHES_hrc')
	except: pass

	## Delete any intersection curves:
	for eachCrv in cmds.ls(type = 'curveVarGroup'):
		if '_Intersect' in eachCrv:
			cmds.delete(eachCrv)

	###############################################
	##### RIGGING
	## This is for RIGGING tests
	inprogressBar.updateProgress(percent = 95, doingWhat = 'Rigging clenaup...')
	try:
		## Delete the ocean resolution expression
		if cmds.objExists('oceanRes_exp'):
			cmds.delete('oceanRes_exp')

		for each in cmds.ls('*stern_guide_loc*'):
			cmds.setAttr('%s.translateY', 0)

		for each in cmds.ls('*bow_guide_loc*'):
			cmds.setAttr('%s.translateY', 0)

		for each in cmds.ls('*port_guide_loc*'):
			cmds.setAttr('%s.translateY', 0)

		for each in cmds.ls('*starboard_guide_loc*'):
			cmds.setAttr('%s.translateY', 0)
	except:
		pass
	if cmds.objExists('world_ctrl'):
		cmds.setAttr('world_ctrl.translateX', 0)
		cmds.setAttr('world_ctrl.translateZ', 0)

	mel.eval("MLdeleteUnused();")
	inprogressBar.updateProgress(percent = 100, doingWhat = 'Complete.')
	inprogressBar.close()

class BubbleCreator(object):

	BUBBLE_GROUP_NAME           = 'bubbles_GRP'

	BUBBLE_CTRL_NAME            = 'bubbles_ctrl'
	BUBBLE_CTRL_OFFSET_GRP      = 'bubbles_offset_grp'
	LOCATOR_NAME                = 'bubbles_locator'

	BUBBLE_NAME                 = 'bubbles_particle'
	BUBBLE_EMITTER_NAME         = 'bubbles_emitter'
	BUBBLE_PRESET_ATTRS         = {'inheritFactor':0.2, 'conserve':0.9, 'lifespanMode':3, 'particleRenderType':7}
	BUBBLE_ATTR_PP              = {'radiusPP':[(0, 0), (0.08, 0.355), (0.62, 0.355), (1, 0)], 'radius':None}

	BUBBLEBURST_NAME            = 'bubbleBursts_particle'
	BUBBLEBURST_EMITTER_NAME    = 'bubbleBursts_emitter'
	BUBBLEBURST_PRESET_ATTRS    = {'forcesInWorld':0, 'conserve':0.9, 'lifespanMode':3, 'particleRenderType':7}
	BUBBLEBURST_ATTR_PP         = {'radiusPP':None}

	UNIFORM_FIELD_NAME          = 'bubbles_uniform'
	TURBULENCE_FIELD_NAME       = 'bubbles_turbulence'
	RADIAL_FIELD_NAME           = 'bubbles_radial'

	BUBBLE_SHADER_NAME          = 'bubbles_shader'
	BUBBLE_SHADER_SG_NAME       = 'bubbles_shaderSG'
	BUBBLE_SHADER_RAMP_NAME     = 'bubbles_ramp'
	BUBBLE_SHADER_SI_NAME       = 'bubbles_samplerInfo'

	def __init__(self, prefix, mesh):

		## Create ctrl for bubbles
		self.bubbleCtrlShape = cmds.createNode( 'implicitSphere', name = '%s_%sShape' % (prefix, self.BUBBLE_CTRL_NAME) )
		self.bubbleCtrl = cmds.listRelatives(self.bubbleCtrlShape, parent = True, fullPath = True)
		self.bubbleCtrl = cmds.rename( self.bubbleCtrl, '%s_%s' % (prefix, self.BUBBLE_CTRL_NAME) )
		self.bubbleCtrlGroup = cmds.group( self.bubbleCtrl, name = '%s_%s' % (prefix, self.BUBBLE_CTRL_OFFSET_GRP) )

		## Space locator with speed attribute
		self.speedLocator = cmds.spaceLocator( name = '%s_%s' % (prefix, self.LOCATOR_NAME) )[0]
		cmds.addAttr(self.speedLocator, longName = 'speed', attributeType = 'double')
		cmds.setAttr('%s.speed' % self.speedLocator, keyable = True)

		###################################################################################################

		## Creation
		self.bubble, self.bubbleShape = cmds.particle(name = '%s_%s' % (prefix, self.BUBBLE_NAME) )

		## Set presets
		for attr, val in self.BUBBLE_PRESET_ATTRS.iteritems():
			cmds.setAttr('%s.%s' % (self.bubbleShape, attr), val)

		## Create necessary PP attr and hook-up necsesary ramp info
		arrayMap, ramp = self.addAttrPP(particleShapeName = self.bubbleShape, attrPP = self.BUBBLE_ATTR_PP)

		## Emitter
		cmds.select(mesh, replace = True)
		self.bubbleEmitter = cmds.emitter(type = 'surface', rate = 100, sro = 0, nuv = 0, cye = 'none', cyi = 1, spd = 1, srn = 0, nsp = 1, tsp = 0, mxd = 0, mnd = 0, dx = 1, dy = 0, dz = 0, sp = 0)[1]
		# elif _TYPE == 'volume':
		#   cmds.select(clear = True)
		#   self.bubbleEmitter = cmds.emitter(pos = [0, 0, 0], type = 'volume', r = 100, sro = 0, nuv = 0, cye = 'none', cyi = 1, spd = 1, srn = 0, nsp = 1, tsp = 0, mxd = 0, mnd = 0, dx = 0, dy = 0, dz = 0, sp = 0, vsh = 'sphere', vof = [0, 0, 0], vsw = 360, tsr = 0.5, afc = 1, afx = 1, arx = 0, alx = 0, rnd = 0, drs = 0, ssz = 0)[0]
		#   cmds.setAttr('%s.scaleX' % self.bubbleEmitter, 0.2)
		#   cmds.setAttr('%s.scaleY' % self.bubbleEmitter, 0.2)
		#   cmds.setAttr('%s.scaleZ' % self.bubbleEmitter, 0.2)

		self.bubbleEmitter = cmds.rename(self.bubbleEmitter, '%s_%s' % (prefix, self.BUBBLE_EMITTER_NAME) )
		cmds.connectDynamic(self.bubbleShape, emitters = self.bubbleEmitter)

		###################################################################################################

		## Creation
		self.bubbleBurst, self.bubbleBurstShape = cmds.particle(name = '%s_%s' % (prefix, self.BUBBLEBURST_NAME) )

		## Set presets
		for attr, val in self.BUBBLEBURST_PRESET_ATTRS.iteritems():
			cmds.setAttr('%s.%s' % (self.bubbleBurstShape, attr), val)

		## Create necessary PP attr and hook-up necsesary ramp info
		self.addAttrPP(particleShapeName = self.bubbleBurstShape, attrPP = self.BUBBLEBURST_ATTR_PP)

		cmds.select(self.bubbleShape, replace = True)
		self.bubbleBurstEmitter = cmds.emitter(type = 'omni', rate = 100, sro = 0, nuv = 0, cye = 'none', cyi = 1, spd = 1, srn = 0, nsp = 1, tsp = 0, mxd = 0, mnd = 0, dx = 1, dy = 0, dz = 0, sp = 0)[1]
		self.bubbleBurstEmitter = cmds.rename(self.bubbleBurstEmitter, '%s_%s' % (prefix, self.BUBBLEBURST_EMITTER_NAME) )
		cmds.setAttr('%s.speed' % self.bubbleBurstEmitter, 0.4)
		cmds.addPP(self.bubbleBurstEmitter, attribute = 'rate')
		cmds.connectDynamic(self.bubbleBurstShape, emitters = self.bubbleBurstEmitter)

		###################################################################################################

		## Create necessary fields
		## Uniform Field
		self.uniformField = cmds.uniform(name = '%s_%s' % (prefix, self.UNIFORM_FIELD_NAME), pos = [0, 0, 0], m = 2.5, att = 0, dx = 0, dy = 2, dz = 0, mxd = -1, vsh = 'none', vex = 0, vof = [0, 0, 0], vsw = 360, tsr = 0.5)[0]

		## Turbulence Field
		self.turbulenceField = cmds.turbulence(name = '%s_%s' % (prefix, self.TURBULENCE_FIELD_NAME), pos = [0, 0, 0], m = 3, att = 0, f = 10, phaseX = 0, phaseY = 0, phaseZ = 0, noiseLevel = 0, noiseRatio = 0.707, mxd = -1, vsh = 'none', vex = 0, vof = [0, 0, 0], vsw = 360, tsr = 0.5)[0]

		## Radial Field
		self.radialField = cmds.radial(name = '%s_%s' % (prefix, self.RADIAL_FIELD_NAME), pos = [0, 0, 0], m = 2, att = 1, typ = 0, mxd = 20, vsh = 'sphere', vex = 0, vof = [0, 0, 0], vsw = 360, tsr = 0.5)[0]

		## Make necessary connections
		cmds.connectDynamic(self.bubbleShape, fields = self.uniformField)
		cmds.connectDynamic(self.bubbleBurstShape, fields = self.uniformField)
		cmds.connectDynamic(self.bubbleShape, fields = self.turbulenceField)
		cmds.connectDynamic(self.bubbleBurstShape, fields = self.turbulenceField)
		cmds.connectDynamic(self.bubbleShape, fields = self.radialField)
		cmds.connectDynamic(self.bubbleBurstShape, fields = self.radialField)

		###################################################################################################

		self.bubbleGroup = cmds.group(self.bubbleCtrlGroup, self.bubble, self.bubbleBurst, self.uniformField, self.turbulenceField, self.radialField, self.bubbleEmitter, self.bubbleBurstEmitter, self.speedLocator, name = '%s_%s' % (prefix, self.BUBBLE_GROUP_NAME) )
		cmds.parent(self.bubbleEmitter, self.speedLocator)
		cmds.pointConstraint(self.bubbleCtrl, self.speedLocator, maintainOffset = False)
		cmds.pointConstraint(cmds.listRelatives(mesh, parent = True, fullPath = True)[0], self.bubbleCtrlGroup, maintainOffset = False)
		cmds.setAttr('%s.scaleX' % self.radialField, 3.165)
		cmds.setAttr('%s.scaleY' % self.radialField, 3.165)
		cmds.setAttr('%s.scaleZ' % self.radialField, 3.165)

		attr = {'longName':'speed', 'niceName':' ', 'attributeType':'enum', 'enumName':'Speed:', 'keyable':False}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'minSpeed', 'attributeType':'double', 'defaultValue':0.01, 'min':0}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'maxSpeed', 'attributeType':'double', 'defaultValue':20}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'useSpeed', 'niceName':'Use Speed', 'attributeType':'bool', 'defaultValue':0}
		self.add_custom_attrs(self.bubbleCtrl, **attr)

		attr = {'longName':'emitters', 'niceName':' ', 'attributeType':'enum', 'enumName':'Emitters:', 'keyable':False}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'rate', 'niceName':'Rate', 'attributeType':'double', 'defaultValue':20, 'min':0}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'splashMaxSpeed', 'niceName':'Splash Max Speed', 'attributeType':'double', 'defaultValue':0.1}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'directionalSpeed', 'niceName':'Directional Speed', 'attributeType':'double', 'defaultValue':0}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'randomDirection', 'niceName':'Random Direction', 'attributeType':'double', 'defaultValue':0}
		self.add_custom_attrs(self.bubbleCtrl, **attr)

		attr = {'longName':'burstAttr', 'niceName':' ', 'attributeType':'enum', 'enumName':'Burst Attrs:', 'keyable':False}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'popVelocity', 'niceName':'Pop Velocity', 'attributeType':'double', 'defaultValue':1}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'burstSizeMin', 'niceName':'Size Min', 'attributeType':'double', 'defaultValue':0.01, 'min':0}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'burstSizeMax', 'niceName':'Size Max', 'attributeType':'double', 'defaultValue':0.1, 'min':0}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'burstLifespanMin', 'niceName':'Lifespan Min', 'attributeType':'double', 'defaultValue':1, 'min':-1}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'burstLifespanMax', 'niceName':'Lifespan Max', 'attributeType':'double', 'defaultValue':2, 'min':-1}
		self.add_custom_attrs(self.bubbleCtrl, **attr)

		attr = {'longName':'bubbleAttr', 'niceName':' ', 'attributeType':'enum', 'enumName':'Bubble Attrs', 'keyable':False}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'bubbleSizeMin', 'niceName':'Size Min', 'attributeType':'double', 'defaultValue':0.2, 'min':0}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'bubbleSizeMax', 'niceName':'Size Max', 'attributeType':'double', 'defaultValue':0.4, 'min':0}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'lifespanMin', 'niceName':'Lifespan Min', 'attributeType':'double', 'defaultValue':2, 'min':-1}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'lifespanMax', 'niceName':'Lifespan Max', 'attributeType':'double', 'defaultValue':4, 'min':-1}
		self.add_custom_attrs(self.bubbleCtrl, **attr)

		attr = {'longName':'killField', 'niceName':' ', 'attributeType':'enum', 'enumName':'Kill Field:', 'keyable':False}
		self.add_custom_attrs(self.bubbleCtrl, **attr)
		attr = {'longName':'killHeight', 'niceName':'Kill Height', 'attributeType':'double', 'defaultValue':-0.1}
		self.add_custom_attrs(self.bubbleCtrl, **attr)

		###################################################################################################

		## Locator speed expression
		expStringList = [
						'float $time;',
						'float $trx;',
						'float $try;',
						'float $trz;',
						'float $dx = %s.translateX - $trx;' % self.speedLocator,
						'float $dy = %s.translateY - $try;' % self.speedLocator,
						'float $dz = %s.translateZ - $trz;' % self.speedLocator,
						'float $d = sqrt( ($dx * $dx) + ($dy * $dy) + ($dz * $dz) );',
						'%s.speed = abs( $d / ( time - ($time + 0.001) ) );' % self.speedLocator,
						'$trx = %s.translateX;' % self.speedLocator,
						'$try = %s.translateY;' % self.speedLocator,
						'$trz = %s.translateZ;' % self.speedLocator,
						'$time = time;'
						]
		expString = self.processExpressionString(expStringList)
		cmds.expression(self.speedLocator, string = expString)

		## Bubbles Creation Expression
		expStringList = [
						'%s.lifespanPP = rand(%s.lifespanMin, %s.lifespanMax);' %(self.bubbleShape, self.bubbleCtrl, self.bubbleCtrl)
						]
		expString = self.processExpressionString(expStringList)
		cmds.dynExpression(self.bubbleShape, string = expString, creation = True)

		## Bubbles Runtime After Dynamics
		expStringList = [
						'vector $vel = %s.velocity;' % self.bubbleShape,
						'vector $kill = %s.position;' % self.bubbleShape,
						'float $popVel = %s.popVelocity;' % self.bubbleCtrl,
						'float $age = %s.age;' % self.bubbleShape,
						'',
						'if ( $kill.y > %s.killHeight )' % self.bubbleCtrl,
						'{',
						'   %s.lifespanPP = 0;' % self.bubbleShape,
						'}',
						'',
						'if ($vel.y >=  $popVel)',
						'{',
						'   %s.lifespanPP = 0;' % self.bubbleShape,
						'   %s.%s_emitterRatePP = 100;' % (self.bubbleShape, '_'.join(self.bubbleBurst.split('_')[0:-1])),
						'}',
						]
		expString = self.processExpressionString(expStringList)
		cmds.dynExpression(self.bubbleShape, string = expString, runtimeAfterDynamics = True)

		## Bubble Bursts Creation Expression
		expStringList = [
						'%s.lifespanPP = rand(%s.burstLifespanMin, %s.burstLifespanMax);' %(self.bubbleBurstShape, self.bubbleCtrl, self.bubbleCtrl),
						'%s.radiusPP = rand(%s.burstSizeMin, %s.burstSizeMax)' % (self.bubbleBurstShape, self.bubbleCtrl, self.bubbleCtrl),
						]
		expString = self.processExpressionString(expStringList)
		cmds.dynExpression(self.bubbleBurstShape, string = expString, creation = True)

		## Bubble Bursts Runtime After Dynamics Expression
		expStringList = [
						'vector $kill = %s.position;' % self.bubbleBurstShape,
						'',
						'if ($kill.y > %s.killHeight)' % self.bubbleCtrl,
						'{',
						'   %s.lifespanPP = 0;' % self.bubbleBurstShape,
						'}',
						]
		expString = self.processExpressionString(expStringList)
		cmds.dynExpression(self.bubbleBurstShape, string = expString, runtimeAfterDynamics = True)

		## Expression for Turbulence Field
		expStringList = [
						'%s.phaseX = time;' % self.turbulenceField,
						'%s.phaseY = time;' % self.turbulenceField,
						'%s.phaseZ = time;' % self.turbulenceField,
						]
		expString = self.processExpressionString(expStringList)
		cmds.expression(self.turbulenceField, string = expString)

		## Expression for Bubble Emitter
		expStringList = [
						'float $minSpeed = %s.minSpeed;' % self.bubbleCtrl,
						'float $maxSpeed = %s.maxSpeed;' % self.bubbleCtrl,
						'float $speed = %s.speed;' % self.speedLocator,
						'float $curve = smoothstep($minSpeed, $maxSpeed, $speed);',
						'float $rateMuliplier = %s.rate;' % self.bubbleCtrl,
						'float $splashMaxSpeed = %s.splashMaxSpeed;' % self.bubbleCtrl,
						'',
						'if (%s.useSpeed == 1)' % self.bubbleCtrl,
						'{',
						'   %s.rate = $rateMuliplier * $curve;' % self.bubbleEmitter,
						'',
						'   float $emitterSpeed = $splashMaxSpeed * $curve;',
						'   if ($emitterSpeed == 0)',
						'   {',
						'       $emitterSpeed = 0.1;',
						'   }',
						'   %s.awayFromCenter = $emitterSpeed;' % self.bubbleEmitter,
						'}',
						'else',
						'{',
						'   %s.rate = $rateMuliplier;' % self.bubbleEmitter,
						'   %s.awayFromCenter = $splashMaxSpeed;' % self.bubbleEmitter,
						'}',
						'%s.alongAxis = %s.directionalSpeed;' % (self.bubbleEmitter, self.bubbleCtrl),
						'%s.randomDirection = %s.randomDirection;' % (self.bubbleEmitter, self.bubbleCtrl),
						]
		expString = self.processExpressionString(expStringList)
		cmds.expression(self.bubbleEmitter, string = expString)

		###################################################################################################

		## Finalizing stuffs
		cmds.connectAttr('%s.bubbleSizeMin' % self.bubbleCtrl, '%s.minValue' % arrayMap)
		cmds.connectAttr('%s.bubbleSizeMax' % self.bubbleCtrl, '%s.maxValue' % arrayMap)

		###################################################################################################

		## Assigning shader
		self.bubbleShader(particleShapeName = [self.bubbleShape, self.bubbleBurstShape])

		###################################################################################################

	def processExpressionString(self, expStringList):
		string = ''
		for eachLine in expStringList:
			string = string + eachLine + '\n'

		return string

	def addAttrPP(self, particleShapeName, attrPP):
		for attr, type in attrPP.iteritems():
			pp_Name =  '%s.%s' %(particleShapeName, attr)

			if not cmds.objExists(pp_Name):
				if attr.endswith('PP'):
					cmds.addAttr(particleShapeName, longName = attr, dataType = "doubleArray")
				else:
					cmds.addAttr(particleShapeName, internalSet = True, longName = attr, attributeType = 'float', min = 0, max = 10, defaultValue = 0.5)

			# Create necessary custom ramp
			if type:
				pp_Connection = cmds.listConnections(pp_Name)
				if not pp_Connection:
					arrayMap = cmds.arrayMapper(target = particleShapeName, destAttr = attr, inputV = 'ageNormalized', type = 'ramp')[0]
					ramp = cmds.listConnections('%s.computeNode' % arrayMap)[0]
					# By default maya provide 3 colorEntryList per ramp, delete most of it first
					for i in range(1, 3):
						cmds.evalDeferred('cmds.removeMultiInstance("%s.colorEntryList[%d]")' %(ramp, i) )
					for i, entry in enumerate(type):
						cmds.evalDeferred( 'cmds.setAttr("%s.colorEntryList[%d].position", %s)' %(ramp, i, entry[0]) )
						cmds.evalDeferred( 'cmds.setAttr("%s.colorEntryList[%d].color", %s, %s, %s, type = "double3")' %(ramp, i, entry[1], entry[1], entry[1]) )

				return [arrayMap, ramp]

	def add_custom_attrs(self, objectName = '', **kwargs):

		fullName = '%s.%s' %(objectName, kwargs['longName'])

		if not cmds.objExists(fullName):
			cmds.addAttr(objectName, **kwargs)
			cmds.setAttr(fullName, keyable = True)

			if 'keyable' in kwargs:
				if kwargs['keyable'] == False:
					cmds.setAttr(fullName, channelBox = True)

	def bubbleShader(self, particleShapeName = []):
		if not cmds.objExists(self.BUBBLE_SHADER_NAME):
			anisotropic = cmds.shadingNode('anisotropic', asShader = True, name = self.BUBBLE_SHADER_NAME)
		if not cmds.objExists(self.BUBBLE_SHADER_SG_NAME):
			anisotropicSG = cmds.sets(renderable = True, noSurfaceShader = True, empty = True, name = self.BUBBLE_SHADER_SG_NAME)
		if not cmds.objExists(self.BUBBLE_SHADER_RAMP_NAME):
			ramp = cmds.createNode('ramp', name = self.BUBBLE_SHADER_RAMP_NAME)
		if not cmds.objExists(self.BUBBLE_SHADER_SI_NAME):
			samplerInfo = cmds.createNode('samplerInfo', name = self.BUBBLE_SHADER_SI_NAME)

		if not cmds.isConnected('%s.facingRatio' % self.BUBBLE_SHADER_SI_NAME, '%s.uCoord' % self.BUBBLE_SHADER_RAMP_NAME):
			cmds.connectAttr('%s.facingRatio' % self.BUBBLE_SHADER_SI_NAME, '%s.uCoord' % self.BUBBLE_SHADER_RAMP_NAME, force = True)
		if not cmds.isConnected('%s.facingRatio' % self.BUBBLE_SHADER_SI_NAME, '%s.vCoord' % self.BUBBLE_SHADER_RAMP_NAME):
			cmds.connectAttr('%s.facingRatio' % self.BUBBLE_SHADER_SI_NAME, '%s.vCoord' % self.BUBBLE_SHADER_RAMP_NAME, force = True)
		if not cmds.isConnected('%s.outColor' % self.BUBBLE_SHADER_RAMP_NAME, '%s.incandescence' % self.BUBBLE_SHADER_NAME):
			cmds.connectAttr('%s.outColor' % self.BUBBLE_SHADER_RAMP_NAME, '%s.incandescence' % self.BUBBLE_SHADER_NAME, force = True)
		if not cmds.isConnected('%s.outColor' % self.BUBBLE_SHADER_NAME, '%s.surfaceShader' % self.BUBBLE_SHADER_SG_NAME):
			cmds.connectAttr('%s.outColor' % self.BUBBLE_SHADER_NAME, '%s.surfaceShader' % self.BUBBLE_SHADER_SG_NAME, force = True)

		cmds.setAttr("%s.colorEntryList[0].color" % self.BUBBLE_SHADER_RAMP_NAME, 0, 0, 0, type = 'double3')
		cmds.setAttr("%s.colorEntryList[0].position" % self.BUBBLE_SHADER_RAMP_NAME, 0.96)
		cmds.setAttr("%s.colorEntryList[1].color" % self.BUBBLE_SHADER_RAMP_NAME, 0.108, 0.108, 0.108, type = 'double3')
		cmds.setAttr("%s.colorEntryList[1].position" % self.BUBBLE_SHADER_RAMP_NAME, 0.025)
		cmds.setAttr("%s.colorEntryList[2].color" % self.BUBBLE_SHADER_RAMP_NAME, 1, 1, 1, type = 'double3')
		cmds.setAttr("%s.colorEntryList[2].position" % self.BUBBLE_SHADER_RAMP_NAME, 0)
		cmds.setAttr("%s.color" % self.BUBBLE_SHADER_NAME, 0.5, 0.5, 0.5, type = 'double3')
		cmds.setAttr("%s.transparency" % self.BUBBLE_SHADER_NAME, 1, 1, 1, type = 'double3')
		cmds.setAttr("%s.ambientColor" % self.BUBBLE_SHADER_NAME, 0, 0, 0, type = 'double3')
		cmds.setAttr("%s.diffuse" % self.BUBBLE_SHADER_NAME, 0.8)
		cmds.setAttr("%s.angle" % self.BUBBLE_SHADER_NAME, 301.538)
		cmds.setAttr("%s.spreadX" % self.BUBBLE_SHADER_NAME, 88.9)
		cmds.setAttr("%s.spreadY" % self.BUBBLE_SHADER_NAME, 62.431)
		cmds.setAttr("%s.roughness" % self.BUBBLE_SHADER_NAME, 1)
		cmds.setAttr("%s.fresnelRefractiveIndex" % self.BUBBLE_SHADER_NAME, 20)
		cmds.setAttr("%s.specularColor" % self.BUBBLE_SHADER_NAME, 0.41, 0.41, 0.41, type = 'double3')
		cmds.setAttr("%s.reflectedColor" % self.BUBBLE_SHADER_NAME, 0, 0, 0, type = 'double3')
		cmds.setAttr("%s.anisotropicReflectivity" % self.BUBBLE_SHADER_NAME, 1)

		if cmds.objExists(self.BUBBLE_SHADER_NAME) and cmds.objExists(self.BUBBLE_SHADER_SG_NAME):
			for each in particleShapeName:
				cmds.sets(each, edit = True, forceElement = self.BUBBLE_SHADER_SG_NAME)

def bubbleSetup():
	selection = cmds.ls(selection = True)
	if selection:
		mesh = cmds.filterExpand(selection, sm = 12, fullPath = True)
		if mesh:
			for each in mesh:
				transform = each.split('|')[-2]
				shape = each.split('|')[-1]
				BubbleCreator(transform, shape)

class splashRigger(object):

	NUCLEUS_NAME = 'fx_nucleus'
	TEXTURE_PATH = 'I:/lsapipeline/fx/sprites/water/water_gloop_3.tga'
	PRESET_PATH = 'I:/lsapipeline/fx/presets/nparticle/spriteSplash.mel'

	def __init__(self):

		for i in itertools.count():
			self.ANIMATABLE_GRP = 'spriteSpray_GRP_%03d' % i
			self.SPEED_LOCATOR_NAME = 'spriteSpray_locator_%03d' % i
			self.PARTICLE_NAME = 'spriteSpray_nParticle_%03d' % i
			self.EMITTER_NAME = 'spriteSpray_emitter_%03d' % i

			if not cmds.objExists(self.ANIMATABLE_GRP) and not cmds.objExists(self.SPEED_LOCATOR_NAME) and not cmds.objExists(self.PARTICLE_NAME) and not cmds.objExists(self.EMITTER_NAME):
				self.ANIMATABLE_GRP = 'spriteSpray_GRP_%03d' % i
				self.SPEED_LOCATOR_NAME = 'spriteSpray_locator_%03d' % i
				self.PARTICLE_NAME = 'spriteSpray_nParticle_%03d' % i
				self.EMITTER_NAME = 'spriteSpray_emitter_%03d' % i

				break

		## Creation of whatever teh shits it needs man
		self.nParticle, self.nParticleShape = self.nParticle_(name = self.PARTICLE_NAME)
		self.locator = cmds.spaceLocator(name = self.SPEED_LOCATOR_NAME)[0]
		cmds.select(clear = True)
		self.emitter = cmds.emitter(name = self.EMITTER_NAME, type = 'volume', scaleRateByObjectSize = False, directionX = 0, volumeShape = 'sphere')[0]

		self.nucleus = self.NUCLEUS_NAME
		if not cmds.objExists(self.nucleus):
			self.nucleus = self.nucleus_(name = self.nucleus)

		## Connect nParticle to nucleus
		cmds.select(self.nParticleShape, replace = True)
		mel.eval('assignNSolver "%s";' % self.nucleus)

		## Build shader for the sprite
		self.spriteSG = self.spriteShader(name = 'fx_sprite')
		cmds.sets(self.nParticleShape, edit = True, forceElement = self.spriteSG)

		## Grouping stuffs
		self.topGroup = cmds.group(self.locator, self.nParticle, name = self.ANIMATABLE_GRP)
		cmds.parent(self.emitter, self.locator)

		## Locking/Hiding attrs for various objects...
		toLockAndHide = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ']
		[cmds.setAttr('%s.%s' %(self.topGroup, each), lock = True, keyable = False, channelBox = False) for each in toLockAndHide]
		[cmds.setAttr('%s.%s' %(self.nParticle, each), lock = True, keyable = False, channelBox = False) for each in toLockAndHide]
		toScale = ['localScaleX', 'localScaleY', 'localScaleZ']
		[cmds.setAttr('%s.%s' %(self.locator, each), 10) for each in toScale]

		# ## Getting the final long name for each objects
		# self.nParticle = cmds.ls(self.nParticle, long = True)[0]
		# self.nParticleShape = cmds.ls(self.nParticleShape, long = True)[0]
		# self.locator = cmds.ls(self.locator, long = True)[0]
		# self.emitter = cmds.ls(self.emitter, long = True)[0]

		## SPEED
		attr = {'longName':'speedDisplay', 'niceName':' ', 'attributeType':'enum', 'enumName':'Speed:', 'keyable':False}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'speed', 'attributeType':'double', 'keyable':False}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'minSpeed', 'attributeType':'double', 'defaultValue':5, 'min':0}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'maxSpeed', 'attributeType':'double', 'defaultValue':20}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'useSpeed', 'niceName':'Use Speed', 'attributeType':'bool', 'defaultValue':1}
		self.add_custom_attrs(self.locator, **attr)
		## EMITTERS
		attr = {'longName':'sideEmitters', 'niceName':' ', 'attributeType':'enum', 'enumName':'Emitters:', 'keyable':False}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'rateMultiplier', 'niceName':'Rate * ', 'attributeType':'double', 'defaultValue':2250, 'min':0}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'splashMaxSpeed', 'niceName':'Speed * ', 'attributeType':'double', 'defaultValue':2.25, 'min':1}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'randomSpeed', 'niceName':'Random Speed', 'attributeType':'double', 'defaultValue':1, 'min':0}
		self.add_custom_attrs(self.locator, **attr)
		## PER PARTICLE CREATION
		attr = {'longName':'ppCreation', 'niceName':' ', 'attributeType':'enum', 'enumName':'PP Creation:', 'keyable':False}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'lifespanMin', 'attributeType':'double', 'defaultValue':1}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'lifespanMax', 'attributeType':'double', 'defaultValue':1.5}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'twistAngleMin', 'attributeType':'double', 'defaultValue':0, 'min':0, 'max':360}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'twistAngleMax', 'attributeType':'double', 'defaultValue':360, 'min':0, 'max':360}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'twistSpeedMin', 'attributeType':'double', 'defaultValue':-4}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'twistSpeedMax', 'attributeType':'double', 'defaultValue':30}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'spriteStartSizeMin', 'attributeType':'double', 'defaultValue':0.15, 'min':0}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'spriteStartSizeMax', 'attributeType':'double', 'defaultValue':0.46, 'min':0}
		self.add_custom_attrs(self.locator, **attr)
		## NPARTICLE
		attr = {'longName':'nParticleSprite', 'niceName':' ', 'attributeType':'enum', 'enumName':'nParticle:', 'keyable':False}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'inheritFactorSprite', 'attributeType':'double', 'defaultValue':0.6, 'min':0, 'max':1}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'conserveSprite', 'attributeType':'double', 'defaultValue':1, 'min':0, 'max':1}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'dragSprite', 'attributeType':'double', 'defaultValue':0.01, 'min':0, 'max':1}
		self.add_custom_attrs(self.locator, **attr)
		attr = {'longName':'dampSprite', 'attributeType':'double', 'defaultValue':0, 'min':0, 'max':1}
		self.add_custom_attrs(self.locator, **attr)

		## Base setups
		self._doBaseParticleShapeSetup(particleShapeName = self.nParticleShape, presetName = self.PRESET_PATH)
		## Connect the emitter to the particles
		cmds.connectDynamic(self.nParticleShape, em = self.emitter)
		## Make sure visibility is connected to isDynamic so hidden means won't simulate
		cmds.connectAttr('%s.visibility' % self.nParticle, '%s.isDynamic' % self.nParticleShape)

		## Expression
		self._build_nParticleExpressions(particleShapeName = self.nParticleShape, animatable = self.locator)
		self._buildSpeedExpression(speedObject = self.locator)
		self._buildEmitterExpression(speedObject = self.locator, emitter = self.emitter, animatable = self.locator)

	def nucleus_(self, name = ''):
		nucleus = cmds.createNode('nucleus')
		if name:
			nucleus = cmds.rename(nucleus, name)
		cmds.connectAttr('time1.outTime', '%s.currentTime' % nucleus)

		return nucleus

	def nParticle_(self, name = ''):
		nParticleShape = eval('cmds.createNode("nParticle")')
		nParticleTransform = cmds.listRelatives(nParticleShape, parent = True, fullPath = False)[0]
		if name:
			nParticleTransform = cmds.rename(nParticleTransform, name)
			nParticleShape = cmds.rename(cmds.listRelatives(nParticleTransform, shapes = True, fullPath = False)[0], '%sShape' % nParticleTransform)

		mel.eval('changeNParticleInput "%s" "radiusScaleInput" 1' % nParticleShape)
		mel.eval('changeNParticleInput "%s" "opacityScaleInput" 1' % nParticleShape)
		mel.eval('changeNParticleInput "%s" "colorInput" 1' % nParticleShape)

		# add lifespan and lifespanPP
		cmds.addAttr(nParticleShape, longName = 'lifespan', attributeType = 'double')
		cmds.addAttr(nParticleShape, longName = 'lifespanPP', dataType = 'doubleArray')

		return [nParticleTransform, nParticleShape]

	def spriteShader(self, name = ''):
		## Check if shader already exists in scene
		shader = "%s_Shader" % name
		place2dTexture = "%s_place2dTexture" % name
		shadingEngine = '%sSG' % name
		fileNode = "%s_FileIn" % name

		## Create lambert shader
		if not cmds.objExists(shader):
			cmds.shadingNode("lambert", asShader = True, name = shader)

		## Create Shading Group
		if not cmds.objExists(shadingEngine):
			cmds.sets(renderable = True, noSurfaceShader = True, empty = True, name = shadingEngine)

			## Connect SG to Shader
			cmds.connectAttr('%s.outColor' % shader, '%s.surfaceShader' % shadingEngine, force = True)

		## Create file node
		if not cmds.objExists(fileNode):
			cmds.shadingNode ("file", asTexture = True, name = fileNode)

			## Connect file texture to shader
			cmds.connectAttr("%s.outColor" % fileNode, "%s.color" % shader, force = True)
			cmds.connectAttr("%s.outTransparency" % fileNode, "%s.transparency" % shader, force = True)

		## Create place2dTexture
		if not cmds.objExists(place2dTexture):
			cmds.shadingNode("place2dTexture", asUtility = True, name = place2dTexture)

			## Connect up place2d to file node
			cmds.connectAttr("%s.coverage" % place2dTexture, "%s.coverage" % fileNode, force = True)
			cmds.connectAttr("%s.translateFrame" % place2dTexture, "%s.translateFrame" % fileNode, force = True)
			cmds.connectAttr("%s.rotateFrame" % place2dTexture, "%s.rotateFrame" % fileNode, force = True)
			cmds.connectAttr("%s.mirrorU" % place2dTexture, "%s.mirrorU" % fileNode, force = True)
			cmds.connectAttr("%s.mirrorV" % place2dTexture, "%s.mirrorV" % fileNode, force = True)
			cmds.connectAttr("%s.stagger" % place2dTexture, "%s.stagger" % fileNode, force = True)
			cmds.connectAttr("%s.wrapU" % place2dTexture, "%s.wrapU" % fileNode, force = True)
			cmds.connectAttr("%s.wrapV" % place2dTexture, "%s.wrapV" % fileNode, force = True)
			cmds.connectAttr("%s.repeatUV" % place2dTexture, "%s.repeatUV" % fileNode, force = True)
			cmds.connectAttr("%s.offset" % place2dTexture, "%s.offset" % fileNode, force = True)
			cmds.connectAttr("%s.rotateUV" % place2dTexture, "%s.rotateUV" % fileNode, force = True)
			cmds.connectAttr("%s.noiseUV" % place2dTexture, "%s.noiseUV" % fileNode, force = True)
			cmds.connectAttr("%s.vertexUvOne" % place2dTexture, "%s.vertexUvOne" % fileNode, force = True)
			cmds.connectAttr("%s.vertexUvTwo" % place2dTexture, "%s.vertexUvTwo" % fileNode, force = True)
			cmds.connectAttr("%s.vertexUvThree" % place2dTexture, "%s.vertexUvThree" % fileNode, force = True)
			cmds.connectAttr("%s.vertexCameraOne" % place2dTexture, "%s.vertexCameraOne" % fileNode, force = True)
			cmds.connectAttr("%s.outUV" % place2dTexture, "%s.uv" % fileNode, force = True)
			cmds.connectAttr("%s.outUvFilterSize" % place2dTexture, "%s.uvFilterSize" % fileNode, force = True)

		cmds.setAttr('%s.fileTextureName' % fileNode, self.TEXTURE_PATH, type = "string")
		cmds.setAttr('%s.defaultColor' % fileNode, 1, 1, 1, type = "double3")
		cmds.setAttr('%s.colorGain' % fileNode, 1, 1, 1, type = "double3")
		cmds.setAttr('%s.colorOffset' % fileNode, 0, 0, 0, type = "double3")

		## ShadowAttenuation to 0
		cmds.setAttr("%s.shadowAttenuation" % shader, 0)

		return shadingEngine

	def _doBaseParticleShapeSetup(self, particleShapeName = '', presetName = None):
		"""
		Function to set the base particle setups for the nParticleShapes
		@param particleShapeName: The nParticleShapeName
		@param presetName: The name of the nParticle preset in the fx preset folder including the .mel extension
		@type particleShapeName: String
		@type presetName: String
		"""

		# Necessary attrs for adding nParticle presets (Splash)
		mel.eval('addAttr -is true -ln "spriteTwist" -at "float" -min -180 -max 180 -dv 0.0 %s;' % particleShapeName)
		mel.eval('addAttr -is true -ln "spriteScaleX" -dv 1.0 %s;' % particleShapeName)
		mel.eval('addAttr -is true -ln "spriteScaleY" -dv 1.0 %s;' % particleShapeName)
		mel.eval('addAttr -is true -ln "spriteNum" -at long -dv 1 %s;' % particleShapeName)
		mel.eval('addAttr -is true -ln "useLighting" -at bool -dv false %s;' % particleShapeName)

		# Create necessary custom Per Particle Attributes (Splash)
		pp_Attrs = {'opacityPP'         : '',
					'opacityMultiplier' : '',
					'spriteStartSizePP' : '',
					'spriteScaleXPP'    : '',
					'spriteScaleYPP'    : '',
					'spriteTwistPP'     : '',
					'twistSpeedPP'      : '',
					'opacRamp'          : [(0.03, 1), (0.49, 0.258), (1, 0), (0, 0), (0.24, 0.834), (0.875, 0.071)],
					'twistRateOverLife' : [(0, 1), (0.84, 0.041)],
					'scaleOverLifeRamp' : [(0.18, 1), (0, 0.021), (1, 0.849), (0.03, 0.971)]
					}

		for attr, type in pp_Attrs.iteritems():
			pp_Name =  "%s.%s" %(particleShapeName, attr)

			if not cmds.objExists(pp_Name):
				cmds.addAttr(particleShapeName, longName = attr, dataType = "doubleArray")

			# Create necessary custom ramp
			if type:
				pp_Connection = cmds.listConnections(pp_Name)
				if not pp_Connection:
					arrayMap = cmds.arrayMapper(target = particleShapeName, destAttr = attr, inputV = 'ageNormalized', type = 'ramp')[0]
					ramp = cmds.listConnections('%s.computeNode' % arrayMap)[0]
					# By default maya provide 3 colorEntryList per ramp, delete most of it first
					for i in range(1, 3):
						cmds.evalDeferred('cmds.removeMultiInstance("%s.colorEntryList[%d]")' %(ramp, i) )

					for i, entry in enumerate(type):
						cmds.evalDeferred( 'cmds.setAttr("%s.colorEntryList[%d].position", %s)' %(ramp, i, entry[0]) )
						cmds.evalDeferred( 'cmds.setAttr("%s.colorEntryList[%d].color", %s, %s, %s, type = "double3")' %(ramp, i, entry[1], entry[1], entry[1]) )

		## Now attach the desired preset from the FX nParticle preset folder
		if presetName:
			mel.eval('applyPresetToNode "%s" "" "" "%s" 1;' %(particleShapeName, self.PRESET_PATH) )

	def processExpressionString(self, expStringList):
		string = ''
		for eachLine in expStringList:
			string = string + eachLine + '\n'
		return string

	def checkExpressionExists(self, name):
		if cmds.objExists(name):
			cmds.delete(name)

	def _build_nParticleExpressions(self, particleShapeName = '', animatable = ''):
		"""
		Setup the expressions for the sideEmitter's nParticleShape node
		@param particleShapeName: The name of the nParticleShape node
		@param boatWorldCtrl: The name of the boatWorldCtrl curve
		@param speedObject: The name of the boat should be stripped :
		@type particleShapeName: String
		@type boatWorldCtrl: String
		@type speedObject: String
		"""

		## Creation
		expStringList = [
						'%s.lifespanPP = rand(%s.lifespanMin, %s.lifespanMax);' %(particleShapeName, animatable, animatable),
						'%s.twistSpeedPP = rand(%s.twistSpeedMin, %s.twistSpeedMax);' %(particleShapeName, animatable, animatable),
						'%s.spriteStartSizePP = rand(%s.spriteStartSizeMin, %s.spriteStartSizeMax);' %(particleShapeName, animatable, animatable),
						'%s.spriteScaleYPP = %s.spriteScaleXPP = %s.spriteStartSizePP;' %(particleShapeName, particleShapeName, particleShapeName),
						'%s.spriteTwistPP = rand(%s.twistAngleMin, %s.twistAngleMax);' %(particleShapeName, animatable, animatable),
						]
		## Build new expression
		cmds.dynExpression( particleShapeName, name = "%s_expression" % particleShapeName, creation = True, string = self.processExpressionString(expStringList) )

		## Runtime Before Dynamics
		expStringList = [
						'%s.spriteScaleYPP = %s.spriteScaleXPP = %s.spriteStartSizePP * %s.scaleOverLifeRamp;' %(particleShapeName, particleShapeName, particleShapeName, particleShapeName),
						'%s.spriteScaleXPP = %s.spriteScaleYPP;' %(particleShapeName, particleShapeName),
						'%s.spriteTwistPP += (%s.twistSpeedPP * %s.twistRateOverLife);' %(particleShapeName, particleShapeName, particleShapeName),
						'',
						]
		## Build new expression
		cmds.dynExpression( particleShapeName, name = "%s_expression" % particleShapeName, rbd = True, string = self.processExpressionString(expStringList) )

		## Connect some attrs to animatable group
		attrs = ['inheritFactor', 'conserve', 'drag', 'damp']
		for att in attrs:
			if not cmds.isConnected( '%s.%sSprite' %(animatable, att), '%s.%s' %(particleShapeName, att) ):
				cmds.connectAttr('%s.%sSprite' %(animatable, att), '%s.%s' %(particleShapeName, att), force = True)

	def _buildEmitterExpression(self, emitter = '', speedObject = '', animatable = ''):
		"""
		New builder for sideSplash nParticle Emitter
		Checks if the NPARTICLE_EMITTLERS_hrc exists or not too

		@param name: The name of the new emitter
		@param particleShapeName: List of the names of nParticleShape nodes to connect to the emitter
		@param boatIntersectCurveShape: The name of the intersection curve to emit from.
		@type name:  String
		@type particleShapeName: List
		@type boatIntersectCurveShape: String
		"""

		expStringList = [
						'float $minSpeed = %s.minSpeed;' % animatable,
						'float $maxSpeed = %s.maxSpeed;' % animatable,
						'float $speed = %s.speed;' % speedObject,
						'float $curve = smoothstep($minSpeed, $maxSpeed, $speed);',
						'float $rateMuliplier = %s.rateMultiplier;' % animatable,
						'float $splashMaxSpeed = %s.splashMaxSpeed;' % animatable,
						'',
						'if (%s.useSpeed == 1)' % animatable,
						'{',
						'	%s.rate = $rateMuliplier * $curve;' % emitter,
						'',
						'	float $emitterSpeed = $splashMaxSpeed * $curve;',
						'	if ($emitterSpeed < 2.25)',
						'	{',
						'		$emitterSpeed = 2.25;',
						'	}',
						'	%s.awayFromCenter = $emitterSpeed;' % emitter,
						'}',
						'else',
						'{',
						'	%s.rate = $rateMuliplier;' % emitter,
						'	%s.awayFromCenter = $splashMaxSpeed;' % emitter,
						'}',
						]
		## Build new expression
		cmds.expression(emitter, name = '%s_expression' % emitter, string = self.processExpressionString(expStringList))

		## Connect some attributes
		if not cmds.isConnected('%s.randomSpeed' % animatable, '%s.speedRandom' % emitter):
			cmds.connectAttr('%s.randomSpeed' % animatable, '%s.speedRandom' % emitter)

		return emitter

	def _buildSpeedExpression(self, speedObject = ''):
		"""
		Builds the base expression for the boats world_ctrl speed attr
		@param boatWorldCtrl: The name of the boat world_ctrl to build the expression for
		@type boatWorldCtrl: String
		"""
		expStringList = [
						'float $time;',
						'float $translation[] = `xform -q -ws -translation "%s"`;' % speedObject,
						'float $trx;',
						'float $try;',
						'float $trz;',
						'float $dx = $translation[0] - $trx;',
						'float $dy = $translation[1] - $try;',
						'float $dz = $translation[2] - $trz;',
						'float $d = sqrt( ($dx * $dx) + ($dy * $dy) + ($dz * $dz) );',
						'%s.speed = abs( $d / ( time - ($time + 0.001) ) );' % speedObject,
						'$trx = $translation[0];',
						'$try = $translation[1];',
						'$trz = $translation[2];',
						'$time = time;'
						]
		cmds.expression(name = '%s_expression' % speedObject.replace(':', '_'), string = self.processExpressionString(expStringList))

	def add_custom_attrs(self, objectName = '', **kwargs):
		fullName = '%s.%s' %(objectName, kwargs['longName'])

		if not cmds.objExists(fullName):
			cmds.addAttr(objectName, **kwargs)
			cmds.setAttr(fullName, keyable = True)

			if 'keyable' in kwargs:
				if kwargs['keyable'] == False:
					cmds.setAttr(fullName, channelBox = True)