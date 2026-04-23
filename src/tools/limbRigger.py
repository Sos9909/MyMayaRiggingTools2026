from core.MayaWidget import MayaWidget
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel
import maya.cmds as mc
from maya.OpenMaya import MVector #this is the same as the Vector3 in Unity, transform.position
from PySide6.QtWidgets import QColorDialog #ColorPicker

import importlib
import core.MayaUtilities
importlib.reload(core.MayaUtilities)
from core.MayaUtilities import (CreateCircleControllerForJnt,
                                CreateBoxControllerForJnt, 
                                CreatePlusController, 
                                ConfigureCtrlForJnt,
                                GetObjectPositionAsMVec
                                )

#the class to handle the rigging job
class LimbRigger:
    #the constructor of the limb rigger class, to initialize the attributes
    def __init__(self):
        self.nameBase = " "
        self.controllerSize = 10
        self.blendControllerSize = 4
        self.controlColorRGB = [0,0,0]

    def SetNameBase(self, newNameBase):
        self.nameBase = newNameBase
        print(f"name base is set to: {self.nameBase}")

    def SetControllerSize(self, newControllerSize):
        self.controllerSize = newControllerSize

    def SetBlendControllerSize(self, newBlendControllerSize):
        self.blendControllerSize = newBlendControllerSize

    def RigLimb(self):
        print("Start Rigging!!")
        rootJnt, midJnt, endJnt = mc.ls(sl=True)
        print(f"found root {rootJnt}, mid: {midJnt} and end: {endJnt}")

        rootCtrl, rootCtrlGrp = CreateCircleControllerForJnt(rootJnt, "fk_" + self.nameBase, self.controllerSize)
        midCtrl, midCtrlGrp = CreateCircleControllerForJnt(midJnt, "fk_" + self.nameBase, self.controllerSize)
        endCtrl, endCtrlGrp = CreateCircleControllerForJnt(endJnt, "fk_" + self.nameBase, self.controllerSize)

        mc.parent(endCtrlGrp, midCtrl)
        mc.parent(midCtrlGrp, rootCtrl)

        endIKCtrl, endIKCtrlGrp = CreateBoxControllerForJnt(endJnt, "ik_" + self.nameBase, self.controllerSize)

        ikFkBlendCtrlPrefix = self.nameBase + "_ikfkBlend"
        ikFkBlendController = CreatePlusController(ikFkBlendCtrlPrefix, self.blendControllerSize)
        ikFkBlendController, ikFkBlendControllerGrp = ConfigureCtrlForJnt(rootJnt, ikFkBlendController, False)

        ikfkBlendAttrName = "ikfkBlend"
        mc.addAttr(ikFkBlendController, ln=ikfkBlendAttrName, min=0, max=1, k=True)

        ikHandleName = "ikHandle_" + self.nameBase
        mc.ikHandle(n=ikHandleName, sj = rootJnt, ee=endJnt, sol="ikRPsolver")

        rootJntLoc = GetObjectPositionAsMVec(rootJnt)
        endJntLoc = GetObjectPositionAsMVec(endJnt)

        poleVectorVals = mc.getAttr(f"{ikHandleName}.poleVector")[0]
        poleVecDir = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2])
        poleVecDir.normalize() #make it a unit vector, a vector that has a length of 1

        rootToEndVec = endJntLoc - rootJntLoc
        rootToEndDist = rootToEndVec.length()

        poleVectorCtrlLoc = rootJntLoc + rootToEndVec/2.0 + poleVecDir * rootToEndDist

        poleVectorCtrlName = "ac_" + self.nameBase + "poleVector"
        mc.spaceLocator(n=poleVectorCtrlName)

        poleVectorCtrlGrpName = poleVectorCtrlName + "_grp"
        mc.group(poleVectorCtrlName, n = poleVectorCtrlGrpName)

        mc.setAttr(f"{poleVectorCtrlGrpName}.translate", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, type="double3")
        mc.poleVectorConstraint(poleVectorCtrlName, ikHandleName)

        mc.parent(ikHandleName, endIKCtrl)
        mc.setAttr(f"{ikHandleName}.v",0)

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}",f"{ikHandleName}.ikBlend")
        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}",f"{endIKCtrlGrp}.v")
        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}",f"{poleVectorCtrlGrpName}.v")

        reverseNodeName = f"{self.nameBase}_reverse"
        mc.createNode("reverse", n=reverseNodeName)

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{reverseNodeName}.inputX")
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{rootCtrlGrp}.v")

        orientConstraint = None
        wristConnections = mc.listConnections(endJnt)
        for connection in wristConnections:
            if mc.objectType(connection) == "orientConstraint":
                orientConstraint = connection
                break

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{orientConstraint}.{endIKCtrl}W1")
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{orientConstraint}.{endCtrl}W0")

        topGrpName = f"{self.nameBase}_rig_grp"
        mc.group(n=topGrpName, empty =True)

        mc.parent(rootCtrlGrp, topGrpName)
        mc.parent(ikFkBlendControllerGrp, topGrpName)
        mc.parent(endIKCtrlGrp, topGrpName)
        mc.parent(poleVectorCtrlGrpName, topGrpName)

        # add color override for the topGrpName to be self.controlColorRGB
        shapes = mc.listRelatives(topGrpName, allDescendents=True, type="shape") or []

        for shape in shapes:
            mc.setAttr(f"{shape}.overrideEnabled", 1)
            mc.setAttr(f"{shape}.overrideRGBColors", 1)
            mc.setAttr(f"{shape}.overrideColorRGB",
                       self.controlColorRGB[0],
                       self.controlColorRGB[1],
                       self.controlColorRGB[2])


class LimbRiggerWidget(MayaWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Limb Rigger")
        self.rigger = LimbRigger()
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.masterLayout.addWidget(QLabel("Select the 3 joints of the limb, from base to end, and then: "))
        
        self.infoLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.infoLayout)
        self.infoLayout.addWidget(QLabel("Name Base" ))

        self.nameBaseLineEdit = QLineEdit()
        self.infoLayout.addWidget(self.nameBaseLineEdit)

        self.setNameBaseBtn = QPushButton("Set Name Base")
        self.setNameBaseBtn.clicked.connect(self.SetNameBaseBtnClicked)
        self.infoLayout.addWidget(self.setNameBaseBtn)

        # add a color pick widget to the self.masterLayout
        self.colorBtn = QPushButton("Pick Controller Color")
        # listen for a color change and connect to a function
        self.colorBtn.clicked.connect(self.OpenColorPicker)
        #the function needs to update the color of limbRigger: self.rigger.controlColorRGB
        self.masterLayout.addWidget(self.colorBtn)

        self.rigLimbBtn = QPushButton("Rig Limb")
        self.rigLimbBtn.clicked.connect(self.RigLimbBtnClicked)
        self.masterLayout.addWidget(self.rigLimbBtn)

    def OpenColorPicker(self):
        color = QColorDialog.getColor()

        if color.isValid():
            r = color.redF()
            g = color.greenF()
            b = color.blueF()

            self.rigger.controlColorRGB = [r, g, b]
            print(f"Selected color: {self.rigger.controlColorRGB}")


    def SetNameBaseBtnClicked(self):
        self.rigger.SetNameBase(self.nameBaseLineEdit.text())

    def RigLimbBtnClicked(self):
        self.rigger.RigLimb() 


    def GetWidgetHash(self):
        return "dbcfbfb7dbac1f171d28a817c8757ec62f7dc8d56c006dc270ecbf3c86656991"
    

def Run():
    limbRiggerWidget = LimbRiggerWidget()
    limbRiggerWidget.show()

Run()