# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import logging
from urlparse import urlparse

from . import stores
from . import LoginError
from .login_dialog import LoginDialog

from .qt_abstraction import QtCore


class Login(object):
    """
    Manage authenticating a login

    This is an abstract class that provides an abstraction over storing login information
    for a service.  For each service it stores a site specification (for example the url
    to log into), a login (for example the username to log in with) and a password.  The
    site and password are stored in a non-encrypted settings file, whereas the password is
    stored in an encrypted keyring, using operating specific implementations.

    To use the interface you should simply be able to request the login info from an
    implementation:
        login_manager = LoginImplementation.get_instance_for_namespace("My Application")
        login_info = login_manager.login()

    If the login info has already been collected, it will be returned.  If the saved values
    successfully authenticate, then the resulting login info will be returned.  Otherwise a
    dialog is shown to the user to collect site/login/password.

    To subclass, you must at a minimum implement _site_connect, who should validate the
    connection information.

    By default, the public settings are stored by Qt's QSettings, which will use the
    QApplication's applicationName and organizationName to figure out where to store the
    settings file.  This can be overridden by implementing the _get_settings method in
    a subclass.

    By default, the keyring used on the system will be named after the site (for example
    if logging into http://www.google.com, it would be "www.google.com.login") and the key
    would be the login being used.  These defaults can be overridden by implementing the
    _get_keyring_values method in a subclass.

    The default dialog that pops up can be overridden by changing the value of _dialog_class.
    The value of _dialog_kwargs will be passed to the dialog constructor.  See the docs from
    login_dialog.LoginDialog for what the valid arguments are for the default dialog.
    """

    # Logging
    _logger = logging.getLogger("tk-framework-login.login")

    # Instance cache
    _instances = {}  # cache of Login objects by namespace

    ##########################################################################################
    # class methods
    @classmethod
    def get_instance_for_namespace(cls, namespace):
        """
        Returns a Login instance for the given namespace.  If the instance already
        exists it is returned.  This acts as a factory to make it easy to reuse instances
        of a login manager.

        :param namespace: A string that acts as a lookup for the login manager.

        :returns: An instance of a login manager
        """
        # return the already created object if it exists
        if namespace in cls._instances:
            return cls._instances[namespace]

        # otherwise create it, cache it, and return it
        instance = cls()
        cls._instances[namespace] = instance
        return instance

    ##########################################################################################
    # public methods
    def __init__(self):
        """ Initialize a login manager """
        # control over the dialog that gets launched
        self._dialog_class = LoginDialog
        self._dialog_kwargs = {}

        # keyring implementation to use
        self._store = stores.get_keyring_store()()

        # cache of authenticated values
        self._login_info = None

    def login(self, site=None, dialog_message=None, force_dialog=False):
        """
        Return the login info for the current authenticated login.

        This will check saved values to see if there is a valid login
        cached. If no valid cached login information is found, a login
        dialog is displayed.

        :param site: The site to get the login for (None implies the default site)
        :param dialog_message: A message to display in the login dialog
        :param force_dialog: If True, pop up the dialog even if some valid credentials are retrieved

        :returns: None on failure and an implementation specific representation on success
        """
        if site is not None:
            raise NotImplementedError("support for multiple sites is not yet implemented")

        if not force_dialog:
            # first check in memory cache
            if self._login_info is not None:
                return self._login_info

            # next see if the saved values return a valid user
            result = self._check_saved_values()
            if result:
                return self._login_info

        # forcing dialog or cache/saved values did not authenticate
        result = self._run_dialog(dialog_message)
        if result:
            return self._login_info

        # failed
        return None

    def logout(self, site=None):
        """
        Log out of the current connection.

        This will clear any cached values and the stored password

        :param site: The site to log out of (None implies the default site)
        """
        if site is not None:
            raise NotImplementedError("support for multiple sites is not yet implemented")

        self._login_info = None
        self._clear_password()

    ##########################################################################################
    # pure virtual methods
    def _site_connect(self, site, login, password):
        """
        Authenticate the given values against the given site.  The return value will be
        cached and returned by login.

        Needs to be implemented in classes deriving from this one.

        :param site: The site to login to
        :param login: The login to use
        :param password: The password to use

        :returns: An object representing the logged in information

        :raises: LoginError on failure.
        """
        raise NotImplementedError

    ##########################################################################################
    # protected methods

    # read values ############################################################################
    def _get_saved_values(self):
        """ Return a tuple of all the stored values """
        # load up the values stored
        (site, login) = self._get_public_values()

        # load up the values stored securely in the os specific keyring
        if login:
            (keyring, keyring_login) = self._get_keyring_values(site, login)
            try:
                password = self._store.get_password(keyring, keyring_login)
            except Exception:
                password = None
        else:
            password = None

        return (site, login, password)

    def _get_public_values(self):
        """ Return a tuple of the values that are stored unencrypted """
        settings = self._get_settings("loginInfo")
        site = settings.value("site", None)
        login = settings.value("login", None)
        return (site, login)

    # set values #############################################################################
    def _save_values(self, site, login, password):
        """ Save the given values, saving the password securely """

        # make sure the keyring supports encryption
        if not self._store.is_encrypted():
            raise LoginError("keyring does not support encryption")

        # save the public settings
        settings = self._get_settings("loginInfo")
        settings.setValue("site", site)
        settings.setValue("login", login)

        # save these settings securely in the os specific keyring
        (keyring, keyring_login) = self._get_keyring_values(site, login)
        self._store.set_password(keyring, keyring_login, password)

    # clear values ###########################################################################
    def _clear_password(self):
        """ clear password value """
        # remove settings stored in the os specific keyring
        settings = self._get_settings("loginInfo")
        site = settings.value("site", None)
        login = settings.value("login", None)

        (keyring, keyring_login) = self._get_keyring_values(site, login)
        try:
            self._store.delete_password(keyring, keyring_login)
        except Exception:
            # windows can sometimes fail to delete a password try to handle this gracefully
            # by overwriting the saved password with a blank one
            self._store.set_password(keyring, keyring_login, "")

    def _clear_saved_values(self):
        """ clear non password values """
        # remove settings stored via QSettings
        settings = self._get_settings("loginInfo")
        settings.remove("")

    # validate values ########################################################################
    def _check_saved_values(self):
        """ return whether the saved values authenticate or not """
        (site, login, password) = self._get_saved_values()
        try:
            return self._check_values(site, login, password)
        except LoginError:
            return False

    def _check_values(self, site, login, password):
        """
        Authenticate the given values

        Will always return True or raise a LoginError.
        """
        # If either login or password is not set
        # don't even try to login with the credentials
        if login is None or password is None:
            raise LoginError("Empty credentials")

        # try to connect to the site
        try:
            results = self._site_connect(site, login, password)
        except Exception, e:
            raise LoginError("Could not connect to server", str(e))

        # cache results
        self._login_info = results

        return True

    # utilities ##############################################################################
    def _get_settings(self, group=None):
        """ Returns the QSettings object to store the values in """
        settings = QtCore.QSettings()

        if group is not None:
            settings.beginGroup(group)
        return settings

    def _run_dialog(self, dialog_message):
        """ run the login dialog """
        dialog = self._dialog_class(self, **self._dialog_kwargs)
        if dialog_message is not None:
            dialog.set_message(dialog_message)
        dialog.raise_()
        dialog.activateWindow()
        result = dialog.exec_()
        if result == dialog.Accepted:
            return True

        # dialog was canceled
        return False

    def _get_keyring_values(self, site, login):
        """
        Returns the values needed to locate a key in a keyring.  The default implementation
        returns the host portion of the site url and the login itself.

        :param site: Site to get the keyring/login for
        :param login: Login to get the keyring/login for

        :returns: A tuple (keyring, login) where the keyring is the keyring
                  to use and the login is the login for that keyring to use.
        """
        parse = urlparse(site)
        return ("%s.login" % parse.netloc, login)
