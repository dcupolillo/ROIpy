""" Created on Mon Nov  6 14:22:55 2023
    @author: dcupolillo """

import flammkuchen as fl
import numpy as np
import matplotlib.pyplot as plt
from ROIpy.analysis.stats import (
    calculate_total_length,
    sholl_analysis, hull_volume)
from ROIpy.analysis.savejson import save_to_json
from ROIpy.core.utils.utils import split_neurite
from ROIpy.core.components import Node, Roi
from ROIpy.core.makeroi.make_roi import convert_to_polygon


class NodeBundle():
    """
    A helper class to wrap a list of nodes and provide additional methods
    for analysis, visualization, and data manipulation.

    Attributes
    ----------
    nodes : list
        A list of `Node` objects representing the neuronal structure.
    """

    def __init__(self, nodes: list) -> None:
        """
        Initialize a NodeBundle instance.

        Parameters
        ----------
        nodes : list
            A list of `Node` objects.

        Returns
        -------
        None
        """
        self.nodes = nodes

        # not necessary since already given to individual nodes
        # self.neurites = self._neurites()

        # max_branch_id = max(
        #     node.branch_id for node in nodes if node.branch_id is not None)

        # # Create a list of empty lists, one for each branch_id
        # branches = [[] for _ in range(max_branch_id)]

        # # Append each node to its corresponding branch list
        # for node in nodes:
        #     if node.branch_id is not None:
        #         branches[node.branch_id - 1].append(node)

        # self.branches = branches

        # branches_degrees = [None] * len(self.neurites)
        # branches_ids = [None] * len(self.neurites)
        # branches_lengths = [None] * len(self.neurites)

        # for n, neurite in enumerate(self.neurites):

        #     branches_degrees[n] = (
        #         list(set([node.branch_degree for node in neurite]))[0])
        #     branches_ids[n] = (
        #         list(set([node.branch_id for node in neurite]))[0])

        #     branches_lengths[n] = calculate_total_length(neurite)

        # self.branches_degrees = branches_degrees
        # self.branches_ids = branches_ids
        # self.branches_lengths = branches_lengths

    def __repr__(self):
        return repr(self.nodes)

    def __iter__(self):
        return iter(self.nodes)

    def __getitem__(
            self,
            index: int):
        return self.nodes[index]

    def __len__(self):
        return len(self.nodes)

    def save_to_h5(self, filename: str) -> None:
        """
        Save the NodeBundle to an HDF5 file.

        Parameters
        ----------
        filename : str
            Path to the HDF5 file where data will be saved.

        Returns
        -------
        None
        """
        data = [node.to_dict() for node in self.nodes]
        fl.save(filename, {'nodes': data})

    @classmethod
    def load_from_h5(cls, filename: str) -> object:
        """
        Load a NodeBundle from an HDF5 file.
        Prevents from computing again for every new instance.

        Parameters
        ----------
        filename : str
            Path to the HDF5 file containing node data.

        Returns
        -------
        object: NodeBundle
            A NodeBundle instance loaded from the file.
        """
        data = fl.load(filename)['nodes']
        nodes = [Node.from_dict(node) for node in data]

        return cls(nodes)

    def get_neurite(self, neurite_index):

        branch = [
            node for node in self.nodes
            if node.branch_id == neurite_index]
        branch_degree = set(node.branch_degree for node in branch).pop()
        branch_id = set(node.branch_id for node in branch).pop()

        return Neurite(
            nodes=branch,
            neurite_index=neurite_index,
            branch_degree=branch_degree,
            branch_id=branch_id,
        )

    def totlen(self) -> float:
        """
        Calculate the total length of the neurites.

        Returns
        -------
        float
            Total length of neurites in micrometers (µm).
        """
        return calculate_total_length(self.nodes)

    def sholl(
        self,
        radius_step: float,
        n_radii: int,
        ax: plt.Axes = None,
        ax_sholl_curve: plt.Axes = None,
        circle_color: str = 'gray',
        circle_linestyle: str = 'dashed',
        circle_linewidth: int or float = 1,
        intersection_color: str = 'blue',
        marker: str = '+',
        size: int or float = 60,
    ) -> plt.Axes:
        """
        Perform 3D Sholl analysis with 2D visualization.

        This method calculates intersections of neurites
        with concentric spheres in 3D space and
        visualizes the results using 2D plots.

        Parameters
        ----------
        radius_step : float
            Distance between concentric spheres (µm).
        n_radii : int
            Number of concentric spheres.
        ax : plt.Axes, optional
            Matplotlib axes for plotting the Sholl analysis. Default is None.
        ax_sholl_curve : plt.Axes, optional
            Matplotlib axes for plotting the Sholl curve. Default is None.
        circle_color : str, optional
            Color of concentric circles in the 2D plot. Default is 'gray'.
        circle_linestyle : str, optional
            Linestyle of concentric circles. Default is 'dashed'.
        circle_linewidth : int or float, optional
            Line width of concentric circles. Default is 1.
        intersection_color : str, optional
            Color of intersection markers. Default is 'blue'.
        marker : str, optional
            Marker style for intersections. Default is '+'.
        size : int or float, optional
            Marker size for intersections. Default is 60.

        Returns
        -------
        plt.Axes
            Matplotlib axes containing the Sholl analysis plot.

        Example
        -------
        >>> fig, ax = plt.subplots()
        >>> fig_curve, ax_curve = plt.subplots()
        >>> sholl_ax = node_bundle.sholl(
                radius_step=10,
                n_radii=20,
                ax=ax,
                ax_sholl_curve=ax_curve,
            )
        """
        return sholl_analysis(
            input_data=self,
            radius_step=radius_step,
            n_radii=n_radii,
            ax=ax,
            ax_sholl_curve=ax_sholl_curve,
            circle_color=circle_color,
            circle_linestyle=circle_linestyle,
            circle_linewidth=circle_linewidth,
            intersection_color=intersection_color,
            marker=marker,
            size=size,
        )

    def hull(
        self,
        show_plot: bool = True,
        ax: plt.Axes = None,
        terminal_point_color: str = 'red',
        linecolor: str = 'blue',
        facecolor: str = 'none',
        linewidth: int or float = 1,
        linestyle: str = '-',
    ) -> float:
        """
        Calculate and optionally plot the convex hull volume
        of terminal points.

        This method wraps the `hull_volume` function, calculating the 3D volume
        of the convex hull formed by terminal points of the neuronal structure.
        A 2D projection of the convex hull can also be plotted.

        Parameters
        ----------
        show_plot : bool, optional
            If True, plots the 2D projection of the convex hull.
            Default is True.
        ax : plt.Axes, optional
            Matplotlib axes to plot on. If None, a new plot is created.
        terminal_point_color : str, optional
            Color of terminal points in the plot. Default is 'red'.
        linecolor : str, optional
            Color of the convex hull edges. Default is 'blue'.
        facecolor : str, optional
            Color of the convex hull area. Default is 'none'.
        linewidth : int | float, optional
            Line width of the convex hull edges. Default is 1.
        linestyle : str, optional
            Line style of the convex hull edges. Default is '-'.

        Returns
        -------
        float
            The volume of the convex hull (in µm³).

        Example
        -------
        >>> fig, ax = plt.subplots()
        >>> volume = node_bundle.hull(show_plot=True, ax=ax)
        >>> print(f"Convex Hull Volume: {volume:.2f} µm³")
        """
        return hull_volume(
            input_data=self.nodes,
            show_plot=show_plot,
            ax=ax,
            terminal_point_color=terminal_point_color,
            linecolor=linecolor,
            facecolor=facecolor,
            linewidth=linewidth,
            linestyle=linestyle,
        )

    def save(
        self,
        json_filename: str,
    ) -> None:
        """
        Save the NodeBundle data to a JSON-formatted file.

        This method serializes the NodeBundle into a JSON file
        for external storage for sharing.
        The JSON file contains the information of all nodes within the
        bundle.

        Parameters
        ----------
        json_filename : str
            Path to the JSON file where data will be saved.

        Returns
        -------
        None

        Example
        -------
        >>> node_bundle.save('output/nodes.json')
        """
        return save_to_json(self, json_filename=json_filename)


class Neurite:
    """
    Representation of a single neurite.

    This class encapsulates the properties and nodes of a single neurite,
    including branch degree, ID, and total length.
    """

    def __init__(
            self,
            nodes: list,
            neurite_index: int,
            branch_degree: int,
            branch_id: int,
    ) -> None:
        """
        Initialize a Neurite instance.

        Parameters
        ----------
        nodes : list
            List of nodes comprising this neurite.
        branch_degree : int
            Degree of the branch to which the neurite belongs.
        branch_id : int
            Unique identifier for the neurite.
        branch_length : float
            Total length of the neurite.
        """
        self.nodes = nodes
        self.neurite_index = neurite_index
        self.branch_degree = branch_degree
        self.branch_id = branch_id

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, index):
        return self.nodes[index]

    def __iter__(self):
        return iter(self.nodes)


class ScanfieldBundle():
    """
    A helper class to wrap a collection of ROI (Region of Interest) objects.

    This class organizes a list of lists of `Roi` objects,
    typically representing
    scanfields across multiple Z-planes, and provides utility methods for
    saving, loading, and calculating properties of the scanfields.

    Attributes
    ----------
    scanfield : list
        A list of lists containing `Roi` objects for each Z-plane.
    """

    def __init__(
            self,
            scanfield: list
    ) -> None:
        """
        Initialize a ScanfieldBundle instance.

        Parameters
        ----------
        scanfield : list
            A list of lists containing `Roi` objects for each Z-plane.

        Returns
        -------
        None
        """

        self.scanfield = scanfield

    def __repr__(self):
        return repr(self.scanfield)

    def __iter__(self):
        return iter(self.scanfield)

    def __getitem__(
            self,
            index: int):
        return self.scanfield[index]

    def __len__(self):
        return len(self.scanfield)

    def save_to_h5(self, filename: str) -> None:
        """
        Save the ScanfieldBundle to an HDF5 file.

        Parameters
        ----------
        filename : str
            The path to the HDF5 file where the scanfields will be saved.

        Returns
        -------
        None
        """

        data = [
            [roi.to_dict() for roi in z_plane]
            for z_plane in self.scanfield]
        fl.save(filename, {'scanfields': data})

    @classmethod
    def load_from_h5(cls, filename: str) -> object:
        """
        Load a ScanfieldBundle from an HDF5 file.
        Prevents from computing again for every new instance.

        Parameters
        ----------
        filename : str
            The path to the HDF5 file containing the scanfields.

        Returns
        -------
        object: ScanfieldBundle
            An instance of the ScanfieldBundle loaded from the file.
        """
        data = fl.load(filename)['scanfields']
        scanfield = [[Roi.from_dict(roi) for roi in z_plane]
                     for z_plane in data]
        return cls(scanfield)

    @property
    def shape(self):
        """
        Get the shape of the ScanfieldBundle.

        Returns
        -------
        tuple
            A tuple containing the number of Z-planes and a list of the number
            of ROIs in each Z-plane.
        """

        return len(self.scanfield), [len(row) for row in self.scanfield]

    @property
    def area(self) -> float:
        """
        Calculate the total area covered by all ROIs in the ScanfieldBundle.

        This method converts ROIs to polygons and accounts for overlapping portions
        by subtracting intersection areas, ensuring non-overlapping area calculation.

        Returns
        -------
        float
            The total non-overlapping area covered by the ROIs.
        """
        total_area = 0
        processed_polygons = []

        for z_plane in self.scanfield:
            for roi in z_plane:
                # Convert the ROI to a polygon
                current_polygon = convert_to_polygon(roi)

                # Add the current polygon's area
                total_area += current_polygon.area

                # Subtract overlapping areas with previously processed polygons
                for processed_polygon in processed_polygons:
                    overlap_area = current_polygon.intersection(
                        processed_polygon).area
                    total_area -= overlap_area

                # Add the current polygon to the processed list
                processed_polygons.append(current_polygon)

        return total_area
