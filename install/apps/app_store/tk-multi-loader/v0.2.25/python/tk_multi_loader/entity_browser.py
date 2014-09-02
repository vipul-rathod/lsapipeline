# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
import os
import sys
import threading

from tank.platform.qt import QtCore, QtGui

browser_widget = tank.platform.import_framework("tk-framework-widget", "browser_widget")

class EntityBrowserWidget(browser_widget.BrowserWidget):

    
    def __init__(self, parent=None):
        browser_widget.BrowserWidget.__init__(self, parent)
        self.__show_only_current = False
        
        # cannot access self._app here so just initialize blank and populate in get_data
        self._types_to_load = []


    def get_data(self, data):
            
        previous_selection = data["prev_selection"]
            
        entity_cfg = self._app.get_setting("sg_entity_types", {})
        # example: {"Shot": [["desc", "startswith", "foo"]] }  
        self._types_to_load = entity_cfg.keys()
                    
        sg_data = []

        # load all entities
        for et in self._types_to_load:
            # only load the context entity type if show only current is checked
            if self.__show_only_current and (et != self._app.context.entity["type"]):
                continue

            item = {}
            item["type"] = et
            filters = []
            
            # add any custom filters
            entity_filters = entity_cfg[et]
            
            # resolve any template fields:
            entity_filters = self._app.resolve_filter_template_fields(entity_filters)
            
            # add resolved filters to list of filters    
            filters.extend(entity_filters)

            # and limit results to current is show only current is checked
            if self.__show_only_current:
                filters.append(["id", "is", self._app.context.entity["id"]])

            # automatically filter by project for all entities that
            # have a project field             
            if "project" in self._app.shotgun.schema_field_read(et): 
                filters.append(["project", "is", self._app.context.project])            
            
            item["data"] = self._app.shotgun.find(et, 
                                                  filters, 
                                                  ["code", "description", "image"],
                                                  [{"field_name": "code", "direction": "asc"}])
            
            sg_data.append(item)
            
        
        return {"previous_selection": previous_selection, "sg_data": sg_data}


    def process_result(self, result):

        previous_selection = result.get("previous_selection") 
        sg_data = result.get("sg_data")

        prev_selection_item = None

        for item in sg_data:
            
            if len(self._types_to_load) > 1:
                i = self.add_item(browser_widget.ListHeader)
                i.set_title("%ss" % tank.util.get_entity_type_display_name(self._app.tank, item.get("type")))
            
            for d in item["data"]:
                i = self.add_item(browser_widget.ListItem)
                
                description = d.get("description")
                if description is None:
                    description = "No Description"
                
                details = "<b>%s %s</b><br>%s" % (tank.util.get_entity_type_display_name(self._app.tank, d.get("type")), 
                                                  d.get("code"), description)
                
                i.set_details(details)
                i.sg_data = d
                if d.get("image"):
                    i.set_thumbnail(d.get("image"))

                # is this previous selection?
                if previous_selection:
                    if previous_selection["type"] == d["type"] and previous_selection["id"] == d["id"]:
                        prev_selection_item = i
        
        # once the list is completely built, select prev item if there is one.
        if prev_selection_item:
            self.select(prev_selection_item)
            
    def set_show_only_current(self, value):
        self.__show_only_current = value

