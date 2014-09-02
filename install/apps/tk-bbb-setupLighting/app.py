"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db
import os
def cleanTOD(rootFolder = 'I:/lsapipeline/fx/presets/Lighting/mia_physicalsky/'):
    for eachFile in os.listdir(rootFolder):
        if 'tod_' in eachFile:
            newName = eachFile.split('tod_')[-1]
            print newName
            os.rename('%s%s'% (rootFolder, eachFile), '%s%s' % (rootFolder, newName)) 
        
cleanTOD('I:/lsapipeline/fx/presets/Lighting/mia_physicalsky/')
cleanTOD('I:/lsapipeline/fx/presets/Lighting/mia_physicalsun/')
cleanTOD('I:/lsapipeline/fx/presets/Lighting/transform/')
"""
import os, getpass, sys
import tank.templatekey
import shutil
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
import maya.cmds as cmds
import maya.mel as mel
try:
    from mentalcore import mapi
except:
    pass
from functools import partial
from tank import TankError
import sgtk

## Now get the custom tools
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')

if 'T:/software/lsapipeline/install/apps/tk-bbb-setupLighting' not in sys.path:
    sys.path.append('T:/software/lsapipeline/install/apps/tk-bbb-setupLighting')

if 'T:/software/lsapipeline/install/apps/tk-submit-mayaplayblast' not in sys.path:
    sys.path.append('T:/software/lsapipeline/install/apps/tk-submit-mayaplayblast')

import shader_lib as shd
import maya_genericSettings as settings
from debug import debug
from UploaderThread import UploaderThread
from InputPrompt import InputPrompt
import maya_asset_MASTERCLEANUPCODE as cleanup
#reload(settings)
#reload(cleanup)
#reload(shd)

class SetupLighting(Application):
    def init_app(self):
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the SetupLighting application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")
        getDisplayName = self.get_setting('display_name')
        self.engine.register_command(getDisplayName, self.run_app)
        debug(self, method = 'init_app', message = 'SetupLighting Loaded...', verbose = False)

    def run_app(self):
        debug(self, method = 'run_app', message = 'SetupLighting...', verbose = False)
        getDisplayName = self.get_setting('display_name')
        self.engine.show_dialog(getDisplayName, self, MainUI, self)


class BB_Widget_vr(QtGui.QFrame):
    def __init__(self, parent = None):
        """ Builds a horizontal line for uis to use"""
        QtGui.QFrame.__init__(self, parent)
        self.setFrameShape(QtGui.QFrame.VLine) 
        self.setFrameShadow(QtGui.QFrame.Sunken)


class MainUI(QtGui.QWidget):
    """
    UI for the lighting setup
    """
    def __init__(self, app):
        QtGui.QWidget.__init__(self)
        self.app = app
        debug(app = self.app, method = 'MainUI', message = 'MainUI initialized...', verbose = False)
        #self.tk = sgtk.sgtk_from_path("T:/software/bubblebathbay")
        self.mainLayout = QtGui.QVBoxLayout(self)
        debug(app = self.app, method = 'MainUI', message = 'mainLayout built...', verbose = False)
        ## Time of Day
        self.todGroupBox = QtGui.QGroupBox(self)
        self.todGroupBox.setTitle('Time of Day:')
        debug(app = self.app, method = 'MainUI', message = 'self.todGroupBox built...', verbose = False)

        self.todLayout = QtGui.QHBoxLayout(self.todGroupBox)
        debug(app = self.app, method = 'MainUI', message = 'self.todLayout built...', verbose = False)
        
        ## Now do the checkBoxes
        self.afternoonLayout = QtGui.QVBoxLayout(self)
        self.afternoonCBox = QtGui.QRadioButton('Afternoon')
        self.afternoonCBox.setChecked(True)
        self.afternoonCBox.setAutoExclusive(True)
        self.afternoonButton = QtGui.QPushButton('Set Now')
        self.afternoonButton.released.connect(partial(self.setTOD, self.afternoonCBox, 'afternoon'))
        self.afternoonLayout.addWidget(self.afternoonCBox)
        self.afternoonLayout.addWidget(self.afternoonButton)

        self.dawnLayout = QtGui.QVBoxLayout(self)
        self.dawnCBox = QtGui.QRadioButton('Dawn')
        self.dawnCBox.setAutoExclusive(True)
        self.dawnButton = QtGui.QPushButton('Set Now')
        self.dawnButton.released.connect(partial(self.setTOD, self.dawnCBox, 'dawn'))
        self.dawnLayout.addWidget(self.dawnCBox)
        self.dawnLayout.addWidget(self.dawnButton)

        self.duskLayout = QtGui.QVBoxLayout(self)
        self.duskCBox = QtGui.QRadioButton('Dusk')
        self.duskCBox.setAutoExclusive(True)
        self.duskButton = QtGui.QPushButton('Set Now')
        self.duskButton.released.connect(partial(self.setTOD, self.duskCBox, 'dusk'))
        self.duskLayout.addWidget(self.duskCBox)
        self.duskLayout.addWidget(self.duskButton)

        self.middayLayout = QtGui.QVBoxLayout(self)
        self.middayCBox = QtGui.QRadioButton('Midday')
        self.middayCBox.setAutoExclusive(True)
        self.middayButton = QtGui.QPushButton('Set Now')
        self.middayButton.released.connect(partial(self.setTOD, self.middayCBox, 'midday'))
        self.middayLayout.addWidget(self.middayCBox)
        self.middayLayout.addWidget(self.middayButton)

        self.morningLayout = QtGui.QVBoxLayout(self)
        self.morningCBox = QtGui.QRadioButton('Morning')
        self.morningCBox.setAutoExclusive(True)
        self.morningButton = QtGui.QPushButton('Set Now')
        self.morningButton.released.connect(partial(self.setTOD, self.morningCBox, 'morning'))
        self.morningLayout.addWidget(self.morningCBox)
        self.morningLayout.addWidget(self.morningButton)

        self.nightLayout = QtGui.QVBoxLayout(self)
        self.nightCBox = QtGui.QRadioButton('Night')
        self.nightCBox.setAutoExclusive(True)
        self.nightButton = QtGui.QPushButton('Set Now')
        self.nightButton.released.connect(partial(self.setTOD, self.nightCBox, 'night'))
        self.nightLayout.addWidget(self.nightCBox)
        self.nightLayout.addWidget(self.nightButton)

        self.sunriseLayout = QtGui.QVBoxLayout(self)
        self.sunriseCBox = QtGui.QRadioButton('Sunrise')
        self.sunriseCBox.setAutoExclusive(True) 
        self.sunriseButton = QtGui.QPushButton('Set Now')
        self.sunriseButton.released.connect(partial(self.setTOD, self.sunriseCBox, 'sunrise'))
        self.sunriseLayout.addWidget(self.sunriseCBox)
        self.sunriseLayout.addWidget(self.sunriseButton)

        self.sunsetLayout = QtGui.QVBoxLayout(self)
        self.sunsetCBox = QtGui.QRadioButton('SunSet')
        self.sunsetCBox.setAutoExclusive(True)
        self.sunsetButton = QtGui.QPushButton('Set Now')
        self.sunsetButton.released.connect(partial(self.setTOD, self.sunsetCBox, 'sunset'))
        self.sunsetLayout.addWidget(self.sunsetCBox)
        self.sunsetLayout.addWidget(self.sunsetButton)
         
        self.todLayout.addLayout(self.dawnLayout)
        self.splitter01 = BB_Widget_vr()
        self.todLayout.addWidget(self.splitter01)
        self.todLayout.addLayout(self.sunriseLayout)
        self.splitter02 = BB_Widget_vr()
        self.todLayout.addWidget(self.splitter02)
        self.todLayout.addLayout(self.morningLayout)
        self.splitter03 = BB_Widget_vr()
        self.todLayout.addWidget(self.splitter03)
        self.todLayout.addLayout(self.middayLayout)
        self.splitter04 = BB_Widget_vr()
        self.todLayout.addWidget(self.splitter04)
        self.todLayout.addLayout(self.afternoonLayout)
        self.splitter05 = BB_Widget_vr()
        self.todLayout.addWidget(self.splitter05)
        self.todLayout.addLayout(self.sunsetLayout)
        self.splitter06 = BB_Widget_vr()
        self.todLayout.addWidget(self.splitter06)
        self.todLayout.addLayout(self.duskLayout)
        self.splitter07 = BB_Widget_vr()
        self.todLayout.addWidget(self.splitter07)
        self.todLayout.addLayout(self.nightLayout)

        self.fixBBBLightDirectionButton = QtGui.QPushButton('FIX LIGHT WORLD ROTATION! (USE WITH CAUTION)')
        self.fixBBBLightDirectionButton.released.connect(self.fixLightWorldRotation)
        
        self.buildTODButton = QtGui.QPushButton('SETUP NOW...')
        self.buildTODButton.released.connect(self.doTODLoad)
        
        self.redoSmoothAttrAttachButton = QtGui.QPushButton('Rebuild subDiv connections...')
        self.redoSmoothAttrAttachButton.released.connect(partial(settings.attachMentalRaySubDiv))

        self.deleteSetupButton = QtGui.QPushButton('Delete Setup!')
        self.deleteSetupButton.setStyleSheet("QPushButton {background: dark red}")
        self.deleteSetupButton.released.connect(self.deleteSetup)

        debug(app = self.app, method = 'MainUI', message = 'Widgets built...', verbose = False)
        
        self.mainLayout.addWidget(self.todGroupBox)
        self.mainLayout.addWidget(self.fixBBBLightDirectionButton)
        self.mainLayout.addWidget(self.buildTODButton)
        self.mainLayout.addWidget(self.redoSmoothAttrAttachButton)
        self.mainLayout.addWidget(self.deleteSetupButton)
        self.mainLayout.addStretch(1)
        
        ## Set the renderglobals on app load
        settings._setRenderGlobals()
        
        ## Check for the base nodes if they exist turn the buttons on...
        self.setButtonStates()

    def fixLightWorldRotation(self):
        if cmds.objExists('LIGHTS_hrc'):
            cmds.setAttr('LIGHTS_hrc.rotateY', -90)

    def setButtonStates(self):
        """
        Used to Check for the base nodes if they exist turn the buttons on...
        """
        buttons = [self.afternoonButton, self.dawnButton, self.duskButton, self.middayButton, self.morningButton, self.sunriseButton, self.sunsetButton, self.nightButton]
        ##sunDirection#######################################
        if not cmds.objExists('sunDirection'):
            for eachButton in buttons:
                eachButton.setEnabled(False)
        else:
            for eachButton in buttons:
                eachButton.setEnabled(True)
        
        ##mia_physicalsky1#######################################
        if not cmds.objExists('mia_physicalsky1'):
            for eachButton in buttons:
                eachButton.setEnabled(False)            
        else:
            for eachButton in buttons:
                eachButton.setEnabled(True)
        
        ##mia_physicalsun1########################################
        if not cmds.objExists('mia_physicalsun1'):
            for eachButton in buttons:
                eachButton.setEnabled(False)
        else:
            for eachButton in buttons:
                eachButton.setEnabled(True)

    def getCheckBox(self):
        """
        Finds the checked checkbox
        """
        self.checkBoxList = [self.afternoonCBox, self.dawnCBox, self.duskCBox, self.middayCBox, self.morningCBox, self.nightCBox, self.sunriseCBox, self.sunsetCBox]
        for each in self.checkBoxList:
            if each.isChecked():
                return each.text()
    
    def setTOD(self, chxBox = '', TODay = ''):
        """
        Used to set the tod presets independently of the main setup.
        """
        debug(app = self.app, method = 'setTOD', message = 'chxBox ....%s' % chxBox, verbose = False)
        pathToSunDir = self.app.get_template('sunDirectionTemplate')
        pathToPhysicalSky = self.app.get_template('mia_physicalskyTemplate')
        pathToPyhsicalSun = self.app.get_template('mia_physicalsunTemplate')
      
        sunPresetPath = r'%s' % pathToSunDir.apply_fields({'presetName' : '%s' % TODay})
        physicalSkyPresetPath = r'%s' % pathToPhysicalSky.apply_fields({'presetName' : '%s' % TODay})
        physicalSunPresetPath = r'%s' % pathToPyhsicalSun.apply_fields({'presetName' : '%s' % TODay})

        ## Apply preset
        mel.eval("""applyPresetToNode \"sunDirection\" "" "" \"%s\" 1;""" % sunPresetPath.replace('\\', '/'))
        mel.eval("""applyPresetToNode \"mia_physicalsky1\" "" "" \"%s\" 1;""" % physicalSkyPresetPath.replace('\\', '/'))
        mel.eval("""applyPresetToNode \"mia_physicalsun1\" "" "" \"%s\" 1;""" % physicalSunPresetPath.replace('\\', '/'))
        cmds.setAttr("mia_physicalsun1.shadow_softness",4)
        cmds.setAttr("mia_physicalsun1.samples",24)
        
        debug(app = self.app, method = 'setTOD', message = 'Presets for %s applied successfully....' % TODay, verbose = False)
        chxBox.setChecked(True)
    
    def doTODLoad(self):
        """
        Main time of day load and setup
        """
        TODay = self.getCheckBox().lower()
        debug(app = self.app, method = 'doTODLoad', message = 'TODay...%s' % TODay, verbose = False)

        pathToSunDir        = self.app.get_template('sunDirectionTemplate')
        pathToPhysicalSky   = self.app.get_template('mia_physicalskyTemplate')
        pathToPyhsicalSun   = self.app.get_template('mia_physicalsunTemplate')
        debug(app = self.app, method = 'doTODLoad', message = 'pathToSunDir...%s' % pathToSunDir, verbose = False)
        debug(app = self.app, method = 'doTODLoad', message = 'pathToPhysicalSky...%s' % pathToPhysicalSky, verbose = False)
        debug(app = self.app, method = 'doTODLoad', message = 'pathToPyhsicalSun...%s' % pathToPyhsicalSun, verbose = False)

        sunPresetPath           = r'%s' % pathToSunDir.apply_fields({'presetName' : '%s' % TODay})
        physicalSkyPresetPath   = r'%s' % pathToPhysicalSky.apply_fields({'presetName' : '%s' % TODay})
        physicalSunPresetPath   = r'%s' % pathToPyhsicalSun.apply_fields({'presetName' : '%s' % TODay})
        debug(app = self.app, method = 'doTODLoad', message = 'sunPresetPath...%s' % sunPresetPath.replace('\\', '/'), verbose = False)
        debug(app = self.app, method = 'doTODLoad', message = 'physicalSkyPresetPath...%s' % physicalSkyPresetPath.replace('\\', '/'), verbose = False)
        debug(app = self.app, method = 'doTODLoad', message = 'physicalSunPresetPath...%s' % physicalSunPresetPath.replace('\\', '/'), verbose = False)

        ## Create sunSky
        if cmds.objExists('sunDirection'):
            cmds.delete('sunDirection')

        cmds.setAttr('defaultRenderGlobals.currentRenderer','mentalRay', type = 'string')
        mel.eval("unifiedRenderGlobalsWindow;")
        mel.eval("int $index = 6;")
        mel.eval("string $renderer = `currentRenderer`;")
        mel.eval("print $renderer")
        mel.eval("string $tabLayout = `getRendererTabLayout $renderer`;")
        mel.eval("print $tabLayout")
        mel.eval("tabLayout -e -sti $index $tabLayout;")
        mel.eval("fillSelectedTabForCurrentRenderer;")

        ## NOW DO THE MAYA BUILD FOR PHYSICAL SKY Note this builds a new directional light every time which is why we delete the old one!!
        ## remove the olds

        if cmds.objExists('sunDirection'):
            cmds.delete('sunDirection')
        try:
            for each in cmds.ls(type = 'mia_physicalsky'):
                cmds.delete(each)
        except:
            pass
        try:
            for each in cmds.ls(type = 'mia_physicalsun'):
                cmds.delete(each)
        except:
            pass
        try:
            for each in cmds.ls(type = 'mia_exposure_simple'):
                cmds.delete(each)
        except:
            pass

        ## Now do the sun and sky setup
        mel.eval("miCreateSunSky;")
        ##
        try:
            cmds.disconnectAttr('mia_physicalsky1.redblueshift','mia_physicalsun1.redblueshift')
        except:
            pass
        try:
            cmds.disconnectAttr('mia_physicalsky1.saturation','mia_physicalsun1.saturation')
        except:
            pass
        try:
            cmds.disconnectAttr('mia_physicalsky1.multiplier','mia_physicalsun1.multiplier')
        except:
            pass

        ## Apply preset
        mel.eval("""applyPresetToNode \"sunDirection\" "" "" \"%s\" 1;""" % sunPresetPath.replace('\\', '/'))
        mel.eval("""applyPresetToNode \"mia_physicalsky1\" "" "" \"%s\" 1;""" % physicalSkyPresetPath.replace('\\', '/'))
        mel.eval("""applyPresetToNode \"mia_physicalsun1\" "" "" \"%s\" 1;""" % physicalSunPresetPath.replace('\\', '/'))
        cmds.setAttr("mia_physicalsun1.shadow_softness",4)
        cmds.setAttr("mia_physicalsun1.samples",24)
        debug(app = self.app, method = 'doTODLoad', message = 'Presets applied successfully....', verbose = False)

        # ## Create cloudLayer
        # if not cmds.objExists('cloud_LYR'):
        #     debug(app = self.app, method = 'doTODLoad', message = 'Building cloud_LYR....', verbose = False)
        #     cmds.createRenderLayer(name = 'cloud_LYR')
        #     debug(app = self.app, method = 'doTODLoad', message = 'cloud_LYR built.....', verbose = False)

        debug(app = self.app, method = 'doTODLoad', message = 'Cleaning to LIGHTS_hrc.....', verbose = False)
        if not cmds.objExists('LIGHTS_hrc'):
            cmds.group(n = 'LIGHTS_hrc', em = True)
        try:
            cmds.parent('sunDirection', 'LIGHTS_hrc')
        except:
            pass

        ## Setup exposure
        shd.buildExposure()

        ## Check the buttons states
        self.setButtonStates()

        ## Set the default render passes
        debug(app = self.app, method = 'doTODLoad', message = 'Building renderPasses now.....', verbose = False)
        shd.setup_MC_renderPasses()

        debug(self.app, method = 'doTODLoad', message = 'Creating custom passes...', verbose = False)
        shd.buildCustomMCRenderPasses()

        ## Now attach all the objects with smoothed attrs ON to a subD node for rendering nice smooth curves...
        ## We are doing this here and not in the fetchLightingShaders because we want to also create a smooth for the SRF step for their renders!
        debug(app = self.app, method = 'doTODLoad', message = 'attachMentalRaySubDiv now.....', verbose = False)
        settings.attachMentalRaySubDiv()

        # cmds.editRenderLayerMembers('cloud_LYR', 'sunDirection', noRecurse = True)

    def deleteSetup(self):
        '''
        Do a complete clean-up of various nodes that setup lighting creates...
        '''
        try:    cmds.delete( _ls(nodeType = 'transform', topTransform = True, stringFilter = 'LIGHTS_hrc', unlockNode = True) )
        except: pass
        try:    cmds.delete( _ls(nodeType = 'mia_exposure_simple', topTransform = True, stringFilter = '', unlockNode = True) )
        except: pass
        try:    cmds.delete( _ls(nodeType = 'mia_physicalsky', topTransform = True, stringFilter = '', unlockNode = True) )
        except: pass
        try:    cmds.delete( _ls(nodeType = 'mia_physicalsun', topTransform = True, stringFilter = '', unlockNode = True) )
        except: pass
#         try:    cmds.delete( _ls(nodeType = 'core_globals', topTransform = True, stringFilter = '', unlockNode = True) )
#         except: pass
#         try:    cmds.delete( _ls(nodeType = 'core_lens', topTransform = True, stringFilter = '', unlockNode = True) )
#         except: pass
        try:    cmds.delete( _ls(nodeType = 'core_renderpass', topTransform = True, stringFilter = '', unlockNode = True) )
        except: pass
        try:    cmds.delete( _ls(nodeType = 'mentalraySubdivApprox', topTransform = True, stringFilter = '', unlockNode = True) )
        except: pass
        try:    cmds.delete( _ls(nodeType = 'renderLayer', topTransform = True, stringFilter = 'cloud_LYR', unlockNode = True) )
        except: pass

    def destroy_app(self):
        self.log_debug("Destroying SetupLighting")

# ls on steroid, good for quick mass deletion of various node types, keeps the script cleaner too

def _ls(nodeType = '', topTransform = True, stringFilter = '', unlockNode = False):
    if nodeType:
        nodes = cmds.ls(type = nodeType)
        if nodes:
            final_nodes = []
            for each in nodes:
                each = cmds.ls(each, long = True)[0]
                top_transform = cmds.listRelatives(each, parent = True, fullPath = True) if topTransform else None
                final_node = top_transform[0] if top_transform else each

                if unlockNode:
                    try:	cmds.lockNode(final_node, lock = False)
                    except:	mel.eval('warning "Failed to unlock %s, skipping...";' % final_node)

                if stringFilter:
                    if stringFilter in final_node:
                        if final_node not in final_nodes:
                            final_nodes.append(final_node)
                else:
                    if final_node not in final_nodes:
                        final_nodes.append(final_node)

            return final_nodes

        return []