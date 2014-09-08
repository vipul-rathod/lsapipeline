import sys
import pickle

if 'T:\\software\\lsapipeline\\install\\core\\python\\' not in sys.path:
    sys.path.append('T:\\software\\lsapipeline\\install\\core\\python\\')
import sgtk

class AssetShotList(object):
    def __init__(self):
        self.databaseAssetFilePath = 'T:/software/lsapipeline/install/apps/tk-custom-workfiles/python/tk_custom_workfiles/database/ShotgunAssetList.txt'
        self.databaseShotFilePath = 'T:/software/lsapipeline/install/apps/tk-custom-workfiles/python/tk_custom_workfiles/database/ShotgunShotList.txt'

    def getAssetList(self):
        assetFile = open(self.databaseAssetFilePath, 'rb')
        newAssetList = pickle.load(assetFile)
        assetFile.close()
        return newAssetList

    def getShotList(self):
        shotFile = open(self.databaseShotFilePath, 'rb')
        newShotList = pickle.load(shotFile)
        shotFile.close()
        return newShotList

        # output should be :
        # [{'image': None, 'code': 'epDev001_mp001', 'type': 'Shot', 'id': 10311, 'description': None}, {'image': None, 'code': 'epDev001_sh001', 'type': 'Shot', 'id': 10310, 'description': None}]
        # [{'image': None, 'code': 'CHAR_Name01', 'type': 'Asset', 'id': 2360, 'description': None}, {'image': None, 'code': 'ENV_Name01', 'type': 'Asset', 'id': 2361, 'description': None}, {'image': None, 'code': 'PROP_Name01', 'type': 'Asset', 'id': 2362, 'description': None}]

if __name__ == '__main__':
    assetShotList = AssetShotList()