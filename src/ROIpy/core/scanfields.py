from __future__ import annotations
import hashlib
import json
from pathlib import Path
from ROIpy.core.bundles import ScanfieldBundle
from ROIpy.core.morphology import Morphology
from ROIpy.core.utils.utils import numpy_json_default
from ROIpy.core.makeroi import make_roi, roi_file


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
            output_filename: str | Path = "scanfields.h5",
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
            force_recompute: bool = False,
    ) -> None:
        """
        Initialize a Scanfields instance with given image and tracing paths,
        and optional parameters.

        Parameters
        ----------
        morphology : Morphology
            Morphology element containing metadata.
        output_filename: str | Path
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
        force_recompute : bool, optional
            If True, ignore any cached scanfields and regenerate them
            (default: False).

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
            self._morph.folder / output_filename)

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
        self._force_recompute = force_recompute

        self.objective_resolution = self._morph.objective_resolution
        self.zs = self._morph.zs

        self.optimal_pix_um_ratio = self._rayleigh_nyquist()

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

    def _make_cache_metadata(self) -> dict:
        """
        Build metadata used to determine whether cached scanfields are valid.
        
        Returns
        -------
        dict
            Metadata dictionary used for cache validation.
        """
        morphology_data = json.dumps(
            [node.to_dict() for node in self._morph.neuron],
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=numpy_json_default,
        ).encode("utf-8")

        return {
            "format_version": 1,
            "algorithm_version": 1,
            "scan_params": self.scan_params,
            "morphology_sha256": hashlib.sha256(morphology_data).hexdigest(),
        }

    def _rayleigh_nyquist(self) -> float:
        """
        Calculate the Rayleigh/Nyquist pixel-to-micrometer ratio.

        Uses the Rayleigh criterion to estimate the diffraction-limited
        lateral resolution:
            
            0.61 * λ / NA
        
        and applies Nyquist sampling to express the
        required pixels per micrometer:
        
            2 / resolution_um
        """

        diffraction_limited_spot_um = (
            0.61 * self.wavelength / self.numerical_aperture
        ) * 1e-3

        return 2 / diffraction_limited_spot_um

    def _make_scanfieldbundle(self) -> list:
        """
        Loads a bundle if exists, otherwise creates it.
        Returns
        -------
        neuron : ScanfieldBundle
            list of separated branches.
        """

        files = list(self._morph.folder.iterdir())

        scanfieldbundle_filename = next(
            (file for file in files
             if file.stem == self.output_filename.stem),
            None)

        metadata = json.dumps(
            self._make_cache_metadata(),
            sort_keys=True,
            default=numpy_json_default)

        if (not self._force_recompute
                and scanfieldbundle_filename is not None
                and scanfieldbundle_filename.exists()):
            try:
                stored = ScanfieldBundle.load_cache_metadata(
                    scanfieldbundle_filename)
            except (KeyError, ValueError):
                stored = None
            if stored == metadata:
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
        neuron.save_to_h5(self.output_filename, cache_metadata=metadata)

        return neuron

    def __getattr__(
            self,
            name: str):
        key = f"_{name}"
        if key in self.__dict__:
            return self.__dict__[key]
        raise AttributeError(name)

    def __setattr__(
            self,
            name: str,
            value):
        self.__dict__[f"_{name}"] = value

    def __len__(self) -> int:
        return sum(len(zplane) for zplane in self.neuron)

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
