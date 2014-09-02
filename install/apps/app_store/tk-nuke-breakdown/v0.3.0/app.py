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


class NukeBreakdown(tank.platform.Application):

    def init_app(self):
        """
        Called as the application is being initialized
        """
        tk_nuke_breakdown = self.import_module("tk_nuke_breakdown")

        self.app_handler = tk_nuke_breakdown.AppHandler(self)

        # add stuff to main menu
        self.engine.register_command("Scene Breakdown...", self.app_handler.show_dialog)


