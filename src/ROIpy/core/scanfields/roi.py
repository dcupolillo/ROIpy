from __future__ import annotations
import math
import random
import numpy as np


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
            pixel_to_ref: np.ndarray | None = None,
            affine: np.ndarray | None = None,
            branch_degree: int | None = None,
            branch_id: int | None = None,
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
        self.obj_res = obj_res

        self.compartment = start[4]
        self.center_xy = center
        self.rotation_degrees = rotation
        
        x, y = size
        self.size_xy = size
        
        self.area = x * y
        self.dim_ratio = x / y
        
        self.z = z
        self.z_ind = zs.index(z)

        self.center_deg = self._um_to_deg(center)
        self.size_deg = self._um_to_deg(size)

        self.start_node = start[:2]
        self.end_node = end[:2]
        self.start_node_deg = self._um_to_deg(start[:2])
        self.end_node_deg = self._um_to_deg(end[:2])
        self.start_node_id = start[3]
        self.end_node_id = end[3]

        corners = self.find_corners()

        self.bottom_right = (
            bottom_right if bottom_right else corners[3])
        self.bottom_right_deg = self._um_to_deg(self.bottom_right)
        self.bottom_left = corners[2]
        self.bottom_left_deg = self._um_to_deg(self.bottom_left)
        self.top_right = corners[1]
        self.top_right_deg = self._um_to_deg(self.top_right)
        self.top_left = corners[0]
        self.top_left_deg = self._um_to_deg(self.top_left)

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
        public_key = name.lstrip('_') if name.startswith('_') else name
        if public_key in self.__dict__:
            return self.__dict__[public_key]
        raise AttributeError(name)

    def _um_to_deg(
            self,
            values: list | tuple | np.ndarray
    ) -> list[float]:
        """Convert one or more micrometer coordinates to degrees."""

        return [float(value) / self.obj_res for value in values]

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
            key.lstrip('_'): value
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
