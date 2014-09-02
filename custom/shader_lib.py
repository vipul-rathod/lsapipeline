"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db
"""
import os, getpass, sys, shutil
from functools import partial
## Tank Stuff
import sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
from tank import TankError
## Maya Stuff
import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm
## XML Stuff
import xml.etree.ElementTree as xml
from xml.etree import ElementTree
try:
    from mentalcore import mapi
except:
    pass
## Now get the custom tools
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug
import maya_genericSettings as settings
import CONST as CONST
#reload(settings)
#reload(CONST)

def treeSHDFix():
    """
    Legacy function stored here just incase
    This was used to remove the randomizer on the trees
    """
    findShader = cmds.ls('*:*:Tree_Bush_cMat_shd')
    if findShader != []:
        getShader = findShader[0]
        findShader.pop(0)
        for shader in findShader:
            debug(self.app, method = 'treeSHDFix', message = 'Connecting to ShadingEngines.. %s' % shader, verbose = False)
            try:
                shadingEngine = cmds.listConnections(shader, source = True, type = 'shadingEngine')[0]
                cmds.connectAttr('%s.outValue'% getShader,'%s.miMaterialShader' % shadingEngine, force = True)
            except:
                pass
    else:
        cmds.warning("Skipping trees... \n\tCan't find TreeShaders in scene to correct core_randomizer shading.")

def replaceBump2WithCoreNormalmap():
    for eachBump in cmds.ls(type = 'bump2d'):
        tangentSpaceNormals = cmds.getAttr('%s.bumpInterp' % eachBump)
        if tangentSpaceNormals == 1:
            fileIn = cmds.listConnections(eachBump, source = True, type = 'file') or cmds.listConnections(eachBump, source = True, type = 'mentalrayTexture')
            core_material = cmds.listConnections(eachBump, destination = True, type = 'core_material')
            if fileIn and core_material:
                cmds.delete(eachBump)
                core_normalMap = cmds.createNode('core_normalmap', name = eachBump)
                cmds.connectAttr('%s.outColor' % fileIn[0], '%s.normal_map' % core_normalMap, f = True)
                cmds.connectAttr('%s.outAlpha' % fileIn[0], '%s.normal_mapA' % core_normalMap, f = True)
                for eachShader in core_material:
                    cmds.connectAttr('%s.message' % core_normalMap, '%s.normal_map' % eachShader, f = True)

def deleteDGSHD():
    getDGSHDNodes = cmds.ls(type = 'script')
    if getDGSHDNodes:
        for eachDGSHD in getDGSHDNodes:
            if 'dgSHD' in eachDGSHD:
                print 'Removing %s because of lazy artist cleanup...CLEAN YOUR SCENES!' % eachDGSHD 
                cmds.delete(eachDGSHD)

def deleteDeadFileInNodes():
    listAllFileNodes = cmds.ls(type = 'file') + cmds.ls(type = "mentalrayTexture")
    for eachFileIn in listAllFileNodes:
        #print cmds.listConnections(eachFileIn, plugs = True)
        getPlugs = cmds.listConnections(eachFileIn, plugs = True)
        #print getPlugs
        if getPlugs:
            for eachPlug in getPlugs:
                if 'defaultRenderUtilityList1' in eachPlug:
                    getCons = cmds.listConnections(eachPlug, plugs = True)
                    if len(getCons) == 1:
                        if getCons[0].endswith('.message'):
                            print 'Removing %s' % eachFileIn
                            cmds.delete(eachFileIn)
                            
def fixDuplicateFileInNodes():
    ## Cleanup duplicate file paths
    allFileNodes = [fileNode for fileNode in cmds.ls(type = 'mentalrayTexture') for fileNode in cmds.ls(type = 'file')]
    duplicateNodes = {}
    for each in allFileNodes:
        try:
            filePath = cmds.getAttr('%s.fileTextureName' % each)
        except:
            pass
        if filePath in duplicateNodes.keys():
            if each not in duplicateNodes[filePath]:
                duplicateNodes[filePath].append(each)
        else:
            duplicateNodes[filePath] = [each]
            
    for eachFilePath, eachNodeList in duplicateNodes.items():
        if len(eachNodeList) > 1:
            #print "{0:<10}{1:<20}    {2:<10}{3}".format('filePath:', eachFilePath, 'nodes:', eachNodeList)
            ## use base [0] as master and connect that to everything else then delete everything else
            master = eachNodeList[0]
            for each in eachNodeList[1:]:
                #find the connected shader to the file
                try:
                    getDest = cmds.listConnections('%s.outColor' % each, plugs = True)[0]
                    cmds.connectAttr('%s.outColor' % master, getDest, f = True)
                except:
                    try:
                        getDest = cmds.listConnections('%s.outAlpha' % each, plugs = True)[0]
                        cmds.connectAttr('%s.outAlpha' % master, getDest, f = True)
                    except TypeError: #there's nothing of value to connect
                        pass

def buildCustomMCRenderPasses():
    getAllPasses = mapi.get_all_passes()

    passes = {
              'matte_eye' : ['*eyeball_white*','*eyeball_clear*'],
              'matte_water' : ['*ocean_srf*'],
              'matte_ground' : ['*bbb_terrain_geo*','*beach_geo*']
              }

    for key , var in passes.items():
        if 'matte' in key:
            if not key in getAllPasses:
                mapi.create_pass('Matte', n= key)
            for eachGeo in var:
                getAllGeo = cmds.ls(eachGeo, type='transform')
                for each in getAllGeo:
                    try:
                        mapi.link_to_pass([each], key, mapi.OBJECTS)
                    except:
                        cmds.warning('Failed to set {0} to renderpass {1}'.format(each, key))
                        pass

def buildExposure():
    if cmds.objExists('mia_exposure_simple1'):
        cmds.delete('mia_exposure_simple1')

    shotCamera = ''
    for eachCam in cmds.ls(type = 'camera'):
        if cmds.objExists('%s.type' % cmds.listRelatives(eachCam, parent = True)[0]):
            if cmds.getAttr('%s.type' % cmds.listRelatives(eachCam, parent = True)[0]) == 'shotCam':
                shotCamera = eachCam

    if shotCamera:
        if cmds.objExists('mentalcoreLens'):
            if not cmds.isConnected('mentalcoreLens.message', '%s.miLensShader' % shotCamera):
                cmds.connectAttr('mentalcoreLens.message', '%s.miLensShader' % shotCamera, f = True)
        else:
            cmds.warning('mentalcoreLens doesn\'t exist!')
    else:
        cmds.warning('NO SHOT CAMERA FOUND!!!')
            
def setup_MC_renderPasses():
    """
    Sets the base default render passes for mental core
    """
    debug(app = None, method = 'renderPasses', message = '.....', verbose = False)
    
    try:
        getAllPasses = mapi.get_all_passes()
        ## ELEMENTS + VISIBLE IN REFRACTIONS
        if not 'ao' in getAllPasses:
            aoPass = mapi.create_pass('Ambient Occlusion')
            cmds.setAttr(aoPass + '.vis_in_refr', 1)
            mapi.associate_pass(aoPass, 'defaultRenderLayer')
        
        if not 'beauty' in getAllPasses:
            beautyPass = mapi.create_pass('Beauty')
            mapi.associate_pass(beautyPass, 'defaultRenderLayer')
            mapi.associate_pass(beautyPass, 'cloud_LYR')
        
        if not 'colour' in getAllPasses:
            colourPass = mapi.create_pass('Colour')
            cmds.setAttr(colourPass + '.vis_in_refr', 1)
            mapi.associate_pass(colourPass, 'defaultRenderLayer')
            mapi.associate_pass(colourPass, 'cloud_LYR')

        if not 'clouds_down' in getAllPasses:
            customColourPass = mapi.create_pass('Custom Colour', n = 'clouds_down')
            mapi.associate_pass(customColourPass, 'cloud_LYR')

        if not 'depth_norm' in getAllPasses:
            depthPass = mapi.create_pass('Depth (Normalized)')
            cmds.setAttr(depthPass + '.vis_in_refr', 1)
            mapi.associate_pass(depthPass, 'defaultRenderLayer')
            mapi.associate_pass(depthPass, 'cloud_LYR')
            cmds.setAttr("depth_norm.filtering",1)
            
        if not 'diffuse' in getAllPasses:
            diffusePass = mapi.create_pass('Diffuse')
            cmds.setAttr(diffusePass + '.vis_in_refr', 1)
            mapi.associate_pass(diffusePass, 'defaultRenderLayer')
        
        if not 'environment' in getAllPasses:
            envPass = mapi.create_pass('Environment')
            mapi.associate_pass(envPass, 'defaultRenderLayer')
            mapi.associate_pass(envPass, 'cloud_LYR')
            
        if not 'facing_ratio' in getAllPasses:
            facingPass = mapi.create_pass('Facing Ratio')
            cmds.setAttr(facingPass + '.vis_in_refr', 1)
            mapi.associate_pass(facingPass, 'defaultRenderLayer')
            mapi.associate_pass(facingPass, 'cloud_LYR')
        
        if not 'incandescence' in getAllPasses:
            incandescencePass = mapi.create_pass('Incandescence')
            mapi.associate_pass(incandescencePass, 'defaultRenderLayer')
        
        if not 'indirect' in getAllPasses:
            indirectPass = mapi.create_pass('Indirect')
            cmds.setAttr(indirectPass + '.vis_in_refr', 1)
            mapi.associate_pass(indirectPass, 'defaultRenderLayer')
    
        if not 'matte_ground' in getAllPasses:
            matteGround = mapi.create_pass('Matte', n = 'matte_ground')
            mapi.associate_pass(matteGround, 'defaultRenderLayer')
        
        if not 'matte_houses' in getAllPasses:
            matteHouses = mapi.create_pass('Matte', n = 'matte_houses')
            mapi.associate_pass(matteHouses, 'defaultRenderLayer')
        
        if not 'matte_water' in getAllPasses:
            matteWater = mapi.create_pass('Matte', n = 'matte_water')
            mapi.associate_pass(matteWater, 'defaultRenderLayer')
        
#         matteChar1 = mapi.create_pass('Matte', n = 'matte_zip')
#         mapi.associate_pass(matteChar1, 'defaultRenderLayer')
# 
#         matteChar2 = mapi.create_pass('Matte', n = 'matte_sydney')

        if not 'matte_clouds' in getAllPasses:
            matteClouds = mapi.create_pass('Matte', n = 'matte_clouds')
            mapi.associate_pass(matteClouds, 'cloud_LYR')
        
        if not 'normal_world_norm' in getAllPasses:
            normPass = mapi.create_pass('Normal World (Normalized)')
            mapi.associate_pass(normPass, 'cloud_LYR')
        
        if not 'point_world' in getAllPasses:
            pointPass = mapi.create_pass('Point World')
            mapi.associate_pass(pointPass, 'cloud_LYR')
        
        if not 'reflection' in getAllPasses:
            reflectionPass = mapi.create_pass('Reflection')
            cmds.setAttr(reflectionPass + '.vis_in_refr', 1)
            mapi.associate_pass(reflectionPass, 'defaultRenderLayer')
        
        if not 'refraction' in getAllPasses:
            refractionPass = mapi.create_pass('Refraction')
            mapi.associate_pass(refractionPass, 'defaultRenderLayer')
        
        if not 'specular' in getAllPasses:
            specularPass = mapi.create_pass('Specular')
            cmds.setAttr(specularPass + '.vis_in_refr', 1)
            mapi.associate_pass(specularPass, 'defaultRenderLayer')
        
        if not 'sss_front' in getAllPasses:
            sssFrontPass = mapi.create_pass('Subsurface Front')
            mapi.associate_pass(sssFrontPass, 'cloud_LYR')
        
        if not 'sss_back' in getAllPasses:
            sssBackPass = mapi.create_pass('Subsurface Back')
            mapi.associate_pass(sssBackPass, 'cloud_LYR')
        debug(app = None, method = 'renderPasses', message = 'Render passes built....', verbose = False)
    except:
        cmds.warning('NO MENTALCORE LOADED!')
        pass

def oceanAttach(app):
    debug(None, method = 'oceanAttach', message = 'oceanAttach...', verbose = False)
    
    presetTemplate = app.get_template('maya_ocean_presetRoot')
    #presetTemplate:<Sgtk TemplatePath maya_lighting_oceanPreset: /fx/presets/Lighting/{presetName}.ma> # 
    debug(None, method = 'oceanAttach', message = 'presetTemplate: %s' % presetTemplate,  verbose = False)
    
    mayaOceanPresetPath = r'%s' % presetTemplate.apply_fields({'presetName' : CONST.OCEAN_RENDER_SHADER_MA})
    debug(None, method = 'oceanAttach', message = 'mayaOceanPresetPath:%s' % mayaOceanPresetPath,  verbose = False)
    
    try:
        ## Now try to import marks/deepeshes final shader from the ma file.
        if not cmds.objExists(CONST.MC_WATERSHD_NAME):
            cmds.file("%s" % mayaOceanPresetPath.replace('\\', '/'), i = True, type = 'mayaAscii', applyTo = ':', options = 'v=0')
            debug(None, method = 'oceanAttach', message = 'oceanWater_render_SHD imported successfully...',  verbose = False)            

        ## Now fix the connections
        ## Out Color
        src = '%s.outColor' % CONST.OCEANDISPSHADER
        dst = '%sSG.surfaceShader' % CONST.OCEANDISPSHADER
        if cmds.objExists(src) and cmds.objExists(dst):
            if cmds.isConnected(src, dst):
                cmds.disconnectAttr(src, dst)

        ## Displacement
        src = '%s.displacement' % CONST.OCEANDISPSHADER
        dst = '%sSG.displacementShader' % CONST.OCEANDISPSHADER
        if cmds.objExists(src) and cmds.objExists(dst):
            if not cmds.isConnected(src, dst):
                cmds.connectAttr(src, dst)

        ## Out Value
        src = '%s.outValue' % CONST.MC_WATERSHD_NAME
        dst = '%sSG.miMaterialShader' % CONST.OCEANDISPSHADER
        if cmds.objExists(src) and cmds.objExists(dst):
            if not cmds.isConnected(src, dst):
                cmds.connectAttr(src, dst)

        ## Out Color
        src = '%s.outColor' % CONST.OCEANDISPSHADER
        dst = 'OceanFoam.outColor'
        if cmds.objExists(src) and cmds.objExists(dst):
            if not cmds.isConnected(src, dst):
                cmds.connectAttr(src, dst, f = True)

        ## Out Alpha
        src = '%s.outAlpha' % CONST.FOAM_FLUID_SHAPENODE
        dst = 'oceanWater_incd_cTxBld.layer[1].opacity'
        if cmds.objExists(src) and cmds.objExists(dst):
            if not cmds.isConnected(src, dst):
                cmds.connectAttr(src, dst, f = True)

        ## Out Alpha 2
        src = '%s.outAlpha' % CONST.FOAM_FLUID_SHAPENODE
        dst = 'oceanWater_incd_cTxBld.layer[2].opacity'
        if cmds.objExists(src) and cmds.objExists(dst):
            if not cmds.isConnected(src, dst):
                cmds.connectAttr(src, dst, f = True)

        ## Now force the final shader to the oceanNURBS plane
        if cmds.objExists('ocean_srf'):
            if cmds.objExists('ocean_dispShaderSG'):
                cmds.sets('ocean_srf', edit = True, forceElement = 'ocean_dispShaderSG')
            else:
                cmds.warning('%s doesn\'t exist...' % 'ocean_dispShaderSG')
        else:
            cmds.warning('%s doesn\'t exist, please rebuild ocean first?' % 'ocean_srf')

        ## More from deepesh
        cmds.setAttr("%s.waterColor" % CONST.OCEANDISPSHADER, 0,0,0, type = 'double3')
        cmds.setAttr("%s.environment[2].environment_Color" % CONST.OCEANDISPSHADER, 0,0,0, type = 'double3')
        cmds.setAttr("%s.specularColor" % CONST.OCEANDISPSHADER, 0,0,0, type = 'double3')
        cmds.setAttr("%s.specularity" % CONST.OCEANDISPSHADER, 0)
        cmds.setAttr("%s.eccentricity" % CONST.OCEANDISPSHADER, 0)
        cmds.setAttr("%s.reflectivity" % CONST.OCEANDISPSHADER, 0)

        mel.eval("removeMultiInstance -break true %s.environment[1];" % CONST.OCEANDISPSHADER)
        mel.eval("removeMultiInstance -break true %s.environment[0];" % CONST.OCEANDISPSHADER)

        debug(None, method = 'oceanAttach', message = 'oceanAttach Complete...', verbose = False)
    
    except RuntimeError:
        debug(None, method = 'oceanAttach', message = 'oceanAttach FAILED...', verbose = False)
        cmds.warning('Ocean Attach FAILED!')

def _buildReplacementFileIn(each, replacement = False):
    """
    Builds a new shadingNode file for any mentalrayTextures, else returns the name of the file node
    """
    if replacement:
        newFile = '%s_fileIn_replacement' % each
    else:
        newFile = each

    ## Build the maya one first
    if replacement:
        if not cmds.objExists('%s_fileIn_replacement' % each):
            cmds.shadingNode('file', asTexture = True, n = newFile)
            getFilePath = cmds.getAttr('%s.fileTextureName' % each)
            cmds.setAttr('%s.fileTextureName' % newFile, getFilePath, type = 'string')
            
            #cmds.warning("Set attr for %s.fileTextureName to %s" % (newFile, getFilePath))
    return newFile

def findConnections(each = '', ignore = [], plugs = False, source = False, destination = False):
    """
    Func for finding the connections to a shader node skipping the uncessary shit and returning a clean list
    """
    typesToSkip = ['shadingEngine','initialParticleSE', 'initialShadingGroup', 'defaultShaderList', 'place2dTexture', 'materialInfo', 'defaultTextureList', 'defaultRenderUtilityList']
    connections = []
    typesToSkip = typesToSkip + ignore
    #print cmds.listConnections(each, destination = True)
    try:
        getConns = cmds.listConnections(each, destination = True, plugs = plugs, source = source)
    except:
        pass
    if getConns:
        for eachConn in getConns:
            if cmds.nodeType(eachConn) not in typesToSkip:
                #print 'Found valid connection: %s' % eachConn
                connections.append(eachConn)

    ## Now return a new culled list of connections to check since maya's listConnections is a fucking nightmare.
    if getConns:
        return connections
    else:
        return False

def findLambert(each):
    """
    This will find a lambert to 4 levels deep of connects for a suuplied node. Usually a File node for us
    """
    getConns = findConnections(each)
    if getConns:##make sure it's a valid list of connections to look through
        for eachConn in getConns:
            #print 'Looking For Lambert: %s \tnodeType: %s' % (eachConn, cmds.nodeType(eachConn))
            if cmds.nodeType(eachConn) == 'lambert':
                return eachConn
            else:            
                getConn2 = findConnections(eachConn)
                if getConn2:##make sure it's a valid list of connections to look through
                    for eachConn2 in getConn2:
                        #print 'Looking For Lambert LvL2: %s \tnodeType: %s' % (eachConn2, cmds.nodeType(getConn2))
                        if cmds.nodeType(eachConn2) == 'lambert':
                            return eachConn2
                        else:
                            getConn3 = findConnections(eachConn2)
                            if getConn3:##make sure it's a valid list of connections to look through
                                for eachConn3 in getConn3:
                                    #print 'Looking For Lambert LvL3: %s \tnodeType: %s' % (eachConn3, cmds.nodeType(eachConn3))
                                    if cmds.nodeType(eachConn3) == 'lambert':
                                        return eachConn3
                                    else:
                                        getConn4 = findConnections(eachConn3)                                        
                                        if getConn4:##make sure it's a valid list of connections to look through
                                            for eachConn4 in getConn4:
                                                #print 'Looking For Lambert LvL4: %s \tnodeType: %s' % (eachConn4, cmds.nodeType(eachConn4))
                                                if cmds.nodeType(eachConn4) == 'lambert':
                                                    return eachConn4
                                                else:
                                                    pass
    else:
        return False

def fixDGLambertFileNodes():
    """
    Replaces all mentalray nodes with regular maya nodes
    Testing to see if this removes the crashing on the displaying of textures in viewport
    """
    if cmds.objExists('dgSHD'):
        ## NOW DISCONNECT ALL THE SHADING FILE IN NODES AND GRAB THEIR APPROX COLOR AND PUT THAT INTO THE DIFFUSE FOR THE SHADER
        badTypes = ['shadingEngine', 'defaultShaderList', 'materialInfo']
        fileNodes = ['mentalrayTexture', 'file']
        
        ## Process file nodes and connect directly to lambert color in.
        for eachFileNode in fileNodes:
            for each in cmds.ls(type = eachFileNode):
                ## if it is a mentrayTexture node replace it with a normal maya one
                if eachFileNode == 'mentalrayTexture':
                    fileNode = _buildReplacementFileIn(each = each, replacement = True)
                    getLambert = findLambert(fileNode)
                    if getLambert:
                        cmds.connectAttr('%s.outColor' % fileNode, '%s.color' % getLambert, f = True)
                else:
                    fileNode = _buildReplacementFileIn(each = each, replacement = False)
                    getLambert = findLambert(fileNode)
                    if getLambert:
                        try:
                            cmds.connectAttr('%s.outColor' % fileNode, '%s.color' % getLambert, f = True)
                        except:##Already connected
                            pass

def fixDGForGPU():
    """
    Function used to set the base color of the lambets to the file or ramp colors
    """
    debug(app = None, method = 'fixDGForGPU', message = 'Fixing shaders to lamb col only', verbose = False)
    if cmds.objExists('dgSHD'):
        
        ## FILES
        ## Now fetch the color for each file node, and set the lamberts color to that.            
        filesDict = {}
        for eachFile in cmds.ls(type = 'file'):
            getColor = cmds.colorAtPoint(eachFile, u=.3, v=.3, o = 'RGB')
            try:
                for eachDest in cmds.listConnections(eachFile, destination = True, type = 'lambert'):
                    try:
                        filesDict[eachFile] = eachDest
                        cmds.disconnectAttr('%s.outColor'% eachFile, '%s.color' % eachDest)
                        cmds.setAttr('%s.color' % eachDest, getColor[0], getColor[1], getColor[2], type = 'double3')
                    except RuntimeError:
                        pass
            except TypeError:
                pass
        debug(app = None, method = 'fixDGForGPU', message = 'Files processed...', verbose = False)
        
        ## RAMPS ETC
        ## Now look at each connection to the lambert color and if it isn't a file grab the current color info and store it
        for each in cmds.ls(type = 'lambert'):
            getConns = findConnections(each = each, ignore =  ['file'], plugs = True, source = True, destination = True)
            if getConns:
               getCurrentColorVal = cmds.getAttr('%s.color' % each)
               for eachConn in getConns:
                   getConns2 = findConnections(each = eachConn, ignore =  ['file'], plugs = True, source = True, destination = True)
                   for eachConn2 in getConns2:
                       if eachConn2 == '%s.color' % each:
                           try:
                               debug(app = None, method = 'fixDGForGPU', message = 'Disconnect %s from %s' % (eachConn, each), verbose = False)
                               cmds.disconnectAttr(eachConn2, '%s.color' % each, f = True)
                               cmds.setAttr('%s.color' % each, getCurrentColorVal[0], getCurrentColorVal[1], getCurrentColorVal[2], type = 'double3')
                           except:
                               pass
        debug(app = None, method = 'fixDGForGPU', message = 'Ramps etc processed...', verbose = False)
        debug(app = None, method = 'fixDGForGPU', message = 'Finished...', verbose = False)
         
def sceneCheck():
    sceneName = cmds.file(query = True, sceneName = True)
    # check if old shaders exist in the scene, return if found
    checkMIA = []
    checkMIA   = cmds.ls(type = ('mia_material_x', 'mia_material_x_passes') )
    errors = False 
    
    if checkMIA != []:
        cmds.warning('\n\nThe following shaders are not mentalCore shaders : ')
        for mia in checkMIA:
            cmds.warning('    ---' + mia)
        cmds.warning( '--== |||||   Please convert your shaders to mentalCore shaders   ||||| ==-- ______________________ More details in the script editor _______________________________________')
        errors = True
    
    ## Now check for cameras
    for cam in cmds.ls(cameras = True):
        parents = cmds.listRelatives(cam, parent = True)
        parents = parents[0]
        originalCameras = ['persp', 'top', 'front', 'side']
        if parents not in originalCameras:
            #print parents
            cmds.warning ("Cannot continue, non default cameras exist in the scene. Please remove them.")
            errors = True

#     ## Now check for lights
#     if cmds.ls(type='light') != []:
#         print '\n\n\n'
#         print ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
#         print ("Please remove any lights in the scene")
#         print '------------------------------------------------------------------------------'
#         for light in cmds.ls(type='light'):
#             print light
#         cmds.warning ("Cannot continue, light(s) exist. Please see script editor for more info."),
#         errors = True
        
    return errors

def smartConn():
    sg = cmds.ls(type = 'shadingEngine')
    for each in sg:
        connections =  cmds.listConnections(each, plugs = True, connections = True)
        for connName in connections:
            findShader = connName.split('.')
            findShader = findShader[0]
            node = cmds.nodeType(findShader)
            shaderConn = cmds.listConnections(findShader, source = True, destination = True, plugs = True, connections = True)
            for eachConn in shaderConn:
                if '.transparency' in eachConn or '.cutout_opacity' in eachConn:
                    connIndex = shaderConn.index(eachConn)
                    connIndexNext = connIndex+1
                    opacityFileName = shaderConn[connIndexNext]
                    shader = eachConn.split('.')
                    shader = shader[0]
                    shader = shader + '.outValue'
                    sg = each + '.miShadowShader'
                    #print shader, sg
                    try:cmds.connectAttr(shader, sg, force = True)
                    except:pass

            if '.miShadowShader' in connName:
                connIndex = connections.index(connName)
                connIndexNext = connIndex+1
                fileName = connections[connIndexNext]
                split = fileName.split('.')
                shader = split[0]
                shaderConn = cmds.listConnections(shader, source = True, destination = True, plugs = True, connections = True)
                strShaderConn = str(shaderConn)
                if '.transparency' not in strShaderConn and '.cutout_opacity' not in strShaderConn:
                    try:
                        cmds.disconnectAttr(fileName, connName)
                    except:
                        pass
            if '.miPhotonShader' in connName:
                connIndex = connections.index(connName)
                connIndexNext = connIndex+1
                fileName = connections[connIndexNext]
                try:
                    cmds.disconnectAttr(fileName, connName)
                except:
                    pass

def fixRamps(rampNodes):
    for node in rampNodes:    
        getName, getPos, getCol, getInt = [],[],[],[]
        typeNode = cmds.nodeType(node)
        ## if node is remap/ramp change attribute values accordingly
        if typeNode == 'remapValue':
            attrValue = '.color'
            attrPostn = '.color_Position'
            attrColor = '.color_Color'
        if typeNode == 'ramp':
            attrValue = '.colorEntryList'
            attrPostn = '.position'
            attrColor = '.color'

        ## Find all multi attributes, using all these flags because it matches the one from the xml export
        listAllArray = cmds.listAttr(node + attrValue, read = True, hasData = True, visible = True, scalarAndArray = False, multi = True, output = True)
        for attr in listAllArray:
            if '.color_Position' in attr or '.position' in attr:
                posValues = attr, cmds.getAttr(node + '.' + attr)
                getPos.append(posValues)
                getName.append(node)
            if attr.endswith('.color_Color') or attr.endswith('.color'):
                colValues = attr, cmds.getAttr(node + '.' + attr)
                getCol.append(colValues)            
            if typeNode == 'remapValue':
                if '.color_Interp' in attr:
                    intValues = attr, cmds.getAttr(node + '.' + attr)
                    getInt.append(intValues)
                
        ## For each in the list, get according information if first value isn't 0
        ## Get position, new position, colour, interpolation (if remap) and connection if any
        ## Break all the plugs down to 0 and then remake it and reconnect
        for each in getPos:
            getPlug = each[0].split('[')[1]
            getPlug = int(getPlug.split(']')[0])    
            getPosition = int(getPos.index(each))
            if getPlug != int(getPosition):
                newSpot  = getPosition
                oldSpot  = getPlug
                nodeName = getName[getPosition]
                newPos   = getPos[getPosition][1]
                colour   = getCol[newSpot][1][0]
                if typeNode == 'remapValue':
                    interp   = getInt[newSpot][1]
                findConn = cmds.connectionInfo( nodeName + attrValue + '[' + str(oldSpot) + ']' + attrColor , sourceFromDestination= True)            
                cmds.removeMultiInstance(nodeName + attrValue + '[' + str(oldSpot) + ']', b = True)
                cmds.setAttr(nodeName + attrValue + '[' + str(newSpot) + ']' + attrPostn , float(newPos))
                cmds.setAttr(nodeName + attrValue + '[' + str(newSpot) + ']' + attrColor , colour[0], colour[1], colour[2], type = 'double3')
                if typeNode == 'remapValue':
                    cmds.setAttr(nodeName + attrValue + '[' + str(newSpot) + '].color_Interp', interp)
                try:
                    cmds.connectAttr(findConn, nodeName + attrValue + '[' + str(newSpot) + ']' + attrColor , force = True)
                except:
                    pass

def createAll(XMLPath = '', parentGrp = '', Namespace = '', Root = 'MaterialNodes', selected = False, selectedOrigHrcName = ''):
    """
    Used to create all the nodes required for an assets shading setup
    @param XMLPath:Path to the xml file
    @param parentGrp: The name of the group above the root group that exists in the xml file. This will get appended to the path
    @param Namespace: The namespace if it exists in the scene
    @param Root: The root name for the xml, this is usally left as the default MaterialNodes
    @param selected: If this is to be performed on a selected object from the shotgun application or not
    @param selectedOrigHrcName:This is used for duplicate assets, for surfVar association. Because we have 2 of the same hrc in maya now with the top node being AssetName1\
                                we need to send this through for correct assignment.
    @type XMLPath: String
    @type parentGrp: String
    @type Namespace: String
    @type Root: String
    @type selected: Boolean
    @type selectedOrigHrcName: String 
    """
    debug(app = None, method = 'createAll', message = 'XMLPath... %s' % XMLPath, verbose = False)
    debug(app = None, method = 'createAll', message = 'Namespace... %s' % Namespace, verbose = False)
    debug(app = None, method = 'createAll', message = 'Root... %s' % Root, verbose = False)
    debug(app = None, method = 'createAll', message = 'selected: %s' % selected, verbose = False)
    debug(app = None, method = 'createAll', message = 'selectedOrigHrcName: %s' % selectedOrigHrcName, verbose = False)
    
    # If the namespace doesn't exist, the objects wont get named correctly
    # create the namespace
    if Namespace != "" and Namespace != ":":
        if not cmds.namespace( exists= Namespace[:-1] ):
            cmds.namespace( add = Namespace[:-1])
    if selected:
        prefix = '%s_' % selectedOrigHrcName
    else:
        prefix = ''
        
    debug(app = None, method = 'createAll', message = 'Namespace check successful...', verbose = False)
    
    typeShader      = cmds.listNodeTypes( 'shader' ) or []
    typeTexture     = cmds.listNodeTypes( 'texture' )  or []
    typeUtility     = cmds.listNodeTypes( 'utility' )  or []
    typeMRTexture   = cmds.listNodeTypes( 'rendernode/mentalray/texture' )  or []
    typeMRDisp      = cmds.listNodeTypes( 'rendernode/mentalray/displace' )  or []
    typeMREnv       = cmds.listNodeTypes( 'rendernode/mentalray/environment' )  or []
    typeMRLightMaps = cmds.listNodeTypes( 'rendernode/mentalray/lightmap' )  or []
    typeMRMisc      = cmds.listNodeTypes( 'rendernode/mentalray/misc' )  or []
    typeMRConv      = cmds.listNodeTypes( 'rendernode/mentalray/conversion') or []
    typeMRInternal  = cmds.listNodeTypes( 'rendernode/mentalray/internal')  or []

    debug(app = None, method = 'createAll', message = 'typeShader %s' % typeShader, verbose = False)
    debug(app = None, method = 'createAll', message = 'typeTexture %s' % typeTexture, verbose = False)
    debug(app = None, method = 'createAll', message = 'typeUtility %s' % typeUtility, verbose = False)
    debug(app = None, method = 'createAll', message = 'typeMRTexture %s' % typeMRTexture, verbose = False)
    debug(app = None, method = 'createAll', message = 'typeMRDisp %s' % typeMRDisp, verbose = False)
    debug(app = None, method = 'createAll', message = 'typeMREnv %s' % typeMREnv, verbose = False)
    debug(app = None, method = 'createAll', message = 'typeMRLightMaps %s' % typeMRLightMaps, verbose = False)
    debug(app = None, method = 'createAll', message = 'typeMRMisc %s' % typeMRMisc, verbose = False)
    debug(app = None, method = 'createAll', message = 'typeMRConv %s' % typeMRConv, verbose = False)
    debug(app = None, method = 'createAll', message = 'typeMRInternal %s' % typeMRInternal, verbose = False)

    # get the root of the XMLPath argument
    debug(app = None, method = 'createAll', message = 'XMLPath...%s' % XMLPath, verbose = False)
    root = xml.parse(XMLPath).getroot()
    debug(app = None, method = 'createAll', message = 'Root XML.parse successful...', verbose = False)
    
    # Create an iterator based on the the root argument
    shaderIterator = root.getiterator(Root)
    # Iterate on shader level
    for levelOne in shaderIterator:
        debug(app = None, method = 'createAll', message = 'Entering levelOne in shaderIterator...', verbose = False)
        # Iterate on parent tag level
        if levelOne.getchildren():
            for levelTwo in levelOne:
                if levelTwo.tag == 'Nodes':
                    debug(app = None, method = 'createAll', message = 'Processing Nodes...', verbose = False)
                    for levelThree in levelTwo.getchildren():
                        node_name = levelThree.tag
                        if '_cCc_' in node_name:
                            node_name = node_name.replace('_cCc_', ':')
                        node_name = '%s%s%s' % (Namespace, prefix, node_name)
                        node_type = levelThree.attrib['value']
                        # Create all node types and sort them into correct hypershade tabs
                        if node_type in typeShader or node_type in typeMRInternal:
                            if not doesAssetAlreadyExistInScene(node_name):
                                cmds.shadingNode(node_type, asShader = True , name = node_name)
                        if node_type in typeTexture or node_type in typeMRInternal:
                            if not doesAssetAlreadyExistInScene(node_name):
                                cmds.shadingNode(node_type, asTexture = True , name = node_name)
                        if node_type in typeUtility or node_type in typeMRTexture or node_type in typeMREnv or node_type in typeMRLightMaps or node_type in typeMRMisc or node_type in typeMRConv or node_type in typeMRDisp or node_type in typeMRInternal:
                            if not doesAssetAlreadyExistInScene(node_name):
                                cmds.shadingNode(node_type, asUtility = True , name = node_name)

                if levelTwo.tag == 'ShadingEngine':
                    debug(app = None, method = 'createAll', message = 'Processing ShadingEngine...', verbose = False)
                    for levelThree in levelTwo.getchildren():
                        node_name  = '%s%s' % (prefix, levelThree.tag)
                        debug(app = None, method = 'createAll', message = 'ShadingEngine: node_name: %s' % node_name, verbose = False)
                        if '_cCc_' in node_name:
                            node_name = node_name.replace('_cCc_', ':')
                        node_type  = levelThree.attrib['value']
                        node_split = node_type.split(', ')
                        node_name  = node_split[0]
                        #node_name  = Namespace + node_name
                        node_name = '%s%s%s' % (Namespace, prefix, node_name)
                        node_type  = node_split[1]

                        if node_type == 'shadingEngine':
                            if not doesAssetAlreadyExistInScene(node_name):
                                cmds.sets(renderable = True, noSurfaceShader = True, empty = True, name = node_name)
    
                if levelTwo.tag == 'Attributes':
                    debug(app = None, method = 'createAll', message = 'Processing Attributes...', verbose = False)
                    for attributes in levelTwo.getchildren():
                        attrNode = attributes.tag
                        #attrNode = Namespace + attrNode
                        attrNode = '%s%s%s' % (Namespace, prefix, attrNode)
                        if '_aAa_' in attrNode:
                            attrNode = attrNode.replace('_aAa_', '[')
                            attrNode = attrNode.replace('_zZz_', ']')
                        if '_cCc_' in attrNode:
                            attrNode = attrNode.replace('_cCc_', ':')

                        attrValue =  attributes.attrib['value']
                        if not attrValue.startswith('[('):
                            try:
                                cmds.setAttr(attrNode, float(attrValue), lock = False)
                            except:
                                pass
                            try:
                                cmds.setAttr(attrNode, str(attrValue), type = 'string', lock = False)
                            except:
                                pass
                            try:
                                cmds.setAttr(attrNode, str(attrValue), type = 'double3', lock = False)
                            except:
                                pass
                        else:
                            #convert to list
                            evalList = eval(attrValue)
                            evalList = evalList[0]
                            if len(evalList) == 2:
                                try:
                                    cmds.setAttr(attrNode, evalList[0], evalList[1], type = 'double2', lock = False)
                                except:
                                    debug(app = None, method = 'createAll', message = '%s failed..' % attrNode, verbose = False)

                            if len(evalList) == 3:
                                try:
                                    cmds.setAttr(attrNode, evalList[0], evalList[1], evalList[2], type = 'double3', lock = False)
                                except:
                                    debug(app = None, method = 'createAll', message = '%s failed..' % attrNode, verbose = False)
    
    debug(app = None, method = 'createAll', message = 'FINSHED for %s...' % XMLPath, verbose = False)
    
def connectAll(XMLPath = '', parentGrp = '', Namespace = '', Root = 'MaterialNodes', selected = False, selectedOrigHrcName = '', xmlVersionNumber = ''):
    debug(app = None, method = 'connectAll', message = 'XMLPath: %s' % XMLPath, verbose = False)
    debug(app = None, method = 'connectAll', message = 'Namespace: %s' % Namespace, verbose = False)
    debug(app = None, method = 'connectAll', message = 'Root: %s' % Root, verbose = False)
    debug(app = None, method = 'connectAll', message = 'parentGrp: %s' % parentGrp, verbose = False)
    debug(app = None, method = 'connectAll', message = 'selected: %s' % selected, verbose = False)
    debug(app = None, method = 'connectAll', message = 'selectedOrigHrcName: %s' % selectedOrigHrcName, verbose = False)
    
    # If the namespace doesn't exist, the objects wont get named correctly
    # create the namespace
    if Namespace != "" and Namespace != ":":
        if not cmds.namespace( exists= Namespace[:-1] ):
            cmds.namespace( add = Namespace[:-1])
    if selected:
        prefix = '%s_' % selectedOrigHrcName
    else:
        prefix = ''

    # get the root of the XMLPath argument
    root = xml.parse(XMLPath).getroot()
    debug(app = None, method = 'connectAll', message = 'root XML.parse connected successfully...', verbose = False)
    
    # Create an iterator based on the the root argument
    shaderIterator = root.getiterator(Root)
    # Iterate on shader level
    for levelOne in shaderIterator:
        debug(app = None, method = 'connectAll', message = 'Entering levelOne in shaderIterator...', verbose = False)
        # Iterate on parent tag level
        if levelOne.getchildren():
            for levelTwo in levelOne:
                # For every node, set each attribute
                if levelTwo.tag == 'Connections':
                    debug(app = None, method = 'connectAll', message = 'Processing Connections...', verbose = False)
                    for connections in levelTwo.getchildren():                            
                        direction = connections.tag
                        connData = connections.attrib['value'].split(', ')
                        conn_srce = '%s%s%s' % (Namespace, prefix, connData[0])
                        conn_dest = '%s%s%s' % (Namespace, prefix, connData[1])

                        if not cmds.objExists(conn_srce):
                            conn_srce = '%s%s' % (Namespace, connData[0])
                            if cmds.objExists(conn_srce):
                                try:
                                    if not cmds.objectType(conn_srce) == 'mesh':
                                        conn_srce = '%s%s%s' % (Namespace, prefix, connData[0])
                                except RuntimeError:
                                    debug(app = None, method = 'connectAll', message = 'FAILED to if not cmds.objectType: conn_srce: %s' % conn_srce, verbose = False)
                                    pass

                        if not cmds.objExists(conn_dest):
                            conn_dest = '%s%s' % (Namespace, connData[1])
                            if cmds.objExists(conn_dest):
                                if not cmds.objectType(conn_dest) == 'mesh':
                                    conn_dest = '%s%s%s' % (Namespace, prefix, connData[1])

                        debug(app = None, method = 'connectAll', message = 'Connections: connData: %s' % connData, verbose = False)
                        debug(app = None, method = 'connectAll', message = 'Connections: conn_srce: %s' % conn_srce, verbose = False)
                        debug(app = None, method = 'connectAll', message = 'Connections: conn_dest: %s' % conn_dest, verbose = False)

                        if direction == 'DownStream':
                            try:
                                debug(app = None, method = 'connectAll', message = 'Connecting DownStream %s to %s now..' % (conn_srce, conn_dest), verbose = False)
                                if not cmds.isConnected(conn_srce, conn_dest):
                                    cmds.connectAttr(conn_srce, conn_dest, force = True)
                            except:
                                cmds.warning('Failed to connect %s to %s, skipping...' % (conn_srce, conn_dest))
                        else:
                            try:
                                debug(app = None, method = 'connectAll', message = 'Connecting Upstream %s to %s now..' % (conn_dest, conn_srce), verbose = False)
                                if not cmds.isConnected(conn_dest, conn_srce):
                                    cmds.connectAttr(conn_dest, conn_srce, force = True)
                            except:
                                cmds.warning('Failed to connect %s to %s, skipping...' % (conn_dest, conn_srce))
                
                ## NOW CONNECT THE SHADING ENGINES TO THE GEO
                if levelTwo.tag == 'ShadingEngine':
                    debug(app = None, method = 'connectAll', message = 'Processing ShadingEngine...', verbose = False)
                    
                    for sg in levelTwo.getchildren():
                        nodeData  = sg.attrib['value'].split(', ')
                        node_name = '%s%s%s' % (Namespace, prefix, nodeData[0])
                        node_type = nodeData[1]
                        
                        debug(app = None, method = 'connectAll', message = 'ShadingEngine: nodeData: %s' % nodeData, verbose = False)
                        debug(app = None, method = 'connectAll', message = 'ShadingEngine: node_name: %s' % node_name, verbose = False)
                        debug(app = None, method = 'connectAll', message = 'ShadingEngine: node_type: %s' % node_type, verbose = False)
                        #Method: connectAll:        ShadingEngine: nodeData: ['CHAR_Zip_MetalChimney_01_shd_SG', 'shadingEngine']
                        #Method: connectAll:        ShadingEngine: node_name: CHAR_Zip_MetalChimney_01_shd_SG
                        #Method: connectAll:        ShadingEngine: node_type: shadingEngine
                        
                        if sg.getchildren():
                            debug(app = None, method = 'connectAll', message = 'ShadingEngine: sg.getchildren(): %s' % sg.getchildren(), verbose = False)
                            for geo in sg.getchildren():
                                if geo.tag == 'Geo':
                                    origName = '|%s%s' % (parentGrp, geo.attrib['value'])
                                    debug(app = None, method = 'connectAll', message = 'ShadingEngine: origName: %s' % origName, verbose = False)

                                    # origNameInScene = origName.split('|')[-2]
                                    # debug(app = None, method = 'connectAll', message = 'ShadingEngine: origNameInScene: %s' % origNameInScene, verbose = False)
                                    if origName.endswith(']'):
                                        # "||ENV_MIDDLEHARBOUR_EAST_STATIC_ABC_STATIC_CACHES_hrc|HC_Bridge001_A_LND_hrc|geo_hrc|Bridge001_A_Plant002_hrc|HC_bridge001_a_plant002_60_geo.f[0:759]".split('|')[-2]
                                        # "HC_bridge001_a_plant002_60_geo.f[0:759]"
                                        origNameInScene = origName.split('|')[-1]
                                        debug(app = None, method = 'connectAll', message = 'ShadingEngine: origNameInScene: %s' % origNameInScene, verbose = False)
                                    else:
                                        # "||ENV_MIDDLEHARBOUR_EAST_STATIC_ABC_STATIC_CACHES_hrc|HC_Bridge001_A_LND_hrc|geo_hrc|Bridge001_A_bush_hrc|HC_bridge001_a_bush57_geo|HC_bridge001_a_bush57_geoShape".split('|')[-2]
                                        # "HC_bridge001_a_bush57_geo"
                                        origNameInScene = origName.split('|')[-2]
                                        debug(app = None, method = 'connectAll', message = 'ShadingEngine: origNameInScene: %s' % origNameInScene, verbose = False)

                                    ## Now get the actual freaking hrc group that was originally publish this is for the rebuild from a lighting publish as opposed to a surfVar assignment.
                                    if parentGrp:
                                        baseHRCGrp = origName.split('|')[3]
                                        debug(app = None, method = 'connectAll', message = 'ShadingEngine: baseHRCGrp: %s' % baseHRCGrp, verbose = False)
                                    else:
                                        if 'CACHES' not in origName:
                                            baseHRCGrp = origName.split('|')[2] 
                                            debug(app = None, method = 'connectAll', message = 'ShadingEngine: baseHRCGrp: %s' % baseHRCGrp, verbose = False)
                                        else:
                                            baseHRCGrp = origName.split('|')[3] 
                                            debug(app = None, method = 'connectAll', message = 'ShadingEngine: baseHRCGrp: %s' % baseHRCGrp, verbose = False)
                                    
                                    ## if it exists in the scene, assign the shader, else we have to look for all the LIB objects in the scene via their metaTags and process these accordingly.
                                    ## Processing multiple instances of the same geo!
                                    if cmds.objExists(origNameInScene):
                                        ## Okay so we have geo in the scene, but what about duplicates for reuse assets.... such as multiple bouys from the same base assets....
                                        ## First we have to list all the assets found in the scene..
                                        getPathToGeoInScene = cmds.ls(origNameInScene, l = True) ## list the objects in the scene with the transform name from the SRF publish, and make sure these return their full path
 
                                        if getPathToGeoInScene: ## Check there are any objects in the scene with the original name!
                                            for eachGeo in getPathToGeoInScene:## go through each of the transforms
                                                if selected: ## only do it if
                                                    matchFound = [each for each in eachGeo.split('|') if each == selectedOrigHrcName] or False
                                                    if matchFound: ## checks to see if the actual selected top level _hrc group is in the long name
                                                        try:
                                                            cmds.sets(eachGeo, edit=True, forceElement = node_name)
                                                            debug(app = None, method = 'connectAll', message = 'SUCCESS ShadingEngine Connection %s %s' % (origName, node_name), verbose = False)

                                                            ## Now add the version tag to the selected _hrc asset group
                                                            ###########################################################
                                                            if xmlVersionNumber:
                                                                _addVersionTag(matchFound[0], xmlVersionNumber)
                                                        except ValueError:
                                                            debug(app = None, method = 'connectAll', message = 'FAILED ShadingEngine: Failed Connection %s %s' % (origName, node_name), verbose = False)
                                                            #print                                                        
                                                else: ## just do it for every geo found in the scene with that name
                                                    matchFound = [each for each in eachGeo.split('|') if each == baseHRCGrp] or False
                                                    if matchFound: ## checks to see if the actual selected top level _hrc group is in the long name
                                                        try:
                                                            if cmds.nodeType(node_name) == 'shadingEngine':
                                                                cmds.sets(eachGeo, edit=True, forceElement = node_name)

                                                                ## Now add the version tag to the selected _hrc asset group
                                                                ###########################################################
                                                                if xmlVersionNumber:
                                                                    _addVersionTag(matchFound[0], xmlVersionNumber)
                                                            else:
                                                                cmds.confirmDialog(title = 'REBUILD SHADER', message = '"%s" is not a shadingEngine type, skip assigning\n"%s" to "%s"...' % (node_name, eachGeo, node_name), button = 'OK')
                                                            debug(app = None, method = 'connectAll', message = 'SUCCESS ShadingEngine Connection %s %s' % (origName, node_name), verbose = False)
                                                            #print
                                                        except ValueError:
                                                            debug(app = None, method = 'connectAll', message = 'FAILED ShadingEngine: Failed Connection %s %s' % (origName, node_name), verbose = False)
                                                            #print
                                    
                                    ## It doesn't exist, so lets lLook for the shading reconnect via the LIB object metaTags
                                    else:
                                        foundImportedGeo = {} ## format  fullDAGPath ; geoName
                                        debug(app = None, method = 'connectAll', message = 'No geo found in scene with original names from SRF, scanning LIB metaTags now...',  verbose = False)
                                        getAllLibGeo = [eachGeo for eachGeo in cmds.ls(type = 'transform')  if cmds.objExists('%s.LIBORIGNAME'  % eachGeo)]
                                        if getAllLibGeo:
                                            for eachGeo in getAllLibGeo:                                               
                                                ## if the attr value is the same as the original geo name continue...
                                                if cmds.getAttr('%s.LIBORIGNAME' % eachGeo) == origNameInScene:## we have found matching geo to assign to
                                                    debug(app = None, method = 'connectAll', message = 'Found matching geo...',  verbose = False)
                                                    ## Get the name to assign to (for readability)
                                                    getOrigName = cmds.getAttr('%s.LIBORIGNAME' % eachGeo)
                                                    debug(app = None, method = 'connectAll', message = 'MetaTags original geoName: %s' % getOrigName,  verbose = False)
                                                    
                                                    ## Get the full path to this new obj as the artist will have re parented this elsewhere..
                                                    fullPathToImportGeo = cmds.ls(eachGeo, l = True)
                                                    debug(app = None, method = 'connectAll', message = 'fullPathTo MetaTagged original geo: %s' % fullPathToImportGeo,  verbose = False)
                                                    
                                                    if fullPathToImportGeo:
                                                        ## Now add this to the list pathToGeoInScene :
                                                        if fullPathToImportGeo[0] not in foundImportedGeo:
                                                            foundImportedGeo[fullPathToImportGeo[0]] =  eachGeo
                                        
                                        debug(app = None, method = 'connectAll', message = 'foundImportedGeo: %s' % foundImportedGeo, verbose = False)
                                        ## Now process the list of geo that exist in the scene that match the geo in the xml and assign the shader
                                        if foundImportedGeo:
                                            debug(app = None, method = 'connectAll', message = 'FOUND matching geos in scene via metaTags. Processing now...', verbose = False)
                                            for fullPath, geoName in foundImportedGeo.items():
                                                try:
                                                    debug(app = None, method = 'connectAll', message = 'Assigning shader %s to %s|%sShape' % (node_name, fullPath, geoName), verbose = False)
                                                    cmds.sets('%s|%sShape' % (fullPath, geoName), edit=True, forceElement = node_name)
                                                except ValueError: ## if the whole thing fails ...
                                                    debug(app = None, method = 'connectAll', message = 'FAILED to connect  ShadingEngine:New Lib Geo Not Found: %s|%sShape' % (fullPath, geoName), verbose = False)
                                                except RuntimeError:
                                                    debug(app = None, method = 'connectAll', message = 'FAILED to connect  ShadingEngine:New Lib Geo Not Found: %s|%sShape' % (fullPath, geoName), verbose = False)
                                        else:
                                            
                                            pass

def reconnectLIBSHD(rootGrp = '', freshImport = True):
    """
    Function to help rebuild shaders on LIB assets that were imported into the system by the import tool
    """
    myXML = []
    if freshImport :
        if cmds.objExists('%s_import' % rootGrp):
            rootGrp = '%s_import' % rootGrp
        else:
            rootGrp = rootGrp
        
    ## Now look for all the LIB assets with the xml metatag
    for eachChild in cmds.listRelatives( '%s' % rootGrp, ad = True, type = 'transform'):
        if cmds.objExists('%s.LIBSHDXML' % eachChild):
            getPath = cmds.getAttr('%s.LIBSHDXML' % eachChild)
            if getPath not in myXML:
                myXML.extend([getPath])
                
    ## Now process all the xml paths for the LIB assets found in the scene
    if myXML:
        for eachXML in myXML:
            debug(app = None, method = 'reconnectLIBSHD', message = 'Creating shaders from %s' % eachXML, verbose = False)
            createAll(XMLPath = eachXML, parentGrp = '%s' % rootGrp, Namespace = '', Root = 'MaterialNodes')
            
            debug(app = None, method = 'reconnectLIBSHD', message = 'Connecting shaders now', verbose = False)
            connectAll(XMLPath = eachXML, parentGrp= '%s' % rootGrp, Namespace = '', Root = 'MaterialNodes')

def _listUpDownStreamConn( node = '', envConn = '', listLighting = False, Conn = None):
    """
    This processes into the xml
    """
    debug(app = None, method = '_listUpDownStreamConn', message = 'listLighting: %s' % listLighting, verbose = False)
    debug(app = None, method = '_listUpDownStreamConn', message = '_listUpDownStreamConn: %s' % node, verbose = False)
    
    odd, even, downConnections, upConnections, dictionaryDown, dictionaryUp, = [],[],[],[],[],[]
    loop = ['0','0']
    value1, value2, Direction = True, False, "DownStream"
    debug(app = None, method = '_listUpDownStreamConn', message = 'value1, value2, Direction: %s, %s, %s' % (value1, value2, Direction), verbose = False)
    
    for eachTurn in loop:
        connections = None
        try:
            connections = cmds.listConnections(node, source = value1, destination = value2, connections = True, plugs = True)
        except:
            pass
        debug(app = None, method = '_listUpDownStreamConn', message = 'connections: %s' % connections, verbose = False)
        if connections:
            odd  =  [connections[i] for i in range(len(connections)) if i % 2 == 1]
            even =  [connections[i] for i in range(len(connections)) if i % 2 == 0]

            debug(app = None, method = '_listUpDownStreamConn', message = 'odd, even: %s, %s' % (odd, even), verbose = False)                           
            for key, value in map(None,odd,even):
                if not listLighting:
                    if 'defaultShaderList1' not in key and 'materialInfo' not in key and 'defaultTextureList1' not in key and 'instObjGroups' not in key and 'lightLinker1' not in key and 'utilities' not in key and 'partition' not in value:
                        connXML = xml.SubElement(envConn, str(Direction), value = (str(key) + ", " + str(value) ))
                else:
                    debug(app = None, method = '_listUpDownStreamConn', message = 'Processing LIGHTS ...', verbose = False)
                    if 'lightList1' not in key and 'defaultLightSet' not in key:
                        debug(app = None, method = '_listUpDownStreamConn', message = 'key PRE FIX: %s' % key, verbose = False)
                        key = key.replace(':', '_cCc_')
                        key = key.replace('|', '_iIi_')
                        debug(app = None, method = '_listUpDownStreamConn', message = 'key POST FIX: %s' % key, verbose = False)
                        ## Add to connections List
                        debug(app = None, method = '_listUpDownStreamConn', message = 'Conn: %s' % Conn, verbose = False)
                        debug(app = None, method = '_listUpDownStreamConn', message = 'Direction: %s' % Direction, verbose = False)
                        debug(app = None, method = '_listUpDownStreamConn', message = 'key: %s' % key, verbose = False)
                        debug(app = None, method = '_listUpDownStreamConn', message = 'value: %s' % value, verbose = False)
                        connXML = xml.SubElement(Conn, str(Direction), value = (str(key) + ", " + str(value) )  )
                        debug(app = None, method = '_listUpDownStreamConn', message = 'connXML: %s' % connXML, verbose = False)
                        
        value1, value2, Direction = False, True, "UpStream  "
        debug(app = None, method = '_listUpDownStreamConn', message = 'value1, value2, Direction: %s, %s, %s' % (value1, value2, Direction), verbose = False)
        
    debug(app = None, method = '_listUpDownStreamConn', message = '_listUpDownStreamConn COMPLETE', verbose = False)

def _shading_attributes(  nodeName, nodetype, envAttrs):
    list_attributes = cmds.listAttr(nodeName, read = True, hasData = True, visible = True, scalarAndArray = False, multi = True, output = True)
    for attribute in list_attributes:
        if attribute != 'caching' and attribute != 'nodeState':
            nodeConn = nodeName + '.' + attribute
            nodeValue = cmds.getAttr(nodeConn)
            if str(nodeValue) == 'False':
                nodeValue = 0.0
            if str(nodeValue) == 'True':
                nodeValue = 1.0
            # get the rounded value of the attribute, there is no need to have 0.00000948193 as a value
            nodeConn = nodeConn.replace('[', '_aAa_')
            nodeConn = nodeConn.replace(']', '_zZz_')
            nodeConn = nodeConn.replace(':', '_cCc_')

            if type(nodeValue).__name__ != 'list':
                roundedValue = round(nodeValue, 3)
                attrXML = xml.SubElement(envAttrs, str(nodeConn), value = str(roundedValue)  )
            else:
                attrXML = xml.SubElement(envAttrs, str(nodeConn), value = str(nodeValue)  )

    if nodetype == 'file' or nodetype == 'mentalrayTexture':
        filePath = cmds.getAttr(nodeName + '.fileTextureName')
        if filePath == 'None':
            filePath = ''
        nodeName = nodeName.replace(':', '_cCc_')
        fileXML = xml.SubElement(envAttrs, str(nodeName + '.fileTextureName'), value = str(filePath)  )

def _light_attributes( nodeName, nodetype, Attrs):
    debug(app = None, method = '_light_attributes', message = 'Entering...', verbose = False)
    debug(app = None, method = '_light_attributes', message = 'nodeName: %s' % nodeName, verbose = False)
    debug(app = None, method = '_light_attributes', message = 'nodetype: %s' % nodetype, verbose = False)
    debug(app = None, method = '_light_attributes', message = 'Attrs: %s' % Attrs, verbose = False)
    
    list_attributes = cmds.listAttr(nodeName, hasData = True, visible = True, scalarAndArray = True, multi = True, output = True)
    debug(app = None, method = '_light_attributes', message = 'list_attributes: %s' % list_attributes, verbose = False)
    
    for attribute in list_attributes:
        if attribute != 'caching' and attribute != 'nodeState':
            debug(app = None, method = '_light_attributes', message = 'Processing attribute: %s' % attribute, verbose = False)
            nodeConn = '%s.%s' % (nodeName, attribute)
            nodeValue = cmds.getAttr(nodeConn)
            if str(nodeValue) == 'False':
                nodeValue = 0.0
            if str(nodeValue) == 'True':
                nodeValue = 1.0
            # get the rounded value of the attribute, there is no need to have 0.00000948193 as a value
            # original roundedValue was 3, but this was causing issues with sun&sky unit conversion, due to it being low by default
            roundedValue = round(nodeValue, 6)
            debug(app = None, method = '_light_attributes', message = 'roundedValue: %s' % roundedValue, verbose = False)
            nodeConn = nodeConn.replace('[', '_aAa_')
            nodeConn = nodeConn.replace(']', '_zZz_')
            nodeConn = nodeConn.replace(':', '_cCc_')
            nodeConn = nodeConn.replace('+', '_tTt_')
            nodeConn = nodeConn.replace('-', '_mMm_')
            nodeConn = nodeConn.replace('|', '_iIi_')
            debug(app = None, method = '_light_attributes', message = 'nodeConn: %s' % nodeConn, verbose = False)
            
            ## Add to _attributes List
            attrXML = xml.SubElement(Attrs, str(nodeConn), value = str(roundedValue)  )
            debug(app = None, method = '_light_attributes', message = 'attribute %s processed fine...' % attribute, verbose = False)

    debug(app = None, method = '_light_attributes', message = 'Atts processed....', verbose = False)
    ## Get file texture path name
    if nodetype == 'file' or nodetype == 'mentalrayTexture':
        filePath = cmds.getAttr(nodeName + '.fileTextureName')
        if filePath == 'None':
            filePath = ''
        nodeName = nodeName.replace(':', '_cCc_')
        fileXML = xml.SubElement(Attrs, str(nodeName + '.fileTextureName'), value = str(filePath)  )
        debug(app = None, method = '_light_attributes', message = 'File texture paths processed....', verbose = False)
    
    ## Get Illuminates by Default as an attribute listing
    cmds.select(clear = True)
    typeLights = cmds.ls(dag = True, lights = True)
    if nodeName in typeLights:
        objParent = cmds.listRelatives( nodeName, parent=True )
        objParent = objParent[0]
        
        ## Find Illuminates by Default
        connections = cmds.listConnections(objParent)
        inst = objParent + '.instObjGroups'
        dfs = cmds.connectionInfo(inst, dfs = True)
        
        ## If off then add attr LLink
        if dfs == []:
            attrXML = xml.SubElement(Attrs, '%s.illuminatesDefault' % str(nodeName), value = '0.0'  )
        else:
            attrXML = xml.SubElement(Attrs, '%s.illuminatesDefault' % str(nodeName), value = '1.0'  )
        debug(app = None, method = '_light_attributes', message = 'illuminatesDefault processed....', verbose = False)
        
    debug(app = None, method = '_light_attributes', message = '_light_attributes COMPLETE', verbose = False)

def exportPrep(lighting = False, path = ''):
    """
    Export all shaders or lighting to XML
    @param lighting: If you want to export the lights to xml or not
    @type lighting: Boolean  
    @param options: This is the options for export
    @type options: String
    """
    xmlFilePath = path
    debug(app = None, method = 'exportPrep', message = 'xmlFilePath: %s' % xmlFilePath, verbose = False)
    transformOnly, newList = [],[] ## For lighting
    sceneName, dirName, sceneSplit, scene, newPath, xmlFile, = [],[],[],[],[],[] ## for SHD and Lighting   
    
    # Create a root element
    root = xml.Element('root')
    debug(app = None, method = 'exportPrep', message = 'root created successfully...', verbose = False)

    #################
    ## Lighting Attrs
    if lighting:
        Light           = xml.SubElement(root,'Lights')
        Nodes           = xml.SubElement(Light,'Nodes')
        Attrs           = xml.SubElement(Light,'Attributes')
        Conn            = xml.SubElement(Light,'Connections')
        LLink           = xml.SubElement(Light,'LightLinking')
    else:
        envMaterials    = xml.SubElement(root,'MaterialNodes')
        envNodes        = xml.SubElement(envMaterials,'Nodes')
        envAttrs        = xml.SubElement(envMaterials,'Attributes')
        envConn         = xml.SubElement(envMaterials,'Connections')
        envSG           = xml.SubElement(envMaterials,'ShadingEngine')
        sEngine         = cmds.ls(type = 'shadingEngine')
        
    #Lights category
    ignoreType = ('core_renderpass', 'core_lens', 'core_globals', 'core_carpaint', "p_MegaTK_pass", "core_state", "core_env_rayswitch", "core_env_light_base", "core_mia_wrapper",
                  "core_carpaint_wrapper","core_pass_sss","core_material_override","core_sss_irradiance","core_normaloutput","core_simple_sss2",
                  "core_skin_sss2","core_texture_lookup","core_carpaint")
    typeLights      = cmds.listNodeTypes( 'light' )
    typeMRLights    = cmds.listNodeTypes( 'rendernode/mentalray/light' )        
    typeMRLens      = cmds.listNodeTypes( 'rendernode/mentalray/lens' )
    typeMRGeometry  = cmds.listNodeTypes( 'rendernode/mentalray/geometry')
    typeSet         = ['objectSet']
    
    #################
    ## Shading Attrs
    #################
    ## Lighting AND Shading 
    typeShader      = cmds.listNodeTypes( 'shader' )
    typeTexture     = cmds.listNodeTypes( 'texture' )
    typeUtility     = cmds.listNodeTypes( 'utility' )
    typeMRTexture   = cmds.listNodeTypes( 'rendernode/mentalray/texture' ) or []
    typeMRDisp      = cmds.listNodeTypes( 'rendernode/mentalray/displace' ) or []
    typeMREnv       = cmds.listNodeTypes( 'rendernode/mentalray/environment' )
    typeMRLightMaps = cmds.listNodeTypes( 'rendernode/mentalray/lightmap' )
    typeMRMisc      = cmds.listNodeTypes( 'rendernode/mentalray/misc' )
    typeMRConv      = cmds.listNodeTypes( 'rendernode/mentalray/conversion')
    typeMRInternal  = cmds.listNodeTypes( 'rendernode/mentalray/internal')
    
    debug(app = None, method = 'exportPrep', message = 'All vars created successfully...' , verbose = False)
    
    ## Now do the main xml process
    if lighting:# DO THE LIGHTING XML EXPORT
        debug(app = None, method = 'exportPrep', message = 'Doing LIGHTS xml export now...', verbose = False)
        allNodes = list(sorted(set(typeLights + typeMRLights + typeMREnv + typeMRInternal + typeMRMisc + typeMRLens + typeSet)))
        debug(app = None, method = 'exportPrep', message = 'allNodes: %s' % allNodes, verbose = False)

        for nodetype in allNodes:
            objs = cmds.ls(type = nodetype)
            if objs:
                for obj in objs:
                    if not cmds.referenceQuery( obj, isNodeReferenced=True ):
                        debug(app = None, method = 'exportPrep', message = 'Processing.... %s' % obj, verbose = False)
                        Type = cmds.nodeType(obj)
                        debug(app = None, method = 'exportPrep', message = '\tType: %s' % Type, verbose = False)

                        if Type not in ignoreType:
                            debug(app = None, method = 'exportPrep', message = 'Type: %s is not in ignoreType...' % Type, verbose = False)
                            if Type == 'core_environment':
                                connected = cmds.listHistory(obj)

                                for item in connected:
                                    ## Get Parent of light, so I can get transforms
                                    objParent = cmds.listRelatives( obj, parent=True )
                                    newType = cmds.nodeType(item)
                                    nodesXML = xml.SubElement(Nodes, str(item), value = str(newType) )
                                    
                                    item = item.replace('_cCc_', ':')
                                    debug(app = None, method = 'exportPrep', message = 'item: %s' % item, verbose = False)
                                    
                                    debug(app = None, method = 'exportPrep', message = '_listUpDownStreamConn now ...', verbose = False)
                                    _listUpDownStreamConn(item, True, Conn)

                                    debug(app = None, method = 'exportPrep', message = '_light_attributes now ...', verbose = False)
                                    _light_attributes(nodeName = item, nodetype = newType, Attrs = Attrs)

                                    isObjType = isinstance(objParent, basestring)
                                    if objParent != None and isObjType is False:
                                        objParent = objParent[0].replace(':', '_cCc_')
                                        _light_attributes(nodeName = objParent, nodetype = newType, Attrs = Attrs)
        
                            if Type != 'shadingEngine' and Type != 'objectSet' and Type != 'core_environment':
                                # Get connections of lights to find connected nodes that need their _attributes captured
                                connectedNodes = cmds.listConnections(obj, source = True, destination = True, plugs = True, connections = True)
                                debug(app = None, method = 'exportPrep', message = 'connectedNodes: %s' % connectedNodes, verbose = False)
                                
                                if connectedNodes:
                                    for each in connectedNodes:
                                        eachName = each.split('.')
                                        eachType = cmds.nodeType(eachName[0])
                                        if eachType in typeTexture or eachType in typeUtility and eachType not in ignoreType:
                                            _light_attributes(nodeName = eachName[0], nodetype = eachType, Attrs = Attrs)
                                            newList.extend([eachName[0]])

                                ## Get Parent of light, so I can get transforms
                                objParent = cmds.listRelatives( obj, parent=True )
                                debug(app = None, method = 'exportPrep', message = 'objParent: %s' % objParent, verbose = False)
                                
                                ## Replace invalid characters temporarily
                                obj = obj.replace(':', '_cCc_')
                                debug(app = None, method = 'exportPrep', message = 'obj: %s' % obj, verbose = False)
                                
                                # Add to Nodes List
                                nodesXML = xml.SubElement(Nodes, str(obj), value = str(Type) )
        
                                obj = obj.replace('_cCc_', ':')## put back the way it was
                                debug(app = None, method = 'exportPrep', message = 'obj back to normal: %s' % obj, verbose = False)
                                
                                debug(app = None, method = 'exportPrep', message = '_listUpDownStreamConn now ...', verbose = False)
                                _listUpDownStreamConn(node = obj, listLighting = True, Conn = Conn)
                                
                                debug(app = None, method = 'exportPrep', message = '_light_attributes now ...', verbose = False)
                                debug(app = None, method = 'exportPrep', message = '\tnodeType: %s' % Type, verbose = False)
                                _light_attributes(nodeName = obj, nodetype = Type, Attrs = Attrs)
                                
                                if objParent != None:
                                    objParent = objParent[0].replace(':', '_cCc_')
                                    _light_attributes(nodeName = objParent, nodetype = Type, Attrs = Attrs)

                            ## If objectSet and named LightLink_ get list of objects
                            if Type == 'objectSet' and 'LightLink_' in obj:
                                try:
                                    setContaints = cmds.sets( obj, q=True )
                                    setsXML = xml.SubElement(LLink, str(obj), value = str(Type) )
                                    for objs in setContaints:
                                        objs = objs.replace(':', '_cCc_')
                                        objs = objs.replace('|', '_iIi_')
                                        objC = xml.SubElement(setsXML, str(objs), value = str(Type) )
                                except:
                                    pass
                            
    else:                       ## DO SHD EXPORT TO XML INSTEAD
        debug(app = None, method = 'exportPrep', message = 'Doing SHD xml export now...', verbose = False)
        allNodes = list(sorted(set(typeShader + typeTexture + typeUtility + typeMRTexture + typeMRDisp + typeMREnv + typeMRLightMaps + typeMRMisc + typeMRConv + typeMRInternal + sEngine)))           
        for nodetype in allNodes:
            try:
                if cmds.nodeType(nodetype) == 'shadingEngine':
                    debug(app = None, method = 'exportPrep', message = 'Doing SHD shadingEngines...', verbose = False)
                    if nodetype != 'initialParticleSE' and nodetype != 'initialShadingGroup':
                        if cmds.listConnections(nodetype, type = 'mesh') or cmds.listConnections(nodetype, type = 'nurbsSurface'):
                            SGArray = nodetype, 'shadingEngine'
                            engineNameXML = xml.SubElement(envSG, 'SGNode', value = (str(SGArray[0]) + ", " + str(SGArray[1]) )  )
                            # for obj in cmds.listConnections( nodetype, shapes = True, destination = False):
                            for obj in cmds.sets(nodetype, query = True): ## takes account into faces assignment as well written into xml something like ball.f[1:100]
                                if cmds.nodeType(obj) == 'mesh' or cmds.nodeType(obj) == 'nurbsSurface':
                                    fullPath = cmds.ls(obj, long = True)
                                    debug(app = None, method = 'exportPrep', message = 'fullPath: %s' % fullPath, verbose = False)
                                    engineObjXML = xml.SubElement(engineNameXML, 'Geo', value = str(fullPath[0]))
            except:
                objs = cmds.ls(type = nodetype)
                if objs != []:
                    for obj in objs:
                        if obj != 'lambert1' and obj != 'particleCloud1':
                            objType = cmds.nodeType(obj)
                            obj = obj.replace(':', '_cCc_')
                            nodesXML = xml.SubElement(envNodes, str(obj), value = str(objType) )
                            obj = obj.replace('_cCc_', ':')
                            _listUpDownStreamConn(node = obj, envConn = envConn)
                            _shading_attributes(obj, objType, envAttrs)

    debug(app = None, method = 'exportPrep', message = 'XML PREP FINISHED....', verbose = False)   
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # EXPORT DATA TO XML
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # find new xml path and if it doesn't exist create the folder
    # open the file for writing and then create an ElementTree object from the root element and close it again
    debug(app = None, method = 'exportPrep', message = 'dirName: %s' % os.path.dirname(xmlFilePath), verbose = False) 
    
    if not os.path.isdir(os.path.dirname(xmlFilePath)):
        os.mkdir(os.path.dirname(xmlFilePath))
    
    xmlfile = open(xmlFilePath, 'w')
    xml.ElementTree(root).write(xmlFilePath, encoding="utf-8")
    xmlfile.close()
    debug(app = None, method = 'exportPrep', message = 'XML EXPORT FINISHED....' % allNodes, verbose = False)
    
def repathFileNodesForWork():
    """
    Sets the working file nodes back to /work not /publish
    """
    listAllFileNodes = cmds.ls(type = 'file') + cmds.ls(type = "mentalrayTexture")
    if listAllFileNodes:
        try:
            [cmds.setAttr('%s.fileTextureName' % eachFile, 'work/maya'.join(cmds.getAttr('%s.fileTextureName' % eachFile).split('publish')), type = 'string') for eachFile in listAllFileNodes if 'work/maya' not in cmds.getAttr('%s.fileTextureName' % eachFile)]
        except:
            pass

def repathFileNodesForPublish():
    """
    Sets the fileIn nodes to publish for secondary push of files from work/sourceimags to /publish/sourceimages
    """
    listAllFileNodes = cmds.ls(type = 'file') + cmds.ls(type = "mentalrayTexture")
    if listAllFileNodes:
        try:
            [cmds.setAttr('%s.fileTextureName' % eachFile, 'publish'.join(cmds.getAttr('%s.fileTextureName' % eachFile).split('work/maya')), type = 'string') for eachFile in listAllFileNodes if 'publish' not in cmds.getAttr('%s.fileTextureName' % eachFile)]
        except:
            pass

def doThumbs(path = ''):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # GENERATE ALL THUMBS
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
    ## Convert image to thumbnail size using openMaya instead of PIL
    ## file all unique files and convert them into this specific folder
    import os, sys
    import maya.OpenMaya as om
    debug(None, method = 'doThumbs', message = 'doThumbs started...', verbose = False)
    debug(None, method = 'doThumbs', message = 'path: %s' % path, verbose = False)
    failedDG = True ## True is a pass False is a fail

    filesToProcess = []
    ## get a list of all the file in nodes
    listAllFileNodes = cmds.ls(type = 'file') + cmds.ls(type = "mentalrayTexture")
    
    publishFolder =  r'%s' % path # %s/publish/sourceimages/256/' % ('/').join(originalFile.split('/')[0:6])
    debug(None, method = 'doThumbs', message = 'publishFolder: %s' % publishFolder, verbose = False)
    
    ## Now process each into native list
    for eachFileNode in listAllFileNodes:
        originalFile = r'%s' % cmds.getAttr('%s.fileTextureName' % eachFileNode)
        debug(None, method = 'doThumbs', message = 'originalFile: %s' % originalFile, verbose = False)
        ## Now add to the dictionary
        filesToProcess.extend([originalFile.replace('\\', '/')])

    for eachFile in filesToProcess:
        if os.path.isfile(eachFile):
            try:
                outputFileName = '%s.png' % eachFile.split('/')[-1].split('.')[0]
                debug(None, method = 'doThumbs', message = 'outputFileName: %s' % outputFileName, verbose = False)
                
                ## now use openMaya to process the image conversion
                image = om.MImage()
                image.readFromFile(eachFile)
                image.resize( 256, 256, 0 )
                finalOutputPath = '%s/%s' % (publishFolder, outputFileName)
                debug(None, method = 'doThumbs', message = 'finalOutputPath: %s' % finalOutputPath, verbose = False)
                
                image.writeToFile(finalOutputPath, 'png')
                debug(None, method = 'doThumbs', message = 'SUCCESSFUL IMAGE PROCESS: finalOutputPath: %s' % finalOutputPath, verbose = False)
                
                
            except RuntimeError:
                debug(None, method = 'doThumbs', message = 'FAILED TO PROCESS: finalOutputPath: %s' % finalOutputPath, verbose = False)
                
                pass

        else:
            cmds.warning('FAILED --- FILE NOT FOUND: %s' % eachFile)
            
            failedDG = False
            
    ## now return the checks as good or bad
    debug(None, method = 'doThumbs', message = 'failedDG: %s' % failedDG, verbose = False)
    return failedDG

def copyHiRes(destFolder = ''):
    """
    Copys across the files found in the scene to the folder specified
    Must send a maya friendly destFolder
    @param destFolder: path/to/my/texturefolder
    @type destFolder: String
    """ 
    nativeList, appendList= [],[]
    listAllFileNodes = cmds.ls(type = 'file') + cmds.ls(type = "mentalrayTexture")
    debug(app = None, method = 'copyHiRes', message = 'destFolder: %s' % destFolder, verbose = False)
    
    ## Now process all the file paths
    for eachFileNode in listAllFileNodes:
        texturePath = r'%s' % cmds.getAttr(eachFileNode + '.fileTextureName')
        debug(app = None, method = 'copyHiRes', message = 'texturePath: %s' % texturePath, verbose = False)
        if texturePath.replace('\\','/') not in nativeList:
            nativeList.extend([texturePath.replace('\\','/')])

    debug(app = None, method = 'copyHiRes', message = 'nativeList: %s' % nativeList, verbose = False)
    for file_name in nativeList:
        if (os.path.isfile(file_name)):
            shutil.copy(file_name, destFolder)
            debug(app = None, method = 'copyHiRes', message = 'SUCCESS file %s copied to %s' % (file_name, destFolder), verbose = False)
        else:
            debug(app = None, method = 'copyHiRes', message = 'FILE NOT FOUND %s' % file_name, verbose = False)
            pass

def disconnectTextureInfo( Info):
    connections = []
    ## We need to specify shape because fluids textures are shape nodes
    ## as well as being textures.
    connections = cmds.listConnections("%s.texture" % Info, connections = True, shapes = True)
    if connections:
        cmds.disconnectAttr('%s.message' % connections[1], connections[0])
    else:
        cmds.warning('No connections found..')

def findMaterialInfo(message):
    getCons = cmds.listConnections(message)
    for each in getCons:
        if cmds.objectType(each) == "materialInfo":
            return each

def fixResolution():
    debug(app = None, method = 'fixResolution', message = 'Fixing Resolutions now...', verbose = False)
    allLambert = cmds.ls(type = 'lambert')
    
    for eachLambert in allLambert:
        debug(app = None, method = 'fixResolution', message = 'Processing: %s now...' % eachLambert, verbose = False)
        if cmds.ls('%s.message' % eachLambert):
            
            matInfo = findMaterialInfo('%s.message' % eachLambert)
            debug(app = None, method = 'fixResolution', message = 'matInfo: %s' % matInfo, verbose = False)
            
            if matInfo:
                texture = ''
                try:
                    texture = cmds.listConnections("%s.texture[0]" % matInfo)[0]
                except TypeError:
                    pass
                
                if texture:            
                    try:
                        resolution = cmds.listAttr(texture, string = 'resolution')
                    except ValueError:
                        pass
        
                    if resolution:
                        cmds.deleteAttr(texture, at = 'resolution')
                        disconnectTextureInfo(matInfo)
                        cmds.addAttr(texture, ln = "resolution", at = 'long', dv = 32)
                        cmds.connectAttr("%s.message" % texture, "%s.texture[0]" % matInfo)
                        cmds.setAttr("%s.resolution" % texture, 256)
                    else:
                        cmds.addAttr(texture, ln = "resolution", at = 'long', dv = 32)
                        cmds.setAttr("%s.resolution" % texture, 256)

def downgradeShaders():
    """
    Initially cleans the shadingGroups to remove duplicates to circumvent a maya bug, when you create a shader using 'Create New Material'
    Then creates a simplified lambert shader that gets connected to the surfaceShader slot of the shadingGroup
    Then force disconnect the material info node to render the lambert instead. 
    Assign all texture paths to point to their 256x256px counterparts.    
    """
    debug(app = None, method = 'downgradeShaders', message = 'DowngradeShaders now...', verbose = False)
    ## Get all the shading groups assigned to the shapes in the scene
    SGused = []
    for shape in cmds.ls(shapes = True):
        dest = cmds.listConnections(shape, destination = True, source = False, plugs = False, type = 'shadingEngine')
        if dest:
            SGused.append(dest[0])     
    
    debug(app = None, method = 'downgradeShaders', message = 'SGused: %s' % SGused, verbose = False)
    
    ## FIX MESSAGE CONNECTIONS TO SGs
    ## Fix for incorrect shadingGroup Connection to material...for some reason I had message instead of outValue..this will fix all shaders. 
    listShaders = cmds.ls(materials = True)
    for shader in listShaders:
        listSG = cmds.listConnections(shader, source = False, destination = True, connections = True, plugs = True, type = 'shadingEngine')
        if listSG:
            for conn in listSG:
                if conn.endswith('Shader'):
                    connInfo = cmds.connectionInfo(conn, sourceFromDestination= True)
                    if '.message' in connInfo:
                        shader = connInfo.split('.')[0]
                        cmds.disconnectAttr(connInfo, conn)
                        cmds.connectAttr('%s.outValue' % shader, conn)     
        
    ## Get the core shading connections now
    connectedShaders = []
    listCoreShaders = cmds.ls(type = ('core_mia_material', 'core_material','core_surface_shader')) 
    for shader in listCoreShaders:
        getConnection, getDiff, getColour, getDiffFile, getDiffColour, getShadingEngine, SG, matInfo = [],[],[],[],[],[],[],[]
        getIncandColour, getColourFile = [],[]
        getConnection =  cmds.listConnections(shader, connections = True, plugs = True)
        ## Now check for file connections into diffuse or color
        getDiff = [i for i in getConnection if '.diffuse' in i if not '.diffuseA' in i]
        getColour = [i for i in getConnection if '.colour' in i if not '.colourA' in i]
        if getDiff:
            getDiffFile = cmds.connectionInfo(getDiff[0], sourceFromDestination= True)
        else:
            getDiffColour = cmds.getAttr('%s.diffuse' % shader)
    
        if getColour:
            getColourFile = cmds.connectionInfo(getColour[0], sourceFromDestination= True)
        else:
            try:
                getIncandColour = cmds.getAttr('%s.colour' % shader)
            except ValueError:
                pass
    
        ## Now find the shading engine for the shader
        getShadingEngine = cmds.listConnections(shader, destination = True, source = False, plugs  = True, type = 'shadingEngine')
        if not getShadingEngine:
            SG = cmds.listConnections(shader, destination = True, source = False)
        else:
            for listSG in getShadingEngine:
                SG = listSG.split('.')
                SG = SG[0] 
        ## Now get the materialInfo used by the SG
        if SG:
            matInfo = cmds.listConnections(SG, type = 'materialInfo')
            ## Now build the new lambert                
            newMaterial = cmds.shadingNode('lambert', asShader = True, name = ('_DGS_%s' % shader) )
            if isinstance(getDiffFile, unicode) or isinstance(getColourFile, unicode):
                try:
                    cmds.connectAttr(getDiffFile, '%s.color' % newMaterial, force = True)
                except:
                    cmds.connectAttr(getColourFile, '%s.color' % newMaterial, force = True)    
            else:
                if getDiffColour:
                    cmds.setAttr('%s.color' % newMaterial, getDiffColour[0][0], getDiffColour[0][1], getDiffColour[0][2], type = 'double3')
                else:
                    cmds.setAttr('%s.incandescence' % newMaterial, getIncandColour[0][0], getIncandColour[0][1], getIncandColour[0][2], type = 'double3')
            try:
                cmds.connectAttr(newMaterial + '.outColor', SG + '.surfaceShader', force = True)
                cmds.disconnectAttr(newMaterial + '.outColor', SG + '.surfaceShader')
                cmds.connectAttr(newMaterial + '.outColor', SG + '.surfaceShader', force = True)
            except TypeError:
                print 'ERROR: Skipping %s due to issue with concatenation...' % newMaterial
            if matInfo != None:
                textureChannel = cmds.listConnections(matInfo[0] + '.texture',connections = True, shapes = True, plugs = True)
                if textureChannel != None:
                    for texture in textureChannel:
                        if 'texture[' in texture:
                            try:cmds.disconnectAttr(getDiffFile[:-9] + '.message', texture)
                            except:pass
                    try:cmds.connectAttr(getDiffFile[:-9] + '.message', matInfo[0] + '.texture[0]')
                    except:pass
            else:
                continue
                
    listAllFileNodes = cmds.ls(type = 'file') + cmds.ls(type = "mentalrayTexture")
    for eachFileNode in listAllFileNodes:
        origTexturePath = cmds.getAttr(eachFileNode + '.fileTextureName')
        (filepath, nameOnly) = os.path.split(origTexturePath)
        newTexturePath = '%s/256/%s' % (filepath, nameOnly)
        cmds.setAttr('%s.fileTextureName' % eachFileNode, newTexturePath, type = 'string')
    ## Now delete all the core shaders
    try:
        cmds.delete(listCoreShaders)
    except TypeError:
        pass
    ## Now clean up any core globals from the scene
    coreLens = cmds.ls(type = 'core_lens')
    coreGlobals = cmds.ls(type = 'core_globals')
    for each in coreLens:
        cmds.lockNode(each, lock = False)
        cmds.delete(each)
    for each in coreGlobals:
        cmds.lockNode(each, lock = False)
        cmds.delete(each)
    
    ## Force a final cleanup
    mel.eval("MLdeleteUnused();")
    
    ## Rename SG's to their materials name_SG
    shaderTypes = ['blinn', 'lambert', 'phong', 'phongE', 'core_material']
    for eachType in shaderTypes:
        for each in cmds.ls(type = eachType):
            getConnections = cmds.listConnections(each, type = 'shadingEngine')
            if 'initial' not in getConnections[0]:
                cmds.rename(getConnections, '%s_SG' % each)
    
    ## now do a quick disconnect and reconnect to force shaders to show properly in viewport
    listShaders = cmds.ls(materials = True)
    debug(app = None, method = 'downgradeShaders', message = 'listShaders: %s' % listShaders, verbose = False)
    for shader in listShaders:
        listSG = cmds.listConnections(shader, source = False, destination = True, connections = True, plugs = True, type = 'shadingEngine')
        debug(app = None, method = 'downgradeShaders', message = 'listSG: %s' % listSG, verbose = False)
        try:
            cmds.disconnectAttr(listSG[0], listSG[1])
            cmds.connectAttr(listSG[0], listSG[1])
        except TypeError:
            cmds.warning('FAILED to disconnect and reconnect shader!')
            
    ## FIX TGA TO PNG
    allFiles = cmds.ls(type = 'file') + cmds.ls(type = "mentalrayTexture")
    for eachFile in allFiles:
        cmds.setAttr('%s.fileTextureName' % eachFile,  '%s.png' % cmds.getAttr('%s.fileTextureName' % eachFile).split('.')[0], type = 'string')
        cmds.setAttr('%s.colorProfile' % eachFile,  3)
        
    ## SEARCH FOR EXISTING CORE NODES
    ## IF OBJS STILL ATTACHED TO A CORE NODE SEARCH THROUGH THE SHADING HEIRACHY
    ## GET THE SWATCH COLOR AND DISCONNECT THE DIFFUSE FILE AND REPLACE WITH THE COLOUR
    badNodes,getTexture = [],[]
    listMRnodes = cmds.listNodeTypes( 'rendernode/mentalray')
    listShader  = cmds.listNodeTypes( 'shader')
    for eachNode in listMRnodes:
        if 'core_' in eachNode:
            objs = cmds.ls(type = eachNode)
            if objs != []:
                badNodes.append(objs[0])
    
    if badNodes != []:            
        for bad in badNodes:
            for each in cmds.listHistory( bad, allFuture = True):
                if cmds.nodeType(each) == 'file':
                    getTexture.append(each)    
            for each in cmds.listHistory( bad, future = True):            
                for shader in listShader:
                    if cmds.nodeType(each) == shader:
                        if getTexture != []:
                            cmds.connectAttr('%s.outColor' % getTexture[0], '%s.color' % each, force = True)
                        else:
                            getTempColour = cmds.getAttr('%s.color' % each)
                            getColourFile = cmds.listConnections('%s.color' % each, connections = True, plugs = True)
                            cmds.disconnectAttr(getColourFile[1], getColourFile[0])
                            cmds.setAttr('%s.color' % each, getTempColour[0][0], getTempColour[0][1], getTempColour[0][2], type = 'double3')  
        print 'Fixed existing core nodes ruinifying the viewport display, potentially crashing viewport!'         
    
    mel.eval("MLdeleteUnused();")
    fixResolution()
########################## END SHADING XML EXPORT SCRIPTS #################################################
###########################################################################################################

###########################################################################################################
########################## START LIGHTING XML EXPORT SCRIPTS ##############################################

def _remakeLL():
    """
    reassign linked lights/sets to lights/objects, sets get recreated later down
    """
    allSets = cmds.listSets(allSets= True)
    for each in allSets:
        if each[:10] == 'LightLink_':
            lightSet = each
            light = each[10:]
            setObjs = cmds.sets( lightSet, q=True )
            cmds.delete(lightSet)
            cmds.select(setObjs, light, replace = True)
            cmds.lightlink(make = True, useActiveLights = True, useActiveObjects = True)

def _reassociateLL():
    """
    Create objectSets to light Link to
    """
    cmds.select(clear = True)
    for nodetype in cmds.listNodeTypes( 'light' ):
        objs = cmds.ls(type = nodetype)
        if objs != []:
            for obj in objs:
                objParent = cmds.listRelatives( obj, parent=True )
                objParent = objParent[0]
                # Find Illuminates by Default
                connections = cmds.listConnections(objParent)
                inst = objParent + '.instObjGroups'
                dfs = cmds.connectionInfo(inst, dfs = True)
                # If off then add attr LLink
                if dfs == []:
                    objects = cmds.lightlink( query=True, light = obj, hierarchy = False, transforms = True, shapes = True )
                    createSet = cmds.sets( name = 'LightLink_' + str(objParent) )
                    setType = cmds.nodeType(createSet)
                    for each in objects:
                        if cmds.nodeType(each) == 'transform':
                            noShape = cmds.listRelatives (each, fullPath = True, shapes = True)
                            if noShape != None:
                                transformShape = cmds.listRelatives(noShape[0],fullPath = True, parent = True)
                                cmds.sets(transformShape[0], edit = True, addElement = createSet)
  
def _runLights():
    """
    Fix shapeName to match transform...otherwise XML can't find proper name
    """
    for nodetype in cmds.listNodeTypes( 'light' ):
        objs = cmds.ls(type = nodetype)
        if objs != []:
            for obj in objs:
                objParent = cmds.listRelatives( obj, parent=True )
                objParent = objParent[0]
                sansShape = obj.replace('Shape','')
                if objParent != sansShape:
                    addShape = objParent + 'Shape'
                    cmds.rename(obj, addShape)
    
    ## Create Light Link optimisations first.
    _remakeLL()
    _reassociateLL()
    
    conn = cmds.listConnections('lightLinker1', connections= True, plugs = True)
    allConn = zip(conn[::2], conn[1::2])
    for each in allConn:
        if 'initialParticleSE' not in each[1] and 'defaultLightSet' not in each[1] and 'initialShadingGroup' not in each[1]:
            cmds.disconnectAttr(each[1],each[0])
    
    allSets = cmds.listSets(allSets= True)
    for each in allSets:
        if each[:10] == 'LightLink_':
            for attr in cmds.listAttr(each):
                if '_Llink' in attr:
                    lightParent =  cmds.listRelatives(attr[:-6], parent = True)
                    lightParent = lightParent[0]
                    Set = each
                    setName = Set[10:]
                    if lightParent in setName:
                        cmds.select(lightParent, Set, replace = True, noExpand = True)
                        cmds.lightlink(make =True, useActiveLights = True, useActiveObjects = True)
    
    cmds.select(clear = True)
    
    # Re connect lightLinks to to lights illuminating everything
    for nodetype in cmds.listNodeTypes( 'light' ):
        objs = cmds.ls(type = nodetype)
        if objs != []:
            for obj in objs:
                objParent = cmds.listRelatives( obj, parent=True )
                objParent = objParent[0]
                # Find Illuminates by Default
                connections = cmds.listConnections(objParent)
                inst = objParent + '.instObjGroups'
                dfs = cmds.connectionInfo(inst, dfs = True)
                # If off then add attr LLink
                if dfs != []:
                    cmds.select(clear = True)
                    allSG = cmds.ls(type = 'shadingEngine')
                    cmds.select(allSG, noExpand = True)
                    cmds.select(obj, add = True)
                    cmds.lightlink(make =True, useActiveLights = True, useActiveObjects = True)
    
    cmds.select(clear = True)
    
    ## Rerun the remakes and reassociates
    _remakeLL()
    _reassociateLL()

def doesAssetAlreadyExistInScene(assetName):
    debug(app = None, method = 'doesAssetAlreadyExistInScene', message = 'assetName...\n%s' % assetName, verbose = False)
    assetExists = False
    if cmds.ls(assetName) != []:
        assetExists = True
    
    return assetExists

def _addVersionTag(assetName, versionNumber):

    assetName = cmds.ls(assetName, long = True)[0]

    if cmds.objExists('%s.SRFversion' % assetName):
        cmds.deleteAttr('%s.SRFversion' % assetName)
    try:
        cmds.addAttr(assetName, ln = 'SRFversion', at = 'long', min = 0, max  = 50000, dv = 0)
    except:
        pass
    cmds.setAttr('%s.SRFversion' % assetName, int(versionNumber))