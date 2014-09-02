import sgtk

class ChildShotCutInfo(object):
    def __init__(self, entity={}):
        self.tk = sgtk.sgtk_from_path('T:/software/bubblebathbay')
        self.entity = entity
#         self.shotName = shotName
#         self.filter = filter
#         self.getChildShotCutInfo_Fn()
        
    def getChildShotCutInfo_Fn(self):
        self.childShotCutInfo = self.tk.shotgun.find_one(self.entity['type'], filters=[['id', 'is', self.entity['id']]], fields=['code', 'sg_cut_in', 'sg_cut_out'])
        return self.childShotCutInfo