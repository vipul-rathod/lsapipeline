# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import abc


class KeyringStoreBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_password(self, keyring, login):
        raise NotImplementedError("pure abstract method called.")

    @abc.abstractmethod
    def set_password(self, keyring, login, password):
        raise NotImplementedError("pure abstract method called.")

    @abc.abstractmethod
    def delete_password(self, keyring, login):
        raise NotImplementedError("pure abstract method called.")

    @abc.abstractmethod
    def is_encrypted(self):
        raise NotImplementedError("pure abstract method called.")
