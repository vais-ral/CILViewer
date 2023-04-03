# -*- coding: utf-8 -*-
"""
Created on Fri Jun 30 13:40:28 2017

@author: ofn77899
http://public.kitware.com/pipermail/vtkusers/2011-February/065961.html
"""

import vtk
import sys

points = vtk.vtkPointSource()
points.SetNumberOfPoints(100000)

pointsMapper = vtk.vtkPolyDataMapper()
pointsMapper.SetInputConnection(points.GetOutputPort())

pointsActor = vtk.vtkQuadricLODActor()
pointsActor.SetMapper(pointsMapper)

ren = vtk.vtkRenderer()
ren.AddActor(pointsActor)
ren.SetBackground(0.1, 0.2, 0.4)

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(300, 300)

iren = vtk.vtkRenderWindowInteractor()
iren.SetInteractorStyle(None)
iren.SetRenderWindow(renWin)

# Add the observers to watch for particular events. These invoke
# Python functions.
Rotating = 0
Panning = 0
Zooming = 0

# Handle the mouse button events.
def ButtonEvent(obj, event):
     global Rotating, Panning, Zooming
     if event == "LeftButtonPressEvent":
         Rotating = 1
     elif event == "LeftButtonReleaseEvent":
         Rotating = 0
     elif event == "MiddleButtonPressEvent":
         Panning = 1
     elif event == "MiddleButtonReleaseEvent":
         Panning = 0
     elif event == "RightButtonPressEvent":
         Zooming = 1
     elif event == "RightButtonReleaseEvent":
         Zooming = 0


# General high-level logic
def MouseMove(obj, event):
     global Rotating, Panning, Zooming
     global iren, renWin, ren
     lastXYpos = iren.GetLastEventPosition()
     lastX = lastXYpos[0]
     lastY = lastXYpos[1]

     xypos = iren.GetEventPosition()
     x = xypos[0]
     y = xypos[1]

     center = renWin.GetSize()
     centerX = center[0]/2.0
     centerY = center[1]/2.0

     if Rotating:
         Rotate(ren, ren.GetActiveCamera(), x, y, lastX, lastY,
                centerX, centerY)
     elif Panning:
         Pan(ren, ren.GetActiveCamera(), x, y, lastX, lastY, centerX,
             centerY)
     elif Zooming:
         Dolly(ren, ren.GetActiveCamera(), x, y, lastX, lastY,
               centerX, centerY)


def Keypress(obj, event):
     key = obj.GetKeySym()
     if key == "e":
         obj.InvokeEvent("DeleteAllObjects")
         sys.exit()
     elif key == "w":
         Wireframe()
     elif key =="s":
         Surface()


# Routines that translate the events into camera motions.

# This one is associated with the left mouse button. It translates x
# and y relative motions into camera azimuth and elevation commands.
def Rotate(renderer, camera, x, y, lastX, lastY, centerX, centerY):
     camera.Azimuth(lastX-x)
     camera.Elevation(lastY-y)
     camera.OrthogonalizeViewUp()
     renWin.Render()


# Pan translates x-y motion into translation of the focal point and
# position.
def Pan(renderer, camera, x, y, lastX, lastY, centerX, centerY):
     FPoint = camera.GetFocalPoint()
     FPoint0 = FPoint[0]
     FPoint1 = FPoint[1]
     FPoint2 = FPoint[2]

     PPoint = camera.GetPosition()
     PPoint0 = PPoint[0]
     PPoint1 = PPoint[1]
     PPoint2 = PPoint[2]

     renderer.SetWorldPoint(FPoint0, FPoint1, FPoint2, 1.0)
     renderer.WorldToDisplay()
     DPoint = renderer.GetDisplayPoint()
     focalDepth = DPoint[2]

     APoint0 = centerX+(x-lastX)
     APoint1 = centerY+(y-lastY)

     renderer.SetDisplayPoint(APoint0, APoint1, focalDepth)
     renderer.DisplayToWorld()
     RPoint = renderer.GetWorldPoint()
     RPoint0 = RPoint[0]
     RPoint1 = RPoint[1]
     RPoint2 = RPoint[2]
     RPoint3 = RPoint[3]

     if RPoint3 != 0.0:
         RPoint0 = RPoint0/RPoint3
         RPoint1 = RPoint1/RPoint3
         RPoint2 = RPoint2/RPoint3

     camera.SetFocalPoint( (FPoint0-RPoint0)/2.0 + FPoint0,
                           (FPoint1-RPoint1)/2.0 + FPoint1,
                           (FPoint2-RPoint2)/2.0 + FPoint2)
     camera.SetPosition( (FPoint0-RPoint0)/2.0 + PPoint0,
                         (FPoint1-RPoint1)/2.0 + PPoint1,
                         (FPoint2-RPoint2)/2.0 + PPoint2)
     renWin.Render()


# Dolly converts y-motion into a camera dolly commands.
def Dolly(renderer, camera, x, y, lastX, lastY, centerX, centerY):
     dollyFactor = pow(1.02,(0.5*(y-lastY)))
     if camera.GetParallelProjection():
         parallelScale = camera.GetParallelScale()*dollyFactor
         camera.SetParallelScale(parallelScale)
     else:
         camera.Dolly(dollyFactor)
         renderer.ResetCameraClippingRange()

     renWin.Render()

# Wireframe sets the representation of all actors to wireframe.
def Wireframe():
     actors = ren.GetActors()
     actors.InitTraversal()
     actor = actors.GetNextItem()
     while actor:
         actor.GetProperty().SetRepresentationToWireframe()
         actor = actors.GetNextItem()

     renWin.Render()

# Surface sets the representation of all actors to surface.
def Surface():
     actors = ren.GetActors()
     actors.InitTraversal()
     actor = actors.GetNextItem()
     while actor:
         actor.GetProperty().SetRepresentationToSurface()
         actor = actors.GetNextItem()
     renWin.Render()


iren.AddObserver("LeftButtonPressEvent", ButtonEvent)
iren.AddObserver("LeftButtonReleaseEvent", ButtonEvent)
iren.AddObserver("MiddleButtonPressEvent", ButtonEvent)
iren.AddObserver("MiddleButtonReleaseEvent", ButtonEvent)
iren.AddObserver("RightButtonPressEvent", ButtonEvent)
iren.AddObserver("RightButtonReleaseEvent", ButtonEvent)
iren.AddObserver("MouseMoveEvent", MouseMove)
iren.AddObserver("KeyPressEvent", Keypress)


iren.Initialize()
renWin.Render()
iren.Start()