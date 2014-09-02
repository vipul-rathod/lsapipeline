"""
Copyright (c) 2013 James Dunlop
----------------------------------------------------
Creates maya assets for BBBay into maya based on the assets lists for a shot in the shotgun db
"""
import os, getpass, sys
import shutil
from functools import partial

## TANK STUFF
import sgtk
import tank.templatekey
from tank.platform.qt import QtCore, QtGui
from tank.platform import Application
from tank import TankError

## MAYA STUFF
import maya.cmds as cmds
import maya.mel as mel


def versionPublishFile(task, publish_path, progress_cb):