from __future__ import annotations
import numpy as np


class Node:
    """
    Representation of an individual node in a neuronal morphology.

    This class encapsulates the attributes and transformations
    associated with a single node within a neuronal structure,
    including positional information, type classification
    and connections to parent/child nodes.

    Attributes
    ----------
    TYPE_MAPPING : dict
        Maps integer type codes (from .swc files)
        to descriptive compartment names.
    """

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
        _type: int | str,
        x: float,
        y: float,
        z_ind: int,
        zs: list[float],
        radius: float,
        parent_id: int,
        matrix: np.ndarray,
        voxel_separation_x: float,
        voxel_separation_y: float,
        voxel_separation_z: float,
    ) -> None:
        """
        Initialize a Node instance.

        Coordinate Systems and Spatial Transformations

        SWC/SWC+ specifies that node coordinates (X, Y, Z) are expressed in micrometers (µm).
        (see: https://neuroinformatics.nl/swcPlus/).

        In this implementation, node coordinates originate in image pixel space and are mapped
        into the ScanImage reference frame (true field-of-view space) as follows:

        1) Node coordinates are converted to pixel coordinates by applying voxel separation factors
            (voxel_separation_x, voxel_separation_y, voxel_separation_z) to account for
            the physical size of each pixel in the acquisition.

        2) pixelToRefTransform (retrieved from ScanImage metadata) is applied to convert pixel coordinates
            into reference coordinates (typically scan angle units, e.g., degrees).
            This affine transform encodes pixel scaling, rotation, and translation into the
            acquisition reference frame.

        Reference coordinates are also converted from scan angle units to micrometers
        using the linear objective calibration factor (obj_res, retrieved from ScanImage metadata).

        This procedure ensures that node coordinates are expressed in the same physical
        reference space as the acquisition system, enabling geometrically correct
        morphometric measurements (e.g., branch length, path length, and spatial density analyses)
        as well as exact placing of node-aligned ROI during subsequent Scanfield generation.

        Z is not considered here as the volume is treated as a stack of discrete 2D planes,
        and each node's Z position is determined by the index of the plane (z_ind)
        and the list of scanned Z positions (zs).
        
        Parameters
        ----------
        obj_res : float
            Objective resolution (conversion factor for coordinates degree -> µm).
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
        zs : list[float]
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
        voxel_separation_z : float
            Voxel-to-micrometer conversion factor along Z.
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

        self.id = int(_id)
        self.type = self.get_type(int(_type))
        self.obj_res = obj_res
        self.zs = zs
        self.matrix = matrix
        self.voxel_separation_x = voxel_separation_x
        self.voxel_separation_y = voxel_separation_y
        self.voxel_separation_z = voxel_separation_z
        self.radius = float(radius)
        self.parent_id = int(parent_id)

        x, y = float(x), float(y)

        # Coordinates in pixel space, degrees, and micrometers FOV space
        self.x_pix, self.y_pix = self._um_to_pixels(x, y)
        self.x_deg, self.y_deg = self._pixels_to_deg(self.x_pix, self.y_pix)
        self.x, self.y = self._deg_to_um(self.x_deg, self.y_deg)

        if zs is not None:
            self.z = float(zs[int(float(z_ind))])
        else:
            self.z = float(z_ind)

        self.z_ind = float(z_ind)

        # Initialize additional attributes with default values
        self.is_fork = None
        self.children = []
        self.branch_degree = None
        self.branch_id = None
        self.has_spine = None
        self.spine_id = None

    def _um_to_pixels(
            self,
            x_um: float,
            y_um: float,
    ) -> tuple:
        """
        Convert coordinates from micrometers to pixel space.
        
        Parameters
        ----------
        x_um : float
            X-coordinate in micrometers.
        y_um : float
            Y-coordinate in micrometers.
        Returns
        -------
        tuple
            (x_pix, y_pix) coordinates in pixel space."""
        
        return (
            x_um / self.voxel_separation_x,
            y_um / self.voxel_separation_y,
        )
    
    def _pixels_to_deg(
            self,
            x_pix: float,
            y_pix: float,
    ) -> tuple:
        """
        Convert coordinates from pixel space to FOV degrees
        using the transformation matrix.
        
        Parameters
        ----------
        x_pix : float
            X-coordinate in pixels.
        y_pix : float
            Y-coordinate in pixels.
        Returns
        -------
        tuple
            (x_deg, y_deg) coordinates in degrees."""
        
        if self.matrix is not None:
            transformed_pixel_to_ref = self.transform_coordinates(
                [x_pix,  y_pix], self.matrix)
            return transformed_pixel_to_ref[0], transformed_pixel_to_ref[1]
        else:
            return x_pix, y_pix
        
    def _deg_to_um(
            self,
            x_deg: float,
            y_deg: float,
    ) -> tuple:
        """
        Convert coordinates from degrees to micrometers using the objective resolution.
        
        Parameters
        ----------
        x_deg : float
            X-coordinate in degrees.
        y_deg : float
            Y-coordinate in degrees.
        Returns
        -------
        tuple
            (x_um, y_um) coordinates in micrometers."""
        
        if self.obj_res is None:
            return x_deg, y_deg
        
        return x_deg * self.obj_res, y_deg * self.obj_res

    def transform_coordinates(
            self,
            coords: list | tuple,
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

        if len(coords) != 2:
            raise ValueError("coords must contain exactly two values: [x, y]")

        pixel_coords = np.array([coords[0], coords[1], 1.0], dtype=float)
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
        return self.TYPE_MAPPING.get(_type, 'unknown')
    
    def __getattr__(self, name: str) -> any:
        
        public_key = name.lstrip('_') if name.startswith('_') else name
        
        if public_key in self.__dict__:
            return self.__dict__[public_key]
        
        raise AttributeError(name)

    def __repr__(self):
        """
        Return a custom string representation of the Node instance.

        Returns
        -------
        str
            String representation of the Node instance.
        """

        attributes_to_display = [
            'id', 'type',
            'x', 'y', 'z',
            'radius', 'parent_id',
            'is_fork', 'children',
            'branch_degree', 'branch_id',
            'has_spine', 'spine_id']

        repr_strings = [None] * len(attributes_to_display)

        for n, key in enumerate(attributes_to_display):
            value = getattr(self, key, None)
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
            key.lstrip('_'): value
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
