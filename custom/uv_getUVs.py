import sys
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug
import maya.api.OpenMaya as om
import maya.cmds as cmds

def _uvMapIndex(pathToGeo, mapName):
    x = 0
    p = True
    maps = {}
    while p:
        if cmds.getAttr('%s.uvSet[%s].uvSetName' % (pathToGeo, x)):
            maps[cmds.getAttr('%s.uvSet[%s].uvSetName' % (pathToGeo, x))] = x
            x = x + 1
        else:
            p = False
    #print maps
    return maps[mapName]

def _getPerFaceUVInfo(shapeFn, map):
    """
    Function used to fetch the information for the assignUV approach
    REQUIRED:
    # (faceId, vertexIndex, uvId, uvSet='') -> self
    # Assigns a UV coordinate from a uvSet to a specified vertex of a face.
    """
    getFaceCount    = shapeFn.numPolygons
    #debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('getFaceCount:',  getFaceCount), verbose = False)
    perFaceUVInfo = {}  
    for x in range(0, getFaceCount):
        #print
        #debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('FaceID:',  x), verbose = False)
        
        ## Now setup an array to take the face vert indexes
        myVertexIntArray        = []

        ## Now setup an array to take the face vert indexes uvIds
        myUVID_IntArray         = []
             
        ## Now get the verts for this faceIndex
        verts = cmds.polyListComponentConversion( '%s.f[%s]' % (shapeFn.name(), x), fromFace=True, toVertex=True)                    
        #debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('verts:',  verts), verbose = False)
  
        for eachVert in verts:
            vertID = eachVert.split('[')[-1].split(']')[0]
            if ':' not in vertID:
                if int(vertID) not in myVertexIntArray:
                    myVertexIntArray.append(int(vertID))
            else:
                for y in range(int(vertID.split(':')[0]), int(vertID.split(':')[-1])+1):
                    if int(y) not in myVertexIntArray:
                        myVertexIntArray.append(int(y))

        #[myVertexIntArray.append(int(eachVert.split('[')[-1].split(']')[0])) for eachVert in verts if ':' not in eachVert]
        #debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('myVertexIntArray:',  myVertexIntArray), verbose = False)
        
        #try: ## there are no : split verts...
        #    splitVerts = [[int(vertID) for vertID in eachVert.split('[')[-1].split(']')[0].split(':')] for eachVert in verts if ':' in eachVert]
            #debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('splitVerts:',  splitVerts), verbose = False)
            
        #    [myVertexIntArray.append(int(y)) for y in range(splitVerts[0][0], splitVerts[0][1] + 1)]
            #debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('myVertexIntArray:',  myVertexIntArray), verbose = False)
        #except:
        #    pass
        ## Now get the face relative ids
        vertCount = len(list(set(myVertexIntArray)))
        #debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('vertCountAFTER:',  vertCount), verbose = False)
        
        if vertCount:
            try:
                [myUVID_IntArray.append(shapeFn.getPolygonUVid(x, s, map)) for s in range(0, vertCount)]
            except:
                for s in range(0, vertCount):
                    try:
                        uv_id = shapeFn.getPolygonUVid(x, s, map)
                        debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('uv_id:',  uv_id), verbose = False)
                        myUVID_IntArray.append(uv_id)
                    except:
                        myUVID_IntArray.append(None)
        
        #debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('myVertexIntArray:',  myVertexIntArray), verbose = False)
        #debug(None, method = 'uv_getUVs._getPerFaceUVInfo', message = '{0:<10}{1}'.format('myUVID_IntArray:',  myUVID_IntArray), verbose = False)
        perFaceUVInfo[x] = [myVertexIntArray, myUVID_IntArray]

    return perFaceUVInfo

def _getUandV(shapeFn, map):
    """
    Function to return the u and v arrays
    """
    myU, myV = shapeFn.getUVs(map)
    #debug(None, method = 'uv_getUVs._getUandV', message = 'u: {0} \nv:{1}'.format(myU, myV), verbose = False)
    return myU, myV

def _getUVSets(shapeFn):
    """
    Function to return the current uvSets IN USE from a MFnMesh node
    """
    #debug(None, method = 'uv_getUVs._getUVSets', message = 'Fetching uvsets now..', verbose = False)
    uvsets          = []
    getFaceCount    = shapeFn.numPolygons
    
    try:
        [[uvsets.extend([eachUVset]) for eachUVset in shapeFn.getFaceUVSetNames(x) if eachUVset not in uvsets] for x in range(0, getFaceCount) ]
    except:
        uvsets = None
#     for eachUVSet in shapeFn.getUVSetNames():
#         for x in range(0, getFaceCount):
#             _getUVSets = shapeFn.getFaceUVSetNames(x)
#             for eachUVset in _getUVSets:
#                 if eachUVset not in uvsets:
#                     uvsets.extend([eachUVset])
    #debug(None, method = 'uv_getUVs._getUVSets', message = '{0:<10}{1}'.format('uvsets:',  uvsets), verbose = False)
    
    if uvsets:
        return uvsets
    else:
        return uvsets

def _getUVShells(shapeFn, map, perFaceInfo):
    """
    Function to call the number of shells and return the array of the uv's shell numbers
    """
    getShells   = shapeFn.getUvShellsIds(map)
    
    #debug(None, method = 'uv_getUVs._getUVShells', message = '{0:<10}{1}'.format('getShells:',  getShells), verbose = False)
    ## The index of this list is also the UVIDs from 0 -> end of list
    ## Need to go through this list and get each index and shell relationship
    shellUVs = {}
    for x, uvShell in enumerate(getShells[1]):
        if not uvShell in shellUVs.keys():
            shellUVs[uvShell] = [x]
        else:
            shellUVs[uvShell].append(x) 
    #debug(None, method = 'uv_getUVs._getUVShells', message = '{0:<10}{1}'.format('shellUVs:',  shellUVs), verbose = False)
    
    shellUVsCount = {}
    for eachShell, eachUVIDList in shellUVs.items():
        #debug(None, method = 'uv_getUVs._getUVShells', message = '{0:<10}{1}'.format('shellID:',  eachShell), verbose = False)
        #debug(None, method = 'uv_getUVs._getUVShells', message = '{0:<10}{1}'.format('uvidList:',  eachUVIDList), verbose = False)
        #debug(None, method = 'uv_getUVs._getUVShells', message = '{0:<10}{1}'.format('len:',  len(eachUVIDList)), verbose = False)
        
        shellCount = om.MIntArray()
        for eachUVID in eachUVIDList:
            for eachFace, eachFaceInfo in perFaceInfo.items():  ## eachFaceID, eachFace [VertList] [UVIDList]
                if eachUVID in eachFaceInfo[1]:                 ## If the id is in the shells id list
                    count = len(eachFaceInfo[0])                ## Get the face vert count
                    shellCount.append(count)                    ## Append this to the array
                        
        if eachShell not in shellUVsCount.keys():
            shellUVsCount[eachShell] = [shellCount]
        else:
            shellUVsCount[eachShell].append(shellCount)
        #debug(None, method = 'uv_getUVs._getUVShells', message = '{0:<10}{1}'.format('shellCountLEN:',  len(shellCount)), verbose = False)
    
    #debug(None, method = 'uv_getUVs._getUVShells', message = '{0:<10}{1}'.format('shellUVsCount:',  shellUVsCount), verbose = False)
    ## Trying to return the array first as opposed to a new list.
    return getShells, shellUVs, shellUVsCount
    
def getUVs(geoName = '', multiOnly = True):
    """
    Function to get as much info about the mesh uvs for use later on as possible
    """
    ### Create dictionary for storing final uv data
    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('geoName:',  geoName), verbose = False)
    uvSetData = {}
    shapeFn = None
    
    ## Full path to the geo for writing out later.
    fullPathToName = cmds.ls(geoName, l = True)[0]
    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('fullPathToName:',  fullPathToName), verbose = False)
    
    ## make sure this is a mesh
    getChildren = cmds.listRelatives(fullPathToName, children = True)[0]
    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('getChildren:',  getChildren), verbose = False)
    
    if getChildren:
        #debug(None, method = 'uv_getUVs.getUVs', message = 'Shape has a child...', verbose = False)
        if cmds.nodeType(getChildren) == 'mesh':
            selectionList    = om.MSelectionList()
            selectionList.add(fullPathToName)
            nodeDagPath      = selectionList.getDagPath(0)
            shapeFn          = om.MFnMesh(nodeDagPath)
            ## Now fetch data from shapeFn
            shapeName        = shapeFn.name()
            #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('shapeName:',  shapeName), verbose = False)
            currentUVSets    = shapeFn.getUVSetNames()
            
            ## Now we find the UV sets for the mesh into a valid list.
            ## We're looking through each face to see what uvSets are assigned to them to find valid uv sets.
            uvsets = _getUVSets(shapeFn)### VALID UV SETS WILL BE RETURNED IF THE ARTIST HAS CREATED AN EMPTY UV SET IT WILL BE DISCARDED
            #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('uvSets:',  uvsets), verbose = False)
            
            ## Check to see if the flag for mult uv sets only is on 
            if multiOnly:
                if len(uvsets) > 1:
                    export = True
                else:
                    export = False
            else:
                export = True
                
            if export:
                debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('Processing: ',  geoName), verbose = False)
                #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('len(currentUVSets): ',  len(currentUVSets)), verbose = False)
            
                for eachUVSet in uvsets:
                    data = []
                    ## Add the uvset name....
                    shapeFn.setCurrentUVSetName(eachUVSet)
                    
                    ## Add the path to the geo
                    ## Returns |path|to|geo
                    data.extend([fullPathToName])
                    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('fullPathToName:',  fullPathToName), verbose = False)
                    
                    ## Add the name
                    ## Returns nameofUvSet
                    data.extend([eachUVSet])
                    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('uvSetName:',  eachUVSet), verbose = False)
                    
                    ## Add the u and v from the straight foward fetch
                    ## Returns [uArray], [vArray]
                    getUVArrays = _getUandV(shapeFn, eachUVSet)
                    data.extend([getUVArrays[0]])
                    data.extend([getUVArrays[1]])
                    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('getUVArraysU:',  getUVArrays[0]), verbose = False)
                    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('getUVArraysV:',  getUVArrays[1]), verbose = False)
                    
                    ## Get the perFace info in case we need it for rebuilding later
                    ## Returns {faceId: [myVertixIntArray, myUVID_IntArray]}
                    faceUVInfo = _getPerFaceUVInfo(shapeFn, eachUVSet)
                    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('faceUVInfo:',  faceUVInfo), verbose = False)
                    data.extend([faceUVInfo])
                    
                    ## Add the num of uvshells and the shell list
                    ## Returns (shellCount, [vertIndexShellAssociationList]), {shell: [shellUVs]}, [ShellUVsCount]
                    #getShells = _getUVShells(shapeFn, eachUVSet, faceUVInfo)
                    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('getShells:',  getShells), verbose = False)
                    #data.extend([getShells])
                    
                    ## The uvName index
                    #print 'processing uvindex for %s' % eachUVSet
                    data.extend([_uvMapIndex(pathToGeo = fullPathToName, mapName = eachUVSet)])
                    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('mapIndex:',  _uvMapIndex(eachUVSet)), verbose = False)
                    
                    uvSetData[eachUVSet] = data
                    #debug(None, method = 'uv_getUVs.getUVs', message = '{0:<10}{1}'.format('uvSetData:',  uvSetData), verbose = False)
                    
                ## Forcing this back to map1 to see if I can avoid crashes
                shapeFn.setCurrentUVSetName('map1')
                #print 'Data stored for %s' % geoName
    if uvSetData:
        return [geoName, uvSetData]
    else:
        return None