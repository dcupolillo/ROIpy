""" Created on Wed Aug 16 14:49:17 2023
    @author: dcupolillo """

from pathlib import Path
import json
import random
from json import JSONEncoder


def generate_roi_uuid(
) -> tuple:

    roiUuidHex = ''.join(random.choices('0123456789ABCDEF', k=16))
    roiUuidUint64 = int(roiUuidHex, 16)
    roiUuidStr = "{:.9e}".format(roiUuidUint64)

    return roiUuidHex, roiUuidStr


class MarkedList:

    _list = None

    def __init__(
            self,
            l
    ) -> None:
        """
        To flag lists as MarkedList type.
        """
        self._list = l


class NullValue:

    def __init__(
            self,
            s
    ) -> None:
        """
        To flag the string "null" as NullValue type
        """

        self._string = s


class CustomJSONEncoder(JSONEncoder):

    def default(
            self,
            o):

        if isinstance(o, MarkedList):
            return "##<{}>##".format(o._list)

        if isinstance(o, NullValue):
            return "##<{}>##".format(o._string)


def generate_roi_file(
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
            "name": "Z{z_ind:02}",
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
