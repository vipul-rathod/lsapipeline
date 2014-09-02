import os, getpass, sys, shutil, sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
from functools import partial
from tank import TankError

## Custom stuff
if 'T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean' not in sys.path:
    sys.path.append('T:/software/lsapipeline/install/apps/tk-bbb-mayaOcean')
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug
import utils as utils
#reload(utils)

def _intersectOceanPreviewPlane(boatName = 'CHAR_Sydney'):
    sides = ['Left', 'Right']
    intersectionCurves = []
    for eachSide in sides:
        debug(None, method = '_intersectOceanPreviewPlane', message = ' Building intersection for: %s' % eachSide, verbose = False)
        if cmds.objExists('%s:NurbsHull%s' % (boatName, eachSide)):
            curveName = '%s_IntersectCurve%s_crv' % (boatName, eachSide)
            if not cmds.objExists(curveName):
                debug(None, method = '_intersectOceanPreviewPlane', message = ' Found %s:NurbsHull%s' % (boatName, eachSide), verbose = False)
                intersectingCurve = cmds.intersect('%s:NurbsHull%s' % (boatName, eachSide), '%s_NurbsIntersect_geo' % boatName, fs=True, name = curveName)
                cmds.rename(intersectingCurve[0].split('>')[-1], curveName)
                intersectionCurves.append('%sShape_1' % curveName)
                debug(None, method = '_intersectOceanPreviewPlane', message = ' Appended %s' % intersectingCurve[0], verbose = False)
            else:
                intersectionCurves.append('%sShape_1' % curveName)
        else:
            cmds.warning('INCOMPLETE RIG FOUND!!! %s:NurbsHull%s MISSING FROM RIG! Fix Immediately!' % (boatName, eachSide))
            debug(None, method = '_intersectOceanPreviewPlane', message = ' %s:NurbsHull%s MISSING FROM RIG!' % (boatName, eachSide), verbose = False)

    debug(None, method = '_intersectOceanPreviewPlane', message = ' intersectionCurves complete, returning: %s' % intersectionCurves, verbose = False)
    return intersectionCurves

def buildOceanNurbsPreviewPlane(xRes = 20, zRes = 20, size = 8, oceanShader = '', boatName = ''):
    """
    Creates NURBS plane that moves along with ocean so we can intersect this with our boatName to create the emitter curves
    """
    debug(None, method = 'buildOceanNurbsPreviewPlane', message = 'Building NURBS Intersection plane now', verbose = False)
    if cmds.objExists('%s_NurbsIntersect_geo' % boatName):
        cmds.warning('Skipping %s_NurbsIntersect. Already exists in the scene!' % boatName)
        debug(None, method = 'buildOceanNurbsPreviewPlane', message = 'Skipping %s_NurbsIntersect. Already exists in the scene!' % boatName, verbose = False)
    else:
        NURBSPlane = cmds.nurbsPlane( width=1,lengthRatio = 1,degree = 1, patchesU=xRes, patchesV=zRes, axis = (0,1,0) , constructionHistory = 0, name = '%s_NurbsIntersect_geo' % boatName)
        debug(None, method = 'buildOceanNurbsPreviewPlane', message = 'Built NURBSPlane: %s' % NURBSPlane, verbose = False)

        ## Now set the attrs of the NURBSPlane
        cmds.setAttr ( "%s.rotate" % NURBSPlane[0], lock= True)
        cmds.setAttr ("%s.scaleY" % NURBSPlane[0], lock= True)
        cmds.setAttr ("%s.scaleX" % NURBSPlane[0], size)
        cmds.setAttr ("%s.scaleZ" % NURBSPlane[0], size)
        cmds.setAttr ( "%s.translateY" % NURBSPlane[0] , lock= True)
        #cmds.setAttr (NURBSPlane[0] + ".visibility",0)
        cmds.setAttr ("%s.primaryVisibility" % NURBSPlane[0],0)
        cmds.setAttr ("%s.visibleInReflections" % NURBSPlane[0],0)
        cmds.setAttr ("%s.visibleInRefractions" % NURBSPlane[0],0)
        debug(None, method = 'buildOceanNurbsPreviewPlane', message = 'All Attrs set correctly', verbose = False)
        ## Cleanup the build
        _cleanupNURBSPlane(NURBSPlane, boatName)
        debug(None, method = 'buildOceanNurbsPreviewPlane', message = 'Cleanup Performed Successfully', verbose = False)
        ## Build the expression
        _buildNURBSPlaneExpression(NURBSPlane, xRes, zRes, oceanShader)
        debug(None, method = 'buildOceanNurbsPreviewPlane', message = 'Expression Built Successfully', verbose = False)

def _buildNURBSPlaneExpression(NURBSPlane, xRes, zRes, oceanShader):
    """
    Function to setup the expression that hooks the nurbsPlane to the ocean
    @param NURBSPlane: The build of the nurbsPlane, this build command should have returned a list. Due to refactoring we're just handling this list instead of accepting the actual name
    @type NURBSPlane: List
    """
    ## Now build the expression to connect the cv's of the NURBSPlane to the ocean
    xSize = xRes+1
    zSize = zRes+1

    expStringList = ['float $u, $v;\n float $minx = %s.scaleX * -0.5 + %s.translateX;\n' % (NURBSPlane[0], NURBSPlane[0]),
                                'float $maxx = %s.scaleX *  0.5 + %s.translateX;\n' % (NURBSPlane[0], NURBSPlane[0]),
                                'float $minz = %s.scaleZ * -0.5 + %s.translateZ;\n' % (NURBSPlane[0], NURBSPlane[0]),
                                'float $maxz = %s.scaleZ *  0.5 + %s.translateZ;\n' % (NURBSPlane[0], NURBSPlane[0]),
                                'float $disp[] = `colorAtPoint -o A -su %s  -sv  %s -mu $minx -mv $minz -xu $maxx -xv $maxz %s`;\n' % (str(xSize), str(zSize), oceanShader)
                                ]
    expString = utils.processExpressionString(expStringList)
    #unfold loop and use output connections
    i=0
    for x in range(xSize):
        planeX = x * zSize
        for z in range(zSize):
            planeZ= zSize - z - 1
            addTo = "%s.cv[%s].yv = $disp[%s];\n" % (NURBSPlane[0], str(planeX +planeZ), str(i))
            expString += addTo
            #increment by 1
            i=i+1

    ## Check if the expression already exists in the scene, if so delete it
    utils.checkExpressionExists( '%s_IntersectionPlane' % NURBSPlane[0])

    ## Build new expression
    cmds.expression(n = '%s_IntersectionPlane' % '_'.join(NURBSPlane[0].split(':')), string = expString)

def _cleanupNURBSPlane(NURBSPlane = '', boatName = ''):
    """
    Cleans the scene up after the NURBSPLane setup
    """
    ##Cleanup
    if not cmds.objExists('Shot_FX_hrc'):
        cmds.group(n = 'Shot_FX_hrc', em = True)

    cmds.parent(NURBSPlane[0], 'Shot_FX_hrc')
    cmds.setAttr('%s.visibility' % NURBSPlane[0], 0)
    if cmds.objExists('%s:world_ctrl' % boatName):
        cmds.parentConstraint('%s:cog_ctrl' % boatName,  NURBSPlane[0],  mo = False, skipRotate = ['x', 'y' , 'z'], skipTranslate = ['y'])
    else:
        cmds.warning('Cannot find %s. The rig needs to have the correct naming for the world_ctrl!' % '%s:world_ctrl' % boatName)

def _cleanupPolyPlane(polyPlane = ''):
    """
    Cleans the scene up after the Poly Collider setup
    """
    if not cmds.objExists('Shot_FX_hrc'):
        cmds.group(n = 'Shot_FX_hrc', em = True)
    cmds.parent('%s_collider' % polyPlane, 'Shot_FX_hrc')
    cmds.parent( '%s_collider_nRigid' % polyPlane, 'Shot_FX_hrc')
    cmds.setAttr('%s_collider.visibility' % polyPlane, 0)

def buildPolyPlane():
    """
    Splitting out the part so we can choose what to convert and what not to to reduce the load on the FX scene
    Builds a polyPlane with construction history from the nurbsPlane to help collide partilces
    Note you must have a valid nurbsPlane selection for this function
    """
    for eachSel in cmds.ls(sl= True):
        name = '%s_polyCollide_geo' % eachSel.split('NurbsIntersect')[0]
        cmds.nurbsToPoly(eachSel, n = '%s_collider' % eachSel, format = 0, pt = 1, pc = 200, ch= True)
        cmds.select('%s_collider' % eachSel, r = True)
        mel.eval('makeCollideNCloth;')
        cmds.rename('nRigid1', '%s_collider_nRigid' % eachSel)
        _cleanupPolyPlane(polyPlane = '%s_collider_nRigid' % eachSel)
