import maya.cmds as cmds

class ShiftAnimCurves(object):
    def shiftAnimCurves_Fn(self, startFrame):
        self.startFrame = startFrame
        self.animCurves = cmds.ls(type=("animCurveTL","animCurveTU","animCurveTA","animCurveTT"))
        if self.animCurves:
            for animCurve in self.animCurves:
                cmds.keyframe(animCurve, edit=True, relative=True, iub=True, timeChange= -(self.startFrame-1))

if __name__ == '__main__':
    shiftAnimCurves = ShiftAnimCurves()
    shiftAnimCurves.shiftAnimCurves_Fn(101)