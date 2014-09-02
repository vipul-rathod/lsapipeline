import os, getpass, sys
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import time
import maya.cmds as cmds
import maya.api.OpenMaya as om
from xml.etree.ElementTree import ElementTree
import xml.etree.ElementTree as etree
from xml.etree.ElementTree import Element, SubElement, tostring
from debug import debug
from mentalcore import mapi

def checkFilePath(filePath):
    if os.path.exists(filePath):
        return True
    else:
        return False

def writeXML(tree, filePath):
    """
    Function to write out the final xml data
    """
    tree.write(open(r'%s' % filePath, 'w'))

def _getMentalCoreRenderglobals():
    '''
    Recording the MentalCore global settings. 
    '''
    newGlobDic = {}
    globMC = "mentalcoreGlobals"
    AttLists = ['output_mode','file_mode','fb_mem_mode','exr_comp','exr_format','en_colour_management',
                'in_cprofile','out_cprofile','preview_cprofile','unified_sampling','samples_min','samples_max',
                'samples_quality','samples_error_cutoff','samples_per_object','progressive','prog_subsamp_size',
                'prog_subsamp_mode','prog_subsamp_pattern','prog_max_time','prog_min_samples','prog_max_samples',
                'prog_error_threshold','prog_ao_cache','prog_ao_cache_points','prog_ao_cache_rays',
                'prog_ao_cache_max_frame','prog_ao_cache_exclude','en_stereo_rendering','stereo_method',
                'eye_separation','parallax_distance','ibl_mode','ibl_quality','ibl_shadows',
                'ibl_env_res','ibl_env_shader_samples','ibl_env_cache','en_envl','envl_scale','envl_blur',
                'envl_blur_res','envl_en_flood_colour','en_ao','ao_samples',
                'ao_spread','ao_near_clip','ao_far_clip','ao_falloff','ao_amt_amb_occ','ao_amt_direct_occ',
                'indirect_scale','indirect_occlusion','en_bloom','bloom_source','bloom_scale','bloom_threshold',
                'bloom_saturation','en_global_clamp','global_clamp','en_beauty_passes','en_post_passes',
                'en_matte_passes','en_custom_passes','primary_channels','primary_bit_depth','primary_group',
                'output_override','light_relative_scale','trace_camera_motion_vectors',
                'trace_camera_clip','preview_profile_pri_buffer','use_proxy_textures','use_proxy_textures_sec',
                'disable_baked_textures','contrast_all_buffers','ray_differentials','finalgather_legacy',
                'hair_mem_mode','hair_caps','finalgather_importance',
                'ibl_scaleA','ibl_scaleB','ibl_scaleG','ibl_scaleR','detail_shadowmap_contrastA','detail_shadowmap_contrastB',
                'detail_shadowmap_contrastG','detail_shadowmap_contrastR','ao_colourA','ao_colourB','ao_colourG',
                'ao_colourR','envl_flood_colourA','envl_flood_colourB','envl_flood_colourG','envl_flood_colourR']
    
    extraUnknown =['ao_cache_density','ao_cache_points','ao_caching','ao_flag_caustic','ao_flag_finalgather',
                   'ao_flag_globillum','ao_flag_reflect','ao_flag_refract','ao_flag_shadow','ao_flag_transp',
                   'ao_flag_visible','ao_gpu_override_quality','ao_gpu_passes','ao_gpu_rays','ao_inclexcl_id',
                   'ao_mode','ao_nonself_id','ao_opacity','ao_vis_indirect','ao_vis_refl','ao_vis_refr','ao_vis_trans',
                   'binMembership','caching','enable','ibl_approx_split','ibl_approx_split_vis','isHistoricallyInteresting',
                   'light_importance_sampling','light_importance_sampling_precomp','light_importance_sampling_variance',
                   'maya_file_name','maya_file_path','metadata','miFactoryNode','miForwardDefinition','multiple_importance_sampling',
                   'nested_assemblies','nodeState','shutter_efficiency','shutter_shape','version',]
    
    notValid = ['dof_shader','env_shader','geoshader','message','metadata.meta_bool','metadata.meta_enable','metadata.meta_int',
                'metadata.meta_key','metadata.meta_scalar','metadata.meta_string','metadata.meta_type','metadata.meta_vector',
                'metadata.meta_vectorX','metadata.meta_vectorY','metadata.meta_vectorZ','outValue','photographic_shader',
                'preview_composite','preview_pass','renderpasses']
    
    listOfTuple = ['ibl_scale','detail_shadowmap_contrast','ao_colour','envl_flood_colour']
    
    for each in AttLists:
        eachValue = cmds.getAttr("%s.%s"%(globMC,each))
        newGlobDic[each] = eachValue
        #newGlobDic.setdefault(each,eachValue)
        
    return newGlobDic

def _getLensData():
    '''
    Recording the Mental Core Lens Setting
    '''
    newLensDic = {}
    lensMC = "mentalcoreLens"
    lenAttLists = ['lens','affect_env','exposure','saturation','filter_amt', 'en_tonemap','tm_gain',
                   'tm_exposure','tm_blend', 'overlayA','overlayR', 'overlayG', 'overlayB','backgroundR', 
                   'backgroundG', 'backgroundB', 'backgroundA','filter_colB', 'filter_colA','filter_colR', 
                   'filter_colG']
    
    extraUnknown = ['caching', 'isHistoricallyInteresting', 'nodeState', 'binMembership', 'miFactoryNode', 
                    'miForwardDefinition', 'fe_distortion', 'fe_mask', 'ovr_colprofile', 
                    'bg_colprofile', 'outValue', 'outValueR', 'outValueG','outValueB', 'outValueA']
    
    listOfTuple = ['overlay','background','filter_col']
    
    for each in lenAttLists:
        eachValue = cmds.getAttr("%s.%s"%(lensMC,each))
        newLensDic[each] = eachValue
        #newLensDic.setdefault(each, eachValue)
    return newLensDic

def _getMCPasses():
    '''
    recording the Mental Core passes in the scene
    return sceneDictionary {[PASS NAME]: 
                                        [PASS TYPE]
                                        [PASS CONNECTED]
                                        {[NAME OF SETTING]:
                                                            [VALUE]}
                                        [PASS WITHOUT VALUE]}
    '''
    sceneDictionary = {}
    allPasssInScene = mapi.get_all_passes()
    for eachPass in allPasssInScene:
        passType = cmds.getAttr('%s.type' % eachPass) #Getting the type
        
        allTransforms = cmds.ls(type="transform")
        allGeos = cmds.ls(type="mesh")
        totalItems = allTransforms + allGeos
        validTs = []
        for eachT in totalItems:
            listAttrT = cmds.listConnections(eachT)
            if listAttrT != None:
                if eachPass in listAttrT:
                    validTs.append(eachT) #Getting the Assets
        
        passAttrs = cmds.listAttr(eachPass) 
        passSettingDictionary = {}
        failValue = []
        for eachAttr in passAttrs:
            try:
                passValue = cmds.getAttr("%s.%s"%(eachPass,eachAttr))
                passSettingDictionary[eachAttr] = passValue #Getting the pass's list of setting
            except:
                failValue.append(eachAttr) 
        sceneDictionary[eachPass] = [passType,validTs,passSettingDictionary,failValue]
    return sceneDictionary

def _getLayersPasses():
    '''
    Recording the layers, assosiated mental core passes and Objects that are connected to.
    return layersDictionary {[LAYER NAME]:
                                            [ASSOSIATED PASSES]
                                            [PASS CONNECTED]}
    '''
    listOfLayers = cmds.ls(type="renderLayer")
    layersDictionary = {}
    for eachlayer in listOfLayers:
        allAssosiatedPasses = mapi.get_associated_passes(eachlayer) #List of Assosiated Passes
        
        itemInsideLayer = cmds.editRenderLayerMembers(eachlayer,fullNames=True, q=True) #List of Items
        validItems = []
        if itemInsideLayer != None:
            for eachItem in itemInsideLayer:
                listAttrItem = cmds.listConnections(eachItem)
                if listAttrItem != None:
                    validItems.append(eachItem)
#                     for eachAPass in allAssosiatedPasses:
#                         if eachAPass in listAttrItem:
#                             validItems.append(eachItem)
                    
        layersDictionary[eachlayer] = [allAssosiatedPasses,validItems]
    return layersDictionary
        
def _getimDefaultOptions():
    '''
    Recording all the Render Setting
    '''
    miDic = {}
    renderDefaultOptions = "miDefaultOptions"
    validList = ['rayTracing','maxReflectionRays','maxRefractionRays','maxRayDepth','maxShadowRayDepth',
                'scanline','rapidSamplesCollect','rapidSamplesMotion','rapidSamplesShading','faces',
                'shadowMethod','shadowMaps','traceShadowMaps','windowShadowMaps','motionBlurShadowMaps',
                'rebuildShadowMaps','motionBlur','motionBlurBy','shutter','shutterDelay','timeContrastR',
                'timeContrastG','timeContrastB','timeContrastA','motionSteps','caustics','causticFilterType',
                'causticFilterKernel','causticAccuracy','causticRadius','globalIllum',
                'globalIllumAccuracy','globalIllumRadius','maxReflectionPhotons',
                'maxRefractionPhotons','maxPhotonDepth','photonVolumeAccuracy','photonVolumeRadius',
                'photonAutoVolume','photonMapRebuild','photonMapFilename','photonMapVisualizer','finalGather',
                'finalGatherFast','finalGatherRays','finalGatherMinRadius','finalGatherMaxRadius',
                'finalGatherView','finalGatherTraceDiffuse','finalGatherTraceReflection',
                'finalGatherTraceRefraction','finalGatherTraceDepth','finalGatherFalloffStart',
                'finalGatherFalloffStop','finalGatherFilter','finalGatherRebuild','finalGatherFilename',
                'finalGatherMapVisualizer','contrastR','contrastG','contrastB','contrastA','minSamples',
                'maxSamples','sampleLock','jitter','filter','filterWidth','filterHeight','minObjectSamples',
                'maxObjectSamples','volumeSamples','diagnoseSamples','diagnoseGrid','diagnoseGridSize',
                'diagnosePhoton','diagnosePhotonDensity','diagnoseBsp','diagnoseFinalg','lensShaders',
                'volumeShaders','geometryShaders','displacementShaders','outputShaders','autoVolume',
                'displacePresample','mergeSurfaces','renderHair','renderPasses','maxDisplace','causticsGenerating',
                'causticsReceiving','globalIllumGenerating','globalIllumReceiving','contourBackground',
                'enableContourColor','contourPriIdx','contourInstance','contourMaterial',
                'contourLabel','enableContourDist','contourDist','enableContourDepth','contourDepth',
                'enableContourNormal','contourNormal','contourNormalGeom','contourInvNormal','enableContourTexUV',
                'contourTexU','contourTexV','caching','nodeState','maxReflectionBlur','maxRefractionBlur',
                'allocateOnHeap','forceMotionVectors','causticAutoRadius','causticScaleA','causticMerge',
                'photonVolumeAutoRadius','photonVolumeScaleA','photonVolumeMerge',
                'photonDepthAuto','globalIllumAutoRadius','globalIllumScaleA','globalIllumMerge','finalGatherMode',
                'finalGatherAutoRadius','finalGatherPoints','finalGatherScaleA','finalGatherPresampleDensity',
                'finalGatherBounceScaleA','finalGatherImportance','finalGatherContrastA',
                'lightMaps','lightmapRender','userFrameBuffer0Mode',
                'userFrameBuffer0Type','userFrameBuffer1Mode','userFrameBuffer1Type','userFrameBuffer2Mode',
                'userFrameBuffer2Type','userFrameBuffer3Mode','userFrameBuffer3Type','userFrameBuffer4Mode',
                'userFrameBuffer4Type','userFrameBuffer5Mode','userFrameBuffer5Type','userFrameBuffer6Mode',
                'userFrameBuffer6Type','userFrameBuffer7Mode','userFrameBuffer7Type','contourPriData','description',
                
                'luminanceB','luminanceG','luminanceR','causticScaleB','causticScaleG','causticScaleR','contourColorB',
                'contourColorG','contourColorR','finalGatherContrastB','finalGatherContrastG','finalGatherContrastR',
                'photonVolumeScaleB','photonVolumeScaleG','photonVolumeScaleR','globalIllumScaleB','globalIllumScaleG',
                'globalIllumScaleR','finalGatherScaleB','finalGatherScaleG','finalGatherScaleR',
                'finalGatherBounceScaleB','finalGatherBounceScaleG','finalGatherBounceScaleR']
    
    extraUnknown = ['binMembership','contourTex','hardware','hardwareCg','hardwareFast','hardwareForce',
                    'hardwareGL','isHistoricallyInteresting','lightMapsNetwork','userFrameBuffer0',
                    'userFrameBuffer1','userFrameBuffer2','userFrameBuffer3','userFrameBuffer4',
                    'userFrameBuffer5','userFrameBuffer6','userFrameBuffer7']
    
    listOfTuple = ['luminance','causticScale','contourColor','finalGatherContrast','photonVolumeScale','globalIllumScale',
                   'finalGatherScale','finalGatherBounceScale']
    
    for eachAttr in validList:
        eachValue = cmds.getAttr("%s.%s"%(renderDefaultOptions,eachAttr))
        miDic[eachAttr] = eachValue
    
    return miDic

def _getMentalrayGlobals():
    '''
    recording the Mental ray Global setting
    '''
    mentalrayDic = {}
    mentalrayGlobal = "mentalrayGlobals"
    validList = ['renderMode','renderVerbosity','inheritVerbosity','exportMessages','shadowsObeyLightLinking',
                'shadowsObeyShadowLinking','shadowEffectsWithPhotons','renderShadersWithFiltering',
                'useLegacyShaders','jobLimitPhysicalMemory','accelerationMethod','bspSize','bspDepth',
                'bspShadow','taskSize','exportVerbosity','exportExactHierarchy','exportFullDagpath',
                'exportTexturesFirst','exportParticles','exportParticleInstances','exportFluids',
                'exportHair','exportPostEffects','exportVertexColors','exportAssignedOnly','exportVisibleOnly',
                'optimizeAnimateDetection','exportSharedVertices','exportAssembly','exportShapeDeformation',
                'exportMotionSegments','exportTriangles','exportPolygonDerivatives','mayaDerivatives',
                'smoothPolygonDerivatives','exportNurbsDerivatives','exportObjectsOnDemand','exportPlaceholderSize',
                'exportStateShader','exportLightLinker','exportMayaOptions','exportCustomColors','exportCustom',
                'exportCustomData','exportCustomVectors','exportCustomMotion','exportMotionOutput',
                'exportMotionOffset','exportAssignedOnly','previewAnimation','previewFinalGatherTiles',
                'previewMotionBlur','previewRenderTiles','previewConvertTiles','previewTonemapTiles',
                'tonemapRangeHigh','passAlphaThrough','passDepthThrough','passLabelThrough','versions',
                'links','includes','preRenderMel','postRenderMel','caching','nodeState','renderThreads',
                'memoryAuto','memoryZone','frameBufferMode','gridAuto','exportIgnoreErrors','exportShadowLinker',
                'exportInstanceLights','exportInstanceShadows','optimizeVisibleDetection','exportMotionCamera']
    for eachAttr in validList:
        eachValue = cmds.getAttr("%s.%s"%(mentalrayGlobal,eachAttr))
        mentalrayDic[eachAttr] = eachValue
    
    return mentalrayDic

def writeRenderGlobalData(pathToXML = '', print4Me = 0):
    """
    Function to write out renderglobals
    """
    debug(app = None, method = 'renderGlobals_writeXML.writeRenderGlobalData', message = 'pathToXML: %s' % pathToXML, verbose = False)
    
    ## now process the data into the xml tree      
    root        = Element('RenderGlobals')
    tree        = ElementTree(root)
      
    mcglobalsdata   = _getMentalCoreRenderglobals()
    mclensdata      = _getLensData()
    mayaRenderLayers= _getLayersPasses()
    mcScenePasses   = _getMCPasses()
    imDefOptions    = _getimDefaultOptions()
    mentalrayData   = _getMentalrayGlobals()
    debug(app = None, method = 'renderGlobals_writeXML.writeRenderGlobalData', message = 'data: %s' % mcglobalsdata, verbose = False)
    
    mcglobals     = Element('mentalcoreGlobals')
    root.append(mcglobals)
    
    mclensD     = Element('mentalcoreLens')
    root.append(mclensD)
    
    mentalrayGlobals = Element('mentalrayGlobals')
    root.append(mentalrayGlobals)
    
    renderIMDO       = Element('miDefaultOptions')
    root.append(renderIMDO)
    
    mcPassesData     = Element('renderLayers')
    root.append(mcPassesData)

    MCScenePasses    = Element('MentalCorePasses')
    root.append(MCScenePasses)

    for renderGlobal, globalAttr in mcglobalsdata.items():
        group = SubElement(mcglobals,  str(renderGlobal), value = str(globalAttr))

    for lensAttr, lensData in mclensdata.items():
        group = SubElement(mclensD,  str(lensAttr), value = str(lensData))
        
    for eachAttr, eachValue in mentalrayData.items():
        group = SubElement(mentalrayGlobals,  str(eachAttr), value = str(eachValue))
    
    for imAttr, imAttrValue in imDefOptions.items():
        group = SubElement(renderIMDO,  str(imAttr), value = str(imAttrValue))
    
    for layerName , LayerData in mayaRenderLayers.items():
        myRenderLayerName = SubElement(mcPassesData, str(layerName))
        mcAssociatedPass = SubElement(myRenderLayerName, 'associatedPasses', value = str(LayerData[0]).split('[')[-1].split(']')[0].replace(',', '_iCommai_'))
        renderlayer = SubElement(myRenderLayerName,  'associatedObjects', value = str(LayerData[1]).split('[')[-1].split(']')[0].replace(',', '_iCommai_'))
    
    for eachPassMC , eachDataMC in mcScenePasses.items():
        passName = SubElement(MCScenePasses, str(eachPassMC))
        passType = SubElement(passName, 'passType', value = str(eachDataMC[0]).split('[')[-1].split(']')[0].replace(',', '_iCommai_'))
        passObj = SubElement(passName, 'passConnected', value = str(eachDataMC[1]).split('[')[-1].split(']')[0].replace(',', '_iCommai_'))
        passSetting = SubElement(passName, 'passSetting')
        for eachSetting, eachValue in eachDataMC[2].items():
            passValue = SubElement(passSetting, str(eachSetting), value = str(eachValue).split('[')[-1].split(']')[0].replace(',', '_iCommai_'))
        failedPasses = SubElement(passName, 'notInclude', value = str(eachDataMC[3]).split('[')[-1].split(']')[0].replace(',', '_iCommai_'))
        #sceneDictionary[eachPass] = [passType,validTs,passSettingDictionary,failValue]
        
    tree.write(open(pathToXML, 'w'), encoding="utf-8")
    
    if "1" in  str(print4Me):
        print "This is MentalCore Globals:"
        for key, val in mcglobalsdata.iteritems():
            print "%s:%s"%(key,val)
                    
    if "2" in str(print4Me):
        print "This is MentalCore Lense:"
        for key, val in mclensdata.iteritems():
            print "%s:%s"%(key,val)
                    
    if "3" in str(print4Me):
        print "This is MentalRay Data:"
        for key, val in mentalrayData.iteritems():
            print "%s:%s"%(key,val)
                    
    if "4" in  str(print4Me):
        print "This is imDefaultOption:"
        for key, val in imDefOptions.iteritems():
            print "%s:%s"%(key,val)
                    
    if "5" in  str(print4Me):
        print "This is Layer:"
        for key, val in mayaRenderLayers.iteritems():
            print "%s:" %key
            for eachVal in val:
                if type(eachVal) == dict:
                    for childKey, childVal in eachVal.iteritems():
                        print "%s: %s" %(childKey,childVal)
                else:
                    print eachVal
                    
    if "6" in str(print4Me):
        print "This is MentalCore Passes:"
        for key, val in mcScenePasses.iteritems():
            print "%s:" %key
            for eachVal in val:
                if type(eachVal) == dict:
                    for childKey, childVal in eachVal.iteritems():
                        print "%s: %s" %(childKey,childVal)
                else:
                    print eachVal
                     
    
    ## Mentalcore tracks its passes to the render layers, each of MC passes can have different links to mattes etc that need to be stored
    ## the renderlayers themselves will also have objects attached to them that need to be stored.