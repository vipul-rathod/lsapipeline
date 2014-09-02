import os, sys
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import xml.etree.ElementTree as ET
import maya.cmds as cmds
import time 
import xml.etree.ElementTree as ET
from debug import debug

alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 
            'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 
            'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

signs = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ',)', ')', 'e-', '+', '=', '\\', '}', '{', ']', '[', "'", ':', ';', '>', '<', '?', '/', ' ']

def _readLightXML(pathToXML):
    '''
    convert all the XML Data to separate Dictionary
    '''
    tree = ET.parse(pathToXML)
    root = tree.getroot()
    
    lightSettingDict = {} #Light Setting Dictionary 
    lightDict = {} #Light Dictionary
    
#     print root[1].tag
    for childLight in root[1]: # getting into Light group
        generalDict = {}
        for eachgroup in childLight: # getting in to each light setting
            
            eachAttr = eachgroup.tag #getting Name of group
            eachAttr = _CleanUpSpecialText(eachAttr)
            
            eachValue = eachgroup.attrib #getting Value of group
            eachValue = eachValue['value']
            eachValue = _Converter(eachValue) #Converting the Value to right format 
            
            generalDict[eachAttr] = eachValue
        lightDict[childLight.tag] = generalDict
    
    for childSetting in root[0]:
        generalDict = {}
        for eachSetting in childSetting:
            
            attributeName = eachSetting.tag #getting Name of attribute
            attributeName  = _CleanUpSpecialText(attributeName)
            
            attributeValue = eachSetting.attrib #getting Value of attribute
            attributeValue = attributeValue['value']
            attributeValue = _Converter(attributeValue) #Converting the Value to right format 

            generalDict[attributeName] = attributeValue
        lightSettingDict[childSetting.tag] = generalDict
        
    return lightDict,lightSettingDict

def _Converter(newValue):
    
    eachValue = newValue
    valid = 1
    for eachSign in signs:
        if eachSign in eachValue:
            eachValue = eachValue.replace(eachSign, "")
    if eachValue != "":
        if "," in eachValue:
            eachValue = eachValue.split(",")
        if type(eachValue) == list:
            listHolder = []
            for eachV in eachValue:
                valid = 1
                for eachLetter in alphabet:
                    if eachLetter in eachV:
                        valid = 0
                if valid == 1:
                    if "." in eachV:
                        eachV = float(eachV)
                    else:
                        eachV = int(eachV)
                if "True" == eachV or "False" == eachV:
                    eachV = bool(eachV)
                listHolder.append(eachV)
            listHolder = tuple(listHolder)
            newValue = listHolder
        if type(eachValue) == str:
            for eachLetter in alphabet:
                if eachLetter in eachValue:
                    valid = 0
            if valid == 1:
                if "." in eachValue:
                    eachValue = float(eachValue)
                else:
                    eachValue = int(eachValue)
            if "True" == eachValue or "False" == eachValue:
                eachValue = bool(eachValue)
            newValue = eachValue
    else:
        newValue = ""
    return newValue

def _CleanUpSpecialText(newValue):
    
    if "_tTt_" in newValue:
        newValue = newValue.replace("_tTt_","+")
    if "_mMm_" in newValue:
        newValue = newValue.replace("_mMm_","-")
    if "_aAa_" in newValue: 
        newValue = newValue.replace('_aAa_', '[')
    if "_zZz_" in newValue: 
        newValue = newValue.replace('_zZz_', ']')
    
    return newValue

def _CleanUp(lightName, lightType, lightT, lightR, lightS, lightLinked):
    if cmds.objExists('LIGHTS_hrc') != True:
        cmds.group(name='LIGHTS_hrc', empty=True)
    
    if cmds.objExists(lightName):
        if cmds.objectType(lightName) == lightType:
            lightSucced = 1
            newLight = cmds.listRelatives(lightName, parent=True)[0]
        else:
            lightSucced = 0
            print "%s is not %s type of light, so information wont transfer"%(lightName,lightType)
    else:
        lightSucced = 1
        if lightType == 'ambientLight':
            cmds.rename(cmds.CreateAmbientLight(1, 0.45, 1,1,1, "0", 0,0,0, "1"),lightName)
            newLight = cmds.rename(lightName,lightName.replace('Shape',''))
            cmds.rename(cmds.listRelatives(newLight, children=True)[0],lightName)
        elif lightType == 'directionalLight':
            cmds.rename(cmds.CreateDirectionalLight(1, 1,1,1, "0", 0,0,0, 0),lightName)
            newLight = cmds.rename(lightName,lightName.replace('Shape',''))
            cmds.rename(cmds.listRelatives(newLight, children=True)[0],lightName)
        elif lightType == 'pointLight':
            cmds.rename(cmds.CreatePointLight(1, 1,1,1, 0, 0, 0,0,0, 1),lightName)
            newLight = cmds.rename(lightName,lightName.replace('Shape',''))
            cmds.rename(cmds.listRelatives(newLight, children=True)[0],lightName)
        elif lightType == 'spotLight':
            cmds.rename(cmds.CreateSpotLight(1, 1,1,1, 0, 40, 0, 0, 0, 0,0,0, 1, 0),lightName)
            newLight = cmds.rename(lightName,lightName.replace('Shape',''))
            cmds.rename(cmds.listRelatives(newLight, children=True)[0],lightName)
        elif lightType == 'areaLight':
            cmds.rename(cmds.CreateAreaLight(1, 1,1,1, 0, 0, 0,0,0, 1, 0),lightName)
            newLight = cmds.rename(lightName,lightName.replace('Shape',''))
            cmds.rename(cmds.listRelatives(newLight, children=True)[0],lightName)
        elif lightType == 'volumeLight':
            cmds.rename(cmds.CreateVolumeLight(1, 1,1,1, 0, 0, 0,0,0, 1),lightName)
            newLight = cmds.rename(lightName,lightName.replace('Shape',''))
            cmds.rename(cmds.listRelatives(newLight, children=True)[0],lightName)

#         newLight = cmds.createNode(lightType)
#         newLight = cmds.rename(newLight,lightName)
#         newLight = cmds.rename(cmds.listRelatives(newLight, parent=True)[0],lightName.replace('Shape',''))

    cmds.xform(newLight, translation=lightT,rotation=lightR,scale=lightS)

    if cmds.listRelatives('LIGHTS_hrc', children=True) == None or newLight not in cmds.listRelatives('LIGHTS_hrc', children=True):
        cmds.parent(newLight,'LIGHTS_hrc')
    
    everything = cmds.ls()
    cmds.lightlink(b=True,light=lightName,object=everything)
    if lightLinked != "":
        for eachAsset in lightLinked:
            try:
    #             time.sleep(1)
                cmds.lightlink(light=lightName,object=eachAsset)
            except:
#                 print eachAsset
                pass
    return lightSucced

def actionLightXML(pathToXML=''):
    
    debug(None, method = 'actionLightXML', message = '{0:<10}{1}'.format('pathToXML: ',  pathToXML), verbose = False)
    lightDict ,lightSettingDict = _readLightXML(pathToXML)
    
    validLights = []
    for eachLight, eachSetting in lightDict.iteritems():
        cleanUpResult = _CleanUp(eachLight, eachSetting['Type'],eachSetting["Translation"],eachSetting["Rotation"],eachSetting["Scale"],eachSetting['Linked'])
        if cleanUpResult == 1:
            validLights.append(eachLight)

    for eachValid in validLights:
        for eachKey, eachValue in lightSettingDict[eachValid].iteritems():
            #print type(eachValid), type(eachKey),type(eachValue)
            if type(eachValue) == int:
                cmds.setAttr("%s.%s"%(eachValid,eachKey),eachValue)
            if type(eachValue) == bool and 'intermediateObject' not in eachKey :
                #print 'cmds.setAttr(\"%s.%s\", %s)' % (eachValid,eachKey,eachValue)
                cmds.setAttr("%s.%s"%(eachValid,eachKey),eachValue)
            if type(eachValue) == str:
                cmds.setAttr("%s.%s"%(eachValid,eachKey),eachValue, type="string")
            if type(eachValue) == tuple:
                #print "%s.%s %s Progressing" %(eachValid,eachKey,eachSettingValue)
                pass