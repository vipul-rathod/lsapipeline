import sys, os
import maya.cmds as cmds
if 'T:/software/lsapipeline/custom' not in sys.path:
    sys.path.append('T:/software/lsapipeline/custom')

if 'C:/Python27/Lib/site-packages' not in sys.path:
    sys.path.append('C:/Python27/Lib/site-packages')

import CONST as CONST

def writeSubAssets():
    for eachARef in cmds.ls(type = 'assemblyReference'):
        getADefFilePath = cmds.getAttr('%s.definition' % eachARef)
        #print getADefFilePath 
        ## I:/lsapipeline/assets/Building/BBB_ZipBoatHouse_BLD/MDL/publish/assemblyDef/BBBZipBoatHouseBLD_ADef.v031.ma
        
        ## Convert this path to the gpu bbox and alembic paths
        gpuFolderPath = '%s/gpu' % '/'.join(getADefFilePath.split('/')[0:7])
        getLatestGPU = max(os.listdir(gpuFolderPath))
        gpuFilePath = '%s/%s'% (gpuFolderPath, getLatestGPU)
        
        ## Alembic
        abcFolderPath = '%s/alembic' % '/'.join(getADefFilePath.split('/')[0:7])
        getLatestABC = max(os.listdir(abcFolderPath))
        abcFilePath = '%s/%s'% (abcFolderPath, getLatestABC)
        
        ## BBox
        bboxFolderPath = '%s/bbox' % '/'.join(getADefFilePath.split('/')[0:7])
        getLatestBBOX = max(os.listdir(bboxFolderPath))
        bboxFilePath = '%s/%s'% (bboxFolderPath, getLatestBBOX)

        ## Maya File
        mayaFolderPath = '%s/maya' % '/'.join(getADefFilePath.split('/')[0:7])
        getLatestMaya = max(os.listdir(mayaFolderPath))
        mayaFilePath = '%s/%s'% (mayaFolderPath, getLatestMaya)
        
        ## SRF
        srfFolderPath = '%s/SRF/publish/sourceimages/256' % '/'.join(getADefFilePath.split('/')[0:5])

        ## Now write the bat file out since we can't use tar as a os.system command
        pathToTextFile = CONST.PATHTOPATHSTEXTFILE
        if not os.path.isfile(pathToTextFile):
            outfile = open(pathToTextFile, "w")
        else:
            outfile = open(pathToTextFile, "a")
        outfile.write('%s\n' % getADefFilePath)
        outfile.write('%s\n' % gpuFilePath)
        #outfile.write('%s\n' % abcFilePath)
        outfile.write('%s\n' % bboxFilePath)
        #outfile.write('%s\n' % mayaFilePath)
        #outfile.write('%s\n' % srfFolderPath)
        outfile.close()
        
def quitCMD():
    print 'HOW DO I CLOSE THIS WINDOW AUTOMATICALLY????'
    print 'HOW DO I CLOSE THIS WINDOW AUTOMATICALLY????'
    print 'HOW DO I CLOSE THIS WINDOW AUTOMATICALLY????'
    print 'HOW DO I CLOSE THIS WINDOW AUTOMATICALLY????'
    print 'HOW DO I CLOSE THIS WINDOW AUTOMATICALLY????'
    print 'HOW DO I CLOSE THIS WINDOW AUTOMATICALLY????'
    print 'HOW DO I CLOSE THIS WINDOW AUTOMATICALLY????'
    print 'YUP THAT MEANS YOU HAVE TO CLICK THE LITTLE CLOSE BUTTON NOW!!!'
    print 'YUP THAT MEANS YOU HAVE TO CLICK THE LITTLE CLOSE BUTTON NOW!!!'
    print 'YUP THAT MEANS YOU HAVE TO CLICK THE LITTLE CLOSE BUTTON NOW!!!'