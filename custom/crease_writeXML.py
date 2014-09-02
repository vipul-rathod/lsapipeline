import os, sys
import maya.cmds as cmds
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
    
def writeCreaseData(rootName = '', pathToXML = ''):
    """
    Function to write out crease data.
    """
    ## Delete existing
    if checkFilePath(pathToXML):
        os.remove(pathToXML)
    
    ## now process the data into the xml tree   
    root = Element(rootName)
    tree = ElementTree(root)
    
    ## process the scene's geo now...
    creaseDict = {}
    for eachMesh in cmds.ls(type = 'mesh'):
        getParent = cmds.listRelatives(eachMesh, parent = True, f = True)[0]
        edgeCount = cmds.polyEvaluate(eachMesh, e = True)
        
        for x in range(0, edgeCount):
            if cmds.polyCrease('%s.e[%s]' % (getParent, x), q = True, v = True)[0] != -1.0:
                getInfo = [x, cmds.polyCrease('%s.e[%s]' % (getParent, x), q = True, v = True)[0]]
                if not getParent in creaseDict.keys():
                    creaseDict[getParent] = []
                    creaseDict[getParent].append(getInfo)
                else:
                    if getInfo not in creaseDict[getParent]:
                        creaseDict[getParent].append(getInfo)
    
    ## Now process the dictionary into the xml tree
    for key, var in creaseDict.items():
        geoName = Element(str(key.replace('|', '_iPipei_')))
        root.append(geoName)
        if var: ## need a valid list of objects to write else just ignore the darn things...
            for each in var:
                creaseData = SubElement(geoName, 'idx_%s' % str(each[0]), value = str(each[1]).replace('.', '_iPeriodi_'))   
    
    tree.write(open(pathToXML, 'w'), encoding="utf-8")