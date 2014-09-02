import maya.cmds as cmds
import os, sys
import maya.mel as mel
## Custom stuff
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
if 'T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean' not in sys.path:
    sys.path.append('T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean')
from debug import debug
import boat_FX as bfx
import utils as utils
import maya_asset_MASTERCLEANUPCODE as cleanup
import connectOceanHeights as connOH
import boat_FX as bfx
import utils as utils
import fluids_lib as fluidLib
import CONST as CONST
import fluidCaches as fluidCaches
#reload(CONST)
#reload(utils)
#reload(bfx)
#reload(connOH)
#reload(fluidCaches)

def _findOceans(*args):
    """
    Find existing oceans within scene and add to TSL
    """
    allOceans = cmds.ls(type = 'oceanShader')
    return allOceans

def _connectAnimToDisp(shaderToConnect = CONST.OCEANANIMSHADER, previewPlaneName = CONST.OCEAN_ANIM_PREVIEWPLANENAME):
    """
    Function used to export the current DISP ocean preset and apply it to the animation Ocean so the animation is following the main displacement
    It is important to note that the wakes interfer with animation so we needed two oceans to handle this
    """
    ##NOTE TRYING THIS JUST CRASHES MAYA!!
#     attrs = [
#             'waterColor', 'transparency', 'ambientColor', 'incandescence', 'observerSpeed', 'waveDirSpread', 'numFrequencies',  'waveLengthMin', 'waveLengthMax',
#             'waveHeight[0]', 'waveTurbulence', 'wavePeaking', 'scale', 'time', 'windUV', 'waveSpeed', 'waveHeight[0]', 'waveTurbulence[0]', 'wavePeaking[0]', 'wavePeaking[1]'
#             ]
    attrs = [
            'time'
            ]
    for eachAttr in attrs:
        try:
            cmds.connectAttr('%s.%s' % (CONST.OCEANDISPSHADER, eachAttr), '%s.%s' % (shaderToConnect, eachAttr), f = True)
        except RuntimeError:
            pass

    if not cmds.objExists(previewPlaneName):
        ## Build the height field for showing the animation plane without the fluid effects in it
        cmds.shadingNode('heightField', n = '%s_heightF' % previewPlaneName, asUtility = True)
        cmds.rename('transform1', previewPlaneName)
        cmds.connectAttr("%s.displacement" % shaderToConnect, '%s_heightF.displacement' % previewPlaneName, f  = True)
        cmds.connectAttr("%s.outColor" % shaderToConnect, '%s_heightF.color' % previewPlaneName, f  = True)

        ## Now connect the original preview plane to the new anim so they follow each other properly
        attrs = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ', 'resolution']
        for eachAttr in attrs:
            cmds.connectAttr("oceanPreviewPlane_prv.%s" % eachAttr, '%s.%s' % (previewPlaneName, eachAttr), f  = True)

    debug(None, method = '_connectAnimToDisp', message = 'Successfully connected %s to %s' % ('oceanPreviewPlane_prv', previewPlaneName), verbose = False)

def _createInteractiveOcean():
    """
    Create the interactive ocean shader for the master boat to lock down to
    """
    if not cmds.objExists(CONST.OCEANDISPSHADER):
        cmds.warning('No base ocean built, please build the base ocean first before running this tool.')
    else:
        if not cmds.objExists(CONST.OCEANINTERACTIVESHADER):
            debug(None, method = '_createInteractiveOcean', message = 'Building: %s' % CONST.OCEANINTERACTIVESHADER, verbose = False)
            cmds.duplicate(CONST.OCEANDISPSHADER, n = CONST.OCEANINTERACTIVESHADER)
            debug(None, method = '_createInteractiveOcean', message = 'Build successfully: %s' % CONST.OCEANINTERACTIVESHADER, verbose = False)

            debug(None, method = '_createInteractiveOcean', message = 'Connecting: %s to %s' % (CONST.OCEANINTERACTIVESHADER, CONST.OCEAN_INTERACTIVE_PREVIEWPLANENAME), verbose = False)
            _connectAnimToDisp(shaderToConnect = CONST.OCEANINTERACTIVESHADER, previewPlaneName = CONST.OCEAN_INTERACTIVE_PREVIEWPLANENAME)

def _createOcean(editor, pathToPreset):
    """
    Add a base ocean if there are none in scene, and apply the preset found on pathToPreset

    @param editor:               Name of the maya model editor
    @param pathToOceanPreset:    tank template path for the presets
    @type pathToOceanPreset:     tank template path
    @type editor:                String
    """
    debug(None, method = '_createOcean', message = '_createOcean now...', verbose = False)
    debug(None, method = '_createOcean', message = 'pathToPreset: %s' % pathToPreset, verbose = False)
    mel.eval("CreateOcean;")

    ## Clean up the names
    cmds.rename('transform1', 'oceanPreviewPlane_prv')
    cmds.rename('oceanPlane1', 'ocean_srf')

    ## Now add the fx attr so the shot_scan scene has something to find when exporting 2ndry shot data for the ocean mel preset from the shot
    cmds.addAttr('ocean_srf', ln = 'type', dt = 'string')
    cmds.setAttr('%s.type' % 'ocean_srf', 'fx', type = 'string')

    ## Rename and create the anim shader
    cmds.rename('oceanPreviewPlane1', 'oceanPreviewPlane_heightF')
    if not cmds.objExists(CONST.OCEANDISPSHADER):
        cmds.rename('oceanShader1', CONST.OCEANDISPSHADER)
        if not cmds.objExists(CONST.OCEANANIMSHADER):
            cmds.duplicate(CONST.OCEANDISPSHADER, n = CONST.OCEANANIMSHADER)
            _connectAnimToDisp()
    else:
        cmds.warning('You already have an ocean setup. Clean this up and try running again.')
        return -1

    ## Lock height scale value
    cmds.setAttr ("oceanPreviewPlane_heightF.heightScale", lock = True)
    getCam = cmds.modelEditor(editor, query = True, camera = True)
    position = cmds.camera(getCam, q=True, worldCenterOfInterest= True)

    cmds.setAttr ("oceanPreviewPlane_prv.tx", position[0])
    cmds.setAttr ("oceanPreviewPlane_prv.tz", position[2])
    cmds.setAttr ("ocean_srf.tx", position[0])
    cmds.setAttr ("ocean_srf.tz", position[2])

    allOceans = cmds.ls(type= 'oceanShader')
    pathToPreset = pathToPreset.replace("\\", "/")
    for eachOcean in allOceans:
        mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(eachOcean, pathToPreset) )
        debug(None, method = '_createOcean', message = 'Ocean preset applied to %s: %s' % (eachOcean, pathToPreset), verbose = False)

    utils.createTypeTag(obj = CONST.OCEANDISPSHADER, typeName = 'oceanShader')
    debug(None, method = '_createOcean', message = '_createOcean completed successfully.', verbose = False)

def _build_OceanWakeAndFoam_FluidContainers(editor = '', ocean_foam_template= '', ocean_wake_template = '', oceanSHD = CONST.OCEANDISPSHADER,
                                            wakeFluidShapeName = CONST.WAKE_FLUID_SHAPENODE, foamFluidShapeName = CONST.FOAM_FLUID_SHAPENODE):
    """
    Create both fluid containers linked to ocean
    """
    ## Gget fluid containers already in scene
    fluidContainers = cmds.ls(type= 'fluidTexture3D')
    debug(None, method = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers', message = 'fluidContainers: %s' % fluidContainers, verbose = False)
    flGrp = 'fluids_hrc'

    ## Create fluid group if it does not already exist
    if not cmds.objExists(flGrp):
        flGrp = cmds.group(em = True, name = flGrp)
        debug(None, method = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers', message = 'Built grp: %s' % flGrp, verbose = False)
        attrs = ['ty', 'sx', 'sy', 'sz', 'rx', 'rz']
        ## Lock attrs
        for eachAttr in attrs:
            cmds.setAttr ("%s.%s" % (flGrp, eachAttr), lock = True)
            cmds.setAttr ("%s.%s" % (flGrp, eachAttr), keyable = False , channelBox = False)
        debug(None, method = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers', message = 'Locked attrs for grp: %s' % flGrp, verbose = False)

        ## Set the last attrs
        cmds.setAttr (flGrp + ".ry", k=False, cb= True)
        cmds.setAttr (flGrp + ".tx", k=False, cb= True)
        cmds.setAttr (flGrp + ".tz", k=False, cb= True)
        debug(None, method = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers', message = 'Hidden attrs for grp: %s' % flGrp, verbose = False)

    ## Add the type attr if it doesn't already exits
    if not cmds.objExists('%s.type' % flGrp):
        cmds.addAttr(flGrp, ln = 'type', dt = 'string')
        cmds.setAttr('%s.type' % flGrp, 'fx', type = 'string')
        debug(None, method = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers', message = 'Added attrs to grp: %s' % flGrp, verbose = False)

    ## Add custom attrs for fluid container scales
    if cmds.objExists('OCEAN_hrc'):
        try:
            cmds.addAttr('OCEAN_hrc', longName =  'containerWidth', at = "long",defaultValue = 50,)
            cmds.setAttr("OCEAN_hrc.containerWidth", k=False, cb= True)
            cmds.addAttr('OCEAN_hrc', longName =  'containerLength', at = "long",defaultValue = 50)
            cmds.setAttr("OCEAN_hrc.containerLength", k=False, cb= True)
            debug(None, method = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers', message = 'Added attrs for grp: OCEAN_hrc', verbose = False)
        except: ## already added
            pass

    if not cmds.objExists(foamFluidShapeName):
        debug(None, method = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers', message = 'Adding %s...' % foamFluidShapeName, verbose = False)
        foamFluid = fluidLib._create_FOAM_FluidTexture(oceanSHD, 20, ocean_foam_template, foamFluidShapeName)

        ## Now parent the fluid to the flGrp
        debug(None, method = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers', message = 'foamFluid: %s' % foamFluid, verbose = False)
        cmds.parent('%s' % foamFluid.split('Shape')[0], flGrp)

        ## Now connect the OCEAN_hrc groups attrs to the dimensions
        cmds.connectAttr("OCEAN_hrc.containerWidth",  '%s.dimensionsW' % foamFluid, f = True)
        cmds.connectAttr("OCEAN_hrc.containerLength",  '%s.dimensionsH' % foamFluid, f = True)

    if not cmds.objExists(wakeFluidShapeName):
        debug(None, method = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers', message = 'Adding %s...' % wakeFluidShapeName, verbose = False)
        wakeFluid = fluidLib._create_WAKE_FluidTexture(oceanSHD, 20, ocean_wake_template, wakeFluidShapeName)

        ## Now parent the fluid to the flGrp
        cmds.parent('%s' % wakeFluid.split('Shape')[0], flGrp)

        ## Now connect the OCEAN_hrc groups attrs to the dimensions
        cmds.connectAttr("OCEAN_hrc.containerWidth",  '%s.dimensionsW' % wakeFluid, f = True)
        cmds.connectAttr("OCEAN_hrc.containerLength",  '%s.dimensionsH' % wakeFluid, f = True)

    ## Move group to persp camera position in x and z
    getCam = cmds.modelEditor(editor, query = True, camera = True)
    position = cmds.camera(getCam, q=True, worldCenterOfInterest= True)
    try:
        cmds.setAttr (flGrp + ".tx", position[0])
        cmds.setAttr (flGrp + ".tz", position[2])
    except:
        pass

    ## Attrs to manage calculations on the fluid texturesc
    if not cmds.objExists("OCEAN_hrc.oceanCalcOnOff"):
        cmds.addAttr('OCEAN_hrc', longName =  'oceanCalcOnOff', attributeType =  'float', min = 0, max =1, defaultValue = 1)
        cmds.setAttr('OCEAN_hrc.oceanCalcOnOff', keyable  = True)

    ## Now build a multidiv to flip the value so it's not confusing to animators...
    if not cmds.objExists('wakesOnOffMultiDiv'):
        cmds.shadingNode('blendColors', asUtility = True, n = 'wakesOnOffMultiDiv',)

    try:
        cmds.connectAttr('OCEAN_hrc.oceanCalcOnOff', 'wakesOnOffMultiDiv.blender', f= True)
    except:
        pass

    cmds.setAttr('wakesOnOffMultiDiv.color1', 0, 0, 0, type = 'double3')
    cmds.setAttr('wakesOnOffMultiDiv.color2', 1, 1, 1, type = 'double3')

    ## Now connect these to the OCEAN_hrc eval calc attrs
    try:
        cmds.connectAttr("wakesOnOffMultiDiv.outputG",     "%s.disableInteractiveEval" % wakeFluidShapeName, f = True)
        cmds.connectAttr("wakesOnOffMultiDiv.outputG",     "%s.disableInteractiveEval" % foamFluidShapeName, f = True)
    except:
        pass

def _buildOceanGroups():
    """
    Build the base ocean groups
    """

    debug(None, method = '_buildOceanGroups', message = '_buildOceanGroups now...', verbose = False)
    ## Now get a shotbased FX group built
    if not cmds.objExists('Shot_FX_hrc'):
        cmds.group(n = 'Shot_FX_hrc', em = True)
        debug(None, method = '_buildOceanGroups', message = 'Shot_FX_hrc group built...', verbose = False)

    ## Now group the build
    if not cmds.objExists('OCEAN_hrc'):
        cmds.group(n = 'OCEAN_hrc', em = True)
        debug(None, method = '_buildOceanGroups', message = 'OCEAN_hrc group built...', verbose = False)

    debug(None, method = '_buildOceanGroups', message = '_buildOceanGroups FINISHED...', verbose = False)

def _cleanupOcean():
    """
    Cleans up the parenting of various build stuff for the ocean setup
    """

    debug(None, method = '_cleanupOcean', message = '_cleanupOcean now...', verbose = False)
    ## General cleanup
    if not cmds.objExists('Shot_FX_hrc'):
        cmds.ground(n = 'Shot_FX_hrc', em = True)

    if cmds.objExists('fx_nucleus'):
        try:
            cmds.parent('fx_nucleus', 'Shot_FX_hrc')
        except:
            pass

    if cmds.objExists('nucleus'):
        try:
            cmds.parent('nucleus', 'Shot_FX_hrc')
        except:
            pass

    cmds.setAttr("ocean_srfShape.overrideEnabled", 1)
    cmds.setAttr("ocean_srfShape.overrideDisplayType", 2)
    cmds.setAttr("animPreviewPlane_prv.visibility", 0)

    try:
        cmds.connectAttr('oceanPreviewPlane_prv.translateX', 'fluids_hrc.translateX', f = True)
        cmds.connectAttr('oceanPreviewPlane_prv.translateZ', 'fluids_hrc.translateZ', f = True)
    except RuntimeError:
        pass
    try:
        cmds.connectAttr('oceanPreviewPlane_prv.translateX', 'ocean_srf.translateX', f = True)
        cmds.connectAttr('oceanPreviewPlane_prv.translateZ', 'ocean_srf.translateZ', f = True)
    except RuntimeError:
        pass

    ## Fucking hell maya needs to just realise it's parented already and just NOT FAIL driving me nuts with all the try excepts!!
    try:
        cmds.parent('animPreviewPlane_prv', 'OCEAN_hrc')
    except RuntimeError:
        pass

    try:
        cmds.parent(['ocean_srf', 'oceanPreviewPlane_prv'], 'OCEAN_hrc')
    except RuntimeError:
        pass

    try:
        cmds.parent('fluids_hrc', 'OCEAN_hrc')
    except:
        pass

    debug(None, method = '_cleanupOcean', message = '_cleanupOcean FINSIHED...', verbose = False)

#############################
#### MAIN OCEAN BUILD SCRIPTS
#############################

def _buildBaseOceanSetup(editor, ocean_preset_template = '', ocean_foam_template = '', ocean_wake_template = '', hiTide = False):
    """
    Used to setup the base ocean for either FX or Animation.
    The is the base build for the ocean
    @param editor:                     The name of the current modelEditor in the scene to get the camera from
    @param ocean_preset_template:     A valid shotgun template
    @param ocean_foam_template:     A valid shotgun template
    @param ocean_wake_template:     A valid shotgun template
    @param hiTide:                     If the scene is hi or low tide. Note this isn't being used at this time
    @type editor:                      String
    @type ocean_preset_template:     A valid shotgun template
    @type ocean_foam_template:         A valid shotgun template
    @type ocean_wake_template:        A valid shotgun template
    @type hiTide:                     Boolean
    """
    debug(None, method = '_buildBaseOceanSetup', message = 'Entered...', verbose = False)
    debug(None, method = '_buildBaseOceanSetup', message = '_buildOceanGroups...', verbose = False)
    _buildOceanGroups()
    print

    if cmds.objExists('wakesOnOfMultiDiv'):
        cmds.delete('wakesOnOfMultiDiv')
        debug(None, method = '_buildBaseOceanSetup', message = 'Removed wakesOnOfMultiDiv...', verbose = False)

    lowCond = 'OceanPrev_highRes_condition'
    hiCond =  'OceanPrev_lowRes_condition'
    resAddSub = 'OceanPrev_Res_addsubtract'

    anyOceans = cmds.ls(type = "oceanShader")
    if not anyOceans:
        debug(None, method = '_buildBaseOceanSetup', message = 'Creating new ocean...', verbose = False)
        _createOcean(editor, ocean_preset_template)
    else:
        debug(None, method = '_buildBaseOceanSetup', message = 'Ocean already exists in scene: %s' % anyOceans, verbose = False)
        pass

    ## Now check the attrs for the ocean grp exist or not...
    debug(None, method = '_buildBaseOceanSetup', message = 'Setting attrs fr OCEAN_hrc now...', verbose = False)
    try:    cmds.setAttr("OCEAN_hrc.overrideEnabled", 1)
    except: pass
    try:    cmds.setAttr("OCEAN_hrc.overrideDisplayType", 2)
    except: pass
    try:    cmds.setAttr("OCEAN_hrc.translateY", lock = True, keyable = False)
    except: pass
    try:    cmds.setAttr("OCEAN_hrc.rotateX", lock = True, keyable = False)
    except: pass
    try:    cmds.setAttr("OCEAN_hrc.rotateY", lock = True, keyable = False)
    except: pass
    try:    cmds.setAttr("OCEAN_hrc.rotateZ", lock = True, keyable = False)
    except: pass
    try:    cmds.setAttr("OCEAN_hrc.scaleX", lock = True, keyable = False)
    except: pass
    try:    cmds.setAttr("OCEAN_hrc.scaleY", lock = True, keyable = False)
    except: pass
    try:    cmds.setAttr("OCEAN_hrc.scaleZ", lock = True, keyable = False)
    except: pass

    ## Now add an attr to OCEAN_hrc to handle the Res of the preview plane
    debug(None, method = '_buildBaseOceanSetup', message = 'Setting attrs fr OCEAN_hrc.oceanRes now...', verbose = False)
    if not cmds.objExists("OCEAN_hrc.oceanRes"):
        cmds.addAttr('OCEAN_hrc', longName =  'oceanRes', attributeType = 'float', min = 0, max = 200, dv = 50)
        cmds.setAttr('OCEAN_hrc.oceanRes', keyable  = True)

    ## Now add an attr to OCEAN_hrc to handle the height of the of the tide to reference later in other scripts
    if not cmds.objExists("OCEAN_hrc.tideHeight"):
        cmds.addAttr('OCEAN_hrc', longName =  'tideHeight', attributeType =  'float', defaultValue = 0)

    ## Now add expression to resolutions note animPlane gets its from the base ocean prev plane...
    expStringList = [
                    "oceanPreviewPlane_heightF.resolution = OCEAN_hrc.oceanRes;\n",
                    ]
    utils.checkExpressionExists('oceanRes_exp')
    cmds.expression(n = 'oceanRes_exp',  string = utils.processExpressionString(expStringList))

    if hiTide:
        cmds.setAttr('OCEAN_hrc.tideHeight', 0)
    else:
        cmds.setAttr('OCEAN_hrc.tideHeight', .321)

    ## Now transfer the publish DISPocean preset from the ocean over to the animation ocean
    debug(None, method = '_buildBaseOceanSetup', message = '_connectAnimToDisp...', verbose = False)
    _connectAnimToDisp()
    print

    debug(None, method = '_buildBaseOceanSetup', message = 'Base Ocean setup complete!', verbose = False)

def buildAnimOcean(editor, ocean_preset_template = '', ocean_foam_template = '', ocean_wake_template = '', hiTide = False):
    """
    Build of the ocean for the Animation Step

    @param editor:                  The current viewport editor so we can use this to stick the ocean in the right location in the shot
    @param ocean_preset_template:   The publish template for publishing ocean preset to.
    @param ocean_foam_template:     The template to find the preset for the ocean foam fluid container
    @param ocean_wake_template:     The template to find the preset for the ocean wake fluid container
    @type editor:                   String
    @type ocean_preset_template:    A valid shotgun tempate
    @type ocean_foam_template:      A valid shotgun tempate
    @type ocean_wake_template:      A valid shotgun tempate
    """
    debug(None, method = 'buildAnimationOcean', message = 'ocean_preset_template: %s' % ocean_preset_template, verbose = False)
    debug(None, method = 'buildAnimationOcean', message = 'ocean_foam_template: %s' % ocean_foam_template, verbose = False)
    debug(None, method = 'buildAnimationOcean', message = 'ocean_wake_template: %s' % ocean_wake_template, verbose = False)
    debug(None, method = 'buildAnimationOcean', message = 'hiTide: %s' % hiTide, verbose = False)

## Do the build
    ## HighTide -0.172
    ##legacy delete
    _buildBaseOceanSetup(editor, ocean_preset_template = ocean_preset_template, ocean_foam_template = ocean_foam_template, ocean_wake_template = ocean_wake_template, hiTide = hiTide)

    ## NOW LINK THE HEIGHT LOCS
    ## Now process all the height locators to be connected to the ocean via their expressions
    connOH.connectAllWithOceanHeightAttr()

    ## Now cleanup the build
    _cleanupOcean()

def buildAnimInteractionOcean(editor, ocean_preset_template = '', ocean_foam_template = '', ocean_wake_template = '', hiTide = False, xRes = 20, zRes = 20, inprogressBar = '', selected = [], interactive = True):
    """
    Used to setup in animation the ocean interaction from one master boat, to which all other boats will interaction with its wakes.
    """
    debug(None, method = 'buildAnimInteractionOcean', message = 'ocean_preset_template: %s' % ocean_preset_template, verbose = False)
    debug(None, method = 'buildAnimInteractionOcean', message = 'ocean_foam_template: %s' % ocean_foam_template, verbose = False)
    debug(None, method = 'buildAnimInteractionOcean', message = 'ocean_wake_template: %s' % ocean_wake_template, verbose = False)
    debug(None, method = 'buildAnimInteractionOcean', message = 'hiTide: %s' % hiTide, verbose = False)

    ## Do the inital build
    _buildBaseOceanSetup(editor, ocean_preset_template = ocean_preset_template, ocean_foam_template = ocean_foam_template, ocean_wake_template = ocean_wake_template, hiTide = hiTide)

    ## Tag the master boat with a new ATTR
    boatAttrName = '%s.%s' %(selected[0], 'interactiveMasterBoat')
    lockName = '%s:oceanLock' % selected[0].split(':')[0]
    lockAttrName = '%s.%s' %(lockName, 'interactiveMasterBoat')

    ## Add tag to boat world_ctrl
    if not cmds.objExists(boatAttrName):
        cmds.addAttr(selected[0], ln = 'interactiveMasterBoat', at = 'bool')
        cmds.setAttr(boatAttrName, keyable = False, channelBox = False)
        cmds.setAttr(boatAttrName, 1)

    ## Add tag to the oceanLock as well for FX scanning
    if not cmds.objExists(lockAttrName):
        cmds.addAttr(lockName, ln = 'interactiveMasterBoat', at = 'bool')
        cmds.setAttr(lockAttrName, keyable = False, channelBox = False)
        cmds.setAttr(lockAttrName, 1)

    ## Now make the shader for the master boat to follow
    _createInteractiveOcean()

    ## BUILD FUILD CONTAINERS NOW
    ## Now build the fluid containers but with unique names for the master boat
    debug(None, method = 'buildFXOcean', message = 'oceanBuilder._build_OceanWakeAndFoam_FluidContainers...', verbose = False)
    inprogressBar.updateProgress(percent = 25, doingWhat = '_build_OceanWakeAndFoam_FluidContainers...')

    _build_OceanWakeAndFoam_FluidContainers(editor              = editor,
                                            ocean_foam_template = ocean_foam_template,
                                            ocean_wake_template = ocean_wake_template,
                                            oceanSHD            = CONST.OCEANANIMSHADER,
                                            wakeFluidShapeName  = CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE,
                                            foamFluidShapeName  = CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE
                                            )
    ### NOW DO THE FLUID EMITTER BUILDS
    inprogressBar.updateProgress(percent = 40, doingWhat = '_setupBaseBoatFXSystems...')
    bfx._setupBaseBoatFXSystems(xRes            = xRes,
                                zRes            = zRes,
                                fluidContainers = [CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE, CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE],
                                inprogressBar   = inprogressBar,
                                selected        = selected,
                                animInteractive = interactive
                                )

    ## Now connect all the new emitters
    inprogressBar.updateProgress(percent = 50, doingWhat = 'Linking all emitters...')
    fluidLib._linkWakeEmitters(fluids       = [CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE, CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE],
                               wakeFluid    = CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE,
                               foamFluid    = CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE
                               )

    ## APPLY PRESETS TO OCEAN TEXTURE PLANES
    ## Now apply the presets to the ocean Textures
    inprogressBar.updateProgress(percent = 60, doingWhat = '_setFXOceanTexurePresets...')
    fluidLib._setFXOceanTexurePresets(fluidShape = 'interactive_oceanWakeTexture', fluidShape2 = 'interactive_oceanWakeFoamTexture')

    ## DELETE CACHES
    fluidLib._deleteOceanTextureCaches(fluidShape = 'interactive_oceanWakeTexture', fluidShape2 = 'interactive_oceanWakeFoamTexture')

    ## Now cleanup the specific stuff..
    try:
        cmds.parent('interactivePreviewPlane_prv', 'OCEAN_hrc')
    except RuntimeError: ## already parented
        pass
    cmds.setAttr('ocean_srf.visibility', 0)
    cmds.setAttr('oceanPreviewPlane_prv.visibility', 0)
    cmds.setAttr('interactivePreviewPlane_prv.visibility', 0)
    cmds.setAttr('animPreviewPlane_prv.visibility', 1)
    cmds.connectAttr('animPreviewPlane_prv.translateX', 'interactivePreviewPlane_prv.translateX', f = True)
    cmds.connectAttr('animPreviewPlane_prv.translateY', 'interactivePreviewPlane_prv.translateY', f = True)
    cmds.connectAttr('animPreviewPlane_prv.translateZ', 'interactivePreviewPlane_prv.translateZ', f = True)

    ## NOW LINK THE HEIGHT LOCS
    connOH.connectAllWithOceanHeightAttr()

    ## Now cleanup the build
    _cleanupOcean()

    ## Connect some of the core attributes from fluid wake/foam/nucleus to global_dynamicAnim group
    connect_fluidTexture3D_to_animatable(foamContainer = CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE, wakeContainer = CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE, animatable = 'global_dynamicAnim')

def buildFXOcean(editor, ocean_preset_template = '', ocean_foam_template = '', ocean_wake_template = '', hiTide = False, xRes = 20, zRes = 20, inprogressBar = '', pathToAnimCaches = ''):
    """
    Build of the ocean for the FX Step. Check the application here for the ocean_preset_template. This should be coming from a
    published animation ocean preset from the DISPOcean in the animation scene.
    Even though we have `opened' the animation scene we are rebuilding the ocean during this step, so the rebuild should match
    the animation publish via the preset.

    @param editor:                     The current viewport editor so we can use this to stick the ocean in the right location in the shot
    @param ocean_preset_template:     The publish template leading us to the ocean preset mel file from animation
    @param ocean_foam_template:     The template to find the preset for the ocean foam fluid container
    @param ocean_wake_template:      The template to find the preset for the ocean wake fluid container
    @type editor:                     String
    @type ocean_preset_template:     A valid shotgun tempate
    @type ocean_foam_template:         A valid shotgun tempate
    @type ocean_wake_template:         A valid shotgun tempate
    """
    [cmds.currentTime(1) for x in range(2)] ## Twice to ensure start position
    debug(None, method = 'buildFXOcean', message = '_buildBaseOceanSetup...', verbose = False)
    inprogressBar.updateProgress(percent = 15, doingWhat = '_buildBaseOceanSetup...')

    ## Look for the master interactive boat
    masterBoatHook = [eachHook for eachHook in cmds.ls(type = 'transform') if cmds.objExists('%s.oceanHeightHook' % eachHook) and cmds.objExists('%s.interactiveMasterBoat' % eachHook)]
    interactiveBoatName = ''

    ## IF there is a masterboat attr in the scene we have an interactive boat setup coming through from animation and need to handle this correctly.
    if masterBoatHook:
        ## First lets find the name of the boat
        interactiveBoatName = masterBoatHook[0].split(':')[0]
        debug(None, method = 'buildFXOcean', message = 'interactiveBoatName: %s' % interactiveBoatName, verbose = False)

        ## Now delete the original animation fx setup so we don't have to calc these again as we're going to use the caches from animation now.
        fluidLib.cleanupMasterBoatFluids(interactiveBoatName)

        ## Now connect the published animation caches from the highest version folder found in the animation publish fx folder.
        if pathToAnimCaches:
            if os.path.isdir(pathToAnimCaches):
                ## Find and create a list of just the xml files
                getCaches = [eachFile for eachFile in os.listdir(pathToAnimCaches) if eachFile.endswith('.xml')]

                for eachCache in getCaches:
                    pathToXML = r'%s/%s' % (pathToAnimCaches, eachCache)
                    ## Now do the attach using the lib to handle fluid caches
                    try:
                        fluidCaches.rebuild_cache_from_xml(pathToXML)
                    except:
                        cmds.warning('Failed to connect cache: %s' % pathToXML)
                        pass

    ############################################################################################################################
    ## BUILD
    _buildBaseOceanSetup(editor, ocean_preset_template = ocean_preset_template, ocean_foam_template = ocean_foam_template, ocean_wake_template = ocean_wake_template, hiTide = hiTide)

    ## BUILD FUILD CONTAINERS NOW
    ## Now build the fluid texture containers for the wakes and foams...
    debug(None, method = 'buildFXOcean', message = '_build_OceanWakeAndFoam_FluidContainers...', verbose = False)
    inprogressBar.updateProgress(percent = 25, doingWhat = '_build_OceanWakeAndFoam_FluidContainers...')
    _build_OceanWakeAndFoam_FluidContainers(editor, ocean_foam_template, ocean_wake_template)

    # ## NOW LINK THE HEIGHT LOCS
    # ## Now process all the height locators again to be connected to the ocean via their expressions
    # debug(None, method = 'buildFXOcean', message = 'connectAllWithOceanHeightAttr...', verbose = False)
    # inprogressBar.updateProgress(percent = 35, doingWhat = 'connectAllWithOceanHeightAttr...')
    # ## Since if interactive, oceanLoc is tagged and baked during ANM publish, we don't want to rebuild and preserve those to have exactly same character movement.
    # if not cmds.objExists(CONST.INTERACTIVE_FOAM_FLUID_SHAPENODE) and not cmds.objExists(CONST.INTERACTIVE_WAKE_FLUID_SHAPENODE):
    #     connOH.connectAllWithOceanHeightAttr()## Note this now factors in the new metatags for the bakeLocs and masterInteractiveBoat!

    ### NOW DO THE FLUID EMITTER BUILDS
    ### This is the new approach for the wakes and foam!
    inprogressBar.updateProgress(percent = 40, doingWhat = '_setupBaseBoatFXSystems...')
    if interactiveBoatName:
        bfx._setupBaseBoatFXSystems(xRes = xRes, zRes = zRes, inprogressBar = inprogressBar, fxInteractive = True, interactiveBoatName = interactiveBoatName)
    else:
        bfx._setupBaseBoatFXSystems(xRes = xRes, zRes = zRes, inprogressBar = inprogressBar)

    ## Now connect all the new emitters
    inprogressBar.updateProgress(percent = 50, doingWhat = 'Linking all emitters...')
    fluidLib._linkWakeEmitters()

    ## APPLY PRESETS TO OCEAN TEXTURE PLANES
    ## Now apply the presets to the ocean Textures
    inprogressBar.updateProgress(percent = 60, doingWhat = '_setFXOceanTexurePresets...')
    fluidLib._setFXOceanTexurePresets()

    ## DELETE CACHES
    fluidLib._deleteOceanTextureCaches()

    ############################################################################################################################
    #
    #
    ############################################################################################################################
    #########################
    ## FX CLEANUP
    ############################################################################################################################
    debug(None, method = 'buildFXOcean', message = '_cleanupOcean...', verbose = False)
    inprogressBar.updateProgress(percent = 65, doingWhat = '_cleanupOcean...')
    _cleanupOcean()

    ## Now turn on all the modelEditors to speed up mayas playback
    cleanup.turnOnModelEditors()

    ## Now remove the fucking expression that maya refuses to evaluate because maya is a dumb shit cunt..
    cmds.delete('oceanRes_exp')

    ## Now set the defaults
    cmds.setAttr('oceanPreviewPlane_heightF.resolution', 100)
    cmds.setAttr ("OCEAN_hrc.oceanRes", 50)
    cmds.setAttr ("OCEAN_hrc.oceanCalcOnOff", 1)
    cmds.setAttr("%s.shadedDisplay" % CONST.FOAM_FLUID_SHAPENODE, 3)
    cmds.setAttr("%s.shadedDisplay" % CONST.WAKE_FLUID_SHAPENODE, 2)
    cmds.setAttr("oceanPreviewPlane_prv.visibility", 0)

    ## NOTE BUG WORK AROUND
    ## The new fluid textures get offset for some obscure reason just resetting these transforms now..
    cmds.setAttr("%s.translateX" % CONST.FOAM_FLUID_SHAPENODE.split('Shape')[0], 0)
    cmds.setAttr("%s.translateX" % CONST.WAKE_FLUID_SHAPENODE.split('Shape')[0], 0)
    cmds.setAttr("%s.translateZ" % CONST.FOAM_FLUID_SHAPENODE.split('Shape')[0], 0)
    cmds.setAttr("%s.translateZ" % CONST.WAKE_FLUID_SHAPENODE.split('Shape')[0], 0)

    try:
        cmds.parent('nPARTICLE_EMITTERS_hrc', 'Shot_FX_hrc')
    except:
        pass
    try:
        cmds.parent('FLUID_EMITTERS_hrc', 'Shot_FX_hrc')
    except:
        pass
    try:
        cmds.parent('nPARTICLE_PARTICLES_hrc', 'Shot_FX_hrc')
    except:
        pass

    ### Setup the nucleus preset now
    pathToPreset = CONST.FXNUCLEUSPRESETPATH

    fx_nucleus = [each for each in cmds.ls(type = 'nucleus') if 'fx_nucleus' in each and cmds.nodeType(each) == 'nucleus']
    if fx_nucleus:
        for each in fx_nucleus:
            mel.eval( 'applyPresetToNode "%s" "" "" "%s" 1;' %(each, pathToPreset) )
        debug(None, method = 'buildFXOcean', message = 'Mel preset applied to %s: %s' % (each, pathToPreset), verbose = False)

    ## Connect some of the core attributes from fluid wake/foam/nucleus to global_dynamicAnim group
    if fx_nucleus:
        connect_fluidTexture3D_to_animatable(foamContainer = CONST.FOAM_FLUID_SHAPENODE, wakeContainer = CONST.WAKE_FLUID_SHAPENODE, nucleus = fx_nucleus[0], animatable = 'global_dynamicAnim')
    else:
        connect_fluidTexture3D_to_animatable(foamContainer = CONST.FOAM_FLUID_SHAPENODE, wakeContainer = CONST.WAKE_FLUID_SHAPENODE, nucleus = '', animatable = 'global_dynamicAnim')

    inprogressBar.updateProgress(percent = 70, doingWhat = 'Cleanup Completed')

def connect_fluidTexture3D_to_animatable(foamContainer = '', wakeContainer = '', nucleus = '', animatable = ''):

    if cmds.objExists(animatable):
        # Nucleus
        if cmds.objExists(nucleus):
            cmds.connectAttr('%s.startFrame' % animatable, '%s.startFrame' % nucleus)
            cmds.connectAttr('%s.gravity' % animatable, '%s.gravity' % nucleus)
            cmds.connectAttr('%s.substeps' % animatable, '%s.subSteps' % nucleus)
            cmds.connectAttr('%s.maxCollisionIterations' % animatable, '%s.maxCollisionIterations' % nucleus)
            cmds.connectAttr('%s.timeScale' % animatable, '%s.timeScale' % nucleus)
            cmds.connectAttr('%s.spaceScale' % animatable, '%s.spaceScale' % nucleus)
        # Foam Container
        if cmds.objExists(foamContainer):
            cmds.connectAttr('%s.foamStartFrame' % animatable, '%s.startFrame' % foamContainer)
            cmds.connectAttr('%s.foamGravity' % animatable, '%s.gravity' % foamContainer)
            cmds.connectAttr('%s.foamViscosity' % animatable, '%s.viscosity' % foamContainer)
            cmds.connectAttr('%s.foamFriction' % animatable, '%s.friction' % foamContainer)
            cmds.connectAttr('%s.foamDamp' % animatable, '%s.velocityDamp' % foamContainer)
        # Wake Container
        if cmds.objExists(wakeContainer):
            cmds.connectAttr('%s.wakeStartFrame' % animatable, '%s.startFrame' % wakeContainer)
            cmds.connectAttr('%s.wakeGravity' % animatable, '%s.gravity' % wakeContainer)
            cmds.connectAttr('%s.wakeViscosity' % animatable, '%s.viscosity' % wakeContainer)
            cmds.connectAttr('%s.wakeFriction' % animatable, '%s.friction' % wakeContainer)
            cmds.connectAttr('%s.wakeDamp' % animatable, '%s.velocityDamp' % wakeContainer)

