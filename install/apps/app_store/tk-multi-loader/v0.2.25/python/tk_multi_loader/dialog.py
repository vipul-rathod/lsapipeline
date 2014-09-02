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
from .ui.dialog import Ui_Dialog

settings = tank.platform.import_framework("tk-framework-shotgunutils", "settings")

class AppDialog(QtGui.QWidget):

    
    def __init__(self, app):
        QtGui.QWidget.__init__(self)
        
        # set up the UI
        self.ui = Ui_Dialog() 
        self.ui.setupUi(self)

        self._app = app
        
        self._settings = settings.UserSettings(app)
        
        # set up the browsers
        self.ui.left_browser.set_app(self._app)
        self.ui.middle_browser.set_app(self._app)
        self.ui.right_browser.set_app(self._app)

        # set the browser labels        
        entity_cfg = self._app.get_setting("sg_entity_types", {})
        # example: {"Shot": [["desc", "startswith", "foo"]] }        
        types_to_load = entity_cfg.keys()
        
        # now resolve the entity types into display names
        types_nice_names = [ tank.util.get_entity_type_display_name(self._app.tank, x) for x in types_to_load ]
        
        # generate menu heading
        plural_types = [ "%ss" % x for x in types_nice_names] # no fanciness (sheep, box, nucleus etc)
        if len(plural_types) == 1:
            # "Shots"
            types_str = plural_types[0]
        else:
            # "Shots, Assets & Sequences"
            types_str = ", ".join(plural_types[:-1])
            types_str += " & %s" % plural_types[-1]
            
        self.ui.left_browser.set_label(types_str)

        self.ui.middle_browser.set_label("Publishes")
        
        if self._app.get_setting("dependency_mode"):
            self.ui.right_browser.set_label("Contents")
        else:
            self.ui.right_browser.set_label("Versions")
        
        # set the caption on the load button
        self.ui.load_selected.setText( self._app.get_setting("button_name") )
        
        self.toggle_load_button_enabled()
        self.ui.load_selected.clicked.connect( self.load_item )
        self.ui.close.clicked.connect( self.close )
        
        self.ui.left_browser.selection_changed.connect( self.setup_publish_list )
        self.ui.middle_browser.selection_changed.connect( self.setup_version_list )
        self.ui.right_browser.action_requested.connect( self.load_item )
        
        self.ui.left_browser.selection_changed.connect( self.toggle_load_button_enabled )
        self.ui.middle_browser.selection_changed.connect( self.toggle_load_button_enabled )
        self.ui.right_browser.selection_changed.connect( self.toggle_load_button_enabled )
                
        # get user preference
        current_entity_type = self._settings.retrieve("current_entity_type", None, self._settings.SCOPE_INSTANCE) 
        current_entity_id = self._settings.retrieve("current_entity_id", None, self._settings.SCOPE_INSTANCE)
        only_show_current = self._settings.retrieve("only_show_current", False, self._settings.SCOPE_INSTANCE)
        
        if current_entity_type and current_entity_id:
            # we have a stored setting 
            prev_selection = {"type": current_entity_type, "id": current_entity_id}
        else:
            prev_selection = {}
                    
        # and push settings down to the UI
        self.ui.show_current_checkbox.setChecked(only_show_current)
        self.ui.left_browser.set_show_only_current(only_show_current)
                
        # configure the "Show only current" checkbox
        if self._app.context.entity is None:
            # only show checkbox if there is a entity present in the context
            self.ui.show_current_checkbox.setVisible(False)
        elif self._app.context.entity.get("type") not in types_to_load:
            # context entity is not in the list of entity types to display
            self.ui.show_current_checkbox.setVisible(False)
        else:
            ctx_type = self._app.context.entity.get("type")
            self.ui.show_current_checkbox.stateChanged.connect(self.toggle_show_only_context)
            self.ui.show_current_checkbox.setText("Show only current %s" % ctx_type)
        
        self.setup_entity_list(prev_selection)
        
    ########################################################################################
    # make sure we trap when the dialog is closed so that we can shut down 
    # our threads. Nuke does not do proper cleanup on exit.
    
    def closeEvent(self, event):
        self.ui.left_browser.destroy()
        self.ui.middle_browser.destroy()
        self.ui.right_browser.destroy()
        # okay to close!
        event.accept()
        
    ########################################################################################
    # basic business logic        
        
    def toggle_load_button_enabled(self):
        """
        Control the enabled state of the load button
        """
        curr_selection = self.ui.right_browser.get_selected_item()
        if curr_selection is None:
            self.ui.load_selected.setEnabled(False)
        else:
            self.ui.load_selected.setEnabled(True)

    def toggle_show_only_context(self):

        only_show_current = self.ui.show_current_checkbox.isChecked()
        self.ui.left_browser.set_show_only_current(only_show_current)
        
        # remember selection in user prefs        
        self._settings.store("only_show_current", 
                             only_show_current, 
                             self._settings.SCOPE_INSTANCE)

        self.ui.left_browser.clear()
        self.ui.middle_browser.clear()
        self.ui.right_browser.clear()
        d = { "prev_selection": self._app.context.entity}
        self.ui.left_browser.load(d)
        
        
    def setup_entity_list(self, prev_selection): 
        self.ui.left_browser.clear()
        self.ui.middle_browser.clear()
        self.ui.right_browser.clear()
        d = { "prev_selection": prev_selection}
        self.ui.left_browser.load(d)
        
    def setup_publish_list(self):
        
        self.ui.middle_browser.clear()
        self.ui.right_browser.clear()
        
        curr_selection = self.ui.left_browser.get_selected_item()
        if curr_selection is None:
            return
        
        # save selection as user pref
        self._settings.store("current_entity_type", 
                             curr_selection.sg_data["type"], 
                             self._settings.SCOPE_INSTANCE)
        
        self._settings.store("current_entity_id", 
                             curr_selection.sg_data["id"], 
                             self._settings.SCOPE_INSTANCE)

        d = {}
        d["entity"] = curr_selection.sg_data
        self.ui.middle_browser.load(d)
        
    def setup_version_list(self):
        
        self.ui.right_browser.clear()
        
        entity_selection = self.ui.left_browser.get_selected_item()
        if entity_selection is None:
            return
        
        publish_selection = self.ui.middle_browser.get_selected_item()
        if publish_selection is None:
            return
        
        d = {}
        d["entity"] = entity_selection.sg_data
        d["publish"] = publish_selection.sg_data
        self.ui.right_browser.load(d)
        
    def load_item(self):
        """
        Load something into the scene
        """
        curr_selection = self.ui.right_browser.get_selected_item()
        if curr_selection is None:
            return
        
        local_path = curr_selection.sg_data.get("path").get("local_path")

        if local_path is None:
            QtGui.QMessageBox.critical(self, 
                                       "No path!", 
                                       "This publish does not have a path associated!")
            return
        
        # call out to our hook for loading.
        self._app.log_debug("Calling scene load hook for %s - %s" % (local_path, curr_selection.sg_data))
        self._app.execute_hook("hook_add_file_to_scene", 
                               engine_name=self._app.engine.name, 
                               file_path=local_path, 
                               shotgun_data=curr_selection.sg_data)

        if self._app.get_setting("single_select", True):
            # single select mode!
            self.close()
        
        
