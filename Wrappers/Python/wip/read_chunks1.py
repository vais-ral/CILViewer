import numpy as np
import vtk
import os
from ccpi.viewer import viewer2D
from ccpi.viewer.utils.conversion import Converter, parseNpyHeader, cilNumpyMETAImageWriter
from tqdm import tqdm
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import functools
import tempfile


class cilBaseResampleReader(VTKPythonAlgorithmBase):
    '''vtkAlgorithm to load and resample a numpy file to an approximate memory footprint

    
    '''
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        
        self.__FileName = 1
        self.__TargetShape = (256,256,256)
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__NumpyTypeCode = None


        
    def SetFileName(self, value):
        '''Sets the value at which the mask is active'''
        if not os.path.exists(value):
            raise ValueError('File does not exist!' , value)

        if value != self.__FileName:
            self.__FileName = value
            self.Modified()

    def GetFileName(self):
        return self.__FileName
    
    def SetTargetShape(self, value):
        if not isinstance (value, tuple):
            raise ValueError('Expected a tuple. Got {}' , type(value))

        if not value == self.__TargetShape:
            self.__TargetShape = value
            self.Modified()
    def GetTargetShape(self):
        return self.__TargetShape

    def FillInputPortInformation(self, port, info):
        '''This is a reader so no input'''
        return 1

    def FillOutputPortInformation(self, port, info):
        '''output should be of vtkImageData type'''
        info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkImageData")
        return 1
    
        
    def GetStoredArrayShape(self):
        return self.__StoredArrayShape
    def GetFileHeaderLength(self):
        return self.__FileHeaderLength
    def GetBytesPerElement(self):
        return self.__BytesPerElement
    def GetBigEndian(self):
        return self.__BigEndian
    def GetIsFortran(self):
        return self.__IsFortran
    def GetOutputVTKType(self):
        return self.__OutputVTKType
    def GetNumpyTypeCode(self):
        return self.__NumpyTypeCode
    
    def SetStoredArrayShape(self, value):
        if not isinstance (value , tuple):
            raise ValueError('Expected tuple, got {}'.format(type(value)))
        if len(value) != 3:
            raise ValueError('Expected tuple of length 3, got {}'.format(len(value)))
        self.__StoredArrayShape = value
    def SetFileHeaderLength(self, value):
        if not isinstance (value , int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__FileHeaderLength = value
    def SetBytesPerElement(self, value):
        if not isinstance (value , int):
            raise ValueError('Expected int, got {}'.format(type(value)))
        self.__BytesPerElement = value
    def SetBigEndian(self, value):
        if not isinstance (value , bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__BigEndian = value
    def SetIsFortran(self, value):
        if not isinstance (value , bool):
            raise ValueError('Expected bool, got {}'.format(type(value)))
        self.__IsFortran = value
    def SetOutputVTKType(self, value):
        if value not in [vtk.VTK_SIGNED_CHAR, vtk.VTK_UNSIGNED_CHAR,  vtk.VTK_SHORT,  vtk.VTK_UNSIGNED_SHORT,\
                         vtk.VTK_INT, vtk.VTK_UNSIGNED_INT,  vtk.VTK_FLOAT, vtk.VTK_DOUBLE, vtk.VTK_FLOAT,  \
                         vtk.VTK_DOUBLE]:
            raise ValueError("Unexpected Type: got {}", value)
        self.__OutputVTKType = value
    def SetNumpyTypeCode(self, value):
        if value not in ['b','B','h','H','i','I','f','d','F','D']:
            raise ValueError("Unexpected Type: got {}", value)
        self.__NumpyTypeCode = value

    def RequestData(self, request, inInfo, outInfo):
        outData = vtk.vtkImageData.GetData(outInfo)

        # get basic info
        nbytes = self.GetBytesPerElement()
        big_endian = self.GetBigEndian()
        readshape = self.GetStoredArrayShape()
        file_header_length = self.GetFileHeaderLength()
        is_fortran = self.GetIsFortran()
        
        if is_fortran:
            shape = list(readshape)
        else:
            shape = list(readshape)[::-1]

        total_size = shape[0] * shape[1] * shape[2]
        
        # calculate the product of the elements of TargetShape
        max_size = functools.reduce (lambda x,y: x*y, self.GetTargetShape(),1)
        # scaling is going to be similar in every axis (xy the same, z possibly different)
        axis_magnification = np.power(max_size/total_size, 1/3)
        slice_per_chunk = np.int(1/axis_magnification)
        
        # we will read in 5 slices at a time
        low_slice = [ i for i in range (0,shape[2], slice_per_chunk) ]
        
        low_slice.append( shape[2] )
        # print (low_slice)
        # print (len(low_slice))

        z_axis_magnification = (len(low_slice)-1)/shape[2]
        # print ("z_axis_magnification", z_axis_magnification)
        # print ("xy_axis magnification", axis_magnification, int(axis_magnification * shape[0]), int(axis_magnification * shape[1]))
        
        target_image_shape = (int(axis_magnification * shape[0]), 
                            int(axis_magnification * shape[1]), 
                            len(low_slice) -1)
        # print (target_image_shape)

        resampler = vtk.vtkImageReslice()
        resampler.SetOutputExtent(0,target_image_shape[0],
                                0,target_image_shape[1],
                                0,0)
        resampler.SetOutputSpacing(1/axis_magnification, 1/axis_magnification, 1/z_axis_magnification)

        # print ("allocate vtkImageData")
        # resampled_image = vtk.vtkImageData()
        resampled_image = outData
        resampled_image.SetExtent(0,target_image_shape[0],
                                0,target_image_shape[1],
                                0,target_image_shape[2])
        resampled_image.SetSpacing(1/axis_magnification, 1/axis_magnification, 1/z_axis_magnification)
        resampled_image.AllocateScalars(self.GetOutputVTKType(), 1)
    
        # slice size in bytes
        slice_length = shape[1] * shape[0] * nbytes

        
        #dimensions = descr['description']['shape']
        tmpdir = tempfile.mkdtemp()
        header_filename = os.path.join(tmpdir, "header.mhd")
        
        try:
            #resampler.Update()
            reader = vtk.vtkMetaImageReader()
            reader.SetFileName(header_filename)
            resampler.SetInputData(reader.GetOutput())
            
            for i,el in enumerate(low_slice):
                end_slice = el
                start_slice = end_slice - slice_per_chunk
                header_length = file_header_length + el * slice_length
                shape[2] = end_slice - start_slice
                cilNumpyMETAImageWriter.WriteMETAImageHeader(fname, 
                                    header_filename, 
                                    self.GetNumpyTypeCode(), 
                                    big_endian, 
                                    header_length, 
                                    tuple(shape), 
                                    spacing=(1.,1.,1.), 
                                    origin=(0.,0.,0.))
                # reset the filename for the reader to force Update, otherwise it won't work
                #reader.SetFileName('pippo')
                
                reader.Modified()
                reader.Update()
                # change the extent of the resampled image
                extent = (0,target_image_shape[0], 
                        0,target_image_shape[1],
                        i,i)
                resampler.SetOutputExtent(extent)
                resampler.Update()

                ################# vtk way ####################
                resampled_image.CopyAndCastFrom( resampler.GetOutput(), extent )
                self.UpdateProgress(i/len(low_slice))
                # npresampled = Converter.vtk2numpy(resampled_image)
        finally:
            os.remove(header_filename)
            os.rmdir(tmpdir)
        return 1

    def GetOutput(self):
        return self.GetOutputDataObject(0)

class cilNumpyResampleReader(cilBaseResampleReader):
    '''vtkAlgorithm to load and resample a numpy file to an approximate memory footprint

    
    '''
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1)
        super(cilNumpyResampleReader, self).__init__()
        
        self.__FileName = 1
        self.__TargetShape = (256,256,256)
        self.__IsFortran = False
        self.__BigEndian = False
        self.__FileHeaderLength = 0
        self.__BytesPerElement = 1
        self.__StoredArrayShape = None
        self.__OutputVTKType = None
        self.__NumpyTypeCode = None


        
    
    def ReadNpyHeader(self):
        # extract info from the npy header
        descr = parseNpyHeader(self.GetFileName())
        # find the typecode of the data and the number of bytes per pixel
        typecode = ''
        nbytes = 0
        for t in [np.uint8, np.int8, np.int16, np.uint16, np.int32, np.uint32, np.float16, np.float32, np.float64]:
            array_descr = descr['description']['descr'][1:]
            if array_descr == np.dtype(t).descr[0][1][1:]:
                typecode = np.dtype(t).char
                # nbytes = type_to_bytes[typecode]
                nbytes = Converter.numpy_dtype_char_to_bytes[typecode]
                # print ("Array TYPE: ", t, array_descr, typecode)            
                break
        
        # print ("typecode", typecode)
        # print (descr)
        big_endian = 'True' if descr['description']['descr'][0] == '>' else 'False'
        readshape = descr['description']['shape']
        is_fortran = descr['description']['fortran_order']
        file_header_length = descr['header_length']
        
        
        self.__IsFortran = is_fortran
        self.__BigEndian = big_endian
        self.__FileHeaderLength = file_header_length
        self.__BytesPerElement = nbytes
        self.__StoredArrayShape = readshape
        self.__OutputVTKType = Converter.numpy_dtype_char_to_vtkType[typecode]
        self.__NumpyTypeCode = typecode
        
        self.Modified()

        
    def GetStoredArrayShape(self):
        self.ReadNpyHeader()
        return self.__StoredArrayShape
    def GetFileHeaderLength(self):
        self.ReadNpyHeader()
        return self.__FileHeaderLength
    def GetBytesPerElement(self):
        self.ReadNpyHeader()
        return self.__BytesPerElement
    def GetBigEndian(self):
        self.ReadNpyHeader()
        return self.__BigEndian
    def GetIsFortran(self):
        self.ReadNpyHeader()
        return self.__IsFortran
    def GetOutputVTKType(self):
        self.ReadNpyHeader()
        return self.__OutputVTKType
    def GetNumpyTypeCode(self):
        self.ReadNpyHeader()
        return self.__NumpyTypeCode

    



if __name__ == "__main__":
    fname = os.path.abspath(r"D:\Documents\Dataset\CCPi\DVC\f000_crop\frame_000_f.npy")
    
    def progress(x,y):
        print ("{:.0f}%".format(100*x.GetProgress()))

    reader = cilNumpyResampleReader()
    reader.SetFileName(fname)
    reader.SetTargetShape((512,512,512))
    reader.AddObserver(vtk.vtkCommand.ProgressEvent, progress)
    reader.Update()
    resampled_image = reader.GetOutput()
    print ("Spacing ", resampled_image.GetSpacing())
    
    v = viewer2D()
    v.setInputData(resampled_image)
    # v.setInputData2(vtk_not_resampled)

    # lut = v.lut2
    # lut.SetNumberOfColors(16)
    # lut.SetHueRange(.2,.8)
    # lut.SetSaturationRange(.1, .6)
    # lut.SetValueRange(100, 200)
    # lut.SetAlphaRange(0,0.5)
    # lut.Build()
    # v.sliceActor2.Update()

    v.sliceActor.SetInterpolate(True)

    print("interpolated?" , v.sliceActor.GetInterpolate())
    v.startRenderLoop()

