from __future__ import annotations
from pathlib import Path
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
            raise ValueError(
                f"Invalid file format for {stack_filename}."
                "Expected .tif or .tiff file.")

        self.imagename = stack_filename
        self.folder = self.imagename.parent

        image_data = tifffile.imread(self.imagename)
        self.image = (
            image_data[1] if image_data.ndim == 4 else image_data)

        self.metadata = parse_stack_metadata(self.imagename)

        for key, value in self.metadata.items():
            setattr(self, key, value)

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
