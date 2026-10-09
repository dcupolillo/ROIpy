from __future__ import annotations
import flammkuchen as fl
import matplotlib.pyplot as plt
from ROIpy.analysis.stats import (
    calculate_total_length,
    sholl_analysis, hull_volume)
from ROIpy.analysis.savejson import save_to_json
from ROIpy.core.morphology.node import Node
from ROIpy.core.morphology.neurite import Neurite


class NodeBundle():
    """
    A helper class to encapsulate a collection of nodes representing a neuronal
    structure. This class provides methods for analysis, visualization, and
    data manipulation.

    Attributes
    ----------
    nodes : list
        A list of `Node` objects representing the neuronal structure.
    _branches : list
        A list of lists, where each sublist contains nodes
        belonging to a single branch.
    _branches_ids : list
        A list of unique branch IDs corresponding to each branch.
    _branches_degrees : list
        A list of branch degrees corresponding to each branch.
    _branches_lengths : list
        A list of total lengths (in micrometers) for each branch.
    """

    def __init__(
            self,
            nodes: list,
    ) -> None:
        """
        Initialize a NodeBundle instance.

        Parameters
        ----------
        nodes : list
            A list of `Node` objects representing the neuronal structure.
        metadata : dict
            A dictionary containing metadata associated with the neuronal

        Notes
        -----
        During initialization:
        - The branches are automatically identified and grouped.
        - Branch IDs, degrees, and lengths are computed for each branch.
        """
        self.nodes = nodes

        self._branches_ids = list(
            set([node.branch_id for node in self.nodes]))

        self.n_branches = len(self._branches_ids)

        self._branches = [None] * len(self._branches_ids)
        self._branches_degrees = [None] * len(self._branches_ids)
        self._branches_lengths = [None] * len(self._branches_ids)

        for n, branch_id in enumerate(self._branches_ids):
            branch = [node for node in nodes if node.branch_id == branch_id]
            self._branches[n] = branch
            self._branches_degrees[n] = set(
                node.branch_degree for node in branch).pop()
            self._branches_lengths[n] = calculate_total_length(branch)

    def __repr__(self):
        return repr(self.nodes)

    def __iter__(self):
        return iter(self.nodes)

    def __getitem__(self, index: int):
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
        data = fl.load(filename)
        nodes_list = data['nodes']
        nodes = [Node.from_dict(node) for node in nodes_list]

        return cls(nodes)

    def get_branch(self, branch_id: int) -> object:
        """
        Retrieve a neurite for a specific branch ID.

        Parameters
        ----------
        branch_id : int
            The ID of the branch to retrieve.

        Returns
        -------
        list
            The scanfields for the specified branch ID.
        """
        if branch_id not in self._branches_ids:
            raise IndexError(
                f"Specified branch not in {self._branches_ids}")

        branch = self._branches[branch_id]
        branch_degree = self._branches_degrees[branch_id]
        branch_length = self._branches_lengths[branch_id]

        return Neurite(
            nodes=branch,
            branch_degree=branch_degree,
            branch_id=branch_id,
            branch_length=branch_length,
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
        circle_linewidth: int | float = 1,
        intersection_color: str = 'blue',
        color: str = 'black',
        marker: str = '+',
        size: int | float = 60,
        show_sholl_curve: bool = True,
        show_intersections: bool = True,
        linewidth: int | float = 1,
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
        circle_linewidth : int | float, optional
            Line width of concentric circles. Default is 1.
        intersection_color : str, optional
            Color of intersection markers. Default is 'blue'.
        color : str, optional
            Color of the morphology onject. Default is 'black'.
        marker : str, optional
            Marker style for intersections. Default is '+'.
        size : int | float, optional
            Marker size for intersections. Default is 60.
        show_sholl_curve : bool, optional
            If True, shows the Sholl curve. Default is True.
        show_intersections : bool, optional
            If True, shows intersection markers. Default is True.
        linewidth : int | float, optional
            Line width of the morphology object. Default is 1.

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
            color=color,
            marker=marker,
            size=size,
            show_sholl_curve=show_sholl_curve,
            show_intersections=show_intersections,
            linewidth=linewidth
        )

    def hull(
        self,
        show_plot: bool = True,
        ax: plt.Axes = None,
        terminal_point_color: str = 'red',
        linecolor: str = 'blue',
        facecolor: str = 'none',
        linewidth: int | float = 1,
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
