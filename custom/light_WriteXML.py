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
    
def _RecordLightSetting():
    '''
    lightSettingDict {[LIGHT NAME]:
                            [SETTING NAME]:
                                    [VALUE]}
    '''
    areaLightAttribs = ['smapCameraName', 'emitDiffuse', 'areaVisible', 'writeDmap', 'useObjectColor', 'useDmapAutoClipping', 'areaLight', 'overrideEnabled',
                   'smapSceneName', 'uvFilterSizeY', 'uvFilterSizeX', 'lightShadowFraction', 'colorB', 'ghostPostSteps', 'pointWorldY', 'pointWorldX', 'rayDepth', 
                   'smapDetailSamples', 'binMembership', 'colorR', 'locatorScale', 'customTreatment', 'reuseDmap', 'useZ-Dmap', 'emitSpecular', 'smapFrameExt', 
                   'useOnlySingleDmap', 'dmapFrameExt', 'ghostColorPostG', 'ghostColorPostB', 'ghostColorPostA', 'smapCameraAperture', 'useDmapAutoFocus', 'creationDate', 
                   'ghostColorPostR', 'templatePath', 'overrideShading', 'useDepthMapShadows', 'receiveShadows', 'overrideTexturing', 'smapDetailAlpha', 'lightIntensityB', 
                   'lightDiffuse', 'areaHiSamples', 'smapWindowXMax', 'lightIntensityR', 'objectColor', 'decayRate', 'shadColorB', 'boundingBoxMinX', 'boundingBoxMinY', 
                   'boundingBoxMinZ', 'creator', 'ghostRangeEnd', 'lightIntensityG', 'shadColorR', 'intensity', 'miExportMrLight', 'vCoord', 'areaLoSamples', 
                   'templateVersion', 'lightBlindData', 'pointCameraY', 'pointCameraX', 'overridePlayback', 'dmapWidthFocus', 'renderState', 'infoBits', 'identification', 
                   'dmapNearClipPlane', 'template', 'containerType', 'smapWindowYMin', 'normalCameraY', 'viewName', 'useZ+Dmap', 'primitiveId', 'causticPhotonsEmit', 
                   'overrideColor', 'normalCameraZ', 'dmapSceneName', 'rmbCommand', 'useMidDistDmap', 'smapCameraFocal', 'rayInstance', 
                   'boundingBoxCenterX', 'boundingBoxCenterY', 'energyG', 'colorG', 'objectId', 'centerOfIllumination', 'energyR', 'smapTrace', 'emitPhotons', 
                   'ghostRangeStart', 'areaHiSampleLimit', 'pointWorldZ', 'rayDepthLimit', 'raySampler', 'dmapLightName', 'dmapName', 'smapSoftness', 'dmapFarClipPlane', 
                   'overrideLevelOfDetail', 'shadColorG', 'photonIntensity', 'ghosting', 'shadowRays', 'smapWindowXMin', 'objectType', 'isHistoricallyInteresting', 
                   'normalCameraX', 'useX-Dmap', 'useY-Dmap', 'dmapFilterSize', 'useRayTraceShadows', 'fogShadowIntensity', 'useY+Dmap', 'useShadowMapCamera', 
                   'boundingBoxCenterZ', 'preShadowIntensity', 'dmapResolution', 'energyB', 'smapCameraAspect', 'visibility', 'smapCameraResolution', 'layerOverrideColor', 
                   'smapBias', 'uiTreatment', 'areaShapeIntensity', 'opticalFXvisibilityG', 'opticalFXvisibilityB', 'lightRadius', 'smapWindowYMax', 'smapDetail', 
                   'castSoftShadows', 'opticalFXvisibilityR', 'boundingBoxSizeX', 'boundingBoxSizeY', 'boundingBoxSizeZ', 'ghostPreSteps', 'shadowMap', 'objectColorR', 
                   'areaType', 'lightDirectionZ', 'useX+Dmap', 'lightDirectionX', 'lightDirectionY', 'objectColorB', 'objectColorG', 'isCollapsed', 'globIllPhotonsEmit', 
                   'blackBox', 'templateName', 'lightAmbient', 'ghostingControl', 'smapDetailAccuracy', 'lightSpecular', 'smapSamples', 'smapMerge', 'boundingBoxMaxZ', 
                   'overrideDisplayType', 'boundingBoxMaxX', 'boundingBoxMaxY', 'nodeState', 'overrideVisibility', 'ghostColorPreA', 'ghostColorPreB', 'ghostColorPreG', 
                   'layerRenderable', 'pointCameraZ', 'lodVisibility', 'uCoord', 'ghostColorPreR', 'exponent', 'volumeShadowSamples', 'smapFilename', 
                   'smapLightName', 'dmapFocus', 'ghostStepSize', 'viewMode', 'causticPhotons', 'dmapBias', 'caching', 'smapResolution', 'globIllPhotons'
                   ,'instObjGroups']
    
    volumeLightAttribs = ['smapCameraName', 'emitDiffuse', 'areaVisible', 'writeDmap', 'fogIntensity', 'useObjectColor', 'farPointWorldY', 
                          'farPointWorldX', 'useDmapAutoClipping', 'areaLight', 'areaLowLevel', 'overrideEnabled', 'smapSceneName', 'farPointWorldZ', 'uvFilterSizeY', 
                          'uvFilterSizeX', 'lightShadowFraction', 'colorB', 'ghostPostSteps', 'pointWorldY', 'pointWorldX', 'rayDepth', 'smapDetailSamples', 'fogType', 
                          'binMembership', 'colorR', 'locatorScale', 'customTreatment', 'reuseDmap', 'useZ-Dmap', 'emitSpecular', 'smapFrameExt', 'useOnlySingleDmap', 
                          'dmapFrameExt', 'ghostColorPostG', 'ghostColorPostB', 'ghostColorPostA', 'areaNormalX', 'smapCameraAperture', 'useDmapAutoFocus', 'creationDate', 
                          'ghostColorPostR', 'templatePath', 'overrideShading', 'useDepthMapShadows', 'receiveShadows', 'overrideTexturing', 'areaLowSamplingV', 
                          'smapDetailAlpha', 'lightIntensityB', 'lightDiffuse', 'lightIntensityR', 'objectColor', 'areaSamplingU', 'areaEdgeX', 'decayRate', 'shadColorB', 
                          'boundingBoxMinX', 'boundingBoxMinY', 'boundingBoxMinZ', 'creator', 'areaLowSamplingU', 'ghostRangeEnd', 'lightIntensityG', 'shadColorR', 
                          'intensity', 'arc', 'emitAmbient', 'miExportMrLight', 'vCoord', 'templateVersion', 'lightBlindData', 'pointCameraY', 'pointCameraX', 
                          'overridePlayback', 'dmapWidthFocus', 'renderState', 'infoBits', 'identification', 'dmapNearClipPlane', 'template', 'containerType', 
                          'viewName', 'useZ+Dmap', 'fogRadius', 'primitiveId', 'overrideColor', 'areaType', 'dmapSceneName', 'rmbCommand', 'useMidDistDmap', 
                          'smapCameraFocal', 'rayInstance', 'boundingBoxCenterX', 'boundingBoxCenterY', 'energyG', 'colorG', 'objectId', 
                          'centerOfIllumination', 'energyR', 'emitPhotons', 'ghostRangeStart', 'pointWorldZ', 'rayDepthLimit', 'raySampler', 'dmapLightName', 'dmapName', 
                          'smapSoftness', 'dmapFarClipPlane', 'overrideLevelOfDetail', 'shadColorG', 'photonIntensity', 'ghosting', 'shadowRays', 'objectType', 
                          'isHistoricallyInteresting', 'useX-Dmap', 'useY-Dmap', 'dmapFilterSize', 'useRayTraceShadows', 'fogShadowIntensity', 'useY+Dmap', 
                          'useShadowMapCamera', 'areaEdgeY', 'boundingBoxCenterZ', 'areaEdgeZ', 'preShadowIntensity', 'dmapResolution', 'energyB', 'smapCameraAspect', 
                          'visibility', 'smapCameraResolution', 'layerOverrideColor', 'smapBias', 'areaSamplingV', 'uiTreatment', 'opticalFXvisibilityG', 
                          'opticalFXvisibilityB', 'lightRadius', 'coneEndRadius', 'smapDetail', 'castSoftShadows', 'opticalFXvisibilityR', 
                          'boundingBoxSizeX', 'boundingBoxSizeY', 'boundingBoxSizeZ', 'ghostPreSteps', 'shadowMap', 'objectColorR', 'lightDirectionZ', 'useX+Dmap', 
                          'lightDirectionX', 'lightDirectionY', 'objectColorB', 'objectColorG', 'isCollapsed', 'blackBox', 'templateName', 'lightAmbient', 
                          'ghostingControl', 'smapDetailAccuracy', 'lightSpecular', 'smapSamples', 'boundingBoxMaxZ', 'overrideDisplayType', 'boundingBoxMaxX', 
                          'boundingBoxMaxY', 'areaNormalY', 'volumeLightDir', 'nodeState', 'overrideVisibility', 'ghostColorPreA', 'ghostColorPreB', 'ghostColorPreG', 
                          'layerRenderable', 'pointCameraZ', 'lodVisibility', 'uCoord', 'ghostColorPreR', 'exponent', 'volumeShadowSamples', 'smapFilename', 'areaNormalZ', 
                           'smapLightName', 'areaRadius', 'lightAngle', 'dmapFocus', 'ghostStepSize', 'viewMode', 'causticPhotons', 'dmapBias', 
                          'lightShape', 'caching', 'smapResolution', 'globIllPhotons', 'instObjGroups']
    
    pointLight = ['smapCameraName', 'emitDiffuse', 'areaVisible', 'writeDmap', 'fogIntensity', 'useObjectColor', 'farPointWorldY', 'farPointWorldX', 
                  'useDmapAutoClipping', 'areaLight', 'areaLowLevel', 'overrideEnabled', 'smapSceneName', 'farPointWorldZ', 'uvFilterSizeY', 'uvFilterSizeX', 
                  'lightShadowFraction', 'colorB', 'ghostPostSteps', 'pointWorldY', 'pointWorldX', 'rayDepth', 'smapDetailSamples', 'fogType', 'binMembership', 'colorR', 
                  'locatorScale', 'customTreatment', 'reuseDmap', 'useZ-Dmap', 'emitSpecular', 'smapFrameExt', 'useOnlySingleDmap', 'dmapFrameExt', 'ghostColorPostG', 
                  'ghostColorPostB', 'ghostColorPostA', 'areaNormalX', 'smapCameraAperture', 'useDmapAutoFocus', 'creationDate', 'ghostColorPostR', 'templatePath', 
                  'overrideShading', 'useDepthMapShadows', 'receiveShadows', 'overrideTexturing', 'areaLowSamplingV', 'smapDetailAlpha', 'lightIntensityB', 'lightDiffuse', 
                  'lightIntensityR', 'objectColor', 'areaSamplingU', 'areaEdgeX', 'decayRate', 'shadColorB', 'boundingBoxMinX', 'boundingBoxMinY', 'boundingBoxMinZ', 
                  'creator', 'areaLowSamplingU', 'ghostRangeEnd', 'lightIntensityG', 'shadColorR', 'intensity', 'miExportMrLight', 'vCoord', 'templateVersion', 
                  'lightBlindData', 'pointCameraY', 'pointCameraX', 'overridePlayback', 'dmapWidthFocus', 'renderState', 'infoBits', 'identification', 'dmapNearClipPlane', 
                  'template', 'containerType', 'viewName', 'useZ+Dmap', 'fogRadius', 'primitiveId', 'overrideColor', 'areaType', 'dmapSceneName', 'rmbCommand', 
                  'useMidDistDmap', 'smapCameraFocal', 'rayInstance', 'boundingBoxCenterX', 'boundingBoxCenterY', 'energyG', 'colorG', 'objectId', 
                  'centerOfIllumination', 'energyR', 'emitPhotons', 'ghostRangeStart', 'pointWorldZ', 'rayDepthLimit', 'raySampler', 'dmapLightName', 'dmapName', 
                  'smapSoftness', 'dmapFarClipPlane', 'overrideLevelOfDetail', 'shadColorG', 'photonIntensity', 'ghosting', 'shadowRays', 'objectType', 
                  'isHistoricallyInteresting', 'useX-Dmap', 'useY-Dmap', 'dmapFilterSize', 'useRayTraceShadows', 'fogShadowIntensity', 'useY+Dmap', 'useShadowMapCamera', 
                  'areaEdgeY', 'boundingBoxCenterZ', 'areaEdgeZ', 'preShadowIntensity', 'dmapResolution', 'energyB', 'smapCameraAspect', 'visibility', 
                  'smapCameraResolution', 'layerOverrideColor', 'smapBias', 'areaSamplingV', 'uiTreatment', 'opticalFXvisibilityG', 'opticalFXvisibilityB', 'lightRadius', 
                  'smapDetail', 'castSoftShadows', 'opticalFXvisibilityR', 'boundingBoxSizeX', 'boundingBoxSizeY', 'boundingBoxSizeZ', 'ghostPreSteps', 
                  'shadowMap', 'objectColorR', 'lightDirectionZ', 'useX+Dmap', 'lightDirectionX', 'lightDirectionY', 'objectColorB', 'objectColorG', 'isCollapsed', 
                  'blackBox', 'templateName', 'lightAmbient', 'ghostingControl', 'smapDetailAccuracy', 'lightSpecular', 'smapSamples', 'boundingBoxMaxZ', 
                  'overrideDisplayType', 'boundingBoxMaxX', 'boundingBoxMaxY', 'areaNormalY', 'nodeState', 'overrideVisibility', 'ghostColorPreA', 'ghostColorPreB', 
                  'ghostColorPreG', 'layerRenderable', 'pointCameraZ', 'lodVisibility', 'uCoord', 'ghostColorPreR', 'exponent', 'volumeShadowSamples', 'smapFilename', 
                  'areaNormalZ', 'smapLightName', 'areaRadius', 'dmapFocus', 'ghostStepSize', 'viewMode', 'causticPhotons', 'dmapBias', 'caching', 
                  'smapResolution', 'globIllPhotons', 'instObjGroups']
    
    directionalLight = ['smapCameraName', 'emitDiffuse', 'writeDmap', 'useObjectColor', 'useDmapAutoClipping', 'overrideEnabled', 'smapSceneName', 
                        'uvFilterSizeY', 'uvFilterSizeX', 'lightShadowFraction', 'colorB', 'ghostPostSteps', 'pointWorldY', 'pointWorldX', 'rayDepth', 'smapDetailSamples', 
                        'binMembership', 'colorR', 'locatorScale', 'customTreatment', 'reuseDmap', 'useZ-Dmap', 'emitSpecular', 'smapFrameExt', 
                        'useOnlySingleDmap', 'dmapFrameExt', 'ghostColorPostG', 'ghostColorPostB', 'ghostColorPostA', 'smapCameraAperture', 
                        'useDmapAutoFocus', 'creationDate', 'ghostColorPostR', 'templatePath', 'overrideShading', 'useDepthMapShadows', 'receiveShadows', 
                        'overrideTexturing', 'smapDetailAlpha', 'lightIntensityB', 'lightDiffuse', 'useLightPosition', 'lightIntensityR', 'objectColor', 'decayRate', 
                        'shadColorB', 'boundingBoxMinX', 'boundingBoxMinY', 'boundingBoxMinZ', 'creator', 'ghostRangeEnd', 'lightIntensityG', 'shadColorR', 'intensity', 
                        'miExportMrLight', 'vCoord', 'templateVersion', 'lightBlindData', 'pointCameraY', 'pointCameraX', 'overridePlayback', 'dmapWidthFocus', 
                        'renderState', 'infoBits', 'identification', 'dmapNearClipPlane', 'template', 'containerType', 'viewName', 'useZ+Dmap', 
                        'primitiveId', 'overrideColor', 'dmapSceneName', 'rmbCommand', 'useMidDistDmap', 'smapCameraFocal', 'rayInstance', 
                        'boundingBoxCenterX', 'boundingBoxCenterY', 'energyG', 'colorG', 'objectId', 'centerOfIllumination', 'energyR', 'emitPhotons', 'ghostRangeStart', 
                        'pointWorldZ', 'rayDepthLimit', 'raySampler', 'dmapLightName', 'dmapName', 'smapSoftness', 'dmapFarClipPlane', 'overrideLevelOfDetail', 'shadColorG', 
                        'photonIntensity', 'ghosting', 'shadowRays', 'objectType', 'isHistoricallyInteresting', 'useX-Dmap', 'useY-Dmap', 'dmapFilterSize', 
                        'useRayTraceShadows', 'fogShadowIntensity', 'useY+Dmap', 'useShadowMapCamera', 'boundingBoxCenterZ', 'preShadowIntensity', 'dmapResolution', 
                        'energyB', 'smapCameraAspect', 'visibility', 'smapCameraResolution', 'layerOverrideColor', 'smapBias', 'lightAngle', 'uiTreatment', 
                        'opticalFXvisibilityG', 'opticalFXvisibilityB', 'lightRadius', 'smapDetail', 'castSoftShadows', 'opticalFXvisibilityR', 'boundingBoxSizeX', 
                        'boundingBoxSizeY', 'boundingBoxSizeZ', 'ghostPreSteps', 'shadowMap', 'objectColorR', 'lightDirectionZ', 'useX+Dmap', 'lightDirectionX', 
                        'lightDirectionY', 'objectColorB', 'objectColorG', 'isCollapsed', 'blackBox', 'templateName', 'lightAmbient', 
                        'ghostingControl', 'smapDetailAccuracy', 'lightSpecular', 'smapSamples', 'boundingBoxMaxZ', 'overrideDisplayType', 'boundingBoxMaxX', 
                        'boundingBoxMaxY', 'nodeState', 'overrideVisibility', 'ghostColorPreA', 'ghostColorPreB', 'ghostColorPreG', 'dmapUseMacro', 'layerRenderable', 
                        'pointCameraZ', 'lodVisibility', 'uCoord', 'ghostColorPreR', 'exponent', 'volumeShadowSamples', 'smapFilename', 'smapLightName', 
                        'dmapFocus', 'ghostStepSize', 'viewMode', 'causticPhotons', 'dmapBias', 'caching', 'smapResolution', 'globIllPhotons', 'instObjGroups']
    
    ambientLight = ['intermediateObject', 'useObjectColor', 'overrideEnabled', 'uvFilterSizeY', 'uvFilterSizeX', 'lightShadowFraction', 'colorB', 'ghostPostSteps', 
                    'rayDepth', 'binMembership', 'colorR', 'locatorScale', 'customTreatment', 'ghostColorPostG', 'ghostColorPostB', 'ghostColorPostA', 'creationDate', 
                    'ghostColorPostR', 'templatePath', 'overrideShading', 'receiveShadows', 'overrideTexturing', 'lightIntensityB', 'lightDiffuse', 'lightIntensityR', 
                    'objectColor', 'shadColorB', 'boundingBoxMinX', 'boundingBoxMinY', 'boundingBoxMinZ', 'creator', 'ghostRangeEnd', 'lightIntensityG', 'shadColorR', 
                    'intensity', 'vCoord', 'templateVersion', 'lightBlindData', 'pointCameraY', 'pointCameraX', 'overridePlayback', 'renderState', 'infoBits', 
                    'identification', 'template', 'containerType', 'normalCameraY', 'viewName', 'primitiveId', 'overrideColor', 'rmbCommand', 'rayInstance', 
                    'boundingBoxCenterX', 'boundingBoxCenterY', 'colorG', 'objectId', 'centerOfIllumination', 'ghostRangeStart', 'rayDepthLimit', 'raySampler', 
                    'overrideLevelOfDetail', 'shadColorG', 'ghosting', 'shadowRays', 'objectType', 'isHistoricallyInteresting', 'normalCameraX', 'normalCameraZ', 
                    'useRayTraceShadows', 'shadowRadius', 'boundingBoxCenterZ', 'preShadowIntensity', 'visibility', 'layerOverrideColor', 'uiTreatment', 
                    'opticalFXvisibilityG', 'opticalFXvisibilityB', 'ambientShade', 'castSoftShadows', 'opticalFXvisibilityR', 'boundingBoxSizeX', 'boundingBoxSizeY', 
                    'boundingBoxSizeZ', 'ghostPreSteps', 'objectColorR', 'lightDirectionZ', 'lightDirectionX', 'lightDirectionY', 'objectColorB', 'objectColorG', 
                    'isCollapsed', 'blackBox', 'templateName', 'lightAmbient', 'ghostingControl', 'lightSpecular', 'boundingBoxMaxZ', 'overrideDisplayType', 
                    'boundingBoxMaxX', 'boundingBoxMaxY', 'nodeState', 'overrideVisibility', 'ghostColorPreA', 'ghostColorPreB', 'ghostColorPreG', 'layerRenderable', 
                    'pointCameraZ', 'lodVisibility', 'uCoord', 'ghostColorPreR', 'ghostStepSize', 'viewMode', 'caching', 'instObjGroups']
    
    spotLight = ['smapCameraName', 'emitDiffuse', 'areaVisible', 'writeDmap', 'fogIntensity', 'useObjectColor', 'farPointWorldY', 'farPointWorldX', 
                 'useDmapAutoClipping', 'areaLight', 'areaLowLevel', 'overrideEnabled', 'smapSceneName', 'farPointWorldZ', 'uvFilterSizeY', 'uvFilterSizeX', 
                 'lightShadowFraction', 'dropoff', 'colorB', 'ghostPostSteps', 'pointWorldY', 'pointWorldX', 'rayDepth', 'smapDetailSamples', 'binMembership', 'colorR', 
                 'locatorScale', 'customTreatment', 'reuseDmap', 'useZ-Dmap', 'emitSpecular', 'smapFrameExt', 'useOnlySingleDmap', 'dmapFrameExt', 'ghostColorPostG', 
                 'ghostColorPostB', 'ghostColorPostA', 'bottomBarnDoor', 'startDistance1', 'areaNormalX', 'smapCameraAperture', 'useDmapAutoFocus', 'creationDate', 
                 'ghostColorPostR', 'templatePath', 'overrideShading', 'useDepthMapShadows', 'receiveShadows', 'overrideTexturing', 'areaLowSamplingV', 'smapDetailAlpha', 
                 'lightIntensityB', 'lightDiffuse', 'barnDoors', 'lightIntensityR', 'objectColor', 'areaSamplingU', 'topBarnDoor', 'areaEdgeX', 'decayRate', 'shadColorB', 
                 'boundingBoxMinX', 'boundingBoxMinY', 'boundingBoxMinZ', 'creator', 'fogSpread', 'ghostRangeEnd', 'lightIntensityG', 'shadColorR', 'intensity', 
                 'miExportMrLight', 'vCoord', 'templateVersion', 'lightBlindData', 'pointCameraY', 'pointCameraX', 'overridePlayback', 'dmapWidthFocus', 'renderState', 
                 'infoBits', 'identification', 'dmapNearClipPlane', 'template', 'containerType', 'startDistance3', 'startDistance2', 'viewName', 'useZ+Dmap', 'primitiveId', 
                 'endDistance3', 'endDistance1', 'overrideColor', 'coneAngle', 'dmapSceneName', 'rmbCommand', 'useMidDistDmap', 'smapCameraFocal', 'areaLowSamplingU', 
                 'rayInstance', 'boundingBoxCenterX', 'boundingBoxCenterY', 'energyG', 'colorG', 'rightBarnDoor', 'objectId', 'centerOfIllumination', 
                 'energyR', 'penumbraAngle', 'emitPhotons', 'ghostRangeStart', 'pointWorldZ', 'rayDepthLimit', 'raySampler', 'dmapLightName', 'dmapName', 'leftBarnDoor', 
                 'smapSoftness', 'dmapFarClipPlane', 'overrideLevelOfDetail', 'shadColorG', 'photonIntensity', 'ghosting', 'shadowRays', 'objectType', 
                 'isHistoricallyInteresting', 'useX-Dmap', 'useY-Dmap', 'dmapFilterSize', 'useRayTraceShadows', 'fogShadowIntensity', 'endDistance2', 'shadowMap', 
                 'useY+Dmap', 'useShadowMapCamera', 'areaEdgeY', 'boundingBoxCenterZ', 'areaEdgeZ', 'preShadowIntensity', 'dmapResolution', 'energyB', 'smapCameraAspect', 
                 'visibility', 'smapCameraResolution', 'layerOverrideColor', 'smapBias', 'areaSamplingV', 'uiTreatment', 'psIllumSamples', 'opticalFXvisibilityG', 
                 'opticalFXvisibilityB', 'lightRadius', 'smapDetail', 'castSoftShadows', 'opticalFXvisibilityR', 'boundingBoxSizeX', 'boundingBoxSizeY', 'boundingBoxSizeZ', 
                 'ghostPreSteps', 'useDecayRegions', 'objectColorR', 'areaType', 'lightDirectionZ', 'useX+Dmap', 'lightDirectionX', 'lightDirectionY', 'objectColorB', 
                 'objectColorG', 'isCollapsed', 'rayDirectionY', 'rayDirectionZ', 'blackBox', 'templateName', 'lightAmbient', 'ghostingControl', 'smapDetailAccuracy', 
                 'lightSpecular', 'smapSamples', 'boundingBoxMaxZ', 'overrideDisplayType', 'boundingBoxMaxX', 'boundingBoxMaxY', 'areaNormalY', 'rayDirectionX', 'nodeState', 
                 'overrideVisibility', 'ghostColorPreA', 'ghostColorPreB', 'ghostColorPreG', 'layerRenderable', 'pointCameraZ', 'lodVisibility', 'uCoord', 'ghostColorPreR', 
                 'exponent', 'volumeShadowSamples', 'smapFilename', 'areaNormalZ', 'smapLightName', 'areaRadius', 'dmapFocus', 'ghostStepSize', 
                 'viewMode', 'causticPhotons', 'dmapBias', 'caching', 'smapResolution', 'globIllPhotons','instObjGroups']

    
    allTheLights = []
    typeLists = ['directionalLight','volumeLight','areaLight','spotLight','pointLight','ambientLight']
    for eachType in typeLists:
        allTheLights += cmds.ls(exactType = eachType)
    
    lightSettingDict = {}
    if allTheLights != "":
        for eachLight in allTheLights:
            generalDict = {}
            if cmds.objectType(eachLight) == "areaLight":
                lightAttributs = areaLightAttribs
            if cmds.objectType(eachLight) == "volumeLight":
                lightAttributs = volumeLightAttribs
            if cmds.objectType(eachLight) == "pointLight":
                lightAttributs = pointLight
            if cmds.objectType(eachLight) == "directionalLight":
                lightAttributs = directionalLight
            if cmds.objectType(eachLight) == "ambientLight":
                lightAttributs = ambientLight
            if cmds.objectType(eachLight) == "spotLight":
                lightAttributs = spotLight
    #         lightAttributs = cmds.listAttr(eachLight, hasData = True, visible = True, scalarAndArray = True, multi = True, output = True)
            for eachAttrib in lightAttributs:
                if eachAttrib != 'caching' or eachAttrib != 'nodeState':
                    eachValue = cmds.getAttr("%s.%s"%(eachLight,eachAttrib))
                    if "+" in eachAttrib:
                        eachAttrib = eachAttrib.replace("+","_tTt_")
                    if "-" in eachAttrib:
                        eachAttrib = eachAttrib.replace("-","_mMm_")
                    if "[" in eachAttrib: 
                        eachAttrib = eachAttrib.replace('[', '_aAa_')
                    if "]" in eachAttrib: 
                        eachAttrib = eachAttrib.replace(']', '_zZz_')
                    generalDict[eachAttrib] = eachValue
            lightSettingDict[eachLight] = generalDict
        print "Generation Light Setting is Done"
    else:
        print "There is no Light in the scene"
    return lightSettingDict

def _RecordLight():
    '''
    lightDict {[LIGHT NAME]:
                        [TYPE OF LIGHT]:
                                [VALUE]
                        [LINKS]:
                                [VALUE]
                        [TRANSLATE]
                                [VALUE]
                        [ROTATION]
                                [VALUE]
                        [SCALE]
                                [VALUE]}
    '''
    allTheLights = []
    typeLists = ['directionalLight','volumeLight','areaLight','spotLight','pointLight','ambientLight']
    for eachType in typeLists:
        allTheLights += cmds.ls(exactType = eachType)

    lightDict = {}
    if allTheLights:
        for eachLight in allTheLights:
            generalDict = {}
            for eachType in typeLists:
                if cmds.nodeType(eachLight) == eachType:
                    generalDict["Type"]         = eachType #Getting the Type of Light
                    lightLinkedList = []
                    eachLightT = cmds.listRelatives(eachLight, parent=True)[0]
                    for eachLink in cmds.lightlink(query=True, light=eachLight):
                        print eachLink
                        lightLinkedList.append(str(eachLink))
                    generalDict["Linked"]       = lightLinkedList #Getting the list of objects linked to
                    lightTranslation = cmds.xform(eachLightT,query = True, translation=True) 
                    generalDict["Translation"]  = lightTranslation #GEtting the Translation
                    lightRotation = cmds.xform(eachLightT,query = True, rotation=True) 
                    generalDict["Rotation"]     = lightRotation #Getting the Rotation
                    lightScale = cmds.xform(eachLightT,query = True, scale=True, relative=True) 
                    generalDict["Scale"]        = lightScale #Getting the Scale
            lightDict[eachLight] = generalDict
    
    print "Generation Light is Done"
    return lightDict

def writeLightData(pathToXML = ''):
    """
    Function to write out LightSetting
    """
    debug(app = None, method = 'light_writeXML.writeLightData', message = 'pathToXML: %s' % pathToXML, verbose = False)
    
    ## now process the data into the xml tree      
    root        = Element('Lights')
    tree        = ElementTree(root)
      
    lightSettingsData   = _RecordLightSetting()
    lightData           = _RecordLight()
    
    lightSettingsName    = Element('LightSetting')
    root.append(lightSettingsName)
    
    lightName     = Element('Light')
    root.append(lightName)
    
    for eachLightKey, eachLightValue in lightData.items():
        newLightName = SubElement(lightName, str(eachLightKey))
        for eachAttr , eachValue in eachLightValue.items():
            lightType = SubElement(newLightName, eachAttr, value = str(eachValue))

            
    for eachlayer , eachlayerValue in lightSettingsData.items():
        passName = SubElement(lightSettingsName, str(eachlayer))
        for eachSetKey , eachSetValue  in eachlayerValue.items():
            passType = SubElement(passName, eachSetKey, value = str(eachSetValue))
        
    tree.write(open(pathToXML, 'w'), encoding="utf-8")