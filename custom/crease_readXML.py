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

def readCreaseData(pathToXML = '', parentGrp = ''):
    
    tree = ET.parse(pathToXML)
    root = tree.getroot()
    
    debug(None, method = 'crease_readXML.readCreaseData', message = '{0:<10}{1}'.format('ASSETNAME: ',  root.tag), verbose = False)
    
    ## Now process the xml   
    geoToProcess = root.getchildren()
    if not geoToProcess:
        cmds.warning('THERE IS NO DATA WRITTEN TO FILE: %s' % pathToUVXML)
    else:
        ## Process each geos data now
        for eachGeo in geoToProcess:
            geo  = '%s%s' % (parentGrp, eachGeo.tag.replace('_iPipei_', '|'))
            debug(None, method = 'crease_readXML.readCreaseData', message = '{0:<10}{1}'.format('geo: ',  geo), verbose = False)
            
            edges = eachGeo.getchildren()
            debug(None, method = 'crease_readXML.readCreaseData', message = '{0:<10}{1}'.format('edges: ',  edges), verbose = False)
            for eachChild in edges:
                #print int(eachChild.tag.split('idx_')[-1])
                #print float(eachChild.attrib['value'].replace('_iPeriodi_', '.'))
                cmds.polyCrease('%s.e[%s]' % (geo, int(eachChild.tag.split('idx_')[-1])), e = True, v = float(eachChild.attrib['value'].replace('_iPeriodi_', '.')))
                