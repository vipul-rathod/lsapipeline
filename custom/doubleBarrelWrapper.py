import os, sys
## Doublebarrel testing
if 'T:/software/DoubleBarrel/' not in sys.path:
    sys.path.append('T:/software/DoubleBarrel/')
if 'T:/software/python-api/' not in sys.path:
    sys.path.append('T:/software/python-api/')
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')

from ConfigParser import ConfigParser
from doubleBarrel import DoubleBarrel, DoubleBarrelServer
from debug import debug

def _getShotgunObject(api = None, app = None):
    if api:
        config = ConfigParser()
        debug(app = app, method = '_getShotgunObject', message= 'config done..', verbose = False)
        
        dirPath = os.path.dirname('T:/software/lsapipeline/custom/')
        debug(app = app, method = '_getShotgunObject', message= 'dirPath: %s' % dirPath, verbose = False)
        
        sgFile = os.path.join(dirPath, 'shotgunScript.sg')
        debug(app = app, method = '_getShotgunObject', message= 'sgFile: %s' % sgFile, verbose = False)
        
        config.read(sgFile)
        debug(app = app, method = '_getShotgunObject', message= 'config read successfully', verbose = False)
        
        shotgunData = dict(config.items('ShotgunData'))
        debug(app = app, method = '_getShotgunObject', message= 'shotgunData: %s' % shotgunData, verbose = False)
        
        serverPath = shotgunData.get('base_url')
        debug(app = app, method = '_getShotgunObject', message= 'serverPath: %s' % serverPath, verbose = False)
        
        scriptName = shotgunData.get('script_name')
        debug(app = app, method = '_getShotgunObject', message= 'scriptName: %s' % scriptName, verbose = False)
        
        scriptKey = shotgunData.get('api_key')
        debug(app = app, method = '_getShotgunObject', message= 'scriptKey: %s' % scriptKey, verbose = False)
        return api(serverPath, scriptName, scriptKey)
    else:
        print 'SHOTGUN API FAILED'
        return False