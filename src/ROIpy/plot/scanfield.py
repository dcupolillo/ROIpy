from __future__ import annotations
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import ROIpy.core.scanfields as sfld
from ROIpy.plot._common import (
    check_metadata, get_scan_units, equal_cube_limits, apply_zoom_3d,
    merge_kwargs, normalize_rois, make_z_colormap, add_z_colorbar,
    create_2d_axes, create_3d_axes, ensure_3d_axes)


def plot_scanfield(
        rectangles: list | sfld.ScanfieldBundle | sfld.Roi,
        metadata: dict | None = None,
        ax: plt.Axes | None = None,
        cmap: str = None,
        show_cbar: bool = False,
        scan_angle: bool = False,
        rect_kwargs: dict | None = None,
        ax_kwargs: dict | None = None,
) -> None:
    """
    Plot rectangles representing ROIs on a given axis.

    Parameters
    ----------
    rectangles : list or sfld.ScanfieldBundle or sfld.Roi
        List of Roi objects to be plotted.
    metadata : dict, optional
        The morphology metadata dictionary. Default is None.
    ax : plt.Axes, optional
        The axis on which to plot.
        If None, a new figure and axis will be created. Default is None.
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
    ax_kwargs : dict, optional
        Additional keyword arguments passed to `Axes.set` (e.g. title,
        facecolor, aspect, xlim, ylim). Only used when `ax` is None.
        Default is None.

    Returns
    -------
    None
    """
    check_metadata(metadata)

    rectangles = normalize_rois(rectangles)

    units, corners = get_scan_units(metadata, scan_angle)

    default_rect_kwargs = {
        'edgecolor': "black",
        'facecolor': "none",
        'linewidth': 1.0,
        'alpha': 0.5
    }
    rect_kwargs = merge_kwargs(default_rect_kwargs, rect_kwargs)

    if metadata:
        zs = metadata['zs']
        stack_name = metadata['stack_name']
        xlim = (min(corners[0]), max(corners[1]))
        ylim = (max(corners[2]), min(corners[3]))
    
    else:
        zs = [rect.z for rect in rectangles]
        stack_name = None
        xlim, ylim = None, None
    
    zmin, zmax = min(zs), max(zs)

    if cmap is not None:
        rect_kwargs.pop("facecolor", None)

        cmap, norm, sm = make_z_colormap(cmap, zmin, zmax)

    default_ax_kwargs = {
        'xlabel': units,
        'xlim': xlim,
        'ylim': ylim,
        'aspect': 'equal',
        'title': stack_name,
    }

    if not ax:
        ax = create_2d_axes(
            corners, **merge_kwargs(default_ax_kwargs, ax_kwargs))
    else:
        ax.set(xlim=xlim, ylim=ylim, xlabel=units)

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
        sm.set_clim(vmin=zmin, vmax=zmax)

        cbar = add_z_colorbar(sm, ax)
        cbar.set_label('Z')


def plot_scanfields_3d(
        rectangles: list | sfld.ScanfieldBundle | sfld.Roi,
        metadata: dict = None,
        ax: plt.Axes = None,
        cmap: str = None,
        show_cbar: bool = False,
        scan_angle: bool = False,
        elev: float = 30,
        azim: float = 30,
        zoom: float = 1.0,
        rect_kwargs: dict = None,
        ax_kwargs: dict = None,
) -> plt.Axes:
    """
    Plot rectangles representing ROIs in a 3D space.

    Parameters
    ----------
    rectangles : list or sfld.ScanfieldBundle or sfld.Roi
        List of Roi objects to be plotted.
    metadata : dict, optional
        The morphology metadata dictionary. Default is None.
    ax : plt.Axes, optional
        The axis on which to plot.
        If None, a new 3D axis will be created. Default is None.
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
    ax_kwargs : dict, optional
        Additional keyword arguments passed to `Axes.set` (e.g. title,
        zlabel). Only used when `ax` is None. Default is None.

    Returns
    -------
    plt.Axes
        The 3D axes the rectangles were drawn on.
    """
    check_metadata(metadata)

    rectangles = normalize_rois(rectangles)

    zs = metadata['zs'] if metadata else [rect.z for rect in rectangles]

    default_rect_kwargs = {
        'edgecolor': "black",
        'facecolor': "crimson",
        'linewidth': 1.0,
        'alpha': 0.5
    }
    rect_kwargs = merge_kwargs(default_rect_kwargs, rect_kwargs)

    # Most extreme x, y and z values among all corners of all rectangles
    x_vals, y_vals, z_vals = [], [], []
    for rect in rectangles:
        rect_corners = [
            rect.bottom_right,
            rect.top_right,
            rect.top_left,
            rect.bottom_left]

        x_vals.extend([corner[0] for corner in rect_corners])
        y_vals.extend([corner[1] for corner in rect_corners])
        z_vals.extend([rect.z for _ in rect_corners])

    xlim, ylim, zlim = equal_cube_limits(x_vals, y_vals, z_vals)
    limits_kwargs = {'xlim': xlim, 'ylim': ylim, 'zlim': zlim}

    user_supplied_ax = bool(ax)

    if not user_supplied_ax:
        units, _ = get_scan_units(metadata, scan_angle)

        default_ax_kwargs = {
            **limits_kwargs,
            'zticks': (min(zs), max(zs)),
            'zticklabels': (min(zs), max(zs)),
            'aspect': 'equal'
        }
        # Default tick labels only make sense with the default ticks
        if ax_kwargs and 'zticks' in ax_kwargs \
                and 'zticklabels' not in ax_kwargs:
            default_ax_kwargs.pop('zticklabels')
        ax = create_3d_axes(**merge_kwargs(default_ax_kwargs, ax_kwargs))

        ax.set_xlabel(units, labelpad=30)
        ax.set_ylabel(units, labelpad=30)

    ensure_3d_axes(ax)

    z_values = [rect.z for rect in rectangles]

    if cmap is not None:
        rect_kwargs.pop("facecolor", None)
        cmap, norm, scalar_map = make_z_colormap(
            cmap, min(z_values), max(z_values))
    
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
            color = scalar_map.to_rgba(z)

            poly3d = Poly3DCollection(
                faces,
                facecolors=color,
                clip_on=False,
                **rect_kwargs
            )
        else:
            poly3d = Poly3DCollection(
                faces,
                clip_on=False,
                **rect_kwargs
            )

        ax.add_collection3d(poly3d)

    if cmap and show_cbar:
        cbar = add_z_colorbar(scalar_map, ax, inset=False)
        cbar.set_label("Z (Âµm)")

    if user_supplied_ax:
        ax.set(**limits_kwargs)

    if azim is not None:
        ax.view_init(elev=elev, azim=azim)

    apply_zoom_3d(ax, zoom)

    return ax
