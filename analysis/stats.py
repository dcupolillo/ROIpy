""" Created on Mon Aug 28 10:00:25 2023
    @author: dcupolillo """

import numpy as np
from scipy.spatial import ConvexHull, QhullError
import matplotlib.pyplot as plt
from ROIpy.plot.plot import skeleton


def internode_distance(
    node1: object,
    node2: object
) -> float:
    """
    Calculate the Euclidean distance between two nodes in 3D space.

    Parameters
    ----------
    node1 : object
        First node instance with attributes `x`, `y`, and `z`.
    node2 : object
        Second node instance with attributes `x`, `y`, and `z`.

    Returns
    -------
    float
        Euclidean distance between the two nodes in 3D space.
    """
    if isinstance(node1, dict) and isinstance(node2, dict):
        x1, y1, z1 = node1.get('_x'), node1.get('_y'), node1.get('_z')
        x2, y2, z2 = node2.get('_x'), node2.get('_y'), node2.get('_z')

    elif hasattr(node1, '_x') and hasattr(node2, '_x'):
        x1, y1, z1 = node1._x, node1._y, node1._z
        x2, y2, z2 = node2._x, node2._y, node2._z

    vector = np.array([
        x2 - x1,
        y2 - y1,
        z2 - z1
    ])
    return np.linalg.norm(vector)


def internode_distance_along_path(
        neurite: list
) -> float:
    """
    Calculate the distance between the first and last nodes
    along the path of the neurite.

    Parameters
    ----------
    neurite : list
        List of nodes representing a neurite segment.

    Returns
    -------
    float
        Distance between the first and last nodes
        along the path of the neurite.
    """
    total_distance = 0.0

    for i in range(len(neurite) - 1):
        # Calculate distance between consecutive nodes and accumulate
        total_distance += np.linalg.norm(
            np.array([neurite[i+1].x - neurite[i].x,
                      neurite[i+1].y - neurite[i].y]))

    return total_distance


def calculate_total_length(
        input_data: list
) -> float:
    """
    Calculate the cumulative length of all neurites in the morphology.

    Parameters
    ----------
    input_data : list
        List of node instances representing the morphology.

    Returns
    -------
    float
        Total length of neurites.

    """
    if not isinstance(input_data, list):
        raise TypeError(
            "Input data must be a list of node instances."
            f" Got {type(input_data)} instead.")
    
    if not all(isinstance(node, (dict, object)) for node in input_data):
        raise TypeError(
            "All elements in input_data must be node instances or dictionaries.")

    total_length = 0.0

    for node in input_data:

        if isinstance(node, dict):
            parent_id = node.get('_parent_id', None)
        elif hasattr(node, '_parent_id'):
            parent_id = node._parent_id
        else:
            parent_id = getattr(node, '_parent_id', None)

        if parent_id is not None:
            try:
                parent_node = next(
                    (n for n in input_data if n["_id"] == parent_id), None)
            except TypeError:
                parent_node = next(
                    (n for n in input_data if n._id == parent_id), None)

            if parent_node is not None:
                distance = internode_distance(parent_node, node)
                total_length += distance

    return total_length


def sholl_analysis(
    input_data: object,
    radius_step: float,
    n_radii: int,
    ax: plt.Axes,
    ax_sholl_curve: plt.Axes,
    circle_color: str,
    circle_linestyle: str,
    circle_linewidth: int or float,
    intersection_color: str,
    color: str,
    marker: str,
    size: int or float,
    show_sholl_curve: bool,
    show_intersections: bool,
    linewidth: int or float,
) -> tuple:
    """
    Perform Sholl analysis with 3D calculations and 2D representation.

    Parameters
    ----------
    input_data : list
        List of nodes representing the neuron structure.
    radius_step : float
        The step size for increasing the radius.
    n_radii : int
        The number of spheres (radii) to analyze.
    ax : plt.Axes, optional
        The axes to plot the Sholl analysis. Default is None.
    ax_sholl_curve : plt.Axes, optional
        The axes to plot the Sholl curve. Default is None.
    circle_color : str, optional
        Color of the concentric circles. Default is None.
    circle_linestyle : str, optional
        Linestyle of the concentric circles. Default is None.
    circle_linewidth : int or float, optional
        Line width of the concentric circles. Default is None.
    intersection_color : str, optional
        Color of the intersection markers. Default is None.
    color : str, optional
        Color of the morphology onject. Default is 'black'.
    marker : str, optional
        Marker style for intersections. Default is 'o'.
    size : int or float, optional
        Marker size for intersections. Default is None.
    show_sholl_curve : bool, optional
        If True, shows the Sholl curve. Default is True.
    show_intersections : bool, optional
        If True, shows the intersections. Default is True.
    linewidth : int or float, optional
        Line width of the morphology. Default is 1.

    Returns
    -------
    tuple
        A tuple containing:
        - `counts_apical` (array): Intersection counts for apical dendrites.
        - `counts_basal` (array): Intersection counts for basal dendrites.
        - `radii` (array): Radii of concentric spheres.
    """
    try:
        center_node = [
            node for node in input_data if node.type == 'soma'][0]
    except IndexError:
        center_node = min(
            (node for node in input_data),
            key=lambda node: node.id,
            default=None
        )

    branch_list = list(set([node._branch_id for node in input_data]))

    # Define radii for concentric spheres
    max_radius = radius_step * n_radii
    radii = np.arange(0, max_radius + radius_step, radius_step)

    counts_apical = []
    counts_basal = []
    intersecting_nodes_apical = []
    intersecting_nodes_basal = []

    for radius in radii:
        intersection_count_apical = 0
        intersection_count_basal = 0
        intersecting_nodes_per_radius_apical = []
        intersecting_nodes_per_radius_basal = []

        for neurite_n in branch_list:
            neurite = input_data.get_branch(neurite_n)

            # Calculate 3D distance
            first_node_distance = internode_distance(
                center_node, neurite[0])
            last_node_distance = internode_distance(
                center_node, neurite[-1])

            if first_node_distance >= radius and last_node_distance >= radius:
                continue  # Skip this neurite if entirely outside the sphere

            if last_node_distance < first_node_distance:
                neurite = neurite[::-1]  # Reverse neurite direction if needed

            for node in neurite:
                distance = internode_distance(center_node, node)
                if distance >= radius:
                    if node.type == 'apical dendrite':
                        intersection_count_apical += 1
                        intersecting_nodes_per_radius_apical.append(node)
                    elif node.type == 'basal dendrite':
                        intersection_count_basal += 1
                        intersecting_nodes_per_radius_basal.append(node)
                    break

        counts_apical.append(intersection_count_apical)
        counts_basal.append(intersection_count_basal)
        intersecting_nodes_apical.append(intersecting_nodes_per_radius_apical)
        intersecting_nodes_basal.append(intersecting_nodes_per_radius_basal)

    if show_intersections:

        # Plotting (2D representation)
        if not ax:
            _, ax = plt.subplots()
        ax.set_aspect('equal')
        ax.autoscale()

        for radius in radii:
            circle = plt.Circle(
                (center_node.x, center_node.y),
                radius,
                color=circle_color,
                fill=False,
                linestyle=circle_linestyle,
                linewidth=circle_linewidth,
            )
            ax.add_artist(circle)

        for radius, nodes in zip(radii, intersecting_nodes_apical):
            for node in nodes:
                ax.scatter(
                    node.x,
                    node.y,
                    color=intersection_color,
                    marker=marker,
                    s=size,
                    label=('Apical' if radius ==
                        radii[0] and nodes.index(node) == 0 else ""),
                    zorder=2,
                )

        for radius, nodes in zip(radii, intersecting_nodes_basal):
            for node in nodes:
                ax.scatter(
                    node.x,
                    node.y,
                    color=intersection_color,
                    marker=marker,
                    s=size,
                    label=('Basal' if radius ==
                        radii[0] and nodes.index(node) == 0 else ""),
                    zorder=2,
                )          

    if show_sholl_curve:
        if not ax_sholl_curve:
            _, ax_sholl_curve = plt.subplots()

        ax_sholl_curve.plot(radii, counts_apical, label='Apical')
        ax_sholl_curve.plot(-radii, counts_basal, label='Basal')
        ax_sholl_curve.legend()

    return np.array(counts_apical), np.array(counts_basal), radii


def hull_volume(
    input_data: list,
    show_plot: bool,
    ax: plt.Axes,
    terminal_point_color: str,
    linecolor: str,
    facecolor: str,
    linewidth: int or float,
    linestyle: str,
    **kwargs,
) -> float:
    """
    Calculate and optionally plot the convex hull volume
    formed by terminal points.

    Parameters
    ----------
    input_data : list
        List of nodes representing the neuronal structure.
    show_plot : bool, optional
        If True, plots the convex hull. Default is True.
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
        The volume of the convex hull.

    Example
    -------
    >>> volume = hull_volume(nodes, show_plot=True)
    >>> print(f"Convex Hull Volume: {volume:.2f} µm³")
    """
    # Build parent-to-children mapping
    parent_to_children = {}
    for node in input_data:
        if node.parent_id is not None:
            parent_to_children.setdefault(node.parent_id, []).append(node.id)

    # Identify terminal nodes (no children)
    terminal_nodes = [
        node for node in input_data if node.id not in parent_to_children]

    # Extract x, y, and z coordinates of terminal nodes
    x_terminal = np.array([node.x for node in terminal_nodes])
    y_terminal = np.array([node.y for node in terminal_nodes])
    z_terminal = np.array([node.z for node in terminal_nodes])

    # Points for convex hull
    points = np.column_stack((x_terminal, y_terminal, z_terminal))

    points_2d = points[:, :2]

    # Check if there are at least 4 non-coplanar points
    if len(points) < 4:
        raise ValueError(
            f"Not enough points ({len(points)}) to compute a 3D convex hull. "
            "At least 4 non-coplanar points are required.")

    try:
        hull = ConvexHull(points)
    except QhullError as e:
        raise ValueError(
            "Convex hull computation failed due to coplanarity "
            "or insufficient points.") from e

    # Plotting (optional, 2D projection in XY plane)
    if not show_plot:
        return hull.volume

    if ax is None:
        fig, ax = plt.subplots()
    ax.set_aspect('equal')

    # Scatter terminal points (projected to XY plane)
    ax.scatter(
        points[:, 0],
        points[:, 1],
        color=terminal_point_color,
        **kwargs)

    hull_2d = ConvexHull(points_2d)  # 2d for representation

    for simplex in hull_2d.simplices:
        ax.plot(
            points_2d[simplex, 0],
            points_2d[simplex, 1],
            linewidth=linewidth,
            linestyle=linestyle,
            color=linecolor)

    ax.fill(
        points_2d[hull_2d.vertices, 0],
        points_2d[hull_2d.vertices, 1],
        color=facecolor,
        alpha=0.3)

    return hull.volume
