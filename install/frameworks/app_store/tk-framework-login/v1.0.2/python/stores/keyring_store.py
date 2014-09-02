# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from . import keyring as keyring_module
from .base_store import KeyringStoreBase


class KeyringKeyringStore(KeyringStoreBase):
    def get_password(self, keyring, login):
        return keyring_module.get_password(keyring, login)

    def set_password(self, keyring, login, password):
        return keyring_module.set_password(keyring, login, password)

    def delete_password(self, keyring, login):
        return keyring_module.delete_password(keyring, login)

    def is_encrypted(self):
        kr = keyring_module.get_keyring()
        return kr.encrypted()
