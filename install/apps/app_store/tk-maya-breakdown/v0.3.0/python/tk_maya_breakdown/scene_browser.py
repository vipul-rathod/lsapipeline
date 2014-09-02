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
import datetime
import threading 
import maya
import tank

from PySide import QtCore, QtGui

browser_widget = tank.platform.import_framework("tk-framework-widget", "browser_widget")

from .breakdown_list_item import BreakdownListItem

class SceneBrowserWidget(browser_widget.BrowserWidget):

    
    def __init__(self, parent=None):
        browser_widget.BrowserWidget.__init__(self, parent)
        
        # cache the resolved paths metadata - it doesn't change!
        self._resolved_paths = {}

    def get_data(self, data):
        
        items = []

        # because maya is brittle when it comes to threads
        # (even reading dag data WTF) have to use their 
        # special hack. See
        # http://download.autodesk.com/global/docs/maya2013/en_us/files/Python_Python_and_threading.htm
        scene_objects = maya.utils.executeInMainThreadWithResult(self._app.execute_hook, "hook_scan_scene")
        # returns a list of dictionaries, each dict being like this:
        # {"node": node_name, "type": "reference", "path": maya_path}
        
        # scan scene and add all tank nodes to list
        for scene_object in scene_objects:
            
            node_name = scene_object.get("node")
            node_type = scene_object.get("type")
            file_name = scene_object.get("path").replace("/", os.path.sep)
            
            # see if this read node matches any path in the templates setup
            matching_template = self._app.tank.template_from_path(file_name)            
            
            if matching_template:
                
                # see if we have a version number
                fields = matching_template.get_fields(file_name)
                if "version" in fields:
                
                    # now the fields are the raw breakdown of the path in the read node.
                    # could be bla.left.0002.exr, bla.%V.####.exr etc
                    # now normalize the fields SEQ and eye
                    fields["SEQ"] = "FORMAT: %d"
                    fields["eye"] = "%V"
                    normalized_path = matching_template.apply_fields(fields)
                    
                    item = {}
                    item["path"] = normalized_path
                    item["node_name"] = node_name
                    item["node_type"] = node_type
                    item["template"] = matching_template
                    item["fields"] = fields
                    item["sg_data"] = None                
                                                    
                    
                    # store the normalized fields in dict
                    items.append(item)
                    
        # now now do a second pass on all the files that are valid to see if they are published
        # note that we store (by convention) all things on a normalized form in SG.
        valid_paths = [ x.get("path") for x in items ]
        
        # check if we have the path in the cache
        paths_to_fetch = []
        for p in valid_paths:
            if p not in self._resolved_paths:
                paths_to_fetch.append(p)
            else:
                # use cache data!
                for item in items:
                    if item.get("path") == p:
                        item["sg_data"] = self._resolved_paths[p]
        
        fields = ["entity", 
                  "entity.Asset.sg_asset_type", # grab asset type if it is an asset
                  "code",
                  "image",
                  "name", 
                  "task", 
                  "version_number",
                  ]

        if tank.util.get_published_file_entity_type(self._app.tank) == "PublishedFile":
            fields.append("published_file_type")
        else:# == "TankPublishedFile"
            fields.append("tank_type")            
        
        sg_data = tank.util.find_publish(self._app.tank, paths_to_fetch, fields=fields)

        # process and cache shotgun items
        for (path, sg_chunk) in sg_data.items():
            # cache item
            self._resolved_paths[path] = sg_chunk
            
            # change type from valid -> publish
            for item in items:
                if item.get("path") == path:
                    item["sg_data"] = sg_chunk
            
        return {"items": items, "show_red": data["show_red"], "show_green": data["show_green"] } 
    
    def _make_row(self, first, second):
        return "<tr><td><b>%s</b>&nbsp;&nbsp;&nbsp;</td><td>%s</td></tr>" % (first, second)
    

    def process_result(self, result):

        if len(result.get("items")) == 0:
            self.set_message("No versioned data in your scene!")
            return

        ################################################################################
        # PASS 1 - grouping
        # group these items into various buckets first based on type, and asset type
        groups = {}

        for d in result["items"]:

            if d.get("sg_data"):

                # publish in shotgun!
                sg_data = d["sg_data"]
                
                entity = sg_data.get("entity")
                if entity is None:
                    entity_type = "Unknown Type"
                else:
                    entity_type = entity["type"]
                
                asset_type = sg_data["entity.Asset.sg_asset_type"]

                if asset_type:
                    group = "%ss" % asset_type # eg. Characters
                else:
                    group = "%ss" % entity_type # eg. Shots

                # it is an asset, so group by asset type
                if group not in groups:
                    groups[group] = []
                groups[group].append(d)                
                
            else:
                # everything not in shotgun goes into the other bucket
                OTHER_ITEMS = "Unpublished Items"
                if OTHER_ITEMS not in groups:
                    groups[OTHER_ITEMS] = []
                groups[OTHER_ITEMS].append(d)
                

        ################################################################################
        # PASS 2 - display the content of all groups

        if tank.util.get_published_file_entity_type(self._app.tank) == "PublishedFile":
            published_file_type_field = "published_file_type"
        else:# == "TankPublishedFile"
            published_file_type_field = "tank_type"            

        # now iterate through the groups
        for group in sorted(groups.keys()):
            
            i = self.add_item(browser_widget.ListHeader)
            i.set_title(group)
            for d in groups[group]:

                # item has a publish in sg
                i = self.add_item(BreakdownListItem)
                
                # provide a limited amount of data for receivers via the 
                # data dictionary on
                # the item object
                i.data = {"node_name": d["node_name"], 
                          "node_type": d["node_type"],
                          "template": d["template"],
                          "fields": d["fields"] }
                
                # populate the description
                details = []
                
                
                if d.get("sg_data"):

                    sg_data = d["sg_data"]
                    
                    details.append( self._make_row("Item", "%s, Version %d" % (sg_data["name"], sg_data["version_number"]) ) )
                         
                    # see if this publish is associated with an entity
                    linked_entity = sg_data.get("entity")
                    if linked_entity:
                        details.append( self._make_row(linked_entity["type"], linked_entity["name"]) )                    
                    
                    # does it have a tank type ?
                    if sg_data.get(published_file_type_field):
                        details.append( self._make_row("Type", sg_data.get(published_file_type_field).get("name")))

                    details.append( self._make_row("Maya Node", d["node_name"]))


                else:
                    
                    details.append(self._make_row("Version", d["fields"]["version"] ))
                    
                    # display some key fields in the widget
                    # todo: make this more generic?
                    relevant_fields = ["Shot", "Asset", "Step", "Sequence", "name"]
                    
                    for (k,v) in d["fields"].items():
                        # only show relevant fields - a bit of a hack
                        if k in relevant_fields:
                            details.append( self._make_row(k,v) )
                
                    details.append( self._make_row("Maya Node", d["node_name"]))
                
                inner = "".join(details)
                
                i.set_details("<table>%s</table>" % inner)
                
                # finally, ask the node to calculate its red-green status
                # this will happen asynchronously.
                i.calculate_status(d["template"], 
                                   d["fields"], 
                                   result["show_red"],
                                   result["show_green"],
                                   d.get("sg_data"))
