import sys
import vtk
from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import Qt
from ccpi.viewer import viewer2D, viewer3D
from ccpi.viewer.QCILViewerWidget import QCILViewerWidget
import ccpi.viewer.viewerLinker as vlink
from ccpi.viewer.utils.conversion import Converter
import numpy as np
from eqt.ui.UIFormWidget import FormWidget, FormDockWidget

from ccpi.viewer.utils.conversion import cilHDF5ResampleReader
from ccpi.viewer.iviewer import SingleViewerCenterWidget
from PySide2.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QFrame, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QSlider, QSpinBox)

from qdarkstyle.dark.palette import DarkPalette
from qdarkstyle.light.palette import LightPalette
import qdarkstyle

class OpacityViewerWidget(SingleViewerCenterWidget):

    def __init__(self, parent = None, viewer=viewer3D):
        SingleViewerCenterWidget.__init__(self, parent)
        
        self.frame = QCILViewerWidget(viewer=viewer, shape=(600,600))
                
        self.setCentralWidget(self.frame)

        self.create_settings_dockwidget()

        self.set_app_style()
    
        self.show()

    def set_input(self, data):
        self.frame.viewer.setInputData(data)

    def create_settings_dockwidget(self):
        form_dock_widget = FormDockWidget()
        drop_down = QComboBox()
        drop_down.addItems(['gradient', 'scalar'])
        drop_down.currentTextChanged.connect(lambda: self.frame.viewer.setVolumeRenderOpacityMethod(drop_down.currentText()))
        form_dock_widget.addWidget( drop_down, "Select Opacity Method:", 'select_opacity')
        self.addDockWidget(Qt.TopDockWidgetArea, form_dock_widget)

    def set_app_style(self):
        '''Sets app stylesheet '''
        style = qdarkstyle.load_stylesheet(palette=DarkPalette)
        self.setStyleSheet(style)


class viewer_window(object):
    '''
    a Qt interactive viewer with one single dataset
    Parameters
    ----------
    data: vtkImageData
        image to be displayed       
    '''
    def __init__(self, data):
        '''Creator'''
        app = QtWidgets.QApplication(sys.argv)
        self.app = app
        
        self.setUp(data)
        self.show()

    def setUp(self, data):
        window = OpacityViewerWidget()        
        window.set_input(data)
        self.window = window
        self.has_run = None

    def show(self):
        if self.has_run is None:
            self.has_run = self.app.exec_()
        else:
            print ('No instance can be run interactively again. Delete and re-instantiate.')

if __name__ == "__main__":

    err = vtk.vtkFileOutputWindow()
    err.SetFileName("viewer.log")
    vtk.vtkOutputWindow.SetInstance(err)
 
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(r'D:\lhe97136\Work\Data\CILViewer\head.mha')
    reader.Update()


    viewer_window(reader.GetOutput())


