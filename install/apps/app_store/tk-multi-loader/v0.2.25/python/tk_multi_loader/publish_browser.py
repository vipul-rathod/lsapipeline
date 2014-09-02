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


class PublishBrowserWidget(browser_widget.BrowserWidget):
    """
    Middle pane
    """
    
    def __init__(self, parent=None):
        browser_widget.BrowserWidget.__init__(self, parent)        

    def get_data(self, data):
            
        sg_data = []
        current_entity = data["entity"]

        types_to_load = self._app.get_setting("tank_types", [])
        filters = self._app.get_setting("publish_filters", [])

        # resolve any template fields in the filters:
        filters = self._app.resolve_filter_template_fields(filters)

        # always limit to project and entity:
        filters.extend([["entity", "is", current_entity]])             
        
        order_by = [{"field_name": "name", "direction": "asc"},
                    {"field_name": "version_number", "direction": "desc"}]

        # get details about the published file entity:
        published_file_entity_type = tank.util.get_published_file_entity_type(self._app.tank)
        if published_file_entity_type == "PublishedFile":
            published_file_type_field = "published_file_type"
            published_file_type_entity_type = "PublishedFileType"
        else:# == "TankPublishedFile"
            published_file_type_field = "tank_type"
            published_file_type_entity_type = "TankType"
            
        fields = [ "description", 
                   "version_number", 
                   "created_by",
                   "image", 
                   "entity",
                   "created_at",
                   published_file_type_field,
                   "name"]

        if len(types_to_load) == 0:
            # get all publishes for this entity
            data = self._app.shotgun.find(published_file_entity_type, filters, fields, order_by)
                        
            # now group this into sections based on the tank type
            published_file_type_dict = {}
            for d in data:
                published_file_type_link = d.get(published_file_type_field)
                if published_file_type_link is None:
                    published_file_type = "No type associated"
                else:
                    published_file_type = published_file_type_link.get("name")
                published_file_type_dict.setdefault(published_file_type, list()).append(d)
             
            # and attach the raw data to the output
            for published_file_type in published_file_type_dict:
                item = {}
                item["type"] = published_file_type
                item["raw_data"] = published_file_type_dict[published_file_type]
                sg_data.append(item)
            
        else:
            # get list of specific published file types            
            for published_file_type in types_to_load:            
                item = {}
                item["type"] = published_file_type
                
                pf_type_filters = [["code", "is", published_file_type]]
                if published_file_type_entity_type == "TankType":
                    pf_type_filters.extend([["project", "is", self._app.context.project]])
                
                published_file_type_entity = self._app.shotgun.find_one(published_file_type_entity_type, pf_type_filters, ["code", "id"])
                
                if published_file_type_entity is None:
                    # unknown tank type!
                    item["raw_data"] = []
                else:
                    extended_filters = filters + [[published_file_type_field, "is", published_file_type_entity ]]
                    item["raw_data"] = self._app.shotgun.find(published_file_entity_type, extended_filters, fields, order_by)
                    
                sg_data.append(item)
            
        if self._app.get_setting("dependency_mode"):
            # in dependency mode, the right most column will show file contents.
            # in the middle column, show all versions
            for item in sg_data:
                
                # the data list to display matches the raw dump of all versions
                # we got from shtogun
                item["data"] = item["raw_data"]
        
        else:
            # this is std mode
            # post process the list - we just want one item per "publish group"
            for item in sg_data:
                    
                # now group these into chunks based on their name
                groups = {}
                for d in item["raw_data"]:
                    name = str(d["name"]) # to handle None
                    if name not in groups:
                        groups[name] = []
                    groups[name].append(d)  
                
                # now choose one item out of each group - pick the one
                # with the highest version number
    
                # now get list of items, pick one item per group, using max()
                item["data"] = [max(d, key=lambda x:x["version_number"]) for d in groups.values()]

        
        # pass on the list to the result processor 
        return {"sg_data": sg_data }


    def process_result(self, result):

        sg_data = result.get("sg_data")

        # first check if we have results at all
        results = 0
        for item in sg_data:
            results += len(item["data"])
        if results == 0:
            self.set_message("Sorry, no publishes found!")
            return

        for item in sg_data:
            i = self.add_item(browser_widget.ListHeader)
            i.set_title(item["type"])
            for d in item["data"]:
                i = self.add_item(browser_widget.ListItem)
                
                desc = "No Comments"
                if d.get("description") is not None:
                     desc = d.get("description")
                
                if self._app.get_setting("dependency_mode"):
                    
                    # snow name and version
                    details = ("<b>%s v%s</b><br>"
                               "<small><i>%s, %s</i></small><br>"
                               "%s" % (d.get("name"), 
                                       d.get("version_number"),
                                       d.get("created_by", {}).get("name"),
                                       d.get("created_at"), 
                                       desc))
                
                else:
                
                    # show just version
                    details = ("<b>%s</b><br>"
                               "<small><i>Latest publish %s</i></small><br>"
                               "Latest change: %s" % (d.get("name"), d.get("created_at"), desc))
                
                i.set_details(details)
                i.sg_data = d
                if d.get("image"):
                    i.set_thumbnail(d.get("image"))                

        
        
