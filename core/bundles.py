""" Created on Mon Nov  6 14:22:55 2023
    @author: dcupolillo """

import flammkuchen as fl
import numpy as np
import matplotlib.pyplot as plt
from ROIpy.analysis.stats import (
    calculate_total_length,
    sholl_analysis, hull_area)
from ROIpy.analysis.savejson import save_to_json
from ROIpy.core.utils.utils import split_neurite
from ROIpy.core.components import Node, Roi


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
    def load_from_h5(cls, filename: str) -> 'NodeBundle':
        """
        Load a NodeBundle from an HDF5 file.

        Parameters
        ----------
        filename : str
            Path to the HDF5 file containing node data.

        Returns
        -------
        NodeBundle
            A NodeBundle instance loaded from the file.
        """
        data = fl.load(filename)['nodes']
        nodes = [Node.from_dict(node) for node in data]

        return cls(nodes)

    @property
    def neurite(self) -> object:
        """
        Split the structure into a Neurite object.

        A neurite is a portion of the dendrite included between:
        - Soma and end-point
        - Fork-point and end-point

        Returns
        -------
        object: Neurites
            A Neurite object with additional functionalities.
        """
        return Neurites(split_neurite(self.nodes))

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

        This method calculates intersections of neurites with concentric spheres
        in 3D space and visualizes the results using 2D plots.

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
            terminal_point_color: str = None,
            linecolor: str = None,
            facecolor: str = None,
            linewidth: int or float = None,
            linestyle: str = None
    ) -> plt.Axes:
        """
        Plots the hull area.

        Parameters
        ----------
        ax : plt.Axes.ax, optional
            If specified, plots within it. The default is None.

        Returns
        -------
        plt.Axes.ax
            Plot of the hull area.

        """

        return hull_area(
            self.nodes,
            show_plot=show_plot,
            ax=ax,
            terminal_point_color=terminal_point_color,
            linecolor=linecolor,
            facecolor=facecolor,
            linewidth=linewidth,
            linestyle=linestyle)

    def save(
            self,
            json_name: str
    ) -> None:
        """
        Save data in a json-formatted file

        Parameters
        ----------
        json_name : str
            Path to file.

        Returns
        -------
        None
        """

        return save_to_json(self,
                            json_name=json_name)


class Neurites():

    def __init__(
            self,
            neurites: NodeBundle
    ) -> None:
        """
        Representation of a NodeBundle class
        divided in neurites

        Parameters
        ----------
        neurites : NodeBundle
            Input structure.

        Returns
        -------
        None

        """

        self.neurites = neurites

        branches_degree = []
        branches_length = []
        for neurite in self.neurites:
            branches_degree.append(
                list(set([node.branch_degree for node in neurite]))[0])
            branches_length.append(calculate_total_length(neurite))

        self.branches_degree = branches_degree
        self.branches_length = branches_length

        unique_degrees = set(self.branches_degree)

        self.cumulative_lengths = [
            sum(length
                for degree, length in zip(
                    self.branches_degree, self.branches_length)
                if degree == d)
            for d in sorted(unique_degrees)
        ]

    def __getitem__(
            self,
            index):
        return self.neurites[index]

    def __len__(self):
        return len(self.neurites)


class ScanfieldBundle():

    def __init__(
            self,
            scanfield: list
    ) -> None:
        """
        Helper class to wrap a list of Rois and provide additional methods.
        Collection of lists of Roi objects.

        Parameters
        ----------
        scanfield : list
            DESCRIPTION.

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
        data = [[roi.to_dict() for roi in z_plane]
                for z_plane in self.scanfield]
        fl.save(filename, {'scanfields': data})

    @classmethod
    def load_from_h5(cls, filename: str) -> 'ScanfieldBundle':
        data = fl.load(filename)['scanfields']
        scanfield = [[Roi.from_dict(roi) for roi in z_plane]
                     for z_plane in data]
        return cls(scanfield)

    @property
    def shape(self):
        """
        Returns the shape of the scanfields as in:
            [n of scanfield, (list of n of Rois)].
        """

        return len(self.scanfield), [len(row) for row in self.scanfield]

    @property
    def area(self) -> float:
        """
        Returns the total area included by multiple Rois
        """

        return sum(rect.area for z in self.scanfield for rect in z)
