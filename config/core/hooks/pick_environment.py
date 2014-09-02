# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook which chooses an environment file to use based on the current context.

"""
import sys
from tank import Hook
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')
from debug import debug

class PickEnvironment(Hook):

    def execute(self, context, **kwargs):
        """
        The default implementation assumes there are three environments, called shot, asset 
        and project, and switches to these based on entity type.
        """
        debug(None, method = 'PickEnvironment', message = 'context: %s' % context, verbose = False)
        debug(None, method = 'PickEnvironment', message = 'context.project: %s' % context.project, verbose = False)
        if context.project is None:
            debug(None, method = 'PickEnvironment', message = 'Our context is completely empty!', verbose = False)
            # our context is completely empty! 
            # don't know how to handle this case.
            return None
        
        debug(None, method = 'PickEnvironment', message = 'context.entity: %s' % context.entity, verbose = False)
        if context.entity is None:
            # we have a project but not an entity
            debug(None, method = 'PickEnvironment', message = 'We have a project but not an entity!!!', verbose = False)
            return "project"
        
        debug(None, method = 'PickEnvironment', message = 'context.entity["type"]: %s' % context.entity["type"], verbose = False)
        debug(None, method = 'PickEnvironment', message = 'context.step: %s' % context.step, verbose = False)
        if context.entity and context.step is None:
            # we have an entity but no step!
            if context.entity["type"] == "Shot":
                return "shot"
            if context.entity["type"] == "Asset":
                return "asset"            
            if context.entity["type"] == "CustomEntity03":
                return "audio"     
            if context.entity["type"] == "Sequence":
                return "sequence"
                     
        debug(None, method = 'PickEnvironment', message = 'context.entity["type"]: %s' % context.entity["type"], verbose = False)
        if context.entity and context.step:
            # we have a step and an entity
            if context.entity["type"] == "Shot":
                return "shot_step"
            if context.entity["type"] == "Asset":
                return "asset_step"
            if context.entity["type"] == "CustomEntity03":
                return "audio_step"     
        
        debug(None, method = 'PickEnvironment', message = 'Finished... returning none', verbose = False)
        return None
