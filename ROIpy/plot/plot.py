""" Created on Mon Nov  6 14:41:00 2023
    @author: dcupolillo """

from __future__ import annotations
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.colors as colors
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.animation import FuncAnimation
import matplotlib.colors as mcolors
import numpy as np
import ROIpy.core.bundles as bndls
import ROIpy.core.components as cmpnts


def plot(
        data,
        metadata: dict = None,
        projection: str = '2d',
        *args,
        **kwargs
) -> None:
    """
    Generic plotting function that dispatches to specific plotters based on data type.

    Parameters
    ----------
    data : 
        Stack, Morphology, Scanfields,
        Node, NodeBundle, Roi, ScanfieldBundle, list
        
        The data to be plotted. The accepted keyword arguments depend on
        the data type:

        | Data Type                | Main Keyword Arguments (kwargs)          |
        |-------------------------|-------------------------------------------|
        | Stack (np.ndarray)      | cmap, norm, axes_labels, ax               |
        | Morphology/Node/Bundle  | show_nodes, show_segments, cmap,          |
        |                         | show_cmap, axes_labels, nodes_kwargs,     |
        |                         | segments_kwargs, ax, axis_lims            |
        | Scanfields/Roi/Bundle   | cmap, show_cbar, scan_angle, rect_kwargs, |
        |                         | ax, axis_lims                             |
        | 3D Plotting             | projection='3d', azim, elev, axis_lims    |

    metadata : dict, optional
        Metadata dictionary containing relevant information for plotting
        (e.g., units, corners, stack name).
        If passed, it will be used for axis labeling and limits.
    projection : str, optional
        Type of projection: '2d' or '3d'. Default is '2d'.
    *args : tuple
        Additional positional arguments to pass to the specific plotter.
    **kwargs : dict
        Additional keyword arguments to pass to the specific plotter.

    Notes
    -----
    For a full list of accepted arguments, see the docstring of the dispatched
    function for your data type:
    - Stack:
        >>> from ROIpy.plot.plot import plot_image
        >>> help(plot_image)
    - Morphology/Node/NodeBundle:
        >>> from ROIpy.plot.plot import plot_morph, plot_morph_3d
        >>> help(plot_morph)
    - Scanfields/Roi/ScanfieldBundle:
        >>> from ROIpy.plot.plot import plot_scanfield, plot_scanfields_3d
        >>> help(plot_scanfields)

    Returns
    -------
    None
    """
    if projection not in ['2d', '3d']:
        raise ValueError("Invalid projection type. Choose '2d' or '3d'.")

    if isinstance(data, np.ndarray):
        return plot_image(data, metadata=metadata, *args, **kwargs)

    elif (isinstance(data, cmpnts.Node) or
            isinstance(data, bndls.NodeBundle) or
            isinstance(data, bndls.Neurite) or
            (isinstance(data, list) and
             all(isinstance(d, cmpnts.Node) for d in data))):

        if projection == "3d":
            return plot_morph_3d(data, *args, **kwargs)

        else:
            return plot_morph(data, metadata=metadata, *args, **kwargs)

    elif (isinstance(data, cmpnts.Roi) or
            isinstance(data, bndls.ScanfieldBundle) or
            (isinstance(data, list) and
             all(isinstance(d, cmpnts.Roi) for d in data))):

        if projection == "3d":
            return plot_scanfields_3d(data, metadata=metadata, *args, **kwargs)

        else:
            return plot_scanfield(data, metadata=metadata, *args, **kwargs)

    else:
        raise TypeError("Unsupported data type for plotting.")


def animate(
        data,
        *args,
        **kwargs
) -> None:
    """
    Generic animation function that dispatches to specific animators
    based on data type.

    Parameters
    ----------
    data : Morphology, Scanfields, Node, NodeBundle, Roi, ScanfieldBundle, list
        The data to be animated. Accepted keyword arguments depend on
        the data type:

        | Data Type                | Main Keyword Arguments (kwargs)      |
        |-------------------------|--------------------------------------|
        | Morphology/Node/Bundle  | show_nodes, scan_angle, axis_lims,   |
        |                         | cmap, show_cbar, elev_start,         |
        |                         | elev_end, azimut_start, azimut_end,  |
        |                         | interval, frames, save_path,         |
        |                         | axis_label, nodes_kwargs,            |
        |                         | segments_kwargs                      |
        | Scanfields/Roi/Bundle   | cmap, show_cbar, scan_angle,         |
        |                         | elev_start, elev_end, azimut_start,  |
        |                         | azimut_end, interval, frames,        |
        |                         | save_path, zoom, axis_label,         |
        |                         | rect_kwargs                          |

    *args : tuple
        Additional positional arguments to pass to the specific animator.
    **kwargs : dict
        Additional keyword arguments to pass to the specific animator.

    Notes
    -----
    For a full list of accepted arguments, see the docstring of the
    dispatched function for your data type:
    - Morphology/Node/NodeBundle:
        >>> from ROIpy.plot.plot import animate_morph_3d
        >>> help(animate_morph_3d)
    - Scanfields/Roi/ScanfieldBundle:
        >>> from ROIpy.plot.plot import animate_scanfields_3d
        >>> help(animate_scanfields_3d)

    Returns
    -------
    None
    """
    if (isinstance(data, cmpnts.Node) or
            isinstance(data, bndls.NodeBundle) or
            isinstance(data, bndls.Neurite) or
            (isinstance(data, list) and
             all(isinstance(d, cmpnts.Node) for d in data))):

        return animate_morph_3d(data, *args, **kwargs)

    elif (isinstance(data, cmpnts.Roi) or
            isinstance(data, bndls.ScanfieldBundle) or
            (isinstance(data, list) and
             all(isinstance(d, cmpnts.Roi) for d in data))):

        return animate_scanfields_3d(data, *args, **kwargs)

    else:
        raise TypeError("Unsupported data type for plotting.")
    
def update_3d_view(
        ax: plt.Axes,
        elev_start: float,
        elev_end: float,
        azimut_start: float,
        azimut_end: float,
        frames: int
) -> callable:
    """
    Returns a function that updates the 3D view of the Axes.
    
    Parameters
    ----------
    ax : plt.Axes
        The 3D Axes to be updated.
    elev_start : float
        Starting elevation angle.
    elev_end : float
        Ending elevation angle.
    azimut_start : float
        Starting azimuth angle.
    azimut_end : float
        Ending azimuth angle.
    frames : int
        Total number of frames in the animation.
    
    Returns
    -------
    callable
        A function that updates the view for each frame.
    """
    
    def updater(frame):
        
        current_elev = (
            elev_start +
            (elev_end - elev_start) *
            (frame / (frames - 1))
        )
        current_azimut = (
            azimut_start +
            (azimut_end - azimut_start) *
            (frame / (frames - 1))
        )
        ax.view_init(elev=current_elev, azim=current_azimut)
        
        return ax,
    
    return updater


def check_metadata(metadata: dict) -> None:
    """
    Check if metadata contains minimal required keys.

    Parameters
    ----------
    metadata : dict
        The metadata dictionary to be checked.

    Raises
    ------
    TypeError
        if metadata is not a dictionary
    ValueError
        if metadata is None
    KeyError
        if required keys are missing
    """

    required_keys = ['units_um', 'units_deg', 'corners_um', 'corners_deg']

    if metadata and not isinstance(metadata, dict):
        raise TypeError("metadata must be a dictionary.")

    if metadata is not None:
        for key in required_keys:
            if key not in metadata:
                raise KeyError(f"Metadata missing required key: {key}")


def get_scan_units(
        metadata: dict,
        scan_angle: bool
) -> tuple:
    """
    Returns the appropriate units, corners, and labels
    based on the scan_angle flag.

    Parameters
    ----------
    metadata : dict
        The metadata dictionary containing units and corners information.
    scan_angle : bool
        If True, returns angle-based values (degrees).
        If False, returns spatial values (micrometers).

    Returns
    -------
    tuple
        (units, corners)
    """
    if metadata is None:
        return None, None

    if scan_angle:
        return metadata['units_deg'], metadata['corners_deg']

    return metadata['units_um'], metadata['corners_um']


def plot_image(
        image: np.ndarray,
        metadata: dict = None,
        scan_angle: bool = False,
        ax: plt.Axes = None,
        norm: tuple or list = None,
        cmap: str = "binary_r",
        axes_labels: bool = True,
) -> None:
    """
    Plots a 2D image from a Stack class instance.

    Parameters
    ----------
    image : np.ndarray
        The image data to be plotted.
    metadata : dict
        The metadata dictionary containing units and corners information.
    scan_angle : bool, optional
        Specifies whether the scan angle should be used for plotting.
    ax : plt.Axes, optional
        The axes on which to plot. If not provided, a new subplot is created.
    norm : tuple or list, optional
        Normalize colorscale.
    cmap : str, optional
        Colormap of pixel intensity (Matplotlib default colormaps).

    Raises
    ------
    KeyError
        if norm is not a list or a tuple

    Returns
    -------
    None

    """
    check_metadata(metadata)

    stack_name = metadata.get('stack_name', 'Stack') if metadata else None
    units, corners = get_scan_units(metadata, scan_angle)

    if metadata:
        stack_name = metadata['stack_name']
        xlim = (min(corners[0]), max(corners[1]))
        ylim = (max(corners[2]), min(corners[3]))

        flat_corners = [
            [values for values in sublist] for sublist in corners]

        extent = [
            np.min(flat_corners), np.max(flat_corners),
            np.max(flat_corners), np.min(flat_corners)]
    else:
        stack_name = 'Stack'
        xlim, ylim = None, None
        extent = None

    if ax is None:
        _, ax = plt.subplots()

        ax.set(
            xlabel=units if axes_labels else "",
            ylabel=units if axes_labels else "",
            xlim=xlim,
            ylim=ylim,
            aspect="equal",
            title=stack_name,
            )

        if not corners:
            ax.autoscale()

    img = np.max(image, axis=0) if image.ndim == 3 else image

    if norm is None:
        ax.imshow(img, extent=extent, cmap=cmap)

    elif isinstance(norm, (list, tuple)):
        min_value, max_value = norm
        norm = Normalize(vmin=min_value, vmax=max_value)
        ax.imshow(img, extent=extent, cmap=cmap, norm=norm)

    else:
        raise KeyError("'norm' should be a list or a tuple")


def skeleton(
        input_data: list,
        ax: plt.Axes,
        tridim: bool,
        scan_angle: bool,
        **kwargs
) -> None:
    """
    Plots the 2D or 3D skeleton of a structure using matplotlib.

    Parameters
    ----------
    input_data : list
        List of Node objects representing the structure.
    ax : plt.Axes
        Axes object(s) to plot on.
    tridim : bool
        Whether to plot in 3D or not.
    scan_angle : bool
        Whether to use angle-based coordinates or not.
    **kwargs : dict, optional
        Additional keyword arguments for customizing
        line style, color, linewidth, etc. Default is None.

    Returns
    -------
    None
    """

    default_kwargs = {
        'color': "black",
        'linewidth': 1.0,
        "ls": '-'
    }

    skeleton_kwargs = {**default_kwargs, **(kwargs or {})}

    axes = ax if isinstance(ax, list) else [ax]

    node_dict = {node._id: node for node in input_data} if input_data else {}

    for node in input_data if input_data else []:

        if node.parent_id == -1:
            continue  # Skip soma

        parent = node_dict.get(node.parent_id)
        if not parent:
            continue

        for axis in axes:
            if axis is None:
                continue

            x_values = (
                [node.x, parent.x] if not scan_angle
                else [node.x_deg, parent.x_deg])

            y_values = (
                [node.y, parent.y] if not scan_angle
                else [node.y_deg, parent.y_deg])

            r_node = 1 if node.radius == 0 else node.radius
            r_parent = 1 if parent.radius == 0 else parent.radius

            # Determine linewidth priority: skeleton_kwargs > argument > comp.
            if ('linewidth' not in skeleton_kwargs and
                    skeleton_kwargs['linewidth'] is None):
                default_kwargs['linewidth'] = (r_node + r_parent) / 2.0

            if not tridim:
                axis.plot(
                    x_values,
                    y_values,
                    **skeleton_kwargs)
            else:
                z_values = [node.z, parent.z]
                axis.plot(
                    x_values,
                    y_values,
                    z_values,
                    **skeleton_kwargs)


def plot_morph(
        input_data: list or cmpnts.Node or bndls.NodeBundle,
        metadata: dict = None,
        show_segments: bool = True,
        show_nodes: bool = False,
        scan_angle: bool = False,
        ax: plt.Axes = None,
        axis_lims: list = None,
        cmap: str = None,
        show_cbar: bool = False,
        axes_labels: bool = False,
        nodes_kwargs: dict = None,
        segments_kwargs: dict = None,
) -> None:
    """
    Plot a two-dimensional representation of a neuronal morphology.

    This function visualizes a neuronal morphology in 2D,
    optionally showing the segmented skeleton, individual nodes
    and a colormap indicating Z-plane depth.
    The morphology can be visualized either in spatial (µm) or angular
    (degrees) coordinates.

    Parameters
    ----------
    input_data : list
        List of Node objects, a single Node, or a NodeBundle
        representing the neuronal structure.
    metadata : dict, optional
        The metadata dictionary containing units and corners information.
        Default is None.
    show_segments : bool, optional
        If True, display the skeleton connecting nodes.
        Default is True.
    show_nodes : bool, optional
        If True, display individual nodes as scatter points.
        Default is False.
    scan_angle : bool, optional
        If True, use angle-based coordinates (degrees).
        If False, use spatial coordinates (micrometers). Default is False.
    ax : plt.Axes, optional
        Matplotlib axes object to plot on. If None, a new plot is created.
        Default is None.
    axis_lims : list, optional
        List specifying the axis limits as [xmin, xmax, ymin, ymax].
        If None, default bounds are used. Default is None.
    cmap : str, optional
        Name of the colormap to use for visualizing Z-plane depth.
        Default is None.
    show_cbar : bool, optional
        If True, display a colorbar. Default is False.
    axes_labels : bool, optional
        If True, axis labels are displayed. Default is False.
    nodes_kwargs : dict, optional
        Additional keyword arguments for customizing node appearance.
        Default is None.
    segments_kwargs : dict, optional
        Additional keyword arguments for customizing segment appearance.
        Default is None.

    Returns
    -------
    None
        This function modifies the provided axes object or creates
        a new Matplotlib plot.
    """
    check_metadata(metadata)

    if isinstance(input_data, cmpnts.Node):
        input_data = [input_data]

    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)

    default_nodes_kwargs = {
        'edgecolor': 'black',
        'alpha': 0.7,
        'linewidth': 0.5,
        's': 10,
        'color': 'crimson'
    }

    default_segments_kwargs = {
        'color': 'black',
        'linewidth': 1
    }

    # Merge user-supplied kwargs (user overrides default)
    nodes_kwargs = {**default_nodes_kwargs, **(nodes_kwargs or {})}
    segments_kwargs = {**default_segments_kwargs, **(segments_kwargs or {})}

    units, corners = get_scan_units(metadata, scan_angle)

    if metadata:
        title = metadata['stack_name']
        xlim = (min(corners[0]), max(corners[1]))
        ylim = (max(corners[2]), min(corners[3]))
    else:
        title = None
        xlim, ylim = None, None
        
    zs = [node.z for node in input_data] if metadata is None else metadata['zs']
    zmin, zmax = min(zs), max(zs)

    norm = colors.Normalize(
        vmin=zmin,
        vmax=zmax)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)

    if ax is None:
        _, ax = plt.subplots()

        ax.set(
            xlim=xlim,
            ylim=ylim,
            xlabel=units if axes_labels else "",
            ylabel=units if axes_labels else "",
            title=title,
            aspect='equal'
            )

        if not corners:
            ax.autoscale()

    if axis_lims is not None:
        ax.set(
            xlim=(min(axis_lims[0]), max(axis_lims[1])),
            ylim=(max(axis_lims[2]), min(axis_lims[3])))

    x_values = (
        [node.x_deg for node in input_data] if scan_angle
        else [node.x for node in input_data])
    y_values = (
        [node.y_deg for node in input_data] if scan_angle
        else [node.y for node in input_data])
    z_values = [node.z for node in input_data]

    if not show_nodes and not show_segments:
        raise KeyError('At least either show_nodes or'
                       ' show_segments must be True')

    if show_nodes:
        if cmap is not None:
            # Remove 'color' from nodes_kwargs to avoid conflict with cmap
            nodes_kwargs = {
                k: v for k, v in nodes_kwargs.items() if k != 'color'}
            ax.scatter(
                x_values,
                y_values,
                c=z_values,
                cmap=cmap,
                norm=norm,
                zorder=10,
                **nodes_kwargs
            )
        else:
            # Use default color from nodes_kwargs
            ax.scatter(
                x_values,
                y_values,
                **nodes_kwargs
            )

        if show_cbar and cmap is not None:
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="2%", pad=0.1)
            cbar = plt.colorbar(sm, ax=ax, orientation='vertical', cax=cax)
            cbar.set_label('Z')

    if show_segments:
        skeleton(
            input_data=input_data,
            ax=ax,
            tridim=False,
            scan_angle=scan_angle,
            **segments_kwargs)


def plot_morph_3d(
        input_data: list,
        ax: plt.Axes = None,
        show_nodes: bool = False,
        scan_angle: bool = False,
        axis_lims: list = None,
        cmap: str = None,
        show_cbar: bool = False,
        azim: float = 30,
        elev: float = 30,
        zoom: float = 1.0,
        flip_yz: bool = False,
        nodes_kwargs: dict = None,
        segments_kwargs: dict = None
):
    """
    Plot a 3D representation of a morphology object.

    Parameters
    ----------
    input_data : list
        List of Node objects representing the morphology structure.
    ax : plt.Axes, optional
        Matplotlib 3D axes to plot on.
        If None, a new figure and axes are created. Default is None.
    show_nodes : bool, optional
        If True, display individual nodes. Default is False.
    scan_angle : bool, optional
        If True, use angle-based coordinates. Default is False.
    axis_lims : list, optional
        Axis limits [xmin, xmax, ymin, ymax, zmin, zmax]. Default is None.
    cmap : str, optional
        Colormap to use for node coloring. Default is None.
    show_cbar : bool, optional
        If True, display a colorbar. Default is False.
    azim : float, optional
        Azimuth angle for 3D view. Default is None.
    elev : float, optional
        Elevation angle for 3D view. Default is None.
    zoom : float, optional
        Zoom factor for 3D view. Default is 1.0.
    flip_yz : bool, optional
        If True, swaps the Y and Z axes in the plot. Default is False.
    nodes_kwargs : dict, optional
        Additional keyword arguments for customizing node appearance.
        Default is None.
    segments_kwargs : dict, optional
        Additional keyword arguments for customizing segment appearance.
        Default is None.

    Returns
    -------
    None
    """
    if not isinstance(input_data, (list, cmpnts.Node, bndls.NodeBundle)):
        raise TypeError("input_data must be a list of Nodes, a single Node, "
                        "or a NodeBundle.")
    
    if isinstance(input_data, cmpnts.Node):
        input_data = [input_data]

    if not all(isinstance(node, cmpnts.Node) for node in input_data):
        raise TypeError("All elements in input_data must be Nodes.")

    default_nodes_kwargs = {
        'edgecolor': 'black',
        'alpha': 0.7,
        'linewidth': 0.5,
        's': 10,
        'color': 'crimson'
    }

    default_segments_kwargs = {
        'color': 'black',
        'linewidth': 1
    }

    nodes_kwargs = {**default_nodes_kwargs, **(nodes_kwargs or {})}
    segments_kwargs = {**default_segments_kwargs, **(segments_kwargs or {})}

    if not ax:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        ax.set(
            xlabel="X",
            ylabel="Y" if not flip_yz else "Z",
            zlabel="Z" if not flip_yz else "Y",
            )

    if ax is not None and not ax.name == '3d':
        raise ValueError("Provided Axes must be 3D.")

    node_dict = {node.id: node for node in input_data}

    for node in input_data:
        if node.parent_id not in node_dict:
            continue

        parent = node_dict[node.parent_id]

        x = [node.x, parent.x]
        y = [node.y, parent.y] if not flip_yz else [node.z, parent.z]
        z = [node.z, parent.z] if not flip_yz else [node.y, parent.y]

        if segments_kwargs["linewidth"] is None:
            segments_kwargs['linewidth'] = (node.radius + parent.radius) / 2.0

        ax.plot(x, y, z, **segments_kwargs)

    if show_nodes:
        x_nodes = [
            node.x_deg if scan_angle else node.x
            for node in input_data]
        y_nodes = [
            node.y_deg if scan_angle else node.y
            for node in input_data]
        z_nodes = [node.z for node in input_data]

        if cmap is not None:
            # Remove 'color' from nodes_kwargs to avoid conflict with cmap
            nodes_kwargs = {
                k: v for k, v in nodes_kwargs.items() if k != 'color'}
            cmap = plt.get_cmap(cmap)
            norm = plt.Normalize(min(z_nodes), max(z_nodes))
            scalar_map= plt.cm.ScalarMappable(cmap=cmap, norm=norm)

            ax.scatter(
                x_nodes,
                y_nodes if not flip_yz else z_nodes,
                z_nodes if not flip_yz else y_nodes,
                c=z_nodes,
                cmap=cmap,
                **nodes_kwargs)
        else:
            ax.scatter(
                x_nodes,
                y_nodes,
                z_nodes,
                **nodes_kwargs)

        if show_cbar:
            cbar = plt.colorbar(scalar_map, ax=ax)
            cbar.set_label("Z (µm)")

    if axis_lims:
        ax.set(
            xlim=(axis_lims[0], axis_lims[1]),
            ylim=(
                (axis_lims[2], axis_lims[3])
                if not flip_yz else (axis_lims[4], axis_lims[5])),
            zlim=(
                (axis_lims[4], axis_lims[5])
                if not flip_yz else (axis_lims[2], axis_lims[3]))
            )

    else:
        x_vals = [node.x for node in input_data]
        y_vals = [node.y for node in input_data] 
        z_vals = [node.z for node in input_data]

        max_range = np.array(
            [max(x_vals) - min(x_vals),
             max(y_vals) - min(y_vals),
             max(z_vals) - min(z_vals)]).max() / 2.0

        mid_x = (max(x_vals) + min(x_vals)) * 0.5
        mid_y = (max(y_vals) + min(y_vals)) * 0.5
        mid_z = (max(z_vals) + min(z_vals)) * 0.5

        ax.set(
            xlim=(mid_x - max_range, mid_x + max_range),
            ylim=(
                (mid_y - max_range, mid_y + max_range)
                if not flip_yz else (mid_z - max_range, mid_z + max_range)),
            zlim=(
                (mid_z - max_range, mid_z + max_range)
                if not flip_yz else (mid_y - max_range, mid_y + max_range))
            )

    if azim is not None:
        ax.view_init(elev=elev, azim=azim)

    # --- Zoom effect by scaling axis limits ---
    if zoom != 1.0:
        xlim = ax.get_xlim3d()
        ylim = ax.get_ylim3d()
        zlim = ax.get_zlim3d()
        xmid = (xlim[0] + xlim[1]) / 2.0
        ymid = (ylim[0] + ylim[1]) / 2.0
        zmid = (zlim[0] + zlim[1]) / 2.0
        xsize = (xlim[1] - xlim[0]) / zoom
        ysize = (ylim[1] - ylim[0]) / zoom
        zsize = (zlim[1] - zlim[0]) / zoom
        ax.set_xlim3d(xmid - xsize/2, xmid + xsize/2)
        ax.set_ylim3d(ymid - ysize/2, ymid + ysize/2)
        ax.set_zlim3d(zmid - zsize/2, zmid + zsize/2)



def animate_morph_3d(
        input_data: list,
        show_nodes: bool = False,
        scan_angle: bool = False,
        axis_lims: list = None,
        cmap: str = None,
        show_cbar: bool = False,
        elev_start: float = 30,
        elev_end: float = 30,
        azimut_start: float = 0,
        azimut_end: float = 360,
        interval: int = 100,
        frames: int = 360,
        save_path: str = None,
        axis_label: bool = True,
        flip_yz: bool = False,
        zoom: float = 1.0,
        nodes_kwargs: dict = None,
        segments_kwargs: dict = None,
):
    """
    Animate a 3D plot of a morphology structure with customizable
    rotation and elevation changes.

    Parameters
    ----------
    input_data : list
        List of Node objects representing the morphology
        structure to be plotted.
    show_nodes : bool, optional
        If True, individual nodes of the morphology are displayed as
        scatter points. Default is False.
    scan_angle : bool, optional
        If True, uses angle-based coordinates for node positions.
        Default is False.
    axis_lims : list, optional
        A list specifying the axis limits as
        [xmin, xmax, ymin, ymax, zmin, zmax].
        If None, the limits are determined automatically. Default is None.
    cmap : str, optional
        Colormap to use for coloring nodes based on their z-coordinates
        (if `show_nodes` is True). Default is None.
    show_cbar : bool, optional
        If True, display a colorbar. Default is False.
    elev_start : float, optional
        Starting elevation angle (vertical tilt) in degrees for the animation.
        Default is 30.
    elev_end : float, optional
        Ending elevation angle (vertical tilt) in degrees for the animation.
        Default is 30.
    azimut_start : float, optional
        Starting azimuth angle (horizontal rotation)
        in degrees for the animation. Default is 0.
    azimut_end : float, optional
        Ending azimuth angle (horizontal rotation)
        in degrees for the animation. Default is 360.
    interval : int, optional
        Time interval between frames in milliseconds. Default is 100.
    frames : int, optional
        Total number of frames in the animation. Default is 360.
    save_path : str, optional
        File path to save the animation (e.g., as a .gif or .mp4 file).
        If None, the animation is not saved. Default is None.
    axis_label : bool, optional
        If True, axis labels ("X", "Y", "Z") are displayed.
        If False, axis labels and ticks are hidden. Default is True.
    flip_yz : bool, optional
        If True, swaps the Y and Z axes in the plot. Default is False.
    zoom : float, optional
        Zoom factor for the 3D view. Default is 1.0.
    nodes_kwargs : dict, optional
        Additional keyword arguments for customizing node appearance.
        Default is None.
    segments_kwargs : dict, optional
        Additional keyword arguments for customizing segment appearance.
        Default is None.

    Returns
    -------
    anim : matplotlib.animation.FuncAnimation
        The generated animation object. This can be displayed using plt.show()
        or saved to a file.
    """
    default_nodes_kwargs = {
        'edgecolor': 'black',
        'alpha': 0.7,
        'linewidth': 0.5,
        's': 10,
        'color': 'crimson'
    }

    default_segments_kwargs = {
        'color': 'black',
        'linewidth': 1
    }

    # Merge user-supplied kwargs (user overrides default)
    nodes_kwargs = {**default_nodes_kwargs, **(nodes_kwargs or {})}
    segments_kwargs = {**default_segments_kwargs, **(segments_kwargs or {})}

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    if not axis_label:
        ax.tick_params(axis='both', which='both', length=0)
        ax.set(
            xticks=([]),
            yticks=([]),
            zticks=([]),
            xlabel="",
            ylabel="",
            zlabel="")
    else:
        ax.set(
            xlabel="X",
            ylabel="Y",
            zlabel="Z")

    plot_morph_3d(
        input_data=input_data,
        show_nodes=show_nodes,
        scan_angle=scan_angle,
        axis_lims=axis_lims,
        cmap=cmap,
        show_cbar=show_cbar,
        azim=azimut_start,
        elev=elev_start,
        ax=ax,
        flip_yz=flip_yz,
        zoom=zoom,
        nodes_kwargs=nodes_kwargs,
        segments_kwargs=segments_kwargs
    )

    anim = FuncAnimation(
        fig,
        update_3d_view(
            ax,
            elev_start,
            elev_end,
            azimut_start,
            azimut_end,
            frames),
        frames=frames,
        interval=interval,
        blit=False)

    if save_path:
        anim.save(save_path, writer="pillow")

    return anim


def plot_scanfield(
        rectangles: list or bndls.ScanfieldBundle or cmpnts.Roi,
        metadata: dict = None,
        ax: plt.Axes = None,
        axis_lims: list = None,
        cmap: str = None,
        show_cbar: bool = False,
        scan_angle: bool = False,
        rect_kwargs: dict = None,
) -> None:
    """
    Plot rectangles representing ROIs on a given axis.

    Parameters
    ----------
    rectangles : list or bndls.ScanfieldBundle or cmpnts.Roi
        List of Roi objects to be plotted.
    metadata : dict, optional
        The morphology metadata dictionary. Default is None.
    ax : plt.Axes, optional
        The axis on which to plot.
        If None, a new figure and axis will be created. Default is None.
    axis_lims : list, optional
        If specified, plot will be bounded to limits. Default is None.
    cmap : str, optional
        Colormap to use for coloring the rectangles based on z values.
        Default is None.
    show_cbar : bool, optional
        If True, a colorbar will be displayed. Default is False.
    scan_angle : bool, optional
        If True, the rectangles will be plotted using angle coordinates.
        Default is False.
    rect_kwargs : dict, optional
        Additional keyword arguments for customizing rectangle appearance.
        Default is None.

    Returns
    -------
    None
    """
    check_metadata(metadata)

    if not isinstance(rectangles, (list, bndls.ScanfieldBundle, cmpnts.Roi)):
        raise TypeError("rectangles must be a list, ScanfieldBundle, or Roi.")

    if isinstance(rectangles, bndls.ScanfieldBundle):
        rectangles = [rect for roiSet in rectangles for rect in roiSet]

    elif isinstance(rectangles, cmpnts.Roi):
        rectangles = [rectangles]

    units, corners = get_scan_units(metadata, scan_angle)

    default_rect_kwargs = {
        'edgecolor': "black",
        'facecolor': "none",
        'linewidth': 1.0,
        'alpha': 0.5
    }
    rect_kwargs = {**default_rect_kwargs, **(rect_kwargs or {})}

    if metadata:
        zs = metadata['zs']
        stack_name = metadata['stack_name']
        xlim = (min(corners[0]), max(corners[1]))
        ylim = (max(corners[2]), min(corners[3]))
    else:
        zs = [0, 1]
        stack_name = None
        xlim, ylim = None, None

    if cmap is not None:
        rect_kwargs.pop("facecolor", None)

        cmap = plt.cm.get_cmap(cmap)
        norm = colors.Normalize(
            vmin=min(zs), vmax=max(zs))
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)

    # If it's a 2d lists of ROIs (multiple scanfields)
    # flattens it to get a 1d list of ROIs
    if isinstance(rectangles, bndls.ScanfieldBundle):
        rectangles = [rect for roiSet in rectangles for rect in roiSet]

    # If it's an individual ROI
    # put the single ROI object in a single-element list
    elif isinstance(rectangles, cmpnts.Roi):
        rectangles = [rectangles]

    # this block is just for testing intermediate rectangles
    # in the method _create_roi of the class Scanfields
    elif isinstance(rectangles, list):
        rectangles = rectangles

    if not ax:
        _, ax = plt.subplots()
        ax.set(
            aspect='equal',
            title=stack_name,
        )

        if not corners:
            ax.autoscale()

    if axis_lims:
        ax.set(
            xlim=(min(axis_lims[0]), max(axis_lims[1])),
            ylim=(max(axis_lims[2]), min(axis_lims[3])))

    else:
        ax.set(
            xlim=xlim,
            ylim=ylim,
            xlabel=units,)

    for rect in rectangles:

        width, height = (
            rect.size_deg
            if scan_angle
            else rect.size_xy)

        bottom_right = (
            rect.bottom_right_deg
            if scan_angle
            else rect.bottom_right)

        rotation = rect.rotation_degrees

        if cmap is not None:
            facecolor = cmap(norm(rect.z))

            patch = patches.Rectangle(
                bottom_right,
                height, width,
                angle=rotation,
                facecolor=facecolor,
                **rect_kwargs)

        else:
            patch = patches.Rectangle(
                bottom_right,
                height, width,
                angle=rotation,
                **rect_kwargs)

        ax.add_patch(patch)

    if cmap and show_cbar:
        sm.set_array([rect.z for rect in rectangles])
        sm.set_clim(vmin=min(zs), vmax=max(zs))

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="2%", pad=0.1)
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', cax=cax)
        cbar.set_label('Z')


def plot_scanfields_3d(
        rectangles: list or bndls.ScanfieldBundle or cmpnts.Roi,
        metadata: dict = None,
        ax: plt.Axes = None,
        axis_lims: list = None,
        cmap: str = None,
        show_cbar: bool = False,
        scan_angle: bool = False,
        elev: float = 30,
        azim: float = 30,
        zoom: float = 1.0,
        rect_kwargs: dict = None,
) -> None:
    """
    Plot rectangles representing ROIs in a 3D space.

    Parameters
    ----------
    rectangles : list or bndls.ScanfieldBundle or cmpnts.Roi
        List of Roi objects to be plotted.
    metadata : dict, optional
        The morphology metadata dictionary. Default is None.
    ax : plt.Axes, optional
        The axis on which to plot.
        If None, a new 3D axis will be created. Default is None.
    axis_lims : list, optional
        If specified, plot will be bounded to limits. Default is None.
    cmap : str, optional
        Colormap to use for coloring the rectangles based on z values.
        Default is None.
    show_cbar : bool, optional
        If True, a colorbar will be displayed. Default is False.
    scan_angle : bool, optional
        If True, the rectangles will be plotted using angle coordinates.
        Default is False.
    elev : float, optional
        Elevation angle in the z plane. Default is 30.
    azim : float, optional
        Azimuthal angle in the x, y plane. Default is 30.
    zoom : float, optional
        Zoom level for the 3D plot. Default is 1.0.
    rect_kwargs : dict, optional
        Additional keyword arguments for customizing rectangle appearance.
        Default is None.

    Returns
    -------
    None
    """
    check_metadata(metadata)

    if not isinstance(rectangles, (list, bndls.ScanfieldBundle, cmpnts.Roi)):
        raise TypeError("rectangles must be a list, ScanfieldBundle, or Roi.")

    if isinstance(rectangles, bndls.ScanfieldBundle):
        rectangles = [rect for roiSet in rectangles for rect in roiSet]

    elif isinstance(rectangles, cmpnts.Roi):
        rectangles = [rectangles]

    zs = metadata['zs'] if metadata else [rect.z for rect in rectangles]

    default_rect_kwargs = {
        'edgecolor': "black",
        'facecolor': "crimson",
        'linewidth': 1.0,
        'alpha': 0.5
    }
    rect_kwargs = {**default_rect_kwargs, **(rect_kwargs or {})}

    if not ax:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        units, corners = get_scan_units(metadata, scan_angle)

        ax.set(
            xlim=(min(corners[0]), max(corners[1])),
            ylim=(max(corners[2]), min(corners[3])),
            zlim=(min(zs), max(zs)),
            zticks=(min(zs), max(zs)),
            zticklabels=(min(zs), max(zs)),
            aspect='equal')

        ax.set_xlabel(units, labelpad=30)
        ax.set_ylabel(units, labelpad=30)

    if ax is not None and not ax.name == '3d':
        raise ValueError("Provided Axes must be 3D.")

    fig = ax.get_figure()

    z_values = [rect.z for rect in rectangles]
    
    for rect in rectangles:

        x, y = rect.bottom_right
        z = rect.z
        width, height = rect.size_xy

        theta = np.deg2rad(90.0 + rect.rotation_degrees)
        rotation_matrix = np.array(
            [[np.cos(theta), -np.sin(theta)],
             [np.sin(theta), np.cos(theta)]]
        )

        vertices = np.array([
            [x, y, z],
            [x + width, y, z],
            [x + width, y + height, z],
            [x, y + height, z]])

        cxy = np.array([x + width / 2.0, y + height / 2.0])
        rotated_vertices = (
            np.dot(
                vertices[:, :2] - cxy,
                rotation_matrix.T) +
            cxy)

        vertices[:, :2] = rotated_vertices

        # Construct faces
        faces = [vertices]

        if cmap is not None:
            rect_kwargs.pop("facecolor", None)
            cmap = plt.get_cmap(cmap)
            norm = mcolors.Normalize(vmin=min(z_values), vmax=max(z_values))
            scalar_map = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
            color = scalar_map.to_rgba(z)

            poly3d = Poly3DCollection(
                faces,
                facecolors=color,
                **rect_kwargs
            )
        else:
            poly3d = Poly3DCollection(
                faces,
                **rect_kwargs
            )

        ax.add_collection3d(poly3d)

    if cmap and show_cbar:
        cbar = plt.colorbar(scalar_map, ax=ax)
        cbar.set_label("Z (µm)")

    if axis_lims:
        ax.set(
            xlim=(axis_lims[0], axis_lims[1]),
            ylim=(axis_lims[2], axis_lims[3]),
            zlim=(axis_lims[4], axis_lims[5]))
    else:
        # Find most extreme x and y values among all corners of all rectangles
        x_vals = []
        y_vals = []
        z_vals = []
        for rect in rectangles:
            rect_corners = [
                rect.bottom_right,
                rect.top_right,
                rect.top_left,
                rect.bottom_left]
            
            x_vals.extend([corner[0] for corner in rect_corners])
            y_vals.extend([corner[1] for corner in rect_corners])
            z_vals.extend([rect.z for _ in rect_corners])

        max_range = np.array(
            [max(x_vals) - min(x_vals),
             max(y_vals) - min(y_vals),
             max(z_vals) - min(z_vals)]).max() / 2.0
        
        mid_x = (max(x_vals) + min(x_vals)) * 0.5
        mid_y = (max(y_vals) + min(y_vals)) * 0.5
        mid_z = (max(z_vals) + min(z_vals)) * 0.5

        ax.set(
            xlim=(mid_x - max_range, mid_x + max_range),
            ylim=(mid_y - max_range, mid_y + max_range),
            zlim=(mid_z - max_range, mid_z + max_range)
            )
        
    if azim is not None:
        ax.view_init(elev=elev, azim=azim)

    # --- Zoom effect by scaling axis limits ---
    if zoom != 1.0:
        xlim = ax.get_xlim3d()
        ylim = ax.get_ylim3d()
        zlim = ax.get_zlim3d()
        xmid = (xlim[0] + xlim[1]) / 2.0
        ymid = (ylim[0] + ylim[1]) / 2.0
        zmid = (zlim[0] + zlim[1]) / 2.0
        xsize = (xlim[1] - xlim[0]) / zoom
        ysize = (ylim[1] - ylim[0]) / zoom
        zsize = (zlim[1] - zlim[0]) / zoom
        ax.set_xlim3d(xmid - xsize/2, xmid + xsize/2)
        ax.set_ylim3d(ymid - ysize/2, ymid + ysize/2)
        ax.set_zlim3d(zmid - zsize/2, zmid + zsize/2)


def animate_scanfields_3d(
        rectangles: list,
        metadata: dict = None,
        scan_angle: bool = False,
        axis_lims: list = None,
        cmap: str = None,
        show_cbar: bool = False,
        elev_start: float = 30,
        elev_end: float = 30,
        azimut_start: float = 0,
        azimut_end: float = 360,
        interval: int = 100,
        frames: int = 60,
        save_path: str = None,
        axis_label: bool = True,
        zoom: float = 1.0,
        rect_kwargs: dict = None
):
    """
    Animate a 3D representation of scanfields with customizable
    rotation and elevation.

    Parameters
    ----------
    rectangles : list or bndls.ScanfieldBundle or cmpnts.Roi
        List of Roi objects to be plotted.
    metadata : dict, optional
        The morphology metadata dictionary. Default is None.
    cmap : str, optional
        Colormap to use for coloring rectangles based on z values.
        Default is None.
    show_cbar : bool, optional
        If True, a colorbar will be displayed. Default is False.
    scan_angle : bool, optional
        If True, plot rectangles using angle coordinates. Default is False.
    elev_start : float, optional
        Starting elevation angle (vertical tilt) in degrees. Default is 30.
    elev_end : float, optional
        Ending elevation angle (vertical tilt) in degrees. Default is 30.
    azimut_start : float, optional
        Starting azimuth angle (horizontal rotation) in degrees. Default is 0.
    azimut_end : float, optional
        Ending azimuth angle (horizontal rotation) in degrees. Default is 360.
    interval : int, optional
        Time interval between frames in milliseconds. Default is 100.
    frames : int, optional
        Total number of frames in the animation. Default is 60.
    save_path : str, optional
        File path to save the animation (e.g., .gif or .mp4). Default is None.
    zoom : float, optional
        Zoom level for the 3D plot. Default is 1.0.
    axis_label : bool, optional
        If True, display axis labels ("X", "Y", "Z"). Default is False.
    rect_kwargs : dict, optional
        Additional keyword arguments for customizing rectangle appearance.
        Default is None.

    Returns
    -------
    anim : matplotlib.animation.FuncAnimation
        The generated animation object.
    """
    check_metadata(metadata)

    if not isinstance(rectangles, (list, bndls.ScanfieldBundle, cmpnts.Roi)):
        raise TypeError(
            "rectangles must be a list, ScanfieldBundle, or Roi.")

    default_rect_kwargs = {
        'edgecolor': "black",
        'facecolor': "crimson",
        'linewidth': 1.0,
        'alpha': 0.5
    }
    rect_kwargs = {**default_rect_kwargs, **(rect_kwargs or {})}

    if cmap is not None:
        rect_kwargs.pop("facecolor", None)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    if not axis_label:
        ax.tick_params(axis='both', which='both', length=0)
        ax.set(
            xticks=([]),
            yticks=([]),
            zticks=([]),
            xlabel="",
            ylabel="",
            zlabel="")
    else:
        ax.set(
            xlabel="X",
            ylabel="Y",
            zlabel="Z")

    # Initial plot of scanfields
    plot_scanfields_3d(
        rectangles=rectangles,
        metadata=metadata,
        ax=ax,
        axis_lims=axis_lims,
        cmap=cmap,
        show_cbar=show_cbar,
        scan_angle=scan_angle,
        elev=elev_start,
        azim=azimut_start,
        zoom=zoom,
        rect_kwargs=rect_kwargs
    )
    
    # Create the animation
    anim = FuncAnimation(
        fig,
        update_3d_view(
            ax,
            elev_start,
            elev_end,
            azimut_start,
            azimut_end,
            frames),
        frames=frames,
        interval=interval,
        blit=False)

    # Save the animation if a save path is provided
    if save_path:
        anim.save(save_path, writer="pillow")

    return anim
