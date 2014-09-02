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

class VersionBrowserWidget(browser_widget.BrowserWidget):
    """
    Right Column
    """
    
    def __init__(self, parent=None):
        browser_widget.BrowserWidget.__init__(self, parent)        
        

    def get_data(self, data):

        # get details about the published file entity:
        published_file_entity_type = tank.util.get_published_file_entity_type(self._app.tank)
        if published_file_entity_type == "PublishedFile":
            published_file_type_field = "published_file_type"
            published_file_upstream_files_field = "upstream_published_files"
        else:# == "TankPublishedFile":
            published_file_type_field = "tank_type"
            published_file_upstream_files_field = "upstream_tank_published_files"
            
        current_entity = data["entity"]
        current_publish = data["publish"]
        publish_name = current_publish.get("name")
        publish_type = current_publish.get(published_file_type_field)
        
        fields = [ "description", 
                   "version_number", 
                   "created_by",
                   "image", 
                   "entity",
                   "created_at",
                   published_file_type_field,
                   "path",
                   "name"]

        order_by = [{"field_name": "created_at", "direction": "desc"}]

        if self._app.get_setting("dependency_mode"):
            # get all publishes that are children of this publish
            data = self._app.shotgun.find(published_file_entity_type, 
                                          [ [published_file_upstream_files_field, "is", current_publish ] ], 
                                          fields,
                                          order_by
                                          )
            
        else:
            # load publishes with the same name, entity and type 
            data = self._app.shotgun.find(published_file_entity_type, 
                                          [ ["project", "is", self._app.context.project],
                                            ["entity", "is", current_entity],
                                            [published_file_type_field, "is", publish_type],
                                            ["name", "is", publish_name] ], 
                                          fields,
                                          order_by
                                          )
        
            
        return {"data": data }
            
    def process_result(self, result):

        # select the first version we render (the latest version)
        selected = False

        for d in result.get("data"):
            
            i = self.add_item(browser_widget.ListItem)
            if not selected:
                self.select(i)
                selected = True
            
            desc = "No Comments"
            if d.get("description") is not None:
                 desc = d.get("description")
            
            if self._app.get_setting("dependency_mode"):
                
                # show name and version
                details = ("<b>%s v%s</b><br>"
                           "<small><i>%s, %s</i></small><br>"
                           "%s" % (d.get("name"), 
                                   d.get("version_number"),
                                   d.get("created_by", {}).get("name"),
                                   d.get("created_at"), 
                                   desc))
                i.set_details(details)
            
            else:
            
                # show just name
                details = []
                details.append("<b>Version %s</b>" % d.get("version_number") )
                details.append("<i><small>%s, %s</small></i>" % (d.get("created_by", {}).get("name"), 
                                                                 d.get("created_at")) )
                details.append(desc)
                
                i.set_details("<br>".join(details))

            i.sg_data = d
            if d.get("image"):
                i.set_thumbnail(d.get("image"))                

        
        