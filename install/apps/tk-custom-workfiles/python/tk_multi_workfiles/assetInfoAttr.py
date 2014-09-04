import maya.cmds as cmds

class AssetInfoAttr(object):
        
    def assetNameAttr(self, assetName, groupName):
        #    Add attributes and informations
        #        create and set assetName attribute
        cmds.addAttr(groupName, ln='assetName', dt = 'string')
        cmds.setAttr('%s.assetName' % groupName, e=1, k=1)
        cmds.setAttr('%s.assetName' % groupName, assetName, type='string')
        cmds.setAttr('%s.assetName' % groupName, l=1)

    def assetTaskAttr(self, assetTask, groupName):
        #    Add attributes and informations
        #        create and set assetTask attribute
        cmds.addAttr(groupName, ln='assetTask', dt = 'string')
        cmds.setAttr('%s.assetTask' % groupName, e=1, k=1)
        cmds.setAttr('%s.assetTask' % groupName, assetTask, type='string')
        cmds.setAttr('%s.assetTask' % groupName, l=1)

    def assetTypeAttr(self, assetType, groupName):
        #    Add attributes and informations
        #        create and set assetType attribute
        cmds.addAttr(groupName, ln='assetType', dt = 'string')
        cmds.setAttr('%s.assetType' % groupName, e=1, k=1)
        cmds.setAttr('%s.assetType' % groupName, assetType, type='string')
        cmds.setAttr('%s.assetType' % groupName, l=1)

    def assetIdAttr(self, assetId, groupName):
        #    Add attributes and informations
        #        create and set assetId attribute
        cmds.addAttr(groupName, ln='assetId', dt = 'string')
        cmds.setAttr('%s.assetId' % groupName, e=1, k=1)
        cmds.setAttr('%s.assetId' % groupName, assetId, type='string')
        cmds.setAttr('%s.assetId' % groupName, l=1)

    def assetTaskIdAttr(self, assetTaskId, groupName):
        #    Add attributes and informations
        #        create and set assetTaskId attribute
        cmds.addAttr(groupName, ln='assetTaskId', dt = 'string')
        cmds.setAttr('%s.assetTaskId' % groupName, e=1, k=1)
        cmds.setAttr('%s.assetTaskId' % groupName, assetTaskId, type='string')
        cmds.setAttr('%s.assetTaskId' % groupName, l=1)

    def assetLODTypeAttr(self, assetLODType, groupName):
        #    Add attributes and informations
        #        create and set assetLODType attribute
        cmds.addAttr(groupName, ln='assetLODType', dt = 'string')
        cmds.setAttr('%s.assetLODType' % groupName, e=1, k=1)
        cmds.setAttr('%s.assetLODType' % groupName, assetLODType, type='string')
        cmds.setAttr('%s.assetLODType' % groupName, l=1)