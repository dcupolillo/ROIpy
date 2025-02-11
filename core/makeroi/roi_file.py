""" Created on Wed Aug 16 14:49:17 2023
    @author: dcupolillo """

from pathlib import Path
import json
import secrets
import re
import numpy as np
from ROIpy.core.components import Roi
from json import JSONEncoder


def generate_roi_uuid(
        n_bytes: int = 8,
        hex_length: int = 16
) -> tuple:
    """
    Generate a ROI UUID as a hexadecimal string and its exponential
    representation.

    Parameters
    ----------
    n_bytes : int, optional
        Number of random bytes to generate. The resulting hexadecimal
        string will have n_bytes*2 characters.
        Default is 8.
    hex_length : int, optional
        Desired length of the hexadecimal string. Must equal n_bytes * 2.
        Default is 16.

    Returns
    -------
    tuple
        A tuple containing:
            - A hexadecimal string of length hex_length.
            - Its corresponding exponential string representation.

    Raises
    ------
    ValueError
        If hex_length is not equal to n_bytes * 2.
    """

    if hex_length != n_bytes * 2:
        raise ValueError("hex_length must equal n_bytes * 2.")

    roi_uuid_hex = secrets.token_hex(n_bytes).upper()
    roi_uuid_int = int(roi_uuid_hex, 16)
    roi_uuid_str = f"{roi_uuid_int:.9e}"

    return roi_uuid_hex, roi_uuid_str


class MarkedList:
    """
    Wrap a list for custom JSON encoding.
    """

    def __init__(self, lst: list) -> None:
        """
        Initialize with a list.

        Parameters
        ----------
        lst : List[Any]
            The list to wrap.
        """

        if not isinstance(lst, list):
            raise TypeError("MarkedList requires a list.")

        self.lst = lst


class NullValue:
    """
    Wrap the string 'null' for custom JSON encoding.
    """

    def __init__(self, s: str) -> None:
        """
        Initialize with the string 'null'.

        Parameters
        ----------
        s : str
            Must be 'null'.

        Raises
        ------
        ValueError
            If s is not 'null'.
        """
        if s != "null":
            raise ValueError(
                "NullValue must be initialized with the string 'null'.")

        self.s = s


class CustomJSONEncoder(JSONEncoder):
    """
    Custom JSON encoder that formats MarkedList and NullValue objects.
    """

    def default(self, o):

        if isinstance(o, MarkedList):
            return "##<{}>##".format(o._list)

        if isinstance(o, NullValue):
            return "##<{}>##".format(o._string)


def generate_roi_files(
        class_var: object,
        rectangles: list,
        folder_path: str,
        structure_type: str = None
) -> None:

    if structure_type:
        name = class_var.stack_name.split('_')[0] + f"_{structure_type}"
        folder_path = Path(folder_path, name)
    else:
        name = class_var.stack_name
        folder_path = Path(folder_path, name)

    folder_path.mkdir(parents=True, exist_ok=True)

    for z, z_plane in enumerate(rectangles):

        z_ind = rectangles[z][0].z_ind

        # Filename of individual .roi files
        # Leading 0 if necessary
        file_path = Path(folder_path, f'z{z_ind:02}.roi')

        RoiGroup = {
            "ver": 1,
            "classname": "scanimage.mroi.RoiGroup",
            "name": f"Z{z_ind:02}",
            "UserData": NullValue("null"),
            "roiUuid": str(generate_roi_uuid()[0]),
            "roiUuiduint64": generate_roi_uuid()[1],
            "rois": []
        }

        for n_rect, rect in enumerate(z_plane):
            Roi = {
                "ver": 1,
                "classname": "scanimage.mroi.Roi",
                "name": f"z = {rect.z}, roi #{n_rect}",
                "UserData": NullValue("null"),
                "roiUuid": str(generate_roi_uuid()[0]),
                "roiUuiduint64": generate_roi_uuid()[1],
                "zs": 0,
                "scanfields": {
                    "classname":
                        "scanimage.mroi.scanfield.fields.RotatedRectangle",
                    "name": f"roi #{n_rect}",
                    "roiUuid": rect.roi_uuid,  # Replace with the actual UUID
                    "roiUuiduint64": "{:.9e}".format(int(rect.roi_uuid, 16)),
                    "centerXY": MarkedList(rect.center_deg),
                    "sizeXY": MarkedList(rect.size_deg),
                    "rotationDegrees": 90 + rect.rotation_degrees,
                    "enable": 1,
                    "pixelResolutionXY": MarkedList(rect.pixel_resolution_xy),
                    "pixelToRefTransform":
                        [MarkedList(list(row))
                         for row in rect.pixel_to_ref_transform],
                    "affine": [MarkedList(list(row)) for row in rect.affine]
                },
                "discretePlaneMode": 0,
                "powers": NullValue("null"),
                "pzAdjust": NullValue("null"),
                "Lzs": NullValue("null"),
                "interlaceDecimation": NullValue("null"),
                "interlaceOffset": NullValue("null"),
                "enable": 1
            }
            RoiGroup["rois"].append(Roi)

        json_file = json.dumps(RoiGroup, indent=8,
                               separators=(',', ': '),
                               cls=CustomJSONEncoder)

        json_file = json_file.replace('"##<', "").replace('>##"', "")
        json_file = json_file.replace('"##<', "null").replace('>##"', "")

        with open(file_path, 'w') as roi_file:
            roi_file.write(json_file)

    for z, z_plane in enumerate(rectangles):

        z_ind = rectangles[z][0].z_ind

        # Creates an empty folder for future storage of scan files
        z_folder_name = f"z{z_ind:02}"  # leading zero if necessary
        z_folder_path = Path(folder_path, z_folder_name)
        z_folder_path.mkdir(parents=True, exist_ok=True)


def find_closest_node(target, nodes):
    """
    Find the closest node to a given target point.

    Parameters
    ----------
    target : list or tuple
        The target [x, y, z] coordinates to match.
    nodes : list
        List of Node objects with x, y, and z attributes.

    Returns
    -------
    Node
        The closest Node object to the target point.
    """

    return min(
        nodes,
        key=lambda node: np.linalg.norm(
            np.array([node.x, node.y, node.z]) - np.array(target)))


def read_roi_files(
        class_var: object,
        nodes: list,
        folder_path: Path or str
) -> list:
    """
    Reads all .roi JSON files from a given folder and reconstructs
    a nested list of layers containing Roi objects.

    Parameters
    ----------
    folder_path : str
        Path to the folder containing .roi files.

    Returns
    -------
    list
        A nested list where each sublist contains Roi objects
        corresponding to a specific z-layer.

    Notes
    -------
    .roi files should be named according to the convention, for example
    "z00.roi", "z01.roi" and so on.
    """

    folder_path = Path(folder_path)
    roi_files = sorted(folder_path.glob("z*.roi"))

    if not roi_files:
        raise FileNotFoundError(f"No .roi files found in {folder_path}")

    layers_dict = {}

    for roi_file in roi_files:

        with open(roi_file, "r") as f:
            roi_data = json.load(f)

        # z_index = int(roi_data["name"][1:])

        # Alternatively, extract the z-index
        # from the filename (e.g., "z05.roi" -> 5)
        match = re.search(r"z(\d+)\.roi", roi_file.name)
        if not match:
            raise ValueError(f"Invalid filename format: {roi_file.name}")
        z_index = int(match.group(1))

        if z_index not in layers_dict:
            layers_dict[z_index] = []  # Initialize layer list

        for roi_dict in roi_data["rois"]:

            z = class_var.zs[z_index]

            # Create placeholder Nodes following this structure:
            # [x, y, id, compartment]

            size = (
                [dim * class_var.objective_resolution
                 for dim in
                 roi_dict["scanfields"]["sizeXY"]])
            center = (
                [coord * class_var.objective_resolution
                 for coord in
                 roi_dict["scanfields"]["centerXY"]])
            rotation = roi_dict["scanfields"]["rotationDegrees"] - 90

            dx = (size[0] / 2) * np.cos(np.radians(rotation))
            dy = (size[0] / 2) * np.sin(np.radians(rotation))

            estimated_start = [center[0] - dx, center[1] - dy, z]
            estimated_end = [center[0] + dx, center[1] + dy, z]

            if nodes:
                # Find closest actual nodes
                start_node = find_closest_node(estimated_start, nodes)
                end_node = find_closest_node(estimated_end, nodes)

                start_placeholder = [
                    start_node.x,
                    start_node.y,
                    start_node.z,
                    start_node.id,
                    start_node.type]
                end_placeholder = [
                    end_node.x,
                    end_node.y,
                    end_node.z,
                    end_node.id,
                    end_node.type]
            else:
                # Use estimated values if nodes are unavailable
                start_placeholder = estimated_start + [0, "compartment"]
                end_placeholder = estimated_end + [50, "compartment"]

            roi = Roi(
                obj_res=class_var.objective_resolution,
                zs=class_var.zs,
                center=center,
                rotation=rotation % 360,
                size=size,
                z=z,
                start=start_placeholder,
                end=end_placeholder,
                bottom_right=None,
                pixel_resolution_xy=(
                    roi_dict["scanfields"]["pixelResolutionXY"]),
                pix_um_ratio=None,
                acquisition_line_period=None,
                line_scan_period=None,
                rectangle_period=None,
                pixel_to_ref=roi_dict["scanfields"]["pixelToRefTransform"],
                affine=roi_dict["scanfields"]["affine"],
            )

            roi.roi_uuid = roi_dict["roiUuid"]
            roi.roi_uuid_uint64 = roi_dict["roiUuiduint64"]
            roi.pix_um_ratio = (
                (roi_dict["scanfields"]["pixelResolutionXY"][0] /
                 size[0]),
                (roi_dict["scanfields"]["pixelResolutionXY"][1] /
                 size[1]))

            layers_dict[z_index].append(roi)

    # Convert dictionary to sorted nested list
    layers = [layers_dict[z] for z in sorted(layers_dict.keys())]

    return layers
