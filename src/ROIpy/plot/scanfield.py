from __future__ import annotations
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.patches as patches
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import ROIpy.core.scanfields as sfld
from ROIpy.plot._common import check_metadata, get_scan_units


def plot_scanfield(
        rectangles: list | sfld.ScanfieldBundle | sfld.Roi,
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
    rectangles : list or sfld.ScanfieldBundle or sfld.Roi
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

    if not isinstance(rectangles, (list, sfld.ScanfieldBundle, sfld.Roi)):
        raise TypeError("rectangles must be a list, ScanfieldBundle, or Roi.")

    if isinstance(rectangles, sfld.ScanfieldBundle):
        rectangles = [rect for roiSet in rectangles for rect in roiSet]

    elif isinstance(rectangles, sfld.Roi):
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
        zs = [rect.z for rect in rectangles]
        stack_name = None
        xlim, ylim = None, None
    
    zmin, zmax = min(zs), max(zs)

    if cmap is not None:
        rect_kwargs.pop("facecolor", None)

        cmap = plt.cm.get_cmap(cmap)
        norm = colors.Normalize(
            vmin=zmin, vmax=zmax)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)

    # If it's a 2d lists of ROIs (multiple scanfields)
    # flattens it to get a 1d list of ROIs
    if isinstance(rectangles, sfld.ScanfieldBundle):
        rectangles = [rect for roiSet in rectangles for rect in roiSet]

    # If it's an individual ROI
    # put the single ROI object in a single-element list
    elif isinstance(rectangles, sfld.Roi):
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
        sm.set_clim(vmin=zmin, vmax=zmax)

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="2%", pad=0.1)
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', cax=cax)
        cbar.set_label('Z')


def plot_scanfields_3d(
        rectangles: list | sfld.ScanfieldBundle | sfld.Roi,
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
    rectangles : list or sfld.ScanfieldBundle or sfld.Roi
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

    if not isinstance(rectangles, (list, sfld.ScanfieldBundle, sfld.Roi)):
        raise TypeError("rectangles must be a list, ScanfieldBundle, or Roi.")

    if isinstance(rectangles, sfld.ScanfieldBundle):
        rectangles = [rect for roiSet in rectangles for rect in roiSet]

    elif isinstance(rectangles, sfld.Roi):
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
        cbar = plt.colorbar(scalar_map, ax=ax)
        cbar.set_label("Z (Âµm)")

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
