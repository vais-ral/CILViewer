from argparse import ArgumentParser

import yaml
import schema
from schema import SchemaError, Schema, Optional

from ccpi.viewer.utils.io import ImageReader, ImageWriter

# SO FAR THIS READS AND DOWNSAMPLES AND WRITES TO HDF5

#### EXAMPLE INPUT YAML:
'''
array:
  shape: (1024,1024,1024)
  is_fortran: False
  is_big_endian: True
  typecode: 'float32'
  dataset_name: '/entry1/tomo_entry/data/data' # valid for HDF5 and Zarr
resample:
  target_size: 100000
  resample_z: True
output:
  file_name: 'this_fname.nxs'
  format: 'hdf5' # npy, METAImage, NIFTI (or Zarr to come)
  '''

### THIS IS WHAT THE OUTPUT STRUCTURE OF AN EXAMPLE OUTPUT HDF5 FILE WOULD LOOK LIKE:
'''
- entry1 : <HDF5 group "/entry1" (1 members)>
            - tomo_entry : <HDF5 group "/entry1/tomo_entry" (1 members)>
                    - data : <HDF5 group "/entry1/tomo_entry/data" (1 members)>
                            - data : <HDF5 dataset "data": shape (500, 100, 600), type "<f4">
                                            - bit_depth : 64
                                            - file_name : test_3D_data.npy
                                            - header_length : 128
                                            - is_big_endian : False
                                            - origin : [0. 0. 0.]
                                            - shape : [500 100 600]
                                            - spacing : [1 1 1]
    - entry2 : <HDF5 group "/entry2" (1 members)>
            - tomo_entry : <HDF5 group "/entry2/tomo_entry" (1 members)>
                    - data : <HDF5 group "/entry2/tomo_entry/data" (1 members)>
                            - data : <HDF5 dataset "data": shape (500, 18, 109), type "<f8">
                                            - cropped : False
                                            - origin : [2.23861279 2.23861279 0.        ]
                                            - resample_z : True
                                            - resampled : True
                                            - spacing : [5.47722558 5.47722558 1.        ]
'''
 


schema = Schema(
        {
            Optional('array'): {Optional('shape'): tuple, # only for raw
                                Optional('is_fortran'): bool, # only for raw
                                Optional('is_big_endian'): bool, # only for raw
                                Optional('typecode'): str, # only for raw
                                Optional('dataset_name'): str}, # only for hdf5 # need to set default
            'resample': {'target_size': int, 
                         'resample_z' : bool},
            'output': {'file_name': str,
                       'format': str}
        }
    )



def main():
    parser = ArgumentParser(description='Dataset to Resample')
    parser.add_argument('input_dataset', help='Input dataset')
    parser.add_argument('yaml_file', help='Input yaml file')

    args = parser.parse_args()

    with open(args.yaml_file) as f:
        params_raw = yaml.safe_load(f)
        params = {}
        for key, dict in params_raw.items():
            # each of the values in data_raw is a dict
            params[key] = {}
            for sub_key, value in dict.items():
                try:
                    params[key][sub_key] = eval(value)
                except:
                    params[key][sub_key] = value
    try:
        schema.validate(params)
    except SchemaError as e:
        print(e)

   
    if 'array' in params.keys():
        raw_attrs = {}
        for key, value in params['array'].items():
            if key == 'dataset_name':
                dataset_name = value
            else:
                raw_attrs[key] = value
    else:
        raw_attrs = None
        dataset_name = None


    reader = ImageReader(file_name=args.input_dataset, resample=True, target_size=params['resample']['target_size'],
             resample_z=params['resample']['resample_z'], raw_image_attrs=raw_attrs, hdf5_dataset_name=dataset_name)
    downsampled_image = reader.read()
    #print(downsampled_image)
    original_image_attrs = reader.get_original_image_attrs()
    loaded_image_attrs = reader.get_loaded_image_attrs()
    datasets = [None, downsampled_image]
    attributes = [original_image_attrs, loaded_image_attrs]
    
    # writer = ImageWriter(file_name=params['output']['file_name'], format='hdf5', datasets=datasets, attributes=attributes)
    # writer.write()

    writer = ImageWriter()
    writer.SetFileName(params['output']['file_name'])
    writer.SetFileFormat(params['output']['format'])
    writer.SetOriginalDataset(None, original_image_attrs)
    writer.AddChildDataset(downsampled_image,  loaded_image_attrs)
    writer.Write()


if __name__ == '__main__':
    main()
