import os, sys
import shutil
import maya.cmds as cmds
import maya.mel as mel
import xml.etree.ElementTree as xml
import maya.OpenMaya as om
import tank
from tank import Hook
from tank import TankError
## METALCORE / XML STUF
try:
    from mentalcore import mapi
    from mentalcore import mlib
except:
    debug(None, method = 'core_archive_lib', message = 'metalcore mapi and mlib failed to load!!', verbose = False)
    pass
## Now get the custom tools
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug
import core_archive_lib as coreLib
import shader_lib as shd
#reload(shd)
#reload(coreLib)

class PublishHook(Hook):
    """
    Single hook that implements publish functionality for secondary tasks
    """    
    def execute(self, tasks, work_template, comment, thumbnail_path, sg_task, primary_publish_path, progress_cb, **kwargs):
        """
        Main hook entry point
        :tasks:         List of secondary tasks to be published.  Each task is a 
                        dictionary containing the following keys:
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
        """""
        results = []

        for task in tasks:
            item = task["item"]
            output = task["output"]
            errors = []
            
            # report progress:
            progress_cb(0, "Publishing", task)

            if output["name"] == 'coreArchive':
                """
                Main coreArchive exporter
                """
                try:
                
                    self._publish_coreArchive_for_item(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)
                
                except Exception, e:
                    errors.append("Publish failed - %s" % e)
            elif output["name"] == 'copyHiRes':
                """
                Copies the high res files over to the publish sourceimages folder
                """
                try:
                    shd.repathFileNodesForWork()
                    self._publish_copyHiRes_for_item(item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb)
                    
                except Exception, e:
                    errors.append("Copy failed - %s" % e)
            else:
                # don't know how to publish this output types!
                errors.append("Don't know how to publish this item!")

        progress_cb(50)

        ## if there is anything to report then add to result
        if len(errors) > 0:
            ## add result:
            results.append({"task":task, "errors":errors})
        
        progress_cb(100)
        return results

    def _publish_coreArchive_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
        """
        Export an Alembic cache for the specified item and publish it
        to Shotgun.
        """
        group_name = '%s_CORE' % ''.join(item["name"].strip("|").split('_hrc')[0].split('_'))
        debug(None, method = '_publish_coreArchive_for_item', message = 'group_name: %s' % group_name, verbose = False)
        tank_type = output["tank_type"]
        publish_template = output["publish_template"]
        
        ## LOAD MENTALRAY FOR EXPORT
        if not cmds.pluginInfo( 'Mayatomr', query=True, loaded = True ):
            cmds.loadPlugin ('Mayatomr')
        debug(None, method = '_publish_coreArchive_for_item', message = 'MentalRay loaded successfully', verbose = False)
        
        ## SET MR AS THE RENDERER    
        cmds.setAttr('defaultRenderGlobals.currentRenderer','mentalRay', type = 'string')
        debug(None, method = '_publish_coreArchive_for_item', message = 'Set renderer to MRay', verbose = False)
        
        # get the current scene path and extract fields from it
        # using the work template:
        scene_path = os.path.abspath(cmds.file(query=True, sn= True))
        
        fields = work_template.get_fields(scene_path)
        
        publish_version = fields["version"]
        debug(None, method = '_publish_coreArchive_for_item', message = 'publish_version: %s' % publish_version, verbose = False)
        
        # update fields with the group name:
        fields["grp_name"] = group_name

        ## create the publish path by applying the fields 
        ## with the publish template:
        publish_path = publish_template.apply_fields(fields)
        
        cleanPublishPath = r'%s' % publish_path.split('.gz')[0]
        debug(None, method = '_publish_coreArchive_for_item', message = 'cleanPublishPath: %s' % cleanPublishPath, verbose = False)
        pathToVersionDir = os.path.dirname(cleanPublishPath)
        debug(None, method = '_publish_coreArchive_for_item', message = 'pathToVersionDir: %s' % pathToVersionDir, verbose = False)
        if not os.path.isdir(pathToVersionDir):
            os.mkdir(pathToVersionDir)

        try:
            print '====================='
            print 'Exporting coreArchive %s' % publish_path           
            debug(None, method = '_publish_coreArchive_for_item', message = 'Exporting coreArchive now...', verbose = False)
            
            mapi.export_archive(path = cleanPublishPath.replace('/', '\\'), objects = ["geo_hrc"], animation = False, start_frame = None, end_frame = None, compression = 9, materials = True)
            debug(None, method = '_publish_coreArchive_for_item', message = 'coreLib.export_archive successful...', verbose = False)
            
            ## Now register with shotgun
            self._register_publish(publish_path,
                                  group_name, 
                                  sg_task, 
                                  publish_version, 
                                  tank_type,
                                  comment,
                                  thumbnail_path, 
                                  [primary_publish_path])
            
            debug(None, method = '_publish_coreArchive_for_item', message = 'self._register_publish successful for %s' % finalPublishPath, verbose = False)
            print 'Finished coreArchive export...'
            print '====================='
            
        except Exception, e:
            raise TankError("Failed to export coreArchive %s " % coreArchivePath)

    def _publish_copyHiRes_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
        """
        Export the highres textures from work/maya/sourceimages to publish/sourceimages
        """
        group_name = item["name"].strip("|")
        tank_type = output["tank_type"]
        publish_template = output["publish_template"]

        # get the current scene path and extract fields from it
        # using the work template:
        scene_path = os.path.abspath(cmds.file(query=True, sn= True))
        fields = work_template.get_fields(scene_path)
        publish_version = fields["version"]

        # update fields with the group name:
        fields["grp_name"] = group_name

        ## create the publish path by applying the fields 
        ## with the publish template:
        publish_path = publish_template.apply_fields(fields)
        
        highResPublishPath = r'%s' % publish_path
        
        debug(None, method = '_publish_copyHiRes_for_item', message = 'highResPublishPath: %s' % highResPublishPath.replace('\\', '/'), verbose = False)
        try:
            self.parent.log_debug("Executing command: XML EXPORT PREP!")
            print '====================='
            print 'Copying the highRes textures %s' % publish_path

            shd.copyHiRes(destFolder = highResPublishPath.replace('\\', '/'))

            print 'Finished copying textures...'
            print '====================='
        except Exception, e:
            raise TankError("Failed to copy textures")

    def _register_publish(self, path, name, sg_task, publish_version, tank_type, comment, thumbnail_path, dependency_paths=None):
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
        if dependency_paths:
            print "================DEP===================="
            print '%s dependencies: \n\t%s' % (path, dependency_paths[0])
            print "========================================"
        return sg_data
