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
    Calculate the Euclidean distance between two nodes in the XY plane.

    Parameters
    ----------
    node1 : tuple or list
        First node instance.
    node2 : tuple or list
        Second node instance.

    Returns
    -------
    float
        Distance between the two nodes in the XY plane.

    """

    vector = np.array([node2.x - node1.x, node2.y - node1.y])
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
        ax: plt.Axes = None,
        ax_sholl_curve: plt.Axes = None,
        circle_color: str = None,
        circle_linestyle: str = None,
        circle_linewidth: int or float = None,
        intersection_color: str = None,
        marker: str = 'o',
        size: int or float = None
) -> tuple:
    """
    Perform Sholl analysis to count intersections at different radii.
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
    center_node = [node for node in input_data if node.type == 'soma'][0]

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
            # Initialize a comparator for distance

            first_node_distance = internode_distance(center_node, neurite[0])
            last_node_distance = internode_distance(center_node, neurite[-1])

            if (first_node_distance >= radius and
                    last_node_distance >= radius):
                continue  # Skip the entire neurite

            if last_node_distance < first_node_distance:
                # for neurites that extends toward the soma
                # Reverse the neurite list to consider it as extending backward
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

    for radius, nodes in zip(radii, intersecting_nodes_apical):
        for node in nodes:
            ax.scatter(
                node.x,
                node.y,
                color=intersection_color,
                marker=marker,
                s=size,
                label=('Apical'
                       if radius == radii[0]
                       and nodes.index(node) == 0
                       else ""))

        circle = plt.Circle(
            (center_node.x, center_node.y),
            radius,
            color=circle_color,
            fill=False,
            linestyle=circle_linestyle,
            linewidth=circle_linewidth)
        ax.add_artist(circle)

    for radius, nodes in zip(radii, intersecting_nodes_basal):
        for node in nodes:
            ax.scatter(
                node.x,
                node.y,
                color=intersection_color,
                marker=marker,
                s=size,
                label=('Basal'
                       if radius == radii[0]
                       and nodes.index(node) == 0
                       else ""))

        circle = plt.Circle(
            (center_node.x, center_node.y),
            radius,
            color=circle_color,
            fill=False,
            linestyle=circle_linestyle,
            linewidth=circle_linewidth)
        ax.add_artist(circle)

    ax.set_aspect('equal')
    ax.autoscale()

    if not ax_sholl_curve:
        fig_sholl_curve, ax_sholl_curve = plt.subplots()

    ax_sholl_curve.plot(radii, counts_apical, label='Apical')
    ax_sholl_curve.plot(-radii, counts_basal, label='Basal')
    ax_sholl_curve.legend()

    return np.array(counts_apical), np.array(counts_basal), radii


def hull_area(
        input_data: list,
        show_plot: bool = True,
        ax: plt.Axes = None,
        terminal_point_color: str = 'red',
        linecolor: str = 'blue',
        facecolor: str = 'none',
        linewidth: int or float = 1,
        linestyle: str = '-',
        **kwargs
) -> float:
    """
    Calculate the area of the convex hull formed by a set of points.

    Parameters
    ----------
    input_data : list
        A list of nodes or points.
    plot : bool, optional
        If True, plot the convex hull. Default is True. The default is True.
    ax : plt.Axes.ax, optional
        The axes to plot the convex hull.
        If not provided, a new plot will be created. The default is None.

    Returns
    -------
    float
        The area of the convex hull.

    """

    parent_to_children = {}

    # Populate the parent_to_children dictionary
    for node in input_data:
        parent_id = node.parent_id
        if parent_id is not None:
            if parent_id not in parent_to_children:
                parent_to_children[parent_id] = []
            parent_to_children[parent_id].append(node.id)

    # Identify terminal nodes (nodes that are parents to no other nodes)
    terminal_nodes = [node for node in input_data
                      if node.id not in parent_to_children]

    # Extract x and y coordinates of terminal nodes
    x_terminal = np.array([node.x for node in terminal_nodes])
    y_terminal = np.array([node.y for node in terminal_nodes])

    # Create points for the ConvexHull
    points = np.column_stack((x_terminal, y_terminal))

    # Calculate the ConvexHull
    hull = ConvexHull(points)

    # Get the vertices of the convex hull
    hull_vertices = hull.vertices
    hull_points = points[hull_vertices]

    # Plot the neuron and terminal nodes and the convex hull polygon
    if show_plot:
        if not ax:
            fig, ax = plt.subplots()
        ax.set_aspect('equal')

        for point in hull_points:
            ax.scatter(point[0], point[1], color=terminal_point_color)

        hull_polygon = plt.Polygon(hull_points,
                                   edgecolor=linecolor,
                                   facecolor=facecolor,
                                   linewidth=linewidth,
                                   linestyle=linestyle)
        ax.add_patch(hull_polygon)

    return hull.volume
