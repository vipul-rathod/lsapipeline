# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import uuid
import gnomekeyring

from .base_store import KeyringStoreBase
from ..qt_abstraction import QtGui


# This module will only import if gnomekeyring is actually available
if not gnomekeyring.is_available():
    raise ImportError("gnomekeyring not available")


class GnomeKeyringStore(KeyringStoreBase):
    def get_password(self, keyring, login):
        item, _ = self._get_item(keyring, login)
        if item is None:
            return None
        return item.get_secret()

    def set_password(self, keyring, login, password):
        self._get_item(keyring, login, create=True)
        login_key = self._key_for_login(keyring, login)
        gnomekeyring.item_create_sync(
            "Login", gnomekeyring.ITEM_GENERIC_SECRET,
            login_key, {}, password, True)

    def delete_password(self, keyring, login):
        _, item_id = self._get_item(keyring, login)
        if item_id is not None:
            gnomekeyring.item_delete_sync("Login", item_id)

    def is_encrypted(self):
        return True

    def _get_keychain_password(self):
        password, ok = QtGui.QInputDialog.getText(
            None,
            "Keychain Password",
            "Enter a password to protect your login info:",
            QtGui.QLineEdit.Password,
        )

        if ok:
            return password
        return None

    def _key_for_login(self, keyring, login):
        return "%s@%s" % (login, keyring)

    def _get_item(self, keyring, login, create=False):
        login_key = self._key_for_login(keyring, login)

        try:
            item_keys = gnomekeyring.list_item_ids_sync("Login")
        except gnomekeyring.NoSuchKeyringError:
            if create:
                password = self._get_keychain_password()
                if password is not None:
                    gnomekeyring.create_sync("Login", password)
                    item_keys = []
                else:
                    return None, None
            else:
                return None, None

        for key in item_keys:
            item_info = gnomekeyring.item_get_info_sync("Login", key)
            if item_info.get_display_name() == login_key:
                return item_info, key

        if not create:
            return None, None

        item_key = gnomekeyring.item_create_sync(
            "Login",
            gnomekeyring.ITEM_GENERIC_SECRET,
            login_key,
            {},
            str(uuid.uuid4()),
            True
        )
        item = gnomekeyring.item_get_info_sync("Login", item_key)
        return item, item_key