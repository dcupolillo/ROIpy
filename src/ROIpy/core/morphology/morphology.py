from __future__ import annotations
from pathlib import Path
from ROIpy.core.morphology.bundle import NodeBundle
from ROIpy.core.stack import Stack
from ROIpy.core.utils.utils import (
    stack_metadata_dictionary, parse_swc,
    assign_branch_degree_and_id)


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
            swc_filename: str | Path = None,
            stack: Stack = None,
            output_filename: str | Path = "morphology.h5",
            h5_file: str | Path = None,
            force_recompute: bool = False
    ) -> None:
        """
        Initializes a neuronal object. Inherits attributes from Stack.

        Parameters
        ----------
        swc_filename : str | Path, optional
            File name of the morphological reconstruction (.swc format).
            Required if h5_file is not provided. Default is None.
        stack : Stack, optional
            Instance of the Stack containing metadata. Default is None.
        output_filename : str | Path, optional
            File name where morphology data are stored in h5 format.
            Default is `morphology.h5`. Used only when parsing from .swc.
        h5_file : str | Path, optional
            Path to an existing .h5 file to load neuron data directly.
            If provided, skips .swc parsing and uses this file instead.
            Default is None.
        force_recompute : bool, optional
            If True, forces recomputation of morphology data even if .h5 file exists.
            Default is False.

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
            self.folder = h5_file.parent
            self.output_filename = h5_file
            self._load_from_h5 = not force_recompute
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
            self.folder = swc_filename.parent
            self.output_filename = Path(self.filename.parent / output_filename)
            self._load_from_h5 = False
            self._force_recompute = force_recompute

        self.metadata = (
            stack_metadata_dictionary(**stack.metadata) if stack
            else stack_metadata_dictionary())

        self._has_stack = True if stack else False

        for key, value in self.metadata.items():
            setattr(self, key, value)

        # Create the bundles
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

        if (not self._force_recompute
                and nodebundle_filename is not None
                and nodebundle_filename.exists()):
            return NodeBundle.load_from_h5(nodebundle_filename)

        nodes_list = parse_swc(self.filename, self.metadata)
        neuron = NodeBundle(nodes_list)

        assign_branch_degree_and_id(neuron)
        neuron.save_to_h5(self.output_filename)

        return neuron
