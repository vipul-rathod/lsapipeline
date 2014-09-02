import os, getpass, sys, shutil, sgtk
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
import oceanNurbsPreviewPlane as oceanNPP
import nParticleSetup as npart
import fluids_lib as fluidsLib
from debug import debug
import utils as utils
import CONST as CONST
import fx_lib as fxLib
#reload(CONST)
#reload(utils)
#reload(oceanNPP)
#reload(npart)
#reload(fxLib)

def getBoatsList():
    """
    Returns a list of the boats in the scene
    """
    boatsList= []
    getBoats = cmds.ls(type = 'transform')
    for boat in getBoats:
        if cmds.objExists('%s.boatRoot' % boat):
            boatsList.append(boat)
    return boatsList

def _buildSpeedExpression(boatWorldCtrl = ''):
    """
    Builds the base expression for the boats world_ctrl speed attr
    @param boatWorldCtrl: The name of the boat world_ctrl to build the expression for
    @type boatWorldCtrl: String
    """
    expStringList = [
                    'float $time;\n',
                    'float $translation[] = `xform -q -ws -translation "%s"`;\n' % boatWorldCtrl,
                    'float $trx;\n',
                    'float $try;\n',
                    'float $trz;\n',
                    'float $dx = $translation[0] - $trx;\n',
                    'float $dy = $translation[1] - $try;\n',
                    'float $dz = $translation[2] - $trz;\n',
                    'float $d = sqrt( ($dx * $dx) + ($dy * $dy) + ($dz * $dz) );\n',
                    '%s.speed = abs( $d / ( time - ($time + 0.001) ) );\n' % boatWorldCtrl,
                    '$trx = $translation[0];\n',
                    '$try = $translation[1];\n',
                    '$trz = $translation[2];\n',
                    '$time = time;\n'
                    ]

    ## Check if the expression already exists in the scene, if so delete it
    utils.checkExpressionExists( '%s_speed' % boatWorldCtrl)
    ## Build new expression
    try:
        cmds.expression(n = '%s_speed' % boatWorldCtrl.replace(':', '_'), string = utils.processExpressionString(expStringList))
    except:
        cmds.warning('YOU ARE USING OLD RIGS!!! PLEASE UPDATE YOUR RIGS!!!')

def global_dynamicAnimatable(name = ''):
    ## 1. Create empty group
    fxAnimGroup = cmds.group(name = name, empty = 1)
    fxAnimGroup = cmds.parent(fxAnimGroup, 'Shot_FX_hrc')[0]
    lockAttrs = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ', 'visibility']
    for each in lockAttrs:
        cmds.setAttr('%s.%s' %(fxAnimGroup, each), lock = True, keyable = False, channelBox = False)

    ## 2. Adding custom attributes into group
    # FLUIDS FOAM
    attr = {'longName':'fluidsFoam', 'niceName':' ', 'attributeType':'enum', 'enumName':'Foam Fluid:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'foamStartFrame', 'niceName':'Start Frame', 'attributeType':'long', 'defaultValue':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'foamGravity', 'niceName':'Gravity', 'attributeType':'double', 'defaultValue':9.8}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'foamViscosity', 'niceName':'Viscosity', 'attributeType':'double', 'defaultValue':0.5, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'foamFriction', 'niceName':'Friction', 'attributeType':'double', 'defaultValue':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'foamDamp', 'niceName':'Damp', 'attributeType':'double', 'defaultValue':0.02}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    # FLUIDS WAKE
    attr = {'longName':'fluidsWake', 'niceName':' ', 'attributeType':'enum', 'enumName':'Wake Fluid:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'wakeStartFrame', 'niceName':'Start Frame', 'attributeType':'long', 'defaultValue':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'wakeGravity', 'niceName':'Gravity', 'attributeType':'double', 'defaultValue':9.8}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'wakeViscosity', 'niceName':'Viscosity', 'attributeType':'double', 'defaultValue':0.5, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'wakeFriction', 'niceName':'Friction', 'attributeType':'double', 'defaultValue':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'wakeDamp', 'niceName':'Damp', 'attributeType':'double', 'defaultValue':0.02}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    # NPARTICLES
    attr = {'longName':'nParticles', 'niceName':' ', 'attributeType':'enum', 'enumName':'nParticles:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'startFrame', 'attributeType':'long', 'defaultValue':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'gravity', 'attributeType':'double', 'defaultValue':9.8}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'substeps', 'attributeType':'long', 'defaultValue':3}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'maxCollisionIterations', 'attributeType':'long', 'defaultValue':4}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'timeScale', 'attributeType':'double', 'defaultValue':1, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'spaceScale', 'attributeType':'double', 'defaultValue':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)

    return fxAnimGroup

def rear_splashAnimatable(name = ''):
    ## 1. Create empty group
    if name:
        fxAnimGroup = cmds.group(name = name, empty = True)
        fxAnimGroup = cmds.parent(fxAnimGroup, 'Shot_FX_hrc')[0]
        lockAttrs = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ', 'visibility']
        for each in lockAttrs:
            cmds.setAttr('%s.%s' %(fxAnimGroup, each), lock = True, keyable = False, channelBox = False)

        ## 2. Adding custom attributes into group
        # BOAT SPEED
        attr = {'longName':'boatSpeed', 'niceName':' ', 'attributeType':'enum', 'enumName':'Boat Speed:', 'keyable':False}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'minSpeed', 'attributeType':'double', 'defaultValue':5, 'min':0}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'maxSpeed', 'attributeType':'double', 'defaultValue':20}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'useSpeed', 'niceName':'Rate/Speed based on Boat Speed', 'attributeType':'bool', 'defaultValue':1}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        # EMITTERS
        attr = {'longName':'sideEmitters', 'niceName':' ', 'attributeType':'enum', 'enumName':'Emitters:', 'keyable':False}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'rateMultiplier', 'niceName':'Rate * ', 'attributeType':'double', 'defaultValue':7500, 'min':0}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'splashMaxSpeed', 'niceName':'Speed * ', 'attributeType':'double', 'defaultValue':3.5, 'min':1}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'randomSpeed', 'attributeType':'double', 'defaultValue':1, 'min':0}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'randomDirection', 'attributeType':'double', 'defaultValue':1, 'min':0}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        # PER PARTICLE CREATION
        attr = {'longName':'ppCreation', 'niceName':' ', 'attributeType':'enum', 'enumName':'PP Creation:', 'keyable':False}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'lifespanMin', 'attributeType':'double', 'defaultValue':1}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'lifespanMax', 'attributeType':'double', 'defaultValue':1.5}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'twistAngleMin', 'attributeType':'double', 'defaultValue':0, 'min':0, 'max':360}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'twistAngleMax', 'attributeType':'double', 'defaultValue':360, 'min':0, 'max':360}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'twistSpeedMin', 'attributeType':'double', 'defaultValue':-4}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'twistSpeedMax', 'attributeType':'double', 'defaultValue':30}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'spriteStartSizeMin', 'attributeType':'double', 'defaultValue':0.15, 'min':0}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'spriteStartSizeMax', 'attributeType':'double', 'defaultValue':0.46, 'min':0}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        # NPARTICLE
        attr = {'longName':'nParticles', 'niceName':' ', 'attributeType':'enum', 'enumName':'nParticles:', 'keyable':False}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'inheritFactor', 'attributeType':'double', 'defaultValue':0.1, 'min':0, 'max':1}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'conserve', 'attributeType':'double', 'defaultValue':1, 'min':0, 'max':1}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'drag', 'attributeType':'double', 'defaultValue':0.01, 'min':0, 'max':1}
        utils.add_custom_attrs(fxAnimGroup, **attr)
        attr = {'longName':'damp', 'attributeType':'double', 'defaultValue':0, 'min':0, 'max':1}
        utils.add_custom_attrs(fxAnimGroup, **attr)

        return fxAnimGroup

def side_splashAnimatable(name = ''):
    ## 1. Create empty groupz
    fxAnimGroup = cmds.group(name = name, empty = True)
    fxAnimGroup = cmds.parent(fxAnimGroup, 'Shot_FX_hrc')[0]
    lockAttrs = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ', 'visibility']
    for each in lockAttrs:
        cmds.setAttr('%s.%s' %(fxAnimGroup, each), lock = True, keyable = False, channelBox = False)

    ## 2. Adding custom attributes into group
    # BOAT SPEED
    attr = {'longName':'boatSpeed', 'niceName':' ', 'attributeType':'enum', 'enumName':'Boat Speed:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'minSpeed', 'attributeType':'double', 'defaultValue':0.5, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'maxSpeed', 'attributeType':'double', 'defaultValue':20}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'useSpeed', 'niceName':'Rate/Speed based on Boat Speed', 'attributeType':'bool', 'defaultValue':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    # EMITTERS
    attr = {'longName':'sideEmitters', 'niceName':' ', 'attributeType':'enum', 'enumName':'Emitters:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'rateMultiplierL', 'niceName':'L Rate * ', 'attributeType':'double', 'defaultValue':5000, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'rateMultiplierR', 'niceName':'R Rate * ', 'attributeType':'double', 'defaultValue':5000, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'splashMaxSpeedL', 'niceName':'L Speed * ', 'attributeType':'double', 'defaultValue':0.95, 'min':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'splashMaxSpeedR', 'niceName':'R Speed * ', 'attributeType':'double', 'defaultValue':0.95, 'min':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'accelerationMultiplier', 'niceName':'Acceleration', 'attributeType':'double', 'defaultValue':2.5, 'min':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'normalSpeedL', 'niceName':'L Directional Speed', 'attributeType':'double', 'defaultValue':6, 'min':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'normalSpeedR', 'niceName':'R Directional Speed', 'attributeType':'double', 'defaultValue':6, 'min':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'randomSpeedL', 'niceName':'L Random Speed', 'attributeType':'double', 'defaultValue':1, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'randomSpeedR', 'niceName':'R Random Speed', 'attributeType':'double', 'defaultValue':1, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    # PER PARTICLE CREATION
    attr = {'longName':'ppCreation', 'niceName':' ', 'attributeType':'enum', 'enumName':'PP Creation:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'lifespanMin', 'attributeType':'double', 'defaultValue':0.6}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'lifespanMax', 'attributeType':'double', 'defaultValue':1.2}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'twistAngleMin', 'attributeType':'double', 'defaultValue':0, 'min':0, 'max':360}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'twistAngleMax', 'attributeType':'double', 'defaultValue':360, 'min':0, 'max':360}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'twistSpeedMin', 'attributeType':'double', 'defaultValue':-4}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'twistSpeedMax', 'attributeType':'double', 'defaultValue':4}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'spriteStartSizeMin', 'attributeType':'double', 'defaultValue':0.3, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'spriteStartSizeMax', 'attributeType':'double', 'defaultValue':0.23, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    # NPARTICLE SPRITE
    attr = {'longName':'nParticleSprite', 'niceName':' ', 'attributeType':'enum', 'enumName':'Sprite nParticle:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'inheritFactorSprite', 'attributeType':'double', 'defaultValue':0.6, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'conserveSprite', 'attributeType':'double', 'defaultValue':1, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'dragSprite', 'attributeType':'double', 'defaultValue':0.01, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'dampSprite', 'attributeType':'double', 'defaultValue':0, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    # NPARTICLE MIST
    attr = {'longName':'nParticleMist', 'niceName':' ', 'attributeType':'enum', 'enumName':'Mist nParticle:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'inheritFactorMist', 'attributeType':'double', 'defaultValue':0.6, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'conserveMist', 'attributeType':'double', 'defaultValue':0.9, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'dragMist', 'attributeType':'double', 'defaultValue':0.2, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'dampMist', 'attributeType':'double', 'defaultValue':0, 'min':0, 'max':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)

    return fxAnimGroup

def all_fluidAnimatable(name = ''):
    ## 1. Create empty group
    fxAnimGroup = cmds.group(name = name, empty = True)
    fxAnimGroup = cmds.parent(fxAnimGroup, 'Shot_FX_hrc')[0]
    lockAttrs = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ', 'visibility']
    for each in lockAttrs:
        cmds.setAttr('%s.%s' %(fxAnimGroup, each), lock = True, keyable = False, channelBox = False)

    ## 2. Adding custom attributes into group
    # BOAT SPEED
    attr = {'longName':'boatSpeed', 'niceName':' ', 'attributeType':'enum', 'enumName':'Boat Speed:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'minSpeed', 'attributeType':'double', 'defaultValue':0.5, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'maxSpeed', 'attributeType':'double', 'defaultValue':20}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'useSpeed', 'niceName':'Rate based on Boat Speed', 'attributeType':'bool', 'defaultValue':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    # FOAM
    attr = {'longName':'sideFoam', 'niceName':' ', 'attributeType':'enum', 'enumName':'Side Foam:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideFoamMultiplierL', 'niceName':'L Rate * ', 'attributeType':'double', 'defaultValue':7500, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideFoamMultiplierR', 'niceName':'R Rate * ', 'attributeType':'double', 'defaultValue':7500, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideFoamIdleMultiplierL', 'niceName':'L Idle Rate * ', 'attributeType':'double', 'defaultValue':0, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideFoamIdleMultiplierR', 'niceName':'R Idle Rate * ', 'attributeType':'double', 'defaultValue':0, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideFoamDensityL', 'niceName':'L Density', 'attributeType':'double', 'defaultValue':0.25}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideFoamDensityR', 'niceName':'R Density', 'attributeType':'double', 'defaultValue':0.25}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideFoamDropoffL', 'niceName':'L Dropoff', 'attributeType':'double', 'defaultValue':0.05, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideFoamDropoffR', 'niceName':'R Dropoff', 'attributeType':'double', 'defaultValue':0.05, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    # WAKE
    attr = {'longName':'sideWake', 'niceName':' ', 'attributeType':'enum', 'enumName':'Side Wake:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideWakeMultiplierL', 'niceName':'L Rate * ', 'attributeType':'double', 'defaultValue':2500, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideWakeMultiplierR', 'niceName':'R Rate * ', 'attributeType':'double', 'defaultValue':2500, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideWakeIdleMultiplierL', 'niceName':'L Idle Rate * ', 'attributeType':'double', 'defaultValue':1000, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideWakeIdleMultiplierR', 'niceName':'R Idle Rate * ', 'attributeType':'double', 'defaultValue':1000, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideWakeDensityL', 'niceName':'L Density', 'attributeType':'double', 'defaultValue':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideWakeDensityR', 'niceName':'R Density', 'attributeType':'double', 'defaultValue':1}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideWakeDropoffL', 'niceName':'L Dropoff', 'attributeType':'double', 'defaultValue':2.2, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'sideWakeDropoffR', 'niceName':'R Dropoff', 'attributeType':'double', 'defaultValue':2.2, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    # REAR EMITTERS
    attr = {'longName':'rearWake', 'niceName':' ', 'attributeType':'enum', 'enumName':'Rear Wake:', 'keyable':False}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'rearWakeMultiplier', 'niceName':'Rate * ', 'attributeType':'double', 'defaultValue':7500, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'rearWakeIdleMultiplier', 'niceName':'Idle Rate * ', 'attributeType':'double', 'defaultValue':0, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'rearWakeDensity', 'niceName':'Density', 'attributeType':'double', 'defaultValue':-100}
    utils.add_custom_attrs(fxAnimGroup, **attr)
    attr = {'longName':'rearWakeDropoff', 'niceName':'Dropoff', 'attributeType':'double', 'defaultValue':2, 'min':0}
    utils.add_custom_attrs(fxAnimGroup, **attr)

    return fxAnimGroup

def _createSet(name = '', type = '', endswith = '', shapeOnly = True):

    if cmds.objExists(name) and cmds.nodeType(name) == 'objectSet':
        try:
            cmds.delete(name)
        except:
            pass

    if endswith:
        if shapeOnly:
            animatable = [x for x in cmds.ls(type = type) if x.endswith(endswith)]
        else:
            animatable = [cmds.listRelatives(x, parent = True, fullPath = True)[0] for x in cmds.ls(type = type) if x.endswith(endswith)]
    else:
        if shapeOnly:
            animatable = [x for x in cmds.ls(type = type) if cmds.nodeType(x) == type]
        else:
            animatable = [cmds.listRelatives(x, parent = True, fullPath = True)[0] for x in cmds.ls(type = type) if cmds.nodeType(x) == type]

    if animatable:
        cmds.sets(animatable, name = name)

def _setupBaseBoatFXSystems(xRes = 20, zRes = 20, inprogressBar = '', fluidContainers = [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE], selected = [], animInteractive = False, fxInteractive = False, interactiveBoatName = ''):
    """
    Function that sets up the new approach for all the boat wakes.
    This builds;
    - the Nurbs intersection plane
    - the intersection curves
    - the fluid emitters from those curves
    - the rear jet engine emitters from the motor powered boats
    - the hull fluid emitter that pushes the ocean down as the hull carves through the ocean
    @param xRes: The x res of the nurbsPlane being built for intersections
    @param zRes: The z res of the nurbsPlane being built for intersections
    @type xRes: Int
    @type zRes: Int
    """
    debug(None, method = '_setupBaseBoatFXSystems', message = 'setupNParticleBoatWakes now...', verbose = False)

    if animInteractive:
        if selected: ## For interactive boat ocean setup, this will be the master boats selected world_ctrl curve
            if len(selected) > 1:
                cmds.warning('You must have only one boat world ctrl selected!')
            elif 'world_ctrl' not in selected[0]:
                cmds.warning('You must have a valid master boat world_ctrl curve selected!')
            else:
                boatsList = [selected[0]]
    else:
        boatsList = getBoatsList() ## Returns all the world_ctrls for the boats

    inprogressBar.updateProgress(percent = 45, doingWhat = 'Processing all boat setups now...')
    if not boatsList:
        cmds.warning ("NO BOATS HAVE BEEN TAGGED OR EXIST IN THE SCENE!!!\n Please use the boat rigging tools to tag some boats and then try again.")
        debug(None, method = '_setupBaseBoatFXSystems', message = 'NO BOATS HAVE BEEN TAGGED OR EXIST IN THE SCENE', verbose = False)
    else:
        if fxInteractive:
            boatToSkip = interactiveBoatName
            debug(None, method = '_setupBaseBoatFXSystems', message = 'boatToSkip: %s' % boatToSkip, verbose = False)
        else:
            boatToSkip = 'Iamadeadstringtocheckagainst'
            debug(None, method = '_setupBaseBoatFXSystems', message = 'boatToSkip: %s' % boatToSkip, verbose = False)

        ## Create fluids and nucleus global animatable
        if not cmds.objExists('global_dynamicAnim'):
            global_dynamicAnimatable(name = 'global_dynamicAnim')

        ## Iterate through all boats
        for eachBoatWorldCtrl in boatsList:
            boatName = eachBoatWorldCtrl.split(':')[0]
            ########################################
            ## INTERSECTION PLANE AND CURVE BUILD ##
            ########################################
            ## 1. Customising intersection plane's size and resolution according to various boat sizes (If rigs are not updated i.e. no intersectionGeo, fine, go with default setting build. So, we don't have to add into all characters, only to those problematic ones.
            xRes = 20
            zRes = 20
            size = 8
            for each in cmds.ls(type = 'nurbsSurface'):
                if 'NurbsIntersect_geo' in each:
                    if boatName in each:
                        _transform = cmds.listRelatives(each, parent = True, fullPath = True)
                        _makeNurbPlane = cmds.listConnections(each, type = 'makeNurbPlane')

                        if _transform:
                            size = cmds.getAttr('%s.scaleY' % _transform[0])

                        if _makeNurbPlane:
                            xRes = cmds.getAttr('%s.patchesU' % _makeNurbPlane[0])
                            zRes = cmds.getAttr('%s.patchesV' % _makeNurbPlane[0])

            ## 2. Setup the NURBS intersection planes
            oceanNPP.buildOceanNurbsPreviewPlane(xRes = xRes, zRes = zRes, size = size, oceanShader = 'ocean_dispShader', boatName = boatName)

            ## 3. Setup intersection curves
            myIntersectionCurves = oceanNPP._intersectOceanPreviewPlane(boatName = boatName)

            if boatToSkip not in eachBoatWorldCtrl:
                fluidContainers = fluidContainers
                #################
                ## FLUID BUILD ##
                #################
                ## 1. Create fluids animatable
                fluidAnimatable = '%s_fluidAnim' % boatName
                if not cmds.objExists(fluidAnimatable):
                    fluidAnimatable = all_fluidAnimatable(name = fluidAnimatable)

                ## 2. Do the speed expression now
                _buildSpeedExpression(eachBoatWorldCtrl)

                ## 3. Connect intersection curves to fluid containers
                for eachCurve in myIntersectionCurves:
                    for eachFluid in fluidContainers:
                        myEmitter = fluidsLib._connectNURBSCurveToFluidContainer(nurbsCrv = eachCurve, fluidContainer = eachFluid, boatName = boatName, worldCtrl = eachBoatWorldCtrl, animatable = fluidAnimatable)

                ## 4. Build Hull Emitter
                for x in cmds.ls(type = 'implicitSphere'):
                    tagGroup = cmds.listRelatives(x, parent = True, fullPath = True)[0].split('|')[-3]
                    if cmds.objExists('%s.type' % tagGroup):
                        if cmds.getAttr('%s.type' % tagGroup) == 'hullEmitter':
                            if boatName in x:
                                ## Now build the base hull emitter for carving through the ocean
                                transformNode = cmds.listRelatives(x, parent = True)[0]
                                fluidsLib._buildHullEmitter(eachBoatWorldCtrl, constraint = tagGroup, implicitSphere = transformNode, animatable = fluidAnimatable)

            ##############
            ## FX BUILD ##
            ##############
            # completeSideSetup = False
            if not animInteractive:
                for each in cmds.ls(type = 'transform'):
                    if cmds.objExists('%s.type' % each):
                        if cmds.getAttr('%s.type' % each) == 'rearEmitter':
                            if boatName in each:
                                ## REAR SETUP
                                #############
                                ## 1. Create rear splashes animatable
                                rearAnimatable = '%s_rear_splashAnim' % boatName
                                if not cmds.objExists(rearAnimatable):
                                    rearAnimatable = rear_splashAnimatable(name = rearAnimatable)

                                ## 2a. Build nParticleShape
                                myRearParticleShape = '%s_RearSpray' % boatName
                                if not cmds.objExists(myRearParticleShape):
                                    myRearParticleShape = npart._buildparticleShape(particleShapeName = myRearParticleShape)

                                ## 2b. Do the base particleShape setup first
                                npart._doBaseParticleShapeSetup(particleShapeName = myRearParticleShape, type = 'splash', presetName = 'rearSprayMultiStreak.mel')

                                ## 3a. Build shader now...
                                myRearShader = npart._buildParticleShader('fx_sprite')

                                ## 3b. Assign shader to particless
                                cmds.sets(myRearParticleShape, edit = True, forceElement = '%sSG' % myRearShader)

                                ## 4. Build the emitter and attach the particle system to the emitter
                                boatRearEmitter = "%s_RearSpray_emitter" % '_'.join(each.split(':'))

                                ## 5. Build a new emitter with the default emitter preset applied...
                                boatRearEmitter = npart._buildRearEmitter(name = boatRearEmitter, boatName = boatName, splashParticleName = myRearParticleShape, rearAnimatable = rearAnimatable, presetName = 'RearEmitterSplash.mel')

                                ## 6. Build Rear Emitter
                                ## Now constrain this to the rig locator designated by the rigging artist for the emitters location.
                                pConstraint_offsetGrp   = cmds.group(empty = True, name = '%s_OFFSET_GRP' % boatRearEmitter, parent = 'nPARTICLE_EMITTERS_hrc')
                                pConstraint_consGrp     = cmds.group(pConstraint_offsetGrp, name = '%s_CONS_GRP' % boatRearEmitter)
                                pConstraint             = cmds.parentConstraint(each, pConstraint_consGrp, mo = False)[0]
                                cmds.delete( cmds.parentConstraint(pConstraint_offsetGrp, boatRearEmitter, mo = False) )
                                cmds.parent(boatRearEmitter, pConstraint_offsetGrp)

                                ## 7. Offset attrs for offset_group
                                cmds.setAttr('%s.rotateX' % pConstraint_offsetGrp, 45)
                                cmds.setAttr('%s.rotateY' % pConstraint_offsetGrp, 180)

                                ## 8. Setup the expressions for the nParticleShape now
                                npart._setupRear_ParticleExpressions(particleShapeName = myRearParticleShape, type = 'splash', boatWorldCtrl = eachBoatWorldCtrl, boatName = boatName, rearAnimatable = rearAnimatable)

            #                     #################################################################
            #                     ## SIDE SETUP
            #                     #############
            #                     if not completeSideSetup:
            #                         ## Create side splashes animatable
            #                         sideAnimatable = '%s_side_splashAnim' % boatName
            #                         if not cmds.objExists(sideAnimatable):
            #                             sideAnimatable = side_splashAnimatable(name = sideAnimatable)
            #
            #                         ## 1. Build nParticleShape
            #                         mySideSpriteParticleShape   = npart._buildparticleShape(particleShapeName = '%s_SideSpraySprite' % boatName)
            #                         mySideMistParticleShape     = npart._buildparticleShape(particleShapeName = '%s_SideSprayMist' % boatName)
            #
            #                         ## 2. Do the base particleShape setup first
            #                         npart._doBaseParticleShapeSetup(particleShapeName = mySideSpriteParticleShape, type = 'splash', presetName = 'sideSprayMultiStreak.mel')
            #                         npart._doBaseParticleShapeSetup(particleShapeName = mySideMistParticleShape, type = 'mist', presetName = 'sideSprayMultiPoint.mel')
            #
            #                         ## 3. Build shader now...
            #                         mySideShader = npart._buildParticleShader('fx_sprite')
            #
            #                         ## 4. Assign shader to particles
            #                         cmds.sets(mySideSpriteParticleShape, edit = True, forceElement = '%sSG' % mySideShader) # splash
            #                         # cmds.sets(mySideMistParticleShape, edit = True, forceElement = 'initialParticleSE') # mist
            #
            #                         for each in myIntersectionCurves:
            #                             if 'Right' in each:
            #                                 presetName = 'SideRightEmitterSplash.mel'
            #                             elif 'Left' in each:
            #                                 presetName = 'SideLeftEmitterSplash.mel'
            #
            #                             ## 5. Build emitter...
            #                             if cmds.getAttr('%s.spans' % each) > 0: # Check if the curve is not intersecting
            #                                 cPoS_name = npart._buildSideSplashEmitter(name                      = '%s_SideSpray' % each,
            #                                                                           boatName                  = boatName,
            #                                                                           boatIntersectCurveShape   = each,
            #                                                                           splashParticleName        = [mySideSpriteParticleShape, mySideMistParticleShape],
            #                                                                           sideAnimatable            = sideAnimatable,
            #                                                                           presetName                = presetName,
            #                                                                           )
            #
            #                                 ## 6. Setup the expressions for the nParticleShape now...
            #                                 npart._setupSide_ParticleExpressions(particleShapeName = mySideSpriteParticleShape, type = 'splash', boatWorldCtrl = eachBoatWorldCtrl, boatName = boatName, cPoS = cPoS_name, sideAnimatable = sideAnimatable)
            #                                 npart._setupSide_ParticleExpressions(particleShapeName = mySideMistParticleShape, type = 'mist', boatWorldCtrl = eachBoatWorldCtrl, boatName = boatName, cPoS = cPoS_name, sideAnimatable = sideAnimatable)
            #
            #                         completeSideSetup = True

    ## Finalizing build by creating necessary SETS for easy selection
    ## Animatable
    _createSet(name = 'FX_ANIM', type = 'transform', endswith = 'Anim')
    ## fluidTexture3D
    _createSet(name = 'FX_FLUID_CONTAINER', type = 'fluidTexture3D', shapeOnly = False)
    ## fluidEmitter
    _createSet(name = 'FX_FLUID_EMITTER', type = 'fluidEmitter')
    ## nParticle
    _createSet(name = 'FX_NPARTICLE', type = 'nParticle', shapeOnly = False)
    ## pointEmitter
    _createSet(name = 'FX_NPARTICLE_EMITTER', type = 'pointEmitter')
    ## heightField
    _createSet(name = 'FX_HEIGHT_FIELD', type = 'heightField', shapeOnly = False)

    ## Clean-up all animatables into a group
    allAnimatable = [x for x in cmds.ls(type = 'transform') if x.endswith('Anim')]
    if allAnimatable:
        if cmds.objExists('Shot_FX_hrc'):
            if not cmds.objExists('FX_ANIM_hrc'):
                cmds.group(allAnimatable, name = 'FX_ANIM_hrc', parent = 'Shot_FX_hrc')
            else:
                for each in allAnimatable:
                    _parent = cmds.listRelatives(each, parent = True)
                    if _parent:
                        if 'FX_ANIM_hrc' not in _parent:
                            cmds.parent(each, 'FX_ANIM_hrc')
                    else:
                        cmds.parent(each, 'FX_ANIM_hrc')

    ## Set a clean modelPanel for FX environment
    fxLib._fx_modelPanel_cleanUp(modelPanel = '')