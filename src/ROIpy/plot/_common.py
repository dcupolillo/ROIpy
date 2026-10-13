"""Shared helpers for ROIpy plotting modules."""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import ROIpy.core.scanfields as sfld


def merge_kwargs(
        defaults: dict,
        overrides: dict | None
) -> dict:
    """
    Return `defaults` updated with `overrides` (user values win).

    Parameters
    ----------
    defaults : dict
        The default keyword arguments.
    overrides : dict or None
        The user-provided keyword arguments that override defaults.

    Returns
    -------
    dict
        The merged dictionary with user values taking precedence.
    """
    return {**defaults, **(overrides or {})}


def normalize_rois(rectangles: list | sfld.ScanfieldBundle | sfld.Roi) -> list:
    """
    Validate ROI input and return it as a flat list of Roi objects.

    Accepts a list, a ScanfieldBundle (flattened) or a single Roi
    (wrapped in a list).

    Raises
    ------
    TypeError
        If `rectangles` is not a list, ScanfieldBundle or Roi.
    """
    if not isinstance(rectangles, (list, sfld.ScanfieldBundle, sfld.Roi)):
        raise TypeError("rectangles must be a list, ScanfieldBundle, or Roi.")

    if isinstance(rectangles, sfld.ScanfieldBundle):
        return [rect for roiSet in rectangles for rect in roiSet]

    if isinstance(rectangles, sfld.Roi):
        return [rectangles]

    return rectangles


def make_z_colormap(
        cmap: str | mcolors.Colormap | None,
        zmin: float,
        zmax: float
) -> tuple:
    """
    Resolve a colormap and build its Z normalization.

    Parameters
    ----------
    cmap : str or Colormap or None
        Colormap name or object.
    zmin: float
        Minimum Z value of colormap range.
    zmax: float
        Maximum Z value of colormap range.

    Returns
    -------
    tuple
        (cmap, norm, scalar_mappable)
    """
    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)
    
    norm = mcolors.Normalize(vmin=zmin, vmax=zmax)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    
    return cmap, norm, sm


def add_z_colorbar(sm, ax: plt.Axes, inset: bool = True):
    """
    Add a colorbar for a Z ScalarMappable and return it.

    Parameters
    ----------
    sm : ScalarMappable
        Mappable describing the Z colormap.
    ax : plt.Axes
        Axes the colorbar belongs to.
    inset : bool, optional
        If True (2D plots), the colorbar is placed in a thin axes appended
        to the right of `ax`. If False (3D plots), matplotlib's default
        placement is used.
    """
    if not inset:
        return plt.colorbar(sm, ax=ax)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2%", pad=0.1)
    return plt.colorbar(sm, ax=ax, orientation='vertical', cax=cax)


def create_2d_axes(
        corners: tuple | None,
        **props: dict
) -> plt.Axes:
    """
    Create a new 2D Axes with equal aspect and the given properties.

    Autoscaling is enabled when `corners` is falsy (no scan metadata, so
    no fixed limits are available).

    Parameters
    ----------
    corners : tuple or None
        The (xmin, xmax, ymin, ymax) corners for the axes limits. If None, autoscaling is used.
    **props : dict
        Additional properties to set on the Axes.

    Returns
    -------
    plt.Axes
        The created 2D Axes object.
    """
    _, ax = plt.subplots()
    ax.set(aspect='equal', **props)

    if not corners:
        ax.autoscale()

    return ax


def create_3d_axes(**props: dict) -> plt.Axes:
    """
    Create a new figure with a single 3D Axes and set `props` on it.

    Parameters
    ----------
    **props : dict
        Additional properties to set on the Axes.

    Returns
    -------
    plt.Axes
        The created 3D Axes object.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set(**props)
    return ax


def ensure_3d_axes(ax: plt.Axes) -> None:
    """
    Raise ValueError if `ax` is not a 3D Axes.

    Parameters
    ----------
    ax : plt.Axes
        The Axes to check.

    Raises
    ------
    ValueError
        If `ax` is not a 3D Axes.
    """
    if ax is not None and not ax.name == '3d':
        raise ValueError("Provided Axes must be 3D.")


def set_3d_axis_labels(
        ax: plt.Axes,
        axis_label: bool
) -> None:
    """
    Show X/Y/Z labels on a 3D Axes, or strip ticks and labels entirely.

    Parameters
    ----------
    ax : plt.Axes
        The 3D Axes to modify.
    axis_label : bool
        If True, show X/Y/Z labels. If False, remove all ticks and labels.
    """
    if not axis_label:
        ax.tick_params(axis='both', which='both', length=0)
        ax.set(
            xticks=([]), yticks=([]), zticks=([]),
            xlabel="", ylabel="", zlabel="")
    else:
        ax.set(
            xlabel="X",
            ylabel="Y",
            zlabel="Z")


def equal_cube_limits(
        x_vals: list,
        y_vals: list,
        z_vals: list
) -> tuple:
    """
    Compute equal-range 3D axis limits centered on the data.

    All three axes share the same span (half the largest data extent on
    either side of each midpoint), so the plotted volume is not distorted.

    Parameters
    ----------
    x_vals, y_vals, z_vals : list of float
        Coordinates of all the points to be enclosed.

    Returns
    -------
    tuple
        ((xmin, xmax), (ymin, ymax), (zmin, zmax))
    """
    max_range = np.array(
        [max(x_vals) - min(x_vals),
         max(y_vals) - min(y_vals),
         max(z_vals) - min(z_vals)]).max() / 2.0

    mid_x = (max(x_vals) + min(x_vals)) * 0.5
    mid_y = (max(y_vals) + min(y_vals)) * 0.5
    mid_z = (max(z_vals) + min(z_vals)) * 0.5

    return (
        (mid_x - max_range, mid_x + max_range),
        (mid_y - max_range, mid_y + max_range),
        (mid_z - max_range, mid_z + max_range))


def apply_zoom_3d(
        ax: plt.Axes,
        zoom: float
) -> None:
    """
    Zoom a 3D Axes by scaling its limits around their midpoints.

    Parameters
    ----------
    ax : plt.Axes
        The 3D Axes to be zoomed.
    zoom : float
        Zoom factor. Values above 1 zoom in; 1.0 leaves the Axes unchanged.
    """
    if zoom == 1.0:
        return

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
