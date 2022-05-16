#
#   Author 2022 Samuel Jones
#   Copyright 2022 SCD Rutherford Appleton Laboratory UKRI
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import os
import sys

from trame import state

from ccpi.web_viewer.trame_viewer import TrameViewer


TRAME_VIEWER = None


def data_finder():
    """
    Finds all files that are needed to be passed to the TrameViewer that in a list that is digestible, using the passed args.
    :return: list, of full file paths of data in the given directory parameter
    """
    data_files = []
    for index, arg in enumerate(sys.argv):
        if index == 0:
            # this is the python script so we want to skip
            continue
        if os.path.isfile(arg):
            data_files.append(arg)
        elif os.path.isdir(arg):
            files_in_dir = os.listdir(arg)
            for file in files_in_dir:
                data_files.append(os.path.join(arg, file))
        else:
            raise FileNotFoundError(f"This arg: {arg} is not a valid file or directory.")


def main() -> int:
    """
    Create the main class and run the TrameViewer
    :return: int, exit code for the program
    """
    data_files = data_finder()
    try:
        global TRAME_VIEWER
        TRAME_VIEWER = TrameViewer(data_files)
        TRAME_VIEWER.start()
    except Exception as e:
        print(str(e))
        return 1
    return 0


@state.change("slice")
def update_slice(**kwargs):
    TRAME_VIEWER.cil_viewer.setActiveSlice(kwargs["slice"])
    TRAME_VIEWER.cil_viewer.updatePipeline()
    TRAME_VIEWER.html_view.update()


@state.change("orientation")
def change_orientation(**kwargs):
    if "orientation" in kwargs:
        orientation = kwargs["orientation"]
        if orientation is not int:
            orientation = int(orientation)
        TRAME_VIEWER.switch_to_orientation(int(orientation))


@state.change("opacity")
def change_opacity_mapping(**kwargs):
    if "opacity" in kwargs:
        TRAME_VIEWER.set_opacity_mapping(kwargs["opacity"])


@state.change("file_name")
def change_model(**kwargs):
    TRAME_VIEWER.load_file(kwargs['file_name'], windowing_method=kwargs['opacity'])


@state.change("colour_map")
def change_colour_map(**kwargs):
    TRAME_VIEWER.change_colour_map(kwargs['colour_map'])


@state.change("windowing")
def change_windowing(**kwargs):
    TRAME_VIEWER.change_windowing(kwargs["windowing"][0], kwargs["windowing"][1], windowing_method=kwargs['opacity'])


@state.change("colouring")
def change_colouring(**kwargs):
    TRAME_VIEWER.change_colouring(kwargs["colouring"][0], kwargs["colouring"][1])


@state.change("slice_window")
def change_slice_window_level(**kwargs):
    min_window = kwargs["slice_window"][0]
    max_window = kwargs["slice_window"][1]
    level = (max_window + min_window) / 2
    window = (max_window - min_window)
    TRAME_VIEWER.change_slice_window(window=window, level=level)


if __name__ == "__main__":
    sys.exit(main())
