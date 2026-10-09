from __future__ import annotations
import flammkuchen as fl
from ROIpy.core.scanfields.roi import Roi
from ROIpy.core.makeroi.make_roi import convert_to_polygon


class ScanfieldBundle():
    """
    A helper class to wrap a collection of ROI (Region of Interest) objects.

    This class organizes a list of lists of `Roi` objects,
    typically representing
    scanfields across multiple Z-planes, and provides utility methods for
    saving, loading, and calculating properties of the scanfields.

    Attributes
    ----------
    scanfield : list
        A list of lists containing `Roi` objects for each Z-plane.
    """

    def __init__(
            self,
            scanfields: list,
    ) -> None:
        """
        Initialize a ScanfieldBundle instance.

        Parameters
        ----------
        scanfield : list
            A list of lists containing `Roi` objects for each Z-plane.

        Returns
        -------
        None
        """

        self.scanfields = scanfields

    def __repr__(self):
        return repr(self.scanfields)

    def __iter__(self):
        return iter(self.scanfields)

    def __getitem__(
            self,
            index: int):
        return self.scanfields[index]

    def __len__(self):
        return len(self.scanfields)

    def get_branch(self, branch_id: int) -> list:
        """
        Retrieve scanfields for a specific branch ID.

        Parameters
        ----------
        branch_id : int
            The ID of the branch to retrieve.

        Returns
        -------
        list
            The scanfields for the specified branch ID.
        """
        return [
            roi for z_plane in self.scanfields
            for roi in z_plane
            if roi.branch_id == branch_id]

    def save_to_h5(
            self,
            filename: str,
            cache_metadata: str | None = None
    ) -> None:
        """
        Save the ScanfieldBundle to an HDF5 file.

        Parameters
        ----------
        filename : str
            The path to the HDF5 file where the scanfields will be saved.
        cache_metadata : str, optional
            JSON-serialized metadata describing how the scanfields were
            generated. Stored alongside the scanfields when provided.

        Returns
        -------
        None
        """

        data = [
            [roi.to_dict() for roi in z_plane]
            for z_plane in self.scanfields]

        content = {'scanfields': data}
        if cache_metadata is not None:
            content['cache_metadata'] = cache_metadata

        fl.save(filename, content)

    @classmethod
    def load_from_h5(cls, filename: str) -> object:
        """
        Load a ScanfieldBundle from an HDF5 file.
        Prevents from computing again for every new instance.

        Parameters
        ----------
        filename : str
            The path to the HDF5 file containing the scanfields.

        Returns
        -------
        object: ScanfieldBundle
            An instance of the ScanfieldBundle loaded from the file.
        """
        data = fl.load(filename)['scanfields']
        scanfields = [[Roi.from_dict(roi) for roi in z_plane]
                      for z_plane in data]
        return cls(scanfields)

    @staticmethod
    def load_cache_metadata(filename: str) -> str | None:
        """
        Load the cache metadata stored with a ScanfieldBundle.

        Returns
        -------
        str or None
            The stored JSON metadata, or None for legacy files without it.
        """
        return fl.load(filename, '/cache_metadata')

    @property
    def shape(self) -> tuple:
        """
        Get the shape of the ScanfieldBundle.

        Returns
        -------
        tuple
            A tuple containing the number of Z-planes and a list of the number
            of ROIs in each Z-plane.
        """

        return len(self.scanfields), [len(row) for row in self.scanfields]

    def area(self, z: int = None) -> float:
        """
        Calculate the total area covered by all ROIs in the ScanfieldBundle.

        This method converts ROIs to polygons and accounts for
        overlapping portions by subtracting intersection areas,
        ensuring non-overlapping area calculation.

        Returns
        -------
        float
            The total non-overlapping area covered by the ROIs.
        """
        total_area = 0
        processed_polygons = []

        if z is None:
           scanfields = [roi for z in self.scanfields for roi in z]
        else:
            scanfields = self.scanfields[z]
        
        for roi in scanfields:
            # Convert the ROI to a polygon
            current_polygon = convert_to_polygon(roi)

            # Add the current polygon's area
            total_area += current_polygon.area

            # Subtract overlapping areas with previously processed polygons
            for processed_polygon in processed_polygons:
                overlap_area = current_polygon.intersection(
                    processed_polygon).area
                total_area -= overlap_area

            # Add the current polygon to the processed list
            processed_polygons.append(current_polygon)

        return total_area
