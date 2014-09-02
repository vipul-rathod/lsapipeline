import os, getpass, sys, shutil, sgtk, time
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError

## Custom stuff
if 'T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean' not in sys.path:
	sys.path.append('T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean')
if 'T:/software/lsapipeline/custom' not in sys.path:
	sys.path.append('T:/software/lsapipeline/custom')
from debug import debug
import utils as utils
import ProgressBarUI as pbui
import CONST as CONST
#reload(CONST)
#reload(utils)

def isAssemblyRef(node):
	isRef = False
	for each in cmds.ls(node, l = True)[0].split("|"):
		if each:
			if cmds.nodeType(each) == 'assemblyReference':
				isRef = True
	return isRef

def connectAllWithOceanHeightAttr(object = ''):
	"""
	Find and attach everything in the scene which has an oceanHeightHook attribute to the ocean
	"""
	inprogressBar = pbui.ProgressBarUI(title = 'Hooking To Ocean:')
	inprogressBar.show()
	inprogressBar.updateProgress(percent = 0, doingWhat = 'Hooking everything to ocean now...')
	debug(None, method = 'connectAllWithOceanHeightAttr', message = 'Rebuilding Ocean Hooks', verbose = False)

	## Find all in scene with oceanHeightHook Attribute
	## Setup the progress bar
	if not cmds.objExists('Shot_FX_hrc'):
		cmds.group(n = 'Shot_FX_hrc', em = True)
	if not  cmds.objExists('BOAT_OceanLocators_hrc'):
		cmds.group(n = 'BOAT_OceanLocators_hrc', em = True)
		cmds.parent('BOAT_OceanLocators_hrc', 'Shot_FX_hrc')
		cmds.setAttr('BOAT_OceanLocators_hrc.visibility', 0)

	## Clean up existing hooks in the scene
	inprogressBar.updateProgress(percent = 50, doingWhat = 'Cleaning up now..')

	if object.startswith('All'):
		object = ''
	elif object.startswith('Dock'):
		object = 'BLD'
	elif object.startswith('Boat'):
		object = 'CHAR'
	elif object.startswith('Prop'):
		object = 'PROP'

	cleanUpExisting(filters = [object])
	if object == 'BLD':
		## Clean-up the ADEF BLD's oceanHook control animatable groups...
		[cmds.delete(transform) for transform in cmds.ls(type = 'transform') if transform.endswith('_oceanCtrls_hrc')]

	## Rebuild / build the hooks for boats in the scene
	inprogressBar.updateProgress(percent = 75, doingWhat = 'performHookBoatsToOcean now..')
	startTime = time.time()
	performHookBoatsToOcean()
	print 'TOTAL TIME FOR performHookBoatsToOcean: %s' % (time.time()-startTime)

	## Now make sure cycle check is off because it's a fn pita
	cmds.cycleCheck(e = 0)
	_finished(inprogressBar)

def _finished(inprogressBar):
	inprogressBar.updateProgress(percent = 100, doingWhat = 'Finished hooking boats...')
	inprogressBar.close()

def cleanUpExisting(filters = []):
	"""
	Brute force atm.
	Need to clean legacy builds first to see if this will work out okay for deleting all the existing setup and replacing with new locks
	"""
	if cmds.objExists('BOAT_OceanLocators_hrc'):
		getLocs = cmds.listRelatives('BOAT_OceanLocators_hrc', children = True)
		getLocs = [loc for loc in getLocs for fil in filters if fil in loc] if getLocs else None

		if getLocs:
			for loc in getLocs:
				hooked_expression = cmds.listConnections(loc, type = 'expression')
				hooked_expression = list( set( hooked_expression ) ) if hooked_expression else []
				[cmds.delete(exp) for exp in hooked_expression if exp.endswith('_boatLockToOcean')]
				cmds.delete(loc)

	##  Now clean up all the LEGACY expressions...
	[cmds.delete(exp) for exp in cmds.ls(type = 'expression') if exp.endswith('_loc_lockToOcean')]

def deleteExistingConnections(charOceanLock = ''):
	"""
	For legacy fixing
	"""
	debug(None, method = 'deleteExistingConnections', message = 'Deleting for: %s' % charOceanLock, verbose = False)
	## Now disconnect each Attr on the orig oceanloc
	for eachPlug in cmds.listConnections(charOceanLock, plugs = True, destination = True):
		getTheAttr = eachPlug.split('.')[-1]
		debug(None, method = 'deleteExistingConnections', message = 'Checking plug: %s' % eachPlug, verbose = False)
		debug(None, method = 'deleteExistingConnections', message = 'Checking getTheAttr: %s' % getTheAttr, verbose = False)
		if 'world_ctrl' in eachPlug:
			try:

				cmds.disconnectAttr(eachPlug, '%s.%s' % (charOceanLock, getTheAttr))
				debug(None, method = 'deleteExistingConnections', message = 'Successfully deleted connections for %s %s' % (charOceanLock, getTheAttr), verbose = False)
			except:
				try:
					cmds.disconnectAttr('%s.%s' % (charOceanLock, getTheAttr), eachPlug)
					debug(None, method = 'deleteExistingConnections', message = 'Successfully deleted connections for %s %s' % (charOceanLock, getTheAttr), verbose = False)
				except:
					pass
		elif cmds.nodeType(eachPlug) == 'unitConversion' or cmds.nodeType(eachPlug) == 'pairBlend2' and '.output' in eachPlug:
			try:
				cmds.disconnectAttr(eachPlug, '%s.rotateX' % charOceanLock)
				debug(None, method = 'deleteExistingConnections', message = 'Successfully deleted connections for %s %s' % (charOceanLock, getTheAttr), verbose = False)
			except:
				try:
					cmds.disconnectAttr(eachPlug, '%s.rotateZ' % charOceanLock)
					debug(None, method = 'deleteExistingConnections', message = 'Successfully deleted connections for %s %s' % (charOceanLock, getTheAttr), verbose = False)
				except:
					pass

def _deleteAllBakeAttrsOnLocators():
	boatHookList = getBoatHooks()
	if boatHookList:
		for eachHook in boatHookList:
			if cmds.objExists('%s.bakedBoat' % eachHook):
				cmds.deleteAttr('%s.bakedBoat' % eachHook)
				debug(None, method  = 'performHookBoatsToOcean', message = 'deleteAttr("%s.bakedBoat")' % eachHook, verbose = False)

def getBoatHooks():
	boatHookList = [eachHook for eachHook in cmds.ls(type = 'transform') if cmds.objExists('%s.oceanHeightHook' % eachHook)]
	return boatHookList if boatHookList else []

def _removeLegacyOceanHooks():
	## Legacy Attrs on world_Ctrl
	legacyAttrs = ['autoLag', 'sideToSide', 'frontToBack']

	for eachBoatHook in getBoatHooks():
		boatName        = eachBoatHook.split(':')[0]
		worldCtrl       = '%s:world_ctrl' % boatName
		charOceanLock   = '%s:oceanLock' % boatName

		###################
		###### LEGACY FIX
		###################
		for eachAttr in legacyAttrs:
			if cmds.objExists('%s.%s' % (worldCtrl, eachAttr)):
				try:
					cmds.setAttr('%s.%s' % (worldCtrl, eachAttr), 0)
					cmds.setAttr('%s.%s' % (worldCtrl, eachAttr), keyable = False, locked = True)
					cmds.deleteAttr('%s.%s' % (worldCtrl, eachAttr))
				except:
					pass

				## delete any existing connections on the base oceanlocks from the rigs
				deleteExistingConnections(charOceanLock)

def _getAttrsToAdd():
	##  Maya's boat locatorShape attrs
	attrsToAdd = {'startFrame'      : [0, 5000, 1],
				  'buoyancy'        : [0, 1, .5],
				  'waterDamping'    : [0, 1., .5],
				  'airDamping'      : [0, 1, .5],
				  'objectHeight'    : [0, 100, 1],
				  'gravity'         : [0, 980, 9.8],
				  'sceneScale'      : [0, 10, 1],
				  'boatLength'      : [0,100, 1],
				  'boatWidth'       : [0, 100, 1],
				  'roll'            : [0, 1, .1],
				  'pitch'           : [0, 1, .1],
				  'oceanYDamp'      : [1, 1000, 1]
				  }

	return attrsToAdd

def _addAttrsToWorldCtrl(worldCtrl):
	for eachBoatHook in getBoatHooks():
		if ':' in eachBoatHook:
			boatName        = eachBoatHook.split(':')[0]
			worldCtrl       = '%s:world_ctrl' % boatName
		else:
			worldCtrl       = 'world_ctrl'

		## Add the attrs to the boatName:world_ctrl
		for key, var in _getAttrsToAdd().items():
			if not cmds.objExists('%s.%s' % (worldCtrl, key)):
				debug(None, method = 'performHookBoatsToOcean', message = 'Adding attr: %s.%s' % (worldCtrl, key), verbose = False)
				cmds.addAttr(worldCtrl, ln = key,  at = 'double', min = var[0], max = var[1], dv = var[2])
				cmds.setAttr('%s.%s' % (worldCtrl, key), keyable = True)
			else:
				debug(None, method = 'performHookBoatsToOcean', message = 'Skipping attr %s.%s exists already' % (worldCtrl, key), verbose = False)

def _addBakedAttrToHooks():
	boatHookList = getBoatHooks()
	if boatHookList:
		for eachHook in boatHookList:
			bakeAttrName = '%s.%s' %(eachHook, 'bakedBoat')
			## Add attr to all the boat that will need to be baked now...
			if not cmds.objExists(bakeAttrName):
				cmds.addAttr(eachHook, ln = 'bakedBoat', at = 'bool')
				cmds.setAttr(bakeAttrName, keyable = False, channelBox = False)
				cmds.setAttr(bakeAttrName, 1)

def _buildExpression(locShapeName, oceanLocName, oceanShader, boatName):
	## Build the expression for the new locators.
	if ':' in oceanLocName and 'ADef' not in oceanLocName:
		finalLine = '%s.translateY = $cpoint[0] / %s:world_ctrl.oceanYDamp;' % (oceanLocName, boatName)
	else:
		if 'ADef' not in oceanLocName:
			if cmds.objExists('world_ctrl.oceanYDamp'):
				finalLine = '%s.translateY = $cpoint[0] / world_ctrl.oceanYDamp;' % oceanLocName
			else:
				finalLine = '%s.translateY = $cpoint[0] / %s:world_ctrl.oceanYDamp;' % (oceanLocName, boatName)
		else:
			print 'Processing expression for ASSEMBLY REFERENCE'
			finalLine = '%s.translateY = $cpoint[0] / %s_oceanCtrls_hrc.oceanYDamp;' % (oceanLocName, boatName)

	debug(None, method  = '_buildExpression', message = 'finalLine: %s' % finalLine, verbose = False)

	expStringList= [
					'int $lastFrame = %s.lastFrame;\n' % locShapeName,
					'int $startFrame = %s.startFrame;\n' % locShapeName,
					'%s.lastFrame = frame;\n' % locShapeName,
					'if( frame <= $startFrame ){\n\t',
					'if( $lastFrame == frame ){\n\t\t',
					'%s.startY = %s.translateY;\n\t\t' % (locShapeName, oceanLocName),
					'%s.startRotX = %s.rotateX;\n\t\t' % (locShapeName, oceanLocName),
					'%s.startRotZ = %s.rotateZ;\n\t' % (locShapeName, oceanLocName),
					'} else {\n\t\t',
					'float $val = %s.startY;\n\t\t' % locShapeName,
					'setAttr %s.ty $val;\n\t\t' % oceanLocName,
					'$val = %s.startRotX;\n\t\t' % locShapeName,
					'setAttr %s.rx $val;\n\t\t' % oceanLocName,
					'$val = %s.startRotZ;\n\t\t' % locShapeName,
					'setAttr %s.rz $val;\n\t' % oceanLocName,
					'}\n\t',
					'%s.velocity = 0.0;\n\t\t' % locShapeName,
					'%s.waterLevel = 0.0;\n\t\t' % locShapeName,
					'%s.rotVelX = 0.0;\n\t\t' % locShapeName,
					'%s.rotVelZ = 0.0;\n' % locShapeName,
					'} else if( frame > $lastFrame ){\n',
					'float $u = %s.translateX;\n' % oceanLocName,
					'float $v = %s.translateZ;\n' % oceanLocName,
					'float $y = %s.translateY;\n' % oceanLocName,
					'float $gravity = %s.gravity / %s.sceneScale;\n' % (locShapeName, locShapeName),
					'float $dt = 0.006; //timestep value for 30 fps\n',
					'float $height = %s.objectHeight;\n' % locShapeName,
					'float $buoyancy = %s.buoyancy;\n' % locShapeName,
					'if( $buoyancy > 0.98 ){\n\t',
					'$buoyancy = 0.98;\n'
					'}\n',
					'float $waterDamp = %s.waterDamping;\n' % locShapeName,
					'float $airDamp = %s.airDamping;\n' % locShapeName,
					'float $turn = %s.rotateY;\n' % oceanLocName,
					'float $rx = %s.rotateX;\n' % oceanLocName,
					'float $rz = %s.rotateZ;\n' % oceanLocName,
					'float $xoff = sin( deg_to_rad( $turn ));\n',
					'float $zoff = cos( deg_to_rad( $turn ));\n',
					'float $xwidth = %s.boatWidth * 0.4;\n' % locShapeName,
					'float $zwidth = %s.boatLength * 0.4;\n' % locShapeName,
					'float $rxgain = %s.roll;\n' % locShapeName,
					'float $rzgain = %s.pitch;\n' % locShapeName,
					'float $disp[] = `colorAtPoint -u $u -v $v -u (($u + $xoff)*$xwidth) -v (($v + $zoff)*$xwidth) -u (($u - $xoff)*$xwidth) -v (($v - $zoff)*$xwidth) -u (($u - $zoff)*$zwidth) -v (($v + $xoff)*$zwidth) -u (($u + $zoff)*$zwidth) -v (($v - $xoff)*$zwidth) %s`;\n' % oceanShader,
					'float $wHeight = ($disp[0] * 2.0 + $disp[1] + $disp[2] + $disp[3] + $disp[4])/6.0;\n',
					'float $zdiff = ($disp[1] - $disp[2])/$xwidth;',
					'float $xdiff = ($disp[3] - $disp[4])/$zwidth;',
					'float $rotVelX = %s.rotVelX;' % locShapeName,
					'float $rotVelZ = %s.rotVelZ;' % locShapeName,
					'float $newXVel = $rxgain *(($zdiff * -40.0 - $rx) * $waterDamp + $rotVelX * (1-$waterDamp));',
					'float $newZVel = $rzgain *(($xdiff * -40.0 - $rz) * $waterDamp + $rotVelZ * (1-$waterDamp));',
					'%s.rotVelX = $newXVel;\n' % locShapeName,
					'%s.rotVelZ = $newZVel;\n' % locShapeName,
					'float $vel = %s.velocity;\n' % locShapeName,
					'float $waterVel = $wHeight - %s.waterLevel;\n' % locShapeName,
					'%s.waterLevel = $wHeight;\n' % locShapeName,
					'float $aboveWater = (($y + $height/2) - $wHeight)/$height;\n',
					'if( $aboveWater > 1.0 ){\n',
					'$aboveWater = 1.0;\n',
					'$waterVel = 0.0;\n',
					'}\n',
					 'else if( $aboveWater < 0.0 )\n',
					 '{\n',
					'$aboveWater = 0.0;\n',
					'}\n',
					'float $underWater = 1.0 - $aboveWater;\n',
					'float $damp = $waterDamp * $underWater + $airDamp * $aboveWater;\n',
					'float $force = $gravity * $dt *($underWater/(1-$buoyancy) - 1.0);\n',
					'float $newVel = ($waterVel) * $damp + ($force+$vel)*(1-$damp);\n',
					'%s.velocity = $newVel;\n' % locShapeName,
					'setAttr %s.rx ( $rx + $newXVel );\n' % oceanLocName,
					'setAttr %s.rz ( $rz + $newZVel );\n' % oceanLocName,
					'float $dummy = %s.displacement;\n' % oceanShader,
					'}\n\n',
					'float $pu = %s.translateX;\n' % oceanLocName,
					'float $pv = %s.translateZ;\n' % oceanLocName,
					'float $cpoint[] = `colorAtPoint -u $pu -v $pv %s`;\n' % oceanShader,
					finalLine
					]
	## REMOVED 'setAttr %s.ty ( $y + $newVel );\n' % oceanLocName,
	## Check if the expression already exists in the scene, if so delete it
	utils.checkExpressionExists('%s_boatLockToOcean' % boatName)

	## Build new expression
	cmds.expression(n = '%s_boatLockToOcean' % boatName, string = utils.processExpressionString(expStringList))

	debug(None, method  = '_buildExpression', message = 'Expression built successfully', verbose = False)

def _buildMayaBoatOceanLocator():
	## Build a boatLocator for the expression and add it's attrs
	## Select the ocean first
	cmds.select('ocean_srf', r = True)
	mel.eval("AddBoatLocator;")
	debug(None, method = '_buildMayaBoatOceanLocator', message = 'Built AddBoatLocator successfully...', verbose = False)

def performHookBoatsToOcean(oceanShader = CONST.OCEANANIMSHADER, interactiveOceanShader = CONST.OCEANINTERACTIVESHADER):
	"""
	New method that uses the maya's default boat locator approach
	"""
	## cleanup the old build if it exists
	_removeLegacyOceanHooks()

	## Find all hooks in the scene...
	boatHookList = getBoatHooks()
	debug(None, method  = 'performHookBoatsToOcean', message = 'boatHookList: %s' % boatHookList, verbose = False)

	## If we have a valid list of hooks in the scene proceed....
	if boatHookList:
		for eachBoatHook in boatHookList:
			if ':' in eachBoatHook:
				boatName        = eachBoatHook.split(':')[0]
				worldCtrl       = '%s:world_ctrl' % boatName
				oceanLocName    = '%s_boatOceanLoc' % boatName
				charOceanLock   = '%s:oceanLock' % boatName
			else:
				boatName        = ''
				worldCtrl       = 'world_ctrl'
				oceanLocName    = 'temp_boatOceanLoc'
				charOceanLock   = 'oceanLock'

			debug(None, method  = 'performHookBoatsToOcean', message = 'boatName:      %s' % boatName, verbose = False)
			debug(None, method  = 'performHookBoatsToOcean', message = 'worldCtrl:     %s' % worldCtrl, verbose = False)
			debug(None, method  = 'performHookBoatsToOcean', message = 'oceanLocName:  %s' % oceanLocName, verbose = False)
			debug(None, method  = 'performHookBoatsToOcean', message = 'charOceanLock: %s' % charOceanLock, verbose = False)

			###################
			###### START BUILD
			###################
			if not cmds.objExists(oceanLocName):
				startmyLocator = time.time()
				_buildMayaBoatOceanLocator()

				## Now perform a check to find the locator name, because maya has the dumb and doesn't allow us to make this with a name cleanly
				myLocator = [myLoc for myLoc in cmds.ls(type = 'transform') if cmds.objExists('%s.buoyancy' % myLoc) and 'locator' in myLoc]
				debug(None, method = 'performHookBoatsToOcean', message = 'myLocator: %s' % myLocator, verbose = False)

				## If we have a newly made maya boat locator lets work on it...
				if myLocator:
					cmds.rename(myLocator, oceanLocName)
					debug(None, method = 'performHookBoatsToOcean', message = 'myLocator: %s renamed to : %s' % (myLocator, oceanLocName), verbose = False)

					## Add the new attrs tot the world_ctrl
					if not isAssemblyRef(oceanLocName) and 'ADef' not in oceanLocName:
						_addAttrsToWorldCtrl(worldCtrl)

					## Now rename the expression
					start = time.time()
					connectedExpressions = [exp for exp in cmds.listConnections(oceanLocName, source =True) if cmds.nodeType(exp) == 'expression']
					if connectedExpressions:
						exp = list(set(connectedExpressions))
						## DELETE THE EXPRESSION AND BUILD A NEW ONE WITH THE RIGHT FCKN NAMES IN IT!!!!
						cmds.delete(exp)

						## Define the expression:
						locShapeName = '%sShape' % oceanLocName
						debug(None, method = 'performHookBoatsToOcean', message = 'locShapeName: %s' % locShapeName, verbose = False)

						## Now build the expression for the locator
						debug(None, method = 'performHookBoatsToOcean', message = 'Now build the expression for the locator...', verbose = False)
						if not isAssemblyRef(oceanLocName) and 'ADef' not in oceanLocName:
							_buildExpression(locShapeName, oceanLocName, oceanShader, boatName)
							debug(None, method = 'performHookBoatsToOcean', message = '_buildExpression success..', verbose = False)
					print 'TIME to process connected expressions: %s' % (time.time()-start)

					## Now parent it to the right group
					start = time.time()
					try:
						cmds.parent(oceanLocName, 'BOAT_OceanLocators_hrc')
						debug(None, method = 'performHookBoatsToOcean', message = 'parent to BOAT_OceanLocators_hrc success...', verbose = False)
					except:
						pass
					print 'TIME to parent: %s' % (time.time()-start)

				print 'Total time to build default ocean boat locator: %s' % (time.time()-startmyLocator)

				start = time.time()
				## Delete the current legacy expressions in the Y axis of the charOceanLocator setup
				connectedExpressions = [exp for exp in cmds.listConnections(charOceanLock, source =True) if cmds.nodeType(exp) == 'expression']
				debug(None, method = 'performHookBoatsToOcean', message = 'connectedExpressions:%s' % connectedExpressions, verbose = False)
				if connectedExpressions:
					exp = list(set(connectedExpressions))
					cmds.delete(exp)
					debug(None, method = 'performHookBoatsToOcean', message = 'Deleted ... %s' % exp , verbose = False)

				if not isAssemblyRef(oceanLocName) and 'ADef' not in oceanLocName:
					debug(None, method = 'performHookBoatsToOcean', message = 'Point Constraint now for %s' % oceanLocName , verbose = False)
					## Now connect the oceanLocName locator X and Z to the world ctrl so that this locator follows the world ctrl around
					## This locator drives the Up and Down of the world ctrl.
					cmds.pointConstraint(worldCtrl, oceanLocName, skip = ['y'], mo = False, n = '%s_%s_PointConstraint' % (worldCtrl, oceanLocName))
					debug(None, method = 'performHookBoatsToOcean', message = 'Point Constraint Success...' , verbose = False)
				else:
					## Ensure oceanLock translation Y is reset back to 0 because it will cause some minor offset Y value between the 2 locators
					cmds.setAttr('%s.translateY' % eachBoatHook, 0) # This is essential line for both locators to match 100%

					## Create a ctrl grp for the BLD
					assRefCtrlGrp = '%s_oceanCtrls_hrc' % boatName
					if not cmds.objExists(assRefCtrlGrp):
						assRefCtrlGrp = cmds.group(n = assRefCtrlGrp, em = True)
						cmds.parent(assRefCtrlGrp, 'BOAT_OceanLocators_hrc')

					## Now add the attrs to it.
					for key, var in _getAttrsToAdd().items():
						if not cmds.objExists('%s.%s' % (assRefCtrlGrp, key)):
							debug(None, method = 'performHookBoatsToOcean', message = 'Adding attr: %s.%s' % (assRefCtrlGrp, key), verbose = False)
							cmds.addAttr(assRefCtrlGrp, ln = key,  at = 'double', min = var[0], max = var[1], dv = var[2])
							cmds.setAttr('%s.%s' % (assRefCtrlGrp, key), keyable = True)
						else:
							debug(None, method = 'performHookBoatsToOcean', message = 'Skipping attr %s.%s exists already' % (assRefCtrlGrp, key), verbose = False)

					### Put the darn locator for this thing in the right world space
					getLocation = cmds.xform(eachBoatHook, query = True, pivots = True, ws = True)
					cmds.setAttr('%s.translateX' % oceanLocName, getLocation[0])
					cmds.setAttr('%s.translateY' % oceanLocName, getLocation[1])
					cmds.setAttr('%s.translateZ' % oceanLocName, getLocation[2])
					cmds.makeIdentity(oceanLocName, apply = True, t = 1, r = 1, s = 1, n = 0)

					## Now build the expression for the assembly Ref loc
					_buildExpression(locShapeName, oceanLocName, oceanShader, boatName)
				### Now connect the referenced charName:oceanLock.translateY to the new ocean locator which will in turn move the world_ctrl accordingly as a result
				cmds.connectAttr('%s.translateY' % oceanLocName, '%s.translateY' % charOceanLock, f = True)

				## Now connect the orientation for oceanLocName locator to the charOceanLock locator which will in turn move the world_ctrl accordingly as a result
				try:
					cmds.connectAttr('%s.rotateX' % oceanLocName, '%s.rotateX' % charOceanLock, f = True)
				except RuntimeError:
					pass
				try:
					cmds.connectAttr('%s.rotateY' % oceanLocName, '%s.rotateY' % charOceanLock, f = True)
				except RuntimeError:
					pass
				try:
					cmds.connectAttr('%s.rotateZ' % oceanLocName, '%s.rotateZ' % charOceanLock, f = True)
				except RuntimeError:
					pass

				### Now connect the world_ctrl attrs to the locators
				for key, var in _getAttrsToAdd().items():
					try:
						if not isAssemblyRef(oceanLocName) and 'ADef' not in oceanLocName:
							cmds.connectAttr('%s.%s' % (worldCtrl, key), '%s.%s' % (oceanLocName, key), f = True)
						else:
							cmds.connectAttr('%s.%s' % ('%s_oceanCtrls_hrc' % boatName, key), '%sShape.%s' % (oceanLocName, key), f = True)
					except:
						pass

				## Get / Set transform limit of oceanLock
				for x in ['translationX', 'translationY', 'translationZ', 'rotationX', 'rotationY', 'rotationZ']:
					transformEnabler = eval( 'cmds.transformLimits("%s", enable%s%s = True, q = True)' %(eachBoatHook, x[0].upper(), x[1:]) )
					transformValue = eval( 'cmds.transformLimits("%s", %s = True, q = True)' %(eachBoatHook, x) )
					eval( 'cmds.transformLimits("%s", enable%s%s = %s, %s = %s)' %(oceanLocName, x[0].upper(), x[1:], transformEnabler, x, transformValue) )
					eval( 'cmds.transformLimits("%s", enable%s%s = %s, %s = %s)' %(oceanLocName, x[0].upper(), x[1:], transformEnabler, x, transformValue) )
				print 'Time to cleanup expressions and prop and assembly ref locs: %s' % (time.time()-start)
			else:
				print "Skipping %s already in scene..." % oceanLocName