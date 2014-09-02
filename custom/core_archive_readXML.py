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

def readCoreData(pathToUVXML = '', parentGrp = ''):
    
    tree = ET.parse(pathToUVXML)
    root = tree.getroot()
    
    #debug(None, method = 'care_archive_readXML.readCoreData', message = '{0:<10}{1}'.format('ASSETNAME: ',  root.tag), verbose = False)
    if not cmds.objExists(root.tag):
        cmds.group(n = root.tag, em = True)
    
    ## CHeck for this assets core archive group
    if parentGrp:
        assetCoreArchive    = '|%s|%s|geo_hrc|%s_CORE_ARCHIVES_hrc' % (parentGrp, root.tag, root.tag)
    else:
        assetCoreArchive    = '%s|geo_hrc|%s_CORE_ARCHIVES_hrc' % (root.tag, root.tag)
    
    coreArchiveGroupName    = '%s_CORE_ARCHIVES_hrc' % root.tag

    

    if cmds.objExists(assetCoreArchive):
        try:
            cmds.delete(assetCoreArchive)
        except RuntimeError:
            pass

    ## Now build a fresh group
    cmds.group(n = coreArchiveGroupName, em = True)
    cmds.parent(coreArchiveGroupName, '%s|%s|geo_hrc' % (parentGrp, root.tag))
        
    ## Now process the rest of the xml   
    geoToProcess = root.getchildren()
    if not geoToProcess:
        cmds.warning('THERE IS NO DATA WRITTEN TO FILE: %s' % pathToUVXML)
    else:
        ## Process each geos data now
        for eachGeo in geoToProcess:
            coreData        = eachGeo.getchildren()
            path            = coreData[1].attrib['value'].replace('_iColoni_', ':').replace('_iFwdSlashi_', '/')
            translateData   = coreData[2].attrib['value'].split(' ')
            rotateData      = coreData[3].attrib['value'].split(' ')
            scaleData       = coreData[4].attrib['value'].split(' ')
            
            ## Get the parent group
            parent          = '%s_%s' % (root.tag, coreData[0].attrib['value'])
            if not cmds.objExists('%s|%s' % (assetCoreArchive, parent)):
                cmds.group(n = parent, em = True)
                cmds.parent('|%s' % parent, assetCoreArchive)

            ## Now process the GEO
            geoName         = '%s_%s' % (root.tag, eachGeo.tag.replace('_iPipei_', '|').split('|')[-1])
            longGeoName     = '%s|%s|%s' % (assetCoreArchive, parent, geoName)
            
            if not cmds.objExists(longGeoName):
                try:
                    cmds.group(n = geoName, em = True)
                    cmds.parent('|%s' % geoName, '%s|%s' % (assetCoreArchive, parent))
                except:
                    cmds.warning('Failed to create group for core archive, missing assets parent group!')
            
            cmds.setAttr('%s.translate' % longGeoName, float(translateData[0]), float(translateData[1]), float(translateData[2]))
            cmds.setAttr('%s.rotate' % longGeoName, float(rotateData[0]), float(rotateData[1]), float(rotateData[2]))
            cmds.setAttr('%s.scale' % longGeoName, float(scaleData[0]), float(scaleData[1]), float(scaleData[2]))
            cmds.setAttr('%s.scale' % longGeoName, float(scaleData[0]), float(scaleData[1]), float(scaleData[2]))
            if not cmds.objExists('%s.mcAssArchive' % longGeoName):
                cmds.addAttr(longGeoName, ln = 'mcAssArchive', dt = 'string')
            cmds.setAttr('%s.mcAssArchive' % longGeoName, path,  type = 'string')