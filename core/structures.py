""" Created on Mon Nov  6 10:29:44 2023
    @author: dcupolillo """

from pathlib import Path
import tifffile
import matplotlib.pyplot as plt

from ROIpy.core.bundles import NodeBundle, ScanfieldBundle
from ROIpy.plot.plot import (
    plot_image, plot_morph,
    plot_morph_3d, animate_morph_3d,
    plot_scanfield, plot_scanfields_3d,
    animate_scanfields_3d,
    plot_morph_scanned_highlight)

from ROIpy.core.utils.utils import (
    parse_swc, parse_stack_metadata, assign_branch_degree)
from ROIpy.core.makeroi import make_roi, roi_file
from ROIpy.assets.palette import dim

from neuronpath.path import NeuronPath


class Stack():
    """
    Represents a 3D image stack (.tif format) generated with ScanImage.
    This class initializes with a path to a single-channel or
    multi-channel image stack (shape: [z, x, y] or [c, z, x, y]),
    loads the image data, and parses associated ScanImage metadata.
    It is the foundational element for processing dendritic structures.

    Example
    -------
    >>> import ROIpy as rp
    >>> from neuronpath.path import neuronpath
    >>> paths = neuronpath('date_string', cell_number)
    >>> stack = rp.Stack(paths)  # Initialize stack
    >>> stack.plot(cmap='viridis', norm=(100, 2000))  # Visualize

    """

    def __init__(
        self,
        paths: NeuronPath
    ) -> None:
        """
        Initialize a Stack instance.

        Parameters
        ----------
        paths : NeuronPath
            Object manager for stored data. The stack image is defined
            under the object.stackpath attribute.

        Raises
        ------
        Exception
            If the provided path is not a .tif or .tiff file.

        Returns
        -------
        None
        """

        if not (isinstance(paths.stackpath, Path)
                and paths.stackpath.suffix.lower() in ('.tif', '.tiff')):
            raise Exception(
                f"Invalid file format for {paths.stackpath}."
                "Expected .tif or .tiff file.")

        self.paths = paths

        self.imagename = paths.stackpath

        image_data = tifffile.imread(self.imagename)
        self.image = (
            image_data[1] if image_data.ndim == 4 else image_data)

        metadata = parse_stack_metadata(self.imagename)
        for key, value in metadata.items():
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

    def plot(
            self,
            scan_angle: bool = False,
            ax: plt.Axes = None,
            norm: list or tuple = None,
            cmap: str = None,
            z: int = None
    ) -> plt.Axes:
        """
        Plot the max projection stack image or individual images.

        Parameters
        ----------
        scan_angle : bool, optional
            If True, uses scan angle units for plotting. Default is False.
        ax : plt.Axes, optional
            Axes to plot the image on. If None, creates a new Axes.
        norm : list or tuple, optional
            Limits for the lookup table (LUT). Default is None.
        cmap : str, optional
            Colormap for the image. Default is None, which plots in grayscale.
        z : int, optional
            Specific slice to plot.
            If None, plots the entire stack. Default is None.

        Returns
        -------
        plt.Axes
            The axes with the plotted image.

        Example
        -------
        >>> fig, ax = plt.subplots()
        >>> stack.plot(cmap='viridis', norm=(100, 2000), ax=ax)
        """

        return plot_image(
            self,
            scan_angle=scan_angle,
            ax=ax,
            norm=norm,
            cmap=cmap,
            z=z)


class Morphology(Stack):
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
            paths: NeuronPath,

    ) -> None:
        """
        Initializes a neuronal object. Inherits attributes from Stack.

        paths : NeuronPath
            Object manager for stored data. The stack image is defined
            under the object.stackpath attribute.

        Raises
        ------
        Exception
            If the tracing file is not in .swc format.

        Returns
        -------
        None
        """

        if not (isinstance(paths.tracepath, Path) or
                paths.tracepath.suffix.lower() != '.swc'):
            raise Exception(
                f"Invalid file format for {paths.tracepath}."
                "Expected .swc file.")

        super().__init__(paths)

        self.tracename = paths.tracepath

        if paths.morphology.exists():
            self.neuron = NodeBundle.load_from_h5(paths.morphology)
        else:
            self.neuron = NodeBundle(parse_swc(
                self.tracename,
                self.objective_resolution,
                self.zs,
                self.pixel_to_ref_transform))
            assign_branch_degree(self.neuron)
            self.neuron.save_to_h5(paths.morphology)

        self.apical = NodeBundle(
            [node for node in self.neuron
             if node._type == 'apical dendrite'])

        self.basal = NodeBundle(
            [node for node in self.neuron
             if node._type == 'basal dendrite'])

        self.soma = next(
            (node for node in self.neuron if node._type == 'soma'), None)

    def plot(
            self,
            input_data,
            show_segments: bool = True,
            show_nodes: bool = False,
            z: int = None,
            ax: plt.Axes = None,
            axis_lims: list = None,
            cmap: str = None,
            scan_angle: bool = False,
            color: str = "black",
            linewidth: int = 1
    ) -> plt.Axes:
        """
        Plot the neuronal morphology structure.

        Parameters
        ----------
        input_data : NodeBundle or Node
            The data to plot (e.g., apical, basal, or full neuron structure).
        show_segments : bool, optional
            Plot lines connecting the nodes (default is True).
        show_nodes : bool, optional
            Plot individual nodes as scatter points (default is False).
        z : int, optional
            Specific z-plane to plot (default is None for all).
        ax : plt.Axes, optional
            Matplotlib axes to plot on (default is None for new axes).
        axis_lims : list, optional
            Axes bounds as [xmin, xmax, ymin, ymax] (default is None).
        cmap : str, optional
            Colormap for z-position visualization (default is None).
        scan_angle : bool, optional
            Plot using angle units (default is False).
        color : str, optional
            Line color (default is `dim.black.hex`).
        linewidth : int, optional
            Line width for connecting segments (default is 1).

        Returns
        -------
        plt.Axes
            The axes with the plotted morphology.
        """

        return plot_morph(
            self,
            input_data,
            show_segments=show_segments,
            show_nodes=show_nodes,
            z=z,
            ax=ax,
            axis_lims=axis_lims,
            cmap=cmap,
            scan_angle=scan_angle,
            color=color,
            linewidth=linewidth)

    def plot_3d(
            self,
            input_data,
            show_segments: bool = True,
            show_nodes: bool = False,
            z: int = None,
            ax: plt.Axes = None,
            axis_lims: list = None,
            cmap: str = None,
            scan_angle: bool = False,
            color: str = "black",
            linewidth: int = 1,
            azim: float = 45,
            elev: float = 30,
    ) -> plt.Axes:
        """
        Plot the neuronal morphology in 3D.

        Parameters are similar to the `plot` method, with added `azim`
        and `elev` for camera angle control.

        azim : float, optional
            Azimuthal angle for the 3D plot view (default is 45 degrees).
        elev : float, optional
            Elevation angle for the 3D plot view (default is 30 degrees).

        Returns
        -------
        plt.Axes
            The axes with the plotted 3D morphology.
        """

        return plot_morph_3d(
            input_data,
            show_nodes=show_nodes,
            scan_angle=scan_angle,
            color=color,
            linewidth=linewidth,
            axis_lims=axis_lims,
            cmap=cmap,
            azim=azim,
            elev=elev,
            ax=ax)

    def animate_3d(
            self,
            input_data,
            show_nodes: bool = False,
            axis_lims: list = None,
            cmap: str = None,
            scan_angle: bool = False,
            color: str = dim.black.hex,
            linewidth: int = 1,
            elev_start: float = 30,
            elev_end: float = 30,
            azimut_start: float = 0,
            azimut_end: float = 360,
            interval: int = 50,
            frames: int = 360,
            save_path: str or Path = None,
            axis_label: bool = False,
    ) -> plt.Axes:
        """
        Animate the neuronal morphology in 3D.

        Parameters are similar to the `plot` method, with the addition of:

        elev_start : float, optional
            Starting elevation angle for the animation (default is 30 degrees).
        elev_end : float, optional
            Ending elevation angle for the animation (default is 30 degrees).
        azimut_start : float, optional
            Starting azimuthal angle for the animation (default is 0 degrees).
        azimut_end : float, optional
            Ending azimuthal angle for the animation (default is 360 degrees).
        interval : int, optional
            Time interval (in ms) between animation frames (default is 50).
        frames : int, optional
            Number of frames in the animation (default is 360).
        save_path : str or Path, optional
            File path to save the animation (default is None, no save).
        axis_label : bool, optional
            Whether to include axis labels in the animation (default is False).

        Returns
        -------
        plt.Axes
            The axes with the animated 3D morphology.
        """

        return animate_morph_3d(
            input_data,
            show_nodes=show_nodes,
            scan_angle=scan_angle,
            color=color,
            linewidth=linewidth,
            axis_lims=axis_lims,
            cmap=cmap,
            elev_start=elev_start,
            elev_end=elev_end,
            azimut_start=azimut_start,
            azimut_end=azimut_end,
            interval=interval,
            frames=frames,
            save_path=save_path,
            axis_label=axis_label,)


class Scanfields(Morphology):

    """
    A class to create and manage scanfields (rectangular ROIs) for imaging,
    inheriting from the Morphology class.

    This class uses neuronal morphology data to define scanfields based on
    imaging and experimental parameters. It includes methods for visualization,
    ROI generation, and exporting data in compatible formats.

    Example
    -------
    >>> import ROIpy as rp
    >>> from neuronpath.path import neuronpath
    >>> paths = neuronpath('date_string', cell_number)
    >>> sf = rp.Scanfield(paths)
    """

    def __init__(
            self,
            paths: NeuronPath,
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
        paths : NeuronPath
            Paths to the image and tracing files.
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

        super().__init__(paths)

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

        # Abbe's equation for diffraction limited spot
        # Rayleigh criterion: distance required to differentiate 2 structures
        self.optimal_pix_um_ratio = (1 / (
            ((0.61 * self.wavelength / self.numerical_aperture)
             * 1e-3) / 2))

        if paths.scanfields.exists():
            self.neuComp = ScanfieldBundle.load_from_h5(paths.scanfields)
        else:
            self.neuComp = ScanfieldBundle(self.create_roi(self.neuron))
            self.neuComp.save_to_h5(paths.scanfields)

        self.apiComp = ScanfieldBundle(
            [[rect for rect in z if rect.compartment == 'apical dendrite']
             for z in self.neuComp if any(
                rect.compartment == 'apical dendrite' for rect in z)])

        self.basComp = ScanfieldBundle(
            [[rect for rect in z if rect.compartment == 'basal dendrite']
             for z in self.neuComp if any(
                rect.compartment == 'basal dendrite' for rect in z)])

    def __getattr__(
            self,
            name: str):
        return self.__dict__[f"_{name}"]

    def __setattr__(
            self,
            name: str,
            value):
        self.__dict__[f"_{name}"] = value

    def create_roi(
            self,
            input_data: Morphology
    ) -> ScanfieldBundle:
        """
        Create rectangular ROIs based on morphology nodes.

        Parameters
        ----------
        input_data : Morphology
            Morphology data to be subdivided into ROIs.

        Returns
        -------
        ScanfieldBundle
            Nested list of ROI objects.
        """

        return make_roi.make_roi(self, input_data)

    def plot(
            self,
            input_roi: ScanfieldBundle,
            ax: plt.Axes = None,
            axis_lims: list = None,
            cmap: str = None,
            scan_angle: bool = False,
            edgecolor: str = dim.black.hex,
            linewidth: int = 1
    ) -> plt.Axes:
        """
        Plot the scanfields as rotated rectangles

        Parameters
        ----------
        input_roi : ScanfieldBundle
            structure to plot.
        ax : plt.Axes.ax, optional
            if specified, plots in the indicated plot. The default is None.
            The default is False.
        axis_lims : list, optional
            If specified, plot will be bounded to limits.
        cmap : str, optional
            facecolor colormap of the rectangles based on their Z position.
            The default is None.
        scan_angle : bool, optional
            if True, plots in units of angle degrees. The default is False.
        edgecolor : str, optional
            color of rectangles edge. The default is dim.black.hex.
        linewidth : int, optional
            specifies the width of rectangles edge. The default is 1.

        Returns
        -------
        plt.Axes.ax
            Plot of the scanfields.

        Example usage
        -------
        sf.plot(sf.neuComp, scanAngle = True)

        """

        return plot_scanfield(
            self,
            input_roi,
            ax=ax,
            axis_lims=axis_lims,
            cmap=cmap,
            edgecolor=edgecolor,
            linewidth=linewidth,
            scan_angle=scan_angle)

    def plot_3d(
            self,
            input_roi: ScanfieldBundle,
            ax: plt.Axes = None,
            cmap: str = None,
            scan_angle: bool = False,
            edgecolor: str = dim.black.hex,
            linewidth: int = 1,
            elev: int or float = None,
            azim: int or float = None,
            zoom: int or float = None,
    ) -> plt.Axes:
        """
        Plot the scanfields in 3D with customizable
        camera angles and other options.

         Parameters are similar to the `plot` method, with added `azim`
         and `elev` for camera angle control.

         azim : float, optional
             Azimuthal angle for the 3D plot view.
             Default is None for default Matplotlib view.
         elev : float, optional
             Elevation angle for the 3D plot view.
             Default is None for default Matplotlib view.

        Returns
        -------
        plt.Axes
            The 3D Matplotlib axes containing the plotted scanfields.

        Example
        -------
        >>> sf.plot_3d(sf.neuComp, azim=45, elev=30, cmap='viridis')
        """

        return plot_scanfields_3d(
                self,
                input_roi,
                ax=ax,
                cmap=cmap,
                edgecolor=edgecolor,
                linewidth=linewidth,
                scan_angle=scan_angle,
                elev=elev,
                azim=azim,
                zoom=zoom)

    def animate_3d_scanfields(
            self,
            rectangles: ScanfieldBundle,
            elev_start: float = 40,
            elev_end: float = -40,
            azimut_start: float = 0,
            azimut_end: float = 360,
            frames: int = 360,
            interval: float = 50,
            cmap: str = None,
            edgecolor: str = dim.black.hex,
            linewidth: int = 1,
            alpha: float = 1.,
            scan_angle: bool = False,
            save_path: str = None,
            zoom: float = None,
            axis_label: bool = False
    ) -> None:
        """
        Animate the scanfields in 3D with dynamic camera angles.

        Parameters are similar to the `plot` method, with the addition of:

       elev_start : float, optional
           Starting elevation angle for the animation. Default is 40 degrees.
       elev_end : float, optional
           Ending elevation angle for the animation. Default is -40 degrees.
       azimut_start : float, optional
           Starting azimuthal angle for the animation. Default is 0 degrees.
       azimut_end : float, optional
           Ending azimuthal angle for the animation. Default is 360 degrees.
       frames : int, optional
           Total number of frames in the animation. Default is 360.
       interval : float, optional
           Time interval (in milliseconds) between frames. Default is 50 ms.
       save_path : str, optional
           Path to save the animation. Default is None (no save).
       zoom : float, optional
           Zoom factor for the animation. Default is None.
       axis_label : bool, optional
           If True, includes axis labels in the animation. Default is False.
        """

        return animate_scanfields_3d(
            self,
            rectangles,
            elev_start=elev_start,
            elev_end=elev_end,
            azimut_start=azimut_start,
            azimut_end=azimut_end,
            frames=frames,
            interval=interval,
            cmap=cmap,
            edgecolor=edgecolor,
            linewidth=linewidth,
            alpha=alpha,
            scan_angle=scan_angle,
            save_path=save_path,
            zoom=zoom,
            axis_label=axis_label
        )

    def plot_scanned(
            self,
            input_data: NodeBundle,
            z: int = None,
            scan_angle: bool = False,
            ax: plt.Axes = None,
            axis_lims: list = None,
            color: str = dim.magenta.hex,
            linewidth: float = None):

        return plot_morph_scanned_highlight(
                self,
                input_data=input_data,
                rectangles=self.neuComp,
                z=z,
                scan_angle=scan_angle,
                ax=ax,
                axis_lims=axis_lims,
                color=color,
                linewidth=linewidth)

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

        return roi_file.generate_roi_file(
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
