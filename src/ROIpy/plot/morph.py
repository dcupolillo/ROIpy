from __future__ import annotations
import matplotlib.pyplot as plt
import numpy as np
import ROIpy.core.morphology as mrph
from ROIpy.plot._common import (
    check_metadata, get_scan_units, equal_cube_limits, apply_zoom_3d,
    merge_kwargs, make_z_colormap, add_z_colorbar, create_2d_axes,
    create_3d_axes, ensure_3d_axes)


def tapered_segment(
        ax: plt.Axes,
        x1: float, y1: float, r1: float,
        x2: float, y2: float, r2: float,
        tridim: bool = False,
        z1: float = None, z2: float = None,
        **kwargs
) -> None:
    """
    Draw a tapered segment between two nodes with variable thickness.
    
    Parameters
    ----------
    ax : plt.Axes
        The axes to draw on
    x1, y1, r1 : float
        Parent node coordinates and radius
    x2, y2, r2 : float
        Child node coordinates and radius  
    tridim : bool, optional
        Whether this is a 3D plot. Default is False.
    z1, z2 : float, optional
        Z coordinates for 3D plotting
    **kwargs
        Additional styling arguments
    """
    if tridim:
        # For 3D, fall back to line with average thickness
        avg_radius = (r1 + r2) / 2.0
        line_kwargs = {**kwargs, 'linewidth': avg_radius}
        ax.plot([x1, x2], [y1, y2], [z1, z2], **line_kwargs)
        return
    
    # Calculate direction and length
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    
    if length < 1e-10:  # Avoid division by zero
        return
    
    # Unit perpendicular vector (rotated 90 degrees)
    perp_x = -dy / length
    perp_y = dx / length
    
    # Create trapezoid vertices (clockwise)
    polygon_x = [
        x1 + perp_x * r1,  # parent top
        x2 + perp_x * r2,  # child top
        x2 - perp_x * r2,  # child bottom
        x1 - perp_x * r1   # parent bottom
    ]
    polygon_y = [
        y1 + perp_y * r1,
        y2 + perp_y * r2,
        y2 - perp_y * r2,
        y1 - perp_y * r1
    ]
    
    # Remove linewidth and linestyle from kwargs for fill
    fill_kwargs = {k: v for k, v in kwargs.items() 
                   if k not in ['linewidth', 'linestyle', 'ls']}
    fill_kwargs.setdefault('alpha', 0.7)
    fill_kwargs.setdefault('edgecolor', fill_kwargs.get('color', 'black'))
    fill_kwargs.setdefault('linewidth', 0.5)
    
    ax.fill(polygon_x, polygon_y, **fill_kwargs)


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

    skeleton_kwargs = merge_kwargs(default_kwargs, kwargs)

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
            if skeleton_kwargs.get('linewidth') is None:
                # Use tapered segment representation
                z1 = parent.z if tridim else None
                z2 = node.z if tridim else None
                
                tapered_segment(
                    ax=axis,
                    x1=x_values[1], y1=y_values[1], r1=r_parent,
                    x2=x_values[0], y2=y_values[0], r2=r_node,
                    tridim=tridim,
                    z1=z1, z2=z2,
                    **skeleton_kwargs
                )
            else:
                # Use specified linewidth (constant thickness)
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
        input_data: list | mrph.Node | mrph.NodeBundle,
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
    The morphology can be visualized either in spatial (Âµm) or angular
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

    if isinstance(input_data, mrph.Node):
        input_data = [input_data]

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

    nodes_kwargs = merge_kwargs(default_nodes_kwargs, nodes_kwargs)
    segments_kwargs = merge_kwargs(default_segments_kwargs, segments_kwargs)

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

    cmap, norm, sm = make_z_colormap(cmap, zmin, zmax)

    if ax is None:
        ax = create_2d_axes(
            corners,
            xlim=xlim,
            ylim=ylim,
            xlabel=units if axes_labels else "",
            ylabel=units if axes_labels else "",
            title=title)

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
            cbar = add_z_colorbar(sm, ax)
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
    if not isinstance(input_data, (list, mrph.Node, mrph.NodeBundle)):
        raise TypeError("input_data must be a list of Nodes, a single Node, "
                        "or a NodeBundle.")
    
    if isinstance(input_data, mrph.Node):
        input_data = [input_data]

    if not all(isinstance(node, mrph.Node) for node in input_data):
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

    nodes_kwargs = merge_kwargs(default_nodes_kwargs, nodes_kwargs)
    segments_kwargs = merge_kwargs(default_segments_kwargs, segments_kwargs)

    if not ax:
        ax = create_3d_axes(
            xlabel="X",
            ylabel="Y" if not flip_yz else "Z",
            zlabel="Z" if not flip_yz else "Y")

    ensure_3d_axes(ax)

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
            cmap, norm, scalar_map = make_z_colormap(
                cmap, min(z_nodes), max(z_nodes))

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
            cbar = add_z_colorbar(scalar_map, ax, inset=False)
            cbar.set_label("Z (Âµm)")

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
        xlim, ylim, zlim = equal_cube_limits(
            [node.x for node in input_data],
            [node.y for node in input_data],
            [node.z for node in input_data])

        ax.set(
            xlim=xlim,
            ylim=ylim if not flip_yz else zlim,
            zlim=zlim if not flip_yz else ylim
            )

    if azim is not None:
        ax.view_init(elev=elev, azim=azim)

    apply_zoom_3d(ax, zoom)
