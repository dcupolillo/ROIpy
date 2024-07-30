""" Created on Mon Nov  6 14:41:00 2023
    @author: dcupolillo """

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.colors as colors
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.cm import ScalarMappable
import matplotlib.colors as mcolors
import numpy as np

from ROIpy.assets.palette import dim


def plot_image(
        class_var: object,
        scan_angle: bool = False,
        ax: plt.Axes = None,
        norm: tuple or list = None,
        cmap: str = None,
        z: int = None
) -> None:
    """
    Plots a 2D image from a Stack class instance.

    Parameters
    ----------
    class_var : object
        The class instance containing image data and attributes.
    scan_angle : bool, optional
        Specifies whether the scan angle should be used for plotting.
        Default is False. The default is False.
    ax : plt.Axes, optional
        The axes on which to plot. If not provided, a new subplot is created.
        The default is None.
    norm : tuple or list, optional
        Normalize colorscale. The default is None.
    cmap : str, optional
        Colormap of pixel intensity (Matplotlib default colormaps).
        The default is None.
    z : int, optional
        If specified, plot the single Z plane. The default is None.

    Raises
    ------
    KeyError
        if norm is not a list or a tuple

    Returns
    -------
    None

    """

    if ax is None:
        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        if isinstance(z, int):
            ax.set_title(f'{class_var.stack_name}, z = {z}')
        else:
            ax.set_title(f'{class_var.stack_name}')
        ax.autoscale()

    img = (class_var.image[z] if z is not None
           else np.max(class_var.image, axis=0))

    # Define the field of view corners and set axis limit
    corners = class_var.corners_um if not scan_angle else class_var.corners_deg
    flat_corners = [[values for values in sublist] for sublist in corners]
    extent = [np.min(flat_corners), np.max(flat_corners),
              np.max(flat_corners), np.min(flat_corners)]

    ax.set_xlim(min(corners[0]), max(corners[1]))
    ax.set_ylim(max(corners[2]), min(corners[3]))

    label = class_var.units_um if not scan_angle else class_var.units_deg
    ax.set_xlabel(label)
    ax.set_ylabel(label)

    # Define colormap
    cmap = cmap if cmap else 'binary_r'

    if norm is None:
        ax.imshow(img, extent=extent, cmap=cmap)
    elif isinstance(norm, (list, tuple)):
        min_value, max_value = norm
        norm = Normalize(vmin=min_value, vmax=max_value)
        ax.imshow(img, extent=extent, cmap=cmap, norm=norm)
    else:
        raise KeyError("'norm' should be a list or a tuple")


def skeleton(
        input_data: list = None,
        ax: plt.Axes = None,
        tridim: bool = False,
        scan_angle: bool = False,
        color: str = 'black',
        linewidth: int = 1,
        z: int = None
) -> None:
    """
    Plots the 2D or 3D skeleton of a structure using matplotlib.

    Parameters
    ----------
    input_data : list, optional
        List of Node objects representing the structure.
        The default is None.
    ax : plt.Axes, optional
        Axes object(s) to plot on. The default is None.
    tridim : bool, optional
        Whether to plot in 3D or not. The default is False.
    scan_angle : bool, optional
        Whether to use angle-based coordinates or not. The default is False.
    color : str, optional
        Color of the plot lines. The default is 'black'.
    linewidth : int, optional
        Width of the plot lines. The default is 1.
    z : int, optional
        If specified, plot only this Z plane. The default is None.

    Returns
    -------
    None

    """

    color = color if color is not None else dim.black.hex
    axes = ax if isinstance(ax, list) else [ax]

    node_dict = {node.id: node for node in input_data} if input_data else {}

    for n, node in enumerate(input_data if input_data else []):
        if node.parent_id in (-1, 1):
            continue  # Skip root or soma

        parent = node_dict.get(node.parent_id)
        if not parent:
            continue

        for axis in axes:
            if axis is None or (z is not None and z != node.z_ind):
                continue

            x_values = ([node.x, parent.x] if not scan_angle
                        else [node.x_deg, parent.x_deg])
            y_values = ([node.y, parent.y] if not scan_angle
                        else [node.y_deg, parent.y_deg])

            if not tridim:
                axis.plot(x_values,
                          y_values,
                          color=color,
                          linewidth=linewidth)
            else:
                z_values = [node.z, parent.z]
                axis.plot(x_values,
                          y_values,
                          z_values,
                          color=color,
                          linewidth=linewidth)


def plot_morph(
        class_var: object,
        input_data: list,
        z: int = None,
        show_segments: bool = True,
        show_nodes: bool = False,
        scan_angle: bool = False,
        ax: plt.Axes = None,
        axis_lims: list = None,
        cmap: str = 'viridis',
        color: str = None,
        linewidth: int = 1
) -> None:
    """
    Plot a two-dimensional representation of a morphology object.

    Parameters
    ----------
    class_var : object
        The morphology object to visualize.
    input_data : list
        DESCRIPTION.List of Node objects representing the structure.
    z : int, optional
        DESCRIPTION. The default is None.
    show_segments : bool, optional
        If True, show the skeleton of segmented compartments.
        The default is True.
    show_nodes : bool, optional
        If True, show individual nodes on the plot. The default is False.
    scan_angle : bool, optional
        If True, use angle-based coordinates.
        The default is False.
    ax : plt.Axes, optional
        Axes object(s) to plot on, or None to create new axes.
        The default is None.
    cmap : str, optional
        Colormap to use for coloring different Z planes.
        The default is 'viridis'.
    color : str, optional
        Color of the skeleton lines. The default is None.
    linewidth : int, optional
        Width of the connecting line between nodes The default is 1.

    Returns
    -------
    None

    """

    color = color if color is not None else dim.black.hex
    cmap = plt.get_cmap(cmap)
    norm = colors.Normalize(vmin=min(class_var.zs), vmax=max(class_var.zs))
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)

    z = float(z) if z is not None else None

    if ax is None:
        fig, ax = plt.subplots()
        ax.set_title(class_var.stack_name)
        ax.set_aspect('equal')

        corners = class_var.corners_deg if scan_angle else class_var.corners_um
        units = class_var.units_deg if scan_angle else class_var.units_um

        ax.set_xlim(min(corners[0]), max(corners[1]))
        ax.set_ylim(max(corners[2]), min(corners[3]))
        ax.set_xlabel(units)
        ax.set_ylabel(units)

    if axis_lims is not None:
        ax.set_xlim(min(axis_lims[0]), max(axis_lims[1]))
        ax.set_ylim(max(axis_lims[2]), min(axis_lims[3]))

    if z is None:
        x_values = ([node.x_deg for node in input_data] if scan_angle
                    else [node.x for node in input_data])
        y_values = ([node.y_deg for node in input_data] if scan_angle
                    else [node.y for node in input_data])
        z_values = [node.z for node in input_data]

        if not show_nodes and not show_segments:
            raise KeyError('At least either show_nodes or'
                           ' show_segments must be True')

        if show_nodes:
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="2%", pad=0.1)
            ax.scatter(x_values, y_values, c=z_values, cmap=cmap)
            cbar = plt.colorbar(sm, ax=ax, orientation='vertical', cax=cax)
            cbar.set_label('Z')

    else:
        x_values = ([node.x_deg for node in input_data if node.z_ind == z]
                    if scan_angle
                    else [node.x for node in input_data
                          if node.z_ind == z])
        y_values = ([node.y_deg for node in input_data
                     if node.z_ind == z]
                    if scan_angle
                    else [node.y for node in input_data
                          if node.z_ind == z])
        z_values = [node.z for node in input_data if node.z_ind == z]

        if not show_nodes and not show_segments:
            raise KeyError('At least either show_nodes or'
                           ' show_segments must be True')

        if show_nodes:
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="2%", pad=0.1)
            ax.scatter(x_values, y_values, c=z_values, cmap=cmap)
            cbar = plt.colorbar(sm, ax=ax, orientation='vertical', cax=cax)
            cbar.set_label('Z')

    if show_segments:
        skeleton(input_data=input_data, ax=ax, scan_angle=scan_angle,
                 color=color, linewidth=linewidth, z=z)


def plot_morph_scanned_highlight(
        class_var: object,
        input_data: list,
        rectangles: list,
        z: int = None,
        scan_angle: bool = False,
        ax: plt.Axes = None,
        axis_lims: list = None,
        color: str = None,
        linewidth: int = 2
) -> None:
    """
    TODO

    Parameters
    ----------
    class_var : object
        DESCRIPTION.
    input_data : list
        DESCRIPTION.
    rectangles : list
        DESCRIPTION.
    z : int, optional
        DESCRIPTION. The default is None.
    scan_angle : bool, optional
        DESCRIPTION. The default is False.
    ax : plt.Axes, optional
        DESCRIPTION. The default is None.
    axis_lims : list, optional
        DESCRIPTION. The default is None.
    color : str, optional
        DESCRIPTION. The default is None.
    linewidth : int, optional
        DESCRIPTION. The default is 1.

    Returns
    -------
    None
        DESCRIPTION.

    """

    z = float(z) if z is not None else None

    if ax is None:
        fig, ax = plt.subplots()
        ax.set_title(class_var.stack_name)
        ax.set_aspect('equal')

        corners = class_var.corners_deg if scan_angle else class_var.corners_um
        units = class_var.units_deg if scan_angle else class_var.units_um

        ax.set_xlim(min(corners[0]), max(corners[1]))
        ax.set_ylim(max(corners[2]), min(corners[3]))
        ax.set_xlabel(units)
        ax.set_ylabel(units)

    if axis_lims is not None:
        ax.set_xlim(min(axis_lims[0]), max(axis_lims[1]))
        ax.set_ylim(max(axis_lims[2]), min(axis_lims[3]))

    for z_plane_rects in rectangles:
        if z_plane_rects:
            for rect in z_plane_rects:
                highlighted_data = [
                    node for node in input_data
                    if (node.id >= rect.start_node_id and
                        node.id <= rect.end_node_id)]
                # FIXME: check dendrites that run the opposite way,
                # i.e. towards the soma,
                # the order of their id is reversed

                skeleton(
                    input_data=highlighted_data,
                    ax=ax,
                    scan_angle=scan_angle,
                    color=color,
                    linewidth=linewidth,
                    z=z)


def plot_scanfield(
        class_var: object,
        rectangles: list,
        ax: plt.Axes = None,
        axis_lims: list = None,
        cmap: str = None,
        edgecolor: str = dim.black.hex,
        linewidth: int = 1,
        scan_angle: bool = False
) -> None:
    """
    Plot rectangles representing ROIs on a given axis.

    Parameters
    ----------
    class_var : object
        The Scanfield object containing metadata.
    rectangles : list
        List of Roi objects to be plotted.
    ax : plt.Axes, optional
        The axis on which to plot.
        If None, a new figure and axis will be created.
        The default is None.
    axis_lims : list, optional,
        If specified, plot will be bounded to limits.
    cmap : str, optional
        Colormap to use for coloring the rectangles based on z values.
        The default is None.
    edgecolor : str, optional
        Color of the rectangle edges. The default is dim.black.hex.
    linewidth : int, optional
        Width of rectangle's line. The default is 1.
    scan_angle : bool, optional
        If True, the rectangles will be plotted using angle coordinates.
        The default is False.

    Returns
    -------

    """

    if cmap:
        cmap = plt.cm.get_cmap(cmap)
        norm = colors.Normalize(vmin=min(class_var.zs), vmax=max(class_var.zs))
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)

    # If it's a 2d lists of ROIs (multiple scanfields)
    # flattens it to get a 1d list of ROIs
    if str(type(rectangles)) == "<class 'ROIpy.core.bundles.ScanfieldBundle'>":
        rectangles = [rect for roiSet in rectangles for rect in roiSet]

    # If it's an individual ROI
    # put the single ROI object in a single-element list
    elif str(type(rectangles)) == "<class 'ROIpy.core.components.Roi'>":
        rectangles = [rectangles]

    # this block is just for testing intermediate rectangles
    # in the method _create_roi of the class Scanfields
    elif isinstance(rectangles, list):
        try:
            rectangles = [rect for roiSet in rectangles for rect in roiSet]
        except Exception:
            rectangles = [rect for rect in rectangles]

    if not ax:
        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        ax.set_title(class_var.stack_name)
        ax.autoscale()

        corners = (class_var.corners_deg if scan_angle
                   else class_var.corners_um)
        units = (class_var.units_deg if scan_angle
                 else class_var.units_um)

        ax.set_xlim(min(corners[0]), max(corners[1]))
        ax.set_ylim(max(corners[2]), min(corners[3]))
        ax.set_xlabel(units)
        ax.set_ylabel(units)

    if axis_lims is not None:
        ax.set_xlim(min(axis_lims[0]), max(axis_lims[1]))
        ax.set_ylim(max(axis_lims[2]), min(axis_lims[3]))

    for rect in rectangles:

        color = cmap(norm(rect.z)) if cmap else 'none'

        width, height = rect.size_deg if scan_angle else rect.size_xy
        bottom_right = (rect.bottom_right_deg if scan_angle
                        else rect.bottom_right)
        rotation = rect.rotation_degrees

        patch = patches.Rectangle(bottom_right,
                                  height, width,
                                  angle=rotation,
                                  facecolor=color,
                                  edgecolor=edgecolor,
                                  linewidth=linewidth,
                                  alpha=.5)
        ax.add_patch(patch)

    if cmap:
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="2%", pad=0.1)
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', cax=cax)
        cbar.set_label('Z')


def plot_scanfields_3d(
        class_var: object,
        rectangles: list,
        ax: plt.Axes = None,
        figsize: tuple = None,
        show_title: bool = False,
        cmap: str = None,
        edgecolor: str = dim.black.hex,
        linewidth: int = 1,
        alpha: float = None,
        scan_angle: bool = False,
        elev: int or float = None,
        azim: int or float = None,
        zoom: float = None
) -> None:
    """
    Plot rectangles representing ROIs in a 3D space.

    Parameters
    ----------
    class_var : object
        The Scanfield object containing metadata.
    rectangles : list
        List of Roi objects to be plotted.
    ax : plt.Axes, optional
        The axis on which to plot. If None, a new 3D axis will be created.
        The default is None.
    figsize : tuple, optional
        Figure size (width, height) in inches. The default is None.
    show_title : bool, optional
        Whether to show the title of the plot. The default is False.
    cmap : str, optional
        Colormap to use for coloring the rectangles based on z values.
        The default is None.
    edgecolor : str, optional
        Color of the rectangle edges. The default is dim.black.hex.
    linewidth : int, optional
        Width of the rectangle's edges. The default is 1.
    alpha : float, optional
        Transparency of the rectangles. The default is None.
    scan_angle : bool, optional
        If True, the rectangles will be plotted using angle coordinates.
        The default is False.
    elev : int or float, optional
        Elevation angle in the z plane. The default is None.
    azim : int or float, optional
        Azimuthal angle in the x, y plane. The default is None.

    Returns
    -------
    None
    """

    if str(type(rectangles)) == "<class 'ROIpy.core.bundles.ScanfieldBundle'>":
        rectangles = [rect for roiSet in rectangles for rect in roiSet]

    elif str(type(rectangles)) == "<class 'ROIpy.core.components.Roi'>":
        rectangles = [rectangles]

    if not ax:
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        if show_title:
            ax.set_title(class_var.stack_name)

        corners = (class_var.corners_deg if scan_angle
                   else class_var.corners_um)
        units = (class_var.units_deg if scan_angle
                 else class_var.units_um)

        ax.set_xlim(min(corners[0]), max(corners[1]))
        ax.set_ylim(max(corners[2]), min(corners[3]))
        ax.set_zlim(class_var.zs[-1], class_var.zs[0])
        ax.set_xlabel(units, labelpad=30)
        ax.set_ylabel(units, labelpad=30)

        ax.set_zticklabels([])

        ax.set_aspect('equal')

    z_values = [rect.z for rect in rectangles]
    norm = mcolors.Normalize(vmin=min(z_values), vmax=max(z_values))
    scalar_map = plt.cm.ScalarMappable(norm=norm, cmap=cmap)

    for rect in rectangles:

        x, y = rect.bottom_right
        z = rect.z
        width, height = rect.size_xy

        rotation_matrix = np.array(
            [[np.cos(np.deg2rad(90 + rect.rotation_degrees)),
              -np.sin(np.deg2rad(90 + rect.rotation_degrees))],
             [np.sin(np.deg2rad(90 + rect.rotation_degrees)),
              np.cos(np.deg2rad(90 + rect.rotation_degrees))]
             ]
        )

        vertices = np.array([[x, y, z],
                             [x + width, y, z],
                             [x + width, y + height, z],
                             [x, y + height, z]])
        rotated_vertices = (
            np.dot(vertices[:, :2] - [x + width / 2, y + height / 2],
                   rotation_matrix.T) + [x + width / 2, y + height / 2])

        vertices[:, :2] = rotated_vertices

        # Construct faces
        faces = [[vertices[0], vertices[1], vertices[2], vertices[3]]]

        color = scalar_map.to_rgba(z)

        poly3d = Poly3DCollection(
            faces,
            alpha=alpha,
            linewidths=linewidth,
            edgecolors=edgecolor,
            facecolors=color if cmap else None
            )

        ax.add_collection3d(poly3d)

    if cmap:
        scalar_map.set_array(z_values)
        cbar = fig.colorbar(scalar_map, ax=ax, shrink=0.2, aspect=10)
        cbar.set_label("Z depth")
        cbar.set_ticks([])

    ax.view_init(elev=elev, azim=azim)
    ax.dist = zoom
