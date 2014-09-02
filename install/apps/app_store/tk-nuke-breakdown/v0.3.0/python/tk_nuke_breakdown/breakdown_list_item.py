# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import shutil
import urlparse
import tank

from PySide import QtCore, QtGui

browser_widget = tank.platform.import_framework("tk-framework-widget", "browser_widget")
shotgun_data = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")

from .ui.item import Ui_Item


class SmallIconListItem(browser_widget.list_base.ListBase):
    # copied across ListItem class and changed the UI.

    def __init__(self, app, worker, parent=None):
        browser_widget.list_base.ListBase.__init__(self, app, worker, parent)

        # set up the UI
        self.ui = Ui_Item()
        self.ui.setupUi(self)
        self._selected = False
        self._worker = worker
        self._worker_uid = None

        # spinner
        self._spin_icons = []
        self._spin_icons.append(QtGui.QPixmap(":/res/thumb_loading_1.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/thumb_loading_2.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/thumb_loading_3.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/thumb_loading_4.png"))

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect( self._update_spinner )
        self._current_spinner_index = 0

    def supports_selection(self):
        return True

    def set_selected(self, status):
        self._selected = status
        if self._selected:
            self.ui.background.setStyleSheet("background-color: #707070; border: none")
        else:
            self.ui.background.setStyleSheet("")

    def is_selected(self):
        return self._selected

    def set_details(self, txt):
        self.ui.details.setText(txt)

    def get_details(self):
        return self.ui.details.text()

    def set_thumbnail(self, url):
        if url.startswith("http"):
            # start spinning
            self._timer.start(100)

            self._worker_uid = self._worker.queue_work(self._download_thumbnail, {"url": url})
            self._worker.work_completed.connect(self._on_worker_task_complete)
            self._worker.work_failure.connect( self._on_worker_failure)
        else:
            # assume url is a path on disk or resource
            self.ui.thumbnail.setPixmap(QtGui.QPixmap(url))

    ############################################################################################
    # internal stuff

    def _update_spinner(self):
        """
        Animate spinner icon
        """
        self.ui.thumbnail.setPixmap(self._spin_icons[self._current_spinner_index])
        self._current_spinner_index += 1
        if self._current_spinner_index == 4:
            self._current_spinner_index = 0

    def _download_thumbnail(self, data):
        url = data["url"]        
        bundle = tank.platform.current_bundle()
        path_to_cached_thumb = shotgun_data.ShotgunDataRetriever.download_thumbnail(url, bundle)
        return {"thumb_path": path_to_cached_thumb }

    def _on_worker_task_complete(self, uid, data):
        if uid != self._worker_uid:
            return

        # stop spin
        self._timer.stop()

        # set thumbnail!
        try:
            path = data.get("thumb_path")
            self.ui.thumbnail.setPixmap(QtGui.QPixmap(path))
        except:
            self.ui.thumbnail.setPixmap(QtGui.QPixmap(":/res/thumb_empty.png"))

    def _on_worker_failure(self, uid, msg):

        if self._worker_uid != uid:
            # not our job. ignore
            return

        # stop spin
        self._timer.stop()

        # show error message
        self._app.log_warning("Worker error: %s" % msg)


class BreakdownListItem(SmallIconListItem):

    def __init__(self, app, worker, parent=None):
        SmallIconListItem.__init__(self, app, worker, parent)
        self._green_pixmap = QtGui.QPixmap(":/res/green_bullet.png")
        self._red_pixmap = QtGui.QPixmap(":/res/red_bullet.png")
        self._latest_version = None
        self._is_latest = None

    def get_latest_version_number(self):
        # returns none if not yet determined
        return self._latest_version

    def is_latest_version(self):
        # returns none if not yet determined
        return self._is_latest

    def is_out_of_date(self):
        # returns none if not yet determined
        if self._is_latest is None:
            return None
        else:
            return self._is_latest == False

    def calculate_status(self, template, fields, show_red, show_green, entity_dict=None):
        """
        Figure out if this is a red or a green one. Also get thumb if possible
        """

        # we can only process stuff with a version
        if "version" not in fields:
            raise Exception("Fields must have a version!")

        # start spinner
        self._timer.start(100)

        # store data
        self._template = template
        self._fields = fields
        self._show_red = show_red
        self._show_green = show_green
        self._sg_data = entity_dict

        # kick off the worker!
        self._worker_uid = self._worker.queue_work(self._calculate_status, {})
        self._worker.work_completed.connect(self._on_worker_task_complete)
        self._worker.work_failure.connect( self._on_worker_failure)

    def _calculate_status(self, data):
        """
        The computational payload that downloads thumbnails and figures out the
        status for this item. This is run in a worker thread.
        """
        # set up the payload
        output = {}

        ########################################################################
        # stage 1: calculate the thumbnail

        # see if we can download a thumbnail
        # thumbnail can be in any of the fields
        # entity.Asset.image
        # entity.Shot.image
        # entity.Scene.image
        # entity.Sequence.image
        if self._sg_data:

            thumb_url = self._sg_data.get("image")

            if thumb_url is not None:
                # input is a dict with a url key
                # returns a dict with a  thumb_path key
                ret = self._download_thumbnail({"url": thumb_url})
                if ret:
                    output["thumbnail"] = ret.get("thumb_path")
                else:
                    output["thumbnail"] = ":/res/no_thumb.png"
            else:
                output["thumbnail"] = ":/res/no_thumb.png"

        ########################################################################
        # stage 2: calculate visibility
        # check if this is the latest item

        # note - have to do some tricks here to get sequences and stereo working
        # need to fix this in Tank platform

        # get all eyes, all frames and all versions
        # potentially a HUGE glob, so may be really SUPER SLOW...
        # todo: better support for sequence iterations
        all_versions = self._app.tank.paths_from_template(self._template,
                                                          self._fields,
                                                          skip_keys=["version", "SEQ", "eye"])

        # now look for the highest version number...
        latest_version = 0
        for ver in all_versions:
            fields = self._template.get_fields(ver)
            if fields["version"] > latest_version:
                latest_version = fields["version"]

        current_version = self._fields["version"]
        output["up_to_date"] = (latest_version == current_version)

        self._latest_version = latest_version
        self._is_latest = output["up_to_date"]

        return output

    def _on_worker_failure(self, uid, msg):

        if self._worker_uid != uid:
            # not our job. ignore
            return

        # finally, turn off progress indication and turn on display
        self._timer.stop()

        # show error message
        self._app.log_warning("Worker error: %s" % msg)

    def _on_worker_task_complete(self, uid, data):
        """
        Called when the computation is complete and we should update widget
        with the result
        """
        if uid != self._worker_uid:
            return

        # stop spin
        self._timer.stop()

        # set thumbnail
        if data.get("thumbnail"):
            self.ui.thumbnail.setPixmap(QtGui.QPixmap(data.get("thumbnail")))

        # set light - red or green
        if data["up_to_date"]:
            icon = self._green_pixmap
        else:
            icon = self._red_pixmap
        self.ui.light.setPixmap(icon)

        # figure out if this item should be hidden
        if data["up_to_date"] == True and self._show_green == False:
            self.setVisible(False)
        if data["up_to_date"] == False and self._show_red == False:
            self.setVisible(False)
