from __future__ import annotations
from pathlib import Path
import numpy as np
import tifffile
from ROIpy.core.utils.utils import parse_stack_metadata


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
        stack_filename: str | Path,
        channel: int | None = None,
    ) -> None:
        """
        Initialize a Stack instance.

        Parameters
        ----------
        stack_filename : str or Path
            File name of the stack image.
        channel : int, optional
            ScanImage channel number (1-based, as listed in `ch_saved`)
            to load from a multi-channel stack. If None, the second
            plane is used for multi-channel stacks.

        Raises
        ------
        ValueError
            If the provided path is not a .tif or .tiff file, or if
            `channel` is not saved in the file.

        Returns
        -------
        None
        """

        stack_filename = Path(stack_filename)

        if stack_filename.suffix.lower() not in ['.tif', '.tiff']:
            raise ValueError(
                f"Invalid file format for {stack_filename}."
                "Expected .tif or .tiff file.")

        self.imagename = stack_filename
        self.folder = self.imagename.parent

        image_data = tifffile.imread(self.imagename)
        self.metadata = parse_stack_metadata(self.imagename)
        self.image = self._select_channel(image_data, channel)

        for key, value in self.metadata.items():
            setattr(self, key, value)

    def _select_channel(
            self,
            image_data: np.ndarray,
            channel: int | None
    ) -> np.ndarray:
        """
        Return the [z, x, y] image for the requested channel.
        """

        ch_saved = list(self.metadata["ch_saved"])

        if image_data.ndim != 4:
            if channel is not None and ch_saved != [channel]:
                raise ValueError(
                    f"Channel {channel} requested, but the file contains "
                    f"only the saved channel(s) {ch_saved}.")
            return image_data

        if channel is None:
            return image_data[1]

        if channel not in ch_saved:
            raise ValueError(
                f"Channel {channel} not saved in this file "
                f"(saved channels: {ch_saved}).")

        if image_data.shape[0] != len(ch_saved):
            raise ValueError(
                f"Stack has {image_data.shape[0]} channels, but "
                f"metadata lists {len(ch_saved)} saved channels.")

        return image_data[ch_saved.index(channel)]

    def __getattr__(self, name: str) -> any:
        
        key = f"_{name}"
        
        if key in self.__dict__:
            return self.__dict__[key]
        
        raise AttributeError(name)

    def __setattr__(
            self,
            name: str,
            value: any
    ) -> None:
        self.__dict__[f"_{name}"] = value

    @property
    def metadata_dict(self) -> dict:
        """
        Returns the metadata dictionary for this stack.
        """
        return self.metadata
