'''
Created on May 14, 2014

@author: bernard
'''
import maya.cmds as cmds

def getMaxAndMinAxis (objectName, preview=False):
    """
    send a object to get the Max and Min X,Y and Z
    @param objectName: Name of Object
    @type objectName: String
    --------------------------------------------
    @param preview: to see the preview
    @type preview: Bool
    --------------------------------------------
    @return: 0-maxX, 1-minX, 2-maxY, 3-minY, 4-maxZ, 5-minZ
    """
    maxX,maxY,maxZ,minX,minY,minZ = 0,0,0,0,0,0
    vertexList = cmds.getAttr("%s.vrts"%objectName, multiIndices=True )
    i = 0
    for i in vertexList:
        cmds.select("%s.pnts[%s]"%(objectName,i))
        vertexPositionX, vertexPositionY, vertexPositionZ = cmds.xform("%s.pnts[%s]"%(objectName,i), query=True, translation=True, worldSpace=True )
        if vertexPositionX > maxX or i == 0:
            maxX = vertexPositionX
        if vertexPositionY > maxY or i == 0:
            maxY = vertexPositionY
        if vertexPositionZ > maxZ or i == 0:
            maxZ = vertexPositionZ 
        if vertexPositionX < minX or i == 0:
            minX = vertexPositionX
        if vertexPositionY < minY or i == 0:
            minY = vertexPositionY
        if vertexPositionZ < minZ or i == 0:
            minZ = vertexPositionZ 
    
    if preview == True:
        cmds.spaceLocator(name="minX", p=(0, 0, 0))
        cmds.spaceLocator(name="minY", p=(0, 0, 0))
        cmds.spaceLocator(name="minZ", p=(0, 0, 0))
        cmds.spaceLocator(name="maxX", p=(0, 0, 0))
        cmds.spaceLocator(name="maxY", p=(0, 0, 0))
        cmds.spaceLocator(name="maxZ", p=(0, 0, 0))
        meshX,meshY,meshZ = cmds.xform(objectName, query=True, translation=True, worldSpace=True )
        cmds.move( minX, meshY, meshZ, 'minX')
        cmds.move( maxX, meshY, meshZ, 'maxX')
        cmds.move( meshX, minY, meshZ, 'minY')
        cmds.move( meshX, maxY, meshZ, 'maxY')
        cmds.move( meshX, meshY, minZ, 'minZ')
        cmds.move( meshX, meshY, maxZ, 'maxZ')
        
    return maxX,minX,maxY,minY,maxZ,minZ

def objectNameParticleExpressionBeforeDynamics(objectNameParticle="",oceanShader=""):
    """
    send objectParticle and oceanShader to make custom expression on objectParticle
    @param objectNameParticle: Name of Object
    @type objectNameParticle: String
    --------------------------------------------
    @param oceanShader: Name of shader
    @type oceanShader: String
    --------------------------------------------
    @return: 0-ExpressionText
    """
    newExp = ""
    newExp += "%s.lifespanPP = rand(2,4);\n"%objectNameParticle
    newExp += "vector $pos = %s.position;\n"%objectNameParticle
    newExp += "float $px = $pos.x;\n"
    newExp += "float $pz = $pos.z;\n"
    newExp += "float $disp[] = `colorAtPoint -u $px -v $pz %s`;\n"%oceanShader
    newExp += "if( $pos.y > $disp[0]-0.2 ){\n"
    newExp += "\n\t%s.lifespanPP = 0;\n"%objectNameParticle
    newExp += "}\n"
    
    cmds.dynExpression(objectNameParticle, string=newExp, runtimeBeforeDynamics=True)
    
    return newExp
    
def splashDiscParticleExpressionBeforeDynamics(splashDiscParticle="",oceanShader=""):
    """
    send splashDiscParticle and oceanShader to make custom expression on splashDiscParticle
    @param splashDiscParticle: Name of SplashDiscParticle
    @type splashDiscParticle: String
    --------------------------------------------
    @param oceanShader: Name of shader
    @type oceanShader: String
    --------------------------------------------
    @return: 0-ExpressionText
    """
    newExp = ""
    newExp += "float $particleFoamEmission = 0.8; \n"
    newExp += "float $particleWakeEmission = 0.01;\n"
    newExp += "vector $pos = %s.position;\n"%splashDiscParticle
    newExp += "vector $vel = %s.velocity;\n"%splashDiscParticle
    newExp += "float $px = $pos.x;\n"
    newExp += "float $pz = $pos.z;\n"
    newExp += "float $disp[] = `colorAtPoint -u $px -v $pz %s`;\n"%oceanShader
    newExp += "\nif( $vel.y < 0 && $pos.y < ($disp[0]-.2) ){\n\t"
    newExp += "%s.lifespanPP = 0;\n\t"%splashDiscParticle
    newExp += "int $vox[] = `fluidVoxelInfo -objectSpace false -cb -voxel $px 0 $pz OceanWakeTexture1`;\n\t"
    newExp += "if( size($vox) > 0){\n\t\t"
    newExp += "setFluidAttr -at density -ad -xi $vox[0] -yi $vox[1] -zi $vox[2] -fv $particleWakeEmission OceanWakeTexture1;\n\t"
    newExp += "}\n\t"
    newExp += "$vox = `fluidVoxelInfo -objectSpace false -cb -voxel $px 0 $pz OceanWakeFoamTexture1`;\n\t"
    newExp += "if( size($vox) > 0){\n\t\t"
    newExp += "setFluidAttr -at temperature -ad -xi $vox[0] -yi $vox[1] -zi $vox[2] -fv $particleFoamEmission OceanWakeFoamTexture1;\n\t}\n"
    newExp += "}"
    
    cmds.dynExpression(splashDiscParticle,string=newExp,runtimeBeforeDynamics=True)
    
    return newExp

def splashDiscParticleExpressionAfterDynamics(splashDiscParticle=""):
    """
    send splashDiscParticle to make custom expression on splashDiscParticle
    @param splashDiscParticle: Name of SplashDiscParticle
    @type splashDiscParticle: String
    --------------------------------------------
    @return: 0-ExpressionText
    """
    
    newExp = ""
    newExp += "vector $appear = %s.position;\n"%splashDiscParticle
    newExp += "if ($appear.y < -0.25){\n\t"
    newExp += "%s.lifespanPP = 0;\n"%splashDiscParticle
    newExp += "}"
    
    cmds.dynExpression(splashDiscParticle,string=newExp,runtimeAfterDynamics=True)
    
    return newExp

def splashDiscParticleExpressionCreation(splashDiscParticle=""):
    """
    send splashDiscParticle to make custom expression on splashDiscParticle
    @param splashDiscParticle: Name of SplashDiscParticle
    @type splashDiscParticle: String
    --------------------------------------------
    @return: 0-ExpressionText
    """
    newExp = ""
    newExp += "%s.lifespanPP = rand(2,3);\n"%splashDiscParticle
    newExp += "%s.spriteTwistPP = rand(360);"%splashDiscParticle
    
    cmds.dynExpression(splashDiscParticle,string=newExp,creation=True)
    
    return newExp

def createMainExpression(objectNameEmitter=""):
    """
    creating main expression for the scene
    @param objectNameEmitter: Name of objectNameEmitter
    @type objectNameEmitter: String
    --------------------------------------------
    @return: 0-ExpressionText
    """
    newExp = "////////////////////////////// Main Expression //////////////////////////////\n\n"
    cmds.expression (o=objectNameEmitter, string=newExp, alwaysEvaluate=1, unitConversion="all", name = "ocean_MainExpression")
    
    return newExp

def renameShape (currentName='', changNameTo=''):
    """
    send a shapeName and change the name and transform
    @param currentName: The name of shape
    @type currentName: String
    --------------------------------------------
    @param changeNameTo: The new name
    @type changeNameTo: String   
    --------------------------------------------
    @return: 0-Shape, 1-Transform
    """
    returnNewName=[]
    getParentTransform = cmds.listRelatives(currentName, parent = True)
    returnNewName.append(cmds.rename(currentName, '%sShape' % changNameTo))
    returnNewName.append(cmds.rename(getParentTransform, '%s' % changNameTo))
    return returnNewName

def editMainExpression(objectName="", splashDisc="", oceanShader="", objectNameEmitter="", wakeEmitter="", splashDiscEmitter=""):
    """
    editing the main expression for the scene
    @param splashDiscParticle: Name of SplashDiscParticle
    @type splashDiscParticle: String
    --------------------------------------------
    @return: 0-ExpressionText
    """
    
    oldMainExoression = cmds.expression("ocean_MainExpression",query=True, string=True)
    
    startExpression = "\n////////////////////////////// Start %s Expression //////////////////////////////\n"%objectName
    
    newExp = ""
    newExp += "float $%s_particleSprayRate = 3000;\n"%objectName
    newExp += "float $%s_particleBubblesRate = 100;\n" %objectName
    newExp += "float $%s_fluidDisplacement = 6.0;\n" %objectName
    newExp += "float $%s_fluidFoam = 2.0;\n" %objectName
    newExp += "float $%s_u = .I[0];\n" %objectName
    newExp += "float $%s_v = .I[1];\n" %objectName
    newExp += "float $%s_disp[] = `colorAtPoint -u $%s_u -v $%s_v %s`;\n" %(objectName,objectName,objectName,oceanShader)
    newExp += "float $%s_lastY = `getAttr -time (frame - 2) %s.translateY`;\n" %(objectName,objectName)
    newExp += "float $%s_curY = %s.translateY;\n" %(objectName,objectName)
    newExp += "float $%s_ydiff = $%s_lastY - $%s_curY;\n" %(objectName,objectName,objectName)
    
    newExp += "if( $%s_curY < 0.5 ){\n\t"%objectName
    newExp += "%s.rate = $%s_particleBubblesRate;"%(objectNameEmitter,objectName)
    newExp += "\n} else {\n\t"
    newExp += "%s.rate = 0;\n}\n"%objectNameEmitter
    newExp += "if( $%s_ydiff < 0 ){\n\t"%objectName
    newExp += "$%s_ydiff = -$%s_ydiff;"%(objectName,objectName)
    newExp += "\n}\n"
    newExp += "if( $%s_curY > -1 && $%s_curY < 0.6 ){\n\t"%(objectName,objectName)
    newExp += "%s.fluidDensityEmission = $%s_fluidDisplacement;\n\t"%(wakeEmitter,objectName)
    newExp += "%s.fluidHeatEmission = $%s_fluidFoam;"%(wakeEmitter,objectName)
    newExp += "\n} else {\n\t"
    newExp += "%s.fluidDensityEmission = 0;\n\t"%wakeEmitter
    newExp += "%s.fluidHeatEmission = 0;"%wakeEmitter
    newExp += "\n}\n"
    newExp += "if( $%s_curY > -1 && $%s_curY < 0.5 && $%s_ydiff > 0.05 ){\n\t"%(objectName,objectName,objectName)
    newExp += "%s.rate = $%s_particleSprayRate * $%s_ydiff;\n\t"%(splashDiscEmitter,objectName,objectName)
    newExp += "float $%s_speed = $%s_ydiff * 10;\n\t"%(objectName,objectName)
    newExp += "if( $%s_speed > 10 ){\n\t\t"%objectName
    newExp += "$%s_speed = 10;"%objectName
    newExp += "\n\t}\n\t"
    newExp += "%s.speed = $%s_speed;"%(splashDiscEmitter,objectName)
    newExp += "\n} else {\n\t"
    newExp += "%s.rate = 0;"%splashDiscEmitter
    newExp += "\n}\n"
    newExp += "%s.translateY = $%s_disp[0];\n"%(splashDisc,objectName)
    newExp += "float $%s_dummy = %s.displacement;\n"%(objectName,oceanShader)

    endExpression = "////////////////////////////// End %s Expression //////////////////////////////\n\n"%objectName

    totalExp = oldMainExoression+startExpression+newExp+endExpression
    
    cmds.expression ("ocean_MainExpression",string=totalExp ,edit=True, alwaysEvaluate=1, unitConversion="all")
    
    return totalExp

def createChalkLine(projectName, objectName,surfaceName):
    #Initializing  Variables 
    nodeName = cmds.createNode('pfxToon', name = '%s_PaintFXToon'%projectName)
    mesh = objectName
    myPlane = surfaceName
    
    #PaintFXToon setting
    cmds.setAttr('%s.profileLines' % nodeName, False)
    cmds.setAttr('%s.borderLines' % nodeName, False)
    cmds.setAttr('%s.creaseLines' % nodeName, False)
    cmds.setAttr('%s.intersectionLines' % nodeName, True)
    cmds.setAttr('%s.resampleIntersection' % nodeName, True)
    cmds.setAttr('%s.displayPercent' % nodeName, 100)
    
    #Connecting mesh to PaintFXToon
    cmds.connectAttr("%s.outMesh"%mesh,"%s.inputSurface[0].surface"%nodeName)
    cmds.connectAttr("%s.worldMatrix[0]"%mesh,"%s.inputSurface[0].inputWorldMatrix"%nodeName)
    
    #Create NurbsTessellate and Connecting it to NurbSurface
    apple = cmds.createNode("nurbsTessellate", name="%s_nurbsTessellate"%projectName)
    cmds.connectAttr("%s.chordHeight"%myPlane,"%s.chordHeight"%apple)
    cmds.connectAttr("%s.chordHeightRatio"%myPlane,"%s.chordHeightRatio"%apple)
    cmds.connectAttr("%s.curvatureTolerance"%myPlane,"%s.curvatureTolerance"%apple)
    cmds.connectAttr("%s.edgeSwap"%myPlane,"%s.edgeSwap"%apple)
    cmds.connectAttr("%s.explicitTessellationAttributes"%myPlane,"%s.explicitTessellationAttributes"%apple)
    cmds.connectAttr("%s.local"%myPlane,"%s.inputSurface"%apple)
    cmds.connectAttr("%s.modeU"%myPlane,"%s.uType"%apple)
    cmds.connectAttr("%s.modeV"%myPlane,"%s.vType"%apple)
    cmds.connectAttr("%s.numberU"%myPlane,"%s.uNumber"%apple)
    cmds.connectAttr("%s.numberV"%myPlane,"%s.vNumber"%apple)
    cmds.connectAttr("%s.smoothEdge"%myPlane,"%s.smoothEdge"%apple)
    cmds.connectAttr("%s.smoothEdgeRatio"%myPlane,"%s.smoothEdgeRatio"%apple)
    cmds.connectAttr("%s.uDivisionsFactor"%myPlane,"%s.uDivisionsFactor"%apple)
    cmds.connectAttr("%s.useChordHeight"%myPlane,"%s.useChordHeight"%apple)
    cmds.connectAttr("%s.useChordHeightRatio"%myPlane,"%s.useChordHeightRatio"%apple)
    cmds.connectAttr("%s.vDivisionsFactor"%myPlane,"%s.vDivisionsFactor"%apple)
    
    #Connecting NurbsTessellate and NurbSurface to PaintFXToon
    cmds.connectAttr("%s.outputPolygon"%apple,"%s.inputSurface[1].surface"%nodeName)
    cmds.connectAttr("%s.worldMatrix[0]"%myPlane,"%s.inputSurface[1].inputWorldMatrix"%nodeName)
    
    #Creating Curve and connecting it to PaintFXToon
    mainOffSet = cmds.createNode("offsetCurve",name="%s_main_offsetCurve"%projectName)
    topOffSet = cmds.createNode("offsetCurve",name="%s_top_offsetCurve"%projectName)
    midOffSet = cmds.createNode("offsetCurve",name="%s_mid_offsetCurve"%projectName)
    bottomOffSet = cmds.createNode("offsetCurve",name="%s_buttom_offsetCurve"%projectName)
    cmds.setAttr("%s.distance"%mainOffSet, 0)
    cmds.setAttr("%s.useGivenNormal"%mainOffSet, 0)
    cmds.setAttr("%s.subdivisionDensity"%mainOffSet, 10)
    cmds.setAttr("%s.tolerance"%mainOffSet, 0.5)
    cmds.setAttr("%s.distance"%topOffSet, 0)
    cmds.setAttr("%s.useGivenNormal"%topOffSet, 0)
    cmds.setAttr("%s.subdivisionDensity"%topOffSet, 10)
    cmds.setAttr("%s.tolerance"%topOffSet, 0.5)
    cmds.setAttr("%s.distance"%midOffSet, -0.1)
    cmds.setAttr("%s.useGivenNormal"%midOffSet, 0)
    cmds.setAttr("%s.subdivisionDensity"%midOffSet, 10)
    cmds.setAttr("%s.tolerance"%midOffSet, 0.5)
    cmds.setAttr("%s.distance"%bottomOffSet, 0)
    cmds.setAttr("%s.useGivenNormal"%bottomOffSet, 0)
    cmds.setAttr("%s.subdivisionDensity"%bottomOffSet, 10)
    cmds.setAttr("%s.tolerance"%bottomOffSet, 0.5)
    
    cmds.connectAttr("%s.outMainCurves[0]"%nodeName,"%s.inputCurve"%mainOffSet)
    cmds.connectAttr("%s.outputCurve[0]"%mainOffSet,"%s.inputCurve"%topOffSet)
    cmds.connectAttr("%s.outputCurve[0]"%mainOffSet,"%s.inputCurve"%midOffSet)
    cmds.connectAttr("%s.outputCurve[0]"%mainOffSet,"%s.inputCurve"%bottomOffSet)
    cmds.setAttr("%s.displayPercent"%nodeName, 0)
    
    #Creating 3 Curve
    chalkLine1 = cmds.circle(nr=(0, 1, 0), c=(0, 0, 0), r=1,name="%s_Bottom"%projectName)
    chalkLine2 = cmds.circle(nr=(0, 1, 0), c=(0, 0, 0), r=1,name="%s_Mid"%projectName)
    chalkLine3 = cmds.circle(nr=(0, 1, 0), c=(0, 0, 0), r=1,name="%s_Top"%projectName)
    curveGroups =cmds.group(chalkLine1[0],chalkLine2[0],chalkLine3[0],name="%s_CurvesList"%projectName)
    cmds.group(curveGroups, name="%s_CurvesControl"%projectName)
    #     cmds.xform(chalkLine1[0],cp=True)
    #     cmds.xform(chalkLine2[0],cp=True)
    #     cmds.xform(chalkLine3[0],cp=True)
    cmds.move(0.2,chalkLine2[0],moveY=True)
    cmds.move(0.3,chalkLine3[0],moveY=True)
    #     cmds.scale(1.2,1.2,1.2,chalkLine2[0],scaleXYZ=True)
    cmds.delete(chalkLine1[0],constructionHistory=True)
    cmds.delete(chalkLine2[0],constructionHistory=True)
    cmds.delete(chalkLine3[0],constructionHistory=True)
    
    cmds.connectAttr("%s.outputCurve[0]"%topOffSet,"%sShape.create"%chalkLine3[0])
    cmds.connectAttr("%s.outputCurve[0]"%midOffSet,"%sShape.create"%chalkLine2[0])
    cmds.connectAttr("%s.outputCurve[0]"%bottomOffSet,"%sShape.create"%chalkLine1[0])
    
    objectLoft = cmds.loft(chalkLine3[0], chalkLine2[0], chalkLine1[0],name="%s_Loft"%projectName, constructionHistory=True, uniform=True,
               close=False, autoReverse=True, d=3, sectionSpans=1, range=False, polygon=0,rsn=True)
    
    return objectLoft, [chalkLine1[0],chalkLine2[0],chalkLine3[0]],[mainOffSet,topOffSet,midOffSet,bottomOffSet]

def shaderSetup():
    splashShader = cmds.shadingNode("lambert",asShader=True, name="mainSplashDisc_Shader")
    splashShaderEngine = "mainSplashDisc_ShaderSG"
    splashTexture = cmds.shadingNode("file", asTexture = True, name="mainSplashDisc_Texture")
    splash_P2DT = cmds.createNode("place2dTexture", name="mainSplashDisc_P2DT")
    
    cmds.connectAttr(splash_P2DT + ".coverage", splashTexture + ".coverage", force = True)
    cmds.connectAttr(splash_P2DT + ".translateFrame", splashTexture + ".translateFrame", force = True)
    cmds.connectAttr(splash_P2DT + ".rotateFrame", splashTexture + ".rotateFrame", force = True)
    cmds.connectAttr(splash_P2DT + ".mirrorU", splashTexture + ".mirrorU", force = True)
    cmds.connectAttr(splash_P2DT + ".mirrorV", splashTexture + ".mirrorV", force = True)
    cmds.connectAttr(splash_P2DT + ".stagger", splashTexture + ".stagger", force = True)
    cmds.connectAttr(splash_P2DT + ".wrapU", splashTexture + ".wrapU", force = True)
    cmds.connectAttr(splash_P2DT + ".wrapV", splashTexture + ".wrapV", force = True)
    cmds.connectAttr(splash_P2DT + ".repeatUV", splashTexture + ".repeatUV", force = True)
    cmds.connectAttr(splash_P2DT + ".offset", splashTexture + ".offset", force = True)
    cmds.connectAttr(splash_P2DT + ".rotateUV", splashTexture + ".rotateUV", force = True)
    cmds.connectAttr(splash_P2DT + ".noiseUV", splashTexture + ".noiseUV", force = True)
    cmds.connectAttr(splash_P2DT + ".vertexUvOne", splashTexture + ".vertexUvOne", force = True)
    cmds.connectAttr(splash_P2DT + ".vertexUvTwo", splashTexture + ".vertexUvTwo", force = True)
    cmds.connectAttr(splash_P2DT + ".vertexUvThree", splashTexture + ".vertexUvThree", force = True)
    cmds.connectAttr(splash_P2DT + ".vertexCameraOne", splashTexture + ".vertexCameraOne", force = True)
    cmds.connectAttr(splash_P2DT + ".outUV", splashTexture + ".uv", force = True)
    cmds.connectAttr(splash_P2DT + ".outUvFilterSize", splashTexture + ".uvFilterSize", force = True) 
    
    cmds.connectAttr(splashTexture + ".outColor", splashShader + ".color", force = True) 
    cmds.connectAttr(splashTexture + ".outTransparency", splashShader + ".transparency", force = True) 
    cmds.setAttr("%s.fileTextureName"%splashTexture,"I:/lsapipeline/fx/sprites/water/water_gloop_3.tga",type="string")
    

    cmds.sets(renderable=True,noSurfaceShader=True,empty=True,name=splashShaderEngine)
    cmds.defaultNavigation (connectToExisting=True, source=splashShader, destination=splashShaderEngine)
#     cmds.connectAttr(splashShader + ".outColor", splashShaderEngine + ".surfaceShader") 
    
#     splashShaderEngine = cmds.createNode("shadingEngine", name="%s_SG"%projectName)
#     cmds.defaultNavigation(connectToExisting=True, source=splashShader, destination=splashShaderEngine)
#     cmds.sets(edit=True, forceElement=splashShaderEngine)
#     cmds.connectAttr(splashShaderEngine + ".message", "lightLinker1.shadowLink[3].shadowObject", force = True) 
#     cmds.connectAttr(splashShaderEngine + ".message", "lightLinker1.link[3].object", force = True) 
#     cmds.connectAttr(splashShaderEngine + ".partition","renderPartition.sets[3]", force = True) 
#     cmds.connectAttr(splashShader + ".outColor", splashShaderEngine + ".surfaceShader", force = True)
     
#     
#     cmds.connectAttr(objectname + ".instObjGroups[0]", splashShaderEngine + ".dagSetMembers[0]", force = True) 
#     
    return

# def _cleanupNURBSPlane(NURBSPlane = '', boatName = ''):
#     """
#     Cleans the scene up after the NURBSPLane setup
#     """
#     ##Cleanup
#     if not cmds.objExists('Shot_FX_hrc'):
#         cmds.group(n = 'Shot_FX_hrc', em = True)
# 
#     cmds.parent(NURBSPlane[0], 'Shot_FX_hrc')
#     cmds.setAttr('%s.visibility' % NURBSPlane[0], 0)
#     if cmds.objExists('%s:world_ctrl' % boatName):
#         cmds.parentConstraint('%s:cog_ctrl' % boatName,  NURBSPlane[0],  mo = False, skipRotate = ['x', 'y' , 'z'], skipTranslate = ['y'])
#     else:
#         cmds.warning('Cannot find %s. The rig needs to have the correct naming for the world_ctrl!' % '%s:world_ctrl' % boatName)

# def buildOceanNurbsPreviewPlane(xRes = 20, zRes = 20, size = 8, oceanShader = '', boatName = ''):
#     """
#     Creates NURBS plane that moves along with ocean so we can intersect this with our boatName to create the emitter curves
#     """
#     if cmds.objExists('%s_NurbsIntersect_geo' % boatName):
#         cmds.warning('Skipping %s_NurbsIntersect. Already exists in the scene!' % boatName)
#     else:
#         NURBSPlane = cmds.nurbsPlane( width=1,lengthRatio = 1,degree = 1, patchesU=xRes, patchesV=zRes, axis = (0,1,0) , constructionHistory = 0, name = '%s_NurbsIntersect_geo' % boatName)
# 
#         ## Now set the attrs of the NURBSPlane
#         cmds.setAttr ( "%s.rotate" % NURBSPlane[0], lock= True)
#         cmds.setAttr ("%s.scaleY" % NURBSPlane[0], lock= True)
#         cmds.setAttr ("%s.scaleX" % NURBSPlane[0], size)
#         cmds.setAttr ("%s.scaleZ" % NURBSPlane[0], size)
#         cmds.setAttr ( "%s.translateY" % NURBSPlane[0] , lock= True)
#         #cmds.setAttr (NURBSPlane[0] + ".visibility",0)
#         cmds.setAttr ("%s.primaryVisibility" % NURBSPlane[0],0)
#         cmds.setAttr ("%s.visibleInReflections" % NURBSPlane[0],0)
#         cmds.setAttr ("%s.visibleInRefractions" % NURBSPlane[0],0)
#         ## Cleanup the build
#         _cleanupNURBSPlane(NURBSPlane, boatName)
#         ## Build the expression
#         _buildNURBSPlaneExpression(NURBSPlane, xRes, zRes, oceanShader)
# 
# def _buildNURBSPlaneExpression(NURBSPlane, xRes, zRes, oceanShader):
#     """
#     Function to setup the expression that hooks the nurbsPlane to the ocean
#     @param NURBSPlane: The build of the nurbsPlane, this build command should have returned a list. Due to refactoring we're just handling this list instead of accepting the actual name
#     @type NURBSPlane: List
#     """
#     ## Now build the expression to connect the cv's of the NURBSPlane to the ocean
#     xSize = xRes+1
#     zSize = zRes+1
# 
#     expStringList = ['float $u, $v;\n float $minx = %s.scaleX * -0.5 + %s.translateX;\n' % (NURBSPlane[0], NURBSPlane[0]),
#                                 'float $maxx = %s.scaleX *  0.5 + %s.translateX;\n' % (NURBSPlane[0], NURBSPlane[0]),
#                                 'float $minz = %s.scaleZ * -0.5 + %s.translateZ;\n' % (NURBSPlane[0], NURBSPlane[0]),
#                                 'float $maxz = %s.scaleZ *  0.5 + %s.translateZ;\n' % (NURBSPlane[0], NURBSPlane[0]),
#                                 'float $disp[] = `colorAtPoint -o A -su %s  -sv  %s -mu $minx -mv $minz -xu $maxx -xv $maxz %s`;\n' % (str(xSize), str(zSize), oceanShader)
#                                 ]
#     expString = utils.processExpressionString(expStringList)
#     #unfold loop and use output connections
#     i=0
#     for x in range(xSize):
#         planeX = x * zSize
#         for z in range(zSize):
#             planeZ= zSize - z - 1
#             addTo = "%s.cv[%s].yv = $disp[%s];\n" % (NURBSPlane[0], str(planeX +planeZ), str(i))
#             expString += addTo
#             #increment by 1
#             i=i+1
# 
#     ## Check if the expression already exists in the scene, if so delete it
#     utils.checkExpressionExists( '%s_IntersectionPlane' % NURBSPlane[0])
# 
#     ## Build new expression
#     cmds.expression(n = '%s_IntersectionPlane' % '_'.join(NURBSPlane[0].split(':')), string = expString)