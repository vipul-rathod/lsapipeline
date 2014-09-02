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

def getAssetName():
    if cmds.objExists('geo_hrc'):
        assetName = cmds.listRelatives('geo_hrc', parent = True)
        return assetName
    else:
        return False

def getCoreGroups():
    if cmds.objExists('CORE_ARCHIVES_hrc'):
        coreGroups = [eachCore for eachCore in cmds.listRelatives('CORE_ARCHIVES_hrc', children = True)]
        return coreGroups
    else:
        return False

def getCoreData():
    allCoreData = {}
    
    coreGroups  = getCoreGroups()
    #debug(app = None, method = 'getCoreData', message = 'coreGroups: %s' % coreGroups, verbose = False)
    
    ## Process the cores in the scene now.
    if coreGroups:
        for eachGrp in coreGroups:
            cores   = [eachCore for eachCore in cmds.listRelatives(eachGrp, children = True, f = True) if 'Shape' not in eachCore]
            for eachCore in cores:
                ## fetch info
                path    = cmds.getAttr('%s.mcAssArchive' % eachCore)
                trans   = cmds.xform(eachCore, query = True, translation = True)
                rot     = cmds.xform(eachCore, query = True, rotation = True)
                scale   = cmds.xform(eachCore, query = True, scale = True, r = True)
                
                ## Add to the dic
                allCoreData[eachCore] = [eachGrp, path, trans, rot, scale]
    return allCoreData
    
def writeCoreData(pathToXML = ''):
    """
    Function to write out uv data. Note we're passing the data as a list so we can fetch as many uv_getUVs in list to process in one big hit.
    """
    #debug(app = None, method = 'writeCoreData', message = 'pathToXML: %s' % pathToXML, verbose = False)
    
    ## Delete existing
    if checkFilePath(pathToXML):
        os.remove(pathToXML)
    
    ## now process the data into the xml tree   
    assetName   = getAssetName()[0]
    #debug(app = None, method = 'writeCoreData', message = 'assetName: %s' % assetName, verbose = False)
    
    root        = Element(assetName)
    tree        = ElementTree(root)
      
    data        = getCoreData()
    #debug(app = None, method = 'writeCoreData', message = 'data: %s' % data, verbose = False)
    
    for coreName, coreData in data.items():
        geoName     = Element(str(coreName.replace('|', '_iPipei_')))
        root.append(geoName)

        group               = SubElement(geoName,  'GROUPNAME', value = str(coreData[0]))
        corePath            = SubElement(geoName,  'COREPATH', value = str(coreData[1].replace(':', '_iColoni_').replace('/', '_iFwdSlashi_')))
        translationData     = SubElement(geoName,  'TRANSLATEX', value = str(coreData[2]).split('[')[-1].split(']')[0].replace(',', ''))
        rotateData          = SubElement(geoName,  'ROTATION', value = str(coreData[3]).split('[')[-1].split(']')[0].replace(',', ''))
        scaleData           = SubElement(geoName,  'SCALE', value = str(coreData[4]).split('[')[-1].split(']')[0].replace(',', ''))
        #debug(app = None, method = 'writeCoreData', message = 'corePath: %s' % coreData[1], verbose = False)
        #debug(app = None, method = 'writeCoreData', message = 'translation: %s' % coreData[2], verbose = False)
        #debug(app = None, method = 'writeCoreData', message = 'rotation: %s' % coreData[3], verbose = False)
        #debug(app = None, method = 'writeCoreData', message = 'scale: %s' % coreData[4], verbose = False)
    
    tree.write(open(pathToXML, 'w'), encoding="utf-8")
    #debug(None, method = 'uv_writeXML.writeCoreData', message = 'Success. Wrote UV data for %s to %s' % (rootName, pathToXML), verbose = False)