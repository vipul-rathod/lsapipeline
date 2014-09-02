#######################################################################################################
#  FromMaya2Nuke V1.5 - Date: 04.11.2010 - Created by Jan Oberhauser - jan.oberhauser@gmail.com       #
#  Exports Polygon-Objects, Cameras, Lights and Locators to Nuke                                      #
#  Check for a updateted Version at http://janoberhauser.gute-filme-enden-nie.de                      #
#######################################################################################################


#Imports the necessary stuff
import maya.cmds as cmds
import maya.mel as melCmd
import os, sys
import subprocess
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug

class FromMaya2Nuke:
	def __init__(self, exportPath, nukePath, nukeExec, scriptName, startFrame, endFrame, camera = ''):
		#System Specific - Please change that it matches your System. Please use Slash instead of Backslash!!!
		#self.nukePath = '/Applications/Nuke6.1v2-32/Nuke6.1v2.app/Contents/MacOS/'
		self.nukePath = nukePath#'C:/Program Files/Nuke6.1v1/'
		debug(app = None, method = 'FromMaya2Nuke.__init__', message = 'self.nukePath: %s' % self.nukePath, verbose = False)
		
		#self.nukeExec = 'Nuke6.1v2'
		self.nukeExec = nukeExec#'Nuke6.1.exe'
		self.showUI = False #Show UI-Window or just take default-Values

		#Sets Default-Values
		self.defaultExportPath = exportPath#'C:/Users/jober/Desktop/maya2nuke/'
		debug(app = None, method = 'FromMaya2Nuke.__init__', message = 'self.defaultExportPath: %s' % self.defaultExportPath, verbose = False)

		self.defaultNukeExportScriptName = '%s.nk' % scriptName#'NukeScene.nk'
		debug(app = None, method = 'FromMaya2Nuke.__init__', message = 'self.defaultNukeExportScriptName: %s' % self.defaultNukeExportScriptName, verbose = False)

		self.defaultExportTypeValue = 1 #Preset Export-Type - Values(1-> FBX, 2->OBJ)
		self.defaultExportGeometrySequence = False #Preset Export Geometry Sequence - Values(True,False) - Case-Sensetive
		self.defaultCreateDiffuseShader = False #Preset Create Diffuse-Shader for each exported Geometry - Values(True,False) - Case-Sensetive
		self.defaultCreateNukeScript = True #Preset Create Nuke-Script - Values(True,False) - Case-Sensetive
		self.defaultOpenNukeScript = False #Preset Open Nuke-Script - Values(True,False) - Case-Sensetive
		self.defaultDeleteExportFiles = True #Preset Delete Export-Files - Values(True,False) - Case-Sensetive
		self.defaultStartFrameValue = int(startFrame)#int(cmds.playbackOptions(query=True, min= True))
		self.defaultEndFrameValue = int(endFrame)#int(cmds.playbackOptions(query=True, max= True))	
		
		self.selected = cmds.ls( selection=True, type='transform')
		debug(app = None, method = 'FromMaya2Nuke.__init__', message = 'self.selected: %s' % self.selected, verbose = False)
			
		if len(self.selected) == 0:
			cmds.confirmDialog(title="FromMaya2Nuke - ERROR", message="Nothing is selected.\nPlease select the Objects, Cameras, Lights and Locators you want to export.\n", button="OK")
		else:
			self.objects = []
			self.cameras = []
			self.lights = []
			self.locators = []
			self.newCameras = []
			if self.showUI == True:
				self.showParameterWindow()
			else:
				self.startExportProcedure()
				
	def startExportProcedure(self, arg=None):
		frameScriptStart = cmds.currentTime( query=True )
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'frameScriptStart: %s' % frameScriptStart, verbose = False)
		
		if self.showUI == True:
			self.startFrame = int(cmds.textFieldGrp(self.startFrameField, text=True, query= True))
			self.endFrame = int(cmds.textFieldGrp(self.endFrameField, text=True, query= True))
			self.createDiffuseShader = cmds.checkBox(self.createDiffuseShaderField, value=True, query=True )
			self.exportGeometrySequence = cmds.checkBox(self.exportGeometrySequenceField, value=True, query=True )
			self.createNukeScript = cmds.checkBox(self.createNukeScriptField, value=True, query=True )
			self.openNukeScript = cmds.checkBox(self.openNukeScriptField, value=True, query=True )
			self.deleteExport = cmds.checkBox(self.deleteExportFilesField, value=True, query=True )
			self.nukeExportScriptName = str(cmds.textFieldGrp(self.nukeExportScriptNameField, text=True, query= True))
			self.exportPath = str(cmds.textFieldGrp(self.exportPathField, text=True, query= True))
			self.exportType = int(cmds.radioButtonGrp(self.exportTypeField, select=True, query= True))
		else:
			self.startFrame = self.defaultStartFrameValue
			self.endFrame = self.defaultEndFrameValue
			self.createDiffuseShader = self.defaultCreateDiffuseShader
			self.exportGeometrySequence = self.defaultExportGeometrySequence
			self.createNukeScript = self.defaultCreateNukeScript
			self.openNukeScript = self.defaultOpenNukeScript
			self.deleteExport = self.defaultDeleteExportFiles
			
			self.nukeExportScriptName = self.defaultNukeExportScriptName
			debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.nukeExportScriptName: %s' % self.nukeExportScriptName, verbose = False)
			
			self.exportPath = self.defaultExportPath
			debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.exportPath: %s' % self.exportPath, verbose = False)
			
			self.exportType = self.defaultExportTypeValue		
		
		self.exportPath = self.exportPath.replace('\\', '/')
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.exportPath: %s' % self.exportPath, verbose = False)
		
		if self.exportPath[len(self.exportPath)-1] != '/':
			self.exportPath += '/'
		
		if self.showUI == True:
			cmds.deleteUI(self.parWindow);

# 		if (os.path.isdir(self.exportPath) == 0):
# 			os.mkdir(self.exportPath)
		
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.readObjects processing now...', verbose = False)
		self.readObjects()
		
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.createFreeCameras processing now...',  verbose = False)
		self.createFreeCameras() 
		
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.exportObjects processing now...',  verbose = False)
		self.exportObjects()
		
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.exportCameras processing now...',  verbose = False)
		self.exportCameras()
		
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.exportLights processing now...',  verbose = False)
		self.exportLights()
		
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.exportLocators processing now...',  verbose = False)
		self.exportLocators()
		
		if self.createNukeScript == True:
			debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.createNukePythonFile processing now...',  verbose = False)
			self.createNukePythonFile()
		 
		self.deleteFreeCameras()
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.deleteFreeCameras processed successfully...',  verbose = False)
		
# # 		if self.deleteExport == True:
# # 			debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.deleteExport processing...',  verbose = False)
# # 			#self.delteCameraFiles()
# # 			self.delteLightFiles()
# # 			self.delteLocatorFile()
		
# 		if self.createNukeScript == True:
# 			debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'self.delteNukePythonFile processing now...',  verbose = False)
# 			self.delteNukePythonFile()			
# 		if self.openNukeScript == True and self.createNukeScript == True:
# 			self.openNukeScriptAfterwards()
		self.restoreSelection()
		cmds.currentTime(frameScriptStart)
		debug(app = None, method = 'FromMaya2Nuke.startExportProcedure', message = 'COMPLETE',  verbose = False)

	def restoreSelection(self):
		debug(app = None, method = 'FromMaya2Nuke.restoreSelection', message = 'self.selected:%s' % self.selected,  verbose = False)
		cmds.select(eval('\'' + '\',\''.join(self.selected) + '\''))

	def showParameterWindow(self):

		self.parWindow = cmds.window(title="FromMaya2Nuke - Export", widthHeight=(400,400) )
		
		column1 = cmds.columnLayout( columnAttach=('both', 5), rowSpacing=10, columnWidth=400, adjustableColumn=True )
		
		row1 = cmds.rowLayout( p=column1, numberOfColumns=3, columnWidth3=(150, 125, 125), columnAlign3=('right', 'left', 'left'), columnAttach=[(1, 'both', 0), (2, 'both', 0), (3, 'both', 0)] )
		cmds.text( label='Export Framerange:', align='left' )
		self.startFrameField = cmds.textFieldGrp( label='Start', columnWidth2=[60, 65], text=self.defaultStartFrameValue)
		self.endFrameField = cmds.textFieldGrp( label='End', columnWidth2=[60, 65], text=self.defaultEndFrameValue)
		
		column2 = cmds.columnLayout(p=column1, columnAttach=('both', 5), rowSpacing=10, columnWidth=400)
		self.exportPathField = cmds.textFieldGrp( label='Export Path:', columnWidth2=[150, 250], text=self.defaultExportPath)
		self.nukeExportScriptNameField = cmds.textFieldGrp( label='Export Script-Name:', columnWidth2=[150, 250], text=self.defaultNukeExportScriptName)
		self.exportTypeField = cmds.radioButtonGrp( label='Export Geometry as:', labelArray2=['FBX', 'OBJ'], numberOfRadioButtons=2, select=self.defaultExportTypeValue )
		self.exportGeometrySequenceField = cmds.checkBox( label='Export Geometry animated (as Geometry-Sequence)', value=self.defaultExportGeometrySequence, align='left' )
		self.createNukeScriptField = cmds.checkBox( label='Create Nuke-Script', value=self.defaultCreateNukeScript, align='left' )
		self.openNukeScriptField = cmds.checkBox( label='Open Nuke-Script after Export', value=self.defaultOpenNukeScript, align='left' )
		self.createDiffuseShaderField = cmds.checkBox( label='Create Diffuse-Shader for Geometry in Nuke-Script', value=self.defaultCreateDiffuseShader, align='left')
		self.deleteExportFilesField = cmds.checkBox( label='Delete Export-Files (.fm2n-Files) after Export', value=self.defaultDeleteExportFiles, align='left' )
		
		exportButton = cmds.button(label='Export', command=self.startExportProcedure)
		
		cmds.showWindow(self.parWindow)

	def deleteFreeCameras(self):
		debug(app = None, method = 'FromMaya2Nuke.deleteFreeCameras', message = 'self.newCameras:%s' % self.newCameras,  verbose = False)
		for camera in self.newCameras:
			try:
				cmds.delete(camera)
			except:
				cmds.warning('Cannot find %s skipping deletion....' % camera)
	
	def createFreeCameras(self):
		debug(app = None, method = 'FromMaya2Nuke.createFreeCameras', message = 'self.cameras: %s' % self.cameras, verbose = False)
		
		for camera in self.cameras:
			debug(app = None, method = 'FromMaya2Nuke.createFreeCameras', message = 'Processing camera: %s' % camera, verbose = False)
			cmds.select(camera, r= True)
		  
			newCamera = cmds.duplicate( rr=True )
			newCamera = newCamera[0]
			
			debug(app = None, method = 'FromMaya2Nuke.createFreeCameras', message = 'newCamera: %s' % newCamera, verbose = False)
			for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']:
				cmds.setAttr(newCamera + "." + attr, lock=False)
			
			hisObject = cmds.listHistory(newCamera)
			for attr in ['hfa', 'vfa', 'fl', 'lsr', 'fs', 'fd', 'sa', 'coi']:
				cmds.setAttr(hisObject[0] + "." + attr, lock=False)	
			
			parentNode = cmds.listRelatives(camera, p= True)
			if parentNode != None:
				cmds.parent( newCamera, world= True)
      
			pointConst = cmds.pointConstraint( camera, newCamera )
			orientConst = cmds.orientConstraint( camera, newCamera )
      
			cmds.bakeResults( newCamera+'*', t=(self.startFrame, self.endFrame), simulation=True, sparseAnimCurveBake=False, shape=False)
			debug(app = None, method = 'FromMaya2Nuke.createFreeCameras', message = 'newCamera %s baked successfully...' % newCamera, verbose = False)
			
			cmds.delete(pointConst, orientConst, cn=True )
			
			newCameraName = cmds.rename(newCamera, '%s_Cpy' % camera)
			debug(app = None, method = 'FromMaya2Nuke.createFreeCameras', message = 'newCameraName: %s' % newCameraName, verbose = False)

			self.newCameras.extend([newCameraName])
			debug(app = None, method = 'FromMaya2Nuke.createFreeCameras', message = 'self.newCameras: %s' % self.newCameras, verbose = False)
  
	def readObjects(self):
		for object in self.selected:
			hisObject = cmds.listHistory(object)
			lightTypes = ['pointLight', 'directionalLight', 'spotLight']
			thisNodeType = cmds.nodeType(hisObject[0])
			if thisNodeType == 'camera':
				self.cameras[:0] = [object]
			if thisNodeType in lightTypes:
				self.lights[:0] = [object]
			if thisNodeType == 'mesh':
				self.objects[:0] = [object]
			if thisNodeType == 'locator':
				self.locators[:0] = [object]
        
	def exportObjects(self):
		for object in self.objects:
			cmds.select(object, r= True)
	
			if self.exportType == 1:
				fileType = 'Fbx'
				cmds.loadPlugin('fbxmaya', qt= True)
				melCmd.eval('FBXExportShowUI -v false;')
			else:
			  fileType = 'OBJexport'
			  cmds.loadPlugin('objExport', qt= True)
			
			if bool(self.exportGeometrySequence) == bool(True):
				startF = self.startFrame
				endF = self.endFrame 
			else:
				startF = endF = cmds.currentTime( query=True )
			
			nameExtension = ''
			exportName = object.replace(':', '_')
			
			for timevalue in range(startF, (endF+1), 1):
				if bool(self.exportGeometrySequence) == bool(True):
					nameExtension = '.%04d' % timevalue 
				cmds.currentTime(timevalue)
				if self.exportType == 1:
					melCmd.eval('FBXExport -f "' + self.exportPath + exportName + nameExtension + '.fbx" -s')
				else:
					cmds.file(self.exportPath+exportName+nameExtension, op='', typ=fileType, pr=True, es=True )  

			print 'Exported: ' + object;

	def exportLocators(self):
		parameters = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'rotateOrder']
		for locator in self.locators:				
			hisObject = cmds.listHistory(locator)
			exportName = locator.replace(':', '_')
			
			self.exportData(locator, parameters, self.startFrame, self.endFrame+1, self.exportPath + exportName + '.fm2n')
			
			print 'Saved data from: ' + locator

	def exportCameras(self):
		parameters = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'rotateOrder', 'camera:fl', 'camera:horizontalFilmAperture', 'camera:verticalFilmAperture']
		for camera in self.newCameras:				
			hisObject = cmds.listHistory(camera)
			
			exportCamName = camera[:-4]
			hisObjectOld = cmds.listHistory(exportCamName)
			
			exportName = exportCamName.replace(':', '_')
																				
			horAper = cmds.getAttr(camera+".horizontalFilmAperture")
			cmds.setAttr(camera+".horizontalFilmAperture", horAper*25.4)
			verAper = cmds.getAttr(camera+".verticalFilmAperture")
			cmds.setAttr(camera+".verticalFilmAperture", verAper*25.4)
			 
			isAnimated = cmds.listConnections(str(exportCamName) + '.focalLength')
			if isAnimated != None:
				cmds.expression(s=hisObject[0] + ".focalLength = " + hisObjectOld[0] + ".focalLength", o=hisObject[0], n=hisObject[0] + ".focalLength", uc='all')

			self.exportData(camera, parameters, self.startFrame, self.endFrame+1, self.exportPath + exportName + '.fm2n')
			
			print 'Saved data from: ' + camera[:-4]

	def exportLights(self):
		for light in self.lights:			
			
			hisObject = cmds.listHistory(light)
			hisObject = hisObject[0]
			
			exportName = light.replace(':', '_')
			
			thisNodeType = cmds.nodeType(hisObject)
			parameters = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'cr', 'cg', 'cb', 'intensity', 'rotateOrder']
			
			if thisNodeType == 'spotLight':
				writeOutType = 'spot'
				parameters.append('coneAngle')
				parameters.append('penumbraAngle')
				parameters.append('dropoff')
			if thisNodeType == 'pointLight':
				writeOutType = 'point'
			if thisNodeType == 'directionalLight':
				writeOutType = 'directional'
												
			for i in range(self.startFrame, self.endFrame+1):
				if thisNodeType == 'spotLight': 
					lightConeAngle = cmds.getAttr(hisObject + '.coneAngle',time=i)
					lightPenumbraAngle = cmds.getAttr(hisObject + '.penumbraAngle',time=i)
					lightDropoff = cmds.getAttr(hisObject + '.dropoff',time=i)
				else:
					lightConeAngle = 0
					lightPenumbraAngle = 0
					lightDropoff = 0					
				
				self.exportData(light, parameters, self.startFrame, self.endFrame+1, self.exportPath + exportName + '.fm2n')

			print 'Saved data from: ' + light
	
	def delteCameraFiles(self):
		for camera in self.cameras:
			objectFileName = camera.replace(':', '_')
			os.remove(self.exportPath + objectFileName + '.fm2n')

	def delteLightFiles(self):
		for light in self.lights:
			objectFileName = light.replace(':', '_')
			os.remove(self.exportPath + objectFileName + '.fm2n')

	def delteLocatorFile(self):
		for locator in self.locators:
			objectFileName = locator.replace(':', '_')
			os.remove(self.exportPath + objectFileName + '.fm2n')

	def createNukePythonFile(self):

		nukePyFile = "def importData(importFile, channelMatch):\n\
	#Open File\n\
	file = open(importFile, 'r')\n\
	\n\
	#Read first Line\n\
	line = file.readline()\n\
	\n\
	values = line.split('\\t')\n\
	objectName = values[0]\n\
	objectNodeType = values[1]\n\
	if objectNodeType != 'camera' and objectNodeType != 'locator':\n\
		eval(objectName)['light_type'].setValue (objectNodeType)\n\
	\n\
	\n\
	###########################################################################################\n\
	# START - Read all the static channel values                                              #\n\
	###########################################################################################\n\
	line = file.readline()\n\
	while line[:18] != \'+++++Animated+++++':\n\
		#Split apart into channel and value\n\
		values = line.split('\\t')\n\
		\n\
		#Get the DestinationChannel - 0-> Channel, 1-> ChannelIndex\n\
		destinationChannel = channelMatch[values[0]].split(':')\n\
		\n\
		if destinationChannel[0] == 'rot_order':\n\
			eval(objectName)[destinationChannel[0]].setValue(values[1])\n\
		elif len(destinationChannel) == 2:\n\
			eval(objectName)[destinationChannel[0]].setValue(float(values[1]), int(destinationChannel[1]))\n\
		else:\n\
			eval(objectName)[destinationChannel[0]].setValue(float(values[1]))\n\
		\n\
		#Read next Line\n\
		line = file.readline()\n\
	\n\
	###########################################################################################\n\
	# START - Read all the ANIMATED channel values                                            #\n\
	###########################################################################################\n\
	line = file.readline()\n\
	destinationChannels = line.split('\\t')\n\
	destinationChannels[len(destinationChannels)-1] = destinationChannels[len(destinationChannels)-1].replace('\\n', '')\n\
	\n\
	row = 0\n\
	for channel in destinationChannels:\n\
		if row > 0:\n\
			destinationChannel = channelMatch[channel].split(':')\n\
			if len(destinationChannel) == 1:\n\
				eval(objectName)[destinationChannel[0]].setAnimated()\n\
			else:\n\
				eval(objectName)[destinationChannel[0]].setAnimated(int(destinationChannel[1]))\n\
		row += 1\n\
	\n\
	line = file.readline()\n\
	while True:\n\
		values = line.split('\\t')\n\
	\n\
		row = 0\n\
		for value in values:\n\
			if row == 0:\n\
				timevalue = value\n\
			else:\n\
				destinationChannel = channelMatch[destinationChannels[row]].split(':')\n\
				\n\
				if len(destinationChannel) == 2:\n\
					eval(objectName)[destinationChannel[0]].setValueAt(float(value), int(timevalue), int(destinationChannel[1]))\n\
				else:\n\
					eval(objectName)[destinationChannel[0]].setValueAt(float(value), int(timevalue))\n\
			\n\
			row += 1\n\
		\n\
		line = file.readline()\n\
		if line == '':\n\
			file.close()\n\
			break\n\n\n"

		sceneInput = -1
		nukePyFile += '#Create Scene\n\
nuke.root().knob(\'first_frame\').setValue(' + str(self.startFrame) + ')\n\
nuke.root().knob(\'last_frame\').setValue(' + str(self.endFrame) + ')\n\
\n\
scene = nuke.nodes.Scene()\n\
\n\
#Creates Background-Constant\n\
background1 = nuke.nodes.Constant()\n\
background1[\'format\'].setValue(\'HD\')\n\
\n'
 		
		if self.exportType == 1:
			fileExtension = 'fbx'
		else:
		  fileExtension = 'obj'
		for object in self.objects:
			importName = object.replace(':', '_')
			sceneInput += 1
			if bool(self.exportGeometrySequence) == bool(True):
				nameExtension = '.%04d'
			else:
				nameExtension = ''
				
			nukePyFile += '#Creates Geometry-Objects and connects them to Scene\n\
' + importName + ' = nuke.nodes.ReadGeo(file=\'' + self.exportPath + importName + nameExtension + '.' + fileExtension + '\')\n\
\n'

			if bool(self.createDiffuseShader) == bool(True):
				nukePyFile += importName + 'ApplyMat = nuke.nodes.ApplyMaterial()\n\
' + importName + 'ApplyMat.setInput(0, ' + importName + ')\n\
' + importName + 'Diffuse = nuke.nodes.Diffuse()\n\
' + importName + 'ApplyMat.setInput(1, ' + importName + 'Diffuse)\n\
scene.setInput(' + str(sceneInput) + ',' + importName + 'ApplyMat)\n\n'
			else:
				nukePyFile += importName + 'background = nuke.nodes.Constant()\n\
' + importName + 'background[\'color\'].setValue(1)\n\
' + importName + 'background[\'format\'].setValue(\'HD\')\n\
' + importName + '.setInput(0, ' + importName + 'background)\n\
scene.setInput(' + str(sceneInput) + ',' + importName + ')\n\n' 		

		nukePyFile += 'channelMatch = {\'transform.tx\':\'translate:0\', \'transform.ty\':\'translate:1\', \'transform.tz\':\'translate:2\', \'transform.rx\':\'rotate:0\', \'transform.ry\':\'rotate:1\', \'transform.rz\':\'rotate:2\', \'transform.sx\':\'scaling:0\', \'transform.sy\':\'scaling:1\', \'transform.sz\':\'scaling:2\', \'transform.rotateOrder\':\'rot_order\', \'transform.intensity\':\'intensity\', \'transform.cr\':\'color:0\', \'transform.cg\':\'color:1\', \'transform.cb\':\'color:2\', \'transform.coneAngle\':\'cone_angle\', \'transform.penumbraAngle\':\'cone_penumbra_angle\', \'transform.dropoff\':\'cone_falloff\'}\n'
		for light in self.lights:
			importName = light.replace(':', '_')
			sceneInput += 1
			nukePyFile += '#Creates Cameras and connects them with ScanlineRender\n\
' + importName + ' = nuke.nodes.Light2()\n\
' + importName + '[\'name\'].setValue("' + importName + '")\n\
scene.setInput(' + str(sceneInput) + ',' + importName + ')\n\n\
\n\
#IMPORT LIGHT-VALUES\n\
importData(\'' + self.exportPath + importName + '.fm2n\', channelMatch)\n\n'		

		for camera in self.cameras:
			importName = camera.replace(':', '_')
			nukePyFile += '#Creates Cameras and connects them with ScanlineRender\n\
channelMatch = {\'transform.tx\':\'translate:0\', \'transform.ty\':\'translate:1\', \'transform.tz\':\'translate:2\', \'transform.rx\':\'rotate:0\', \'transform.ry\':\'rotate:1\', \'transform.rz\':\'rotate:2\', \'transform.sx\':\'scaling:0\', \'transform.sy\':\'scaling:1\', \'transform.sz\':\'scaling:2\', \'transform.rotateOrder\':\'rot_order\', \'camera.fl\':\'focal\', \'camera.horizontalFilmAperture\':\'haperture\', \'camera.verticalFilmAperture\':\'vaperture\'}\n\
\n\
' + importName + ' = nuke.nodes.Camera()\n\
' + importName + '[\'name\'].setValue("' + importName + '")\n\
\n\
#Creates ScanlineRender and connects it with Scene\n\
' + importName + 'Render = nuke.nodes.ScanlineRender()\n\
#' + importName + 'Render.setXYpos(' + importName + 'Render[\'xpos\'].getValue(), ' + importName + 'Render[\'ypos\'].getValue()+400)\n\
' + importName + 'Render.setInput(1,scene)\n\
' + importName + 'Render.setInput(0,background1)\n\n\
' + importName + 'Render.setInput(2,' + importName + ')\n\
\n\
\n\
#IMPORT CAMERA-VALUES\n\
filename = \'' + self.exportPath + importName + '.fm2n\'\n\
importData(filename, channelMatch)\n\n'

		if len(self.locators) > 0:
			sceneInput += 1
			nukePyFile += '#Create Null to connect all Locators\n\
sceneLocatorInput = -1\n\
sceneLocator = nuke.nodes.Scene()\n\
channelMatch = {\'transform.tx\':\'translate:0\', \'transform.ty\':\'translate:1\', \'transform.tz\':\'translate:2\', \'transform.rx\':\'rotate:0\', \'transform.ry\':\'rotate:1\', \'transform.rz\':\'rotate:2\', \'transform.sx\':\'scaling:0\', \'transform.sy\':\'scaling:1\', \'transform.sz\':\'scaling:2\', \'transform.rotateOrder\':\'rot_order\'}\n\n'

			for locator in self.locators:
				importName = locator.replace(':', '_')
				nukePyFile += '#Creates Locators and connects them with Scene-Node\n\
\n\
' + importName + ' = nuke.nodes.Axis()\n\
' + importName + '[\'name\'].setValue("' + importName + '")\n\
\n\
sceneLocatorInput += 1\n\
sceneLocator.setInput(sceneLocatorInput,' + importName + ')\n\n\
\n\
\n\
#IMPORT LOCATOR-VALUES\n\
filename = \'' + self.exportPath + importName + '.fm2n\'\n\
importData(filename, channelMatch)\n\n\
scene.setInput(' + str(sceneInput) + ',sceneLocator)\n\
\n'

		if len(self.cameras) > 0:
			importName = camera.replace(':', '_')
			nukePyFile += '#Create Viewer-Node\n\
viewer = nuke.nodes.Viewer()\n\
viewer.setInput(0, ' + importName + 'Render)\n'

		nukePyFile += '#Save Nuke-Script\n\
nuke.scriptSave( \'' + self.exportPath + self.nukeExportScriptName + '\')\n'

		nukePyFile += 'sys.exit(0)\n'

		f = open('%s%s' % (self.exportPath, self.nukeExportScriptName.replace('.nk', '.py')), 'w')
		f.write(nukePyFile.encode('ascii', 'xmlcharrefreplace') )
		f.close()
		
		debug(app = None, method = 'FromMaya2Nuke.createNukePythonFile', message = 'WROTE: %s%s' % (self.exportPath, self.nukeExportScriptName.replace('.nk', '.py')),  verbose = False)
		systemCommand = '\"%s%s -t < %s%s\"' % (self.nukePath, self.nukeExec, self.exportPath, self.nukeExportScriptName.replace('.nk', '.py'))
		debug(app = None, method = 'FromMaya2Nuke.createNukePythonFile', message = 'WRITING: %s' % systemCommand,  verbose = False)
		os.system(systemCommand)

	def exportData(self, object, channels, startF, endF, exportFile):
		channalsAnimated = []
		channalsNotAnimated = []
		
		hisObject = cmds.listHistory(object)
		objectNodeType = cmds.nodeType(hisObject[0])

		objectNameWrite = object.replace(':', '_')
		
		if objectNodeType == 'spotLight':
			objectNodeTypeWrite = 'spot'
		elif objectNodeType == 'pointLight':
			objectNodeTypeWrite = 'point'
		elif objectNodeType == 'directionalLight':
			objectNodeTypeWrite = 'directional'
		elif objectNodeType == 'camera':
			objectNameWrite = objectNameWrite[:-4]
			objectNodeTypeWrite = 'camera'
		else: 
			objectNodeTypeWrite = objectNodeType
	
		for channel in channels:
			channelSplit = channel.split(':')
			
			if len(channelSplit) == 1:
				objectName = object
				channelName = channelSplit[0]
				nodeType = cmds.nodeType(object)
			else:
				hisObject = cmds.listHistory(object)
				nodeType = channelSplit[0]
				for child in hisObject:
					thisNodeType = cmds.nodeType(child)
					if thisNodeType == channelSplit[0]:	
						objectName = child
						channelName = channelSplit[1]
						break
						 
			isAnimated = cmds.listConnections(str(objectName) + "." + str(channelName))
			if isAnimated != None:
				channalsAnimated.append(objectName + '+' + channelName + '+' + nodeType)
			else:
				channalsNotAnimated.append(objectName + '+' + channelName + '+' + nodeType)
		
		writeOut = objectNameWrite + '\t'  + objectNodeTypeWrite + '\t\n'
			
		rotateOrders = ['XYZ', 'YZX', 'ZXY', 'XZY', 'YXZ', 'ZYX']	
		for channel in channalsNotAnimated:
			channelValues = channel.split('+')
			thisValue = str(cmds.getAttr(channelValues[0] + '.' + channelValues[1]))
			if channelValues[1] == 'rotateOrder':
				thisValue = rotateOrders[int(thisValue)]
			writeOut += channelValues[2] + '.' + channelValues[1] + '\t' + thisValue + '\n'
		
		writeOut += '+++++Animated+++++\n'
	
		if len(channalsAnimated) > 0:
			writeOut += 'Frame'
			for channel in channalsAnimated:
				channelValues = channel.split('+')
				writeOut += '\t' + channelValues[2] + '.' + channelValues[1]
			writeOut += '\n'
				
			for i in range(startF, endF):
				writeOut += str(i)
				for channel in channalsAnimated:
					channelValues = channel.split('+')
					writeOut += '\t' + str(cmds.getAttr(channelValues[0] + '.' + channelValues[1], time=i))
				writeOut += '\n'
		
		f = open(exportFile, 'w')
		f.write(writeOut)
		f.close()	

	def delteNukePythonFile(self):
		os.remove(self.exportPath + 'nukePyFile.py')
		debug(app = None, method = 'FromMaya2Nuke.delteNukePythonFile', message = 'Deleted %ssnukePyFile.py' % self.exportPath,  verbose = False)
			
	def openNukeScriptAfterwards(self):
		subprocess.Popen('"' + self.nukePath + self.nukeExec + '" ' + self.exportPath + self.nukeExportScriptName)
