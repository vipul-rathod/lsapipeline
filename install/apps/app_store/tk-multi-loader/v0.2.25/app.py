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
A loader application that lets you add new items to the scene.

"""

import tank
import sys
import os

class MultiLoader(tank.platform.Application):
    
    def init_app(self):
        """
        Called as the application is being initialized
        """
        tk_multi_loader = self.import_module("tk_multi_loader")
        cb = lambda : tk_multi_loader.show_dialog(self)
        menu_caption = self.get_setting("menu_name")
        
        # add stuff to main menu
        self.engine.register_command(menu_caption, cb)

    def resolve_filter_template_fields(self, filters):
        """
        Resolves all templated fields in list of filters to their respective shotgun entity
        descriptors.  Used by publish and entity browser widgets when getting data.
        
        :param filters: list of filters to resolve
        :returns: list of resolved filters    
        """
        resolved_filters = []
        for filter in filters:
            resolved_filter = []
            for field in filter:
                if field == "{context.entity}":
                    field = self.context.entity
                elif field == "{context.project}":
                    field = self.context.project
                elif field == "{context.step}":
                    field = self.context.step
                elif field == "{context.task}":
                    field = self.context.task
                elif field == "{context.user}":
                    field = self.context.user                    
                resolved_filter.append(field)
            resolved_filters.append(resolved_filter)
            
        return resolved_filters
