from __future__ import annotations
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
from ROIpy.plot._common import check_metadata, get_scan_units


def plot_image(
        image: np.ndarray,
        metadata: dict = None,
        scan_angle: bool = False,
        ax: plt.Axes = None,
        norm: tuple | list = None,
        cmap: str = "binary_r",
        axes_labels: bool = True,
        **kwargs
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
        ax.imshow(img, extent=extent, cmap=cmap, **kwargs)

    elif isinstance(norm, (list, tuple)):
        min_value, max_value = norm
        norm = Normalize(vmin=min_value, vmax=max_value)
        ax.imshow(img, extent=extent, cmap=cmap, norm=norm, **kwargs)

    else:
        raise KeyError("'norm' should be a list or a tuple")
