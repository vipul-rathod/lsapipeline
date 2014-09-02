import os, sys, time
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om
import tank
from tank import TankError
from debug import debug
if 'T:/software/lsapipeline/custom' not in sys.path:
	sys.path.append('T:/software/lsapipeline/custom')
import core_archive_lib as coreLib
from debug import debug
import maya.api.OpenMaya as om
#reload(coreLib)

def deleteEmptyUVSets():
	"""
	Function to remove empty uv's
	"""
	getMeshes = cmds.ls(type = 'mesh', l = True)
	emptyExists = False
	if getMeshes:
		for eachMesh in getMeshes:
			selectionList    = om.MSelectionList()
			selectionList.add(eachMesh)
			nodeDagPath      = selectionList.getDagPath(0)
			shapeFn          = om.MFnMesh(nodeDagPath)
			## Now fetch data from shapeFn
			shapeName        = shapeFn.name()
			#debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('shapeName:',  shapeName), verbose = False)
			currentUVSets    = shapeFn.getUVSetNames()
			#debug(None, method = 'uv_getUVs._getUVSets', message = 'Fetching uvsets now..', verbose = False)
			validUVSets      = []
			getFaceCount     = shapeFn.numPolygons

			try:
				[[validUVSets.extend([eachUVset]) for eachUVset in shapeFn.getFaceUVSetNames(x) if eachUVset not in validUVSets] for x in range(0, getFaceCount) ]
			except:
				uvsets = None

			for eachUVSet in currentUVSets:
				if eachUVSet not in validUVSets:
					print 'Removing empty UVSet %s from %s' % (eachUVSet, eachMesh)
					cmds.select(eachMesh, r = True)
					try:
						cmds.polyUVSet(delete = True, uvSet = eachUVSet)
						emptyExists = True
					except:
						cmds.warning('Failed to empty uv set %s of %s...' % (eachUVSet, eachMesh))
	if emptyExists:
		cmds.headsUpMessage('YOU HAD EMPTY UV SETS CLEANED UP! MAKE SURE YOU EXPORT SHD.XML AS WELL!', time = 3)

def _fixUVNames():
	"""
	used to cleanup map renames as the behind the scenes maya uvSetName doens't change when using the rename i
	in the maya uv editor.. gg maya!!!
	"""
	for eachMesh in cmds.ls(type = 'mesh'):
		getParent = cmds.listRelatives(eachMesh, parent = True)[0]
		fullPathToParent = cmds.ls(getParent, l = True)[0]
		selectionList    = om.MSelectionList()
		selectionList.add(fullPathToParent)
		nodeDagPath      = selectionList.getDagPath(0)
		shapeFn          = om.MFnMesh(nodeDagPath)
		## Now fetch data from shapeFn
		try:
			shapeName = shapeFn.name()
			currentUVSets = shapeFn.getUVSetNames()
			originalSize = len(currentUVSets)

			for x, each in enumerate(currentUVSets):
				cmds.setAttr('%s.uvSet[%s].uvSetName' % (getParent, x), each, type = 'string')
				uvDict = {}
				uvSets = cmds.polyUVSet(getParent, allUVSets = True, query = True)
				uvSetIds = cmds.polyUVSet(getParent, allUVSetsIndices = True, query = True)
				for i, uv in enumerate(uvSets):
					uvDict.setdefault(uv, [])
					uvDict[uv].append(uvSetIds[i])

				if len(uvSets) > originalSize:
					if len( uvDict[each] ) > 1:
						cmds.polyUVSet(getParent, uvSet = each, rename = True, newUVSet = '%s_temp' % each)
						textureLink = cmds.uvLink(uvSet = '%s.uvSet[%s].uvSetName' % (getParent, uvDict[each][-1]), query = True)

						if textureLink:
							[cmds.uvLink(uvSet = '%s.uvSet[%s].uvSetName' % (getParent, x), texture = tex) for tex in textureLink]

						cmds.polyUVSet(getParent, uvSet = each, delete = True)
						cmds.polyUVSet(getParent, uvSet = '%s_temp' % each, rename = True, newUVSet = each)
		except RuntimeError:
			cmds.warning('Failed to process "%s", probably corrupted mesh, skipping...' % eachMesh)

def switchMeshtoBBox():

	sel = cmds.ls(type = 'mesh')
	for eachMesh in sel:
		parent = cmds.listRelatives(eachMesh, parent=True)[0]
		cmds.setAttr(parent + ".overrideLevelOfDetail", 1)

#     sel = cmds.ls(type='mesh')
#     for s in sel:
#         bbx = cmds.listRelatives(s, parent=True)
#         cmds.setAttr(bbx[0]+".overrideLevelOfDetail",0)

def cleanupUnknown():
	dead = cmds.ls(type = 'unknown')
	if dead:
		for each in dead:
			cmds.lockNode(each, lock = False)
			cmds.delete(each)

def delAllImagePlanes():
	"""
	Func to just delete all image planes for lighting
	"""
	print 'Deleting Image planes..'
	getAllPlanes = cmds.ls(type = 'imagePlane')
	for each in getAllPlanes:
		try:
			cmds.delete(cmds.listRelatives(each, parent =True))
		except:
			pass
	print 'All Image planes successfully deleted...'

def shotCleanupPlacements():
	"""
	Put all the placement nodes in the scene into a placments_hrc group
	"""
	## cleanup all placements
	deadParents = []
	getPlacements = cmds.ls(type = 'place3dTexture')
	if not cmds.objExists('placements_hrc'):
		cmds.group(n = 'placements_hrc', em = True)

	## Now look for placements not already a child of placments_hrc and parent them to placements_hrc
	for eachPlce in getPlacements:
		getParent = cmds.listRelatives(eachPlce, parent = True)
		if getParent:
			if cmds.listRelatives(eachPlce, parent = True)[0] != 'placements_hrc':
				## now get the actual parent if there is one and put it into the deadParents group
				try:
					deadParents.append(cmds.listRelatives(eachPlce, parent = True)[0])
				except:
					pass
				cmds.parent(eachPlce, 'placements_hrc')
		else:
			cmds.parent(eachPlce, 'placements_hrc')
	## Now remove all the placements groups that no longer have children
	if deadParents:
		cmds.delete(deadParents)

def shotCleanupLights():
	## Cleanup all lights
	getLights = cmds.ls(type = 'light')
	if not cmds.objExists('LIGHTS_hrc'):
		cmds.group(n = 'LIGHTS_hrc', em = True)
	
	for eachLight in getLights:
		try:
			if cmds.listRelatives(eachLight, parent = True)[0] != 'LIGHTS_hrc' and 'Shape' not in eachLight:
				try:
					cmds.parent(eachLight, 'LIGHTS_hrc')
				except RuntimeError:
					pass
		except:
			pass

def checkingMessage(checkingWhat = '', start = True, failed = False):
	getChars = len(checkingWhat)
	sepChar = '='
	if start:
		print "%s%s" % (sepChar*11, sepChar * getChars)
		print "|CHECKING| %s " % checkingWhat
	elif failed:
		print "%s%s|FAILED CHECKS|" % ('-'*11, '-' * getChars)

	else:
		print "%s%s|PASSED CHECKS|" % ('-'*11, '-' * getChars)
		print "%s%s" % (sepChar*11, sepChar * getChars)
		print

def removeAllNS(deleteContent = False):
	checkingMessage(checkingWhat = 'REMOVING A LEVEL OF NAMESPACE NOW...', start = True,  failed = False)
	## Now remove all the nameSpaces!! This is to remove any clashes with the core_assemblies later on...
	safeNS = ['UI', 'shared']
	getAllNameSpaces = cmds.namespaceInfo(listOnlyNamespaces = True)
	for eachNS in getAllNameSpaces:
		if eachNS not in safeNS:
			try:
				if deleteContent:
					cmds.namespace(removeNamespace = eachNS, deleteNamespaceContent = True)
				else:
					cmds.namespace(removeNamespace = eachNS, mergeNamespaceWithRoot = True)
			except RuntimeError:
				pass

	if cmds.namespaceInfo(listOnlyNamespaces = True) != ['UI', 'shared']:
		removeAllNS()
	else:
		checkingMessage(checkingWhat = 'NAMESPACES REMOVED...', start = False,  failed = False)

def cleanUpShaders():
	"""
	Assign default lambert to any meshes and then do a remove shaders from hypershade.
	"""
	MC = cmds.ls(type = 'core_archive')
	ignoreAssemblies = []
	finalShadedGeo = []
	## Look for archives connections *geo* and add them to the ignoreAssemblies
	## Build a connection node for the archives and hook them up so they don't get deleted
	if MC:
		for each in MC:
			 ignoreAssemblies = ignoreAssemblies + cmds.listConnections(each)
		# If safe node already exists, delete it.
		if cmds.objExists('core_safe'):
			cmds.delete('core_safe')
		# Create a filter node and connect arbitrary connection to it
		createTempNode = cmds.createNode('objectTypeFilter', name = 'core_safe')
		for eachCore in MC:
			addAlphaAttr = cmds.addAttr(createTempNode, longName = 'core_%s' % '_'.join(eachCore.split(":")) , attributeType = 'double')
			cmds.connectAttr('%s.caching' % eachCore, '%s.core_%s' % (createTempNode, '_'.join(eachCore.split(":"))), force = True)

	## Get all the transforms of the geo only
	allGeo = [eachGeo for eachGeo in cmds.listRelatives(cmds.ls(type = 'mesh'), parent = True)]

	## Now process the final geo lists for shader assignment ignoring anything attached to the core archives
	[finalShadedGeo.extend([eachShape]) for eachShape in allGeo if eachShape not in ignoreAssemblies]

	## Now try to assign the shader
	try:
		cmds.sets(finalShadedGeo, e = True , forceElement = 'initialShadingGroup')
		mel.eval("MLdeleteUnused();")
	except:
		cmds.warning('FAILED TO ASSIGN initialShadingGroup!!!')
		pass

	## Mentalcore cleanup
	try:
		from mentalcore import mapi
		mapi.enable(True)
		mapi.reset(show_dialog = False)
	except:
		cmds.warning('mentalcore not found')
   
def bigbadcleanup():
	"""
	HARD CORE DELETE: Will wipe scene excluding geo to bare bones.
	MDL STEP ONLY
	"""
	bad = ['animCurveTL', 'animCurveTA', 'animCurveTU', 'bump2d', 'condition', 'file', 'gammaCorrect', 'mentalrayTexture', 'mib_color_alpha', 'multiplyDivide',
			'place2dTexture', 'polySplit', 'polyBridgeEdge', 'rgbToHsv', 'script', 'shaderGlow', 'surfaceShader', 'strokeGlobals',
			'surfaceShader', 'lambert', 'displayLayer', 'mia_exposure_simple', 'mia_roundcorners', 'mib_amb_occlusion', 'mip_rayswitch',
			'partition', 'polyCrease', 'polyNormal', 'polyExtrudeFace', 'polyTweak', 'ramp', 'polyBoolOp', 'polyCloseBorder', 'polyCube', 'polyDelEdge',
			'polyExtrudeEdge', 'polyMergeVert', 'polyMirror', 'polySplitRing', 'deleteComponent', 'objectNameFilter', 'objectTypeFilter', 'objectScriptFilter',
			'postProcessList', 'renderLayer', 'checker', 'layeredTexture', 'rampShader']

	AdefBad =  ['hyperLayout', 'hyperGraphInfo', 'hyperView']
	print "CHECKING FOR ASSEMBLY DEFINITION AUX NODES NOW"
	for each in AdefBad:
		for eachNaughty in cmds.ls(type = each):
			try:
				getAdef = cmds.listConnections(eachNaughty)
				if getAdef:
					if '_ADef_ARef' in getAdef[0]:
						cmds.rename(eachNaughty, '%s_%s' % (getAdef[0], each))
						print 'Renamed %s to %s' % (eachNaughty, '%s_%s' % (getAdef[0], each))
					else:
						cmds.delete(eachNaughty)
						print 'Removed: %s' % eachNaughty
				else:
					cmds.delete(eachNaughty)
					print 'Removed: %s' % eachNaughty
			except TypeError:
				cmds.delete(eachNaughty)

	print 'CHECKING FOR LEFT OVER SCENE CRAP NOW...'
	for each in bad:
		for eachNaughty in cmds.ls(type = each):
			try:
				cmds.delete(eachNaughty)
				print 'Removed %s' % eachNaughty
			except:
				pass

def duplicateNameCheck():
	"""
	This will return True if there is a duplicate name in the scene.
	This scans the entire scene for duplicate names including constraints etc
	"""
	## Delete the set if it already exists
	if cmds.objExists('duplicate_Geo_Names'):
		cmds.delete('duplicate_Geo_Names')

	checkingMessage(checkingWhat = 'DUPLICATE NAMES', start = True,  failed = False)

	allDagNodes = cmds.ls(sn=1,dag=1)
	nonUnique = [ node for node in allDagNodes if '|' in node ]
	if nonUnique != []:
		cmds.select(clear = True)
		for name in nonUnique:
			cmds.select(cmds.ls(name, ap= True), add = True)
		cmds.sets(name = 'Duplicate_Geo_Names')
		cmds.select(clear = True)
		checkingMessage(checkingWhat = 'DUPLICATE NAMES', start = False,  failed = True)
		return False
	else:
		checkingMessage(checkingWhat = 'DUPLICATE NAMES', start = False,  failed = False)
		return True

def _geoSuffixCheck(items):
	"""
	Checks for incorrect suffixes
	@param items: The shotgun items list of dictionaries of groups passed through from the scan scene eg:
					[{'type': 'work_file', 'name': u'BBBBellTowerBLD.v005.ma'}, {'type': 'mesh_group', 'name': u'|BBB_BellTower_BLD_hrc'}]
	@type items: List
	"""
	skipTypes = ['parentConstraint', 'scaleConstraint', 'orientConstraint', 'place3dTexture', 'orientConstraint']
	checkingMessage(checkingWhat = 'SUFFIXES', start = True,  failed = False)
	if cmds.objExists('incorrect_Geo_Suffix'):
		cmds.delete('incorrect_Geo_Suffix')
	badSuffix = []
	#debug(None, method = '_geoSuffixCheck', message = 'items: %s' % items, verbose = False)
	for eachItem in items:
		#debug(None, method = '_geoSuffixCheck', message = 'Checking %s now' % eachItem, verbose = False)
		if eachItem["type"] == 'mesh_group':
			geoGroup = [eachGrp for eachGrp in cmds.listRelatives(eachItem["name"], children = True) if 'geo_hrc' in eachGrp]

			try:
				groups = [eachTransform for eachTransform  in cmds.listRelatives(geoGroup, ad = True, type = 'transform') if not cmds.listRelatives(eachTransform, shapes = True) and cmds.nodeType(eachTransform) not in skipTypes] or []
			except:
				groups = []
			if 1:#try:
				geo = [eachTransform for eachTransform  in cmds.listRelatives(geoGroup, ad = True, type = 'transform') if cmds.listRelatives(eachTransform, shapes = True) and cmds.nodeType(eachTransform) != 'place3dTexture'] or []
				print geo
			else:#except:
				geo = []
			try:
				nurbsCurves = [eachTransform for eachTransform in cmds.listRelatives(geoGroup, ad = True, type = 'nurbsCurve') if cmds.listRelatives(eachTransform, shapes = True)] or []
			except:
				nurbsCurves = []

			## Find Bad
			[badSuffix.append(each) for each in groups if len(each.split('_hrc')) == 1]
			[badSuffix.append(each) for each in geo if len(each.split('_geo')) == 1]
			[badSuffix.append(each) for each in nurbsCurves if len(each.split('_crv')) == 1]

			## Now process the list of bad suffixes. If there are items in this list build a set in maya of these items.
			#print badSuffix
			if len(badSuffix) > 0:
				cmds.select(clear = True)
				[cmds.select(each, add = True) for each in badSuffix]
				cmds.sets(name = 'incorrect_Geo_Suffix')
				cmds.select(clear = True)
				checkingMessage(checkingWhat = 'SUFFIXES', start = False, failed = True)
				return False
			else:
				checkingMessage(checkingWhat = 'SUFFIXES', start = False, failed = False)
				return True
		else:
			pass

def cleanUp(items=[], instanceCheck = True, checkShapes = True, history = True, pivots = True, freezeXFRM = True,
			smoothLvl = True, tagSmoothed = True, checkVerts = True, renderflags = True, deleteIntermediate = True,
			turnOffOpposite = True, shaders = True, hyperLayouts = True, removeNS = False, coreArchives = False,
			defaultRG = True, lightingCleanup = False):
	"""
	Performs a clean up on all the geo found under each item(grp)
	@param items: The shotgun items list of dictionaries of groups passed through from the scan scene eg:
					[{'type': 'work_file', 'name': u'BBBBellTowerBLD.v005.ma'}, {'type': 'mesh_group', 'name': u'|BBB_BellTower_BLD_hrc'}]
	@type items: List
	"""

	## Global scene cleans
	checkingMessage(checkingWhat = 'SHAPENAMES:%s\n HISTORY:%s\n PIVOTS:%s\n \nXFORMS:%s\n SMOOTHLVL1:%s\n TAGSMOOTHED:%s\n VERTS:%s\n RENDERFLAGS:%s\n INTERMEDIATES:%s\n OPPOSITEATTR:%s\n INSTANCES:%s\n SHADERS:%s\n HYPERLAYOUTS:%s\n REMMOVENS:%s\n COREARCHIVES:%s' % (checkShapes, history, pivots, freezeXFRM, smoothLvl, tagSmoothed, checkVerts, renderflags, deleteIntermediate, turnOffOpposite, instanceCheck, shaders,  hyperLayouts, removeNS, coreArchives), start = True,  failed = False)

	start = time.time()
	## New scene cleanup required for the UV exporter...
	_fixUVNames()
	print 'Total time to %s: %s' % ('_fixUVNames', time.time()-start)

	start = time.time()
	## Remove any unknown nodes frome the scene before proceeding
	cleanupUnknown()
	print 'Total time to %s: %s' % ('cleanupUnknown', time.time()-start)

	start = time.time()
	## HYPERLAYOUT ISSUE CLEANUP
	if hyperLayouts:
		cleanHyperLayouts()
	print 'Total time to %s: %s' % ('cleanHyperLayouts', time.time()-start)

	## SHADERS
	if shaders:
		start = time.time()
		## Check for artist shader assignments.
		## If they have imported shaders don't clean up the downgraded shaders in the scene for exporting.
		## NOTE THESE SHOULD BE THE DOWNGRADED SHADERS!!! NOT THE HIGH RES!!
		if not cmds.objExists('dgSHD'):
			debug(None, method = 'cleanUp', message = 'NO dgSHD NODE FOUND!! Cleaning out all shaders now..', verbose = False)
			cleanUpShaders()
			debug(None, method = 'cleanUp', message = 'cleanUpShaders complete...', verbose = False)
		else:
			try:
				debug(None, method = 'cleanUp', message = 'dgSHD node found, cleaning out any mentalCore shaders now leaving only lamberts...', verbose = False)
				cmds.delete(cmds.ls(type = 'core_material'))
				mel.eval("MLdeleteUnused();")
				debug(None, method = 'cleanUp', message = 'dgSHD Cleanup complete...', verbose = False)
			except:
				pass
		print 'Total time to %s: %s' % ('clean shaders', time.time()-start)

	## NAMESPACES
	## Delete any namespaces out of the scene!!
	if removeNS:
		start = time.time()
		removeAllNS()
		print 'Total time to %s: %s' % ('removeAllNS', time.time()-start)

	## CORE ARCHIVES
	## Now if a scene requires coreArchive clean up do those now...
#     if coreArchives:
#         coreLib.cleanupCoreArchiveImports()
#         coreLib.cleanPaintedArchives()
#         coreLib._tagDuplicateCoreArchives()
#         coreLib.prepArchivesForPublish()
#         coreLib.deleteAllCores()

	## GENERAL CLEANUPS
	## Now process the geo groups nodes and cleanup as flagged in the scan scene

	for eachItem in items:
		if eachItem["type"] == 'mesh_group':
			start = time.time()
			debug(None, method = 'cleanUp', message = 'eachItem[type]: %s' % eachItem['type'], verbose = False)
			debug(None, method = 'cleanUp', message = 'eachItem[name]: %s' % eachItem['name'], verbose = False)

			geoGroup = []
			geoGroup = [eachGrp for eachGrp in cmds.listRelatives(eachItem["name"], children = True) if 'geo_hrc' in eachGrp] or []

			if geoGroup == []:## Used for the core_archive publish check
				debug(None, method = 'cleanUp', message = 'geoGroup: is EMPTY!!', verbose = False)
				geoGroup = [eachItem["name"]]
				debug(None, method = 'cleanUp', message = 'geoGroup: %s' % geoGroup, verbose = False)

			## Delete construction history
			if history:
				cmds.delete(geoGroup, ch = True)

			## Look for and fix instance geo!
			## NOTE IF USING THIS YOU SHOULD ALSO CHECK ALL SHAPE NAMES AFTER RUNNING IT
			if instanceCheck:
				checkingMessage(checkingWhat = 'INSTANCES', start = True,  failed = False)
				[instanceChecker(eachGeo) for eachGeo in cmds.listRelatives(geoGroup, ad = True, shapes = False, type = 'transform')]
				checkingMessage(checkingWhat = 'INSTANCES', start = False,  failed = False)

			## Check shape names
			if checkShapes:
				checkShapeNames(eachItem)

			## PIVOTS TO 0,0,0
			if pivots:
				checkingMessage(checkingWhat = 'PIVOTS', start = True,  failed = False)
				[cmds.xform(eachGeo, ws = True, piv = (0, 0, 0), p = True) for eachGeo in cmds.listRelatives(geoGroup, ad = True, shapes = False, type = 'transform')]
				checkingMessage(checkingWhat = 'PIVOTS', start = False,  failed = False)

			## FREEZE XFORMS
			if freezeXFRM:
				checkingMessage(checkingWhat = 'FREEZE XFORMS', start = True,  failed = False)
				[cmds.makeIdentity(eachGeo, apply = True, t = True, r = True, s = True) for eachGeo in cmds.listRelatives(geoGroup, ad = True, shapes = False, type = 'transform')]
				checkingMessage(checkingWhat = 'FREEZE XFORMS', start = False,  failed = False)

			## SET ALL GEO TO SMOOTH LEVEL PREVIEW 1
			if smoothLvl:
				checkingMessage(checkingWhat = 'SMOOTH LVL PREVIEW TO ONE', start = True,  failed = False)
				[cmds.setAttr('%s.smoothLevel' % eachGeo, 1) for eachGeo in cmds.listRelatives(geoGroup, ad = True, type = 'mesh')]
				checkingMessage(checkingWhat = 'SMOOTH LVL PREVIEW TO ONE', start = False,  failed = False)

			## TAG ALL SMOOTH PREVIEW MESHES AS SUBDIV FOR RENDER SUBDIVISIONS OR FALSE IF NOT SMOOTHED
			if tagSmoothed:
				checkingMessage(checkingWhat = 'SUBD TAGS', start = True,  failed = False)
				[tagSubDividedMeshes(eachGeo) for eachGeo in cmds.listRelatives(geoGroup, ad = True, type = 'transform') if '_geo' in eachGeo]
				checkingMessage(checkingWhat = 'SUBD TAGS', start = False,  failed = False)

			## Delete intermediate objects
			if deleteIntermediate:
				checkingMessage(checkingWhat = 'INTERMEDIATES', start = True,  failed = False)
				[deleteIntermediates(eachGeo) for eachGeo in cmds.listRelatives(geoGroup, ad = True, type = 'transform') if '_geo' in eachGeo]
				checkingMessage(checkingWhat = 'INTERMEDIATES', start = False,  failed = False)

			## SET ALL GEO TO BE VISISBLE IN RENDER
			if renderFlags:
				checkingMessage(checkingWhat = 'RENDER FLAGS', start = True,  failed = False)
				try:
					[renderFlags(eachGeo) for eachGeo in cmds.listRelatives(geoGroup, ad = True, type = 'mesh')]
				except:
					pass
				checkingMessage(checkingWhat = 'RENDER FLAGS', start = False,  failed = False)

			 ## TURN OFF OPPOSITE FOR ANY FROZEN GEO SO WE CAN SEE FUCKED NORMALS
			if turnOffOpposite:
				checkingMessage(checkingWhat = 'OPPOSITE', start = True,  failed = False)
				[fixOpposite(eachGeo) for eachGeo in cmds.listRelatives(geoGroup, ad = True, type = 'mesh')]
				checkingMessage(checkingWhat = 'OPPOSITE', start = False,  failed = False)

			## LOOK FOR VERTS UNMERGED ON TOP OF EACH OTHER AND MERGE THEM
			if checkVerts:
				checkingMessage(checkingWhat = 'VERTS', start = True,  failed = False)
				[checkMergedVerts(eachGeo) for eachGeo in cmds.listRelatives(geoGroup, ad = True, type = 'transform') if '_geo' in eachGeo]
				checkingMessage(checkingWhat = 'VERTS', start = False,  failed = False)
			print 'Total time to %s: %s' % ('process all checks for %s' % eachItem["name"], time.time()-start)

	if defaultRG:
		start = time.time()
		## Now set the scene to the default renderer to avoid clashes later on
		cmds.setAttr('defaultRenderGlobals.currentRenderer','mayaSoftware', type = 'string')
		print 'Total time to %s: %s' % ('currentRenderer', time.time()-start)

	if lightingCleanup:
		start = time.time()
		## Cleanup mentalCore passes
		for each in cmds.ls(type = 'core_renderpass'):
			try:
				cmds.delete(each)
			except RuntimeError:
				pass

		badList = ['mentalcoreGlobals', 'mentalcoreLens', 'mia_exposure_simple1', 'mia_physicalsun1', 'mia_physicalsky1', 'sunShape', 'LIGHTS_hrc']
		for each in badList:
			if cmds.objExists(each):
				try:
					cmds.lockNode(each, lock = False)
					cmds.delete(each)
				except RuntimeError:
					pass

		for each in cmds.ls(type='renderLayer'):
			if each != 'defaultRenderLayer':
				try:
					cmds.delete(each)
				except RuntimeError:
					pass
		print 'Total time to %s: %s' % ('lightingCleanup', time.time()-start)
	print '===========DONE!=============='

############CLEAN UP METHODS###################

def instanceChecker(eachGeo):
	"""
	Rip off of the maya instance fix from the modify menu
	Altered to cater for duplicated file names due to core archives
	"""
	getGeos = cmds.ls(eachGeo) ## this will return a list with fullpath to objects if more than one exists in the scene with the same name..
	if not getGeos:
		getGeos = [eachGeo]

	for eachGeo in getGeos:
		try:
			children = cmds.listRelatives(eachGeo, fullPath = True, children = True)
			parents =  cmds.listRelatives(children[0], fullPath = True, allParents = True)
			if len(parents) > 1:
				newDup = cmds.duplicate(eachGeo)
				cmds.delete(eachGeo)
				cmds.rename(newDup, eachGeo.split('|')[-1])
				print 'INSTANCE FIXED: %s to %s' % (newDup[0],  eachGeo.split('|')[-1])
		except TypeError:
			cmds.warning('FAILED: Instance cleanup failed for %s' % eachGeo)
			pass

def fixOpposite(eachGeo):
	"""
	Turn opposite OFF on any geo that may have been frozen to help with flipped normals
	"""
	try:
		if cmds.getAttr('%s.opposite' % eachGeo) == 1:
			cmds.setAttr('%s.opposite' % eachGeo, 0)
			cmds.setAttr('%s.doubleSided' % eachGeo, 1)
	except:
		pass

def checkShapeNames(eachItem):
	"""
	Used to rename any shitty shape names that maya has decided to use
	DO NOT RUN THIS ON A RIGGED GEO!!
	@param eachItem: Shotgun Dict
	@type eachItem: Dictionary
	"""
	checkingMessage(checkingWhat = 'SHAPE NAMES', start = True,  failed = False)
	itemDict = {}
	allItems = cmds.listRelatives(eachItem["name"], ad = True, shapes = False, type = 'transform')
	for eachTransform in allItems:
		try:
			itemDict[eachTransform] = cmds.listRelatives(eachTransform, shapes = True)[0]
		except TypeError:
			pass

	for key,var in itemDict.items():
		if var != '%sShape' % key:
			cmds.rename(var, '%sShape' % key)

	checkingMessage(checkingWhat = 'SHAPE NAMES', start = False,  failed = False)

def deleteIntermediates(eachGeo):
	"""
	Used to delete any intermediate objects that may be attached to the geo still
	DO NOT RUN THIS ON A RIGGED GEO!!
	@param eachGeo: Maya transform
	@type eachGeo: String
	"""
	try:
		[cmds.delete(cmds.ls(eachShape)) for eachShape in cmds.listRelatives(eachGeo, shapes = True) if cmds.getAttr('%s.intermediateObject' % eachShape)]
	except TypeError:
		pass

def checkMergedVerts(eachGeo):
	"""
	Used to find any verts that occupy the same space and merges them. THIS WILL INCREASE PUBLISH TIME!
	DO NOT RUN THIS ON A RIGGED GEO!!
	@param eachGeo: Maya transform
	@type eachGeo: String
	"""
	badVerts = []
	badGeo = []
	toleranceOf = 0.001
	vertCount = cmds.polyEvaluate(eachGeo, v = True)
	myVerts = {}

	try:
		for x in range(0, vertCount):
			myVerts['%s.vtx[%s]' % (eachGeo, x)] = cmds.xform('%s.vtx[%s]' % (eachGeo, x), query = True, translation=True, ws= True)
		dupCheck = []

		for key,var in myVerts.items():
			if not var in dupCheck:
				dupCheck.append(var)
			else:
				badVerts.append(key)
				if eachGeo not in badGeo:
					badGeo.append(eachGeo)
		if len(badGeo) >  0:
			for eachGeo in badGeo:
				cmds.polyMergeVertex(eachGeo, d = toleranceOf, am = 1, ch = 0)
				cmds.select(eachGeo, r = True)
				mel.eval("polyCleanupArgList 3 { \"0\",\"1\",\"0\",\"0\",\"0\",\"0\",\"0\",\"0\",\"0\",\"1e-005\",\"0\",\"1e-005\",\"0\",\"1e-005\",\"0\",\"-1\",\"1\" };")
				print 'Merged verts on %s with a tolerance of %s' % (eachGeo, toleranceOf)
		else:
			pass
	except:
		pass

def setSmoothLevelPreviewOne(eachGeo):
	"""
	Used to set the smooth level preview to 1 not the default 2
	@param eachGeo: Maya Shape Node
	@type eachGeo: String
	"""
	try:
		cmds.setAttr('%s.smoothLevel' % eachGeo, 1)
	except RuntimeError:
		pass

def setAllSmoothPreviews(state = 0):
	"""
	Function to turn the state for all the smooth mesh previews
	valid states are 0 1 2  = off, cage+smoothed, smoothed
	"""
	cmds.displaySmoothness(cmds.ls(type = 'mesh'), polygonObject = state)

def setRiggedSmoothPreviews():
	for each in cmds.ls(type = 'mesh'):
		getTransform = cmds.listRelatives(each, parent = True)[0]
		if cmds.objExists('%s.smoothed' % getTransform):
			if cmds.getAttr('%s.smoothed' % getTransform):
				cmds.displaySmoothness(getTransform, polygonObject = 3)
				setSmoothLevelPreviewOne(getTransform)

def tagSubDividedMeshes(eachGeo):
	"""
	Used to TAG ALL SMOOTH PREVIEW MESHES AS SUBDIV FOR RENDER SUBDIVISIONS OR FALSE IF NOT SMOOTHED
	@param eachGeo: Maya transform
	@type eachGeo: String
	"""
	getShape = None
	try:
		getShape = cmds.listRelatives(eachGeo, shapes = True)[0]
	except:
		pass
	if getShape:
		try:
			if cmds.getAttr('%s.displaySmoothMesh' % getShape):
				if cmds.objExists('%s.smoothed' % eachGeo):
					cmds.deleteAttr('%s.smoothed' % eachGeo)
				if cmds.objExists('%s.Smoothed' % eachGeo):
					cmds.deleteAttr('%s.Smoothed' % eachGeo)
				try:
					cmds.addAttr(eachGeo, ln = 'smoothed', at = 'bool')
				except:
					pass
				cmds.setAttr('%s.smoothed' % eachGeo, 1)
			else:
				if cmds.objExists('%s.smoothed' % eachGeo):
				   cmds.deleteAttr('%s.smoothed' % eachGeo)
				if cmds.objExists('%s.Smoothed' % eachGeo):
					cmds.deleteAttr('%s.Smoothed' % eachGeo)
				try:
					cmds.addAttr(eachGeo, ln = 'smoothed', at = 'bool')
				except:
					pass
				cmds.setAttr('%s.smoothed' % eachGeo, 0)
		except ValueError:
			pass

def renderFlags(eachGeo):
	"""
	Used to set the default render flags back to all ON cause fucking maya keeps trying to turn them off! GAH
	@param eachGeo: Maya Shape Node
	@type eachGeo: String
	"""
	attrs = ['castsShadows', 'receiveShadows', 'motionBlur', 'primaryVisibility', 'smoothShading', 'visibleInReflections', 'visibleInRefractions', 'doubleSided' ]
	for eachAttr in attrs:
		cmds.setAttr('%s.%s' % (eachGeo, eachAttr), 1)

def assetCheckAndTag(type = '', customTag = False):
	"""
	Look for root level groups that have meshes as children and add a a type flag to it with the type as its value
	@param type: The type of asset, eg PROP, BLD, CHAR
	@type type: String
	"""

	for grp in cmds.ls(assemblies=True, long= True):
		if cmds.ls(grp, dag=True, type="mesh"):
			if '|ROOT_ARCHIVES_DNT_hrc' not in grp and '|CORE_ARCHIVES_hrc' not in grp:
				debug(app = None, method = 'assetCheckAndTag', message = 'grp: %s' % grp, verbose = False)
				if not grp.endswith('_hrc'):
					return False
				if type not in grp:
					raise TankError("ROOT NODE MISSING PREFIX \"%s_\"\nPlease visit http://www.anim83d.com/bbb/dokuwiki/doku.php?id=bubblebathbay:pipeline:pipeline:modelling:namingconventions" % type)
				if '_hrc' in grp and type in grp:
					if cmds.objExists('%s.type' % grp):
						cmds.deleteAttr('%s.type' % grp)
					try:
						cmds.addAttr(grp, ln = 'type', dt = 'string')
					except:
						pass
					if customTag:
						cmds.setAttr('%s.type' % grp, customTag, type = 'string')
					else:
						cmds.setAttr('%s.type' % grp, type.lower(), type = 'string')
				else:
					 raise TankError("This does not appear to be a valid %s asset" % type)

def tag_SHD_LIB_Geo(root = 'geo_hrc'):
	"""
	Look for root childrens transforms and then tag them all with two attrs
	One for the original objects name as this may change during the modelling stage
	And one for the path to the original XML file it came from
	"""
	for eachGeo in cmds.listRelatives(root, ad = True, type = 'transform'):
		try:
			cmds.addAttr(eachGeo, ln = 'LIBSHDXML', dt = 'string')
		except:
			pass
		try:
			cmds.addAttr(eachGeo, ln = 'LIBORIGNAME', dt = 'string')
		except:
			pass

			getAssetRootPath = '%s/SRF/publish/xml' % "/".join(cmds.file(query = True, sn = True).split('/')[:5])
			getLatestPublish = max(os.listdir(getAssetRootPath))
			xml_publish_path = '%s/%s' % (getAssetRootPath, getLatestPublish)
			debug(None, method = 'tag_SHD_LIB_Geo', message = 'getAssetRootPath: %s' % getAssetRootPath, verbose = False)
			debug(None, method = 'tag_SHD_LIB_Geo', message = 'getLatestPublish: %s' % getLatestPublish, verbose = False)

			cmds.setAttr('%s.LIBSHDXML' % eachGeo, xml_publish_path, type = 'string')
			cmds.setAttr('%s.LIBORIGNAME' % eachGeo, eachGeo, type = 'string')

def rigGroupCheck():
	## Do a quick check for a rig_hrc group, and if it is there bail out before any dmg is done to the opened scene.
	rigGroup = False
	for grp in cmds.ls(assemblies=True, long= True):
		if cmds.ls(grp, dag=True, type="mesh"):
			## Now check the master group found. We're looking for a rig_hrc grp
			for eachChild in cmds.listRelatives(grp, children = True):
				if 'rig_hrc' in eachChild:
					rigGroup = True
	return rigGroup

def BLDTransformCheck(grp):
	## CHECK the group to make sure it's not frozen!
	getTrans = cmds.xform(grp, query = True, translation = True)
	getRot = cmds.xform(grp, query = True, rotation = True)
	getScale = cmds.xform(grp, query = True, scale = True)
	all = getTrans + getRot + getScale
	total = 0
	for each in all:
		total = total + each
	if total == 3:
		raise TankError("Your root transform group doesn't have any transform information.\n This will result in a bad bounding box. To Fix use the location zero helper tools.")
	elif getScale[0] + getScale[1] + getScale[2] != 3:
		raise TankError("Freeze Scale on your root transform group!.")
	else:
		return True

def cleanHyperLayouts():
	checkingMessage(checkingWhat = 'HYPERLAYOUTS, HYPERGRAPHINFO, HYPERVIEW', start = True,  failed = False)
	bad = ['hyperLayout', 'hyperGraphInfo']
	safeHyperViews = []
	for each in bad:
		#print 'Checking %s now...'% each
		getAll = cmds.ls(type = each)
		for eachNaughty in getAll:
			getConnections = cmds.listConnections(eachNaughty)
			if getConnections:
				if not 'dgSHD' in getConnections:
					if not 'ADef_ARef' in getConnections[0]:
						#print 'Removed %s' % eachNaughty
						cmds.delete(eachNaughty)
					else:
						cmds.rename(eachNaughty, '%s_%s' % (getConnections[0], eachNaughty))
						#print 'Renamed %s_hyperLayout' % (getConnections[0])
				else:
					safeHyperViews.append(cmds.listConnections(eachNaughty)[0])
					#print cmds.listConnections(eachNaughty)

	#===========================================================================
	# getAll = cmds.ls(type = 'hyperView')
	# print 'Checking hyperView now...'
	# for eachNaughty in getAll:
	#     if not eachNaughty in safeHyperViews:
	#         #print 'Removed %s' % eachNaughty
	#         pass
	#===========================================================================
	checkingMessage(checkingWhat = 'HYPERLAYOUTS, HYPERGRAPHINFO, HYPERVIEW', start = False,  failed = False)

def turnOffModelEditors():
	"""
	Turns off all modelEditors in maya
	"""
	mel.eval('cycleCheck -e off;')

	for editor in cmds.lsUI(panels= True):
		if cmds.objectTypeUI(editor)=='modelEditor':
			print 'Turning off %s' % editor
			cmds.modelEditor(editor, edit = True, allObjects = False)
	for editor in cmds.lsUI(editors= True):
		if 'BB_myMayaEditor' in editor:
			print 'Turning off %s' % editor

	## check for height fields that need to be turned of manually as they still display
	heightFields = cmds.ls(type = 'heightField')
	for eachHF in heightFields:
		try:
			cmds.setAttr('%s.visibility' % eachHF, 0)
		except:
			pass

def turnOnModelEditors():
	"""
	Turns on all modelEditors in maya
	"""
	for editor in cmds.lsUI(panels= True):
		if cmds.objectTypeUI(editor)=='modelEditor':
			print 'Turning on %s' % editor
			cmds.modelEditor(editor, edit = True, allObjects = True)
	for editor in cmds.lsUI(editors= True):
		if 'BB_myMayaEditor' in editor:
			print 'Turning on %s' % editor
			cmds.modelEditor(editor, edit = True, allObjects = True)
			cmds.modelEditor(editor, edit = True, allObjects = False)

	## check for height fields that need to be turned of manually as they still display
	heightFields = cmds.ls(type = 'heightField')
	for eachHF in heightFields:
		try:
			cmds.setAttr('%s.visibility' % eachHF, 1)
		except:
			pass