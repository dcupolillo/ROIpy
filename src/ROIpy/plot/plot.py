from __future__ import annotations
import numpy as np
import ROIpy.core.morphology as mrph
import ROIpy.core.scanfields as sfld
from ROIpy.plot._common import check_metadata, get_scan_units
from ROIpy.plot.image import plot_image
from ROIpy.plot.morph import (
    tapered_segment, skeleton, plot_morph, plot_morph_3d)
from ROIpy.plot.scanfield import plot_scanfield, plot_scanfields_3d
from ROIpy.plot.animation import (
    update_3d_view, animate_morph_3d, animate_scanfields_3d)


# ---------------------------------------------------
# Helper functions for type checking and dispatching
# ---------------------------------------------------

def _is_non_empty_list_of(data, expected_type: type) -> bool:
    """
    Return True when data is a non-empty list of the expected type.

    Parameters
    ----------
    data : any
        The data to check.
    expected_type : type
        The expected type of the list elements.

    Returns
    -------
    bool
        True if data is a non-empty list of the expected type, False otherwise.
    """

    return (
        isinstance(data, list)
        and bool(data)
        and all(isinstance(item, expected_type) for item in data)
    )


def _is_node_data(data) -> bool:
    """
    Return True when data can be plotted as morphology data.

    Parameters
    ----------
    data : any
        The data to check.

    Returns
    -------
    bool
        True if data can be plotted as morphology data, False otherwise.
    """

    return (
        isinstance(data, (mrph.Node, mrph.NodeBundle, mrph.Neurite))
        or _is_non_empty_list_of(data, mrph.Node)
    )


def _is_roi_data(data) -> bool:
    """
    Return True when data can be plotted as ROI data.

    Parameters
    ----------
    data : any
        The data to check.

    Returns
    -------
    bool
        True if data can be plotted as ROI data, False otherwise.
    """

    return (
        isinstance(data, (sfld.Roi, sfld.ScanfieldBundle))
        or _is_non_empty_list_of(data, sfld.Roi)
    )


def _reject_empty_list(data) -> None:
    """
    Reject ambiguous empty list inputs for dispatch functions.

    Parameters
    ----------
    data : any
        The data to check.

    Raises
    ------
    TypeError
        If data is an empty list.
    """

    if isinstance(data, list) and not data:
        raise TypeError("Empty lists are not supported for plotting.")


# ---------------------------------------------------
# Generic dispatch functions
# ---------------------------------------------------

def plot(
        data: np.ndarray | mrph.Node | mrph.NodeBundle | mrph.Neurite | sfld.Roi | sfld.ScanfieldBundle | list,
        metadata: dict = None,
        projection: str = '2d',
        *args,
        **kwargs
) -> None:
    """
    Generic plotting function that dispatches to specific plotters based on data type.

    Parameters
    ----------
    data : np.ndarray | Node | NodeBundle | Neurite | Roi | ScanfieldBundle | list
        Supported inputs are image arrays, individual Node or Roi objects,
        NodeBundle or Neurite bundles, ScanfieldBundle bundles, and non-empty
        lists of only Node or only Roi objects.
        
        The data to be plotted. The accepted keyword arguments depend on
        the data type:

        | Data Type                | Main Keyword Arguments (kwargs)          |
        |-------------------------|-------------------------------------------|
        | np.ndarray              | cmap, norm, axes_labels, ax               |
        | Node/NodeBundle/Neurite | show_nodes, show_segments, cmap,          |
        |                         | show_cmap, axes_labels, nodes_kwargs,     |
        |                         | segments_kwargs, ax, axis_lims            |
        | Roi/ScanfieldBundle     | cmap, show_cbar, scan_angle, rect_kwargs, |
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
    - np.ndarray:
        >>> from ROIpy.plot.plot import plot_image
        >>> help(plot_image)
    - Node/NodeBundle/Neurite:
        >>> from ROIpy.plot.plot import plot_morph, plot_morph_3d
        >>> help(plot_morph)
    - Roi/ScanfieldBundle:
        >>> from ROIpy.plot.plot import plot_scanfield, plot_scanfields_3d
        >>> help(plot_scanfields)

    Returns
    -------
    None
    """
    if projection not in ['2d', '3d']:
        raise ValueError("Invalid projection type. Choose '2d' or '3d'.")

    _reject_empty_list(data)

    if isinstance(data, np.ndarray):
        return plot_image(data, metadata=metadata, *args, **kwargs)

    if _is_node_data(data):
        if projection == "3d":
            return plot_morph_3d(data, *args, **kwargs)
        return plot_morph(data, metadata=metadata, *args, **kwargs)

    if _is_roi_data(data):
        if projection == "3d":
            return plot_scanfields_3d(data, metadata=metadata, *args, **kwargs)
        return plot_scanfield(data, metadata=metadata, *args, **kwargs)

    raise TypeError("Unsupported data type for plotting.")


def animate(
        data: mrph.Node | mrph.NodeBundle | mrph.Neurite | sfld.Roi | sfld.ScanfieldBundle | list,
        *args,
        **kwargs
) -> None:
    """
    Generic animation function that dispatches to specific animators
    based on data type.

    Parameters
    ----------
    data : mrph.Node | mrph.NodeBundle | mrph.Neurite | sfld.Roi | sfld.ScanfieldBundle | list
        Supported inputs are individual Node or Roi objects, NodeBundle or
        Neurite bundles, ScanfieldBundle bundles, and non-empty lists of only
        Node or only Roi objects.

        The data to be animated. Accepted keyword arguments depend on
        the data type:

        | Data Type                | Main Keyword Arguments (kwargs)      |
        |-------------------------|--------------------------------------|
        | Node/NodeBundle/Neurite | show_nodes, scan_angle, axis_lims,   |
        |                         | cmap, show_cbar, elev_start,         |
        |                         | elev_end, azimut_start, azimut_end,  |
        |                         | interval, frames, save_path,         |
        |                         | axis_label, nodes_kwargs,            |
        |                         | segments_kwargs                      |
        | Roi/ScanfieldBundle     | cmap, show_cbar, scan_angle,         |
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
    - Node/NodeBundle/Neurite:
        >>> from ROIpy.plot.plot import animate_morph_3d
        >>> help(animate_morph_3d)
    - Roi/ScanfieldBundle:
        >>> from ROIpy.plot.plot import animate_scanfields_3d
        >>> help(animate_scanfields_3d)

    Returns
    -------
    None
    """
    _reject_empty_list(data)

    if _is_node_data(data):
        return animate_morph_3d(data, *args, **kwargs)

    if _is_roi_data(data):
        return animate_scanfields_3d(data, *args, **kwargs)

    raise TypeError("Unsupported data type for plotting.")
