from __future__ import annotations
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import ROIpy.core.scanfields as sfld
from ROIpy.plot._common import check_metadata
from ROIpy.plot.morph import plot_morph_3d
from ROIpy.plot.scanfield import plot_scanfields_3d


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


def animate_morph_3d(
        input_data: list,
        show_nodes: bool = False,
        scan_angle: bool = False,
        cmap: str = None,
        show_cbar: bool = False,
        elev_start: float = 30,
        elev_end: float = 30,
        azimut_start: float = 0,
        azimut_end: float = 360,
        interval: int = 100,
        frames: int = 360,
        save_path: str = None,
        flip_yz: bool = False,
        zoom: float = 1.0,
        nodes_kwargs: dict = None,
        segments_kwargs: dict = None,
        ax_kwargs: dict = None,
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
    ax_kwargs : dict, optional
        Additional keyword arguments passed to `Axes.set` when the 3D axes
        are created (e.g. title, xlabel, xticks, xlim). Default is None.

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

    ax = plot_morph_3d(
        input_data=input_data,
        show_nodes=show_nodes,
        scan_angle=scan_angle,
        cmap=cmap,
        show_cbar=show_cbar,
        azim=azimut_start,
        elev=elev_start,
        flip_yz=flip_yz,
        zoom=zoom,
        nodes_kwargs=nodes_kwargs,
        segments_kwargs=segments_kwargs,
        ax_kwargs=ax_kwargs
    )

    anim = FuncAnimation(
        ax.get_figure(),
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


def animate_scanfields_3d(
        rectangles: list,
        metadata: dict = None,
        scan_angle: bool = False,
        cmap: str = None,
        show_cbar: bool = False,
        elev_start: float = 30,
        elev_end: float = 30,
        azimut_start: float = 0,
        azimut_end: float = 360,
        interval: int = 100,
        frames: int = 60,
        save_path: str = None,
        zoom: float = 1.0,
        rect_kwargs: dict = None,
        ax_kwargs: dict = None,
):
    """
    Animate a 3D representation of scanfields with customizable
    rotation and elevation.

    Parameters
    ----------
    rectangles : list or sfld.ScanfieldBundle or sfld.Roi
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
    rect_kwargs : dict, optional
        Additional keyword arguments for customizing rectangle appearance.
        Default is None.
    ax_kwargs : dict, optional
        Additional keyword arguments passed to `Axes.set` when the 3D axes
        are created (e.g. title, xlabel, xticks, xlim). Default is None.

    Returns
    -------
    anim : matplotlib.animation.FuncAnimation
        The generated animation object.
    """
    check_metadata(metadata)

    if not isinstance(rectangles, (list, sfld.ScanfieldBundle, sfld.Roi)):
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

    # Initial plot of scanfields
    ax = plot_scanfields_3d(
        rectangles=rectangles,
        metadata=metadata,
        cmap=cmap,
        show_cbar=show_cbar,
        scan_angle=scan_angle,
        elev=elev_start,
        azim=azimut_start,
        zoom=zoom,
        rect_kwargs=rect_kwargs,
        ax_kwargs=ax_kwargs
    )
    
    # Create the animation
    anim = FuncAnimation(
        ax.get_figure(),
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
