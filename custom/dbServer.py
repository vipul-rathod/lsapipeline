'''
Created on Mar 21, 2012

@author: mat.facer
'''
import os, sys
print 'Importing now...'
if 'T:/software/DoubleBarrel/' not in sys.path:
    sys.path.append('T:/software/DoubleBarrel/')

if 'T:/software/DoubleBarrel/doublebarrel' not in sys.path:
    sys.path.append('T:/software/DoubleBarrel/doublebarrel')

if 'T:/software/python-api/' not in sys.path:
    sys.path.append('T:/software/python-api/')

import doubleBarrel as db
#reload(db)

class InitServer(object):
    def __init__(self, pathTo = 'T:/software/lsapipeline/custom'):
        self.dirPath = pathTo
        print 'Config folder: %s' % self.dirPath
        self.sgFile  = os.path.join(self.dirPath, 'shotgunScript.sg')
        print 'Config file: %s' % self.sgFile
        print 'Starting server now...'
        self.sg     = db.server.DoubleBarrelServer(self.sgFile).run()
    
    def isRunning(self):
        return self.sg.isRunning()
if __name__ == '__main__':   
    InitServer()