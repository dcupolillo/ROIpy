""" Created on Mon Nov  6 10:29:44 2023
    @author: dcupolillo """

import flammkuchen as fl
from pathlib import Path
import tifffile
import matplotlib.pyplot as plt

from ROIpy.core.bundles import NodeBundle, ScanfieldBundle
from ROIpy.plot.plot import (
    plot_image, plot_morph,
    plot_scanfield, plot_scanfields_3d,
    plot_morph_scanned_highlight)

from ROIpy.core.utils.utils import parse_swc, parse_stack_metadata
from ROIpy.core.makeroi import make_roi, roi_file
from ROIpy.assets.palette import dim

from neuronpath.path import NeuronPath


class Stack():

    def __init__(
        self,
        imagepath: str or Path or NeuronPath
    ) -> None:
        """
        Initialize a Stack instance with the path to a .tif image file.

        Parameters
        ----------
        imagepath : Path or NeuronPath
            The full path to the .tif image file.
        """

        if isinstance(imagepath, str):
            imagepath = Path(imagepath)

        if not (isinstance(imagepath, Path)
                and imagepath.suffix.lower() in ('.tif', '.tiff')):
            raise Exception(
                f"Invalid file format for {imagepath}."
                "Expected .tif or .tiff file.")

        self.imagename = imagepath
        self.image = tifffile.imread(self.imagename)

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
        Plot the max projection stack image.

        Parameters
        ----------
        scanAngle : bool, optional
            Select the plotting unit. The default is False.
        ax : plt.axes.Axes, optional
            If specified, plots within it. The default is None.
        norm : list or tuple, optional
            Specifies the LUT limits. The default is None.
        cmap : str, optional
            Colormap of the image. The default is None.
        z : int, optional
            If specified, only that slice is plotted. The default is None.

        Returns
        -------
        plt.axes.Axes
            The axes with the plotted image.

        Example usage
        -------
        fig, ax = plt.subplots()
        stack.plot(cmap = 'viridis', norm = (100, 2000), ax = ax)

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
    Class to represent neuronal morphology data.

    Attributes:
        tracename (str): Pathname of the tracing file.
        neuron (NodeBundle): Neuronal structure loaded from the tracing file.
        apical (NodeBundle): Subset of the neuron structure
                             representing apical dendrites.
        basal (NodeBundle): Subset of the neuron structure
                            representing basal dendrites.
        soma (Node): Soma node of the neuron.

    Example usage:
        morph = Morphology("imagename.tif", "tracingname.swc")

    """

    def __init__(
            self,
            imagename: str or Path or NeuronPath,
            tracename: str or Path or NeuronPath
    ) -> None:
        """
        Creates a neuronal object (list of Nodes instances).

        Inherits all field of view attributes from from Stack.
        Subclasses Scanfield.

        Parameters
        ----------
        imagename : str
            image pathname.
        tracename : str
            tracing pathname.

        Raises
        ------
        Exception
            If the tracing file is not in .swc format.

        Returns
        -------
        None

        """

        if not (isinstance(tracename, (str, Path, NeuronPath)) or
                tracename.suffix.lower() != '.swc'):
            raise Exception(f"Invalid file format for {tracename}."
                            "Expected .swc file.")

            raise Exception(
                f"Invalid file format for {tracename}. Expected .swc file.")

        # Super call Stack
        super().__init__(imagename)
        self.tracename = tracename

        self.neuron = NodeBundle(parse_swc(
            self.tracename,
            self.objective_resolution,
            self.zs,
            self.pixel_to_ref_transform))

        self.apical = NodeBundle(
            [node for node in self.neuron if node.type == 'apical dendrite'])
        self.basal = NodeBundle(
            [node for node in self.neuron if node.type == 'basal dendrite'])
        self.soma = next(
            (node for node in self.neuron if node.type == 'soma'), None)

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
            color: str = dim.black.hex,
            linewidth: int = 1
    ) -> plt.Axes:
        """
        Plot the structure.

        Parameters
        ----------
        input_data : TYPE
            DESCRIPTION.
        z_planes : bool, optional
            If True return a multiplot with each individual Z plane.
            The default is False.
        show_segments : bool, optional
            If True, plot the line connecting the nodes.
            The default is True.
        show_nodes : bool, optional
            If True, plots the individual nodes as scattered dots.
            The default is False.
        z : int, optional
            DESCRIPTION. The default is None.
        ax : plt.Axes.ax, optional
            if specified, plots in the indicated plot. The default is None.
        axis_lims : list, optional
            if specified, ax will be bounded to lists
        cmap : str, optional
            colormap of the scattered nodes based on their Z position.
            The default is None.
        scan_angle : bool, optional
            if True, plots in units of angle degrees.
            The default is False.
        color : str, optional
            color of the connecting lines. The default is dim.black.hex.
        linewidth : int, optional
            Specifies the width of the connecting line. The default is 1.

        Returns
        -------
        plt.Axes.ax
            The axes with the plotted morphology structure.

        Example usage
        -------
            morph.plot(morph.neuron, nodes = True, cmap = 'jet', linewidth = 3)

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


class Scanfields(Morphology):

    """
    A class to create and manage scanfields for imaging,
    inheriting from the Morphology class.

    This class is designed to work with neuronal imaging data,
    creating scanfields
    based on provided morphology data and imaging parameters.
    """

    def __init__(
            self,
            imagename: str or Path or NeuronPath,
            tracename: str or Path or NeuronPath,
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
            filtering_radius: tuple = (50.0, 20.0)
    ) -> None:
        """
        Initialize a Scanfields instance with given image and tracing paths,
        and optional parameters.

        Parameters
        ----------
        imagename : str
            image pathname.
        tracename : str
            tracing pathname.
        desired_framerate : int, optional
            rate (Hz) at which frames are acquired. The default is 16.
        elongating_factor : float, optional
            multiplier for ROI elongation across
            longitudinal axis during ROI design. The default is 1.33.
        dim_ratio_threshold : float, optional
            width-to-height ratio threshold for assigning
            rectangular rois to merging function. The default is 3.5.
        overlap_threshold : float, optional
            treshold for area covered by surrounding
            rectangles in a single scanfield. The default is 0.90.
        wavelength : int, optional
            wavelength (nm) of used laser beam. The default is 830.
        fill_fraction : float, optional
            ratio between the length of an active acquisition of a line
            and the total length of the line.
            In Galvo-Galvo mode, spatial and temporal fill fraction
            are equal. The default is 0.9.
        frame_flyback : float, optional
            time (s) to allow scan mirror to travel from frame end position
            to frame start position at the end of a frame.
            The default is 0.001.
        fly_to_line : float, optional
            time (s) to allow  scanner to transition from the end position
            of one ROI to the start position of another. The default is 0.001.
        numerical_aperture : float, optional
            of the used objective. The default is 0.8.
        sampling_rate : float, optional
            rate (Hz) of ADC spample collection. The default is 1.250 * 1e6.
        pixel_bin_factor : int, optional
            ADC samples that are averaged into one pixel. The default is 4.

        Returns
        -------
        None.

        Example usage
        -------
        sf = Scanfield("imagename.tif", "tracingname.swc")

        # to change the final computed framerate
        sf.desiredFramerate = 18

        """

        # if isinstance(imagename, str):
        #     imagename = Path(imagename)

        super().__init__(imagename, tracename)

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

        # Abbe's equation for diffraction limited spot
        # Rayleigh criterion: distance required to differentiate 2 structures
        self.optimal_pix_um_ratio = (1 / (
            ((0.61 * self.wavelength / self.numerical_aperture)
             * 1e-3) / 2))

        self.neuComp = ScanfieldBundle(self.create_roi(self.neuron))

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
        Functions to create rotated rectangular Rois
        based on node positions in xyz
        applies desired_framerate, elongating_factor and dim_ratio_threshold

        Parameters
        ----------
        input_data : Morphology
            the compartement to be subdivided in Rois.

        Returns
        -------
        ScanfieldBundle
            nested list of Roi objects.

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
            figsize: tuple = None,
            show_title: bool = False,
            cmap: str = None,
            scan_angle: bool = False,
            edgecolor: str = dim.black.hex,
            linewidth: int = 1,
            elev: int or float = None,
            azim: int or float = None,
            zoom: int or float = None,
    ) -> plt.Axes:

        return plot_scanfields_3d(
                self,
                input_roi,
                ax=ax,
                figsize=figsize,
                show_title=show_title,
                cmap=cmap,
                edgecolor=edgecolor,
                linewidth=linewidth,
                scan_angle=scan_angle,
                elev=elev,
                azim=azim,
                zoom=zoom)

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
        Save the generated ROIs into a json-formatted text
        that can be interpreted by ScanImage mROI Editor.

        Parameters
        ----------
        input_data : ScanfieldBundle
            The Scanfield bundle to save as .roi file.
        folder_path : str
            destionation of the .roi files.
        structure_type : str, optional
            'neuron', 'apical' or 'basal'. The default is None.

        Returns
        -------
        None

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
        Prints the total number of generated rectangles.
        """

        print(sum(len(z) for z in inputData))
