"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db
"""
import os, getpass, sys, re
import shutil
from functools import partial

## TANK STUFF
import sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
from tank import TankError

## MAYA STUFF
import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm

## Now get the custom tools
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import maya_genericSettings as settings
import utils as utils
from debug import debug
import CONST as CONST
#reload(utils)
#reload(CONST)
#reload(settings)

## METALCORE / XML STUF
try:
    from mentalcore import mapi
    from mentalcore import mlib
except:
    debug(None, method = 'core_archive_lib', message = 'metalcore mapi and mlib failed to load!!', verbose = False)
    pass

import xml.etree.ElementTree as xml
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.dom import minidom
import tempfile
import gzip

def _convertOceanToPolys():
    oceanName = 'ocean_srf'
    dispName = '%s_displacement_geo' % oceanName

    if cmds.objExists(oceanName):
        cmds.select(oceanName, r = True)

        # Take note here as this require more smoothing *IT ALL HAS TO DO WITH THE NURBS ADVANCED TESELLETION U, V PATHCES BEFORE CONVERTING
        mel.eval("setupAnimatedDisplacement")
        cmds.rename('ocean_srfDisplacement1', dispName)

        ## Build a surface shader
        if not cmds.objExists('ocean_holdOut'):
            shader = cmds.shadingNode('surfaceShader', asShader = True, name = 'ocean_holdOut')
            shaderSG = cmds.sets(name = '%sSG' % shader, renderable = True, noSurfaceShader = True)
            cmds.connectAttr('%s.outColor' % shader, '%s.surfaceShader' % shaderSG)
            cmds.setAttr("ocean_holdOut.outMatteOpacity", 0,0,0, type = 'double3')

            ## Apply shader to ocean displacement geo
            cmds.sets(dispName, e = True , forceElement = shaderSG)

def _buildRateNetwork(eachBoatWorldCtrl):
    myMultiDiv = cmds.shadingNode('multiplyDivide', asTexture = True, name = '%s_rateMultiDiv' % eachBoatWorldCtrl)
    cmds.connectAttr('%s.speedNormalized' % eachBoatWorldCtrl, '%s.input1Y' % myMultiDiv)
    cmds.setAttr('%s.input2Y' % myMultiDiv, 800)
    return myMultiDiv

def _connectNURBSCurveToFluidContainer(nurbsCrv = '', fluidContainer = '', boatName = '', worldCtrl = '', animatable = ''):
    """
    Used to connect the intersection curves to the fluids.
    """
    debug(None, method = '_connectNURBSCurveToFluidContainer', message = 'Selecting: %s' % nurbsCrv, verbose = False)
    cmds.select(nurbsCrv, r = True)
    cmds.selectKey(clear  = True)
    debug(None, method = '_connectNURBSCurveToFluidContainer', message = 'Selecting: %s' % fluidContainer, verbose = False)

    #mel.eval("EmitFluidFromObject;")
    emitterName = '%s_%s_emitter' % (nurbsCrv, fluidContainer)
    debug(None, method = '_connectNURBSCurveToFluidContainer', message = 'emitterName: %s' % emitterName, verbose = False)

    if not cmds.objExists(emitterName):
        mel.eval("fluidEmitter -type curve -name \"%s\" -der 1 -her 1 -fer 1 -fdr 2 -r 100.0 -cye none -cyi 1 -mxd 1 -mnd 0" % emitterName)

    cmds.select(fluidContainer, add = True)

    ## NOTE we don't need to do this connect here as we use _linkWakeEmitters later on which does them all
    #cmds.connectDynamic (fluidContainer, em = emitterName, d = True)

    ## Set basic attrs for emitter across both foam and wake
    try: ## for re running script over existing build
        cmds.setAttr('%s.emitterType' % emitterName,  3)
        cmds.setAttr('%s.rate' % emitterName,  1500)
        cmds.setAttr('%s.fluidJitter' % emitterName,  0)
        cmds.setAttr('%s.motionStreak' % emitterName,  1)
        cmds.setAttr('%s.fluidDropoff' % emitterName,  1)

        ## Set special attrs for wake or foam
        if 'oceanWakeTextureShape' in emitterName:
            cmds.setAttr('%s.heatMethod' % emitterName, 0)
            cmds.setAttr('%s.fuelMethod' % emitterName, 0)
            cmds.setAttr('%s.fluidDensityEmission' % emitterName, 0.05)
        else:
            cmds.setAttr('%s.densityMethod' % emitterName, 0)
            cmds.setAttr('%s.fuelMethod' % emitterName, 0)
            cmds.setAttr('%s.fluidHeatEmission' % emitterName, 0.05)
            cmds.setAttr('%s.turbulence' % emitterName, 1)
    except RuntimeError:
        pass

    ## Now build the scene emitter group
    if not cmds.objExists('FLUID_EMITTERS_hrc'):
        cmds.group(n = 'FLUID_EMITTERS_hrc', em = True)
    try:
        cmds.parent(emitterName, 'FLUID_EMITTERS_hrc')
    except RuntimeError:
        pass

    ## DO THE EXPRESSIONS...
    if 'oceanWakeTextureShape' in emitterName:
        if 'IntersectCurveRight' in emitterName:
            direction = 'R'
        else:
            direction = 'L'
        ### FOR WAKE EMITTERS
        ######################################
        ## EMISSION RATE: Expression to tie emission rate to boat speed
        ## LEFT
        expStringList = [
                        'float $minSpeed = %s.minSpeed;\n' % animatable,
                        'float $maxSpeed = %s.maxSpeed;\n' % animatable,
                        'float $speed = %s.speed;\n' % worldCtrl,
                        'float $curve = smoothstep($minSpeed, $maxSpeed, $speed);\n',
                        'float $rateMultiplier%s = %s.sideWakeMultiplier%s;\n' %(direction, animatable, direction),
                        'float $idleRate%s = %s.sideWakeIdleMultiplier%s;\n' %(direction, animatable, direction),
                        '\n',
                        'if (%s.useSpeed == 1)\n' % animatable,
                        '{\n\t',
                            'if ($speed < $minSpeed)\n\t',
                            '{\n\t',
                                '\t%s.rate = $idleRate%s;\n\t' %(emitterName, direction),
                            '}\n\t',
                            'else\n\t',
                            '{\n\t',
                                '\t%s.rate = $rateMultiplier%s * $curve;\n\t' %(emitterName, direction),
                            '}\n',
                        '}\n',
                        'else\n',
                        '{\n\t',
                            '%s.rate = $rateMultiplier%s;\n' %(emitterName, direction),
                        '}\n',
                        ]
        debug(None, method = '_connectNURBSCurveToFluidContainer', message = 'FOAM expression: %s' % utils.processExpressionString(expStringList), verbose = False)
        ## Check if the expression already exists in the scene, if so delete it
        utils.checkExpressionExists( '%s_emissionRate' % emitterName)
        ## Build new expression
        cmds.expression(n = '%s_emissionRate' % emitterName, string = utils.processExpressionString(expStringList))

        ## Connect some attributes
        if not cmds.isConnected('%s.sideWakeDensity%s' %(animatable, direction), '%s.fluidDensityEmission' % emitterName):
            cmds.connectAttr('%s.sideWakeDensity%s' %(animatable, direction), '%s.fluidDensityEmission' % emitterName)
        if not cmds.isConnected('%s.sideWakeDropoff%s' %(animatable, direction), '%s.fluidDropoff' % emitterName):
            cmds.connectAttr('%s.sideWakeDropoff%s' %(animatable, direction), '%s.fluidDropoff' % emitterName)

    elif 'oceanWakeFoamTextureShape' in emitterName:
        if 'IntersectCurveRight' in emitterName:
            direction = 'R'
        else:
            direction = 'L'
        ### FOR WAKE EMITTERS
        ######################################
        ## EMISSION RATE: Expression to tie emission rate to boat speed
        wakeEmitterName = '%sTextureShape_emitter' % emitterName.split('FoamTextureShape_emitter')[0]
        expStringList = [
                        'float $minSpeed = %s.minSpeed;\n' % animatable,
                        'float $maxSpeed = %s.maxSpeed;\n' % animatable,
                        'float $speed = %s.speed;\n' % worldCtrl,
                        'float $curve = smoothstep($minSpeed, $maxSpeed, $speed);\n',
                        'float $rateMultiplier%s = %s.sideFoamMultiplier%s;\n' %(direction, animatable, direction),
                        'float $idleRate%s = %s.sideFoamIdleMultiplier%s;\n' %(direction, animatable, direction),
                        '\n',
                        'if (%s.useSpeed == 1)\n' % animatable,
                        '{\n\t',
                            'if ($speed < $minSpeed)\n\t',
                            '{\n\t',
                                '\t%s.rate = $idleRate%s;\n\t' %(emitterName, direction),
                            '}\n\t',
                            'else\n\t',
                            '{\n\t',
                                '\t%s.rate = $rateMultiplier%s * $curve;\n\t' %(emitterName, direction),
                            '}\n',
                        '}\n',
                        'else\n',
                        '{\n\t',
                            '%s.rate = $rateMultiplier%s;\n' %(emitterName, direction),
                        '}\n',
                        ]
        debug(None, method = '_connectNURBSCurveToFluidContainer', message = 'WAKE expression: %s' % utils.processExpressionString(expStringList), verbose = False)
        ## Check if the expression already exists in the scene, if so delete it
        utils.checkExpressionExists( '%s_emissionRate' % emitterName)
        ## Build new expression
        cmds.expression(n = '%s_emissionRate' % emitterName, string = utils.processExpressionString(expStringList))

        ## Connect some attributes
        if not cmds.isConnected('%s.sideFoamDensity%s' %(animatable, direction), '%s.fluidHeatEmission' % emitterName):
            cmds.connectAttr('%s.sideFoamDensity%s' %(animatable, direction), '%s.fluidHeatEmission' % emitterName)
        if not cmds.isConnected('%s.sideFoamDropoff%s' %(animatable, direction), '%s.fluidDropoff' % emitterName):
            cmds.connectAttr('%s.sideFoamDropoff%s' %(animatable, direction), '%s.fluidDropoff' % emitterName)
    else:
        pass

    return emitterName

def _setBaseFluidAttrs(fluid):
    #set required attributes
    attrs = ['ty', 'sx', 'sy', 'sz']

    ## Lock attrs
    for eachAttr in attrs:
        cmds.setAttr ("%s.%s" % (fluid[0], eachAttr), lock = True)
        cmds.setAttr ("%s.%s" % (fluid[0], eachAttr), keyable = False , channelBox = False)

    #scale fluid container
    attrs = ['scaleX', 'scaleY', 'scaleZ', 'rx']
    for each in attrs:
        if each != 'rx':
            var = 0.26
        else:
            var = -90
        try:
            cmds.setAttr ("%s.%s" % (fluid[0], each), var)
        except RuntimeError:
            cmds.setAttr ("%s.%s" % (fluid[0], each), lock = False)
            cmds.setAttr ("%s.%s" % (fluid[0], each), var)
    try:
        cmds.setAttr ("%sShape.gravity" % fluid[0], 1)
    except RuntimeError:
        pass

    debug(None, method = '_setBaseFluidAttrs', message = 'Successfully set attrs for %s:' % fluid , verbose = False)

def _create_WAKE_FluidTexture(oceanShader = '', size = '', pathToPreset = '', wakeFluidShapeName = CONST.WAKE_FLUID_SHAPENODE):
    """
    Create a 3d fluid texture, make it a 2d simulation and texture the waveHeightOffset of the ocean shader with it's outAlpha.
    @param oceanShader:
    @param size:
    @type oceanShader:
    @type size:
    """
    debug(None, method = '_create_WAKE_FluidTexture', message = 'Building fluid %s' % wakeFluidShapeName, verbose = False)
    fluidShape = cmds.shadingNode('fluidTexture3D', asTexture = True, name = wakeFluidShapeName)

    # Get parent of shape and set attrs
    fluid = cmds.listRelatives(fluidShape, parent= True)
    _setBaseFluidAttrs(fluid)

    ## Connect to time
    cmds.connectAttr ("time1.outTime", (fluidShape + ".currentTime"))
    debug(None, method = '_create_WAKE_FluidTexture', message = '%s connected to time1'  % fluidShape, verbose = False)

    ## Apply wake preset
    mel.eval("""applyPresetToNode " """+fluidShape+""" " "" "" "%s" 1;""" % pathToPreset)
    debug(None, method = '_create_WAKE_FluidTexture', message = 'Mel preset applied: %s' % pathToPreset, verbose = False)

    #expression to maintain resolution/container size relationship
    expStringList = ["int $width = %s.dimensionsW;\r\n" % fluidShape,
                    'int $height = %s.dimensionsH;\r\n' % fluidShape,
                    'if ($width>= $height)\r\n',
                    '{\r\n',
                    '%s.baseResolution = $width*4;\r\n'  % fluidShape,
                    '}\r\n',
                    'else\r\n',
                    '{\r\n%s.baseResolution = $height*4;\r\n}' % fluidShape]

    utils.checkExpressionExists('waterSurfaceFluidTexture')
    cmds.expression(n = 'waterSurfaceFluidTexture', string = utils.processExpressionString(expStringList))
    debug(None, method = '_create_WAKE_FluidTexture', message = ' Expression %s_foamTexture_ContainerSize built' % fluidShape, verbose = False)

    baseTextureName = wakeFluidShapeName.split('Shape')[0]
    cmds.rename(fluid[0], '%s' % baseTextureName)
    utils.createTypeTag(obj = '%s' % baseTextureName, typeName = '%s' % baseTextureName)
    debug(None, method = '_create_WAKE_FluidTexture', message = ' Rename and Tag successful..', verbose = False)

    ## Connect new wake fluid tex to ocean
    cmds.connectAttr("%s.outAlpha" % wakeFluidShapeName, "%s.waveHeightOffset" % oceanShader, force = True)

    debug(None, method = '_create_WAKE_FluidTexture', message = ' Returning %s:' % fluidShape, verbose = False)
    return fluidShape

def _create_FOAM_FluidTexture(oceanShader = '', size = '', pathToPreset = '', foamFluidShapeName = CONST.FOAM_FLUID_SHAPENODE):
    """
    create a 3d fluid texture for FOAM, make it a 2d simulation and texture the foamOffset of the ocean shader with it's outAlpha.
    """
    debug(None, method = 'fluids_lib._create_FOAM_FluidTexture', message = 'Building fluid %s' % foamFluidShapeName, verbose = False)
    fluidShape = cmds.shadingNode('fluidTexture3D', asTexture = True, name = foamFluidShapeName)

    # Get parent of shape and set attrs
    fluid = cmds.listRelatives(fluidShape, parent= True)
    _setBaseFluidAttrs(fluid)

    ## Connect to time
    cmds.connectAttr ("time1.outTime",(fluidShape + ".currentTime"))
    debug(None, method = 'fluids_lib._create_FOAM_FluidTexture', message = '%s connected to time1' % fluidShape, verbose = False)

    ## Apply foam preset
    mel.eval("""applyPresetToNode " """+fluidShape+""" " "" "" "%s" 1;""" % pathToPreset)
    debug(None, method = 'fluids_lib._create_FOAM_FluidTexture', message = 'Mel preset applied: %s' % pathToPreset, verbose = False)


    #add expression to texture
    expStringList = [
                    "float $foamSpeed = 1.0;\n",
                     "%s.textureTime = time * $foamSpeed;\n" % fluidShape
                    ]
    utils.checkExpressionExists('s_foamTexture_Speed')
    cmds.expression(n = '%s_foamTexture_Speed' % fluidShape,  string = utils.processExpressionString(expStringList))

    expStringList = [
                    'int $width = %s.dimensionsW;\r\n' % fluidShape,
                    'int $height = %s.dimensionsH;\r\n' % fluidShape,
                    'if ($width>= $height)\r\n',
                    '{\r\n',
                    '%s.baseResolution = $width*2;\r\n' % fluidShape,
                    '}\r\n',
                    'else\r\n',
                    '{\r\n',
                    '%s.baseResolution = $height*2;\r\n' % fluidShape,
                    '}'
                    ]
    #expression to maintain resolution/container size relationship
    cmds.expression(n = '%s_foamTexture_ContainerSize' % fluidShape, string = utils.processExpressionString(expStringList))
    debug(None, method = 'fluids_lib._create_FOAM_FluidTexture', message = ' Expression %s_foamTexture_ContainerSize built' % fluidShape, verbose = False)

    baseTextureName = fluidShape.split('Shape')[0]
    cmds.rename(fluid[0], '%s' % baseTextureName)
    utils.createTypeTag(obj = '%s' % baseTextureName, typeName = '%s' % baseTextureName)
    debug(None, method = 'fluids_lib._create_FOAM_FluidTexture', message = ' Rename and Tag successful..', verbose = False)

    ## Connect fluid to ocean shader
    cmds.connectAttr("%s.outAlpha" % fluidShape, "%s.foamOffset" % oceanShader, force = True)

    debug(None, method = 'fluids_lib._create_FOAM_FluidTexture', message = ' Returning %s:' % fluidShape, verbose = False)
    return fluidShape

def _addWakeEmitter():
    """
    Quick add additional linked emitter for the app UI only
    This builds a linked emitter to the scene for custom wakes such as around buildings etc
    """
    debug(None, method = '_addWakeEmitter', message = 'Adding wake emmiter now..', verbose = False)
    #get camera from current view
    currentPanel = cmds.getPanel(withFocus= True) or 'modelPanel4'
    debug(None, method = '_addWakeEmitter', message = 'currentPanel: %s' % currentPanel, verbose = False)

    panelType = cmds.getPanel(typeOf= currentPanel )
    debug(None, method = '_addWakeEmitter', message = 'panelType: %s' % panelType, verbose = False)

    if panelType !=  "modelPanel":
        print "Model panel not selected, please make view port live and try again"
    else:
        camera=cmds.modelPanel(currentPanel, q=True, camera = True)
        debug(None, method = '_addWakeEmitter', message = 'camera: %s' % camera, verbose = False)

        cameraShape =cmds.listRelatives(camera) or camera
        debug(None, method = '_addWakeEmitter', message = 'cameraShape: %s' % cameraShape, verbose = False)

        position = cmds.camera(cameraShape, q=True, worldCenterOfInterest= True)

        #build a new vector
        import maya.OpenMaya as om
        vec = om.MVector(position[0],0,position[2])

        # create a fluid emitter
        emitter = cmds.fluidEmitter( pos=vec, name = "additionalEmitter_WAKE#",  type='volume', densityEmissionRate=-3000, heatEmissionRate=50000, fuelEmissionRate=0, fluidDropoff=0.1, rate=150.0, cycleEmission='none', cycleInterval=1, maxDistance=1, minDistance=0, volumeShape = "sphere" )
        # connect to fluids
        cmds.connectDynamic(CONST.FOAM_FLUID_SHAPENODE, em = emitter)
        cmds.connectDynamic(CONST.WAKE_FLUID_SHAPENODE, em = emitter)
        # set some presets
        cmds.setAttr('%s.rate' % emitter[0], 150)
        cmds.setAttr('%s.fluidDensityEmission' % emitter[0], -3000)
        cmds.setAttr('%s.fluidHeatEmission' % emitter[0], 50000)
        cmds.setAttr('%s.fuelMethod' % emitter[0], 0)
        cmds.setAttr('%s.fluidJitter' % emitter[0], 0)
        cmds.setAttr('%s.motionStreak' % emitter[0], 1)

    debug(None, method = '_addWakeEmitter', message = 'FINISHED..', verbose = False)

def _unlinkAllEmitters():
    """
    Convenience function to unlink all fluid emitters in scene to ocean used in the app UI
    """
    fluids = [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE]
    for eachFluid in fluids:
        for eachEmitter in cmds.ls(type = 'fluidEmitter'):
            cmds.connectDynamic (eachFluid, em = eachEmitter, d = True)

def _linkWakeEmitters(fluids = [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE], wakeFluid = CONST.WAKE_FLUID_SHAPENODE, foamFluid = CONST.FOAM_FLUID_SHAPENODE):
    """
    Function to link all fluid emitters in scene to ocean used in the app UI
    """
    ## Build a list of the referenced emitters
    getAllReferenceEmitters = [eachEmitter for eachEmitter in cmds.ls (type = 'fluidEmitter') if cmds.referenceQuery(eachEmitter, isNodeReferenced = True)]
    debug(None, method = '_linkWakeEmitters', message = 'getAllReferenceEmitters: %s' % getAllReferenceEmitters, verbose = False)

    fluids = fluids
    debug(None, method = '_linkWakeEmitters', message = 'fluids: %s' % fluids, verbose = False)

    ## Now run through every emitter in the scene that isn't referenced and link it to the ocean fluid textures
    for eachFluid in fluids:
        for eachEmitter in cmds.ls(type = 'fluidEmitter'):
            try:
                if eachEmitter not in getAllReferenceEmitters:
                    if 'oceanWakeFoamTextureShape' in eachEmitter and eachFluid == foamFluid:
                        debug(None, method = '_linkWakeEmitters', message = 'FOAM emitter found: %s' % eachEmitter,  verbose = False)
                        cmds.connectDynamic (eachFluid, em = eachEmitter)
                        debug(None, method = '_linkWakeEmitters', message = 'Linked: %s to %s' % (eachFluid, eachEmitter), verbose = False)
                        print
                    elif 'oceanWakeTextureShape' in eachEmitter and eachFluid == wakeFluid:
                        debug(None, method = '_linkWakeEmitters', message = 'WAKE emitter found: %s' % eachEmitter,  verbose = False)
                        cmds.connectDynamic (eachFluid, em = eachEmitter)
                        debug(None, method = '_linkWakeEmitters', message = 'Linked: %s to %s' % (eachFluid, eachEmitter), verbose = False)
                        print
                    elif 'hullEmitter' in eachEmitter and eachFluid == wakeFluid:
                        debug(None, method = '_linkWakeEmitters', message = 'HULL emitter found: %s' % eachEmitter,  verbose = False)
                        cmds.connectDynamic (eachFluid, em = eachEmitter)
                        debug(None, method = '_linkWakeEmitters', message = 'Linked: %s to %s' % (eachFluid, eachEmitter), verbose = False)
                        print
                    else:
                        pass
            except RuntimeError:
                pass

def _deleteOceanTextureCaches(fluidShape = 'oceanWakeFoamTexture', fluidShape2 = 'oceanWakeTexture'):
    cmds.select([fluidShape, fluidShape2])
    try:
        mel.eval('deleteCacheFile 2 { "keep", "" };')
    except RuntimeError:
        pass

def _setFXOceanTexurePresets(fluidShape = 'oceanWakeFoamTexture', fluidShape2 = 'oceanWakeTexture'):
    """
    Function to apply the default fx ocean texture presets
    """
    pathToFoamPreset = '%s/newOceanWakeFoamTexture.mel' % CONST.OCEANTEXTURE_PRESETPATH
    pathToWakePreset = '%s/newOceanWakeTexture.mel' % CONST.OCEANTEXTURE_PRESETPATH
    fluidShape = fluidShape
    fluidShape2 = fluidShape2

    mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(fluidShape, pathToFoamPreset) )
    debug(None, method = '_setFXOceanTexurePresets', message = 'Preset applied to oceanWakeFoamTextureShape from %s' % pathToFoamPreset, verbose = False)

    mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(fluidShape2, pathToWakePreset) )
    debug(None, method = '_setFXOceanTexurePresets', message = 'Preset applied to oceanWakeTextureShape from %s' % pathToWakePreset, verbose = False)

def _setFluidEmitterPresets(wakeEmitterPreset, foamEmitterPreset, hullEmitterPreset):
    """
    Update function for new parsePreset
    This will attach the presets to the newly created fluid emitters that are constrained back to the rigged emitters in the scene
    """
    validEmitters = [eachEmitter for eachEmitter in cmds.ls(type = 'fluidEmitter') if ':' not in eachEmitter]
    for eachEmitter in validEmitters:
        if 'Bow' not in eachEmitter and 'Stern' not in eachEmitter: ## Note we can prob remove this check later on...
            debug(None, method = '_setFluidEmitterPresets', message = 'Setting presets for eachEmitter: %s' % eachEmitter, verbose = False)

            if 'oceanWakeFoamTextureShape' in eachEmitter:
                pathToPreset = '%s/%s' % (CONST.FLUID_EMITTER_PRESETPATH, foamEmitterPreset)
                debug(None, method = '_setFluidEmitterPresets', message = 'pathToPreset: %s' % pathToPreset, verbose = False)
                mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(eachEmitter, pathToPreset) )

            elif 'oceanWakeTextureShape' in eachEmitter:
                pathToPreset = '%s/%s' % (CONST.FLUID_EMITTER_PRESETPATH, wakeEmitterPreset)
                debug(None, method = '_setFluidEmitterPresets', message = 'pathToPreset: %s' % pathToPreset, verbose = False)
                mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(eachEmitter, pathToPreset) )
            else:
                ## This is a hull emitter
                pathToPreset = '%s/%s' % (CONST.FLUID_EMITTER_PRESETPATH, hullEmitterPreset)
                debug(None, method = '_setFluidEmitterPresets', message = 'pathToPreset: %s' % pathToPreset, verbose = False)
                mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(eachEmitter, pathToPreset) )

def _getValidAttrs(sourceNode):

    validAttrs = {}
    for attr in cmds.listAttr(sourceNode):
        badTypes = ('TdataCompound','message', 'float3', 'double3', 'doubleArray', 'vectorArray', None,
                    'mesh', 'sweptGeometry', 'Nobject', 'fluid', 'Nid', 'Int32Array', 'long3', 'matrix', 'defaultValue', 'newParticles')
        try:
            type =  cmds.getAttr('%s.%s' % (sourceNode, attr), type = True)
            if type in badTypes:
                #print 'BadAttr found. Skipping %s of type %s' % (attr, type)
                pass
            else:
                if attr not in validAttrs.keys():
                    validAttrs[attr] = cmds.getAttr('%s.%s' % (sourceNode, attr), type = True)
                    #DEBUGGING#
                    #print 'Found valid attr: \t%s of type: \t\t\t\t\t%s' % (attr, cmds.getAttr('%s.%s' % (sourceNode, attr), type = True))
        except TypeError:
            pass
        except ValueError:
            pass
    return validAttrs

def _buildFluidEmitter(newName):
    """
    Function to build a fluid emitter
    @param newName:                The name of the emitter
    @type newName:                 String
    """
    if not cmds.objExists(newName):
        newFluid = cmds.fluidEmitter(name = newName,  type='volume', densityEmissionRate=0.1, heatEmissionRate=0.1, fuelEmissionRate=1, fluidDropoff=0.1, rate=100.0, cycleEmission='none', cycleInterval=1, maxDistance=1, minDistance=0, volumeShape = "sphere" )
        return newFluid
    else:
        return [newName]

def _buildHullEmitter(boatName, constraint = '', implicitSphere = '', animatable = ''):
    worldCtrl = boatName
    cmds.select(clear = True)
    ns = boatName.split(':')[0]
    newName = '%s_hullEmitter' % ns
    grpName = '%s_CONS_GRP' % newName
    offsetGrp = '%s_OFFSET_GRP' % newName
    debug(None, method = '_buildHullEmitter', message = 'worldCtrl: %s' % worldCtrl, verbose = False)
    debug(None, method = '_buildHullEmitter', message = 'ns: %s' % ns, verbose = False)
    debug(None, method = '_buildHullEmitter', message = 'newName: %s' % newName, verbose = False)
    debug(None, method = '_buildHullEmitter', message = 'grpName: %s' % grpName, verbose = False)
    debug(None, method = '_buildHullEmitter', message = 'offsetGrp: %s' % offsetGrp, verbose = False)

    if not cmds.objExists(newName):
        cmds.select(clear = True)
        emitterName = _buildFluidEmitter(newName)

        if not cmds.objExists(offsetGrp):
            offsetGrp = cmds.group(emitterName, name = offsetGrp)

        if not cmds.objExists(grpName):
            grpName = cmds.group(offsetGrp, name = grpName)
    else:
        emitterName = [newName]

    ## Constraint stuffs
    if constraint:
        cmds.parentConstraint(constraint, grpName, maintainOffset = False, name = '%s_fluidPointConstraint' % newName)
    else:
        cmds.parentConstraint('%scog_ctrl' % boatName.split('world_ctrl')[0], grpName, maintainOffset = False, name = '%s_fluidPointConstraint' % newName)

    ## Presets from implicit sphere template
    if implicitSphere:
        cmds.delete( cmds.parentConstraint(implicitSphere, offsetGrp, maintainOffset = False) )
        cmds.delete( cmds.scaleConstraint(implicitSphere, offsetGrp, maintainOffset = False) )

    ## Now build the scene emitter group
    if not cmds.objExists('FLUID_EMITTERS_hrc'):
        cmds.group(name = 'FLUID_EMITTERS_hrc', empty = True)
    try:
        cmds.parent(grpName, 'FLUID_EMITTERS_hrc')
    except RuntimeError:
        pass

    ### FOR HULL EMITTERS
    ######################################
    ## EMISSION RATE: Expression to tie emission rate to boat speed
    expStringList = [
                        'float $minSpeed = %s.minSpeed;\n' % animatable,
                        'float $maxSpeed = %s.maxSpeed;\n' % animatable,
                        'float $speed = %s.speed;\n' % worldCtrl,
                        'float $curve = smoothstep($minSpeed, $maxSpeed, $speed);\n',
                        'float $rateMultiplier = %s.rearWakeMultiplier;\n' % animatable,
                        'float $idleRate = %s.rearWakeIdleMultiplier;\n' % animatable,
                        '\n',
                        'if (%s.useSpeed == 1)\n' % animatable,
                        '{\n\t',
                            'if ($speed < $minSpeed)\n\t',
                            '{\n\t',
                                '\t%s.rate = $idleRate;\n\t' % emitterName[0],
                            '}\n\t',
                            'else\n\t',
                            '{\n\t',
                                '\t%s.rate = $rateMultiplier * $curve;\n\t' % emitterName[0],
                            '}\n',
                        '}\n',
                        'else\n',
                        '{\n\t',
                            '%s.rate = $rateMultiplier;\n' % emitterName[0],
                        '}\n',
                    ]
    debug(None, method = '_buildHullEmitter', message = 'HULL expression: %s' % utils.processExpressionString(expStringList), verbose = False)
    ## Check if the expression already exists in the scene, if so delete it
    utils.checkExpressionExists( '%s_emissionRate' % emitterName[0])
    ## Build new expression
    cmds.expression(n = '%s_emissionRate' % emitterName[0], string = utils.processExpressionString(expStringList))

    ## Connect some attributes
    if not cmds.isConnected('%s.rearWakeDensity' % animatable, '%s.fluidDensityEmission' % emitterName[0]):
        cmds.connectAttr('%s.rearWakeDensity' % animatable, '%s.fluidDensityEmission' % emitterName[0])
    if not cmds.isConnected('%s.rearWakeDropoff' % animatable, '%s.fluidDropoff' % emitterName[0]):
        cmds.connectAttr('%s.rearWakeDropoff' % animatable, '%s.fluidDropoff' % emitterName[0])

def _rebuildAllEmmiters():
    """
    Helper to rebuild all the referenced rigged emitters in the FX shot
    """
    getAllReferenceEmitters = [eachEmitter for eachEmitter in cmds.ls (type = 'fluidEmitter') if cmds.referenceQuery(eachEmitter, isNodeReferenced = True)]
    for eachRefEm in getAllReferenceEmitters:
        cmds.select(clear = True)
        ns = eachRefEm.split(':')[0]
        newName = '%s_%s_fx' % (ns, eachRefEm.split(':')[-1])
        if not cmds.objExists(newName):
            _buildFluidEmitter(newName, eachRefEm)
        else:
            cmds.delete(newName)
            _buildFluidEmitter(newName, eachRefEm)

        getAttrs = _getValidAttrs(eachRefEm)
        ignoreAttrs = ['message', 'binMembership', 'isHierarchicalConnection', 'needParentUV', 'translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'visibility']
        for eachAttr in getAttrs:
            if eachAttr not in ignoreAttrs:
                try:
                    cmds.connectAttr('%s.%s' % (eachRefEm, eachAttr), '%s.%s' % (newName, eachAttr), f = True)
                except RuntimeError: # already connected
                    pass

        ## Hide the original emtter
        cmds.setAttr('%s.visibility' % eachRefEm , 0)
        ## Unlink the original emtter
        fluids = [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE]
        for eachFluid in fluids:
            cmds.connectDynamic (eachFluid, em = eachRefEm, d = True)

        ## Now build the scene emitter group
        if not cmds.objExists('FLUID_EMITTERS_hrc'):
            cmds.group(n = 'FLUID_EMITTERS_hrc', em = True)

        try:
            cmds.parent(newName, 'FLUID_EMITTERS_hrc')
        except RuntimeError:
            pass

def setupFXDefaultSettings():
    print 'THIS WILL BE THE TWEAKS TO THE BASE SCENE TO RESET / SET ALL THE ATTRS WE CAN COME UP WITH TO HELP SET A BASE WORKING FX SHOT'

def cleanupMasterBoatFluids(masterBoatName = ''):
    if masterBoatName:
        ## Delete any fluid emitters
        for each in cmds.ls(type = 'fluidEmitter'):
            if masterBoatName in each:
                cmds.delete(each)
        debug(None, method = 'fluids_lib.cleanupMasterBoatFluids', message = 'Emitters Cleaned.', verbose = False)

        ## Delete the hull emitter group, the fluidAnim group, the intersection NURBS Plane geo
        for each in cmds.ls(type = 'transform'):
            if each == '%s_hullEmitter_hrc' % masterBoatName:
                cmds.delete(each)
            elif each == '%s_fluidAnim' % masterBoatName:
                cmds.delete(each)
            elif each == '%s_NurbsIntersect_geo' % masterBoatName:
                cmds.delete(each)
            else:
                pass
        debug(None, method = 'fluids_lib.cleanupMasterBoatFluids', message = 'Grps Cleaned.', verbose = False)
        debug(None, method = 'fluids_lib.cleanupMasterBoatFluids', message = 'Hull Emitter Cleaned.', verbose = False)
        debug(None, method = 'fluids_lib.cleanupMasterBoatFluids', message = 'Intersection Plane Cleaned.', verbose = False)

        ## Now delete the curveVarGroup intersection curves for the NURBS hulls
        for each in cmds.ls(type = 'curveVarGroup'):
            if masterBoatName in each:
                cmds.delete(each)
        debug(None, method = 'fluids_lib.cleanupMasterBoatFluids', message = 'Intersection Crvs Cleaned.', verbose = False)

        ## Now delete the expressions
        for each in cmds.ls(type = 'expression'):
            if 'interactive' in each:
                cmds.delete(each)
        debug(None, method = 'fluids_lib.cleanupMasterBoatFluids', message = 'Expressions Cleaned.', verbose = False)
        debug(None, method = 'fluids_lib.cleanupMasterBoatFluids', message = 'FINISHED', verbose = False)
        print

def _intersect_animShader_expression(oceanShader = 'ocean_animShader'):
    for each in cmds.ls(type = 'expression'):
        if each.endswith('NurbsIntersect_geo_IntersectionPlane'):
            expr_str = cmds.expression(each, string = True, query = True)
            current_shader = re.findall( r'%s' % oceanShader, expr_str )

            if not current_shader:
                if oceanShader == 'ocean_dispShader':
                    expr_new_str = expr_str.replace('ocean_animShader', 'ocean_dispShader')
                elif oceanShader == 'ocean_animShader':
                    expr_new_str = expr_str.replace('ocean_dispShader', 'ocean_animShader')

                cmds.expression(each, string = expr_new_str, edit = True)
                mel.eval( 'print "%s expression set to use %s.\\n";' %(each, oceanShader) )
            else:
                mel.eval( 'print "%s expression already using the %s.\\n";' %(each, oceanShader) )

def _intersect_dispShader_expression(oceanShader = 'ocean_dispShader'):
    for each in cmds.ls(type = 'expression'):
        if each.endswith('NurbsIntersect_geo_IntersectionPlane'):
            expr_str = cmds.expression(each, string = True, query = True)
            current_shader = re.findall( r'%s' % oceanShader, expr_str )

            if not current_shader:
                if oceanShader == 'ocean_dispShader':
                    expr_new_str = expr_str.replace('ocean_animShader', 'ocean_dispShader')
                elif oceanShader == 'ocean_animShader':
                    expr_new_str = expr_str.replace('ocean_dispShader', 'ocean_animShader')

                cmds.expression(each, string = expr_new_str, edit = True)
                mel.eval( 'print "%s expression set to use %s.\\n";' %(each, oceanShader) )
            else:
                mel.eval( 'print "%s expression already using the %s.\\n";' %(each, oceanShader) )
