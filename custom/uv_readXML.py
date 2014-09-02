import os, getpass, sys
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug
import time
from xml.etree.ElementTree import ElementTree
import xml.etree.ElementTree as etree
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET

import maya.cmds as cmds
import maya.api.OpenMaya as om

import uv_setUVs as setUvs
#reload(setUvs)

def makeMFloatArray(xmldata):
    myFloatArray = om.MFloatArray()
    for each in xmldata.attrib['value'].split(' '):
        myFloatArray.append(float(each))
    return myFloatArray
    
def parseFaceInfo(xmldata):
    ## Final dict to return
    perFaceUVInfo = {}
    getData = xmldata.getchildren()
    for eachDataSet in getData:
        myVertexIntArray        = []
        myUVID_IntArray         = []
        getArrays = eachDataSet.getchildren()
        for eachArray in getArrays:
            if 'faceVert_MIntArray' in eachArray.tag:
                for eachVal in eachArray.attrib['value'].split(' '):
                    myVertexIntArray.append(eachVal)
            if 'faceUV_MIntArray' in eachArray.tag:
                for eachVal in eachArray.attrib['value'].split(' '):
                    myUVID_IntArray.append(eachVal)
            perFaceUVInfo[int(eachDataSet.attrib['value'])] = [myVertexIntArray, myUVID_IntArray]

    return perFaceUVInfo

def parseShellInfo(xmldata):
    getData = xmldata.getchildren()[0].getchildren()
    ##<Element ShellCount at 34797948>, <Element ShellUVInfo at 347979c8>, <Element ShellUVs at 34797a08>
    #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('getData:',  getData), verbose = False)
    
    allShellUVIDInttArray = om.MIntArray()
    #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('getData[1].attrib["value"]:',  getData[1].attrib['value']), verbose = False)
    
    for eachVal in getData[1].attrib['value'].split(' '):
        allShellUVIDInttArray.append(int(eachVal))
    #getShells   = shapeFn.getUvShellsIds(map) ## From uv_getUVs
    getShells     = (getData[0].attrib['value'], allShellUVIDInttArray)  
    #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('getShells:',  getShells), verbose = False)
    
    shellUVs = {}
    shellUVsCount = {}
    getShellIDInfo = getData[2].getchildren()
    for eachShellID in getShellIDInfo:
        #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('eachShellID:',  eachShellID), verbose = False)
        
        if eachShellID.tag == 'shellID':
            getArray            = eachShellID.getchildren()
            #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('getArray:',  getArray), verbose = False)
            shellUVID_IntArray  = om.MIntArray()
            
            ## now put them back into an IntArray
            for eachVal in getArray[0].attrib['value'].split(' '):
                shellUVID_IntArray.append(int(eachVal))
            
            #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('shellUVID_IntArray:',  shellUVID_IntArray), verbose = False)
            #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('shellID:',  eachShellID.attrib['value']), verbose = False)
            shellUVs[int(eachShellID.attrib['value'])] = shellUVID_IntArray
        elif eachShellID.tag == 'shellFaceCount ':
            getArray            = eachShellID.getchildren()
            #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('getArray:',  getArray), verbose = False)
            shellFaceCount_IntArray  = om.MIntArray()
            
            ## now put them back into an IntArray
            for eachVal in getArray[0].attrib['value'].split(' '):
                shellFaceCount_IntArray.append(int(eachVal))
            
            #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('shellUVID_IntArray:',  shellUVID_IntArray), verbose = False)
            #debug(None, method = 'uv_readXML.parseShellInfo', message = '{0:<10}{1}'.format('shellID:',  eachShellID.attrib['value']), verbose = False)
            shellUVsCount[int(eachShellID.attrib['value'])] = shellFaceCount_IntArray
        else:
            pass
    return getShells, shellUVs, shellUVsCount

def readUVData(pathToUVXML = '', parentGrp = '', assignUVS = True):
    
    tree = ET.parse(pathToUVXML)
    root = tree.getroot()
    geoToProcess = root.getchildren()
    
    print 'Parsing uv data from: %s' % pathToUVXML
    if not geoToProcess:
        cmds.warning('THERE IS NO UV DATA WRITTEN TO FILE: %s' % pathToUVXML)
    else:
        
        for eachGeo in geoToProcess:
            #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('geoToProcess: ',  geoToProcess), verbose = False)
            uvSetData = {}
            #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('Processing: ',  eachGeo.tag), verbose = False)
            uvSets = eachGeo.getchildren()
            for eachUVSet in uvSets:
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('Processing uvset: ',  eachUVSet.tag), verbose = False)
                data = []
                ## Get all the children
                getSetData          = eachUVSet.getchildren()
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('getSetData: ',  getSetData), verbose = False)
                ## convert the children data back to python usable data so we can push to the uv_setUVs
                if parentGrp:
                    pathToGeo           = '%s%s' % (parentGrp, str(getSetData[0].tag).replace('_iIi_', '|'))
                    #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('pathToGeo: ',  pathToGeo), verbose = False)
                else:
                    pathToGeo           = str(getSetData[0].tag).replace('_iIi_', '|')
                    #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('pathToGeo: ',  pathToGeo), verbose = False)
                uvsetName           = getSetData[1].tag
                uData               = makeMFloatArray(getSetData[2])
                vData               = makeMFloatArray(getSetData[3])
                perFaceInfo         = parseFaceInfo(getSetData[4])
                #shellInfo           = parseShellInfo(getSetData[5])
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('uvsetName: ',  uvsetName), verbose = False)
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('uData: ',  uData), verbose = False)
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('vData: ',  vData), verbose = False)
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('perFaceInfo: ',  perFaceInfo), verbose = False)
                
                try:mapIndex        = int(getSetData[5].attrib['value'])
                except:
                    debug(None, method = 'uv_readXML.readUVData', message = 'mapIndex set to 0 for: %s' % eachGeo, verbose = False)
                    mapIndex = 0
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('mapIndex:',  mapIndex), verbose = False)
                ## Rebuild the data into the accepted dictionary for the setUvs function
                ## Add the path to the geo
                ## Returns |path|to|geo
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('pathToGeo:',  pathToGeo), verbose = False)
                data.extend([pathToGeo])
                
                ## Add the name
                ## Returns nameofUvSet
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('uvsetName:',  uvsetName), verbose = False)
                data.extend([uvsetName])
                
                ## Add the u and v from the straight foward fetch
                ## Returns [uArray], [vArray]
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('uData:',  uData), verbose = False)
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('vData:',  vData), verbose = False)
                data.extend([uData])
                data.extend([vData])
        
                ## Get the perFace info in case we need it for rebuilding later
                ## Returns {faceId: [myVertixIntArray, myUVID_IntArray]}
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('perFaceInfo:',  perFaceInfo), verbose = False)
                data.extend([perFaceInfo])
                
                ## Add the num of uvshells and the shell list
                ## Returns (shellCount, [vertIndexShellAssociationList]), {shell: [shellUVs]}, [ShellUVsCount]
#                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('shellInfo:',  shellInfo), verbose = False)
#                data.extend([shellInfo])
                
                if eachGeo.tag not in uvSetData.keys():
                    uvSetData[eachGeo.tag] = [[data]]
                else:
                    uvSetData[eachGeo.tag].append([data])
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('data:',  data), verbose = False)
                #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('Appended uvData to uvSetData for:', eachGeo.tag), verbose = False)
                #print
                
                #if mapIndex:           
                data.extend([mapIndex])
                
            ## Now perform the UV setup in maya
            if assignUVS:
                #for key, var in uvSetData.items():
                #    print key, var
                setUvs.readData(uvSetData)
            else:
                #===============================================================
                # for key, var in uvSetData.items():
                #     #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('uvSetData key:',  key), verbose = False)
                #     #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('uvSetData var:',  var), verbose = False)
                #     for each in var:
                #         #debug(None, method = 'uv_readXML.readUVData', message = '{0:<10}{1}'.format('EACH IN VAR:',  each), verbose = False)
                #         pass
                #===============================================================
                pass
                    