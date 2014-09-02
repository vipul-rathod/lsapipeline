'''
Created on May 14, 2014

@author: bernard
'''

import maya.cmds as cmds
from PyQt4 import QtGui, QtCore
from modules.SplashTool_Style import Icon
import modules.SplashTool_Helper as generator
#reload(generator)

class MainWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self,parent)
        
        mainlayout = QtGui.QVBoxLayout(self)
        layout_01 = QtGui.QHBoxLayout(self)
        
        mainlayout.addLayout(layout_01)
        
        layout_01.addWidget(self.SplashToolUI())
        mainlayout.setStretch(1,1)
        
        
        self.setLayout(mainlayout)
        
        self.setWindowTitle('Splash Tool v1.0')
        self.resize(300,0)
        
    def SplashToolUI(self):
        groupCreate = QtGui.QGroupBox("Setup Splash:")
        
        staticObject = QtGui.QLabel('Object:')
        staticObject.setAlignment(QtCore.Qt.AlignVCenter)
        self.getObject = QtGui.QLineEdit(self)
        self.getObject.setEnabled(False)
        self.getObject.setText("<Empty>")
        self.actionObject = QtGui.QPushButton(Icon("AssignIt3.png"),'Assign')
        self.actionObject.released.connect(self.assignObject)
        self.checkOcean = QtGui.QCheckBox("Ocean:")
        self.checkOcean.clicked.connect(self.oceanChecked)
#         staticOcean = QtGui.QLabel('Ocean:')
#         staticOcean.setAlignment(QtCore.Qt.AlignVCenter)
        self.getOcean = QtGui.QLineEdit(self)
        self.getOcean.setEnabled(False)
        self.getOcean.setText("<Create New Ocean>")
        self.actionOcean = QtGui.QPushButton(Icon("AssignIt3.png"),'Assign')
        self.actionOcean.released.connect(self.assignOcean)
        self.actionOcean.setEnabled(False)
        self.checkWake = QtGui.QCheckBox("Wake:")
        self.checkWake.clicked.connect(self.wakeChecked)
#         staticWake = QtGui.QLabel('Wake:')
#         staticWake.setAlignment(QtCore.Qt.AlignVCenter)
        self.getWake = QtGui.QLineEdit(self)
        self.getWake.setEnabled(False)
        self.getWake.setText("<Create New Wake>")
        self.actionWake = QtGui.QPushButton(Icon("AssignIt3.png"),'Assign')
        self.actionWake.released.connect(self.assignWake)
        self.actionWake.setEnabled(False)
        actionCreate = QtGui.QPushButton(Icon("WizardIt.png"),"Build")
        actionCreate.released.connect(self.buildSplash)
        
        mainlayout = QtGui.QVBoxLayout(self)
        layout_01 = QtGui.QGridLayout(self)
        layout_02 = QtGui.QHBoxLayout(self)
        
        mainlayout.addLayout(layout_01)
        mainlayout.addLayout(layout_02)

        layout_01.addWidget(staticObject,0,0)
        layout_01.addWidget(self.getObject,0,1)
        layout_01.addWidget(self.actionObject,0,2)
        layout_01.addWidget(self.checkWake,1,0)
        layout_01.addWidget(self.getWake,1,1)
        layout_01.addWidget(self.actionWake,1,2)
        layout_01.addWidget(self.checkOcean,2,0)
        layout_01.addWidget(self.getOcean,2,1)
        layout_01.addWidget(self.actionOcean,2,2)
        layout_02.addWidget(actionCreate)
                
        groupCreate.setLayout(mainlayout)
        return groupCreate
    
    def oceanChecked(self):
        if self.checkOcean.isChecked()==True:
            self.actionOcean.setEnabled(True)
        else:
            self.actionOcean.setIcon(Icon("AssignIt3.png"))
            self.getOcean.setText("<Create New Ocean>")
            self.actionOcean.setEnabled(False)
    
    def wakeChecked(self):
        if self.checkWake.isChecked()==True:
            self.actionWake.setEnabled(True)
        else:
            self.actionWake.setIcon(Icon("AssignIt3.png"))
            self.getWake.setText("<Create New Wake>")
            self.actionWake.setEnabled(False)
    
    def assignOcean(self):
        selected = cmds.ls(selection=True)
        if selected == []:
            self.getOcean.setText("<File is not qualified!>")
            self.actionOcean.setIcon(Icon("EmptyFileIt2.png"))
        else:
            self.getOcean.setText(str(selected[0]))
            self.actionOcean.setIcon(Icon("AssignedIt2.png"))
        return
        
    def assignObject(self):
        selected = cmds.ls(selection=True)
        if selected == []:
            self.getObject.setText("<File is not qualified!>")
            self.actionObject.setIcon(Icon("EmptyFileIt2.png"))
        else:
            self.getObject.setText(str(selected[0]))
            self.actionObject.setIcon(Icon("AssignedIt2.png"))
        return
        
    def assignWake(self):
        selected = cmds.ls(selection=True)
        if selected == []:
            self.getWake.setText("<File is not qualified!>")
            self.actionWake.setIcon(Icon("EmptyFileIt2.png"))
        else:
            self.getWake.setText(str(selected[0]))
            self.actionWake.setIcon(Icon("AssignedIt2.png"))
        return
        
    def buildSplash(self):            
        objectName = str(self.getObject.text())
        if self.checkWake.isChecked()==True:
            wakeEmitter = str(self.getWake.text())
        else:
            wakeEmitter = "OceanWakeEmitter1"
        if self.checkOcean.isChecked()==True:
            oceanShader = str(self.getOcean.text())
        else:
            oceanShader = "oceanShader1"
        
        ###Bcreating Splash Disc
        objectNameAxis = generator.getMaxAndMinAxis(objectName)
        #generator_Return: 0-maxX, 1-minX, 2-maxY, 3-minY, 4-maxZ, 5-minZ
        avrgX = objectNameAxis[0] - objectNameAxis[1]
        avrgZ = objectNameAxis[4] - objectNameAxis[5]
        avrgY = objectNameAxis[2] - objectNameAxis[3]
        if avrgX > avrgZ:
            SplashCurve = avrgX
        else:
            SplashCurve = avrgZ
        baseCurve = cmds.circle(name="base",normal=[0,1,0],radius=SplashCurve/1.5)
        headCurve = cmds.circle(name="head",normal=[0,1,0],radius=SplashCurve/2)
        cmds.move(0,(avrgY/4),0,headCurve)
        cmds.rebuildCurve ("base", ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=0, kt=0, s=100, d=7, tol=0.01)
        cmds.rebuildCurve ("head", ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=0, kt=0, s=100, d=7, tol=0.01)
        splashDisc = cmds.loft ("base", "head",name="%s_SplashDisc"%objectName, ch=1, u=1, c=0, ar=1, d=3, ss=int(avrgY+1), rn=0, po=0, rsn=True)
        #Return: 0-SplashDisc, 1-loft1
        cmds.delete(baseCurve,headCurve)    
        cmds.setAttr("%s.visibility"%splashDisc[0], False )
        objectPosition = cmds.xform(objectName, query=True, translation=True, worldSpace=True )
        cmds.move(objectPosition[0], 0, objectPosition[2], splashDisc[0])
        
        ###adding emitter and particle to Object
        objectNameEmitter = cmds.emitter(objectName,type='surface',rate=0,scaleRateByObjectSize=False,needParentUV=False,cycleEmission="none",
                           cycleInterval=1,speed=1,speedRandom=0,normalSpeed=1,tangentSpeed=0,maxDistance=0,minDistance=0,
                           directionX=1,directionY=0,directionZ=0,spread=0,name="%s_emitter"%objectName)
        #Return: 0-objectName, 1-objectName_emitter
        objectNameParticle = cmds.particle(name="%s_particle"%objectName)
        cmds.connectDynamic(objectNameParticle[0],emitters=objectNameEmitter[0])
        ###adding emitter and particle to Splash Disc
        splashDiscEmitter = cmds.emitter(splashDisc[0],type='surface',rate=0,scaleRateByObjectSize=False,needParentUV=False,cycleEmission="none",
                           cycleInterval=1,speed=1,speedRandom=1.5,normalSpeed=1,tangentSpeed=0,maxDistance=0,minDistance=0,
                           directionX=1,directionY=0,directionZ=0,spread=0,name="%s_emitter"%splashDisc[0])
        #Return: 0-SplashDisc, 1-SplashDisc_emitter
        splashDiscParticle = cmds.particle(name="%s_particle"%splashDisc[0])
        cmds.connectDynamic(splashDiscParticle[0],emitters=splashDiscEmitter[0])
        
        #connecting the X and Z object position to Splash Disc to follow 
        cmds.connectAttr("%s.translate.translateZ"%objectName, "%s.translate.translateZ"%splashDisc[0])
        cmds.connectAttr("%s.translate.translateX"%objectName, "%s.translate.translateX"%splashDisc[0])
        
        #setting up the splash Disc particle Setting 
        cmds.setAttr("%s.lifespanMode"%splashDiscParticle[1],3)
        cmds.setAttr("%s.lifespanRandom"%splashDiscParticle[1],0.5)
        cmds.setAttr("%s.conserve"%splashDiscParticle[1],0.983)
        cmds.setAttr("%s.inheritFactor"%splashDiscParticle[1],0.2)
        cmds.setAttr("%s.particleRenderType"%splashDiscParticle[1],5)
        cmds.addAttr(splashDiscParticle[1], keyable=True, ln="useLighting", at="bool", dv=False)
        cmds.addAttr(splashDiscParticle[1], ln="spriteScaleYPP", dt="doubleArray")
        cmds.addAttr(splashDiscParticle[1], ln="spriteScaleYPP0", dt="doubleArray")
        cmds.addAttr(splashDiscParticle[1], ln="spriteScaleXPP", dt="doubleArray")
        cmds.addAttr(splashDiscParticle[1], ln="spriteScaleXPP0", dt="doubleArray")
        cmds.addAttr(splashDiscParticle[1], ln="spriteTwistPP", dt="doubleArray")
        cmds.addAttr(splashDiscParticle[1], ln="spriteTwistPP0", dt="doubleArray")
        #creating Ramp for Splash Disc particle
        splashDiscParticle_spriteScaleXPP = cmds.arrayMapper(target=splashDiscParticle[1], destAttr="spriteScaleXPP", inputV="ageNormalized", type="ramp")
        ramp_spriteScaleXPP = cmds.listConnections(splashDiscParticle_spriteScaleXPP, type="ramp")
        ramp_spriteScaleXPP = cmds.rename(ramp_spriteScaleXPP[1], "%s_spriteScaleXPP_Rampe"%splashDiscParticle[1])
        cmds.setAttr("%s.colorEntryList[2].color"%ramp_spriteScaleXPP, 0,0,0)
        cmds.setAttr("%s.colorEntryList[2].position"%ramp_spriteScaleXPP, 1)
        cmds.setAttr("%s.colorEntryList[1].color"%ramp_spriteScaleXPP, 0.5,0.5,0.5)
        cmds.setAttr("%s.colorEntryList[1].position"%ramp_spriteScaleXPP, 0.165)
        cmds.setAttr("%s.colorEntryList[0].color"%ramp_spriteScaleXPP, 1,1,1)
        cmds.setAttr("%s.colorEntryList[0].position"%ramp_spriteScaleXPP, 0)
        
        splashDiscParticle_spriteScaleYPP = cmds.arrayMapper(target=splashDiscParticle[1], destAttr="spriteScaleYPP", inputV="ageNormalized", type="ramp")
        ramp_spriteScaleYPP = cmds.listConnections(splashDiscParticle_spriteScaleYPP, type="ramp")
        ramp_spriteScaleYPP = cmds.rename(ramp_spriteScaleYPP[1], "%s_SpriteScaleYPP_Rampe"%splashDiscParticle[1])
        cmds.setAttr("%s.colorEntryList[2].color"%ramp_spriteScaleYPP, 0,0,0)
        cmds.setAttr("%s.colorEntryList[2].position"%ramp_spriteScaleYPP, 1)
        cmds.setAttr("%s.colorEntryList[1].color"%ramp_spriteScaleYPP, 0.5,0.5,0.5)
        cmds.setAttr("%s.colorEntryList[1].position"%ramp_spriteScaleYPP, 0.165)
        cmds.setAttr("%s.colorEntryList[0].color"%ramp_spriteScaleYPP, 1,1,1)
        cmds.setAttr("%s.colorEntryList[0].position"%ramp_spriteScaleYPP, 0)
         
        #setting up the object particle Setting 
        cmds.setAttr("%s.lifespanMode"%objectNameParticle[1],3)
        cmds.setAttr("%s.particleRenderType"%objectNameParticle[1],7)
        cmds.addAttr(objectNameParticle[1], keyable=True, ln="threshold", at="float", min=0, max=10, dv=0.7)
        cmds.addAttr(objectNameParticle[1], keyable=True, ln="radius", at="float", min=0, max=10, dv=0.5)
        cmds.addAttr (objectNameParticle[1], ln="radiusPP", dt="doubleArray")
        #creating Ramp for object particle
        objectNameParticle_radiusPP = cmds.arrayMapper(target=objectNameParticle[1], destAttr="radiusPP", inputV="ageNormalized", type="ramp")
        ramp_radiusPP = cmds.listConnections(objectNameParticle_radiusPP, type="ramp")
        ramp_radiusPP = cmds.rename(ramp_radiusPP[1], "%s_RadiusPP_Rampe"%objectNameParticle[1])
        cmds.setAttr("%s.colorEntryList[3].color"%ramp_radiusPP, 0.056,0.056,0.056)
        cmds.setAttr("%s.colorEntryList[3].position"%ramp_radiusPP, 1)
        cmds.setAttr("%s.colorEntryList[2].color"%ramp_radiusPP, 0.223,0.223,0.223)
        cmds.setAttr("%s.colorEntryList[2].position"%ramp_radiusPP, 0.690)
        cmds.setAttr("%s.colorEntryList[1].color"%ramp_radiusPP, 0.178,0.178,0.178)
        cmds.setAttr("%s.colorEntryList[1].position"%ramp_radiusPP, 0.455)
        cmds.setAttr("%s.colorEntryList[0].color"%ramp_radiusPP, 0,0,0)
        cmds.setAttr("%s.colorEntryList[0].position"%ramp_radiusPP, 0)
         
        #adding gravity to SplashDisc
        splashDiscGravity = cmds.gravity(name="%s_GravityField"%splashDiscParticle[0], pos=[0,0,0], m=9.8, att=0, dx=0, dy=-1, dz=0, mxd=-1, vsh="none", vex=0, vof=[0,0,0], vsw=360, tsr=0.5)
        cmds.connectDynamic(splashDiscParticle[0], fields=splashDiscGravity)
         
        #adding gravity to Object
        objectNameGravity = cmds.uniform(name="%s_UniformField"%objectNameParticle[0], pos=[0,0,0], m=5, att=1, dx=1, dy=-1, dz=0, mxd=-1, vsh="none", vex=0, vof=[0,0,0], vsw=360, tsr=0.5)
        cmds.connectDynamic(objectNameParticle[0], fields=objectNameGravity)
        print objectNameGravity
        cmds.setAttr("%s.directionX"%objectNameGravity[0],0)
        cmds.setAttr("%s.directionY"%objectNameGravity[0],1)
        cmds.setAttr("%s.directionZ"%objectNameGravity[0],0)
        cmds.setAttr("%s.magnitude"%objectNameGravity[0],28)
         
        #adding Expression for Object and SplashDisc
        generator.objectNameParticleExpressionBeforeDynamics(objectNameParticle[1], oceanShader)
        generator.splashDiscParticleExpressionBeforeDynamics(splashDiscParticle[1], oceanShader)
        generator.splashDiscParticleExpressionAfterDynamics(splashDiscParticle[1])
        generator.splashDiscParticleExpressionCreation(splashDiscParticle[1])
        if "ocean_MainExpression" not in cmds.ls() :
            generator.createMainExpression(objectNameEmitter[1])
        if "ocean_MainExpression" in cmds.ls() :
            generator.editMainExpression(objectName, splashDiscEmitter[0], oceanShader, objectNameEmitter[1], wakeEmitter, splashDiscEmitter[1])
#         num=0 
        if "mainSplashDisc_Shader" not in cmds.ls():
            generator.shaderSetup()
#             cmds.select(splashDiscEmitter[0], replace=True)
#             cmds.sets(edit=True,forceElement="mainSplashDisc_ShaderSG")
            cmds.sets(splashDiscParticle, edit = True, forceElement = 'mainSplashDisc_ShaderSG')
        else:
            cmds.sets(splashDiscParticle, edit = True, forceElement = 'mainSplashDisc_ShaderSG')
#             while cmds.connectionInfo("mainSplashDisc_ShaderSG.dagSetMembers[%s]"%num,getExactDestination=True) != "":
#                 num+=1
#             cmds.connectAttr(splashDiscEmitter[1] + ".instObjGroups[0]", "mainSplashDisc_Shader.dagSetMembers[%s]"%num, force = True)
#         else:     
#             while cmds.connectionInfo("mainSplashDisc_ShaderSG.dagSetMembers[%s]"%num,getExactDestination=True) != "":
#                 num+=1
#             cmds.connectAttr(splashDiscEmitter[1] + ".instObjGroups[0]", "mainSplashDisc_Shader.dagSetMembers[%s]"%num, force = True)
#         pSphere1_SplashDisc.translateX = pSphere1.translateX;
#         pSphere1_SplashDisc.translateZ = pSphere1.translateZ;
        return  
     
    
    
    
    
    
    