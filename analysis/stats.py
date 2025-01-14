""" Created on Mon Aug 28 10:00:25 2023
    @author: dcupolillo """

import numpy as np
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt


def internode_distance(
        node1: object,
        node2: object
) -> float:
    """
    Calculate the Euclidean distance between two nodes in XYZ.

    Parameters
    ----------
    node1 : Node
        First node instance.
    node2 : Node
        Second node instance.

    Returns
    -------
    float
        Distance between the two nodes in the XY plane.

    """

    vector = np.array([
        node2.x - node1.x,
        node2.y - node1.y,
        node2.z - node1.z
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

    total_length = 0.0

    for node in input_data:
        if node.parent_id is not None:
            parent_node = next((n for n in input_data
                                if n.id == node.parent_id), None)
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
        circle_linewidth: int | float,
        intersection_color: str,
        marker: str,
        size: int | float
) -> tuple:
    """
    Perform 3D Sholl analysis to count intersections at different radii.
    This version of the function also generates a graphical representation.

    Parameters
    ----------
    input_data : list
        List of nodes representing the neuron structure.
    center_node : tuple or list
        The central node for which the Sholl analysis is performed.
    radius_step : float
        The step size for increasing the radius.
    n_radii : int
        The number of circles to be analyzed.
    ax : plt.Axes.ax, optional
        The axes to plot the Sholl analysis. The default is None.

    Returns
    -------
    tuple
        A tuple containing a list of intersection counts at different radii,
        and the radii themselves.

    """
    center_node = [
        node for node in input_data if node.type == 'soma'][0]

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

        for neurite in input_data.neurite:

            first_node_distance = internode_distance(center_node, neurite[0])
            last_node_distance = internode_distance(center_node, neurite[-1])

            if (first_node_distance >= radius and
                    last_node_distance >= radius):
                # Skip this neurite if entirely outside the sphere
                continue

            if last_node_distance < first_node_distance:
                # Reverse neurite direction if needed
                neurite = neurite[::-1]

            for n, node in enumerate(neurite):
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

    if not ax:
        fig, ax = plt.subplots()
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
                label=(
                    'Apical'
                    if radius == radii[0]
                    and nodes.index(node) == 0
                    else ""))

    for radius, nodes in zip(radii, intersecting_nodes_basal):
        for node in nodes:
            ax.scatter(
                node.x,
                node.y,
                color=intersection_color,
                marker=marker,
                s=size,
                label=(
                    'Basal'
                    if radius == radii[0]
                    and nodes.index(node) == 0
                    else ""))

    if not ax_sholl_curve:
        fig_sholl_curve, ax_sholl_curve = plt.subplots()

    ax_sholl_curve.plot(radii, counts_apical, label='Apical')
    ax_sholl_curve.plot(-radii, counts_basal, label='Basal')
    ax_sholl_curve.legend()

    return (
        np.array(counts_apical),
        np.array(counts_basal),
        radii)


def hull_volume(
    input_data: list,
    show_plot: bool,
    ax: plt.Axes,
    terminal_point_color: str,
    linecolor: str,
    facecolor: str,
    linewidth: int | float,
    linestyle: str,
    **kwargs,
) -> float:
    """
    Calculate and optionally plot the convex hull volume formed by terminal points.

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
    hull = ConvexHull(points)

    # Plotting (optional, 2D projection in XY plane)
    if show_plot:
        if ax is None:
            fig, ax = plt.subplots()
        ax.set_aspect('equal')

        # Scatter terminal points (projected to XY plane)
        ax.scatter(points[:, 0], points[:, 1],
                   color=terminal_point_color, **kwargs)

        # Draw the convex hull edges in 2D (projected to XY plane)
        hull_polygon = plt.Polygon(
            points[hull.vertices, :2],  # Use only x, y for 2D polygon
            edgecolor=linecolor,
            facecolor=facecolor,
            linewidth=linewidth,
            linestyle=linestyle,
        )
        ax.add_patch(hull_polygon)

    # Return the 3D volume of the convex hull
    return hull.volume
