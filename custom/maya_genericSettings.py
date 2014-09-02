import os, sys
import maya.cmds as cmds
import maya.mel as mel
import tank
from tank import TankError
try:
    from mentalcore import mapi
except:
    pass
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug
import utils as utils

def setBoundingBoxViewPortDisplay(selected = False, val = True):
    """
    Function to set the boundingbox in viewport
    """
    if selected:
        for each in cmds.ls(sl=True):
            getShapes = [eachChild for eachChild in cmds.listRelatives(each, children = True) if cmds.nodeType(eachChild) == 'mesh']
            for eachMesh in getShapes:
                cmds.setAttr('%s.overrideEnabled' % eachMesh, val)
                cmds.setAttr('%s.overrideLevelOfDetail' % eachMesh, val)
    else:
        for each in cmds.ls(type = 'mesh'):
            cmds.setAttr('%s.overrideEnabled' % each, val)
            cmds.setAttr('%s.overrideLevelOfDetail' % each, val)

def detachSubDiv(mySel = cmds.ls(sl=True)):
    ## Store selection
    if mySel:
        for each in mySel:
            getShape = [eachShape for eachShape in cmds.listRelatives(each, children = True, f = True) if cmds.nodeType(eachShape) == 'mesh']
            if getShape:
                if cmds.objExists("%s.smoothed" %  each):
                    cmds.setAttr('%s.smoothed' % each, 0)
                
                if cmds.objExists('%s.miSubdivApprox' % getShape[0]):
                    for each in getShape:
                        try:
                            cmds.disconnectAttr('auto_mrSubdAppx.message', '%s.miSubdivApprox' % each)
                        except:pass
    else:
        cmds.warning('You need a valid selection!')
    
def attachMentalRaySubDiv():
    ## Build the auto-mrSubDAppx now...
    if cmds.objExists('auto_mrSubdAppx'):
        cmds.delete('auto_mrSubdAppx')
        print '"auto_mrSubdAppx" has been deleted.'
    subdNode = cmds.createNode( 'mentalraySubdivApprox', name = 'auto_mrSubdAppx' )
    debug(app = None, method = 'attachMentalRaySubDiv', message = 'Success rebuilt auto_mrSubdAppx', verbose = False)

    ## Now find the smooth attr
    toSmooth = []
    for each in cmds.ls(type = 'transform'):
        try:
            if cmds.getAttr('%s.smoothed' % each) == 1:
                toSmooth.extend([each])
        except ValueError:
            pass

    ## Now assign to the subDNode
    try:
        cmds.select(toSmooth, r = True)
        try:
            mel.eval("""sz_RV_AssignMRApprox Subdiv """ + subdNode + """ "attach";""")
        except RuntimeError:
            pass
        cmds.select(clear = True)
    except TypeError:
        pass

    ## Now set the attrs for the approx node..
    cmds.setAttr(subdNode + '.approxMethod', 2)
    cmds.setAttr(subdNode + '.minSubdivisions', 0)
    cmds.setAttr(subdNode + '.maxSubdivisions', 2)
    cmds.setAttr(subdNode + '.length', 0.6)
    cmds.setAttr(subdNode + '.viewDependent', 1)
    cmds.setAttr(subdNode + '.fine', 1)

def _setCameraDefaults(camera = ''):
    """
    Sets the base defaults for the camera
    @param camera: The name of the camera transform node NOT the shape node!
    @type camera: String
    """
    if not camera:
        camera = utils.getShotCamera()

    if camera:
        camName = camera
        camShape = cmds.listRelatives(camera, shapes = True)[0]
        cmds.camera(camName, e = True,  displayFilmGate  = 0,  displayResolution = 1,  overscan = 1.19)
        cmds.setAttr("%s.displayGateMask" % camShape, 1)
        cmds.setAttr('%s.displayGateMaskOpacity' % camShape, 1)
        cmds.setAttr('%s.displayGateMaskColor' % camShape, 0, 0, 0, type = 'double3' )
        cmds.setAttr("%s.displayResolution" % camShape, 1)
        cmds.setAttr("%s.displaySafeAction" % camShape, 1)
        cmds.setAttr("%s.journalCommand" % camShape, 0)
        cmds.setAttr("%s.nearClipPlane" % camShape, 0.05)
        cmds.setAttr("%s.overscan" % camShape, 1)

def _setHWRenderGlobals(width = 1280, height = 720, animation = False):
    cmds.currentUnit(time = 'pal')
    cmds.currentUnit(linear = 'cm')

    mel.eval('setAttr defaultResolution.width %s' % width)
    mel.eval('setAttr defaultResolution.height %s' % height)
    mel.eval('setAttr defaultResolution.deviceAspectRatio 1.777')
    mel.eval('setAttr defaultResolution.pixelAspect 1')

    cmds.setAttr('defaultRenderGlobals.currentRenderer','mayaHardware', type = 'string')
    # mel.eval('unifiedRenderGlobalsWindow;')

    ## Default Render Globals
    cmds.setAttr('defaultRenderGlobals.imageFormat', 51)
    cmds.setAttr('defaultRenderGlobals.imfkey','exr', type = 'string')
    cmds.setAttr('defaultRenderGlobals.animation', 1)
    cmds.setAttr('defaultRenderGlobals.extensionPadding', 3)
    cmds.getAttr('defaultRenderGlobals.extensionPadding')
    cmds.setAttr('defaultRenderGlobals.periodInExt', 1)
    cmds.setAttr('defaultRenderGlobals.outFormatControl', 0)
    cmds.setAttr('defaultRenderGlobals.putFrameBeforeExt', 1)
    cmds.setAttr('defaultRenderGlobals.enableDefaultLight', 0)
    cmds.setAttr('defaultResolution.aspectLock', 0)

    ## Set Hardware render globals
    cmds.setAttr("hardwareRenderGlobals.colorTextureResolution", 512)
    cmds.setAttr("hardwareRenderGlobals.bumpTextureResolution", 1024)
    cmds.setAttr("hardwareRenderGlobals.enableNonPowerOfTwoTexture", 1)
    cmds.setAttr("hardwareRenderGlobals.culling", 0)
    cmds.setAttr("hardwareRenderGlobals.numberOfSamples", 9)
    cmds.setAttr("hardwareRenderGlobals.textureCompression", 0)
    cmds.setAttr("hardwareRenderGlobals.motionBlurByFrame", .5)
    cmds.setAttr("hardwareRenderGlobals.numberOfExposures", 3)
    cmds.setAttr("hardwareRenderGlobals.maximumGeometryCacheSize", 64)
    cmds.setAttr("hardwareRenderGlobals.enableGeometryMask", 1)
    cmds.setAttr("hardwareRenderGlobals.blendSpecularWithAlpha", 0)
    cmds.setAttr("hardwareRenderGlobals.enableHighQualityLighting", 1)
    cmds.setAttr("hardwareRenderGlobals.frameBufferFormat", 1)

def _setRenderGlobals(width = 1280, height = 720, animation = False):
    cmds.currentUnit(time='pal')
    debug(app = None, method = 'utils._setRenderGlobals', message= 'Set currentTime to pal', verbose = False)
    cmds.currentUnit(linear='cm')
    debug(app = None, method = 'utils._setRenderGlobals', message= 'Set units to cm', verbose = False)

    mel.eval('setAttr defaultResolution.width %s' % width)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'Set defaultResolution width: %s' % width, verbose = False)
    mel.eval('setAttr defaultResolution.height %s' % height)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'Set defaultResolution height: %s' % height, verbose = False)
    mel.eval('setAttr defaultResolution.deviceAspectRatio 1.777')
    debug(app = None, method = 'utils._setRenderGlobals', message= 'Set defaultResolution deviceAspectRatio: 1.777', verbose = False)
    mel.eval('setAttr defaultResolution.pixelAspect 1')
    debug(app = None, method = 'utils._setRenderGlobals', message= 'Set defaultResolution pixelAspect: 1', verbose = False)

    ## load mentalray
    if not cmds.pluginInfo( 'Mayatomr', query=True, loaded = True ):
        cmds.loadPlugin('Mayatomr')
        debug(app = None, method = 'utils._setRenderGlobals', message= 'Loaded Mayatomr plugin..', verbose = False)

    cmds.setAttr('defaultRenderGlobals.currentRenderer','mentalRay', type = 'string')
    debug(app = None, method = 'utils._setRenderGlobals', message= 'Set currentRenderer to mentalRay', verbose = False)
    mel.eval('unifiedRenderGlobalsWindow;')
    debug(app = None, method = 'utils._setRenderGlobals', message= 'unifiedRenderGlobalsWindow', verbose = False)

    # Default Render Globals
    # /////////////////////
    cmds.setAttr('defaultRenderGlobals.imageFormat', 51)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.imageFormat: 51', verbose = False)

    cmds.setAttr('defaultRenderGlobals.imfkey','exr', type = 'string')
    debug(app = None, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.imfkey: exr', verbose = False)

    cmds.setAttr('defaultRenderGlobals.animation', 1)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.animation: 1', verbose = False)

    cmds.setAttr('defaultRenderGlobals.extensionPadding', 3)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.extensionPadding: 3', verbose = False)

    cmds.getAttr('defaultRenderGlobals.extensionPadding')

    cmds.setAttr('defaultRenderGlobals.periodInExt', 1)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.periodInExt: 1', verbose = False)

    cmds.setAttr('defaultRenderGlobals.outFormatControl', 0)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.outFormatControl: 0', verbose = False)

    cmds.setAttr('defaultRenderGlobals.putFrameBeforeExt', 1)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.putFrameBeforeExt: 1', verbose = False)

    cmds.setAttr('defaultRenderGlobals.enableDefaultLight', 0)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.enableDefaultLight: 0', verbose = False)

    cmds.setAttr('defaultResolution.aspectLock', 0)
    debug(app = None, method = 'utils._setRenderGlobals', message= 'defaultRenderGlobals.aspectLock: 0', verbose = False)

    # MentalRay Globals
    # /////////////////////
    cmds.setAttr('mentalrayGlobals.imageCompression', 4)
    cmds.setAttr('mentalrayGlobals.exportPostEffects', 0)
    cmds.setAttr('mentalrayGlobals.accelerationMethod', 4)
    cmds.setAttr('mentalrayGlobals.exportVerbosity', 5)
    # miDefault Frame Buffer
    cmds.setAttr('miDefaultFramebuffer.datatype', 16)
    # miDefault sampling defaults
    cmds.setAttr('miDefaultOptions.filterWidth', 0.6666666667)
    cmds.setAttr('miDefaultOptions.filterHeight', 0.6666666667)
    cmds.setAttr('miDefaultOptions.filter', 2)
    cmds.setAttr('miDefaultOptions.sampleLock', 0)
    # enable raytracing, disable scanline
    cmds.setAttr('miDefaultOptions.scanline', 0)
    try:
        cmds.optionMenuGrp('miSampleModeCtrl', edit = True,  select = 2)
    except:
        pass
    cmds.setAttr('miDefaultOptions.minSamples', -2)
    cmds.setAttr('miDefaultOptions.maxSamples', 0)

    # set sampling quality for RGB channel to eliminate noise
    # costs a bit extra time because it will sample more in the
    # red / green channel but will be faster for blue.
    # using unified sampling
    cmds.setAttr('miDefaultOptions.contrastR', 0.04)
    cmds.setAttr('miDefaultOptions.contrastG', 0.03)
    cmds.setAttr('miDefaultOptions.contrastB', 0.06)
    cmds.setAttr('miDefaultOptions.contrastA', 0.03)

    cmds.setAttr('miDefaultOptions.maxReflectionRays', 3)
    cmds.setAttr('miDefaultOptions.maxRefractionRays', 3)
    cmds.setAttr('miDefaultOptions.maxRayDepth', 5)
    cmds.setAttr('miDefaultOptions.maxShadowRayDepth', 5)

    cmds.setAttr('miDefaultOptions.finalGatherRays', 20)
    cmds.setAttr('miDefaultOptions.finalGatherPresampleDensity', 0.2)
    cmds.setAttr('miDefaultOptions.finalGatherTraceDiffuse', 0)
    cmds.setAttr('miDefaultOptions.finalGatherPoints', 50)

    cmds.setAttr('miDefaultOptions.displacePresample', 0)

    playStart  = cmds.playbackOptions( query = True, minTime= True)
    playFinish = cmds.playbackOptions( query = True, maxTime= True)
    cmds.setAttr('defaultRenderGlobals.startFrame', playStart)
    cmds.setAttr('defaultRenderGlobals.endFrame', playFinish)

    # MentalCore
    # /////////////////////
    if not animation:
        try:
            mapi.enable(True)
            cmds.setAttr('mentalcoreGlobals.en_colour_management',1)
            mel.eval('unifiedRenderGlobalsWindow;')

            cmds.setAttr('mentalcoreGlobals.contrast_all_buffers', 1)

            cmds.setAttr('mentalcoreGlobals.output_mode', 0)
            cmds.setAttr('mentalcoreGlobals.unified_sampling', 1)
            cmds.setAttr('mentalcoreGlobals.samples_min', 1)
            cmds.setAttr('mentalcoreGlobals.samples_max', 80)
            cmds.setAttr('mentalcoreGlobals.samples_quality', 0.8)
            cmds.setAttr('mentalcoreGlobals.samples_error_cutoff', 0.02)

            cmds.setAttr('mentalcoreGlobals.en_envl', 1)
            cmds.setAttr('mentalcoreGlobals.envl_scale', 0.5)
            cmds.setAttr('mentalcoreGlobals.envl_blur_res', 0)
            cmds.setAttr('mentalcoreGlobals.envl_blur', 0)
            cmds.setAttr('mentalcoreGlobals.envl_en_flood_colour', 1)
            cmds.setAttr('mentalcoreGlobals.envl_flood_colour', 1, 1, 1, 1, type = 'double3')
            cmds.setAttr('mentalcoreGlobals.en_ao', 1)
            cmds.setAttr('mentalcoreGlobals.ao_samples', 24)
            cmds.setAttr('mentalcoreGlobals.ao_spread', 60)
            cmds.setAttr('mentalcoreGlobals.ao_near_clip', 1)
            cmds.setAttr('mentalcoreGlobals.ao_far_clip', 10)
            cmds.setAttr('mentalcoreGlobals.ao_opacity', 0)
            cmds.setAttr('mentalcoreGlobals.ao_vis_indirect', 0)
            cmds.setAttr('mentalcoreGlobals.ao_vis_refl', 0)
            cmds.setAttr('mentalcoreGlobals.ao_vis_refr', 1)
            cmds.setAttr('mentalcoreGlobals.ao_vis_trans', 1)
        except:
            cmds.warning('NO MENTAL CORE LOADED!!!')
            pass

        # Default Resolution
        cmds.setAttr('defaultResolution.width', 1280)
        cmds.setAttr('defaultResolution.height', 720)
        cmds.setAttr('defaultResolution.pixelAspect', 1)
        cmds.setAttr('defaultResolution.deviceAspectRatio', 1.7778)
        print 'Default render settings initialized.'

def _createCamGate(camera = '', pathToImage = 'I:/lsapipeline/fx/ImageGate_1280_720.png'):
    if not camera:
        camera = utils.getShotCamera()

    if camera:
        if not cmds.objExists('camGate'):
            cmds.imagePlane(n = 'camGate')
            cmds.rename('camGate1', 'camGate')
            cmds.pointConstraint('%s' % camera, 'camGate', mo = False, n ='tmpPoint')
            cmds.orientConstraint('%s' % camera, 'camGate', mo = False, n ='tmpOrient')
            cmds.delete(['tmpPoint', 'tmpOrient'])
            cmds.parent('camGate', '%s' % camera)
            cmds.connectAttr('camGateShape.message', '%sShape.imagePlane[0]' % camera, f = True)
            cmds.setAttr('camGate.depth', 0.01)
            cmds.setAttr('camGate.sizeX', 1.710)
            cmds.setAttr('camGate.sizeY', 2)
            cmds.setAttr('camGate.offsetX', 0.004)
            cmds.setAttr('camGate.offsetY', 0.003)
            cmds.setAttr('camGateShape.imageName', pathToImage, type = 'string')
            cmds.setAttr('camGateShape.lockedToCamera', 1)
            cmds.setAttr('camGateShape.displayOnlyIfCurrent', 1)

def _showCamShotHUD():
    pass