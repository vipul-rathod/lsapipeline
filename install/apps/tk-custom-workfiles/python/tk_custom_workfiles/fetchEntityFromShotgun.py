import sys
import pickle

if 'T:\\software\\lsapipeline\\install\\core\\python\\' not in sys.path:
    sys.path.append('T:\\software\\lsapipeline\\install\\core\\python\\')
import sgtk

#    Changes to be done for new projects
#     self.tk = sgtk.sgtk_from_path('T:/software/lsapipeline') : change the path to new project
#     projectId = 113 : change the project ID with new project
#     databasePath = 'T:/software/lsapipeline/install/apps/tk-custom-workfiles/python/tk_custom_workfiles/database/' : change the database path

class fetchEntityFromShotgun(object):
    def __init__(self):
        self.tk = sgtk.sgtk_from_path('T:/software/lsapipeline')
        fields = ['image', 'code', 'id', 'description']
        projectId = 113
        databasePath = 'T:/software/lsapipeline/install/apps/tk-custom-workfiles/python/tk_custom_workfiles/database/'
        self.getAssetList(projectId, fields, databasePath)
        self.getShotList(projectId, fields, databasePath)
    
    def getAssetList(self, projectId, fields, databasePath):
        self.assetList = self.tk.shotgun.find('Asset', [['project', 'is', {'type':'Project', 'id':projectId}]], fields)
        assetFile = open('%sShotgunAssetList.txt' % databasePath, 'wb')
        pickle.dump(self.assetList, assetFile)
        assetFile.close()
        print 'ShotgunAssetList updated...!!!!'
        return self.assetList

    def getShotList(self, projectId, fields, databasePath):
        self.shotList = self.tk.shotgun.find('Shot', [['project', 'is', {'type':'Project', 'id':projectId}]], fields)
        shotFile = open('%sShotgunShotList.txt' % databasePath, 'wb')
        pickle.dump(self.shotList, shotFile)
        shotFile.close()
        print 'ShotgunShotList updated...!!!!'
        return self.shotList

# output should be :
# [{'image': None, 'code': 'epDev001_mp001', 'type': 'Shot', 'id': 10311, 'description': None}, {'image': None, 'code': 'epDev001_sh001', 'type': 'Shot', 'id': 10310, 'description': None}]
# [{'image': None, 'code': 'CHAR_Name01', 'type': 'Asset', 'id': 2360, 'description': None}, {'image': None, 'code': 'ENV_Name01', 'type': 'Asset', 'id': 2361, 'description': None}, {'image': None, 'code': 'PROP_Name01', 'type': 'Asset', 'id': 2362, 'description': None}]

if __name__ == '__main__':
    entityLib = fetchEntityFromShotgun()