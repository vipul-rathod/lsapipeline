# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


def get_keyring_store():
    try:
        from .gnomekeyring_store import GnomeKeyringStore
        return GnomeKeyringStore
    except ImportError:
        pass

    try:
        from .keyring_store import KeyringKeyringStore
        return KeyringKeyringStore
    except ImportError:
        pass

    raise RuntimeError("No keyring store available")
