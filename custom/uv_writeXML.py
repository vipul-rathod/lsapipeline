import os, getpass, sys
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import time
import maya.cmds as cmds
import uv_getUVs as getUvs
import uv_setUVs as setUvs
import maya.api.OpenMaya as om
from xml.etree.ElementTree import ElementTree
import xml.etree.ElementTree as etree
from xml.etree.ElementTree import Element, SubElement, tostring
from debug import debug
#reload(getUvs)
#reload(setUvs)

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
    
def writeUVData(rootName = '', data = [], pathToXML = ''):
    """
    Function to write out uv data. Note we're passing the data as a list so we can fetch as many uv_getUVs in list to process in one big hit.
    """
    ## Delete existing
    if checkFilePath(pathToXML):
        os.remove(pathToXML)
    
    ## now process the data into the xml tree   
    root = Element(rootName)
    tree = ElementTree(root)
    
    for eachData in data:
        geoName = Element(eachData[0].split('|')[-1])
        root.append(geoName)
        finalData = eachData[1]
        for uvset, uvdata in finalData.items():
            uvData = SubElement(geoName, '%s_uvData' % str(uvdata[1]))            
            ## Now process into the correct child elements
            pathToGeo = SubElement(uvData, str(uvdata[0].replace('|', '_iIi_')))
            #debug(None, method = 'uv_writeXML.writeUVData', message = '{0:<10}{1}'.format('pathToGeo: ',  pathToGeo), verbose = False)
            
            uvSet = SubElement(uvData, str(uvdata[1]))
            
            uData = SubElement(uvData, 'uData', value = str(uvdata[2]).split('[')[-1].split(']')[0].replace(',', ''))
            #debug(None, method = 'uv_writeXML.writeUVData', message = '{0:<10}{1}'.format('uData: ',  uData), verbose = False)
            
            vData = SubElement(uvData, 'vData', value = str(uvdata[3]).split('[')[-1].split(']')[0].replace(',', ''))
            #debug(None, method = 'uv_writeXML.writeUVData', message = '{0:<10}{1}'.format('vData: ',  vData), verbose = False)

            perFaceInfo = SubElement(uvData, 'perFaceInfo')
            for key, var in uvdata[4].items():
                faceId = SubElement(perFaceInfo, "faceID_int", value = str(key))
                faceVertInfo = SubElement(faceId, 'faceVert_MIntArray', value = str(var[0]).split('[')[-1].split(']')[0].replace(',', ''))
                faceUVInfo = SubElement(faceId, 'faceUV_MIntArray', value = str(var[1]).split('[')[-1].split(']')[0].replace(',', ''))
                
            uvMapIndex = SubElement(uvData, 'mapIndex', value = str(uvdata[5]))
    
    tree.write(open(pathToXML, 'w'), encoding="utf-8")
    #debug(None, method = 'uv_writeXML.writeUVData', message = 'Success. Wrote UV data for %s to %s' % (rootName, pathToXML), verbose = False)