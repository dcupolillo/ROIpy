""" Created on Mon Nov  6 14:11:21 2023
    @author: dcupolillo """

import numpy as np
import random
import math


class Node:
    """
    Representation of an individual node in a neuronal morphology.

    This class encapsulates the attributes and transformations
    associated with a single node within a neuronal structure,
    including positional information, type classification
    and connections to parent/child nodes.

    Attributes
    ----------
    type_mapping : dict
        Maps integer type codes (from .swc files)
        to descriptive compartment names.
    """

    type_mapping = {
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
        _type: int or str,
        x: float,
        y: float,
        z_ind: int,
        zs: list,
        radius: float,
        parent_id: int,
        matrix: np.ndarray,
        voxel_separation_x: float,
        voxel_separation_y: float,
    ) -> None:
        """
        Initialize a Node instance.

        Parameters
        ----------
        obj_res : float
            Objective resolution (conversion factor for coordinates).
        _id : int
            Unique identifier for the node.
        _type : int
            Compartment type code (e.g., soma, axon).
        x : float
            X-coordinate of the node (in pixels).
        y : float
            Y-coordinate of the node (in pixels).
        z_ind : int
            Index of the Z-plane the node is located on.
        zs : list
            List of all scanned Z positions (in µm).
        radius : float
            Radius of the node (in µm).
        parent_id : int
            ID of the parent node connected to this node.
        matrix : np.ndarray
            Transformation matrix for coordinate conversion.
        voxel_separation_x : float
            Voxel-to-micrometer conversion factor along X.
        voxel_separation_y : float
            Voxel-to-micrometer conversion factor along Y.
        is_fork : bool, optional
            Indicates if the node is a bifurcation point. Default is False.
        children : list, optional
            List of IDs of child nodes. Default is an empty list.
        x_deg : float, optional
            X-coordinate in degrees after transformation. Default is None.
        y_deg : float, optional
            Y-coordinate in degrees after transformation. Default is None.
        x_pix : int, optional
            X-coordinate in pixels. Default is None.
        y_pix : int, optional
            Y-coordinate in pixels. Default is None.
        z : float, optional
            Z-coordinate in micrometers. Default is None.
        branch_degree : int
            Degree of the branch the node belongs to. Default is None.
        branch_id : int
            ID of the branch the node belongs to, Default is None.
        has_spine : bool
            Indicate whether the node i the closest to a spine.
            Default is None.
        spine_id : int
            In case node has a spine, the ID od the spine. Default is None.

        Returns
        -------
        None
        """

        # Spatial calibration adjustement for pixel size
        x_corrected = float(x) / voxel_separation_x
        y_corrected = float(y) / voxel_separation_y

        self.id = int(_id)
        self.type = self.get_type(int(_type))
        self.obj_res = obj_res
        self.zs = zs
        self.matrix = matrix
        self.voxel_separation_x = voxel_separation_x
        self.voxel_separation_y = voxel_separation_y

        if matrix is not None:
            transformed_pixel_to_ref = self.transform_coordinates(
                [x_corrected,  y_corrected], matrix)

            self.x = transformed_pixel_to_ref[0] * obj_res  # deg to µm
            self.y = transformed_pixel_to_ref[1] * obj_res
            self.x_deg = transformed_pixel_to_ref[0]
            self.y_deg = transformed_pixel_to_ref[1]

        else:
            self.x = x_corrected
            self.y = y_corrected
            self.x_deg = None
            self.y_deg = None

        if zs is not None:
            self.z = float(zs[int(float(z_ind))])
        else:
            self.z = float(z_ind)

        self.z_ind = float(z_ind)

        self.x_pix = x_corrected
        self.y_pix = y_corrected
        self.radius = float(radius)
        self.parent_id = int(parent_id)
        self.is_fork = None
        self.children = []
        self.branch_degree = None
        self.branch_id = None
        self.has_spine = None
        self.spine_id = None

    def __getattr__(self, name: str):
        key = f"_{name}"
        if key in self.__dict__:
            return self.__dict__[key]
        raise AttributeError(name)

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
        Apply a transformation matrix to the node's coordinates.

        Parameters
        ----------
        coords : list or tuple
            X, Y coordinates of the node.
        matrix : np.ndarray
            Transformation matrix.

        Returns
        -------
        list
            Transformed coordinates in angle degrees.
        """

        pixel_coords = np.array(coords + [1])
        ref_coords = np.dot(matrix, pixel_coords)

        return ref_coords[:-1]

    def get_type(self,  _type: int) -> str:
        """
        Retrieve the compartment type name for a given type code.

        Parameters
        ----------
        _type : int
            Type code from the .swc file.

        Returns
        -------
        str
            Compartment name corresponding to the type code.
        """
        return self.type_mapping.get(_type, 'unknown')

    def __repr__(self):
        """
        Return a custom string representation of the Node instance.

        Returns
        -------
        str
            String representation of the Node instance.
        """

        attributes_to_display = [
            '_id', '_type',
            'x', 'y', 'z',
            'radius', 'parent_id',
            'is_fork', 'children',
            'branch_degree', 'branch_id',
            'has_spine', 'spine_id']

        repr_strings = [None] * len(attributes_to_display)

        for n, key in enumerate(attributes_to_display):
            value = getattr(self, key, None)
            key = key.lstrip('_') if key.startswith('_') else key
            repr_strings[n] = f"{key} = {value}"

        return "\n(" + "\n".join(repr_strings) + ")\n"

    def to_dict(self) -> dict:
        """
        Serialize the Node instance to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the Node instance.
        """

        return {
            key: value
            for key, value in self.__dict__.items()}

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create a Node instance from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary containing Node attributes.

        Returns
        -------
        Node
            Node instance created from the dictionary.
        """

        node = cls.__new__(cls)
        for key, value in data.items():
            if key.startswith('_'):
                key = key.lstrip('_')
            setattr(node, key, value)

        return node


class Roi:
    """
    Representation of an individual rectangular ROI (Region of Interest).

    This class encapsulates attributes and methods to define and manipulate a
    rectangular ROI, including transformations, corner calculations, and
    metadata generation.
    """

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
            branch_degree: int = None,
            branch_id: int = None,
    ) -> None:
        """
        Initialize a rectangular ROI.

        Parameters
        ----------
        obj_res : float
            Objective resolution of the used objective.
        zs : list
            List of all scanned Z positions (in µm).
        center : list
            [x, y] coordinates of the rectangle's center (in µm).
        rotation : float
            Rotation of the rectangle (in degrees).
        size : list
            [width, height] dimensions of the rectangle (in µm).
        z : float
            Z position (in µm) of the rectangle.
        start : list
            [x, y, id, compartment] of the starting node within the rectangle.
        end : list
            [x, y, id, compartment] of the ending node within the rectangle.
        bottom_right : list
            [x, y] coordinates of the bottom-right corner (in µm).
        pixel_resolution_xy : list
            [x, y] dimensions in pixels.
        pix_um_ratio : list
            Pixel-to-micrometer conversion ratios for x and y.
        acquisition_line_period : float
            Period of acquisition for a single line (in seconds).
        line_scan_period : float
            Time taken to scan one line (in seconds).
        rectangle_period : float
            Time taken to scan the rectangle (in seconds).
        pixel_to_ref : np.ndarray, optional
            Transformation matrix for pixel-to-reference coordinate conversion.
            Default is None.
        affine : np.ndarray, optional
            Affine transformation matrix. Default is None.
        branch_degree : int
            The branch degree the ROI is drawn on. Default is None.
        branch_id : int
            The branch id the ROI is drawn on. Default is None.

        Returns
        -------
        None
        """

        self.roi_uuid, self.roi_uuid_uint64 = self.generate_roi_uuid()

        self.compartment = start[4]
        self.center_xy = center
        self.rotation_degrees = rotation
        self.size_xy = size
        self.area = size[0] * size[1]
        self.dim_ratio = size[0] / size[1]
        self.z = z
        self.z_ind = zs.index(z)

        self.center_deg = [coord / obj_res for coord in center]
        self.size_deg = [dim / obj_res for dim in size]

        self.start_node = start[:2]
        self.end_node = end[:2]
        self.start_node_deg = [coord / obj_res for coord in start[:2]]
        self.end_node_deg = [coord / obj_res for coord in end[:2]]
        self.start_node_id = start[3]
        self.end_node_id = end[3]

        self.bottom_right = (
            bottom_right if bottom_right else self.find_corners()[3])
        self.bottom_right_deg = [
            coord / obj_res for coord in self.bottom_right]
        self.bottom_left = self.find_corners()[2]
        self.bottom_left_deg = [coord / obj_res for coord in self.bottom_left]
        self.top_right = self.find_corners()[1]
        self.top_right_deg = [coord / obj_res for coord in self.top_right]
        self.top_left = self.find_corners()[0]
        self.top_left_deg = [coord / obj_res for coord in self.top_left]

        self.pixel_resolution_xy = pixel_resolution_xy
        self.pix_um_ratio = pix_um_ratio
        self.pixel_to_ref_transform = np.array(pixel_to_ref)
        self.affine = np.array(affine)

        self.acquisition_line_period = acquisition_line_period
        self.line_scan_period = line_scan_period
        self.rectangle_period = rectangle_period

        self.branch_degree = branch_degree
        self.branch_id = branch_id

    def __getattr__(self, name: str):
        return self.__dict__[f"_{name}"]

    def __setattr__(
            self,
            name: str,
            value):
        self.__dict__[f"_{name}"] = value

    def generate_roi_uuid(self) -> list:
        """
        Generate a unique identifier for the ROI compatible with Scanimage.

        Returns
        -------
        tuple
            A tuple containing a hexadecimal UUID and its scientific notation.
        """
        roi_uuid_hex = ''.join(random.choices('0123456789ABCDEF', k=16))
        roi_uuid_uint64 = int(roi_uuid_hex, 16)
        roi_uuid_str = "{:.9e}".format(roi_uuid_uint64)
        return [roi_uuid_hex, roi_uuid_str]

    def find_corners(self) -> tuple:
        """
        Calculate the coordinates of the rectangle's corners.

        Returns
        -------
        tuple
            A tuple containing the corners in the following order:
            [top_left, top_right, bottom_left, bottom_right]
        """

        deg_rad = math.radians(self.rotation_degrees + 90)
        half_height = self.size_xy[1] / 2
        half_width = self.size_xy[0] / 2
        x_center, y_center = self.center_xy

        # Rotation components
        x_cos = half_width * math.cos(deg_rad)  # dx_w
        y_sin = half_height * math.sin(deg_rad)  # dx_h
        x_sin = half_width * math.sin(deg_rad)  # dy_w
        y_cos = half_height * math.cos(deg_rad)  # dy_h

        # Corners calculation
        x_top_left, y_top_left = (
            x_center + (x_cos + y_sin),
            y_center + (x_sin - y_cos))

        x_top_right, y_top_right = (
            x_center + (y_sin - x_cos),
            y_center - (x_sin + y_cos))

        x_bottom_left, y_bottom_left = (
            x_center - (y_sin - x_cos),
            y_center + (x_sin + y_cos))

        x_bottom_right, y_bottom_right = (
            x_center + (y_cos + x_sin),
            y_center - (y_sin - x_cos))

        return (
            [x_top_left, y_top_left],
            [x_top_right, y_top_right],
            [x_bottom_left, y_bottom_left],
            [x_bottom_right, y_bottom_right])

    def __repr__(self):
        """
        Return a custom string representation of the ROI instance.

        Returns
        -------
        str
            String representation of the ROI instance.
        """

        repr_strings = []

        for key, value in self.__dict__.items():
            key = key.lstrip('_') if key.startswith('_') else key
            repr_strings.append(f"{key} = {value}")

        return "\n(" + "\n".join(repr_strings) + ")\n"

    def to_dict(self) -> dict:
        """
        Serialize the ROI instance to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the ROI instance.
        """

        return {
            key: value
            for key, value in self.__dict__.items()}

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create an ROI instance from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary containing ROI attributes.

        Returns
        -------
        Roi
            ROI instance created from the dictionary.
        """

        obj = cls.__new__(cls)

        for key, value in data.items():
            key = key.lstrip('_') if key.startswith('_') else key
            setattr(obj, key, value)

        return obj
