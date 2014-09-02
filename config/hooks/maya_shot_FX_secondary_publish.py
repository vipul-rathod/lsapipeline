import os, sys
import shutil
import maya.cmds as cmds
import maya.mel as mel
import tank
from tank import Hook
from tank import TankError
## Now get the custom tools
if 'T:/software/bubblebathbay/custom' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/custom')
if 'T:/software/bubblebathbay/install/apps/tk-bbb-mayaOcean' not in sys.path:
    sys.path.append('T:/software/bubblebathbay/install/apps/tk-bbb-mayaOcean')
from debug import debug
import utils as utils
import fluids_lib as fluidLib
import CONST as CONST
import maya_asset_MASTERCLEANUPCODE as cleanup
import fluidCaches as fluidCaches
#reload(fluidLib)
#reload(CONST)
#reload(cleanup)
#reload(fluidCaches)

class PublishHook(Hook):
    """
    Single hook that implements publish functionality for secondary tasks
    """
    def execute(self, tasks, work_template, comment, thumbnail_path, sg_task, primary_publish_path, progress_cb, **kwargs):
        """
        Main hook entry point
        :tasks:         List of secondary tasks to be published.  Each task is a
                        dictionary containing the following keys:(
                        {
                            item:   Dictionary
                                    This is the item returned by the scan hook
                                    {
                                        name:           String
                                        description:    String
                                        type:           String
                                        other_params:   Dictionary
                                    }

                            output: Dictionary
                                    This is the output as defined in the configuration - the
                                    primary output will always be named 'primary'
                                    {
                                        name:             String
                                        publish_template: template
                                        tank_type:        String
                                    }
                        }

        :work_template: template
                        This is the template defined in the config that
                        represents the current work file

        :comment:       String
                        The comment provided for the publish

        :thumbnail:     Path string
                        The default thumbnail provided for the publish

        :sg_task:       Dictionary (shotgun entity description)
                        The shotgun task to use for the publish

        :primary_publish_path: Path string
                        This is the path of the primary published file as returned
                        by the primary publish hook

        :progress_cb:   Function
                        A progress callback to log progress during pre-publish.  Call:

                            progress_cb(percentage, msg)

                        to report progress to the UI

        :returns:       A list of any tasks that had problems that need to be reported
                        in the UI.  Each item in the list should be a dictionary containing
                        the following keys:
                        {
                            task:   Dictionary
                                    This is the task that was passed into the hook and
                                    should not be modified
                                    {
                                        item:...
                                        output:...
                                    }

                            errors: List
                                    A list of error messages (strings) to report
                        }
        """
        debug(app = None, method = 'execute', message = 'Secondary publishes in progress...', verbose = False)
        results = []

        ## Clean the animation alembic bat now for a fresh publish
        pathToBatFile = CONST.PATHTOFXBAT
        if os.path.isfile(pathToBatFile):
            os.remove(pathToBatFile)

        for task in tasks:
            item = task["item"]
            output = task["output"]
            errors = []
            debug(app = None, method = 'execute', message = 'item: %s' % item, verbose = False)
            ##DEBUGG
            # report progress:
            geoGrp = ''
            progress_cb(0, "Processing Scene Secondaries now...", task)

            ## FX CACHES
            if item["type"] == "fx_caches":
                ## Note because we are tagging more than one maya Nodetype as an fx type we need to check the nodes for what they are and process these
                ## accordingly
                progress_cb(25, "Processing Fluid Cache %s now..." % item['name'], task)
                debug(app = None, method = 'execute', message = 'Processing Fluid Cache %s now...' % item['name'], verbose = False)

                ### Check for fluids get exported as fluid caches.
                if cmds.nodeType(cmds.listRelatives(item['name'], children = True))  == 'fluidTexture3D' or cmds.nodeType(item['name']) == 'fluidTexture3D':
                    debug(app = None, method = 'execute', message =  'Doing _publish_fx_caches_for_item now...',  verbose = False)
                    # Check if whether current fluid node has cache attached and if yes, don't cache again.
                    fluidsCached = fluidCaches._filter_cache_on_fluids([item['name']])
                    if not fluidsCached:
                        self._publish_fx_caches_for_item(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)

                ## Check for the fluid_hrc group which gets exported as an mb file
                elif item['name'] == 'fluids_hrc':
                    debug(app = None, method = 'execute', message =  'Doing _publish_fx_caches_for_item now...',  verbose = False)
                    self._publish_fx_caches_for_item(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)

                progress_cb(50, "DONE Processing Fluid Cache %s" % item['name'], task)
                progress_cb(75, "Copying Fluid Caches into server...", task)
                ### COPY THE CACHE FILES TO THE SERVER NOW
                ### Subprocess to copy files from the temp folder to the server
                import subprocess
                CTEMP           = CONST.CTMP
                BATCHNAME       = CONST.FXBATCHNAME
                p = subprocess.Popen(BATCHNAME, cwd=CTEMP, shell=True, bufsize=4096, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                stdout, stderr = p.communicate()
                progress_cb(100, "Fluid Caches copied to server successfully.", task)

            ## NPARTICLE CACHES
            elif item["type"] == "nparticle_caches":
                debug(app = None, method = 'execute', message =  'Doing _publish_nparticle_caches_for_item now...',  verbose = False)
                self._publish_nparticle_caches_for_item(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)

            ## FX RENDERS
            elif item["type"] == "fx_renders":
                debug(app = None, method = 'execute', message =  'Doing _publish_fx_renders_for_item now...',  verbose = False)
                self._publish_fx_renders_for_item(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)

            else:
                # don't know how to publish this output types!
                errors.append("Don't know how to publish this item! Contact your supervisor to build a hook for this type.")

            ## if there is anything to report then add to result
            if len(errors) > 0:
                ## add result:
                results.append({"task":task, "errors":errors})

            progress_cb(100, "Done Processing Inital Secondaries, moving to final caching....", task)

        return results

    def _publish_fx_caches_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
        """
        Export the Fluid Texture Caches
        """
        ## Do the regular Shotgun processing now
        group_name = item['name']
        debug(app = None, method = '_publish_fx_caches_for_item', message =  'group_name: %s' % group_name, verbose = False)

        tank_type = 'Alembic Cache'
        debug(app = None, method = '_publish_fx_caches_for_item', message =  'tank_type: %s' % tank_type, verbose = False)

        publish_template = output["publish_template"]
        debug(app = None, method = '_publish_fx_caches_for_item', message =  'publish_template: %s' % publish_template, verbose = False)

        # get the current scene path and extract fields from it
        # using the work template:
        scene_path = os.path.abspath(cmds.file(query=True, sn= True))
        debug(app = None, method = '_publish_fx_caches_for_item', message =  'scene_path: %s' % scene_path, verbose = False)

        fields = work_template.get_fields(scene_path)

        publish_version = fields["version"]

        # update fields with the group name:
        fields["grp_name"] = group_name

        ## create the publish path by applying the fields
        ## with the publish template:
        publish_path = publish_template.apply_fields(fields)
        debug(app = None, method = '_publish_fx_caches_for_item', message =  'publish_path: %s' % publish_path, verbose = False)

        tempFolder = r"C:\Temp%s" % publish_path.split("I:")[-1]
        debug(app = None, method = '_publish_fx_caches_for_item', message = 'tempFolder: %s' % tempFolder, verbose = False)

        #print 'CHECKING IF DIR %s EXISTS' % publish_path
        if not os.path.isdir(publish_path):
            os.mkdir(publish_path)
        ## If the temp folder doesn't exist make one now
        if not os.path.isdir(os.path.dirname(tempFolder)):
            os.makedirs(os.path.dirname(tempFolder))

        print '====================='
        if group_name == 'fluids_hrc':
            print 'EXPORTING FLUIDS_HRC TO %s' % '%s/%s.v%s' % (publish_path, group_name, publish_version)
            debug(app = None, method = '_publish_fx_caches_for_item', message =  'EXPORTING FLUIDS_HRC TO %s' % '%s/%s.v%s' % (publish_path, group_name, publish_version), verbose = False)
            ## Look for interactive fluids now
            for each in cmds.listRelatives('fluids_hrc', children = True):
                if 'interactive' in each:
                    cmds.delete(each)

            ## Now select and export the fluids group and fluid textures under it out to an mb file.
            cmds.select(group_name, r = True)
            cmds.file('%s/%s.v%s'% (publish_path, group_name, publish_version), options = "v=0;", constructionHistory = False, typ = "mayaBinary", es = True, force= True)
        else:
            ## Do the fluid caches now...
            print 'Exporting %s now to %s' % (group_name, publish_path)

            #################################
            #######PERFORM CACHE OF FX FLUIDS
            #################################
            caches = [CONST.FOAM_FLUID_SHAPENODE, CONST.WAKE_FLUID_SHAPENODE]
            fluidCaches._cacheWake(cachepath = tempFolder, oceanFluidTextures = group_name, fluids = caches)
            ## add to bat file
            ## Now write the bat file out for the file copy
            pathToBatFile = CONST.PATHTOFXBAT
            if not os.path.isfile(pathToBatFile):
                outfile = open(pathToBatFile, "w")
            else:
                outfile = open(pathToBatFile, "a")
            outfile.write( 'robocopy "%s" "%s" /e /move\n' % (tempFolder, publish_path) )
            outfile.close()

        self._register_publish(publish_path,
                               '%s_FX' % group_name,
                               sg_task,
                               publish_version,
                               tank_type,
                               comment,
                               thumbnail_path,
                               [primary_publish_path])
        print 'DONE exporting %s to %s' % (group_name, publish_path)
        print '====================='
        cmds.currentTime(1)

    def _publish_nparticle_caches_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
        """
        Export the nParticles
        """
        ## Do the regular Shotgun processing now
        group_name = item['name']
        debug(app = None, method = '_publish_fx_caches_for_item', message =  'group_name: %s' % group_name, verbose = False)

        tank_type = 'Alembic Cache'
        debug(app = None, method = '_publish_fx_caches_for_item', message =  'tank_type: %s' % tank_type, verbose = False)

        publish_template = output["publish_template"]
        debug(app = None, method = '_publish_fx_caches_for_item', message =  'publish_template: %s' % publish_template, verbose = False)

        # get the current scene path and extract fields from it
        # using the work template:
        scene_path = os.path.abspath(cmds.file(query=True, sn= True))
        debug(app = None, method = '_publish_fx_caches_for_item', message =  'scene_path: %s' % scene_path, verbose = False)

        fields = work_template.get_fields(scene_path)

        publish_version = fields["version"]

        # update fields with the group name:
        fields["grp_name"] = group_name

        ## create the publish path by applying the fields
        ## with the publish template:
        publish_path = publish_template.apply_fields(fields)
        debug(app = None, method = '_publish_nparticle_caches_for_item', message = 'publish_path: %s' % publish_path, verbose = False)

        tempFolder = r"C:\Temp%s" % publish_path.split("I:")[-1]
        debug(app = None, method = '_publish_nparticle_caches_for_item', message = 'tempFolder: %s' % tempFolder, verbose = False)

        ## Make folder if it is not there
        if not os.path.isdir(publish_path):
            os.mkdir(publish_path)
        ## If the temp folder doesn't exist make one now
        if not os.path.isdir(os.path.dirname(tempFolder)):
            os.makedirs(os.path.dirname(tempFolder))

        output = r'%s' % tempFolder
        startFrame = cmds.playbackOptions(q = True,  min = True)
        endFrame = cmds.playbackOptions(q = True,  max = True)
        [cmds.currentTime(startFrame) for i in range(2)]

        print '====================='
        print 'Exporting nparticle caches now to %s' % publish_path
        print 'group_name is %s' % group_name
        cmds.select(group_name, r = True)
        debug(None, method = '_publish_nparticle_caches_for_item', message = 'group_name: %s' % group_name, verbose = False)
        ## Set maya prefs so maya doesn't crash when caching nparticles
        cmds.dynPref(rt = 1, rf = 1, sr = 0, ec = 0)

        def nCacher(nParticleShape = []):
            """
            nCacher, how it works? Iterate through specified nParticleShape (iterate from start frame until the frame it emits first particle)
            By doing this, Maya won't crash when caching nParticles particularly Sprites with expressions.
            """

            if type(nParticleShape) == str:
                nParticleShape = [nParticleShape]
            elif type(nParticleShape) == list:
                nParticleShape = nParticleShape
            else:
                nParticleShape = False

            approved_nParticleShape = []
            if nParticleShape:
                # Get timeslider min and max
                startFrame = cmds.playbackOptions(min = 1, q = True)
                endFrame = cmds.playbackOptions(max = 1, q = True)

                for each in nParticleShape:
                    if cmds.objExists(each):
                        cmds.currentTime(startFrame)

                        while True:
                            ppCount = cmds.nParticle(each, count = True, q = True)
                            frame = cmds.currentTime(q = True)
                            if ppCount == 0:
                                if frame < endFrame:
                                    cmds.currentTime(frame + 1)
                                else:
                                    break
                            else:
                                cmds.currentTime(frame + 1)
                                approved_nParticleShape.append(each)
                                break

            return approved_nParticleShape

        nParticleShape = nCacher(nParticleShape = group_name)
        if nParticleShape:
            cmds.select(nParticleShape, replace = True)
            ## Cache command for particles
            mel.eval('doCreateNclothCache 4 { "3", "%s", "%s", "OneFile", "1", "%s","0","","0", "add", "0", "1", "5","0","1" };' % (startFrame, endFrame, output.replace('\\', '/')))

        ## add to bat file
        ## Now write the bat file out for the file copy
        pathToBatFile = CONST.PATHTOFXBAT
        if not os.path.isfile(pathToBatFile):
            outfile = open(pathToBatFile, "w")
        else:
            outfile = open(pathToBatFile, "a")
        outfile.write('copy %s %s\n' % (tempFolder, publish_path))
        outfile.close()

        self._register_publish(publish_path,
                               group_name,
                               sg_task,
                               publish_version,
                               tank_type,
                               comment,
                               thumbnail_path,
                               [primary_publish_path])
        print 'DONE exporting nparticle chaces'
        print '====================='

    def _publish_fx_renders_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
        """
        Render the FX Splashes (any nParticles) with Hardware Render Buffer (HWB)
        """
        ## Do the regular Shotgun processing now
        group_name = item['name'] # spriteSpray_nParticle_T_RShape
        debug(app = None, method = '_publish_fx_renders_for_item', message =  'group_name: %s' % group_name, verbose = False)

        tank_type = 'Rendered Image' # Alembic Cache
        debug(app = None, method = '_publish_fx_renders_for_item', message =  'tank_type: %s' % tank_type, verbose = False)

        publish_template = output["publish_template"] # <Sgtk TemplatePath maya_shot_fxRenderFinal: episodes/{Sequence}/{Shot}//FxLayers/R{version}>
        debug(app = None, method = '_publish_fx_renders_for_item', message =  'publish_template: %s' % publish_template, verbose = False)

        # Get the current scene path and extract fields from it
        # Using the work template:
        scene_path = os.path.abspath(cmds.file(query=True, sn= True)) # I:\bubblebathbay\episodes\ep106\ep106_sh030\FX\work\maya\ep106sh030.v025.ma
        debug(app = None, method = '_publish_fx_renders_for_item', message =  'scene_path: %s' % scene_path, verbose = False)

        fields = work_template.get_fields(scene_path) # {'Shot': u'ep106_sh030', 'name': u'ep106sh030', 'Sequence': u'ep106', 'Step': u'FX', 'version': 25, 'group_name': u'spriteSpray_nParticle_T_RShape'}

        publish_version = fields["version"]

        ## Update fields with the group_name
        fields["group_name"] = group_name

        ## Get episode and shot name from field directly
        epShotName = fields["name"]

        ## create the publish path by applying the fields
        ## with the publish template:
        publish_path = publish_template.apply_fields(fields) # K:\bubblebathbay\episodes\ep106\ep106_sh030\FxLayers\R025

        ## Make the publish directory for images rendering to be placed
        if not os.path.isdir(publish_path):
            os.mkdir(publish_path)

        # ## Hardware Render Buffer settings (LEGACY FOR NOW)
        # ## Get shotCam
        # shotCam = []
        # for cam in cmds.ls(cameras = 1):
        #     if not cmds.camera(cam, query = 1, startupCamera = 1):
        #         transform = cmds.listRelatives(cam, parent = True, fullPath = True)[0]
        #         if cmds.objExists('%s.type' % transform):
        #             if cmds.getAttr('%s.type' % transform) == 'shotCam':
        #                 shotCam.append(transform)
        #
        # if shotCam:
        #     debug(app = None, method = '_publish_fx_renders_for_item', message =  'shotCam for Hardware Render Buffer: %s' % shotCam[0], verbose = False)
        #
        #     ## Set the necessary correct settings for the HWB
        #     mel.eval('glRenderWin;')
        #     cmds.setAttr('defaultHardwareRenderGlobals.filename', epShotName, type = 'string')
        #     cmds.setAttr('defaultHardwareRenderGlobals.extension', 4)
        #     cmds.setAttr('defaultHardwareRenderGlobals.startFrame', cmds.playbackOptions(q = True, min = True))
        #     cmds.setAttr('defaultHardwareRenderGlobals.endFrame', cmds.playbackOptions(q = True, max = True))
        #     cmds.setAttr('defaultHardwareRenderGlobals.byFrame', 1)
        #     cmds.setAttr('defaultHardwareRenderGlobals.imageFormat', 19) # TARGA
        #     cmds.setAttr('defaultHardwareRenderGlobals.resolution', 'HD_720 1280 720 1.777', type = 'string')
        #     cmds.setAttr('defaultHardwareRenderGlobals.alphaSource', 0)
        #     cmds.setAttr('defaultHardwareRenderGlobals.writeZDepth', 0)
        #     cmds.setAttr('defaultHardwareRenderGlobals.lightingMode', 0)
        #     cmds.setAttr('defaultHardwareRenderGlobals.drawStyle', 3)
        #     cmds.setAttr('defaultHardwareRenderGlobals.texturing', 1)
        #     cmds.setAttr('defaultHardwareRenderGlobals.lineSmoothing', 1)
        #     cmds.setAttr('defaultHardwareRenderGlobals.fullImageResolution', 1)
        #     cmds.setAttr('defaultHardwareRenderGlobals.geometryMask', 1)
        #     cmds.setAttr('defaultHardwareRenderGlobals.backgroundColor', 0, 1, 0, type = 'double3')
        #     cmds.glRenderEditor('hardwareRenderView', edit = True, lookThru = shotCam[0])
        #     cmds.workspace(fileRule = ['images', publish_path])
        #     cmds.glRender(renderSequence = 'hardwareRenderView')

        ###############################################################################################
        ## Playblast Render
        ###############################################################################################
        # Get shotCams
        non_startup_cams = [cmds.listRelatives(cam, parent = True, fullPath = True)[0] for cam in cmds.ls(cameras = True) if not cmds.camera(cam, query = True, startupCamera = True)]
        shotCam = [cam for cam in non_startup_cams if cmds.objExists('%s.type' % cam)]
        shotCamShape = [cmds.listRelatives(cam, shapes = True, fullPath = True)[0] for cam in shotCam if cmds.getAttr('%s.type' % cam) == 'shotCam']

        # Get model panel
        model_panel = cmds.getPanel(withFocus = True)

        proceed = False
        if not shotCamShape:
            cmds.warning('No shotCam found in scene, please fix it first...!')
        else:
            if not cmds.objExists('ocean_dispShader'):
                cmds.warning('ocean_dispShader not found in scene, please fix it first...!')
            else:
                if not cmds.objExists('oceanPreviewPlane_heightF'):
                    cmds.warning('oceanPreviewPlane_heightF not found in scene, please fix it first...!')
                else:
                    if not 'modelPanel' in model_panel:
                        cmds.warning('No valid modelPanel in focus for playblasting...!')
                    else:
                        proceed = True

        if proceed == True:
            for cam in shotCamShape:
                ## Set appropriate camera display option settings for optimal playblasting
                cmds.setAttr('%s.overscan' % cam, 1)
                cmds.setAttr('%s.displayFilmGate' % cam, 0)
                cmds.setAttr('%s.displayResolution' % cam, 0)
                cmds.setAttr('%s.displayGateMask' % cam, 0)
                cmds.setAttr('%s.displayFieldChart' % cam, 0)
                cmds.setAttr('%s.displaySafeAction' % cam, 0)
                cmds.setAttr('%s.displaySafeTitle' % cam, 0)
                cmds.setAttr('%s.displayFilmPivot' % cam, 0)
                cmds.setAttr('%s.displayFilmOrigin' % cam, 0)

            ## Set appropriate "SHOW" to modelPanel
            cmds.modelEditor(model_panel, edit = True, displayLights = 'none')
            cmds.modelEditor(model_panel, edit = True, displayLights = 'default', camera = shotCamShape[0], allObjects = False, polymeshes = True, nParticles = True, manipulators = True, pluginShapes = True, pluginObjects = ['gpuCacheDisplayFilter', True], useDefaultMaterial = True, displayAppearance = 'flatShaded', displayTextures = True)

            ## Set lambert1 to green matte
            cmds.setAttr("lambert1.color", 0, 10, 0, type = 'double3')
            cmds.setAttr("lambert1.transparency", 1, 1, 1, type = 'double3')
            cmds.setAttr("lambert1.ambientColor", 0, 10, 0, type = 'double3')
            cmds.setAttr("lambert1.incandescence", 0, 10, 0, type = 'double3')
            cmds.setAttr("lambert1.diffuse", 0)
            cmds.setAttr("lambert1.translucence", 0)
            cmds.setAttr("lambert1.translucenceDepth", 0)
            cmds.setAttr("lambert1.translucenceFocus", 0)

            ## Set ocean shader to green matte
            if cmds.isConnected('ocean_dispShader.outColor', 'oceanPreviewPlane_heightF.color'):
                cmds.disconnectAttr('ocean_dispShader.outColor', 'oceanPreviewPlane_heightF.color')
                cmds.setAttr('oceanPreviewPlane_heightF.color', 0, 1, 0, type = 'double3')

            ## Set view port BG to green matte
            default_bg_color = cmds.displayRGBColor('background', q = True)
            default_bgTop_color = cmds.displayRGBColor('backgroundTop', q = True)
            default_bgBtm_color = cmds.displayRGBColor('backgroundBottom', q = True)
            cmds.displayRGBColor('background', 0, 1, 0)
            cmds.displayRGBColor('backgroundTop', 0, 1, 0)
            cmds.displayRGBColor('backgroundBottom', 0, 1, 0)

            ## Get timeslider min/max
            min = cmds.playbackOptions(min = True, q = True)
            max = cmds.playbackOptions(max = True, q = True)

            ## Force current time to min of time slider to avoid popping at frame 1 issue
            [cmds.currentTime(min) for i in range(2)]

            ## Now find the fx stuff and make sure the groups are visible and good for playblasting
            grps = ['OCEAN_hrc', 'oceanPreviewPlane_prv']
            for eachGrp in grps:
                if cmds.objExists(eachGrp):
                    cmds.setAttr('%s.visibility' % eachGrp, True)
            cmds.select(clear = True)

            ## Find all mesh in scene that has smoothed checked and Mentalray preview smooth them...
            mesh_with_smoothTag = [cmds.listRelatives(mesh, parent = True, fullPath = True)[0] for mesh in cmds.ls(type = 'mesh') if cmds.objExists('%s.smoothed' % cmds.listRelatives(mesh, parent = True, fullPath = True)[0])]
            mesh_with_smoothTag = [mesh for mesh in mesh_with_smoothTag if cmds.getAttr('%s.smoothed' % mesh)]
            [cmds.displaySmoothness(each, polygonObject = 3) for each in mesh_with_smoothTag if 'CHAR_' in each]

            ## Playblast rendering
            cmds.playblast( filename = os.path.join(publish_path, epShotName).replace('\\', '/'),
                            clearCache = True,
                            startTime = min,
                            endTime = max,
                            viewer = False,
                            forceOverwrite = True,
                            format = 'image',
                            compression = 'png',
                            framePadding = 4,
                            offScreen = True,
                            options = False,
                            percent = 100,
                            quality = 100,
                            sequenceTime = False,
                            showOrnaments = False,
                            widthHeight = [(1280 * 3), (720 * 3)]
                            )

            ## Find all mesh in scene and un-preview smooth them...
            [cmds.displaySmoothness(mesh, polygonObject = 1) for mesh in cmds.ls(type = 'mesh')]

            ## After playblast, set back the scene BG's color as default
            cmds.displayRGBColor('background', default_bg_color[0], default_bg_color[1], default_bg_color[2])
            cmds.displayRGBColor('backgroundTop', default_bgTop_color[0], default_bgTop_color[1], default_bgTop_color[2])
            cmds.displayRGBColor('backgroundBottom', default_bgBtm_color[0], default_bgBtm_color[1], default_bgBtm_color[2])

            ## Set appropriate "SHOW" to modelPanel back...
            cmds.modelEditor(model_panel, edit = True, useDefaultMaterial = False, displayTextures = False, displayAppearance = 'smoothShaded', activeOnly = False)

            ## Set lambert1 to default
            cmds.setAttr("lambert1.color", 0.5, 0.5, 0.5, type = 'double3')
            cmds.setAttr("lambert1.transparency", 0, 0, 0, type = 'double3')
            cmds.setAttr("lambert1.ambientColor", 0, 0, 0, type = 'double3')
            cmds.setAttr("lambert1.incandescence", 0, 0, 0, type = 'double3')
            cmds.setAttr("lambert1.diffuse", 0.8)
            cmds.setAttr("lambert1.translucence", 0)
            cmds.setAttr("lambert1.translucenceDepth", 0.5)
            cmds.setAttr("lambert1.translucenceFocus", 0.5)

            ## Set ocean shader to default color
            if not cmds.isConnected('ocean_dispShader.outColor', 'oceanPreviewPlane_heightF.color'):
                cmds.connectAttr('ocean_dispShader.outColor', 'oceanPreviewPlane_heightF.color', force = True)

            ## Finally after render, register publish to shotgun...
            self._register_publish(publish_path,
                                   group_name,
                                   sg_task,
                                   publish_version,
                                   tank_type,
                                   comment,
                                   thumbnail_path,
                                   [primary_publish_path])
            print 'Successfully rendered nParticles Splashes to %s...' % os.path.join(publish_path, epShotName).replace('\\', '/')
            print '=================================================='

    def _register_publish(self, path, name, sg_task, publish_version, tank_type, comment, thumbnail_path, dependency_paths = None):
        """
        Helper method to register publish using the
        specified publish info.
        """
        # construct args:
        args = {
            "tk": self.parent.tank,
            "context": self.parent.context,
            "comment": comment,
            "path": path,
            "name": name,
            "version_number": publish_version,
            "thumbnail_path": thumbnail_path,
            "task": sg_task,
            "dependency_paths": dependency_paths,
            "published_file_type":tank_type,
        }

        # register publish;
        sg_data = tank.util.register_publish(**args)
        return sg_data