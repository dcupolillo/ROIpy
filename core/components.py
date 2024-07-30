""" Created on Mon Nov  6 14:11:21 2023
    @author: dcupolillo """

import numpy as np
import random
import math


class Node:

    # Node type classificators
    TYPE_MAPPING = {
        -1: 'root',
        0: 'undefined',
        1: 'soma',
        2: 'axon',
        3: 'basal dendrite',
        4: 'apical dendrite',
        5: 'custom'
    }

    def __init__(
            self,
            obj_res: float,
            _id: int,
            _type: int,
            x: float,
            y: float,
            z_ind: int,
            zs: list,
            radius: float,
            parent_id: int,
            matrix: np.ndarray,
            voxel_separation_x: float,
            voxel_separation_y: float
    ) -> None:
        """
        Individual node representation
        Gets initialized when creating a Morphology object

        Parameters
        ----------
        obj_res : float
            Objective Resolution.
        _id : int
            node id.
        _type : int
            compartment node belongs to.
        x : float
            x position.
        y : float
            y position.
        z_ind : int
            z slice node lays onto.
        zs : list
            list of all the scanned z positions.
        radius : float
            radius of the node.
        parent_id : int
            id of the parent node the node is connected to.
        matrix : np.ndarray
            transformation matrix.
        voxel_separation_x : float
            conversion factor generated during tracing.
        voxel_separation_y : float
            conversion factor generated during tracing.

        Returns
        -------
        None
            DESCRIPTION.

        """

        x_corrected = float(x) / voxel_separation_x
        y_corrected = float(y) / voxel_separation_y
        transformed_pixel_to_ref = self.transform_coordinates(
            [x_corrected,  y_corrected], matrix)

        self.id = int(_id)
        self.type = self.get_type(int(_type))
        self.x = transformed_pixel_to_ref[0] * obj_res
        self.y = transformed_pixel_to_ref[1] * obj_res
        self.z = float(zs[int(float(z_ind))])
        self.z_ind = float(z_ind)
        self.x_deg = transformed_pixel_to_ref[0]
        self.y_deg = transformed_pixel_to_ref[1]
        self.x_pix = x_corrected
        self.y_pix = y_corrected
        self.radius = float(radius)
        self.parent_id = int(parent_id)
        self.is_fork = False
        self.children = []

    def __getattr__(
            self,
            name: str):
        return self.__dict__[f"_{name}"]

    def __setattr__(
            self,
            name,
            value):
        self.__dict__[f"_{name}"] = value

    def transform_coordinates(
            self,
            coords: list or tuple,
            matrix: np.ndarray
    ) -> list:
        """
        Apply matrix transformation on individual nodes.

        Parameters
        ----------
        coords : list or tuple
            x, y coordinates of a single node.
        matrix : np.ndarray
            transformation matrix.

        Returns
        -------
        list
            transformed coordinates.

        """
        pixel_coords = np.array(coords + [1])
        ref_coords = np.dot(matrix, pixel_coords)
        return ref_coords[:-1]

    def get_type(
            self,
            _type: int
    ) -> str:
        """
        Returns neuron type

        Parameters
        ----------
        _type : int
            the identity classificator provided by .swc file.

        Returns
        -------
        str
            compartment name.

        """
        return self.TYPE_MAPPING.get(_type, 'unknown')

    def __repr__(self):
        repr_strings = []

        for key, value in self.__dict__.items():
            if key.startswith('_'):
                key = key.lstrip('_')
            repr_strings.append(f"{key} = {value}")

        return "\n(" + "\n".join(repr_strings) + ")\n"


class Roi:

    def __init__(
            self,
            obj_res: float,
            zs: list,
            center: list,
            rotation: float,
            size: list,
            z: float,
            start: list,
            end: list,
            bottom_right: list,
            pixel_resolution_xy: list,
            pix_um_ratio: list,
            acquisition_line_period: float,
            line_scan_period: float,
            rectangle_period: float,
            pixel_to_ref: np.ndarray = None,
            affine: np.ndarray = None,
    ) -> None:
        """
        Individual rectangular Roi representation
        Gets initialized when creating a Scanfield object.
        Calculate all corner's position
        Calculate all dimensions in micrometers, scanner degrees and pixel

        Parameters
        ----------
        obj_res : float
            Objective Resolution of the used objective.
        zs : list
            list of all the scanned z positions.
        center : list
            x, y coordinates of the rect_deg's center.
        rotation : float
            rotation degrees.
        size : list
            x, y dimension in micrometers.
        z : float
            z slice the rectangle lays onto.
        start : list
            x, y coordinate of the first Node included.
        end : list
            x, y coordinates of the last Node included.
        bottom_right : list
            x, y coordinates of the rectangle's bottom right corner.
        pixel_resolution_xy : list
            x, y dimensions in pixels.
        pix_um_ratio : list
            ratio between pixel and micrometer.
        pixel_to_ref : np.ndarray, optional
            transformation matrix. The default is None.
        affine : np.ndarray, optional
            affine matrix. The default is None.

        Returns
        -------
        None

        """

        self.roi_uuid = self.generate_roi_uuid()[0]
        self.roi_uuid_uint64 = self.generate_roi_uuid()[1]
        self.compartment = start[4]
        self.center_xy = center
        self.rotation_degrees = rotation
        self.size_xy = size
        self.area = size[0] * size[1]
        self.dim_ratio = size[0] / size[1]
        self.z = z
        self.z_ind = zs.index(z)
        self.center_deg = [(i / obj_res) for i in center]
        self.size_deg = [(i / obj_res) for i in size]
        self.pixel_resolution_xy = pixel_resolution_xy
        self.pix_um_ratio = pix_um_ratio
        self.start_node = start[:2]
        self.end_node = end[:2]
        self.start_node_deg = [(i / obj_res) for i in start[:2]]
        self.end_node_deg = [(i / obj_res) for i in end[:2]]
        self.start_node_id = start[3]
        self.end_node_id = end[3]
        self.bottom_right = bottom_right or self.find_corners()[3]
        self.bottom_right_deg = [(i / obj_res) for i in bottom_right]
        self.bottom_left = self.find_corners()[2]
        self.bottom_left_deg = [(i / obj_res) for i in self.bottom_left]
        self.top_right = self.find_corners()[1]
        self.top_right_deg = [(i / obj_res) for i in self.top_right]
        self.top_left = self.find_corners()[0]
        self.top_left_deg = [(i / obj_res) for i in self.top_left]
        self.pixel_to_ref_transform = np.array(pixel_to_ref)
        self.affine = np.array(affine)
        self.acquisition_line_period = acquisition_line_period
        self.line_scan_period = line_scan_period
        self.rectangle_period = rectangle_period

    def __getattr__(
            self,
            name: str):
        return self.__dict__[f"_{name}"]

    def __setattr__(
            self,
            name: str,
            value):
        self.__dict__[f"_{name}"] = value

    def generate_roi_uuid(self) -> list:
        """
        Generate a unique random hexadecimal string
        and assign it to each rectangle
        """
        roi_uuid_hex = ''.join(random.choices('0123456789ABCDEF', k=16))
        roi_uuid_uint64 = int(roi_uuid_hex, 16)
        roi_uuid_str = "{:.9e}".format(roi_uuid_uint64)
        return [roi_uuid_hex, roi_uuid_str]

    def find_corners(self) -> tuple:
        """
        Calculate rect's corners x, y position
        """
        deg_rad = math.radians(self.rotation_degrees + 90)
        half_height = self.size_xy[1] / 2
        half_width = self.size_xy[0] / 2
        x_center, y_center = self.center_xy

        x_cos = half_width * math.cos(deg_rad)
        y_sin = half_height * math.sin(deg_rad)
        x_sin = half_width * math.sin(deg_rad)
        y_cos = half_height * math.cos(deg_rad)

        x_bottom_right, y_bottom_right = (x_center + (y_cos + x_sin),
                                          y_center - (y_sin - x_cos))
        x_bottom_left, y_bottom_left = (x_center - (y_sin - x_cos),
                                        y_center + (x_sin + y_cos))
        x_top_right, y_top_right = (x_center + (y_sin - x_cos),
                                    y_center - (x_sin + y_cos))
        x_top_left, y_top_left = (x_center + (x_cos + y_sin),
                                  y_center + (x_sin - y_cos))

        return ([x_top_left, y_top_left],
                [x_top_right, y_top_right],
                [x_bottom_left, y_bottom_left],
                [x_bottom_right, y_bottom_right])

    def __repr__(self):
        repr_strings = []

        for key, value in self.__dict__.items():
            if key.startswith('_'):
                key = key.lstrip('_')
            repr_strings.append(f"{key} = {value}")

        return "\n(" + "\n".join(repr_strings) + ")\n"
