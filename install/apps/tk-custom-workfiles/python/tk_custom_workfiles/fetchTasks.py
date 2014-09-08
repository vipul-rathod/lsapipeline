import assetShotList
import sys
if 'T:\\software\\lsapipeline\\install\\core\\python\\' not in sys.path:
    sys.path.append('T:\\software\\lsapipeline\\install\\core\\python\\')
import sgtk
import pickle

tk = sgtk.sgtk_from_path('T:/software/lsapipeline')
databasePath = 'T:/software/lsapipeline/install/apps/tk-custom-workfiles/python/tk_custom_workfiles/database/'

asList = assetShotList.AssetShotList()
sg_datas = asList.getAssetList()

for each in asList.getShotList():
    sg_datas.append(each)

fields = ["content", "task_assignees", "image", "sg_status_list", "step.Step.list_order"]
taskDetails = {}

for each in sg_datas:
    task = tk.shotgun.find("Task", [["project", "is", {'type':'Project','id':113}], ["step", "is_not", None], ["entity", "is", each]], fields)
    taskDetails[each["code"]] = [each, task]

file = open("%s/ShotgunTaskList.txt" % databasePath, "wb")
pickle.dump(taskDetails, file)
file.close()
