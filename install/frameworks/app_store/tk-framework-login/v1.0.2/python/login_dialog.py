# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


from .qt_abstraction import QtGui
from .qt_abstraction import QtCore

from . import LoginError

from .ui import resources_rc
from .ui import login as login_ui


class LoginDialog(QtGui.QDialog):
    """
    Default dialog for getting login information.

    This dialog is connected with an instance of a Login subclass and collects
    the information needed to authenticate a login.
    """
    def __init__(self, login, parent=None, **kwargs):
        """
        Constructs a dialog.

        :param login: An instance of a Login subclass.  This will be used to
            authenticate the information collected.

        :param parent: The Qt parent for the dialog (defaults to None)

        :param kwargs: The following keyword arguments are recognized:
            default_site - The string to populate the site field with unless already set (defaults to "")
            default_login - The string to populate the login field with unless already set (defaults to "")
            show_site - Whether or not to show the site widgets (defaults to True)
            stay_on_top - Whether the dialog should stay on top (defaults to True)
            pixmap - QPixmap to show in the dialog (defaults to the Shotgun logo)
            title - The string to set the window title to (defaults to "Shotgun Login")
        """
        QtGui.QDialog.__init__(self, parent)

        # initialize variables
        self._login = login
        self._default_site = kwargs.get("default_site") or ""
        self._default_login = kwargs.get("default_login") or ""

        # set the dialog to always stay on top
        if kwargs.get("stay_on_top", True):
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # setup the gui
        self.ui = login_ui.Ui_LoginDialog()
        self.ui.setupUi(self)

        # process kwarg overrides
        if not kwargs.get("show_site", True):
            self.ui.site.hide()
        if "title" in kwargs:
            self.setWindowTitle(kwargs["title"])

        # set the logo
        pixmap = kwargs.get("pixmap")
        if not pixmap:
            pixmap = QtGui.QPixmap(":/tk-framework-login/shotgun_with_text_logo.png")
        self.ui.logo.setPixmap(pixmap)

        # load up the values for the text fields
        self.load_settings()

        # default focus
        if self.ui.site.text():
            if self.ui.login.text():
                self.ui.password.setFocus()
            else:
                self.ui.login.setFocus()
        else:
            self.ui.site.setFocus()

        # hook up signals
        self.connect(self.ui.sign_in, QtCore.SIGNAL("clicked()"), self.ok_pressed)
        self.connect(self.ui.cancel, QtCore.SIGNAL("clicked()"), self.cancel_pressed)

    def set_message(self, message):
        """ Set the message in the dialog """
        if not message:
            self.ui.message.hide()
        else:
            self.ui.message.setText(message)
            self.ui.message.show()

    def cancel_pressed(self):
        self.close()

    def ok_pressed(self):
        """
        validate the values, accepting if login is successful and display an error message if not.
        """
        # pull values from the gui
        site = self.ui.site.text()
        login = self.ui.login.text()
        password = self.ui.password.text()

        # if not protocol specified assume https
        if len(site.split("://")) == 1:
            site = "https://%s" % site
            self.ui.site.setText(site)
        try:
            # set the wait cursor
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            QtGui.QApplication.processEvents()

            # try and authenticate
            self._login._check_values(site, login, password)
        except LoginError, e:
            # authentication did not succeed
            self.ui.message.setText("<font style='color: rgb(252, 98, 70);'>%s:&nbsp;&nbsp;%s</font>" % (e[0], e[1]))
            self.ui.message.show()
            return
        finally:
            # restore the cursor
            QtGui.QApplication.restoreOverrideCursor()
            QtGui.QApplication.processEvents()

        # all good, save the settings if requested and return accepted
        try:
            self.save_settings()
        except LoginError:
            # error saving the settings
            self.ui.message.setText("Could not store login information safely.")
            return

        # dialog is done
        self.accept()

    def load_settings(self):
        """ Load the saved values for the dialog """
        (site, login, password) = self._login._get_saved_values()

        # populate the ui
        self.ui.site.setText(site or self._default_site)
        self.ui.login.setText(login or self._default_login)
        self.ui.password.setText(password or "")

    def save_settings(self):
        """ Save the values from the dialog """
        # pull values from the gui
        site = self.ui.site.text()
        login = self.ui.login.text()
        password = self.ui.password.text()

        self._login._save_values(site, login, password)