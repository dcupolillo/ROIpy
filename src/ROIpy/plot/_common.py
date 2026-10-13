from __future__ import annotations
"""Shared helpers for ROIpy plotting modules."""


def check_metadata(metadata: dict) -> None:
    """
    Check if metadata contains minimal required keys.

    Parameters
    ----------
    metadata : dict
        The metadata dictionary to be checked.

    Raises
    ------
    TypeError
        if metadata is not a dictionary
    ValueError
        if metadata is None
    KeyError
        if required keys are missing
    """

    required_keys = ['units_um', 'units_deg', 'corners_um', 'corners_deg']

    if metadata and not isinstance(metadata, dict):
        raise TypeError("metadata must be a dictionary.")

    if metadata is not None:
        for key in required_keys:
            if key not in metadata:
                raise KeyError(f"Metadata missing required key: {key}")


def get_scan_units(
        metadata: dict,
        scan_angle: bool
) -> tuple:
    """
    Returns the appropriate units, corners, and labels
    based on the scan_angle flag.

    Parameters
    ----------
    metadata : dict
        The metadata dictionary containing units and corners information.
    scan_angle : bool
        If True, returns angle-based values (degrees).
        If False, returns spatial values (micrometers).

    Returns
    -------
    tuple
        (units, corners)
    """
    if metadata is None:
        return None, None

    if scan_angle:
        return metadata['units_deg'], metadata['corners_deg']

    return metadata['units_um'], metadata['corners_um']
