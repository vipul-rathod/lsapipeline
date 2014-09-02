"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

Open selection in Shotgun
"""

from PySide import QtGui
from PySide import QtCore

import hiero.core

from tank.platform import Application
from tank import TankError

class HieroOpenInShotgun(Application):
    """
    This app adds a menu item that allows a user to jump from an object 
    in Hiero to the associated object in Shotgun.
    """
    
    def init_app(self):
        """
        Initialization
        """
        self.engine.register_command("Open in Shotgun", self.callback)

    def callback(self):
        """
        Command implementation
        """
        try:
            self._open_shot()
        except TankError, e:
            # report all tank errors with a UI popup.
            QtGui.QMessageBox.critical(None, "Shot Lookup Error!", str(e))
        except Exception, e:
            # log full call stack to console
            self.log_exception("General error reported.")
            # pop up message
            msg = "A general error was reported: %s" % e
            QtGui.QMessageBox.critical(None, "Shot Lookup Error!", msg)
        
    def _open_shot(self):
        """
        Look up shot in shotgun from selection
        """
        # grab the current selection from the view that triggered the event
        selection = self.engine.get_menu_selection()
        
        if len(selection) != 1:
            raise TankError("Please select a single Shot!")
        
        if not isinstance(selection[0] , hiero.core.TrackItem):
            raise TankError("Please select a Shot in the Timeline or Spreadsheet!")
            
        # this is always okay according to the hiero API docs
        sequence = selection[0].parent().parent()
        
        shot_name = selection[0].name()
        sequence_name = sequence.name() 
        
        self.log_debug("Looking for a shot '%s' with a sequence '%s' in Shotgun..." % (shot_name, sequence_name))
        
        filters = []
        filters.append( ["sg_sequence.Sequence.code", "is", sequence_name] )
        filters.append( ["code", "is", shot_name] )
        
        sg_data = self.shotgun.find_one("Shot", filters)
        
        if sg_data is None:
            raise TankError("Could not find a Shot in Shotgun with name '%s' associated with a Sequence '%s'!" % (shot_name, sequence_name))
        
        # launch Shotgun Url using default browser
        url = "%s/detail/Shot/%s" % (self.shotgun.base_url, sg_data["id"])        
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        
