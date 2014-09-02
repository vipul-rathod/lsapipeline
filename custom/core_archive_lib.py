"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db
"""
import os, getpass, sys
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
import shutil
from functools import partial
from debug import debug

## TANK STUFF
import sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
from tank import TankError

## MAYA STUFF
import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm

## METALCORE / XML STUF
try:
    from mentalcore import mapi
    from mentalcore import mlib
except:
    #debug(None, method = 'core_archive_lib', message = 'metalcore mapi and mlib failed to load!!', verbose = False)
    pass
import xml.etree.ElementTree as xml
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.dom import minidom
import tempfile
import gzip

## Now get the custom tools
import maya_genericSettings as settings
#reload(settings)

def deleteAllCores():
    for eachCore in cmds.ls(type ='core_archive'):
        cmds.delete(eachCore)

    ## Now delete the root cores as we don't need these anymore as they will be recreated at rebuild time
    if cmds.objExists('ROOT_ARCHIVES_DNT_hrc'):
        cmds.delete('ROOT_ARCHIVES_DNT_hrc')

def removePreppedArchives():
    MC = cmds.ls(type = 'core_archive')
    if MC:
        for each in MC:
            if each.endswith('_prepped'):
                cmds.delete(each)

def tagRootArchive():
    """
    Used to tag the imported core archives base geo when using the shotgun loader to load a core_archive
    """

    for eachArchive in cmds.ls(type ='core_archive'):
        okay = True
        listConns = cmds.listConnections(eachArchive)
        #debug(None, method = 'tagRootArchive', message = 'listConns: %s' % listConns, verbose = False)

        if cmds.objExists('%s.cleanedCore' % eachArchive):
            okay = False

        if okay:
            if cmds.nodeType(listConns[0]) == 'transform':
                eachGeo = cmds.listConnections(eachArchive)[0]
            else: ## it is an expression in [0] use [1] instead
                eachGeo = cmds.listConnections(eachArchive)[1]

            ## Delete existing attr
            if cmds.objExists('%s.coreRoot' % eachGeo):
                cmds.deleteAttr('%s.coreRoot' % eachGeo)

            cmds.addAttr(eachGeo, ln = 'coreRoot', at = 'bool')
            cmds.setAttr('%s.coreRoot' % eachGeo, 1)
            #debug(None, method = 'tagRootArchive', message = 'eachGeo tagged: %s' % eachGeo, verbose = False)
        else:
            pass

def _tagDuplicateCoreArchives():
    """
    Quick method to look for any duplciated core_archive transforms in the scene and to add an attr to each of these with the path of the archive used
    This tag gets used for rebuilding the archives
    """
    #debug(None, method = '_tagDuplicateCoreArchives', message = 'Tagging core archives now...', verbose = False)
    archives = cmds.ls(type = 'core_archive')

    #debug(None, method = '_tagDuplicateCoreArchives', message = 'archives: %s' % archives, verbose = False)
    for each in archives:
        getGeo = [eachGeo for eachGeo in cmds.listConnections(each) if cmds.nodeType(eachGeo) == 'transform' and ':' not in eachGeo]
        #debug(None, method = '_tagDuplicateCoreArchives', message = 'getGeo: %s' % getGeo, verbose = False)
        getFile = cmds.getAttr('%s.filename' % each)

        for eachGeo in getGeo:
            rootCore = False
            try:
                rootCore = cmds.getAttr('%s.coreRoot' % eachGeo)
            except:
                pass
            ## First make sure this is not a coreRoot geo. We only want to tag duplicated geo here.
            if not rootCore:
                ## Now if the tage doesn't exist add it
                if not cmds.objExists('%s.mcAssArchive' % eachGeo):
                    cmds.addAttr(eachGeo, ln = 'mcAssArchive', dt = 'string')
                    #debug(None, method = 'tagAssemblies', message = 'Tagged: %s' % eachGeo, verbose = False)

                ## Now set the tag to the file path
                cmds.setAttr('%s.mcAssArchive' % eachGeo, getFile, type = 'string')
                #debug(None, method = '_tagDuplicateCoreArchives', message = '\tstring: %s' % getFile, verbose = False)
    #debug(None, method = '_tagDuplicateCoreArchives', message = 'Finished', verbose = False)

def _stripRootArchiveTag(geo):
    """
    Func to remove the core attr from duplicated root cores
    """
    if cmds.objExists('%s.coreRoot' % geo):
        cmds.deleteAttr('%s.coreRoot' % geo)
        #debug(None, method = '_stripRootArchiveTag', message = 'Removed coreRoot attr from : %s' % geo, verbose = False)
    else:
        #debug(None, method = '_stripRootArchiveTag', message = 'NO coreRoot attr to remove from : %s' % geo, verbose = False)
        pass

def _setAllBBoxUpdatesOff():
    """
    This turns off the BBx update per frame, so that we can delete faces on the cores
    And not run into any errors
    """
    for each in cmds.ls(type = 'core_archive'):
        cmds.setAttr('%s.auto_bbox_update' % each, 0)

def _setAllToHold():
    """
    This sets the archives to HOLD so they render after being imported
    """
    for each in cmds.ls(type = 'core_archive'):
        cmds.setAttr('%s.outside_frames' % each, 1)

def _fixCoreArchiveName(core_archive):
    ## Check for the fucking number that keeps popping up regardless of how clean the scene is if you've deleted and wanted to start over
    if not core_archive.endswith('_CORE_Geoshader'):
        #debug(None, method = 'fixCoreArchiveName', message = 'BAD NAME FOUND!! FIXING NOW: %s' % each, verbose = False)
        cmds.rename(core_archive, '%s_CORE_Geoshader' % each.split('_')[0])
        each = '%s_CORE_Geoshader' % each.split('_')[0]
    else:
        each = core_archive

    return each

def cleanPaintedArchives():
    """
    Used after a paint of a landscape.
    This cleans up all the duplicated core_archives in the scene
    This re-attaches all the duplicates back to the master core_archive so they render correctly.
    This cleans up the placements of the archives into the placements_hrc group
    """
    getArchives = cmds.ls(type = 'core_archive')
    duplicatedCA = []    ## this holds ALL the duplicated geo

    if not getArchives:
        cmds.warning('cleanPaintedArchives requires core_archives to be present in the scene!')
        return -1
    else:
        ###############################################
        ############FIRST PASS#########################
        ## SCAN ROOT_ARCHIVES_DNT_hrc FOR DUPLICATES
        ###############################################
        ############SECOND PASS########################
        ## SCAN ROOT_ARCHIVES_DNT_hrc AND CORE_ARCHIVES_hrc

    #####################PROCESS THE MAIN SCENE NOW AND BUILD THE DUPLICATES LIST
        if not cmds.objExists('CORE_ARCHIVES_hrc'):
            ## this is the first time this tool has been run. All the duplicated geo should exist under ROOT_ARCHIVES_DNT_hrc
            ## all duplicated geo won't have a clean _geo suffix so we're searching for those.
            [duplicatedCA.extend([eachChild]) for eachChild in cmds.listRelatives('ROOT_ARCHIVES_DNT_hrc') if not eachChild.endswith('_geo') and eachChild not in duplicatedCA]
            #===================================================================
            # for eachChild in cmds.listRelatives('ROOT_ARCHIVES_DNT_hrc'):
            #     if not eachChild.endswith('_geo') and eachChild not in duplicatedCA:
            #         duplicatedCA.extend([eachChild])
            #===================================================================
            cmds.group(n = 'CORE_ARCHIVES_hrc', em = True)

        else:
            ## This is being run over a scene with existing core archive bases and duplicate so we have have to be very careful here..
            ## we have duplicated cores in the scene with cleaned up duplicates
            ## this means we have coreRoot attrs on duplicated geo and on the base cores.
            ## since all the duplicated geos should be in the ROOT_ARCHIVES_DNT_hrc
            try:[duplicatedCA.extend([eachChild]) for eachChild in cmds.listRelatives('ROOT_ARCHIVES_DNT_hrc') if not eachChild.endswith('_geo')]
            except:pass
            #===================================================================
            # for eachChild in cmds.listRelatives('ROOT_ARCHIVES_DNT_hrc'):
            #     if not eachChild.endswith('_geo'):
            #         duplicatedCA.extend([eachChild])
            #===================================================================

            ## NOW SCAN FOR EXISTING DUPLICATES IN  CORE_ARCHIVES_hrc
            try:
                [[duplicatedCA.extend([eachChild]) for eachChild in cmds.listRelatives(eachChildGrp)] for eachChildGrp in cmds.listRelatives('CORE_ARCHIVES_hrc')]
            except ValueError:
                ## we have more than one coreArchive group
                getCoreArchiveGroups = cmds.ls('CORE_ARCHIVES_hrc')
                for eachGrp in getCoreArchiveGroups:
                    [[duplicatedCA.extend([eachChild]) for eachChild in cmds.listRelatives(eachChildGrp)] for eachChildGrp in cmds.listRelatives(eachGrp)]
            #===================================================================
            # for eachChildGrp in cmds.listRelatives('CORE_ARCHIVES_hrc'):
            #     for eachChild in cmds.listRelatives(eachChildGrp):
            #         duplicatedCA.extend([eachChild])
            #===================================================================

        #debug(None, method = 'cleanPaintedArchives', message = 'duplicatedCA: %s' % duplicatedCA, verbose = False)

        ## Strip the duplicated attr
        #debug(None, method = 'cleanPaintedArchives', message = 'Stripped archiveTags...', verbose = False)
        [_stripRootArchiveTag(eachDup) for eachDup in duplicatedCA]

    #####################PROCESS THE CORE ARCHIVE NAMES TO CHECK AGAINST
        #debug(None, method = 'cleanPaintedArchives', message = 'Getting clean core names...', verbose = False)
        coresNameCleaned = []
        ## Get the base name for the core_archive
        ## gives us LIBBBBLargeTree01CArch_CORE
        [coresNameCleaned.extend([each.split('_CORE_Geoshader')[0]]) for each in getArchives]

    #####################PROCESS THE DUPLICATES NOW
        ## Now build and parent into a clean duplicate group for each duplicated core_archive
        #debug(None, method = 'cleanPaintedArchives', message = 'Processing duplicate list for core_archives now...', verbose = False)
        for eachCleanName in coresNameCleaned:
            #debug(None, method = 'cleanPaintedArchives', message = 'eachCleanName: %s' % eachCleanName, verbose = False)
            geoToParent = []
            duplicateGroup = '%s_Archives_hrc' % eachCleanName
            #debug(None, method = 'cleanPaintedArchives', message = 'duplicateGroup: %s' % duplicateGroup, verbose = False)

            ## BUILD THE DUPLICATE GROUP
            if not cmds.objExists(duplicateGroup):
                cmds.group(name = duplicateGroup, empty = True)

            ## Now process the actual geo to put into the group
            #debug(None, method = 'cleanPaintedArchives', message = 'duplicatedCA: %s' % duplicatedCA, verbose = False)
            if duplicatedCA:
                [geoToParent.extend([eachGeo]) for eachGeo in duplicatedCA if eachCleanName in eachGeo]
            #debug(None, method = 'cleanPaintedArchives', message = 'geoToParent: %s' % geoToParent, verbose = False)

            ## Now process the core_archives specific geo
            if geoToParent: ## If there IS any geo?!
                ## Now put the transforms into the duplicate group
                [cmds.parent(eachGeo, duplicateGroup) for eachGeo in geoToParent if cmds.listRelatives(eachGeo, parent = True)[0] != duplicateGroup]
                #===============================================================
                # for eachGeo in geoToParent:
                #     ## Now check the parent of the transform...
                #     if cmds.listRelatives(eachGeo, parent = True)[0] != duplicateGroup:
                #         cmds.parent(eachGeo, duplicateGroup)
                #===============================================================

                ## RENUMBER the duplicates now....
                _renumberDuplicated(duplicateGroup, '%s_CORE_Geoshader' % eachCleanName)
                ## RECONNECT them to the core_Archive now...
                _reconnectDuplicates(duplicateGroup, '%s_CORE_Geoshader' % eachCleanName)

            else:
                cmds.warning('No duplicated paint geo found for %s' % duplicateGroup)
                ## Remove the group because we don't need it if it is empty
                if not cmds.listRelatives(duplicateGroup, children = True):
                    cmds.delete(duplicateGroup)

            ## Now parent the duplicateGroup to the CORE_ARCHIVES_hrc group
            if cmds.objExists(duplicateGroup):
                if cmds.listRelatives(duplicateGroup, parent = True):
                    if cmds.listRelatives(duplicateGroup, parent = True)[0] != 'CORE_ARCHIVES_hrc':
                        cmds.parent(duplicateGroup, 'CORE_ARCHIVES_hrc')
                else:
                    cmds.parent(duplicateGroup, 'CORE_ARCHIVES_hrc')

        ## Now parent the grps properly
        _cleanupCoreArchiveRebuildGrps()

def _reconnectDuplicates(baseGrp = '', core_archive = ''):
    """
    used to renumber the transforms in a duplicate group
    @param baseGrp: Name of the duplicate group to renumber the children of
    @type baseGrp: String
    """
    ## Fetch the Geo Shaders
    ## Now reconnect
    getCoreConnections = cmds.listConnections('%s.message' % core_archive, plugs = True)
    #print getCoreConnections

    if not cmds.objExists(core_archive):
        cmds.warning('_reconnectDuplicates needs a valid core_archive to work!!\n\t%s is invalid!' % core_archive)
    else:
        for eachChild in cmds.listRelatives(baseGrp, children = True):
            if '%s.miGeoShader' % eachChild not in getCoreConnections:
                cmds.connectAttr('%s.message' % core_archive, '%s.miGeoShader' % eachChild, force = True)

def _renumberDuplicated(baseGrp = '', core_archive = ''):
    """
    used to renumber the transforms in a duplicate group
    @param baseGrp: Name of the duplicate group to renumber the children of
    @type baseGrp: String
    """
    #debug(None, method = '_renumberDuplicated', message = 'Renumbering...', verbose = False)
    ## First rename all with _dup to avoid clashing on reanme
    for eachChild in cmds.listRelatives(baseGrp, children = True):
        cmds.rename(eachChild, '%s_dup' % eachChild)

    ## Now (re)process all the duplicates in the group with unique names and correct numbering
    x = 0
    padding = ''
    for eachChild in cmds.listRelatives(baseGrp, children = True, f = True):
        newName = core_archive.split('_CORE_Geoshader')[0]
        if x < 100:
            pad = '0'
        elif x < 10:
            pad = '00'
        else:
            pad = ''
        cmds.rename(eachChild, '%s_%s%s_geo' % (newName.split('|')[-1], pad, x))
        #debug(None, method = '_renumberDuplicated', message = 'newName: %s' % '%s_%s%s_geo' % (newName.split('|')[-1], pad, x), verbose = False)
        x = x + 1

def cleanupPlacements():
    """
    Put all the placement nodes in the scene into a placments_hrc group
    """
    ## cleanup all placements
    deadParents = []
    getPlacements = cmds.ls(type = 'place3dTexture')
    if not cmds.objExists('|placements_hrc'):
        cmds.group(n = '|placements_hrc', em = True)

    ## Now look for placements not already a child of placments_hrc and parent them to placements_hrc
    for eachPlce in getPlacements:
        getParent = cmds.listRelatives(eachPlce, parent = True, fullPath = True)
        if getParent:
            if getParent[0] != '|placements_hrc':
                ## now get the actual parent if there is one and put it into the deadParents group
                deadParents.append(getParent[0])

                try:
                    cmds.parent(eachPlce, '|placements_hrc')
                except ValueError:
                    pass
                except RuntimeError:
                    pass
        else:
            try:
                cmds.parent(eachPlce, '|placements_hrc')
            except ValueError:
                pass

    ## Now remove all the placements groups that no longer have children
    if deadParents:
        cmds.delete(deadParents)

def cleanMaterialNS():
    """
    This is a namespace cleaner for the materials of the core_archives in the scene.
    NOTE: If we remove ALL namespaces from the scene the core archives render without materials!!!!
    """
    ## Now remove all the nameSpaces!! This is to remove any clashes with the core_assemblies later on...
    safeNS = ['UI', 'shared']
    getAllNameSpaces = cmds.namespaceInfo(listOnlyNamespaces = True)
    for eachNS in getAllNameSpaces:
        if eachNS not in safeNS:
            try:
                for eachNS in cmds.namespaceInfo(eachNS, listNamespace = True):
                    if 'materials' in eachNS:
                        try:
                            cmds.namespace(removeNamespace = eachNS, mergeNamespaceWithRoot = True)
                        except RuntimeError:
                            pass
            except TypeError:
                pass

def cleanupDeadCoreArchives():
    """
    Quick method for searching for core_archives that only have an expression attached and nothing else = dead archive.
    This removes the expression and the archive from the scene and then preforms a cleanup on the shaders to get rid of any dead shading networks in the scene
    """
    for each in cmds.ls(type = 'core_archive'):
        if len(cmds.listConnections(each)) == 1:
            if cmds.nodeType(cmds.listConnections(each)[0]) == 'expression':
                cmds.delete(cmds.listConnections(each)[0])
                cmds.delete(each)
                #debug(None, method = 'cleanupDeadCoreArchives', message = 'Deleted:%s' % each, verbose = False)

                ## Now remove all the nameSpaces!! This is to remove any clashes with the core_assemblies later on...
                safeNS = ['UI', 'shared']
                getAllNameSpaces = cmds.namespaceInfo(listOnlyNamespaces = True)
                for eachNS in getAllNameSpaces:
                    if eachNS not in safeNS:
                        try:
                            for eachNS in cmds.namespaceInfo(eachNS, listNamespace = True):
                                if each in eachNS:
                                    try:
                                        cmds.namespace(removeNamespace = eachNS, mergeNamespaceWithRoot = True)
                                    except RuntimeError:
                                        pass
                        except TypeError:
                            pass

    mel.eval("MLdeleteUnused();")

def cleanupCoreArchiveImports():
    """
    Method for cleaning up all the coreArchives after importing.
    This;
    - strips the namespaces of the main core_archive but leaves the children with their namespace so they can still render!
    - renames the Geoshaders correctly
    - renames the expressions to something clean
    """

    ## tag the base geo now
    tagRootArchive()

    ## Now process the archives
    for eachCoreArchive in cmds.ls(type ='core_archive'):
        removeNS = eachCoreArchive.split(':')[0]
        #debug(None, method = 'cleanupCoreArchiveImports', message = 'removeNS: %s' % removeNS, verbose = False)

        getConn = cmds.listConnections(eachCoreArchive)
        #debug(None, method = 'cleanupCoreArchiveImports', message = 'ORIGINAL getConn: %s' % getConn, verbose = False)
        if getConn:
            for eachConn in getConn:
                ## Cleanup the top level geo name but leave the children with the correct namespace
                if cmds.nodeType(eachConn) == 'transform':
                    if ":" in eachConn:
                        if 'Archive' in eachConn:
                            ## strip the namespace but make the namespace the name!
                            if not cmds.objExists('%s_geo' % eachConn.split(':')[0]):
                                cmds.rename(eachConn, '%s_geo' % eachConn.split(':')[0])
                                #debug(None, method = 'cleanupCoreArchiveImports', message = 'Renamed %s to %s' % (eachConn, '%s_geo' % eachConn.split(':')[0]), verbose = False)
                            else:
                                #debug(None, method = 'cleanupCoreArchiveImports', message = 'SKIPPING rename as %s already exists in scene!!' % '%s_geo' % eachConn.split(':')[0], verbose = False)
                                pass
                        else:
                            ## The sub nodes strip the namespace
                            ## YOU MUST NOT STRIP THESE FUCKING NAME SPACES!!! OR THE SHADERS STOP WORKING
                            #cmds.rename(eachConn, '%s' % eachConn.split(':')[-1])
                            pass

        ## Now rename the core_archive
        if not eachCoreArchive.endswith('_Geoshader'):
            cmds.rename(eachCoreArchive, '%s_Geoshader' % removeNS)
            eachCoreArchive = '%s_Geoshader' % removeNS
            #debug(None, method = 'cleanupCoreArchiveImports', message = 'Renamed core_archive: %s to %s' % (eachCoreArchive, '%s_Geoshader' % removeNS), verbose = False)

        #debug(None, method = 'cleanupCoreArchiveImports', message = 'eachCoreArchive: %s' % eachCoreArchive, verbose = False)
        ## Now cleanup the expression names
        if getConn:
            for eachConn in getConn:
                try:## Try here because the rename will make the geo not exist anymore...
                    if cmds.nodeType(eachConn) == 'expression':
                        if eachConn != '%s_exp' % eachCoreArchive:
                            cmds.rename(eachConn, '%s_exp' % eachCoreArchive)
                            #debug(None, method = 'cleanupCoreArchiveImports', message = 'Renamed core_archive: %s to %s' % (eachConn, '%s_exp' % eachCoreArchive), verbose = False)
                except RuntimeError:
                    pass

        ## Now parent the base geo to the master group
        ## Note if the group exists all the cores should already be grouped correctly so we shouldn't have to process this again.
        if not cmds.objExists('ROOT_ARCHIVES_DNT_hrc'):
            cmds.group(n = 'ROOT_ARCHIVES_DNT_hrc', em = True)

        ## Now after renaming grab the connections again as a means of freshing the list
        getConn = cmds.listConnections(eachCoreArchive)
        #debug(None, method = 'cleanupCoreArchiveImports', message = 'REFRESHED getConn: %s' % getConn, verbose = False)

        for eachConn in getConn:
            ##Check here that the [0] isn't an expression if it is use 1 instead of 0
            if cmds.nodeType(eachConn) == 'transform':
                #debug(None, method = 'cleanupCoreArchiveImports', message = 'Expression found! Trying .. getConn[1]: %s' % getConn[1], verbose = False)
                if cmds.objExists('%s.coreRoot' % eachConn):
                    if cmds.listRelatives(eachConn, parent = True) != 'ROOT_ARCHIVES_DNT_hrc':
                        try:
                            cmds.parent(eachConn, 'ROOT_ARCHIVES_DNT_hrc')
                        except RuntimeError:
                            pass

        ## Now add an attr to the core_archive to let us know it's been cleaned already and shouldn't be cleaned again
        if not cmds.objExists('%s.cleanedCore' % eachCoreArchive):
            cmds.addAttr(eachCoreArchive, ln = 'cleanedCore', at = 'bool')
            cmds.setAttr('%s.cleanedCore' % eachCoreArchive, 1)

        ## Now clean up the materials namespaces
        cleanMaterialNS()

        ## Now put the placements into placements_hrc
        cleanupPlacements()

        ## Now cleanup the groups
        ## _cleanupCoreArchiveRebuildGrps('geo_hrc')

    #debug(None, method = 'cleanupCoreArchiveImports', message = 'Finished', verbose = False)

def _cleanupCoreArchiveRebuildGrps(parentTO = 'geo_hrc'):
    """
    Put all the rebuilt archives under a specified node in the scene
    @param parentTO: Name of the group to put the rebuild groups under
    @type parentTO: String
    """
    ## Check parentTo actually exists in the scene, if not build a group
    if len(cmds.ls(parentTO)) > 1:
        cmds.warning('There is more than one %s in scene, adding prefix now...' % parentTO)
        parentTO = 'unique_%s' % parentTO

    if not cmds.objExists(parentTO):
        cmds.group(n = parentTO, em = True)

    groups = ['CORE_ARCHIVES_hrc', 'ROOT_ARCHIVES_DNT_hrc']
    ## Now parent the groups to the parentTo group
    for each in groups:
        try:
            cmds.parent(each, parentTO)
        except:
            pass

    ## Now we want placements not to be under geo_hrc so find the parent of geo_hrc and parent placements_hrc ot that instead
    if parentTO == 'geo_hrc':
        getRoot = cmds.listRelatives('geo_hrc', parent = True)[0]
        try:
            cmds.parent('placements_hrc', getRoot)
        except:
            pass
    else:
        pass

def makeCoresSafeForExport():
    MC = cmds.ls(type = 'core_archive')
    ignoreAssemblies = []
    finalShadedGeo = []
    ## Look for archives connections *geo* and add them to the ignoreAssemblies
    ## Build a connection node for the archives and hook them up so they don't get deleted
    if MC:
        for each in MC:
             ignoreAssemblies = ignoreAssemblies + cmds.listConnections(each)
        # If safe node already exists, delete it.
        if cmds.objExists('core_safe'):
            cmds.delete('core_safe')
        # Create a filter node and connect arbitrary connection to it
        createTempNode = cmds.createNode('objectTypeFilter', name = 'core_safe')
        for eachCore in MC:
            addAlphaAttr = cmds.addAttr(createTempNode, longName = 'core_%s' % '_'.join(eachCore.split(":")) , attributeType = 'double')
            cmds.connectAttr('%s.caching' % eachCore, '%s.core_%s' % (createTempNode, '_'.join(eachCore.split(":"))), force = True)

def prepArchivesForPublish(defaultSHD = True):
    """
    Now delete and clean up all archive geo that will get broken during publish so we don't publish all the unnecesasry crap
    Now get the children in the archives as we want to delete these as they are rebuilt during lighting setup
    """
    #debug(None, method = 'prepArchivesForPublish', message = 'Processing cleanup of archives for export now....', verbose = False)
    getChildren = []
    assignDefaultSHD = []
    MC = cmds.ls(type = 'core_archive')
    allCoreArvices = []

    if MC:
        ## Look for coreArchive geo and create a list of these to check against
        archiveList = []
        for each in MC:
            MCConnGeo = cmds.listConnections(each)
            [archiveList.extend([eachGeo]) for eachGeo in MCConnGeo if cmds.nodeType(eachGeo) == 'transform']

        #debug(None, method = 'prepArchivesForPublish', message = 'archiveList:%s' % archiveList, verbose = False)
        for eachArchive in archiveList:
            #debug(None, method = 'prepArchivesForPublish', message = 'Fetching children now...', verbose = False)
            [getChildren.extend([eachChild]) for eachChild in cmds.listRelatives(eachArchive, children = True, shapes= False, parent =False, f = True) if cmds.nodeType(eachChild) != 'mesh']

            #debug(None, method = 'prepArchivesForPublish', message = 'Fecthing base geo for default shader...', verbose = False)
            [assignDefaultSHD.extend([eachChild]) for eachChild in cmds.listRelatives(eachArchive, children = True, shapes= False, parent =False, f = True) if cmds.nodeType(eachChild) == 'mesh']

        #debug(None, method = 'prepArchivesForPublish', message = 'getChildren:%s' % getChildren, verbose = False)
        if getChildren:
            cmds.delete(getChildren)
        #debug(None, method = 'prepArchivesForPublish', message = 'Deleted all children of base archive transforms..', verbose = False)

        if defaultSHD:
            for each in assignDefaultSHD:
                try:
                    cmds.sets(each, e = True , forceElement = 'initialShadingGroup')
                except:
                    pass
            #debug(None, method = 'prepArchivesForPublish', message = 'Assigned default lambert to all archives...', verbose = False)

        for eachArchive in MC:
            if not eachArchive.endswith('_prepped'):
                cmds.rename(eachArchive, '%s_prepped' % eachArchive)
                #debug(None, method = 'prepArchivesForPublish', message = 'Renaming to prepped %s' % eachArchive, verbose = False)

        ## Now make sure the cores are hooked up to something becasuse their base geo will be gone!!
        ## makeCoresSafeForExport()

        ## Now make sure everything is groups correctly
        _cleanupCoreArchiveRebuildGrps(parentTO = 'geo_hrc')

        #shapesToDelete = [each for each in cmds.listRelatives('CORE_ARCHIVES_hrc', ad = True) if cmds.nodeType(each) == 'mesh']
        #cmds.delete(shapesToDelete)

    else:
        #debug(None, method = 'prepArchivesForPublish', message = 'No archives found to process...', verbose = False)
        pass
    #debug(None, method = 'prepArchivesForPublish', message = 'Finished', verbose = False)

def loadCoreArchives(paths=[], app = None):
    """
    load core archives in from their paths
    @param paths: list of paths including the file name and ext .mi
    @type paths: List
    """
    #debug(app = app, method = 'loadAssemblees', message = 'Entering loadCoreArchives...', verbose = False)
    [load_archive(path = eachPath) for eachPath in paths]
    #debug(app = app, method = 'loadAssemblees', message = 'All archives loaded successfully...', verbose = False)

    return True

    # ## Remove core unused faces
    # ## Faces in these are really just for holding the material information anyway.
    # import maya.api.OpenMaya as om
    # try:
    #     cores       = om.MGlobal.getSelectionListByName('*CArch_CORE:Archive*')
    #     myList      = om.MSelectionList(cores)
    #     for x in range(0, myList.length()):
    #         myObj   = om.MFnMesh(myList.getDagPath(x))
    #
    #         for x in range(0, 4):
    #             id = 1
    #             try:myObj.deleteFace(id)
    #             except:pass
    #         #now do the same for each child
    #         getChildren = [each for each in cmds.listRelatives(cmds.listRelatives(myObj.name(), p=True), children = True) if 'Shape' not in each and each != myObj.name()]
    #
    #         for each in getChildren:
    #             matGeo      = om.MGlobal.getSelectionListByName(each)
    #             myList2     = om.MSelectionList(matGeo)
    #             myChildObj  = om.MFnMesh(myList2.getDagPath(0))
    #
    #             for x in range(1, 4):
    #                 id = 1
    #                 try:myChildObj.deleteFace(id)
    #                 except:pass
    #     return True
    # except Exception, e:
    #     cmds.warning('Can not find any core archives in the scene!!! You must have valid transforms to process! Rebuild from xml now...\n%s' % e)
    #     return False

def getCorePaths(app = None):
    """
    Looks at all the tagged core_archives inthe scene and gets the path to their core_archive on disk from the attr set on the transform
    @param app: used for debugging if there is a shotgun application you can send this through to the debugger, use None for prints.
    @type app: None or a valid Shotgun application class
    """
    #debug(app = app, method = 'getCorePaths', message = 'Entering getCorePaths..', verbose = False)
    paths = []
    ## get all the geo with the mcAssArchive attr
    getGeo = [eachGeo for eachGeo in cmds.ls(type = 'transform') if cmds.objExists('%s.mcAssArchive' % eachGeo)]
    ## Add the file path to the paths list
    [paths.append(cmds.getAttr(each + '.mcAssArchive')) for each in getGeo if cmds.getAttr(each + '.mcAssArchive') not in paths]
    #debug(app = app, method = 'getCorePaths', message = 'paths... %s' % paths, verbose = False)
    return paths

def load_archive(path='', archive_node=None, app = None):
    '''
    !!!!!!!!!!!STOLEN FROM CORE MENTALCORE CODE mapi file!!!!!!!!!!!!!

    Loads a archive in the current scene from the specified archive file.
    If it file belongs the a sequence, the sequence is automatically loaded.

    @param app: Used for debugging if there is a shotgun application you can send this through to the debugger, use None for prints.
    @param path: The path to a archive file.
    @param archive_node:  Instead of creating a new archive node, you can specify the name of a existing node to load the archive onto.
    @type app: shotgun application class or None
    @type path: string
    @type archive_node: string
    '''
    # -------------------------
    # Get archive info
    #debug(app = app, method = 'load_archive', message = 'Entering load_archive..', verbose = False)
    #debug(app = app, method = 'load_archive', message = 'path:... %s'  % path, verbose = False)
    #debug(app = app, method = 'load_archive', message = 'archive_node:... %s'  % archive_node, verbose = False)

    archive_info = mapi.get_archive_info(path)
    #debug(app = app, method = 'load_archive', message = 'archive_info:... %s'  % archive_info, verbose = False)
    #debug(app = app, method = 'load_archive', message = 'archive_info[name]:... %s'  % archive_info['name'], verbose = False)

    getAllArchives = cmds.ls(type = 'core_archive')

    ## Perform a full impor again, Note you shouldn't run this script without first cleaning the scene properly!!!
    # Create new archive shader and proxy geo
    # -------------------------
    # Create namespace
    ns = archive_info['name']
    i = 1
    while pm.namespace(exists=ns):
        ns = archive_info['name'] + str(i)
        i += 1
    ns = pm.namespace(add=ns) + ':'
    #debug(app = app, method = 'load_archive', message = 'ns...%s' % ns, verbose = False)
    # -------------------------
    # Create proxy geo
    proxy = pm.polyCube(w=1, h=1, d=1, sx=1, sy=1, sz=1, ch=False, n='%sArchive' % ns)[0]

    # -------------------------
    # Create geo shader
    archive_node = pm.createNode('core_archive', ss=True, n='%sGeoshader' % ns)

    archive_node.attr('filename').set(archive_info['filename'])

    archive_node.attr('outside_frames').set(1)

    archive_node.attr('auto_bbox_update').set(0)

    if archive_info.has_key('start_frame'):
        archive_node.attr('start_frame').set(archive_info['start_frame'])

    if archive_info.has_key('end_frame'):
        archive_node.attr('end_frame').set(archive_info['end_frame'])

    pm.expression(s='%s.frame=frame' % archive_node)

    # ----------------------------------
    # Connect to proxy
    proxy.attr('miExportGeoShader').set(True)
    archive_node.attr('message') >> proxy.attr('miGeoShader')

    # ----------------------------------
    # Import Materials
    cleanPath = '/'.join(path.split('/')[0:-1])
    #debug(app = app, method = 'load_archive', message = 'cleanPath... %s' % cleanPath, verbose = False)
    #I:/lsapipeline/fx/assemblies/treeSmallPoint_C.mi.gz
    material_path = os.path.join(os.path.dirname(path), '%s_materials.ma' % archive_info['name'])
    #debug(app = app, method = 'load_archive', message = 'material_path... %s' % material_path, verbose = False)
    xml_path = os.path.join(os.path.dirname(path), '%s_materials.xml' % archive_info['name'])
    #debug(app = app, method = 'load_archive', message = 'xml_path... %s' % xml_path, verbose = False)

    if os.path.exists(material_path) and os.path.exists(xml_path):
        # Import materials
        #debug(app = app, method = 'load_archive', message = 'IMPORTING MATERIALS FOR...%s' % archive_node, verbose = False)
        import_archive_materials(archive_node)
    else:
        #debug(app = app, method = 'load_archive', message = 'FAILED!!!!: XML OR MA', verbose = False)
        print 'MentalCore(): Materials import skipped, could not find materials xml and/or ma file!'

    # ----------------------------------
    # Update bounding box
    #debug(app = app, method = 'load_archive', message = 'Updating bounding box', verbose = False)
    mapi.update_archive_bbox(str(archive_node))
    #debug(app = app, method = 'load_archive', message = 'Bounding box updated', verbose = False)

    #debug(app = app, method = 'load_archive', message = 'loadArchive FINISHED %s' % archive_info['name'], verbose = False)
    #debug(app = app, method = 'load_archive', message = '=============================NEXT========================', verbose = False)

def create_material_reference(name='', parent='', sg=None, app = ''):
    '''
    !!!!!!!!!!!STOLEN FROM CORE MENTALCORE CODE mapi file!!!!!!!!!!!!!

    Create an empty mesh and apply a material to it to force it to be exported by mentalray
    '''
    #debug(app = app, method = 'create_material_reference', message = 'Entering create_material_reference..', verbose = False)
    oldSel = pm.ls(sl= True)
    cube = pm.polyCube( w=0.00001, h=0.00001, d=0.00001, sx=1, sy=1, sz=1, ax=[0,1,0], cuv=4, ch=0 )
    #debug(app = app, method = 'create_material_reference', message = 'Cube built... %s' % cube[0],  verbose = False)
    if sg:
        pm.sets( sg, e=True, forceElement=cube[0] )
        #debug(app = app, method = 'create_material_reference', message = 'Material %s assigned...' % sg,  verbose = False)
    pm.parent(cube[0], parent)
    pm.rename(cube[0], name)
    #debug(app = app, method = 'create_material_reference', message = '%s built...' % cube[0],  verbose = False)
    return cube[0]

def import_archive_materials(archive_node='', app = ''):
    '''
    !!!!!!!!!!!STOLEN FROM CORE MENTALCORE CODE mapi file!!!!!!!!!!!!!

    Import materials for the archive and create material reference objects.
    This imports a ma file containing the materials and read the xml material assignments file to build material reference objects
    and connect them to the archive geoshader. The materials ma and xml file must live in the same folder as the archive is located.

    Arguments:
        archive_node (string) - The archive node to load materials and reference objects for.
    '''
    #debug(app = app, method = 'import_archive_materials', message = 'Entering import_archive_materials..', verbose = False)
    # ----------------------------------
    # Store selection
    sel = pm.ls(sl= True)

    # -------------------------
    # Get archive path
    archive_node = pm.PyNode(archive_node)
    #debug(app = app, method = 'import_archive_materials', message = 'archive_node..%s' % archive_node, verbose = False)

    archive_path = pm.getAttr('%s.filename' % archive_node)
    #debug(app = app, method = 'import_archive_materials', message = 'archive_path..%s' % archive_path, verbose = False)

    if not archive_path:
        raise Exception, '%s has no filename specified!' % archive_node

    # -------------------------
    # Get archive info
    project_dir = os.path.normpath(pm.workspace(query=True, rd= True)).replace('\\','/') + '/'
    archive_name = os.path.basename(archive_path).split('.')[0]
    archive_dir = os.path.dirname(archive_path)
    #debug(app = app, method = 'import_archive_materials', message = 'project_dir..%s' % project_dir, verbose = False)
    #debug(app = app, method = 'import_archive_materials', message = 'archive_name..%s' % archive_name, verbose = False)
    #debug(app = app, method = 'import_archive_materials', message = 'archive_dir..%s' % archive_dir, verbose = False)

    # Check if archive dir is relative
    if not os.path.exists(archive_dir):
        temp_archive_dir = project_dir + archive_dir
        if os.path.exists(temp_archive_dir):
            archive_dir = temp_archive_dir

    ma_path = os.path.join(archive_dir, '%s_materials.ma' % archive_name)
    xml_path = os.path.join(archive_dir, '%s_materials.xml' % archive_name)
    #debug(app = app, method = 'import_archive_materials', message = 'ma_path..%s' % ma_path, verbose = False)
    #debug(app = app, method = 'import_archive_materials', message = 'xml_path..%s' % xml_path, verbose = False)
    # -------------------------
    # Check materials paths
    if not os.path.exists(ma_path):
        #debug(app = app, method = 'import_archive_materials', message =  'Materials file does not exist! %s' % ma_path, verbose = False)
        raise Exception, 'Materials file does not exist! %s' % ma_path

    if not os.path.exists(xml_path):
        #debug(app = app, method = 'import_archive_materials', message =  'Materials file does not exist! %s' % xml_path, verbose = False)
        raise Exception, 'Materials assignment file does not exist! %s' % xml_path

    # -------------------------
    # Get archive object
    archive_object = pm.listConnections(archive_node, type='transform', s=False, d= True)
    #debug(app = app, method = 'import_archive_materials', message = 'archive_object..%s' % archive_object, verbose = False)
    if not archive_object:
        #debug(app = app, method = 'import_archive_materials', message = '%s must be connected to a object as a geoshader' % archive_node, verbose = False)
        raise Exception, '%s must be connected to a object as a geoshader' % archive_node

    archive_object = archive_object[0]
    #debug(app = app, method = 'import_archive_materials', message = 'archive_object..%s' % archive_object, verbose = False)

    # -------------------------
    # Import materials
    imported_materials = pm.importFile(ma_path, namespace='%s:materials' % archive_name, returnNewNodes= True)
    #debug(app = app, method = 'import_archive_materials', message = 'Materials imported successfully..', verbose = False)
    # Get namespace from imported materials
    mat_ns = ''
    if imported_materials:
        mat_ns = ':'.join(str(imported_materials[0]).split(':')[:2]) + ':'

    #debug(app = app, method = 'import_archive_materials', message = 'mat_ns.. %s' % mat_ns, verbose = False)

    # -------------------------
    # Prase xml and build list of objects and materials
    xml_doc = xml.parse( xml_path )
    object_list = []
    object_material_map = {}

    for sg_node in xml_doc.findall( 'SG' ):
        sg = sg_node.text.strip()
        for obj_node in sg_node.getchildren():
             obj = obj_node.text.strip()
             object_list.append(obj)
             object_material_map[obj] = '%s%s' % (mat_ns, sg)

    object_list.sort()

    # -------------------------
    # Create ref object namespace
    archive_object_split = str(archive_object).split(':')
    if len(archive_object_split) > 1:
        ns = ':'.join(archive_object_split[:-1])
    else:
        ns = archive_name

    ns = '%s:ref' % ns
    #debug(app = app, method = 'import_archive_materials', message = 'ns.. %s' % ns, verbose = False)
    if pm.namespace(exists=ns):
        ns += ':'
    else:
        ns = pm.namespace(add=ns) + ':'

    # Add namespace to archive node prefix
    archive_node.attr('prefix').set(ns)
    #debug(app = app, method = 'import_archive_materials', message = 'Namespace successfully added to archive_node... %s' % ns, verbose = False)
    # -------------------------
    # Root archive path
    root_path = archive_object.fullPath()

    # -------------------------
    # Create reference objects and assign materials

    i = 0
    for object in object_list:
        #debug(app = app, method = 'import_archive_materials', message = 'root_path... %s' % root_path, verbose = False)
        #debug(app = app, method = 'import_archive_materials', message = '%s%s' % (ns, object), verbose = False)
        #debug(app = app, method = 'import_archive_materials', message = 'sg... %s' % object_material_map[object], verbose = False)
        full_path = '%s|%s%s' % (root_path, ns, object)
        if not pm.objExists(full_path):
            mat_ref = create_material_reference('%s%s' % (ns, object), root_path, sg=object_material_map[object])
            pm.connectAttr(mat_ref.attr('message'), archive_node.attr('obj_refs[%d]' % i))
            i += 1
        else:
            pm.sets( object_material_map[object], e = True, forceElement = full_path )

    # ----------------------------------
    # Restore selection
    pm.select(sel, r= True)
    #debug(app = app, method = 'import_archive_materials', message = 'import_archive_materials COMPLETE!', verbose = False)

def connectArchives():
    listArchives = cmds.ls(type = 'core_archive')
    listTransforms = cmds.ls(type = 'transform')
    for eachArchive in listArchives:
        archiveName = eachArchive.split(':')[0]
        for each in listTransforms:
            if cmds.objExists('%s.mcAssArchive' % each) :
                try:
                    getFilePath = cmds.getAttr('%s.mcAssArchive' % each)
                    if archiveName in getFilePath:
                        cmds.connectAttr('%s.message' % eachArchive,  '%s.miGeoShader' % each, force = True)
                except:
                    pass

def doReconnect(app = None, postPublish = False):
    """
    To reconnect archives in the scene that have been cleaned up post publishing.
    """
    #debug(app = app, method = 'doReconnect', message = 'Entering doReconnect now..', verbose = False)

    # Find all archives
    ## Now find the ones with the new namespacing them as they get imported with namespaces..
    allCoreArchives = [eachCore for eachCore in cmds.ls(type = 'core_archive')]
    #debug(app = app, method = 'doReconnect', message = 'allCoreArchives: %s' % allCoreArchives, verbose = False)

    archivesDict = {}## ArchiveName: [filepath, [listofGeo]]
    sceneGeoDict = {}## GeoName: [filepath, getTrans]
    ## Now process each Archives information to a dictionary
    for eachArchive in allCoreArchives:
        archivesDict[eachArchive] = [cmds.getAttr('%s.filename' % eachArchive), cmds.listConnections(eachArchive, source = False, type = 'transform')]

    #debug(app = app, method = 'doReconnect', message = 'archivesDict: %s' % archivesDict, verbose = False)

    ## Now process the scene geo info to a dictionary
    getGeo = [eachGeo for eachGeo in cmds.ls(type = 'transform') if cmds.objExists('%s.mcAssArchive' % eachGeo)]
    for eachGeo in getGeo:
        archivePath = cmds.getAttr('%s.mcAssArchive' % eachGeo)
        getTrans = cmds.xform(eachGeo, query = True, matrix = True)
        sceneGeoDict[eachGeo] = [archivePath, getTrans]

    #debug(app = app, method = 'doReconnect', message = 'sceneGeoDict: %s' % sceneGeoDict, verbose = False)
    ## Create all the groups first based of the names of the working archives
    allGroups = []
    for eachArchive in allCoreArchives:
        stripName = eachArchive.split('_CORE_Geoshader')[0]
        #debug(app = app, method = 'doReconnect', message = 'eachArchive: %s' % stripName, verbose = False)
        if not cmds.objExists('%s_Archives_hrc' % stripName.replace(':', '_')):
            cmds.group(name = '%s_Archives_hrc' % stripName.replace(':', '_'), empty = True)

        if '%s_Archives_hrc' % stripName.replace(':', '_') not in allGroups:
            allGroups.extend(['%s_Archives_hrc' % stripName.replace(':', '_')])

    ## Now process the duplication
    for archKey, archVar in archivesDict.items():
        for geoKey, geoVar in sceneGeoDict.items():
            ## If filepath == filepath
            if archVar[0] ==  geoVar[0]:
                #print geoKey, archVar[0]
                grpName = '%s_Archives_hrc' % archKey.split('_CORE_Geoshader')[0]
                #debug(app = app, method = 'doReconnect', message = 'grpName: %s' % grpName, verbose = False)

                fullpathtoorig = cmds.ls(geoKey, l = True)
                #debug(app = app, method = 'doReconnect', message = 'fullpathtoorig: %s' % fullpathtoorig, verbose = False)

                #debug(app = app, method = 'doReconnect', message = 'Duplicating: %s' % archVar[1][0], verbose = False)

                dupGeo = cmds.duplicate(archVar[1][0], returnRootsOnly = True, renameChildren = True, inputConnections = True)
                #debug(app = app, method = 'doReconnect', message = 'Duplicated as dupGeo: %s' % dupGeo[0], verbose = False)
                [cmds.delete(eachChild) for eachChild in cmds.listRelatives(dupGeo[0], children = True) if 'Shape' not in eachChild]

                cmds.parent(dupGeo[0], world = True)
                rename = cmds.rename(dupGeo[0], geoKey)
                #debug(app = app, method = 'doReconnect', message = 'Renamed as dupGeo as: %s' % rename, verbose = False)

                cmds.delete(fullpathtoorig)
                #debug(app = app, method = 'doReconnect', message = 'Deleted: %s' % fullpathtoorig, verbose = False)

                ## Now check for a 1 in the damn name if they duplicated on world!
                if rename.endswith('1'):
                    #debug(app = app, method = 'doReconnect', message = 'FOUND BAD NAME: %s' % rename, verbose = False)
                    cmds.rename(rename, rename[:-1])
                    #debug(app = app, method = 'doReconnect', message = 'FIXED BAD NAME: %s' % rename, verbose = False)

                cmds.xform(geoKey, matrix = geoVar[1])
                cmds.parent(geoKey, grpName)
                #debug(app = app, method = 'doReconnect', message = 'Parented %s to %s' % (geoKey, grpName), verbose = False)
                ##Now do a quick suffix check
                try:[cmds.rename(eachChild, '%s_geo' % eachChild) for eachChild in cmds.listRelatives(geoKey, children = True, shapes = False) if '_geo' not in eachChild]
                except:pass
                #debug(app = app, method = 'doReconnect', message = 'Suffix fixed for: %s' % eachChild, verbose = False)

    #debug(app = app, method = 'doReconnect', message = 'Duplications successful..', verbose = False)
    ## Now clean up the naming on the imported archives to get rid of the namespaces. They're not needed
    [cmds.rename(each, '%s_geo' % each.replace(':', '_')) for each in cmds.ls(type = 'core_archive') if ':' in each]
    #debug(app = app, method = 'doReconnect', message = 'Renamed %s to %s' % (each, '%s_geo' % each.replace(':', '_')), verbose = False)

    #debug(app = app, method = 'doReconnect', message = 'Building groups...', verbose = False)
    ## Now do a main group for these
    if not cmds.objExists('CORE_ARCHIVES_hrc'):
        cmds.group(allGroups, n = 'CORE_ARCHIVES_hrc')

    #debug(app = app, method = 'doReconnect', message = 'allGroups: %s' % allGroups, verbose = False)
    if allGroups:
        for eachGrp in allGroups:
            if len(cmds.ls('CORE_ARCHIVES_hrc')) > 1:
                ## we have an OLD scene with more than one published ENV file in it.
                ## Do a brute force hack now
                cmds.group(n = 'tempArchives' , em = True)
                cmds.parent(eachGrp, 'tempArchives')
                
            else:
                try:
                    cmds.parent(eachGrp, 'CORE_ARCHIVES_hrc')
                except:
                    pass

    #debug(app = app, method = 'doReconnect', message = 'doReconnect Finished...', verbose = False)

## CREATE
def corePreviewSetup():
    for x in cmds.ls(type = 'core_archive'):
        core_mesh         = '%s_CORE_geo' % x.split('_')[0]
        core_preview = '%s_corePreview' % core_mesh
        core_path         = cmds.getAttr('%s.filename' % x)
        cArch_geo         = '%s*' % '_'.join( core_preview.split('_')[:-3] )
        
        if not cmds.objExists(core_preview):
            if core_path:
                if os.path.exists(core_path) and core_path.endswith('.mi.gz'):
                    version = os.path.basename(core_path).split('.')[-3]
                    work_path = os.path.abspath( os.path.join(os.path.dirname(core_path), '..', '..', 'maya') ).replace('\\', '/')
                    
                    if os.path.exists(work_path):
                        mayaScenes = [each for each in os.listdir(work_path) if each.endswith('.mb')]
                        
                    if mayaScenes:
                        highestVersion = os.path.join(work_path, max(mayaScenes)).replace('\\', '/')
                        if os.path.exists(highestVersion):
                            importedScene = cmds.file(highestVersion, i = True, namespace = 'corePreview', returnNewNodes = True)
                            
                        ## COMBINE ALL MESHES
                        meshes = cmds.filterExpand(importedScene, selectionMask = 12, fullPath = True)
                        meshes = list( set( meshes ) )
                        if meshes:
                            if len(meshes) > 1:
                                mesh = cmds.polyUnite(meshes, constructionHistory = False)
                                mesh = cmds.rename(mesh, '%s_corePreview' % core_mesh)
                            else:
                                mesh = cmds.listRelatives(meshes[0], parent = True, fullPath = True)[0]
                                mesh = cmds.rename(mesh, '%s_corePreview' % core_mesh)
                                cmds.parent(mesh, world = True)
                            shape = cmds.listRelatives(mesh, shapes = True, fullPath = True)[0]
                                
                            ## DELETE ALL IMPORTED SCENE SHITS
                            for each in importedScene:
                                if cmds.objExists(each):
                                    cmds.lockNode(each, lock = False)
                                    cmds.delete(each)
            
                        ## ITERATE ALL CARCH GEO AND ADD CORE PREVIEW SHAPES INTO
                        for each in cmds.ls(cArch_geo, type = 'mesh'):
                            if not each.endswith('_corePreviewShape'):
                                geo_transform = cmds.listRelatives(each, parent = True, fullPath = True)[0]
                                cmds.setAttr('%s.visibility' % each, False)
                                try:cmds.parent(shape, geo_transform, shape = True, add = True)
                                except:pass
                                
## DELETE CORE PREVIEW SETUP
def deleteCorePreviewSetup():
    for x in cmds.ls(type = 'mesh'):
        if x.endswith('corePreviewShape'):
            cmds.delete(x)
            
    for x in cmds.ls(type = 'transform'):
        if x.endswith('corePreview'):
            cmds.delete(x)
            
## CARCH VISIBILITY
def cArch_visibility(state = True):
    for x in cmds.ls(type = 'mesh'):
        if not x.endswith('_corePreviewShape'):
            if 'CArch_' in x:
                cmds.setAttr('%s.visibility' % x, state)

## PREVIEW VIS OFF
def cPreview_visibility(state = True):
    for x in cmds.ls(type = 'mesh'):
        if x.endswith('_corePreviewShape'):
            cmds.setAttr('%s.visibility' % x, state)