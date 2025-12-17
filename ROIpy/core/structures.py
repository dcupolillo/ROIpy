""" Created on Mon Nov  6 10:29:44 2023
    @author: dcupolillo """

from pathlib import Path
import tifffile
from ROIpy.core.bundles import NodeBundle, ScanfieldBundle
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
    >>> rp.plot(stack.image, stack.metadata, cmap='viridis', norm=(100, 2000))  # Visualize
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
    >>> stack = rp.Stack(stack_filename)
    >>> morph = rp.Morphology('path/to/swc_filename', stack)
    >>> rp.plot(morph.neuron, show_nodes=True, cmap='jet')
    """

    def __init__(
            self,
            swc_filename: str or Path = None,
            stack: Stack = None,
            output_filename: str or Path = "morphology.h5",
            h5_file: str or Path = None
    ) -> None:
        """
        Initializes a neuronal object. Inherits attributes from Stack.

        Parameters
        ----------
        swc_filename : str or Path, optional
            File name of the morphological reconstruction (.swc format).
            Required if h5_file is not provided. Default is None.
        stack : Stack, optional
            Instance of the Stack containing metadata. Default is None.
        output_filename : str or Path, optional
            File name where morphology data are stored in h5 format.
            Default is `morphology.h5`. Used only when parsing from .swc.
        h5_file : str or Path, optional
            Path to an existing .h5 file to load neuron data directly.
            If provided, skips .swc parsing and uses this file instead.
            Default is None.

        Raises
        ------
        ValueError
            If neither swc_filename nor h5_file is provided.
            If both swc_filename and h5_file are provided.
            If the tracing file is not in .swc format.
            If output_filename is not in .h5 format.
            If h5_file does not exist or is not in .h5 format.

        Returns
        -------
        None
        """

        # Validate input arguments
        if swc_filename is None and h5_file is None:
            raise ValueError(
                "Either 'swc_filename' or 'h5_file' must be provided.")
        
        if swc_filename is not None and h5_file is not None:
            raise ValueError(
                "Cannot provide both 'swc_filename' and 'h5_file'. "
                "Choose one loading method.")
        
        # Handle h5_file loading path
        if h5_file is not None:
            h5_file = Path(h5_file)
            if not h5_file.exists():
                raise ValueError(
                    f"Provided h5_file does not exist: {h5_file}")
            if h5_file.suffix.lower() != '.h5':
                raise ValueError(
                    f"Invalid file format for {h5_file}. Expected .h5")
            
            self.filename = None  # No .swc file in this case
            self.output_filename = h5_file
            self._load_from_h5 = True
            self.h5_file = h5_file
        
        # Handle swc_filename loading path
        else:
            swc_filename = Path(swc_filename)
            output_filename = Path(output_filename)

            if swc_filename.suffix.lower() != '.swc':
                raise ValueError(
                    f"Invalid file format for {swc_filename}. Expected .swc")

            if output_filename.suffix.lower() != ".h5":
                raise ValueError(
                    "Output filename needs to be in .h5 format")

            self.filename = swc_filename
            self.output_filename = Path(self.filename.parent / output_filename)
            self._load_from_h5 = False

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

        # If loading directly from h5_file, load and return immediately
        if self._load_from_h5:
            return NodeBundle.load_from_h5(self.h5_file)

        # Original behavior: check for existing cache or create new
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

    def get_roi_by_uuid(
            self,
            uuid: str
    ) -> object:
        """
        Retrieve a specific ROI by its UUID.

        Parameters
        ----------
        uuid : str
            The UUID of the desired ROI.

        Returns
        -------
        object
            The ROI object with the specified UUID, or None if not found.

        Example
        -------
        >>> roi = sf.get_roi_by_uuid('123e4567-e89b-12d3-a456-426614174000')
        """

        for zplane in self.neuron:
            for roi in zplane:
                if roi.roi_uuid == uuid:
                    return roi
        return None
