# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
A breakdown window in Nuke which shows all inputs and what is out of date.

"""

import tank
import os, sys
import nuke, nukescripts
import sgtk

class SubmitToDeadline(tank.platform.Application):

    def init_app(self):
        """
        Called as the application is being initialized
        """


        # tk_submitToDeadline = self.import_module("tk_submitToDeadline")

        # self.app_handler = tk_submitToDeadline.submitToDeadline(self)
        # self.app_handler = self.hello()

        # # add stuff to main menu
        self.engine.register_command("Submit To Deadline...", self.main)

    def convertWriteNode(self):
        eng = sgtk.platform.current_engine()
        apps = eng.apps["tk-nuke-writenode"]
        if  apps.get_write_nodes():
            nodes = apps.get_write_nodes()[0]
            renderPath = apps.get_node_render_path(nodes)
            basePath = os.path.dirname(renderPath)
            versionFolder = basePath.split('/')[-1]
            if not os.path.exists(basePath):
                os.mkdir(basePath)
            if apps:
                apps.convert_to_write_nodes()
        else:
            apps.convert_from_write_nodes()
            apps = eng.apps["tk-nuke-writenode"]
            nodes = apps.get_write_nodes()[0]
            renderPath = apps.get_node_render_path(nodes)
            basePath = os.path.dirname(renderPath)
            versionFolder = basePath.split('/')[-1]
            if not os.path.exists(basePath):
                os.mkdir(basePath)
            if apps:
                apps.convert_to_write_nodes()

    def main(self):
        # Get the repository root
        try:
            stdout = None
            if os.path.exists( "C:/Program Files/Thinkbox/Deadline/bin/deadlinecommand.exe" ):
                stdout = os.popen( "deadlinecommand.exe GetRepositoryRoot" )
            else:
                stdout = os.popen( "deadlinecommand GetRepositoryRoot" )
            path = stdout.read()
            stdout.close()
            
            if path == "" or path == None:
                nuke.message( "The SubmitNukeToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is in your PATH, and that the Deadline Client has been configured to point to a valid Repository." )
            else:
                self.convertWriteNode()
                path += "/submission/Nuke"
                path = path.replace("\n","").replace( "\\", "/" )
                
                # Add the path to the system path
                print "Appending \"" + path + "\" to system path to import SubmitNukeToDeadline module"
                sys.path.append( path )

                # Import the script and call the main() function
                import SubmitNukeToDeadline
                SubmitNukeToDeadline.SubmitToDeadline( path )
        except IOError:
            nuke.message( "An error occurred while getting the repository root from Deadline. Please try again, or if this is a persistent problem, contact Deadline Support." )