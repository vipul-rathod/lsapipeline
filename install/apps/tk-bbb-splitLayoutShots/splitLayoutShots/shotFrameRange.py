import pymel.core as pm
import sys

### Best idea here is to assume the information is correct in shotgun
### Fetch the data from shotgun, and set the ranges from that information.
class FetchShotFrameRange(object):
    def __init__(self):
        pass

    def fetchShotFrameRange_Fn(self, shotName):
        self.shotName = shotName
        if pm.objExists(self.shotName + '_shotCam'):
            self.camName = pm.PyNode(self.shotName + '_shotCam')
            pm.select(self.camName, r=1)
            if pm.objectType(self.camName.getShape()) == 'camera':
                startFrame = pm.findKeyframe(timeSlider=False, which='first')
                endFrame = pm.findKeyframe(timeSlider=False, which='last')
                pm.select(cl=1)
                if startFrame == endFrame:
                    return sys.stderr.write('Please check the keyframes on %s_shotCam\n' % self.shotName)
                else:
                    return {'shotName':self.shotName, 'cameraName':str(self.camName.name()), 'mpStartFrame':startFrame, 'mpEndFrame':endFrame}

if __name__ == '__main__':
    fetchShotFrameRange = FetchShotFrameRange()
    mpShotFrameRange = fetchShotFrameRange.fetchShotFrameRange_Fn('ep107_sh053')