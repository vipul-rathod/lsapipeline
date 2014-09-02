import sys
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug
import maya.api.OpenMaya as om
import maya.cmds as cmds

def findArrayLen(storedMap1Array, arrayToCheck):
    """
    Function to check the length of an array against the map1 array length
    """
    if len(storedMap1Array) != arrayToCheck:
        if len(storedMap1Array) > len(arrayToCheck):
            bloatBy = len(storedMap1Array) - len(arrayToCheck)
            return True, bloatBy
        else:
            return False

def bloatArray(arrayToBloat, bloatBy):
    """
    Function to bloat an array but a specific number
    """
    #debug(None, method = 'setUVs.bloatArray', message = '{0:<10}{1}'.format('Bloated by:', bloatBy),    verbose = False)
    for x in range(0, bloatBy):
        arrayToBloat.append(0.0)

def checkArraySizes(uData, vData):
    sizeU = len(uData)
    sizeV = len(vData)
    if sizeU != sizeV:
        if sizeU > sizeV:
            #debug(None, method = 'setUVs.checkArraySizes', message = 'vData needs to be bloated...',  verbose = False)
            return 'bloatV'
        elif sizeV > sizeU:
            #debug(None, method = 'setUVs.checkArraySizes', message = 'uData needs to be bloated...',  verbose = False)
            return 'bloatU'
        else:
            return None

def _orderUVSets(uvdataSets):
    if uvdataSets:
        uvSetNum = len(uvdataSets) - 1
        orderedUVSets = []
        x = 1 ## skipping 0 index = map1
        loopBreaker = 1
        while uvSetNum > 0:

            ########################################################################################
            # Put a infinite loop breaker here just to find out which asset is wrongly published so
            # that the artist can shoot back to the modelers and republish a correct uvxml
            loopBreaker += 1
            if loopBreaker > 10:
                cmds.confirmDialog(title = 'UV REBUILD', message = 'Failed to rebuild uv on this asset:\n\n"%s"\n\nGet this problematic geometry fixed and republish a proper uvxml for the asset!' % uvdataSets[0][0][0], button = 'GET THIS RESOLVED BY TALKING TO THE MODELERS NOW!')
                break
            ########################################################################################

            for uvdata in uvdataSets:
                uvsetName       = uvdata[0][1]
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('Processing uvsetName: ',  uvsetName),        verbose = False)
    
                getIndex        = int(uvdata[0][5])
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('getIndex: ',  getIndex),        verbose = False)
    
                if getIndex == x:
                    orderedUVSets.append(uvdata)
                    uvSetNum = uvSetNum - 1
                    x = x + 1
                    
        return orderedUVSets
    else:
        print 'No more uvsets to process...'
        return []
    
def readData(data):
    """
    Function to strip back the data from getUVs.py
    """
    storeMap1uArray = None
    storeMap1vArray = None
    
    for uvset, uvdataSets in data.items():
        for uvdata in uvdataSets:
            ## Store map1 arrays first
            ## This is for the advice to bloat the mapArray to match map1
            ## http://ewertb.soundlinker.com/api/api.010.php
            if uvdata[0][1] == 'map1':
                storeMap1uArray = uvdata[0][2] ## u
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('storeMap1uArray: ',  storeMap1uArray),    verbose = False)
                
                storeMap1vArray = uvdata[0][3] ## v
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('storeMap1vArray: ',  storeMap1vArray),    verbose = False)

        for uvdata in uvdataSets:
            ## PROCESS MAP ONE SPECIFICALLY          
            #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('UVMAP:',  uvdata[0][1]),                verbose = False)
            if uvdata[0][1] == 'map1':
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('Assigning map: ',  uvdata[0][1]),  verbose = False)
                pathToGeo       = uvdata[0][0]
                uvsetName       = uvdata[0][1]
                uData           = uvdata[0][2]
                vData           = uvdata[0][3]
                perFaceInfo     = uvdata[0][4]
                #shellInfo       = uvdata[0][5]
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('pathToGeo:',  pathToGeo),        verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uvset:',  uvsetName),                verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uData:',  uData),                verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('vData:',  vData),                verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('perFaceInfo:',  perFaceInfo),    verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('shellInfo:',  shellInfo),        verbose = False)
                ## Now start
                selectionList   = om.MSelectionList()
                # selectionList.add(pathToGeo)
                
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('pathToGeo:',  pathToGeo),        verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uvsetName:',  uvsetName),                verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uData:',  uData),                verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('vData:',  vData),                verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('perFaceInfo:',  perFaceInfo),    verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('selectionList:',  selectionList),    verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('shellInfo:',  shellInfo),        verbose = False)
                
                if cmds.objExists(pathToGeo):
                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('Object found: ',  selectionList),  verbose = False)
                    selectionList.add(pathToGeo)
                    nodeDagPath     = selectionList.getDagPath(0)
                    shapeFn         = om.MFnMesh(nodeDagPath)
                    ## Now fetch data from shapeFn
                    shapeName       = shapeFn.name()
                    currentUVSets   = shapeFn.getUVSetNames()

                    currentSetSize  = shapeFn.numUVs()
                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('currentSetSize:',  currentSetSize),  verbose = False)

                    if uvsetName not in currentUVSets:
                        shapeFn.createUVSet(uvsetName)

                    ## First clear the existing map and make map1 the current
                    shapeFn.setCurrentUVSetName(uvsetName)

                    ### DO THE ARRAY BLOATING NOW IF NECESSARY!
                    if findArrayLen(storeMap1uArray, uData):
                        #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uSizeCheck:',  findArrayLen(storeMap1uArray, uData)[1]),  verbose = False)
                        bloatArray(uData, findArrayLen(storeMap1uArray, uData)[1])

                    if findArrayLen(storeMap1vArray, vData):
                        #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uSizeCheck:',  findArrayLen(storeMap1vArray, vData)[1]),  verbose = False)
                        bloatArray(uData, findArrayLen(storeMap1vArray, vData)[1])

                    checkArrays = checkArraySizes(uData, vData)
                    if checkArrays != None:
                        if checkArrays == 'bloatU':
                            bloatBy = len(vData) - len(uData)
                            bloatArray(uData, bloatBy)
                        else:
                            bloatBy = len(uData) - len(vData)
                            bloatArray(vData, bloatBy)

                    ## We're going to assume this was an empty set to begin with.
                    ## Set the num of UVS first before assigning
                    ## After using this method to set the UV values, you must call one of the assignUV methods to assign the corresponding UV ids to the geometry. ##

                    try:
                        shapeFn.setUVs(uData, vData, uvsetName)
                    except RuntimeError:
                        cmds.warning('FAILED UV.setUVs for %s' % shapeFn.name())

                    uvCounts   = om.MIntArray()
                    uvIds      = om.MIntArray()
                    ## UvCounts = a list of faces by their vert count
                    for face, faceInfo in perFaceInfo.items():#PerFaceInfo       ## {faceId: [attachVertArray], [uvIds]}, ## -1 for no id
                        if not faceInfo[1].count('None') >= 1:
                            for each in faceInfo[1]:
                                uvIds.append(int(each))
                            uvCounts.append(len(faceInfo[0]))

                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uvCounts:',  uvCounts),  verbose = False)
                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uvIds:',  uvIds),  verbose = False)
                    try:
                        shapeFn.assignUVs(uvCounts, uvIds, uvsetName)
                    except RuntimeError:
                        cmds.warning('FAILED UV.setUVs for %s' % shapeFn.name())
                        

                    ## Now delete the history to complete the changes
                    cmds.delete(pathToGeo, ch = True)
                    #print
                    numUVs_map1  = shapeFn.numUVs( uvsetName );
                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('numUVs_map1:',  numUVs_map1),  verbose = False)
                    #print
                    #print
        
        ## Since map1 should always be in index 0 we are now going to process the maps in order to make sure they show up in the same order for 
        ## texture maps to be assigned correctly.
        ## Lets put em into an ordered list since we can't just max() or min() the current lists.

        ## Check to see if the len of the uvsets is > 1 first
        if len(uvdataSets) > 1:
            ## Okay we have more than one uvSet to process..
            ## Lets process these into an ordered list real quick skipping 0 (map1)

            for uvdata in _orderUVSets(uvdataSets):
                ## Now go through everything except map1

                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('UVMAP:',  uvdata[0][1]),                verbose = False)
                pathToGeo       = uvdata[0][0]
                uvsetName       = uvdata[0][1]
                #===============================================================
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uvsetName:',  uvsetName),        verbose = False)
                #===============================================================
                uData           = uvdata[0][2]
                vData           = uvdata[0][3]
                perFaceInfo     = uvdata[0][4]
                #shellInfo       = uvdata[0][5] ## Check this ifyou need to enable it because the index was added in after, this is most likely 6 now.
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('pathToGeo:',  pathToGeo),        verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uvsetName:',  uvsetName),                verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uData:',  uData),                verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('vData:',  vData),                verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('perFaceInfo:',  perFaceInfo),    verbose = False)
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('shellInfo:',  shellInfo),        verbose = False)
                mapIndex        = uvdata[0][5]
                #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('mapIndex:',  mapIndex),        verbose = False)
                
                ## Now start
                selectionList   = om.MSelectionList()
                if cmds.objExists(pathToGeo):
                    selectionList.add(pathToGeo)
                    nodeDagPath     = selectionList.getDagPath(0)
                    shapeFn         = om.MFnMesh(nodeDagPath)
                    ## Now fetch data from shapeFn
                    shapeName       = shapeFn.name()
                    currentUVSets   = shapeFn.getUVSetNames()

                    ## Now create the empty uv set
                    if uvsetName not in currentUVSets:
                        shapeFn.createUVSet(uvsetName)

                    shapeFn.setCurrentUVSetName(uvsetName)

                    ### DO THE ARRAY BLOATING NOW IF NECESSARY!
                    ### This is a tip from one of the websites, that states you can't assign a 2nd uv set if it's array length is different to the base map1
                    if findArrayLen(storeMap1uArray, uData):
                        bloatArray(uData, findArrayLen(storeMap1uArray, uData)[1])

                    if findArrayLen(storeMap1vArray, vData):
                        bloatArray(uData, findArrayLen(storeMap1vArray, vData)[1])

                    checkArrays = checkArraySizes(uData, vData)
                    if checkArrays != None:
                        if checkArrays == 'bloatU':
                            bloatBy = len(vData) - len(uData)
                            bloatArray(uData, bloatBy)
                        else:
                            bloatBy = len(uData) - len(vData)
                            bloatArray(vData, bloatBy)

                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('bloatCheck uData:',  len(uData)),  verbose = False)
                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('bloatCheck vData:',  len(vData)),  verbose = False)

                    ## Set the UVs to the mesh.
                    shapeFn.setUVs(uData, vData, uvsetName)

                    ## We're going to assume this was an empty set to begin with.
                    ## Set the num of UVS first before assigning
                    ## After using this method to set the UV values, you must call one of the assignUV methods to assign the corresponding UV ids to the geometry. ##
                    numUVs  = shapeFn.numUVs( uvsetName );
                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('numUVs:',  numUVs),  verbose = False)

                    uvCounts   = om.MIntArray()
                    uvIds      = om.MIntArray()

                    ## UvCounts = a list of faces by their vert count
                    #print pathToGeo, uvdata[0][1]
                    for face, faceInfo in perFaceInfo.items():
                        if not faceInfo[1].count('None') >= 1:
                            for each in faceInfo[1]:
                                uvIds.append(int(each))
                            uvCounts.append(len(faceInfo[0]))


                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uvCounts:',  uvCounts),  verbose = False)
                    #debug(None, method = 'setUVs.readData', message = '{0:<10}{1}'.format('uvIds:',  uvIds),  verbose = False)
                    try:shapeFn.assignUVs(uvCounts, uvIds, uvsetName)
                    except RuntimeError:pass

                    ## Now copy the map1 to the newUV set name
                    ## shapeFn.copyUVSet('map1', uvsetName)

                    cmds.delete(pathToGeo, ch = True)