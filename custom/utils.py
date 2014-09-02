import os, getpass, sys, shutil, sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
from functools import partial
from tank import TankError
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')

if 'C:/Program Files/Autodesk/Maya2013.5/Python/Lib/site-packages' not in sys.path:
    sys.path.append('C:/Program Files/Autodesk/Maya2013.5/Python/Lib/site-packages')

import maya.cmds as cmds
import maya.mel as mel
from debug import debug

def getFilmFit(myFilmFit):
    if myFilmFit == 0:
        return 'fill'
    elif myFilmFit == 1:
        return 'horizontal'
    elif myFilmFit == 2:
        return 'vertical'
    elif myFilmFit == 3:
        return 'overscan'     
    
def _bakeCamera(sourceCamera = ''):
    """
    Used for quickly baking out a camera into an existing CAM group.
    Useful for checking in tracked cameras etc
    """
    if sourceCamera == '':
        sourceCamera = cmds.ls(sl=True)[0]
    sourceCameraShape = cmds.listRelatives(sourceCamera, shapes = True)[0]
    startFrame = int(cmds.playbackOptions(query = True, animationStartTime = True))
    endFrame = int(cmds.playbackOptions(query = True, animationEndTime = True))
    focallength = int(cmds.getAttr('%s.focalLength' % sourceCameraShape) )
    
    camName = '%s_bake' % (sourceCamera)
    newCam = cmds.camera(
            name = camName, 
            centerOfInterest = 5, 
            focalLength = cmds.getAttr('%s.focalLength' % sourceCamera),
            lensSqueezeRatio = 1,  
            cameraScale = cmds.getAttr('%s.cameraScale' % sourceCamera),
            horizontalFilmAperture = cmds.getAttr('%s.horizontalFilmAperture' % sourceCamera),  
            horizontalFilmOffset = 0, 
            verticalFilmAperture = cmds.getAttr('%s.verticalFilmAperture' % sourceCamera), 
            verticalFilmOffset = 0,
            filmFit = getFilmFit(cmds.getAttr('%s.filmFit' % sourceCamera)) ,  
            overscan = cmds.getAttr('%s.overscan' % sourceCamera), 
            motionBlur  = 0,  
            shutterAngle = 144,  
            nearClipPlane = cmds.getAttr('%s.nearClipPlane' % sourceCamera),  
            farClipPlane = cmds.getAttr('%s.farClipPlane' % sourceCamera), 
            orthographic = 0,  
            orthographicWidth = 30, 
            panZoomEnabled = 0,  
            horizontalPan = 0,  
            verticalPan = 0,  
            zoom = 1, 
            dgm = True, 
            dr= True,
            dsa = True
            )
    cmds.rename('%s1' % camName, camName)#stupid freaking maya can't create a new freaking node without putting a 1 at the end of it.
    createTypeTag(camName, 'shotCam')
    
    cmds.connectAttr('%s.focalLength' % sourceCameraShape, '%sShape.focalLength' % camName)
    cmds.pointConstraint(sourceCamera, camName, n = 'TmpPoint', mo = False)
    cmds.orientConstraint(sourceCamera, camName, n = 'TmpOrient', mo = False)
    cmds.bakeResults(
                    camName, 
                    simulation = True,  
                    t = (startFrame,endFrame), 
                    sampleBy  = 1,
                    disableImplicitControl = True,  
                    preserveOutsideKeys = False,  
                    sparseAnimCurveBake = False, 
                    removeBakedAttributeFromLayer = False,
                    bakeOnOverrideLayer = False, 
                    controlPoints = False,  
                    shape = True
                    )
    cmds.delete('TmpPoint')
    cmds.delete('TmpOrient')
    try:
        cmds.parent(camName, 'BAKE_CAM_hrc')
    except TypeError:
        cmds.group(n = 'BAKE_CAM_hrc', em = True)
        cmds.parent(camName, 'BAKE_CAM_hrc')
    except ValueError:
        cmds.group(n = 'BAKE_CAM_hrc', em = True)
        cmds.parent(camName, 'BAKE_CAM_hrc')
         
    #get the imageplane and put it into the new camera.
    try:
        for input in cmds.listConnections('%s' % sourceCameraShape, source = True):
            if 'imagePlane' in input:
                cmds.shadingNode('imagePlane', asUtility = True , name = 'tempPlane')
                cmds.connectAttr('%s.message' % input, '%sShape.imagePlane[0]' % camName)
                cmds.delete('tempPlane')
    except TypeError:
        print 'No image plane found, skipping...'
       
    return camName

def _parsePreset(applyTo = "", presetFile = ""):
    """
    Function to cleanly try to set attrs on a node without actually using the apply preset mel approach which crashes maya hard
    @param presetFile: Full path the preset file including the .mel extension
    @param applyTo: The name of the particle shape node..
    @type applyTo: String
    @type presetFile: String 
    """
    debug(None, method = 'utils._parsePreset', message = 'Applying preset to: %s' % applyTo, verbose = False)
    badKeys = ['useParticleRadius', 'useLighting', 'spriteTwist', 'startFrame', 'spriteNum', 'currentTime', 'spriteScaleY', 'spriteScaleX', 'spriteScaleZ', 'pointSize', 'normalDir'] #, 'useRatePP']
    ## fix pathing if /
    if '/' in presetFile:
        presetFile = '\\'.join(presetFile.split('/'))
    
    debug(None, method = 'utils._parsePreset', message = 'presetFile: %s' % presetFile, verbose = False)
    
    readFile = open(presetFile, "r").readlines()
    myVars = {}
    for line in readFile:
        if 'blendAttr' in line:
            split = line.strip()
            attr = str( split.split('"')[1] )
            val = split.split('"')[-1][:-1]
            
            if val:
                if attr not in badKeys:
                    myVars.setdefault(attr, float(val) )
    
    for attr, val in myVars.iteritems():
        try:    
            cmds.setAttr("%s.%s" %(applyTo, attr), val)
            debug(None, method = 'utils._parsePreset', message = 'Setting attr on %s attr: %s %s' % (applyTo, attr, val), verbose = False)
        except RuntimeError:
            debug(None, method = 'utils._parsePreset', message = 'FAILED to setAttr on "%s.%s", attrName may not exist...' %(applyTo, attr), verbose = False)

def checkRoot_hrc_Naming(items):
    """
    Function to check the naming of the shotgun asset matches the naming of the root_hrc asset in maya
    """
    debug(None, method = 'checkRoot_hrc_Naming', message = 'items: %s' % items, verbose = False)
    assetName = cmds.file(query=True, sn= True).split('/')[4]
    debug(None, method = 'checkRoot_hrc_Naming', message = 'assetName: %s' % assetName, verbose = False)
    for eachItem in items:
        #print 'Checking %s now' % items
        if eachItem["type"] == 'mesh_group':
            parent = eachItem["name"].split('_hrc')[0].split('|')[-1] ## note this should be the root _hrc group but it is returned from shotgun with a | at the head.
            debug(None, method = 'checkRoot_hrc_Naming', message = 'parent: %s' % parent, verbose = False)
            
            if parent != assetName:
                cmds.warning('YOUR ASSET IS NAMED INCORRECTLY. MAKE SURE YOUR ROOT NODE IS %s_hrc' % assetName)
                return False
            else:
                return True

def loadSceneAssemblyPlugins(tankError = False):
        ## PLUGIN CHECK
        ## First try to make sure the plugins are loaded in maya
        if not cmds.pluginInfo('AbcExport.mll', query = True, loaded = True):
            try:
                cmds.loadPlugin('AbcExport.mll')
            except RuntimeError:
                if TankError:
                    raise TankError("AbcExport failed to load!!")
        if not cmds.pluginInfo('AbcImport.mll', query = True, loaded = True):
            try:
                cmds.loadPlugin('AbcImport.mll')
            except RuntimeError:
                if TankError:
                    raise TankError("AbcImport plugin failed to load!!")
        if not cmds.pluginInfo('gpuCache.mll', query = True, loaded = True):
            try:
                cmds.loadPlugin('gpuCache.mll')
            except RuntimeError:
                if TankError:
                    raise TankError("gpuCache plugin failed to load!!")            
        if not cmds.pluginInfo('sceneAssembly.mll', query = True, loaded = True):
            try:
                cmds.loadPlugin('sceneAssembly.mll')
            except RuntimeError:
                if TankError:
                    raise TankError("sceneAssembly plugin failed to load!!")   

def processExpressionString(expStringList):
    string = ''
    for eachLine in expStringList:
        string = string + eachLine
    return string

def checkExpressionExists(name):
    if cmds.objExists(name):
        cmds.delete(name)
        print 'Removed expression %s' %  name
        
def attributeExists(attr,node):
    """
    Check if attribute exists on node
    """
    if (attr and node):
        if not cmds.objExists(node):
            return 0
        if attr in cmds.listAttr(node,shortNames= True):
            return 1
        if attr in cmds.listAttr(node):
            return 1
        return 0
    
## USEFUL FUNCTIONS#
def getSelectedType(nodeType):
    """
    Get all nodes within current selection of a specific type
    """
    nodes = []
    for s in cmds.ls( sl=True ):
        n = cmds.listRelatives( s, type=nodeType )
        if n != None:
            nodes.append(n)
    return nodes

def saveme(pathTo):
    ignores = ['.git', '.settings', 'tools_freeMelScripts']
    if os.path.isdir(pathTo):
        for eachFolder in os.listdir(pathTo):
            if eachFolder not in ignores and eachFolder != 'BBmaya':
                finalpath = os.path.join(pathTo, eachFolder)
                if os.path.isdir(finalpath):
                    shutil.rmtree(finalpath)
                else:
                    try:
                        os.remove(finalpath)
                    except:
                        pass
                    
            elif eachFolder == 'BBmaya':
                for eachSubFolder in os.listdir(os.path.join(pathTo, 'BBmaya')):
                    if eachSubFolder not in ignores:
                        finalpath = os.path.join(pathTo, 'BBmaya', eachSubFolder)
                        if os.path.isdir(finalpath):
                            shutil.rmtree(finalpath)
                        else:
                            try:
                                os.remove(finalpath)
                            except:
                                pass
            else:
                pass
                
def getShotCamera():
    cameras = []
    for each in cmds.ls(type = 'camera'):
        if cmds.objExists('%s.type' % cmds.listRelatives(each, parent =True)[0]):
            if cmds.getAttr('%s.type'% cmds.listRelatives(each, parent =True)[0]) == 'shotCam':
                cameras.append(each)
    #print 'Cameras: %s' % cameras
    if len(cameras) > 1:
        cmds.warning('More than one shotCam found! Please make sure you scene only has one shotCam in it!')
        return None
    else:
        return cameras[0]

def createTypeTag(obj, typeName):
    """
    Builds an attr on the node called type and sets it to the typeName
    @param obj:  The object or node you want to tag
    @param typeName: The type name
    @type obj: String
    @type typeName: String
    """  
    if cmds.objExists('%s.type' % obj):
        cmds.deleteAttr('%s.type' % obj)
    try:
        cmds.addAttr(obj, ln = 'type', dt = 'string')
    except:
        pass
    cmds.setAttr('%s.type' % obj, typeName, type = 'string')
    
def add_custom_attrs(objectName = '', **kwargs):
    
    fullName = '%s.%s' %(objectName, kwargs['longName'])
    
    if not cmds.objExists(fullName):
        cmds.addAttr(objectName, **kwargs)
        cmds.setAttr(fullName, keyable = True)
        
        if 'keyable' in kwargs:
            if kwargs['keyable'] == False:
                cmds.setAttr(fullName, channelBox = True)