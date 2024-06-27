from ccpi.viewer.CILViewer2D import CILViewer2D as viewer2D
from ccpi.viewer.CILViewer import CILViewer as viewer3D
import glob
import vtk
import numpy as np

def createAnimation(viewer, FrameCount=20, 
                    InitialCameraPosition=None, FocalPoint=None, 
                    ClippingRange=None, AngleRange = 360, ViewUp = None):
    
    viewer

    if InitialCameraPosition is None:
        InitialCameraPosition = viewer.getCamera().GetPosition()
    if FocalPoint is None:
        FocalPoint = viewer.getCamera().GetFocalPoint()
    if ClippingRange is None:
        ClippingRange = (0,2000)
    if ViewUp is None:
        ViewUp = (0,0,1)
    if FrameCount is None:
        FrameCount = 100
    #Setting locked values for camera position
    locX = InitialCameraPosition[0]
    locY = InitialCameraPosition[1]
    locZ = InitialCameraPosition[2]

    print('Initial Camera Position: {}'.format(InitialCameraPosition))
    #Setting camera position
    viewer.getCamera().SetPosition(InitialCameraPosition)
    viewer.getCamera().SetFocalPoint(FocalPoint)

    #Setting camera viewup 
    viewer.getCamera().SetViewUp(ViewUp)

    #Set camera clipping range
    viewer.getCamera().SetClippingRange(ClippingRange)

    #Defining distance from camera to focal point
    r = np.sqrt(((InitialCameraPosition[0]-FocalPoint[0])**2)
    +(InitialCameraPosition[1]-FocalPoint[1])**2)
    print('Radius (distance from camera to focal point): {}'.format(r))
    


    #Animating the camera
    for x in range(FrameCount):
        # move the slice during rotation
        new_slice = round(x/FrameCount * viewer.img3D.GetDimensions()[2])
        print('displaying slice {}'.format(new_slice))
        viewer.style.SetActiveSlice(new_slice)
        viewer.updatePipeline(False)

        
        angle = (2 * np.pi ) * (x/FrameCount)
        NewLocationX = r * np.sin(angle) + FocalPoint[0]
        NewLocationY = r * np.cos(angle) + FocalPoint[1]
        NewLocation = (NewLocationX, NewLocationY, locZ)
        camera = vtk.vtkCamera()
        camera.SetFocalPoint(FocalPoint)
        camera.SetViewUp(ViewUp)
        camera.SetPosition(*NewLocation)
        viewer.ren.SetActiveCamera(camera)
        viewer.adjustCamera()
        
        import time
        time.sleep(0.1)
        print("render frame {} angle {}".format(x, angle))
        print('Camera Position: {}'.format(NewLocation))
        rp = np.sqrt(((NewLocation[0]-FocalPoint[0])**2)
            +(NewLocation[1]-FocalPoint[1])**2)
        print ('Camera trajectory radius {}'.format(rp))
        #Rendering and saving the render
        viewer.getRenderer().Render()
        viewer.renWin.Render()
        saveRender(viewer, x, 'test')

def saveRender(viewer, number, file_prefix, directory='.'):
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(viewer.renWin)
    w2if.Update()

    
    saveFilename = '{}_{:04d}.png'.format(os.path.join(directory, file_prefix), number)

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(saveFilename)
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.Write()

if __name__ == '__main__':
    v = viewer3D(debug=False)
    from ccpi.viewer.utils.io import ImageReader, cilHDF5ResampleReader, cilTIFFResampleReader
    from ccpi.viewer.utils.conversion import cilTIFFImageReaderInterface
    import os
    # reader = ImageReader(r"C:\Users\ofn77899\Data\dvc/frame_000_f.npy", resample=False)
    # reader = ImageReader(r"{}/head_uncompressed.mha".format(os.path.dirname(__file__)), resample=False)
    # data = reader.Read()
    
    dirname = r"C:\Users\ofn77899\Data\HOW\Not_Angled"
    fnames = [el for el in glob.glob(os.path.join(dirname, "*.tiff"))]
    
    reader = cilTIFFResampleReader()
    reader.SetFileName(fnames)
    reader.SetTargetSize(1024*1024*1024)
    reader.Update()
    data = reader.GetOutput()

    dims = data.GetDimensions()
    spac = list(data.GetSpacing())
    spac[2] = dims[0]/dims[2]
    print (data.GetSpacing())
    data.SetSpacing(*spac)
    print (data.GetSpacing())

    v.setInputData(reader.GetOutput())

    v.style.ToggleVolumeVisibility()
    
    color_percentiles = (75., 99.)
    scalar_opacity_percentiles = (80., 99.)
    gradient_opacity_percentiles = (95., 99.9)
    max_opacity = 0.05
    

    # self.setVolumeColorPercentiles(*color_percentiles, update_pipeline=False)
    # self.setScalarOpacityPercentiles(*scalar_opacity_percentiles, update_pipeline=False)
    # self.setGradientOpacityPercentiles(*gradient_opacity_percentiles, update_pipeline=False)
    # self.setMaximumOpacity(max_opacity)

    v.setVolumeColorMapName('bone')

    # define colors and opacity with default values
    colors, opacity = v.getColorOpacityForVolumeRender()

    v.volume_property.SetColor(colors)

    method = 'gradient'
    if method == 'gradient':
        v.setVolumeRenderOpacityMethod('gradient')
        v.setGradientOpacityPercentiles(*gradient_opacity_percentiles, update_pipeline=False)
        v.volume_property.SetGradientOpacity(opacity)
    else:
        v.setVolumeRenderOpacityMethod('scalar')
        v.setScalarOpacityPercentiles(*scalar_opacity_percentiles, update_pipeline=False)
        v.volume_property.SetScalarOpacity(opacity)
    
    v.setVolumeColorPercentiles(*color_percentiles, update_pipeline=False)
    v.setMaximumOpacity(max_opacity)

    # v.style.ToggleSliceVisibility()

    # default background
    # self.ren.SetBackground(.1, .2, .4)
    v.ren.SetBackground(0, 0, 0)
    
    # v.startRenderLoop()

    createAnimation(v, FrameCount=10, InitialCameraPosition=((483.8653687626969, -2173.282759469902, 1052.4208133258792)), AngleRange=360)

    