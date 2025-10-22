""" Created on Mon Nov  6 10:29:44 2023
    @author: dcupolillo """

from pathlib import Path
import tifffile
import matplotlib.pyplot as plt
from ROIpy.core.bundles import NodeBundle, ScanfieldBundle
# from ROIpy.plot.plot import (
#     plot_image, plot_morph,
#     plot_morph_3d, animate_morph_3d,
#     plot_scanfield, plot_scanfields_3d,
#     animate_scanfields_3d)
from ROIpy.core.utils.utils import (
    stack_metadata_dictionary, parse_swc,
    parse_stack_metadata, assign_branch_degree_and_id)
from ROIpy.core.makeroi import make_roi, roi_file


class Stack:
    """
    Represents a 3D image stack (.tif format) generated with ScanImage.
    This class initializes with a path to a single-channel or
    multi-channel image stack (shape: [z, x, y] or [c, z, x, y]),
    loads the image data, and parses associated ScanImage metadata.
    It is the foundational element for processing dendritic structures.

    Example
    -------
    >>> import ROIpy as rp
    >>> path = "path/to/tiff"
    >>> stack = rp.Stack(path)  # Initialize stack
    >>> stack.plot(cmap='viridis', norm=(100, 2000))  # Visualize

    """

    def __init__(
        self,
        stack_filename: str or Path,
    ) -> None:
        """
        Initialize a Stack instance.

        Parameters
        ----------
        stack_filename : str or Path
            File name of the stack image.

        Raises
        ------
        Exception
            If the provided path is not a .tif or .tiff file.

        Returns
        -------
        None
        """

        stack_filename = Path(stack_filename)

        if stack_filename.suffix.lower() not in ['.tif', '.tiff']:
            raise Exception(
                f"Invalid file format for {stack_filename}."
                "Expected .tif or .tiff file.")

        self.imagename = stack_filename

        image_data = tifffile.imread(self.imagename)
        self.image = (
            image_data[1] if image_data.ndim == 4 else image_data)

        self.metadata = parse_stack_metadata(self.imagename)

        for key, value in self.metadata.items():
            setattr(self, key, value)

        self.folder = self.imagename.parent

    def __getattr__(
            self,
            name: str
    ):
        return self.__dict__[f"_{name}"]

    def __setattr__(
            self,
            name: str,
            value
    ):
        self.__dict__[f"_{name}"] = value

    # def plot(
    #         self,
    #         scan_angle: bool = False,
    #         ax: plt.Axes = None,
    #         norm: list or tuple = None,
    #         cmap: str = 'binary_r',
    #         z: int = None,
    #         axes_labels: bool = True,
    # ) -> plt.Axes:
    #     """
    #     Plot the max projection stack image or individual images.
# 
    #     Parameters
    #     ----------
    #     scan_angle : bool, optional
    #         If True, uses scan angle units for plotting. Default is False.
    #     ax : plt.Axes, optional
    #         Axes to plot the image on. If None, creates a new Axes.
    #     norm : list or tuple, optional
    #         Limits for the lookup table (LUT). Default is None.
    #     cmap : str, optional
    #         Colormap for the image. Default is None, which plots in grayscale.
    #     z : int, optional
    #         Specific slice to plot.
    #         If None, plots the entire stack. Default is None.
# 
    #     Returns
    #     -------
    #     plt.Axes
    #         The axes with the plotted image.
# 
    #     Example
    #     -------
    #     >>> fig, ax = plt.subplots()
    #     >>> stack.plot(cmap='viridis', norm=(100, 2000), ax=ax)
    #     """
# 
    #     return plot_image(
    #         self,
    #         scan_angle=scan_angle,
    #         ax=ax,
    #         norm=norm,
    #         cmap=cmap,
    #         z=z,
    #         axes_labels=axes_labels)

        @property
        def metadata_dict(self) -> dict:
            """
            Returns the metadata dictionary for this stack.
            """
            return self.metadata


class Morphology:
    """
    Represents neuronal morphology data, inheriting from the Stack class.

    The Morphology class processes the structure of the neuron
    from a .swc tracing file.
    Rectangular ROIs are defined and placed on this structure.

    Attributes
    ----------
    neuron : NodeBundle
        The overall neuron structure containing all compartments.
    apical : NodeBundle
        The apical dendritic compartment.
    basal : NodeBundle
        The basal dendritic compartment.
    soma : Node or None
        The cell body of the neuron.

    Example
    -------
    >>> import ROIpy as rp
    >>> from neuronpath.path import neuronpath
    >>> paths = neuronpath('date_string', cell_number)
    >>> morph = rp.Morphology(paths)
    >>> morph.plot(morph.neuron, show_nodes=True, cmap='jet', linewidth=1)
    """

    def __init__(
            self,
            swc_filename: str or Path,
            stack: Stack = None,
            output_filename: str or Path = "morphology.h5"
    ) -> None:
        """
        Initializes a neuronal object. Inherits attributes from Stack.

        swc_filename : str or Path
            File name of the morphological reconstruction.
        stack : Stack, optional
            Instance of the Stack containing metadata. Default is None.
        output_filename: str or Path
            File name where morphology data are stored in h5 format.
            Default is `morphology.h5`.

        Raises
        ------
        Exception
            If the tracing file is not in .swc format.

        Returns
        -------
        None
        """

        swc_filename = Path(swc_filename)
        output_filename = Path(output_filename)

        if swc_filename.suffix.lower() != '.swc':
            raise Exception(
                f"Invalid file format for {swc_filename}."
                "Expected .swc")

        if not output_filename.suffix == ".h5":
            raise ValueError(
                "Output filename needs to be in .h5 format")

        self.filename = swc_filename
        self.output_filename = Path(self.filename.parent / output_filename)

        if stack:
            self.metadata = stack_metadata_dictionary(**stack.metadata)
        else:
            self.metadata = stack_metadata_dictionary()

        self._has_stack = True if stack else False

        for key, value in self.metadata.items():
            setattr(self, key, value)

        self.neuron = self._make_nodebundle()

        self.apical = NodeBundle(
            [node for node in self.neuron
             if node._type == 'apical dendrite'])

        self.basal = NodeBundle(
            [node for node in self.neuron
             if node._type == 'basal dendrite'])

        try:
            self.soma = [
                node for node in self.neuron
                if node._type == 'soma'][0]  # so it's not a list
        except IndexError:
            # handles cases where only branches are given
            self.soma = []

        self._branches_ids = list(
            set([node.branch_id for node in self.neuron]))
        self.n_branches = len(self._branches_ids)

    def _make_nodebundle(self) -> list:
        """
        Loads a bundle if exists, otherwise creates it.

        Returns
        -------
        neuron : NodeBundle
            list of separated branches.
        """

        files = list(self.filename.parent.iterdir())
        nodebundle_filename = next(
            (file for file in files
             if file.stem == self.output_filename.stem),
            None)

        if nodebundle_filename is not None and nodebundle_filename.exists():
            return NodeBundle.load_from_h5(nodebundle_filename)

        nodes_list = parse_swc(self.filename, self.metadata)
        neuron = NodeBundle(nodes_list)

        assign_branch_degree_and_id(neuron)
        neuron.save_to_h5(self.output_filename)

        return neuron

    # def plot(
    #         self, 
    #         input_data: object,
    #         show_segments: bool = True,
    #         show_nodes: bool = False,
    #         nodes_size: float = 10,
    #         z: int = None,
    #         ax: plt.Axes = None,
    #         axis_lims: list = None,
    #         cmap: str = 'viridis',
    #         show_cmap: bool = True,
    #         scan_angle: bool = False,
    #         color: str = "black",
    #         linewidth: int = None
    # ) -> plt.Axes:
    #     """
    #     Plot the neuronal morphology structure.
# 
    #     Parameters
    #     ----------
    #     input_data : NodeBundle or list(Node)
    #         The data to plot (e.g., apical, basal, or full neuron structure).
    #     show_segments : bool, optional
    #         Plot lines connecting the nodes (default is True).
    #     show_nodes : bool, optional
    #         Plot individual nodes as scatter points (default is False).
    #     z : int, optional
    #         Specific z-plane to plot (default is None for all).
    #     ax : plt.Axes, optional
    #         Matplotlib axes to plot on (default is None for new axes).
    #     axis_lims : list, optional
    #         Axes bounds as [xmin, xmax, ymin, ymax] (default is None).
    #     cmap : str, optional
    #         Colormap for z-position visualization (default is None).
    #     show_cmap : bool, optional
    #         Show the colormap legend (default is True).
    #     scan_angle : bool, optional
    #         Plot using angle units (default is False).
    #     color : str, optional
    #         Line color (default is black).
    #     linewidth : int, optional
    #         Line width for connecting segments (default is 1).
# 
    #     Returns
    #     -------
    #     plt.Axes
    #         The axes with the plotted morphology.
    #     """
# 
    #     return plot_morph(
    #         self,
    #         input_data,
    #         show_segments=show_segments,
    #         show_nodes=show_nodes,
    #         nodes_size=nodes_size,
    #         z=z,
    #         ax=ax,
    #         axis_lims=axis_lims,
    #         cmap=cmap,
    #         show_cmap=show_cmap,
    #         scan_angle=scan_angle,
    #         color=color,
    #         linewidth=linewidth)
# 
    #     @property
    #     def metadata_dict(self) -> dict:
    #         """
    #         Returns the metadata dictionary for this morphology.
    #         """
    #         return self.metadata
# 
    # def plot_3d(
    #         self,
    #         input_data: object,
    #         show_nodes: bool = False,
    #         ax: plt.Axes = None,
    #         axis_lims: list = None,
    #         cmap: str = "vridis",
    #         scan_angle: bool = False,
    #         color: str = "black",
    #         linewidth: int = None,
    #         azim: float = 45,
    #         elev: float = 30,
    # ) -> plt.Axes:
    #     """
    #     Plot the neuronal morphology in 3D.
# 
    #     Parameters are similar to the `plot` method, with added `azim`
    #     and `elev` for camera angle control.
# 
    #     azim : float, optional
    #         Azimuthal angle for the 3D plot view (default is 45 degrees).
    #     elev : float, optional
    #         Elevation angle for the 3D plot view (default is 30 degrees).
# 
    #     Returns
    #     -------
    #     plt.Axes
    #         The axes with the plotted 3D morphology.
    #     """
# 
    #     return plot_morph_3d(
    #         input_data,
    #         show_nodes=show_nodes,
    #         scan_angle=scan_angle,
    #         color=color,
    #         linewidth=linewidth,
    #         axis_lims=axis_lims,
    #         cmap=cmap,
    #         azim=azim,
    #         elev=elev,
    #         ax=ax)
# 
    # def animate_3d(
    #         self,
    #         input_data: object,
    #         show_nodes: bool = False,
    #         axis_lims: list = None,
    #         cmap: str = "viridis",
    #         scan_angle: bool = False,
    #         color: str = "black",
    #         linewidth: int = None,
    #         elev_start: float = 30,
    #         elev_end: float = 30,
    #         azimut_start: float = 0,
    #         azimut_end: float = 360,
    #         interval: int = 50,
    #         frames: int = 360,
    #         save_path: str or Path = None,
    #         axis_label: bool = False,
    # ) -> plt.Axes:
    #     """
    #     Animate the neuronal morphology in 3D.
# 
    #     Parameters are similar to the `plot` method, with the addition of:
# 
    #     elev_start : float, optional
    #         Starting elevation angle for the animation (default is 30 degrees).
    #     elev_end : float, optional
    #         Ending elevation angle for the animation (default is 30 degrees).
    #     azimut_start : float, optional
    #         Starting azimuthal angle for the animation (default is 0 degrees).
    #     azimut_end : float, optional
    #         Ending azimuthal angle for the animation (default is 360 degrees).
    #     interval : int, optional
    #         Time interval (in ms) between animation frames (default is 50).
    #     frames : int, optional
    #         Number of frames in the animation (default is 360).
    #     save_path : str or Path, optional
    #         File path to save the animation (default is None, no save).
    #     axis_label : bool, optional
    #         Whether to include axis labels in the animation (default is False).
# 
    #     Returns
    #     -------
    #     plt.Axes
    #         The axes with the animated 3D morphology.
    #     """
# 
    #     return animate_morph_3d(
    #         input_data,
    #         show_nodes=show_nodes,
    #         scan_angle=scan_angle,
    #         color=color,
    #         linewidth=linewidth,
    #         axis_lims=axis_lims,
    #         cmap=cmap,
    #         elev_start=elev_start,
    #         elev_end=elev_end,
    #         azimut_start=azimut_start,
    #         azimut_end=azimut_end,
    #         interval=interval,
    #         frames=frames,
    #         save_path=save_path,
    #         axis_label=axis_label,)


class Scanfields:

    """
    A class to create and manage scanfields (rectangular ROIs) for imaging.

    This class uses neuronal morphology data to define scanfields based on
    imaging and experimental parameters. It includes methods for visualization,
    ROI generation, and exporting data in compatible formats.

    Raises
    ------
    KeyError
        If the passed Morphology was not initiated using a Stack.

    Example
    -------
    >>> import ROIpy as rp
    >>> sf = rp.Scanfield(morphology)
    """

    def __init__(
            self,
            morphology: Morphology,
            output_filename: str or Path = "scanfields.h5",
            desired_framerate: int = 16,
            elongating_factor: float = 1.33,
            dim_ratio_threshold: float = 3.5,
            overlap_threshold: float = 0.90,
            wavelength: int = 830,
            fill_fraction: float = 0.9,
            frame_flyback: float = 0.001,
            fly_to_line: float = 0.001,
            numerical_aperture: float = 0.8,
            sampling_rate: float = 1.250 * 1e6,
            sampling_rate_ctl: float = 156250,
            pixel_bin_factor: int = 4,
            filtering_radius: tuple = (50.0, 20.0),
            framerate_delta_threshold: float = 0.3,
    ) -> None:
        """
        Initialize a Scanfields instance with given image and tracing paths,
        and optional parameters.

        Parameters
        ----------
        morphology : Morphology
            Morphology element containing metadata.
        output_filename: str or Path
            File name where scanfields data are stored in h5 format.
            Default is `scanfields.h5`.
        desired_framerate : int, optional
            Imaging framerate in Hz (default: 16).
        elongating_factor : float, optional
            ROI elongation factor along the longitudinal axis (default: 1.33).
        dim_ratio_threshold : float, optional
            Width-to-height ratio threshold for ROI design (default: 3.5).
        overlap_threshold : float, optional
            Overlap threshold for ROI merging (default: 0.90).
        wavelength : int, optional
            Laser wavelength in nanometers (default: 830 nm).
        fill_fraction : float, optional
            Fraction of active acquisition time per line (default: 0.9).
        frame_flyback : float, optional
            Time for mirrors to return to
            the frame start position (default: 0.001 s).
        fly_to_line : float, optional
            Time for scanner movement between ROIs (default: 0.001 s).
        numerical_aperture : float, optional
            Objective lens numerical aperture (default: 0.8).
        sampling_rate : float, optional
            ADC sampling rate in Hz (default: 1.25 MHz).
        sampling_rate_ctl : float, optional
            Control sampling rate in Hz (default: 156,250).
        pixel_bin_factor : int, optional
            ADC samples averaged per pixel (default: 4).
        filtering_radius : tuple, optional
            Spatial filtering radii in micrometers (default: (50.0, 20.0)).
        framerate_delta_threshold : float, optional
            Allowed framerate deviation (default: 0.3).

        Returns
        -------
        None
        """

        if not morphology._has_stack:
            raise KeyError(
                "Morphology needs to be initiated using a Stack "
                "to create a Scanfields object")

        if not Path(output_filename).suffix == ".h5":
            raise ValueError(
                "Output filename needs to be in .h5 format")

        self._morph = morphology
        self.soma = self._morph.soma
        self.output_filename = Path(
            self._morph.filename.parent / output_filename)

        self.metadata = self._morph.metadata

        self.desired_framerate = desired_framerate
        self.elongating_factor = elongating_factor
        self.dim_ratio_threshold = dim_ratio_threshold
        self.overlap_threshold = overlap_threshold
        self.wavelength = wavelength
        self.fill_fraction = fill_fraction
        self.frame_flyback = frame_flyback
        self.fly_to_line = fly_to_line
        self.numerical_aperture = numerical_aperture

        self.sampling_rate = sampling_rate
        self.sampling_rate_ctl = sampling_rate_ctl
        self.pixel_bin_factor = pixel_bin_factor
        self.dwell_time = self.pixel_bin_factor / self.sampling_rate
        self.filtering_radius = filtering_radius
        self.framerate_delta_threshold = framerate_delta_threshold

        self.objective_resolution = self._morph.objective_resolution
        self.zs = self._morph.zs

        # Abbe's equation for diffraction limited spot
        # Rayleigh criterion: distance required to differentiate 2 structures
        self.optimal_pix_um_ratio = (1 / (
            ((0.61 * self.wavelength / self.numerical_aperture)
             * 1e-3) / 2))

        self.neuron = self._make_scanfieldbundle()

        self.apical = ScanfieldBundle(
            [[rect for rect in z if rect.compartment == 'apical dendrite']
             for z in self.neuron if any(
                rect.compartment == 'apical dendrite' for rect in z)])

        self.basal = ScanfieldBundle(
            [[rect for rect in z if rect.compartment == 'basal dendrite']
             for z in self.neuron if any(
                rect.compartment == 'basal dendrite' for rect in z)])

    @property
    def scan_params(self) -> dict:
        """
        Returns a dictionary of all scan/imaging parameters
        for this Scanfields instance.
        """
        return {
            'desired_framerate': self.desired_framerate,
            'elongating_factor': self.elongating_factor,
            'dim_ratio_threshold': self.dim_ratio_threshold,
            'overlap_threshold': self.overlap_threshold,
            'wavelength': self.wavelength,
            'fill_fraction': self.fill_fraction,
            'frame_flyback': self.frame_flyback,
            'fly_to_line': self.fly_to_line,
            'numerical_aperture': self.numerical_aperture,
            'sampling_rate': self.sampling_rate,
            'sampling_rate_ctl': self.sampling_rate_ctl,
            'pixel_bin_factor': self.pixel_bin_factor,
            'dwell_time': self.dwell_time,
            'filtering_radius': self.filtering_radius,
            'framerate_delta_threshold': self.framerate_delta_threshold,
            'objective_resolution': self.objective_resolution,
            'zs': self.zs,
            'optimal_pix_um_ratio': self.optimal_pix_um_ratio,
        }

    def _make_scanfieldbundle(self) -> list:

        files = list(self._morph.filename.parent.iterdir())

        scanfieldbundle_filename = next(
            (file for file in files
             if file.stem == self.output_filename.stem),
            None)

        if (scanfieldbundle_filename is not None
                and scanfieldbundle_filename.exists()):
            return ScanfieldBundle.load_from_h5(scanfieldbundle_filename)

        neuron = ScanfieldBundle(self.create_roi(self._morph.neuron))

        # Eventually sort the ROIs by layer index
        sorted_neuron = sorted(
            neuron,
            key=lambda layer: layer[0].z_ind
            if layer else float('inf'))

        for layer in sorted_neuron:
            layer.sort(key=lambda roi: roi.z_ind)

        neuron = ScanfieldBundle(sorted_neuron)
        neuron.save_to_h5(self.output_filename)

        return neuron

    def __getattr__(
            self,
            name: str):
        return self.__dict__[f"_{name}"]

    def __setattr__(
            self,
            name: str,
            value):
        self.__dict__[f"_{name}"] = value

    def __len__(self) -> int:
        return sum([len(zplane) for zplane in self.neuron])

    def create_roi(
            self,
            input_data: Morphology
    ) -> list:
        """
        Create rectangular ROIs based on morphology nodes.

        Parameters
        ----------
        input_data : Morphology
            Morphology data to be subdivided into ROIs.

        Returns
        -------
        list
            Nested list of ROI objects.
        """

        return make_roi.make_roi(self, input_data)

    # ef plot(
    #        self,
    #        input_roi: ScanfieldBundle,
    #        ax: plt.Axes = None,
    #        axis_lims: list = None,
    #        cmap: str = None,
    #        show_cmap: bool = True,
    #        scan_angle: bool = False,
    #        edgecolor: str = "black",
    #        facecolor: str = 'none',
    #        linewidth: int = 1,
    #        alpha: float = .5,
    #  -> plt.Axes:
    #    """
    #    Plot the scanfields as rotated rectangles

    #    Parameters
    #    ----------
    #    input_roi : ScanfieldBundle
    #        structure to plot.
    #    ax : plt.Axes.ax, optional
    #        if specified, plots in the indicated plot. The default is None.
    #        The default is False.
    #    axis_lims : list, optional
    #        If specified, plot will be bounded to limits.
    #    cmap : str, optional
    #        facecolor colormap of the rectangles based on their Z position.
    #        The default is None.
    #    show_cmap : bool, optional
    #        If True, shows the colormap legend. The default is True.
    #    scan_angle : bool, optional
    #        if True, plots in units of angle degrees. The default is False.
    #    edgecolor : str, optional
    #        color of rectangles edge. The default is black.
    #    linewidth : int, optional
    #        specifies the width of rectangles edge. The default is 1.
    #    alpha : float, optional
    #        The set alpha value for the Roi's edgecolor. Default is 0.5.

    #    Returns
    #    -------
    #    plt.Axes.ax
    #        Plot of the scanfields.

    #    Example usage
    #    -------
    #    sf.plot(sf.neuComp, scanAngle = True)

    #    """

    #    return plot_scanfield(
    #        self._morph,
    #        input_roi,
    #        ax=ax,
    #        axis_lims=axis_lims,
    #        cmap=cmap,
    #        show_cmap=show_cmap,
    #        edgecolor=edgecolor,
    #        facecolor=facecolor,
    #        linewidth=linewidth,
    #        scan_angle=scan_angle,
    #        alpha=alpha)

    # ef plot_3d(
    #        self,
    #        input_roi: ScanfieldBundle,
    #        ax: plt.Axes = None,
    #        cmap: str = None,
    #        scan_angle: bool = False,
    #        edgecolor: str = "black",
    #        linewidth: int = 1,
    #        alpha: float = 0.5,
    #        elev: int or float = None,
    #        azim: int or float = None,
    #        zoom: int or float = None,
    #  -> plt.Axes:
    #    """
    #    Plot the scanfields in 3D with customizable
    #    camera angles and other options.

    #     Parameters are similar to the `plot` method, with added `azim`
    #     and `elev` for camera angle control.

    #     azim : float, optional
    #         Azimuthal angle for the 3D plot view.
    #         Default is None for default Matplotlib view.
    #     elev : float, optional
    #         Elevation angle for the 3D plot view.
    #         Default is None for default Matplotlib view.

    #    Returns
    #    -------
    #    plt.Axes
    #        The 3D Matplotlib axes containing the plotted scanfields.

    #    Example
    #    -------
    #    >>> sf.plot_3d(sf.neuComp, azim=45, elev=30, cmap='viridis')
    #    """

    #    return plot_scanfields_3d(
    #        self._morph,
    #        input_roi,
    #        ax=ax,
    #        cmap=cmap,
    #        edgecolor=edgecolor,
    #        linewidth=linewidth,
    #        alpha=alpha,
    #        scan_angle=scan_angle,
    #        elev=elev,
    #        azim=azim,
    #        zoom=zoom)

    # ef animate_3d(
    #        self,
    #        rectangles: ScanfieldBundle,
    #        elev_start: float = 40,
    #        elev_end: float = -40,
    #        azimut_start: float = 0,
    #        azimut_end: float = 360,
    #        frames: int = 360,
    #        interval: float = 50,
    #        cmap: str = None,
    #        edgecolor: str = "black",
    #        linewidth: int = 1,
    #        alpha: float = 1.,
    #        scan_angle: bool = False,
    #        save_path: str = None,
    #        zoom: float = None,
    #        axis_label: bool = False
    #  -> None:
    #    """
    #    Animate the scanfields in 3D with dynamic camera angles.

    #    Parameters are similar to the `plot` method, with the addition of:

    #   elev_start : float, optional
    #       Starting elevation angle for the animation. Default is 40 degrees.
    #   elev_end : float, optional
    #       Ending elevation angle for the animation. Default is -40 degrees.
    #   azimut_start : float, optional
    #       Starting azimuthal angle for the animation. Default is 0 degrees.
    #   azimut_end : float, optional
    #       Ending azimuthal angle for the animation. Default is 360 degrees.
    #   frames : int, optional
    #       Total number of frames in the animation. Default is 360.
    #   interval : float, optional
    #       Time interval (in milliseconds) between frames. Default is 50 ms.
    #   save_path : str, optional
    #       Path to save the animation. Default is None (no save).
    #   zoom : float, optional
    #       Zoom factor for the animation. Default is None.
    #   axis_label : bool, optional
    #       If True, includes axis labels in the animation. Default is False.
    #    """

    #    return animate_scanfields_3d(
    #        self._morph,
    #        rectangles,
    #        elev_start=elev_start,
    #        elev_end=elev_end,
    #        azimut_start=azimut_start,
    #        azimut_end=azimut_end,
    #        frames=frames,
    #        interval=interval,
    #        cmap=cmap,
    #        edgecolor=edgecolor,
    #        linewidth=linewidth,
    #        alpha=alpha,
    #        scan_angle=scan_angle,
    #        save_path=save_path,
    #        zoom=zoom,
    #        axis_label=axis_label
    #    )

    def save(
            self,
            input_data: ScanfieldBundle,
            folder_path: str,
            structure_type: str = None
    ) -> None:
        """
        Save the generated ROIs in a format compatible with ScanImage.

        Parameters
        ----------
        input_data : ScanfieldBundle
            The scanfield bundle to save as `.roi` files.
        folder_path : str
            Destination directory for the `.roi` files.
        structure_type : str, optional
            Type of structure to save
            ('neuron', 'apical', or 'basal'). Default is None.

        Raises
        ------
        ValueError
            If `structure_type` is not one of ['neuron', 'apical', 'basal'].

        Returns
        -------
        None

        Example
        -------
        >>> sf.save(sf.neuComp, 'path/to/save', structure_type='neuron')
        """
        if structure_type not in ['neuron', 'apical', 'basal']:
            raise ValueError('Invalid structure_type')

        return roi_file.generate_roi_files(
            self,
            input_data,
            folder_path,
            structure_type)

    def count(
            self,
            inputData: ScanfieldBundle
    ) -> None:
        """
        Print the total number of rectangles in the scanfield bundle.

        Parameters
        ----------
        inputData : ScanfieldBundle
            The bundle of scanfields to count.

        Returns
        -------
        None

        Example
        -------
        >>> sf.count(sf.neuComp)
        Total rectangles: 128
        """

        print(sum(len(z) for z in inputData))
