import maya.cmds as mc
from PySide6.QtWidgets import QWidget, QMainWindow
from PySide6.QtCore import Qt
import maya.OpenMayaUI as omui
from shiboken6 import wrapInstance

def GetMayaMainWindow()->QMainWindow:
    GetMayaMainWindow = omui.MQtUtil.mainWindow()
    return wrapInstance(int(GetMayaMainWindow), QMainWindow)

def RemoveWidgetWithName(objectName):
    for widget in GetMayaMainWindow().findChildren(QWidget, objectName):
        widget.deleteLater()


class MayaWidget(QWidget):
    def __init__(self):
        super().__init__(parent=GetMayaMainWindow())
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle("Maya Widget")
        RemoveWidgetWithName(self.GetWidgetHash())
        self.setObjectName(self.GetWidgetHash())

    def GetWidgetHash(self):
        #random hash generator
        return "ce4f1c8f314dc8e96952e2cbe080f1b41517a5921aefad04fc891e90c39b8e07" 
