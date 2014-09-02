import os, getpass, sys, shutil, sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError

## Custom stuffs
if 'T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean' not in sys.path:
    sys.path.append('T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean')
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug
import utils as utils
import CONST as CONST
#reload(utils)
#reload(CONST)

def _nucleus(name = ''):
    nucleus = cmds.createNode('nucleus')
    if name:
        nucleus = cmds.rename(nucleus, name)
    cmds.connectAttr('time1.outTime', '%s.currentTime' % nucleus)

    return nucleus

def _nParticle(name = ''):
    """
    If using cmds.nParticle(), nucleus creation is sometimes there and not so it's pretty unstable.
    But if we're creating nParticle using cmds.createNode(), we can avoid it to create but we just
    need to make sure some essential stuffs are connected such as the default internalRamp...
    """

    nParticleShape = eval('cmds.createNode("nParticle")')
    nParticleTransform = cmds.listRelatives(nParticleShape, parent = True, fullPath = False)[0]
    if name:
        nParticleTransform = cmds.rename(nParticleTransform, name)
        nParticleShape = cmds.listRelatives(nParticleTransform, shapes = True, fullPath = False)[0]

    mel.eval('changeNParticleInput "%s" "radiusScaleInput" 1' % nParticleShape)
    mel.eval('changeNParticleInput "%s" "opacityScaleInput" 1' % nParticleShape)
    mel.eval('changeNParticleInput "%s" "colorInput" 1' % nParticleShape)

    # add lifespan and lifespanPP
    cmds.addAttr(nParticleShape, longName = 'lifespan', attributeType = 'double')
    cmds.addAttr(nParticleShape, longName = 'lifespanPP', dataType = 'doubleArray')

    return [nParticleTransform, nParticleShape]

def _buildparticleShape(particleShapeName = ''):
    """
    Used to create a base nParticle node
    @param particleShapeName: The particleShapeName of the nParticle to build
    @param presetName: The name of the preset eg: myNParticlePreset.mel
    @type particleShapeName: String
    @type presetName: String
    """
    debug(None, method = '_buildNParticleShape', message = 'Building Nparticle for %s' % particleShapeName, verbose = False)

    ## create new nParticle system
    newPart = _nParticle(name = particleShapeName)
    debug(None, method = '_buildNParticleShape', message = 'newPart: %s' % newPart, verbose = False)

    ## create 1 unique nucleus for all the splashes to share
    fx_nucleus = 'fx_nucleus'
    if not cmds.objExists(fx_nucleus):
        fx_nucleus = _nucleus(name = fx_nucleus)
    else:
        if not cmds.nodeType(fx_nucleus) == 'nucleus':
            fx_nucleus = _nucleus(name = fx_nucleus)
    cmds.select(newPart[1], replace = True)
    mel.eval('assignNSolver "%s";' % fx_nucleus)

    debug(None, method = '_buildNParticleShape', message = 'Unique nucleus: %s' % fx_nucleus, verbose = False)

    ## Take it as an nParticleShape for publishing
    utils.createTypeTag(obj = newPart[1], typeName = 'nParticle')

    if not cmds.objExists('nPARTICLE_PARTICLES_hrc'):
        cmds.group(n = 'nPARTICLE_PARTICLES_hrc', em = True)

    try:
        cmds.parent(newPart[0], 'nPARTICLE_PARTICLES_hrc')
    except:
        pass

    ## Make sure visibility is connected to isDynamic so hidden means won't simulate
    cmds.connectAttr('%s.visibility' % newPart[0], '%s.isDynamic' % newPart[1])

    debug(None, method = '_buildNParticleShape', message = 'Successfully built nparticle %s' % particleShapeName, verbose = False)
    debug(None, method = '_buildNParticleShape', message = 'Returning: %s' % newPart[1], verbose = False)

    return newPart[1]

def _connect_NParticleShape_to_NParticleEmitter(particleShapeNode = '', emitter = ''):
    """
    Helper to connect nParticleShape nodes and nParticleEmitters together
    @param particleShapeNode: The name of the nParticles Shape node
    @param emitter: The name of the nParticle emitter to attach the shape node to
    @type particleShapeNode: String
    @type emitter: String
    """
    debug(None, method = '_connect_NParticleShape_to_NParticleEmitter', message = 'Connecting %s to %s now...' % (particleShapeNode, emitter), verbose = False)
    cmds.connectDynamic(particleShapeNode, em = emitter)
    debug(None, method = '_connect_NParticleShape_to_NParticleEmitter', message = 'Successfully connected particle to emitter',  verbose = False)

def _buildSideSplashEmitter(name = '', boatName = '', splashParticleName = [], boatIntersectCurveShape = '', sideAnimatable = '', presetName = None):
    """
    New builder for sideSplash nParticle Emitter
    Checks if the NPARTICLE_EMITTLERS_hrc exists or not too

    @param name: The name of the new emitter
    @param splashParticleName: List of the names of nParticleShape nodes to connect to the emitter
    @param boatIntersectCurveShape: The name of the intersection curve to emit from.
    @type name:  String
    @type splashParticleName: List
    @type boatIntersectCurveShape: String
    """
    if not cmds.objExists('nPARTICLE_EMITTERS_hrc'):
        cmds.group(n = 'nPARTICLE_EMITTERS_hrc', em = True)

    debug(None, method = '_buildSideSplashEmitter', message = 'name: %s' % name, verbose = False)

    # Get base flat surface
    lineCurve       = cmds.curve( name = '%s_extrudeCurve' % name, degree = 1, point = [(-0.01, 0, 0), (0.01, 0, 0)] )
    flatSurface  = cmds.extrude(lineCurve, boatIntersectCurveShape, name = '%s_flatSurface' % name, constructionHistory = True, range = False, polygon = 0, useComponentPivot = 1, fixedPath = True, useProfileNormal = True, extrudeType = 2, reverseSurfaceIfPathReversed = True)[0]
    cmds.rebuildSurface(flatSurface, constructionHistory = True, replaceOriginal = True, rebuildType = 0, endKnots = 1, keepCorners = False, spansU = 1, degreeU = 1, spansV = 100, degreeV = 3)

    # Offset upwards curve from surface
    offsetUp = cmds.offsetCurve('%s.u[0.5]' % flatSurface, name = '%s_offsetUp' % name, distance = 0, constructionHistory = True, range = 0, subdivisionDensity = 1)[0]
    cmds.rebuildCurve(offsetUp, constructionHistory = False, replaceOriginal = True, end = 1, keepRange = 0, keepControlPoints = True, degree = 1)
    cmds.setAttr('%s.translateY' % offsetUp, 0.01)

    # Offset from upwards curve with distance and translate down to get the 45 degree angle
    offset_distance = -0.01
    offsetOut = cmds.offsetCurve(offsetUp, name = '%s_offsetOut' % name, distance = offset_distance, constructionHistory = True, range = 0, subdivisionDensity = 1)[0]
    cmds.setAttr('%s.translateY' % offsetOut, offset_distance)

    # Finally, loft a non-flipping surface solution (45 degree angle of the boat)
    noFlipSurface = cmds.loft(offsetUp, offsetOut, degree = 1, constructionHistory = True, range = 0, polygon = 0, sectionSpans = 1)[0]
    noFlipSurface = cmds.rename(noFlipSurface, '%s_noFlipSurface' % name)

    ## Build the emitter
    emitter = cmds.emitter(noFlipSurface, name = '%s_emitter' % name, type = 'surface')

    # Create closestPointOnSurface for acceleration expression where front more acceleration
    cPoS = cmds.createNode('closestPointOnSurface', name = '%s_cPoS' % name)
    cmds.connectAttr('%s.worldSpace' % noFlipSurface, '%s.inputSurface' % cPoS)

    ## Build the emitter group if it doesn't already exist
    emitterGroup = '%s_hrc' % name
    if not cmds.objExists(emitterGroup):
        cmds.group(lineCurve, flatSurface, offsetUp, offsetOut, noFlipSurface, emitter[0], n = emitterGroup)
    debug(None, method = '_buildSideSplashEmitter', message = 'emitterName: %s' % emitter[1], verbose = False)

    ## Check if a custom preset has been assigned via the func flags for the emitter, if not use the default preset...
    if presetName:
        pathToPreset = '%s/%s' %(CONST.EMITTERBASEPRESETPATH, presetName)
        debug(None, method = '_buildSideSplashEmitter', message = 'pathToPreset: %s' % pathToPreset, verbose = False)
        mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(emitter[1], pathToPreset) )

    ## Now parent it
    try:    cmds.parent(emitterGroup, 'nPARTICLE_EMITTERS_hrc')
    except: pass

    ## Connect the emitter to the particles
    debug(None, method = '_buildSideSplashEmitter', message = 'Connected %s: %s' % (splashParticleName, emitter[1]), verbose = False)
    for each in splashParticleName:
        _connect_NParticleShape_to_NParticleEmitter(particleShapeNode = each, emitter = emitter[1])

    ## Now do the expression for the side emitter
    if 'IntersectCurveRight' in emitter[1]:
        direction = 'R'
    else:
        direction = 'L'

    expStringList = [
                    'float $minSpeed = %s.minSpeed;\n' % sideAnimatable,
                    'float $maxSpeed = %s.maxSpeed;\n' % sideAnimatable,
                    'float $speed = %s:world_ctrl.speed;\n' % boatName,
                    'float $curve = smoothstep($minSpeed, $maxSpeed, $speed);\n',
                    'float $rateMuliplier = %s.rateMultiplier%s;\n' %(sideAnimatable, direction),
                    'float $splashMaxSpeed = %s.splashMaxSpeed%s;\n' %(sideAnimatable, direction),
                    '\n',
                    'if (%s.useSpeed == 1)\n' % sideAnimatable,
                    '{\n\t',
                        '%s.rate = $rateMuliplier * $curve;\n' % emitter[1],
                        '\n\t\t',
                        'float $emitterSpeed = $splashMaxSpeed * $curve;\n\t\t',
                        'if ($emitterSpeed == 0)\n\t\t',
                        '{\n\t\t\t',
                            '$emitterSpeed = 0.1;\n\t\t',
                        '}\n\t\t',
                        '%s.speed = $emitterSpeed;\n' % emitter[1],
                    '}\n',
                    'else\n',
                    '{\n\t',
                        '%s.rate = $rateMuliplier;\n\t' % emitter[1],
                        '%s.speed = $splashMaxSpeed;\n' % emitter[1],
                    '}\n',
                    ]
    ## Check if the expression already exists in the scene, if so delete it
    utils.checkExpressionExists('%s_sideSplashEmitter' % boatName)

    ## Build new expression
    cmds.expression(emitter[1], n = '%s_sideSplashEmitter' % emitter[1], string = utils.processExpressionString(expStringList))

    ## Connect some attributes
    if not cmds.isConnected('%s.normalSpeed%s' %(sideAnimatable, direction), '%s.normalSpeed' % emitter[1]):
        cmds.connectAttr('%s.normalSpeed%s' %(sideAnimatable, direction), '%s.normalSpeed' % emitter[1])
    if not cmds.isConnected('%s.randomSpeed%s' %(sideAnimatable, direction), '%s.speedRandom' % emitter[1]):
        cmds.connectAttr('%s.randomSpeed%s' %(sideAnimatable, direction), '%s.speedRandom' % emitter[1])

    return cPoS

def _buildRearEmitter(name = '', boatName = '', splashParticleName = '', rearAnimatable = '', presetName = None):
    """
    New builder for rear nParticle Emitter
    Checks if the NPARTICLE_EMITTLERS_hrc exists or not too

    @param name: The name of the new emitter
    @param splashParticleName: The name of the nParticleShape node for the splash
    @type name:  String
    @type splashParticleName: String
    """
    if not cmds.objExists('nPARTICLE_EMITTERS_hrc'):
        cmds.group(n = 'nPARTICLE_EMITTERS_hrc', em = True)

    debug(None, method = '_buildRearEmitter', message = 'name: %s' % name, verbose = False)
    cmds.select(clear = True) ## Because if you have anything selected maya may freak out it's the wrong damn thing.. fuck you maya seriously!

    ## Build the emitter
    emitter = cmds.emitter(name = name)
    emitter[0] = cmds.ls(emitter[0], long = True)[0]

    if presetName:
        pathToPreset = '%s/%s' %(CONST.EMITTERBASEPRESETPATH, presetName)
        debug(None, method = '_buildRearEmitter', message = 'emitter: %s' % emitter, verbose = False)
        debug(None, method = '_buildRearEmitter', message = 'pathToPreset: %s' % pathToPreset, verbose = False)

        ## Apply the preset to the emitter
        try:
            mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(emitter[0], pathToPreset) )
            debug(None, method = '_buildRearEmitter', message = 'Mel preset applied to %s: %s' % (emitter[0], pathToPreset), verbose = False)
        except RuntimeError:
            pass

    ## Now parent it
    try:
        emitter[0] = cmds.parent(emitter[0], 'nPARTICLE_EMITTERS_hrc')[0]
    except:
        pass

    ## Connect the emitter to the particles
    _connect_NParticleShape_to_NParticleEmitter(particleShapeNode = splashParticleName, emitter = emitter[0])

    ## Now do the expression for the rear emitter
    expStringList = [
                    'float $minSpeed = %s.minSpeed;\n' % rearAnimatable,
                    'float $maxSpeed = %s.maxSpeed;\n' % rearAnimatable,
                    'float $speed = %s:world_ctrl.speed;\n' % boatName,
                    'float $curve = smoothstep($minSpeed, $maxSpeed, $speed);\n',
                    'float $rateMuliplier = %s.rateMultiplier;\n' % rearAnimatable,
                    'float $splashMaxSpeed = %s.splashMaxSpeed;\n' % rearAnimatable,
                    '\n',
                    'if (%s.useSpeed == 1)\n' % rearAnimatable,
                    '{\n\t',
                        '%s.rate = $rateMuliplier * $curve;\n\t\t' % emitter[0],
                        '\n\t\t',
                        'float $emitterSpeed = $splashMaxSpeed * $curve;\n\t\t',
                        'if ($emitterSpeed == 0)\n\t\t',
                        '{\n\t\t\t',
                            '$emitterSpeed = 0.1;\n\t\t',
                        '}\n\t\t',
                        '%s.alongAxis = $emitterSpeed;\n' % emitter[0],
                    '}\n',
                    'else\n',
                    '{\n\t',
                        '%s.rate = $rateMuliplier;\n\t' % emitter[0],
                        '%s.alongAxis = $splashMaxSpeed;\n' % emitter[0],
                    '}\n',
                    ]
    ## Check if the expression already exists in the scene, if so delete it
    # utils.checkExpressionExists('%s_rearEmitter' % boatName)

    ## Build new expression
    cmds.expression(emitter[0], n = '%s_rearEmitter' % boatName, string = utils.processExpressionString(expStringList))

    ## Connect some attributes
    if not cmds.isConnected('%s.randomSpeed' % rearAnimatable, '%s.speedRandom' % emitter[0]):
        cmds.connectAttr('%s.randomSpeed' % rearAnimatable, '%s.speedRandom' % emitter[0])
    if not cmds.isConnected('%s.randomDirection' % rearAnimatable, '%s.randomDirection' % emitter[0]):
        cmds.connectAttr('%s.randomDirection' % rearAnimatable, '%s.randomDirection' % emitter[0])

    return emitter[0]

def _buildParticleShader(name):
    """
    Builds the base particle shader for the nParticleShape node
    @param name: The name of the nParticleShape node
    @type name: String
    """
    #SHADER#
    #======#
    #build and connect sprite shader
    shader = "%s_Shader" % name
    #check if shader already existas in scene
    if not cmds.objExists(shader):
        cmds.shadingNode("lambert", asShader = True, name = shader)
        fileNode = "%s_FileIn" % shader
        cmds.shadingNode ("file", asTexture = True, name = fileNode)
        cmds.setAttr('%s.fileTextureName' % fileNode, CONST.TEXTUREPATH, type = "string")
        cmds.setAttr('%s.defaultColor' % fileNode, 1, 1, 1, type = "double3")
        cmds.setAttr('%s.colorGain' % fileNode, 1, 1, 1, type = "double3")
        cmds.setAttr('%s.colorOffset' % fileNode, 0, 0, 0, type = "double3")

        texture = shader + "place2dTexture"
        cmds.shadingNode("place2dTexture", asUtility = True, name = texture)

        #Create Shading Group
        cmds.sets(renderable = True, noSurfaceShader = True, empty = True, name = shader + 'SG')
        #Connect SG to Shader
        cmds.connectAttr(shader + '.outColor', shader + 'SG.surfaceShader', force = True)
        #connect up place2d to file texture
        cmds.connectAttr(texture + ".coverage", fileNode + ".coverage", force = True)
        cmds.connectAttr(texture + ".translateFrame", fileNode + ".translateFrame", force = True)
        cmds.connectAttr(texture + ".rotateFrame", fileNode + ".rotateFrame", force = True)
        cmds.connectAttr(texture + ".mirrorU", fileNode + ".mirrorU", force = True)
        cmds.connectAttr(texture + ".mirrorV", fileNode + ".mirrorV", force = True)
        cmds.connectAttr(texture + ".stagger", fileNode + ".stagger", force = True)
        cmds.connectAttr(texture + ".wrapU", fileNode + ".wrapU", force = True)
        cmds.connectAttr(texture + ".wrapV", fileNode + ".wrapV", force = True)
        cmds.connectAttr(texture + ".repeatUV", fileNode + ".repeatUV", force = True)
        cmds.connectAttr(texture + ".offset", fileNode + ".offset", force = True)
        cmds.connectAttr(texture + ".rotateUV", fileNode + ".rotateUV", force = True)
        cmds.connectAttr(texture + ".noiseUV", fileNode + ".noiseUV", force = True)
        cmds.connectAttr(texture + ".vertexUvOne", fileNode + ".vertexUvOne", force = True)
        cmds.connectAttr(texture + ".vertexUvTwo", fileNode + ".vertexUvTwo", force = True)
        cmds.connectAttr(texture + ".vertexUvThree", fileNode + ".vertexUvThree", force = True)
        cmds.connectAttr(texture + ".vertexCameraOne", fileNode + ".vertexCameraOne", force = True)
        cmds.connectAttr(texture + ".outUV", fileNode + ".uv", force = True)
        cmds.connectAttr(texture + ".outUvFilterSize", fileNode + ".uvFilterSize", force = True)

        #connect file texture to shader
        cmds.connectAttr(fileNode + ".outColor" , shader+".color", force =True )
        cmds.connectAttr(fileNode + ".outTransparency" , shader+".transparency", force =True )
        #shadowAttenuation to 0
        cmds.setAttr(shader + ".shadowAttenuation",0)
        return shader
    else:
        return shader

def _setParticlePresets(sprayPresetPath = '', mistPresetPath = '', rearPresetPath = ''):
    """
    Used to set the freaking presets cause for some reason these will not set!!!
    @param sprayPresetPath: Preset name for the multiStreak side spray, including .mel extension
    @param mistPresetPath: Preset name for the multiPoint side mist, including .mel extension
    @param rearPresetPath: Preset name for the multiStreak rear engine spray, including .mel extension
    @type sprayPresetPath: String
    @type mistPresetPath: String
    @type rearPresetPath: String
    """
    debug(None, method = '_setParticlePresets', message = 'sprayPresetPath: %s' % sprayPresetPath, verbose = False)
    debug(None, method = '_setParticlePresets', message = 'mistPresetPath: %s' % mistPresetPath, verbose = False)
    debug(None, method = '_setParticlePresets', message = 'rearPresetPath: %s' % rearPresetPath, verbose = False)

    parse = False
    for eachParticle in cmds.ls(type = 'nParticle'):
        #########
        ## MULTIPOINT MIST
        if 'SideSprayMist' in eachParticle:
            pathToPreset = '%s/%s ' % (CONST.NPART_PRESETPATH, sprayPresetPath)
            debug(None, method = '_setParticlePresets', message = 'pathToPreset: %s' % pathToPreset, verbose = False)

            if not parse:
                mel.eval("""applyPresetToNode " """ +eachParticle+""" " "" "" "%s" 1;""" % pathToPreset)
                debug(None, method = '_setParticlePresets', message = 'Applied eval preset: %s to %s' % (pathToPreset, eachParticle), verbose = False)
            else:
                utils._parsePreset(applyTo = eachParticle, presetFile = pathToPreset)
                debug(None, method = '_setParticlePresets', message = 'Applied preset: %s to %s' % (pathToPreset, eachParticle), verbose = False)

        #########
        ## MULTISTREAK SPRAY
        elif 'SideSprayMultiStreak' in eachParticle:
            pathToPreset = '%s/%s ' % (CONST.NPART_PRESETPATH, mistPresetPath)
            debug(None, method = '_setParticlePresets', message = 'pathToPreset: %s' % pathToPreset, verbose = False)

            if not parse:
                mel.eval("""applyPresetToNode " """ +eachParticle+""" " "" "" "%s" 1;""" % pathToPreset)
                debug(None, method = '_setParticlePresets', message = 'Applied eval preset: %s to %s' % (pathToPreset, eachParticle), verbose = False)
            else:
                utils._parsePreset(applyTo = eachParticle, presetFile = pathToPreset)
                debug(None, method = '_setParticlePresets', message = 'Applied parse preset: %s to %s' % (pathToPreset, eachParticle), verbose = False)

        #########
        ## REAR MULTISTREAK
        elif 'RearSpray' in eachParticle:
            pathToPreset = '%s/%s' % (CONST.NPART_PRESETPATH, rearPresetPath)
            debug(None, method = '_setParticlePresets', message = 'pathToPreset: %s' % pathToPreset, verbose = False)

            if not parse:
                mel.eval("""applyPresetToNode " """ +eachParticle+""" " "" "" "%s" 1;""" % pathToPreset)
                debug(None, method = '_setParticlePresets', message = 'Applied eval preset: %s to %s' % (pathToPreset, eachParticle), verbose = False)
            else:
                utils._parsePreset(applyTo = eachParticle, presetFile = pathToPreset)
                debug(None, method = '_setParticlePresets', message = 'Applied parse preset: %s to %s' % (pathToPreset, eachParticle), verbose = False)

        else:
            pass

def _doBaseParticleShapeSetup(particleShapeName = '', type = 'splash', presetName = None):
    """
    Function to set the base particle setups for the nParticleShapes
    @param particleShapeName: The nParticleShapeName
    @param presetName: The name of the nParticle preset in the fx preset folder including the .mel extension
    @type particleShapeName: String
    @type presetName: String
    """
    lockedGrpAttrs = ['tx', 'ty', 'tz','rx', 'ry', 'rz', 'sx','sy','sz']
    lockedGrp = 'nPARTICLE_PARTICLES_hrc'
    if not cmds.ls("nPARTICLE_PARTICLES_hrc"):
        cmds.group(name = lockedGrp)
        for eachAttr in lockedGrpAttrs:
            cmds.setAttr("%s.%s" % (lockedGrp, eachAttr), lock =  True)
            cmds.setAttr ("%s.%s" % (lockedGrp, eachAttr), keyable=False,channelBox=False)
        try:
            cmds.parent(lockedGrp, 'Shot_FX_hrc')
        except RuntimeError:
            pass

    #parent particles under locked group
    try:
        cmds.parent(particleShapeName, lockedGrp)
    except RuntimeError:
        pass

    ## Now attach the desired preset from the FX nParticle preset folder
    if presetName:
        #debug(None, method = '_doBaseParticleShapeSetup', message = 'pathToPreset: %s' % pathToPreset, verbose = False)
        pathToPreset = '%s/%s' %(CONST.NPART_PRESETPATH, presetName)

        ## 1. Perform setup for nParticle to either Splashs or Mists
        if type == 'splash':
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

        elif type == 'mist':
            # Necessary attrs for adding nParticle presets (Mist)
            mel.eval('addAttr -is true -ln "betterIllumination" -at bool -dv false %s;' % particleShapeName)
            mel.eval('addAttr -is true -ln "surfaceShading" -at "float" -min 0 -max 1 -dv 0 %s;' % particleShapeName)
            mel.eval('addAttr -is true -ln "flatShaded" -at bool -dv false %s;' % particleShapeName)

            # Import particleCloud shader
            particleCloudShader = 'mist_particleCloud_shader'
            if not cmds.objExists(particleCloudShader):
                particleCloudMayaPath = CONST.PARTICLE_CLOUD_MA_PATH
                cmds.file(particleCloudMayaPath, i = True)
                debug(None, method = '_doBaseParticleShapeSetup', message = 'Imported particleCloud shader: %s' % particleCloudMayaPath, verbose = False)

            # Apply particleCloud shader preset
            particleCloudShaderPresetPath = CONST.PARTICLE_CLOUD_SHADER
            mel.eval('applyPresetToNode "%s" "" "" "%s" 1;' %(particleCloudShader, particleCloudShaderPresetPath) )
            debug(None, method = '_doBaseParticleShapeSetup', message = 'Applied preset: %s to particleCloud1' % particleCloudShaderPresetPath, verbose = False)

            # Create shading engine for the partiCloud shader because by default import, it doesn't have any.
            cmds.select(particleShapeName, replace = True)
            cmds.hyperShade(assign = particleCloudShader)

        ## 2. Apply presets
        mel.eval('applyPresetToNode "%s" "" "" "%s" 1;' %(particleShapeName, pathToPreset) )
        debug(None, method = '_doBaseParticleShapeSetup', message = 'Applied preset: %s to %s' % (pathToPreset, particleShapeName), verbose = False)

def _setupRear_ParticleExpressions(particleShapeName = '', type = 'splash', boatWorldCtrl = '', boatName = '', rearAnimatable = ''):
    """
    Setup the expressions for the rearEmitter nParticleShape node
    @param particleShapeName: The name of the nParticleShape node
    @param boatWorldCtrl: The name of the boatWorldCtrl curve
    @param boatName: The name of the boat should be stripped :
    @type particleShapeName: String
    @type boatWorldCtrl: String
    @type boatName: String
    """

    if type == 'splash':
        ############################
        ## Creation
        expStringList = [
                        '%s.lifespanPP = rand(%s.lifespanMin, %s.lifespanMax);\n' %(particleShapeName, rearAnimatable, rearAnimatable),
                        '%s.twistSpeedPP = rand(%s.twistSpeedMin, %s.twistSpeedMax);\n' %(particleShapeName, rearAnimatable, rearAnimatable),
                        '%s.spriteStartSizePP = rand(%s.spriteStartSizeMin, %s.spriteStartSizeMax);\n' %(particleShapeName, rearAnimatable, rearAnimatable),
                        '%s.spriteScaleYPP = %s.spriteScaleXPP = %s.spriteStartSizePP;\n' %(particleShapeName, particleShapeName, particleShapeName),
                        '%s.spriteTwistPP = rand(%s.twistAngleMin, %s.twistAngleMax);\n' %(particleShapeName, rearAnimatable, rearAnimatable),
                        ]

        ## Check if the expression already exists in the scene, if so delete it
        utils.checkExpressionExists('%s_sprite_settings' % particleShapeName)

        ## Build new expression
        cmds.dynExpression( particleShapeName, n = "%s_sprite_settings" % particleShapeName, creation = True, string = utils.processExpressionString(expStringList) )

        ############################
        ## Runtime Before Dynamics
        expStringList = [
                        '%s.spriteScaleYPP = %s.spriteScaleXPP = %s.spriteStartSizePP * %s.scaleOverLifeRamp;\n' %(particleShapeName, particleShapeName, particleShapeName, particleShapeName),
                        '%s.spriteScaleXPP = %s.spriteScaleYPP;\n' %(particleShapeName, particleShapeName),
                        '%s.spriteTwistPP += (%s.twistSpeedPP * %s.twistRateOverLife);\n' %(particleShapeName, particleShapeName, particleShapeName),
                        '\n',
                        ]

        ## Check if the expression already exists in the scene, if so delete it
        utils.checkExpressionExists('%s_sprite_settings' % particleShapeName)

        ## Build new expression
        cmds.dynExpression( particleShapeName, n = "%s_sprite_settings" % particleShapeName, rbd = True, string = utils.processExpressionString(expStringList) )

        ## Connect some attrs to animatable group
        attrs = ['inheritFactor', 'conserve', 'drag', 'damp']
        for att in attrs:
            if not cmds.isConnected( '%s.%s' %(rearAnimatable, att), '%s.%s' %(particleShapeName, att) ):
                cmds.connectAttr('%s.%s' %(rearAnimatable, att), '%s.%s' %(particleShapeName, att), force = True)

def _setupSide_ParticleExpressions(particleShapeName = '', type = 'splash', boatWorldCtrl = '', boatName = '', cPoS = '', sideAnimatable = ''):
    """
    Setup the expressions for the sideEmitter's nParticleShape node
    @param particleShapeName: The name of the nParticleShape node
    @param boatWorldCtrl: The name of the boatWorldCtrl curve
    @param boatName: The name of the boat should be stripped :
    @type particleShapeName: String
    @type boatWorldCtrl: String
    @type boatName: String
    """

    if type == 'splash':
        ############################
        ## Creation
        expStringList = [
                        '%s.lifespanPP = rand(%s.lifespanMin, %s.lifespanMax);\n' %(particleShapeName, sideAnimatable, sideAnimatable),
                        '%s.twistSpeedPP = rand(%s.twistSpeedMin, %s.twistSpeedMax);\n' %(particleShapeName, sideAnimatable, sideAnimatable),
                        '%s.spriteStartSizePP = rand(%s.spriteStartSizeMin, %s.spriteStartSizeMax);\n' %(particleShapeName, sideAnimatable, sideAnimatable),
                        '%s.spriteScaleYPP = %s.spriteScaleXPP = %s.spriteStartSizePP;\n' %(particleShapeName, particleShapeName, particleShapeName),
                        '%s.spriteTwistPP = rand(%s.twistAngleMin, %s.twistAngleMax);\n' %(particleShapeName, sideAnimatable, sideAnimatable),
                        ]

        ## Check if the expression already exists in the scene, if so delete it
        utils.checkExpressionExists('%s_sprite_settings' % particleShapeName)

        ## Build new expression
        cmds.dynExpression( particleShapeName, n = "%s_sprite_settings" % particleShapeName, creation = True, string = utils.processExpressionString(expStringList) )

        ############################
        ## Runtime Before Dynamics
        expStringList = [
                        '%s.spriteScaleYPP = %s.spriteScaleXPP = %s.spriteStartSizePP * %s.scaleOverLifeRamp;\n' %(particleShapeName, particleShapeName, particleShapeName, particleShapeName),
                        '%s.spriteScaleXPP = %s.spriteScaleYPP;\n' %(particleShapeName, particleShapeName),
                        '%s.spriteTwistPP += (%s.twistSpeedPP * %s.twistRateOverLife);\n' %(particleShapeName, particleShapeName, particleShapeName),
                        '\n',
                        ]

        ## Check if the expression already exists in the scene, if so delete it
        utils.checkExpressionExists('%s_sprite_settings' % particleShapeName)

        ## Build new expression
        cmds.dynExpression( particleShapeName, n = "%s_sprite_settings" % particleShapeName, rbd = True, string = utils.processExpressionString(expStringList) )

        ## Connect some attrs to animatable group
        attrs = ['inheritFactor', 'conserve', 'drag', 'damp']
        for att in attrs:
            if not cmds.isConnected( '%s.%sSprite' %(sideAnimatable, att), '%s.%s' %(particleShapeName, att) ):
                cmds.connectAttr('%s.%sSprite' %(sideAnimatable, att), '%s.%s' %(particleShapeName, att), force = True)

    elif type == 'mist':
        ## Creation
        expStringList = [
                        '%s.lifespanPP = rand(%s.lifespanMin, %s.lifespanMax);\n' %(particleShapeName, sideAnimatable, sideAnimatable),
                        ]

        ## Check if the expression already exists in the scene, if so delete it
        utils.checkExpressionExists('%s_sprite_settings' % particleShapeName)

        ## Build new expression
        cmds.dynExpression( particleShapeName, n = "%s_sprite_settings" % particleShapeName, creation = True, string = utils.processExpressionString(expStringList) )

        ## Connect some attrs to animatable group
        attrs = ['inheritFactor', 'conserve', 'drag', 'damp']
        for att in attrs:
            if not cmds.isConnected( '%s.%sMist' %(sideAnimatable, att), '%s.%s' %(particleShapeName, att) ):
                cmds.connectAttr('%s.%sMist' %(sideAnimatable, att), '%s.%s' %(particleShapeName, att), force = True)