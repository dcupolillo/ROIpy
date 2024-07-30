""" Created on Mon Aug 14 09:38:53 2023
    @author: dcupolillo """

import math
import numpy as np
import matplotlib.path as mpath
from statistics import mode
from shapely.geometry import Polygon
from ROIpy.core.components import Roi


def make_roi(
        class_var: object,
        input_data: list
) -> list:
    """
    Series of functions executed in order to generate the final Rois.

    Parameters
    ----------
    class_var : Scanfield
        class itself.
    input_data : list
        the compartment to be subdivided in Rois.

    Returns
    -------
    list
        nested list of Roi objects.

    """

    # Split the nodes in consecutive coplanar groups
    grouped_z = group_z(input_data)
    segments = split_consecutive(grouped_z)

    # Calculates segments start nodes and end nodes
    close, far = distance_node(class_var, segments)

    # Finds initial group of rectangles
    rectangles = find_rectangles(class_var, close, far)

    # Threshold them based on dimension ratio
    included, excluded = remove_short_rectangles(class_var, rectangles)

    # Merge the excluded ones to make bigger rectangles
    excluded_merged = merge_neighbors(class_var, input_data, excluded)
    reintegrated_rectangles = reintegrate(
        class_var, included, excluded_merged)

    # Widens and elongates rectangles
    widened_rectangles = correct_curvatures(
        class_var, input_data, reintegrated_rectangles)
    elongated_rectangles = elongate_rectangles(class_var, widened_rectangles)

    # Remove rectangles whose area is covered by other rectangles
    non_overlapped_rectangles = remove_overlapping(
        class_var, elongated_rectangles)

    # Remove rectangles within a certain radius from soma
    filtered_rectangles = remove_rect_within_radius(
        class_var, non_overlapped_rectangles)

    # Populate the rectangles with pixels giving them a certain dimension
    roi_pixel = roi_populate_pixels(class_var, filtered_rectangles)

    # Add transformation matrices
    transform_added_rectangles = calculate_transform(class_var, roi_pixel)

    return transform_added_rectangles


def group_z(
        input_data: list
) -> list:
    """
    Groups nodes of a morphology object according to their z plane.

    Parameters
    ----------
    input_data : list
        List of Node objects representing the morphology..

    Returns
    -------
    list
        Nested list of node groups, each group representing a z plane.

    """

    grouped_nodes = {}

    # Create a dictionary with all the z values as keys
    # and empty lists as elements
    for node in input_data:
        if node.z not in grouped_nodes:
            grouped_nodes[node.z] = []

        # Fills the list elements with nodes corresponding to that z
        grouped_nodes[node.z].append(node)

    # Sort the groups based on the z plane values
    # in descending order (Z planes are negative)
    sorted_grouped_nodes = sorted(grouped_nodes.items(),
                                  key=lambda x: x[0],
                                  reverse=True)

    return [group for _, group in sorted_grouped_nodes]


def split_consecutive(
        input_data: list
) -> list:
    """
    Groups coplanar nodes into consecutive node segments.

    Parameters
    ----------
    input_data : list
        2D list of nodes, grouped according to Z plane - group_z.

    Returns
    -------
    list
        Nested list containing consecutive segments within each Z plane..

    """

    # Sort input_data based on z plane of the first node in each group
    # in descending order (z planes are negative)
    input_data_sorted = sorted(
        input_data,
        key=lambda node_group: node_group[0].z,
        reverse=True)

    consecutive_segments = []

    for coplanar_nodes in input_data_sorted:

        current_group = []
        consecutive_nodes = []

        # Nodes within the same z plane
        for node in coplanar_nodes:
            if not node:
                continue

            if node.type == 'soma':
                continue

            # Extends current_group if nodes are consecutive
            if not current_group or node.parent_id == current_group[-1].id:
                current_group.append(node)
            else:
                # If not consecutive, store the extended group,
                # and starts a new current_group
                if current_group:
                    consecutive_nodes.append(current_group)
                current_group = [node]

        # Appends the last group
        if current_group:
            consecutive_nodes.append(current_group)

        # Filters out groups composed by single nodes
        consecutive_nodes = [g for g in consecutive_nodes if len(g) > 1]

        consecutive_segments.append(consecutive_nodes)

    return consecutive_segments


def distance_node(
        class_var: object,
        input_data: list
) -> (list, list):
    """
    Calculate the closest and farthest points
    within each segment of consecutive nodes
    from a specified soma.

    Parameters
    ----------
    class_var : TYPE
        The class object containing relevant parameters..
    input_data : list
        Nested list of z-sorted consecutive segments.

    Returns
    -------
    closest_points : list
        Nested list of closest points within each segment.
    farthest_points : list
        Nested list of farthest points within each segment.

    """

    soma = class_var.soma

    # Pre-allocate empty list
    closest_points = [None] * len(class_var.zs)
    farthest_points = [None] * len(class_var.zs)

    for z, z_plane_segments in enumerate(input_data):
        z_closest_list = []
        z_farthest_list = []

        for segment in z_plane_segments:
            closest_node = None
            closest_dist = float('inf')
            farthest_node = None
            farthest_dist = 0

            for node in segment:
                dist = np.sqrt((node.x - soma.x) ** 2 + (node.y - soma.y) ** 2)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_node = [node.x, node.y,
                                    node.z, node.id,
                                    node.type]
                if dist > farthest_dist:
                    farthest_dist = dist
                    farthest_node = [node.x, node.y,
                                     node.z, node.id,
                                     node.type]

            if closest_node is not None:
                z_closest_list.append(closest_node)

            if farthest_node is not None:
                z_farthest_list.append(farthest_node)

        closest_points[z] = z_closest_list
        farthest_points[z] = z_farthest_list

    # In case z planes are empty of nodes
    closest_points = [points for points in closest_points
                      if points is not None]
    farthest_points = [points for points in farthest_points
                       if points is not None]

    return closest_points, farthest_points


def find_rectangles(
        class_var: object,
        close: list,
        far: list
) -> list:
    """
    Create rectangular Roi objects based on close and far points.

    Parameters
    ----------
    class_var : TYPE
        Class containing objective resolution and zs.
    close : list
        Nested list of closest points.
    far : list
        Nested list of farthest points.

    Returns
    -------
    list
        Nested list of rectangular Roi objects.

    """

    objective_resolution = class_var.objective_resolution
    zs = class_var.zs

    # Pre-allocate empty list of rectangles
    rectangles = [None] * len(close)

    for z_plane, (close_z_plane, far_z_plane) in enumerate(zip(close, far)):

        z_plane_rectangles = []

        for close_node, far_node in zip(close_z_plane, far_z_plane):

            if not close_node and far_node:
                continue

            center = [(close_node[0] + far_node[0]) / 2,
                      (close_node[1] + far_node[1]) / 2]
            dx = far_node[0] - close_node[0]
            dy = far_node[1] - close_node[1]
            rotation = np.degrees(np.arctan2(dy, dx))
            height = np.sqrt(dx ** 2 + dy ** 2)
            width = 10
            size = [width, height]
            x = close_node[0] + width / 2 * np.sin(np.radians(rotation))
            y = close_node[1] - width / 2 * np.cos(np.radians(rotation))
            bottom_right = [x, y]
            z = close_node[2]

            # Create a Roi object
            rectangle = Roi(
                objective_resolution,
                zs,
                center,
                rotation,
                size,
                z,
                close_node,
                far_node,
                bottom_right,
                pixel_resolution_xy=None,
                pix_um_ratio=None)

            z_plane_rectangles.append(rectangle)

        rectangles[z_plane] = z_plane_rectangles

    return rectangles


def remove_short_rectangles(
        class_var: object,
        rectangles: list
) -> (list, list):
    """
    Removes rectangles based on the width-to-height ratio.

    Parameters
    ----------
    class_var : TYPE
        The class object containing relevant parameters.
    rectangles : list
        List of rectangles grouped by z-plane.

    Returns
    -------
    included_rectangles : list
        Rectangles with width-to-height ratio < dim_ratio_threshold.
    excluded_rectangles : list
        Rectangles with width-to-height ratio >= dim_ratio_threshold.

    """

    dim_ratio_threshold = class_var.dim_ratio_threshold

    included_rectangles = []
    excluded_rectangles = []

    for z_plane_rectangles in rectangles:

        included_z_plane_rectangles = [
            rect for rect in z_plane_rectangles
            if rect.dim_ratio
            < dim_ratio_threshold]
        excluded_z_plane_rectangles = [
            rect for rect in z_plane_rectangles
            if rect.dim_ratio
            >= dim_ratio_threshold]

        included_rectangles.append(included_z_plane_rectangles)
        excluded_rectangles.append(excluded_z_plane_rectangles)

    return included_rectangles, excluded_rectangles


def merge_neighbors(
        class_var: object,
        input_data: list,
        excluded_rectangles: list
) -> list:
    """
    Merges excluded consecutive rectangles into a single rectangle

    Parameters
    ----------
    class_var : TYPE
        The class object containing relevant parameters.
    input_data : list
        List of Node objects.
    excluded_rectangles : list
        List of excluded rectangles grouped by z-plane.

    Returns
    -------
    list
        List of merged rectangles.

    """

    objective_resolution = class_var.objective_resolution
    zs = class_var.zs

    # Sort excluded roi based on start node
    sorted_roi = sorted([rect for z in excluded_rectangles for rect in z],
                        key=lambda x: x.start_node_id)

    children_dict = {node.id: node.children for node in input_data}

    # Elongate a train if rectangles are consecutive
    consecutive_rectangles = []
    train = []

    for i, rect in enumerate(sorted_roi):
        # Check if it's the first rectangle
        # or consecutive to the last rectangle in the train
        if (i == 0 or
            rect.start_node_id == train[-1].end_node_id + 1 and
                rect.start_node_id in children_dict[train[-1].end_node_id]):
            # Add the rectangle to the current train
            train.append(rect)
        else:
            # Append the current train to consecutive_rectangles
            if len(train) > 1:
                consecutive_rectangles.append(train)
            # Start a new train with the current rectangle
            train = [rect]

    # After the loop, check if the last train needs to be added
    if len(train) > 1:
        consecutive_rectangles.append(train)

    # Create a new Roi object for each train
    merged_rectangles = []

    for train in consecutive_rectangles:
        if not train:
            continue

        # Start of the first rectangle
        close_node = train[0].start_node
        # End of the last rectangle
        far_node = train[-1].end_node
        close_node.append(train[0].z)
        far_node.append(train[-1].z)
        close_node.append(train[0].start_node_id)
        far_node.append(train[-1].end_node_id)
        close_node.append(train[0].compartment)
        far_node.append(train[-1].compartment)
        dx = far_node[0] - close_node[0]
        dy = far_node[1] - close_node[1]
        rotation = np.degrees(np.arctan2(dy, dx))
        height = np.sqrt(dx ** 2 + dy ** 2)
        width = 10
        size = [width, height]
        center = [(close_node[0] + far_node[0]) / 2,
                  (close_node[1] + far_node[1]) / 2]
        x = close_node[0] + width / 2 * np.sin(np.radians(rotation))
        y = close_node[1] - width / 2 * np.cos(np.radians(rotation))
        bottom_right = [x, y]

        # Calculate the Mode (most represented value)
        # for z values among merged rectangles
        z_values = [rect.z_ind for rect in train]
        z_most_common = int(mode(z_values))

        # Create a Roi object
        new_rect = Roi(objective_resolution,
                       zs, center, rotation, size, zs[z_most_common],
                       close_node, far_node, bottom_right,
                       pixel_resolution_xy=None, pix_um_ratio=None)

        merged_rectangles.append(new_rect)

    return merged_rectangles


def reintegrate(
        class_var: object,
        previously_included: list,
        rects_to_reintegrate: list
) -> list:
    """
    Reintegrates a set of rectangles into a previously
    generated rectangle list.

    Parameters
    ----------
    class_var : TYPE
        The class object containing relevant parameters.
    previously_included : list
        List of included rectangles grouped by z-plane.
    rects_to_reintegrate : list
        List of rectangles to reintegrate.

    Returns
    -------
    list
        Updated list of included rectangles.

    """

    # Create a copy of the previously_included list
    # to avoid modifying the original list
    copy_included = [plane[:] for plane in previously_included]

    # Initialize empty dictionary where to store lists of Rois under z keys
    rois_by_z = {}

    for z_plane in copy_included:
        for rect in z_plane:
            z_value = rect.z

            if z_value in rois_by_z:
                rois_by_z[z_value].append(rect)
            else:
                rois_by_z[z_value] = [rect]

    for rect in rects_to_reintegrate:
        z_value = rect.z

        if z_value in rois_by_z:
            rois_by_z[z_value].append(rect)
        else:
            rois_by_z[z_value] = [rect]

    result = list(rois_by_z.values())

    return result


def nodes_outside(
        nodes: list,
        rect: Roi
) -> list:
    """
    Determines the nodes outside the boundaries of a given rectangle.
    Helper function to correct_curvatures to identify nodes that are
    outside the boundaries of rectangles, which aids in correcting curvatures.

    Parameters
    ----------
    nodes : list
        List of nodes to check.
    rect : Roi
        The rectangle to compare against.

    Returns
    -------
    list
        List of nodes that are outside the rectangle's boundaries.

    """

    start_id = rect.start_node_id
    end_id = rect.end_node_id
    width = rect.size_xy[0]
    height = rect.size_xy[1]
    cx, cy = rect.center_xy
    rotation = np.radians(rect.rotation_degrees)
    half_width = width / 2
    half_height = height / 2
    cos = np.cos(rotation)
    sin = np.sin(rotation)
    top_right = [cx + half_height * cos - half_width * sin,
                 cy + half_height * sin + half_width * cos]
    top_left = [cx - half_height * cos - half_width * sin,
                cy - half_height * sin + half_width * cos]
    bottom_left = [cx + half_height * cos + half_width * sin,
                   cy + half_height * sin - half_width * cos]
    bottom_right = rect.bottom_right
    corners = [bottom_left, bottom_right, top_left, top_right]  # order matters
    path = mpath.Path(corners)

    outside_nodes = []

    for node in nodes:
        if node.id not in [start_id, end_id]:
            if not path.contains_point((node.x, node.y)):
                outside_nodes.append(node)

    return outside_nodes


def correct_curvatures(
        class_var: object,
        input_data: list,
        rectangles: list
) -> list:
    """
    Corrects curvatures in a set of rectangles within
    different z-planes of an input structure.

    Parameters
    ----------
    class_var : TYPE
        The class object containing relevant parameters.
    input_data : list
        List of all nodes in the input structure.
    rectangles : list
        List of subdivided rectangles by z-plane.

    Returns
    -------
    list
        List of corrected rectangles.

    """

    objective_resolution = class_var.objective_resolution
    zs = class_var.zs

    # Pre-allocate empty list of z planes
    new_rectangles = [None] * len(rectangles)

    # Divide input_data into the different Z planes
    grouped_z = group_z(input_data)

    for z, (z_nodes, z_plane) in enumerate(zip(grouped_z, rectangles)):

        if not z_plane:
            continue

        new_rects = []
        outside_nodes = []
        included_segment = []

        for rect in z_plane:
            start = rect.start_node_id
            end = rect.end_node_id
            included_segment = [node for node in z_nodes
                                if node.id >= start and node.id <= end]
            outside_nodes = nodes_outside(included_segment, rect)

            if outside_nodes:
                close_node = rect.start_node + \
                    [rect.z, rect.start_node_id, rect.compartment]
                far_node = rect.end_node + \
                    [rect.z, rect.end_node_id, rect.compartment]
                dx = far_node[0] - close_node[0]
                dy = far_node[1] - close_node[1]
                rotation = np.degrees(np.arctan2(dy, dx))
                distances = []

                for node in outside_nodes:
                    numerator = abs(
                        dy * node.x - dx * node.y + far_node[0] *
                        close_node[1] - far_node[1] * close_node[0])
                    denominator = np.sqrt(dy ** 2 + dx ** 2)
                    perpendicular_dist = numerator / denominator
                    distances.append(perpendicular_dist)

                width = rect.size_xy[0] + max(distances) * 2
                height = np.sqrt(dx ** 2 + dy ** 2)
                size = [width, height]
                center = [(close_node[0] + far_node[0]) / 2,
                          (close_node[1] + far_node[1]) / 2]
                x = close_node[0] + width / 2 * np.sin(np.radians(
                    rotation))
                y = close_node[1] - width / 2 * np.cos(np.radians(
                    rotation))
                bottom_right = [x, y]

                # Create a new enlarged Roi object
                widened_rect = Roi(objective_resolution,
                                   zs, center, rotation, size, rect.z,
                                   close_node, far_node, bottom_right,
                                   pixel_resolution_xy=None,
                                   pix_um_ratio=None)

                new_rects.append(widened_rect)

            else:
                # No correction needed, append original rectangle
                new_rects.append(rect)

            new_rectangles[z] = new_rects

    return new_rectangles


def elongate_rectangles(
        class_var: object,
        rectangles: list
) -> list:
    """
    Elongates rectangles in the long-direction
    for each z-plane by a specified factor.

    Parameters
    ----------
    class_var : TYPE
        The class object containing relevant parameters.
    rectangles : list
        Rectangles to elongate.

    Returns
    -------
    list
        List of elongated rectangles.

    """

    objective_resolution = class_var.objective_resolution
    zs = class_var.zs
    elongating_factor = class_var.elongating_factor

    # Pre-allocate empty list of z planes
    elongated_rectangles = [None] * len(rectangles)

    for z, z_plane_rectangles in enumerate(rectangles):
        if not z_plane_rectangles:
            continue

        elongated_z_plane_rectangles = []

        for rect in z_plane_rectangles:
            close_node = rect.start_node + \
                [rect.z, rect.start_node_id, rect.compartment]
            far_node = rect.end_node + \
                [rect.z, rect.end_node_id, rect.compartment]
            dx, dy = (far_node[0] - close_node[0],
                      far_node[1] - close_node[1])
            rotation = np.degrees(np.arctan2(dy, dx))
            width, height = (rect.size_xy[0],
                             rect.size_xy[1] * elongating_factor)
            size = [width, height]
            center = [(close_node[0] + far_node[0]) / 2,
                      (close_node[1] + far_node[1]) / 2]
            half_width, half_height = width / 2, height / 2
            cos, sin = (np.cos(np.radians(rotation)),
                        np.sin(np.radians(rotation)))
            bottom_right = [center[0] - half_height
                            * cos + half_width * sin,
                            center[1] - half_height
                            * sin - half_width * cos]

            # Create elongated rectangle and append to the list
            elongated_rect = Roi(
                objective_resolution,
                zs,
                center,
                rotation,
                size,
                rect.z,
                close_node,
                far_node,
                bottom_right,
                pixel_resolution_xy=None,
                pix_um_ratio=None)

            elongated_z_plane_rectangles.append(elongated_rect)

        elongated_rectangles[z] = elongated_z_plane_rectangles

    return elongated_rectangles


def convert_to_polygon(
        rectangle: Roi
) -> Polygon:
    """
    Convert the rectangles into shapely.Polygon object because
    it allows to calculate the intersection area
    in calculate_overlap_matrix.

    Parameters
    ----------
    rectangle : Roi
        custom Roi object

    Returns
    -------
    Polygon
        custom Roi object as a Polygon

    """

    return Polygon([rectangle.bottom_right, rectangle.bottom_left,
                    rectangle.top_left, rectangle.top_right])


def calculate_overlap_matrix(
        class_var: object,
        rectangles: list
) -> list:
    """
    For a list of rectangles (in a z-plane) generates an overlap matrix,
    describing how much of a rectangle's area
    is covered by another rectangle (in %).
    The row-based sum of %s indicates the overall
    overlap for a rectangle in a scanfield.
    If this value is greater than a threshold,
    that rectangle will be discarded,
    as the area it covers is covered by surrounding rectangles.

    Parameters
    ----------
    class_var : TYPE
        The class object containing relevant parameters.
    rectangles : list
        list of custom Roi objects.

    Returns
    -------
    list
        boolean list of rectangles to discard

    """

    # Initialize empty matrix
    n = len(rectangles)
    overlap_matrix = np.zeros((n, n))

    # Compare all rectangles with all the others and fill in the matrix
    for i, rect1 in enumerate(rectangles):
        polygon1 = convert_to_polygon(rect1)
        for j, rect2 in enumerate(rectangles):
            polygon2 = convert_to_polygon(rectangles[j])
            intersection = polygon1.intersection(polygon2)
            percentage_overlap = (intersection.area * 100) / rect1.area
            overlap_matrix[i, j] = percentage_overlap

    # Initialize boolean mask
    overlap_mask = [False] * n

    # For every rectangle that fits the overlap criteria, set mask to True
    for i in range(n):
        percentage_overlap = ((convert_to_polygon(rectangles[i]).area * 100)
                              / rectangles[i].area)
        overlap_matrix[i, :] /= percentage_overlap

        # 1.0 is full overlap with itself
        global_overlap = sum(overlap_matrix[i, :]) - 1.0
        if global_overlap > class_var.overlap_threshold:
            overlap_mask[i] = True

    return overlap_mask


def remove_overlapping(
        class_var: object,
        rectangles: list
) -> list:
    """
    Checks all the scanfields and removes rectangles that overlap with others
    within the same z plane to prevent repetitive scanning of the same area.
    Applies calculate_overlap_matrix on each z plane.

    Parameters
    ----------
    class_var : TYPE
        list of custom Roi objects.
    rectangles : list
        DESCRIPTION.

    Returns
    -------
    list
        list of custom Roi objects without overlapping rectangles.

    """

    # Pre-allocate empty list of z planes
    removed_overlapped_rectangles = [None] * len(rectangles)

    for n, z_plane in enumerate(rectangles):

        if len(z_plane) > 1:
            overlap_mask = calculate_overlap_matrix(class_var, z_plane)

            if any(overlap_mask):
                removing_indices = [i for i in range(len(overlap_mask))
                                    if overlap_mask[i]]
                z_plane = [rect for n, rect in enumerate(z_plane)
                           if n not in removing_indices]

        removed_overlapped_rectangles[n] = z_plane

    return removed_overlapped_rectangles


def euclidean_distance(
        point1: object,
        point2: object
) -> float:

    return math.sqrt(
        (point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def remove_rect_within_radius(
        class_var: object,
        rectangles: list
) -> list:

    radius_apical, radius_basal = class_var.filtering_radius

    filtered_rectangles = []

    for n, z_plane_rectangles in enumerate(rectangles):

        filtered_z_plane = []

        if not z_plane_rectangles:
            continue

        for rect in z_plane_rectangles:

            if rect.compartment == 'apical dendrite':
                radius = radius_apical
            elif rect.compartment == 'basal dendrite':
                radius = radius_basal

            corners = [rect.bottom_left,
                       rect.bottom_right,
                       rect.top_left,
                       rect.top_right]

            max_distance = max(
                euclidean_distance(corner, (class_var.soma.x,
                                            class_var.soma.y))
                for corner in corners)

            if max_distance > radius:
                filtered_z_plane.append(rect)

        filtered_rectangles.append(filtered_z_plane)

    return filtered_rectangles


def affine(
        rect: Roi
) -> np.ndarray:
    """
    Constructs an affine transformation matrix for a given rectangle.

    Parameters
    ----------
    rect : Roi
        Roi object.

    Returns
    -------
    np.ndarray
        Affine transformation matrix.

    """

    center = rect.center_deg
    size = rect.size_deg
    rotation_degrees = rect.rotation_degrees

    # Translation to origin (pre-scaling)
    translation_to_origin = np.eye(3)
    translation_to_origin[:, 2] = [-0.5, -0.5, 1]

    # Rotation by rotation_degrees
    rotation_transformation = np.eye(3)
    radians = np.radians(rotation_degrees)
    cos = np.cos(radians)
    sin = np.sin(radians)
    rotation_transformation[0:2, 0:2] = [[cos, -sin], [sin, cos]]

    # Scaling
    scaling = np.diag([size[0], size[1], 1])

    # Translation to rect center
    translation_to_center = np.eye(3)
    translation_to_center[:, 2] = [center[0], center[1], 1]

    return np.matmul(
        np.matmul(np.matmul(translation_to_center,
                            rotation_transformation),
                  scaling), translation_to_origin)


def pixel_to_ref_transformation(
        rect: Roi,
        affine: np.ndarray
) -> np.ndarray:
    """
    Constructs a pixel to reference transformation matrix
    for a given rectangle and its affine matrix.

    Parameters
    ----------
    rect : Roi
        Roi object
    affine : np.ndarray
        Affine transformation matrix.

    Returns
    -------
    t : np.ndarray
        Pixel to reference transformation matrix

    """

    pixel_resolution_xy = rect.pixel_resolution_xy
    pixel_width_xy = 1 / np.array(rect.pixel_resolution_xy)

    x_off = -pixel_width_xy[0] / 2
    y_off = -pixel_width_xy[1] / 2

    x_scale = 1 / pixel_resolution_xy[0]
    y_scale = 1 / pixel_resolution_xy[1]

    t = [
        [x_scale, 0, x_off],
        [0, y_scale, y_off],
        [0, 0, 1]
    ]

    transformation_matrix = np.dot(affine, t)

    # Set precision to 9 decimal places and suppress scientific notation
    np.set_printoptions(precision=9, suppress=True)

    return transformation_matrix


def calculate_transform(
        class_var: object,
        rectangles: list
) -> list:
    """
    Calculates the transformation matrices for a set of rectangles.

    Parameters
    ----------
    class_var : TYPE
        The class object containing relevant parameters.
    rectangles : list
        List of lists of Roi objects.

    Returns
    -------
    list
        Updated list of rectangles with transformation matrices.

    """

    objective_resolution = class_var.objective_resolution
    zs = class_var.zs

    new_rectangles = []

    for z_plane_rectangles in rectangles:
        if not z_plane_rectangles:
            continue

        new_z_plane_rectangles = []

        for rect in z_plane_rectangles:
            T = affine(rect)

            close_node = rect.start_node + \
                [rect.z, rect.start_node_id, rect.compartment]
            far_node = rect.end_node + \
                [rect.z, rect.end_node_id, rect.compartment]

            new_rect = Roi(objective_resolution,
                           zs, rect.center_xy, rect.rotation_degrees,
                           rect.size_xy, rect.z,
                           close_node, far_node, rect.bottom_right,
                           pixel_resolution_xy=rect.pixel_resolution_xy,
                           pix_um_ratio=rect.pix_um_ratio,
                           pixel_to_ref=[list(row)
                                         for row in
                                         pixel_to_ref_transformation(
                                             rect, T)],
                           affine=[list(row) for row in T])
            new_z_plane_rectangles.append(new_rect)

        new_rectangles.append(new_z_plane_rectangles)

    return new_rectangles


def roi_populate_pixels(
        class_var: object,
        rectangles: list
) -> list:
    """
    Derives scanfield pixel properties by reverse-calculation
    starting from desired framerate.
    The function calculates each rectangle's properties
    such as pixel resolution, width, height
    and creates new rectangle instances with updated properties.
    The updated rectangles are returned in the same format as the input.
    It ensures a consistent frame rate across all scanfields.

    Parameters
    ----------
    class_var : object
       The class object containing relevant parameters.
    rectangles : list
        List of rectangles grouped by Z-plane.

    Returns
    -------
    list
        Updated list of rectangles with modified properties.

    """

    objective_resolution = class_var.objective_resolution
    frame_flyback = class_var.frame_flyback
    fly_to_line = class_var.fly_to_line
    dwell_time = class_var.dwell_time
    fill_fraction = class_var.fill_fraction
    optimal_pix_um_ratio = class_var.optimal_pix_um_ratio
    sampling_rate_ctl = class_var.sampling_rate_ctl

    desired_framerate = class_var.desired_framerate
    desired_scanperiod = 1 / desired_framerate

    # Pre-allocate empty list
    new_z_planes = [None] * len(rectangles)

    for z, z_plane in enumerate(rectangles):

        if not z_plane:
            continue

        # Time needed for scanning all the rectangular ROI
        # without flyto and frame flyback time
        roi_active_scantime = (
            desired_scanperiod -
            frame_flyback -
            (fly_to_line * (len(z_plane) - 1))
        )

        # Initial pixel size considering all rectangles and overscan
        pixel_size = calculate_pixel_size(
            roi_active_scantime,
            dwell_time,
            z_plane,
            fill_fraction)

        # Pre-allocate empty list
        new_rects = [None] * len(z_plane)

        for r, rect in enumerate(z_plane):

            # Current dimensions of a single rectangle
            width, height = rect.size_xy
            aspect_ratio = width / height

            # Calculate the number of pixels based on the pixel size
            num_pixels_width = np.ceil(width / pixel_size)
            num_pixels_height = np.ceil(height / pixel_size)

            # Ensure pixel dimensions are even
            if num_pixels_width % 2 != 0:
                num_pixels_width += 1
            if num_pixels_height % 2 != 0:
                num_pixels_height += 1

            acquisition_line_period = dwell_time * num_pixels_width

            # this if-else chunck is from Scanimage GalvoGalvo.m
            if class_var.sampling_rate is not None:

                scan_acq_samples = np.ceil(
                    class_var.sampling_rate *
                    acquisition_line_period /
                    fill_fraction)
                scan_acq_samples_range = np.arange(
                    scan_acq_samples,
                    int(np.ceil(1.5 * scan_acq_samples)) + 1)

                scan_acq_samples_range = scan_acq_samples_range[
                    scan_acq_samples_range % 2 == 0]

                scan_acq_times = (
                    scan_acq_samples_range / class_var.sampling_rate)

                ctl_samples = scan_acq_times * sampling_rate_ctl

                ctl_samples = ctl_samples[ctl_samples % 2 == 0]

                line_scan_period = (
                    min(ctl_samples) / sampling_rate_ctl)

            else:
                samples_acq = (
                    acquisition_line_period * sampling_rate_ctl)

                samples_turnaround_half = np.ceil(
                    ((samples_acq / fill_fraction) - samples_acq) / 2)

                samples_scan = samples_acq + 2 * samples_turnaround_half

                line_scan_period = (
                    samples_scan / sampling_rate_ctl)

            # line_scan_period = acquisition_line_period / fill_fraction
            rectangle_period = line_scan_period * num_pixels_height
            derived_line_period = rectangle_period / aspect_ratio

            print(line_scan_period, derived_line_period * 0.9)

            pix_um_ratio = num_pixels_width / width
            if pix_um_ratio < optimal_pix_um_ratio:
                pix_um_ratio = optimal_pix_um_ratio

            # Recalculate width and height based on the pixel ratio
            width_recalculated = num_pixels_width / pix_um_ratio
            height_recalculated = num_pixels_height / pix_um_ratio

            # Calculate the new bottom right coordinates and nodes
            x_center, y_center = rect.center_xy
            half_width = width_recalculated / 2
            half_height = height_recalculated / 2
            rotation = rect.rotation_degrees
            sin = np.sin(np.radians(rotation))
            cos = np.cos(np.radians(rotation))
            close_node = [x_center - half_height *
                          cos, y_center - half_height * sin]
            x = close_node[0] + half_width * sin
            y = close_node[1] - half_width * cos

            close_node = rect.start_node + [
                rect.z, rect.start_node_id, rect.compartment]
            far_node = rect.end_node + [
                rect.z, rect.end_node_id, rect.compartment]
            close_node.append(rect.start_node_id)
            far_node.append(rect.end_node_id)

            new_bottom_right = [x, y]

            # Create a new rectangle instance with updated properties
            new_rect = Roi(
                objective_resolution,
                class_var.zs,
                center=rect.center_xy,
                rotation=rect.rotation_degrees,
                size=[width_recalculated, height_recalculated],
                z=rect.z,
                start=close_node,
                end=far_node,
                bottom_right=new_bottom_right,
                pixel_resolution_xy=[num_pixels_width, num_pixels_height],
                pix_um_ratio=pix_um_ratio
            )

            # Add the updated rectangle to the list
            new_rects[r] = new_rect

        # Add the updated z-plane to the list
        new_z_planes[z] = new_rects

    # Calculate the resulting frame rates for each z-plane
    frame_rates = calculate_z_framerate(class_var, new_z_planes)

    # Print frame rates for verification
    for z, rate in enumerate(frame_rates):
        print(f"Z-plane 0{z}: {rate:.3f} Hz, period {1/rate:.3f}"
              if z < 10 else
              f"Z-plane {z}: {rate:.3f} Hz, period {1/rate:.3f}")

    return new_z_planes


def calculate_pixel_size(
        desired_scanperiod,
        pixel_dwell_time,
        rectangles,
        fill_fraction):
    """
    Calculate the required pixel size for multiple rectangles
    given the active scan time and pixel dwell time.

    Parameters
    ----------
    desired_scanperiod, float
        The total active scan time for the region of interest (ROI) in µs.
    pixel_dwell_time, float
        The time to scan one pixel in µs.
    rectangles, list
        A list of dictionaries where each dictionary represents
        a rectangle's dimensions with keys 'width' and 'height' µm.

    Returns:
    - float: The required pixel size in micrometers (µm/pixel).
    """

    scan_area_um = sum(
        [((rect.size_xy[0] / fill_fraction) * rect.size_xy[1])
         for rect in rectangles])

    # time required to scan all pixels
    numerator = scan_area_um * pixel_dwell_time
    pixel_size_squared = numerator / desired_scanperiod
    pixel_size = math.sqrt(pixel_size_squared)

    return pixel_size


def calculate_line_period(
        class_var: object,
        rect: object
) -> (float, float, float):

    dwell_time = class_var.dwell_time
    fill_fraction = class_var.fill_fraction

    num_pixels_width, num_pixels_height = rect.pixel_resolution_xy

    # Calculate line active acquisition time
    line_active_acquisition_time = num_pixels_width * dwell_time

    # Calculate line period including fill fraction
    line_period = line_active_acquisition_time / fill_fraction

    # Calculate rectangle period
    rect_period = line_period * num_pixels_height

    return line_active_acquisition_time, line_period, rect_period



def calculate_z_framerate(
        class_var: object,
        rectangles: list,
) -> list:
    """
    Calculates the frame rate for each z-plane based on
    rectangle properties and scanning parameters.

    Parameters
    ----------
    rectangles : list
        2D list of Roi objects grouped by z-plane.

    Returns
    -------
    list
        Frame rates for each z-plane.

    """

    frame_flyback = class_var.frame_flyback
    fly_to_line = class_var.fly_to_line

    scan_period = []
    for z, z_plane in enumerate(rectangles):
        if z_plane:
            scan_period_z = 0
            for rect in z_plane:

                (
                    line_active_acquisition_time,
                    line_period,
                    rect_period
                ) = calculate_line_period(class_var, rect)

                scan_period_z += rect_period
            scan_period.append(scan_period_z + frame_flyback +
                               (fly_to_line * (len(z_plane) - 1)))
    framerate = [(1 / i) for i in scan_period]

    return framerate
