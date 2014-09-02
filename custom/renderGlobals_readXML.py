import os, getpass, sys
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import maya.cmds as cmds
from debug import debug
import time
from xml.etree.ElementTree import ElementTree
import xml.etree.ElementTree as etree
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET
from debug import debug
import maya.cmds as cmds
from mentalcore import mapi

alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 
            'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 
            'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

signs = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '=', '\\', '}', '{', ']', '[', "'", ':', ';', '>', '<', '?', '/', ' ']

def readCoreData(pathToXML = ''):
    '''
    Clean up the Scene, get the Dictionary and setup the scene.
    '''
    print 'MY PATHTOXML IS: %s' % pathToXML
    _cleanUp()
    print "Cleaned Up successfully"
    mentalCoreGlobalsDict,mentalCoreLensDataDict,mentalrayGlobalsDict,miDefaultOptionDict, layerDict, mentalCorePassesDict = _XML2Dictinary(pathToXML)
#     print mentalCoreGlobalsDict
#     print mentalCoreLensDataDict
#     print mentalrayGlobalsDict
#     print miDefaultOptionDict
#     print layerDict
#     print mentalCorePassesDict
    print "Dictionaries are here successfully"
    mentalCoreAvailibleDict = {0:'Beauty', 1:'Colour', 2:'Diffuse', 3:'Diffuse Raw', 4:'Shadow', 
                               5:'Shadow Raw', 6:'Diffuse Without Shadows', 7:'Diffuse Without Shadows Raw', 
                               8:'Ambient', 9:'Ambient Raw', 10:'Indirect', 11:'Indirect Raw', 
                               12:'Ambient Occlusion', 13:'Translucency', 14:'Subsurface', 
                               15:'Subsurface Front', 16:'Subsurface Mid', 17:'Subsurface Back', 
                               18:'Incandescence', 19:'Specular', 20:'Reflection', 21:'Refraction', 
                               38:'Light Select', 22:'Bloom Source', 37:'Environment', 23:'Depth', 
                               23:'Depth (Normalized)', 24:'Normal World', 24:'Normal World (Normalized)', 
                               25:'Normal Camera', 25:'Normal Camera (Normalized)', 26:'Point World', 
                               27:'Point Camera', 28:'Motion Vector', 28:'Motion Vector (Normalized)', 
                               29:'Opacity', 30:'Facing Ratio', 31:'UV', 32:'Material ID', 33:'Object ID', 
                               34:'Matte', 35:'Custom Colour', 36:'Custom Vector', 39:'Diagnostic Samples', 
                               40:'Diagnostic Error', 41:'Diagnostic Time'}

        #########################################################################
        # 1- check if layer exist and if not create a new layer
        #########################################################################
    for eachKey, eachValue in layerDict.iteritems():
        if eachKey not in cmds.ls(type="renderLayer"): #Looking for Existing layers and adding to the scene
            cmds.createRenderLayer(name=eachKey)
        #########################################################################
        # 2- assign the each Asset under each layer
        #########################################################################
        if eachKey != "defaultRenderLayer": #assigning each assets to each existing layer
            for eachOBJ in eachValue[1]:
                cmds.editRenderLayerMembers(eachKey,eachOBJ, noRecurse=True)
        
        #########################################################################
        # 3- check the passes in the scene and create one if doesn't exist
        #########################################################################
    for eachKey, eachValue in mentalCorePassesDict.iteritems():
        if eachValue[0] != "":
            mapi.create_pass(mentalCoreAvailibleDict[eachValue[0]], n=eachKey)
        
        
        #########################################################################
        # 4- set each passes setting in the scene
        #########################################################################
        for eachSettingKey, eachSettingValue in eachValue[2].iteritems():
#             print "%s.%s %s Progressing" %(eachKey,eachSettingKey,eachSettingValue)
#             print type(eachSettingValue)
            if eachSettingValue != "":
                if type(eachSettingValue) == int:
                    cmds.setAttr("%s.%s"%(eachKey,eachSettingKey),eachSettingValue)
                if type(eachSettingValue) == bool:
                    cmds.setAttr("%s.%s"%(eachKey,eachSettingKey),eachSettingValue)
                if type(eachSettingValue) == str:
                    cmds.setAttr("%s.%s"%(eachKey,eachSettingKey),eachSettingValue, type="string")
                if type(eachSettingValue) == tuple:
                    print "%s.%s %s Progressing" %(eachKey,eachSettingKey,eachSettingValue)
                    print type(eachSettingValue)
        
        #########################################################################
        # 5- connect the passes to asses in the scene
        #########################################################################
        if eachValue[1] != "":
            mapi.link_to_pass(eachValue[1], eachKey, mapi.OBJECTS)
        
        
        #########################################################################
        # 6- check the associated passes and create new if doesn't exist
        #########################################################################
    for eachlayerKey , eachlayerValue in layerDict.iteritems():
        if eachlayerValue[0] != "":
            for eachAssociacted in eachlayerValue[0]:
                mapi.associate_pass(eachAssociacted, eachlayerKey)

        #########################################################################
        # 7- set the setting of imDefaultOption
        #########################################################################
    miDefaultName = "miDefaultOptions"
    for eachMIKey, eachIMValue in miDefaultOptionDict.iteritems():
        if eachIMValue != "":
            if type(eachIMValue) == int:
                cmds.setAttr("%s.%s"%(miDefaultName,eachMIKey),eachIMValue)
            if type(eachIMValue) == bool:
                cmds.setAttr("%s.%s"%(miDefaultName,eachMIKey),eachIMValue)
            if type(eachIMValue) == str:
                cmds.setAttr("%s.%s"%(miDefaultName,eachMIKey),eachIMValue, type="string")
            if type(eachIMValue) == tuple:
                print "%s.%s %s Progressing" %(miDefaultName,eachMIKey,eachIMValue)
                print type(eachIMValue)
        
        if eachIMValue == "":
            cmds.setAttr("%s.%s"%(miDefaultName,eachMIKey),"", type="string")
        
        #########################################################################
        # 8- set the setting of Mentalray Globals
        #########################################################################
    mentalrayName = "mentalrayGlobals"
    for eachMRKey, eachMRValue in mentalrayGlobalsDict.iteritems():
        if eachMRValue != "":
            if type(eachMRValue) == int:
                cmds.setAttr("%s.%s"%(mentalrayName,eachMRKey),eachMRValue)
            if type(eachMRValue) == bool:
                cmds.setAttr("%s.%s"%(mentalrayName,eachMRKey),eachMRValue)
            if type(eachMRValue) == str:
                cmds.setAttr("%s.%s"%(mentalrayName,eachMRKey),eachMRValue, type="string")
            if type(eachMRValue) == tuple:
                print "%s.%s %s Progressing" %(mentalrayName,eachMRKey,eachMRValue)
                print type(eachMRValue)
        if eachMRValue == "":
            cmds.setAttr("%s.%s"%(mentalrayName,eachMRKey),"", type="string")
        #########################################################################
        # 9- set the setting of MentalCore Globals
        #########################################################################
    mentalcoreGlobalsName = "mentalcoreGlobals"
    for eachMCGKey, eachMCGValue in mentalCoreGlobalsDict.iteritems():
        if eachMCGValue != "":
            if type(eachMCGValue) == int:
                cmds.setAttr("%s.%s"%(mentalcoreGlobalsName,eachMCGKey),eachMCGValue)
            if type(eachMCGValue) == bool:
                cmds.setAttr("%s.%s"%(mentalcoreGlobalsName,eachMCGKey),eachMCGValue)
            if type(eachMCGValue) == str:
                cmds.setAttr("%s.%s"%(mentalcoreGlobalsName,eachMCGKey),eachMCGValue, type="string")
            if type(eachMCGValue) == tuple:
                print "%s.%s %s Progressing" %(mentalcoreGlobalsName,eachMCGKey,eachMCGValue)
                print type(eachMCGValue)
        if eachMCGValue == "":
            cmds.setAttr("%s.%s"%(mentalcoreGlobalsName,eachMCGKey),"", type="string")
        
        #########################################################################
        # 10- set the setting of MentalCore Lens Data
        #########################################################################
    mentalcoreLensName = "mentalcoreLens"
    for eachMCLKey, eachMCLValue in mentalCoreLensDataDict.iteritems():
        if eachMCLValue != "":
            if type(eachMCLValue) == int:
                cmds.setAttr("%s.%s"%(mentalcoreLensName,eachMCLKey),eachMCLValue)
            if type(eachMCLValue) == bool:
                cmds.setAttr("%s.%s"%(mentalcoreLensName,eachMCLKey),eachMCLValue)
            if type(eachMCLValue) == str:
                cmds.setAttr("%s.%s"%(mentalcoreLensName,eachMCLKey),eachMCLValue, type="string")
            if type(eachMCLValue) == tuple:
                print "%s.%s %s Progressing" %(mentalcoreLensName,eachMCLKey,eachMCLValue)
                print type(eachMCLValue)
        if eachMCLValue == "":
            cmds.setAttr("%s.%s"%(mentalcoreLensName,eachMCLKey),"", type="string")
    return

    
def _cleanUp():
    cmds.editRenderLayerGlobals(currentRenderLayer='defaultRenderLayer')
    cmds.select(clear=True)
    listOfLayers = cmds.ls(type="renderLayer")
    cmds.select("defaultRenderLayer")
    for eachlayer in listOfLayers:
        if eachlayer != "defaultRenderLayer":
            cmds.delete(eachlayer)
    for eachPass in mapi.get_all_passes():
        cmds.delete(eachPass)
        
def _XML2Dictinary(pathToXML):
    '''
    convert all the XML Data to separate Dictionary
    '''
    tree = ET.parse(pathToXML)
    root = tree.getroot()
    
    weirdSign = ["'", "[", "(", "]", ")"]
    
    
    mentalCoreGlobalsDict = {}
    mentalCoreLensDataDict = {}
    mentalrayGlobalsDict = {}
    miDefaultOptionDict = {}
    allDicts = []
    numberDicts = [0,1,2,3]
    for eachNum in numberDicts: 
        generalDict = {}
        for child in root[eachNum]:
            valid = 1
            eachValue = child.attrib
            eachValue = eachValue['value']
            
            for eachSign in signs:
                if eachSign in eachValue:
                    eachValue = eachValue.replace(eachSign, "")
            if "," in eachValue:
                eachValue = eachValue.split(",")
            if type(eachValue) == list:
                listHolder = []
                for eachV in eachValue:
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
                generalDict[child.tag] = listHolder
            if type(eachValue) == str:
                for eachLetter in alphabet:
                    if eachLetter in eachValue:
                        valid = 0
                if eachValue != "":
                    if valid == 1:
                        if "." in eachValue:
                            eachValue = float(eachValue)
                        else:
                            eachValue = int(eachValue)
                if "True" == eachValue or "False" == eachValue:
                    eachValue = bool(eachValue)
                generalDict[child.tag] = eachValue
        allDicts.append(generalDict)
    mentalCoreGlobalsDict = allDicts[0]
    mentalCoreLensDataDict = allDicts[1]
    mentalrayGlobalsDict = allDicts[2]
    miDefaultOptionDict = allDicts[3]    
    
    layerDict = {} # [ASSOCIATED PASS], [ASSETS UNDER LAYER]
    for child in root[4]:
        layerValue = []
        for eachGrp in child:
            newAsset = []
            myDict = eachGrp.attrib
            myDict = myDict['value']
            if myDict != "":
                newDict = myDict.split('_iCommai_')
                for eachAsset in newDict:
                    eachAsset = eachAsset.split("'")[1]
                    newAsset.append(eachAsset)
            layerValue.append(newAsset)
        layerDict[child.tag] = layerValue
    
    mentalCorePassesDict = {} # [PASS TYPE],[ASSETS CONNECTED TO PASS],[{PASS SETTING}]
    for child in root[5]:
        passValue = []
        passSettingDict = {}
        for eachType in child:
            if eachType.tag == "passType":
                fixAttrib = eachType.attrib
                fixAttrib = fixAttrib['value']
                passValue.append(int(fixAttrib))
            
            if eachType.tag == "passConnected":
                newPassSetting = []
                fixAttrib = eachType.attrib
                fixAttrib = fixAttrib['value']
                if '_iCommai_' in fixAttrib: # Need to get ride of "_iCommai_"
                    fixAttrib = fixAttrib.split('_iCommai_')
                if type(fixAttrib) == list:
                    for eachAsset in fixAttrib: # Need to get ride of "u'"
                        if "'" in eachAsset:
                            eachAsset = eachAsset.split("'")[1]
                        newPassSetting.append(eachAsset)
                    passValue.append(newPassSetting)
                if type(fixAttrib) == str:
                    if "'" in fixAttrib:
                        fixAttrib = fixAttrib.split("'")[1]
                    newPassSetting.append(fixAttrib)
                    passValue.append(newPassSetting)
            
            if eachType.tag == "passSetting":
                for eachChildSetting in eachType:
                    valid = 1
                    fixAttrib = eachChildSetting.attrib
                    fixAttrib = fixAttrib['value']
                    if type(fixAttrib) == str:
                        for cleanup in weirdSign:
                            if cleanup in fixAttrib:
                                fixAttrib = fixAttrib.replace(cleanup, "")
                    for eachletter in alphabet:
                        if eachletter in fixAttrib:
                            valid = 0
                    if valid == 1:
                        if fixAttrib != "":
                            if "." in fixAttrib:
                                fixAttrib = float(fixAttrib)
                            else:                    
                                fixAttrib = int(fixAttrib)
                    if "False" == fixAttrib or "True" == fixAttrib:
                        fixAttrib = bool(fixAttrib)
                    passSettingDict[eachChildSetting.tag] = fixAttrib
                passValue.append(passSettingDict)
                
        mentalCorePassesDict[child.tag] = passValue
    print "Done"

    return  mentalCoreGlobalsDict,mentalCoreLensDataDict,mentalrayGlobalsDict,miDefaultOptionDict, layerDict, mentalCorePassesDict
    