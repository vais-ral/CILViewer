from ccpi.viewer.utils.conversion import Converter
from ccpi.viewer.utils.conversion import vtkImageResampler
import unittest
import numpy as np


def calculate_target_downsample_shape(max_size, total_size, shape, acq=False):
    if not acq:
        xy_axes_magnification = np.power(max_size/total_size, 1/3)
        slice_per_chunk = int(1/xy_axes_magnification)
    else:
        slice_per_chunk = 1
        xy_axes_magnification = np.power(max_size/total_size, 1/2)
    num_chunks = 1 + len([i for i in
                          range(slice_per_chunk, shape[2], slice_per_chunk)])

    target_image_shape = (int(xy_axes_magnification * shape[0]),
                          int(xy_axes_magnification * shape[1]), num_chunks)
    return target_image_shape


class TestVTKImageResampler(unittest.TestCase):

    def setUp(self):
        # Generate random 3D array and convert to VTK Image Data:
        np.random.seed(1)
        bits = 16
        self.bytes_per_element = int(bits/8)
        self.input_3D_array = np.random.randint(10, size=(50, 10, 60), dtype=eval(f"np.uint{bits}"))
        self.input_vtk_image = Converter.numpy2vtkImage(self.input_3D_array)
        

    def test_vtk_resample_reader(self):
        # Tests image with correct target size is generated by resample reader:
        # Not a great test, but at least checks the resample reader runs
        # without crashing
        # TODO: improve this test
        reader = vtkImageResampler()
        reader.SetInputDataObject(self.input_vtk_image)
        target_size = 100
        reader.SetTargetSize(target_size)
        reader.Update()

        image = reader.GetOutput()
        extent = image.GetExtent()
        og_shape = np.shape(self.input_3D_array)
        resulting_shape = (extent[1]+1, (extent[3]+1), (extent[5]+1))
        og_shape = (og_shape[2], og_shape[1], og_shape[0])
        og_size = og_shape[0]*og_shape[1]*og_shape[2]*self.bytes_per_element
        expected_shape = calculate_target_downsample_shape(
            target_size, og_size, og_shape)
        self.assertEqual(resulting_shape, expected_shape)

        # # Now test if we get the full image extent if our
        # # target size is larger than the size of the image:
        target_size = og_size*2
        reader.SetTargetSize(target_size)
        reader.Update()
        image = reader.GetOutput()
        extent = image.GetExtent()
        expected_shape = og_shape
        resulting_shape = (extent[1]+1, (extent[3]+1), (extent[5]+1))
        self.assertEqual(resulting_shape, expected_shape)
        resulting_array = Converter.vtk2numpy(image)
        np.testing.assert_array_equal(self.input_3D_array, resulting_array)

        # # Now test if we get the correct z extent if we set that we
        # # have acquisition data
        target_size = 100
        reader.SetTargetSize(target_size)
        reader.SetIsAcquisitionData(True)
        reader.Update()
        image = reader.GetOutput()
        extent = image.GetExtent()
        shape_not_acquisition = calculate_target_downsample_shape(
            target_size, og_size, og_shape, acq=True)
        expected_size = shape_not_acquisition[0] * \
            shape_not_acquisition[1]*shape_not_acquisition[2]
        resulting_shape = (extent[1]+1, (extent[3]+1), (extent[5]+1))
        resulting_size = resulting_shape[0] * \
            resulting_shape[1]*resulting_shape[2]
        # angle (z direction) is first index in numpy array, and in cil
        # but it is the last in vtk.
        resulting_z_shape = extent[5]+1
        og_z_shape = np.shape(self.input_3D_array)[0]
        self.assertEqual(resulting_size, expected_size)
        self.assertEqual(resulting_z_shape, og_z_shape)


if __name__ == '__main__':
    unittest.main()
