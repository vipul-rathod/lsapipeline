import sys, os
import maya.cmds as cmds
import maya.utils as mu
import maya.mel as mel
import getpass
try:
    import mentalcore
except:
    pass

userName = getpass.getuser()

if 'T:/software/bbbay' not in sys.path:
    sys.path.append('T:/software/bbbay')

import BBmaya.main_lib.BB_CONST as BB_CONST

### Now process for dev env for plugin path
MAYA_PLUGIN_PATH = "T:/software/bbbay/BBmaya/plugins/win/2013.5"

## Now load the plugins from the right paths
def loadPlugins():
    for eachPlugin in os.listdir(MAYA_PLUGIN_PATH):
        if eachPlugin.endswith('.mll'):
            try:
                print 'Loading %s/%s... ' % (MAYA_PLUGIN_PATH, eachPlugin)
                cmds.loadPlugin('%s/%s'  % (MAYA_PLUGIN_PATH, eachPlugin))
            except RuntimeError:
                cmds.warning('%s plugin failed to load.' % eachPlugin)
        elif eachPlugin.endswith('.py'):
            try:
                print 'Loading %s/%s... ' % (MAYA_PLUGIN_PATH, eachPlugin)
                cmds.loadPlugin('%s/%s.py'  % (MAYA_PLUGIN_PATH, eachPlugin))
            except RuntimeError:
                cmds.warning('%s failed to load.' % eachPlugin)
        else:
            pass
loadPlugins()

#mel.eval("hyperShadePanel;")
mel.eval("source \"sz_RenderView.mel\"")
print 'sz_RenderView.mel sourced successfully...'
mel.eval("source \"mayaPreviewRender.mel\"")
print 'mayaPreviewRender.mel sourced successfully...'
mel.eval("source \"mentalrayPreviewRender.mel\"")
print 'mentalrayPreviewRender.mel sourced successfully...'
mel.eval("source \"renderWindowPanel.mel\"")
print 'renderWindowPanel.mel sourced successfully...'

## Insist that mentalray is loaded at startup
cmds.evalDeferred("if cmds.pluginInfo( 'Mayatomr', query=True, loaded = True ) == 0 :cmds.loadPlugin ('Mayatomr')", lp = True)
print 'Mayatomr forced to load successfully...'

## ---- MENTALCORE STARTUP 
mu.executeDeferred('mentalcore.startup()')
print 'mentalcore.startup() forced to load successfully...'
mu.executeDeferred(mel.eval('bonusToolsMenu;'))
print 'bonusToolsMenu forced to load successfully...'