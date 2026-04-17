""" Created on Mon Nov  6 10:29:44 2023
    @author: dcupolillo """

from __future__ import annotations
from pathlib import Path
import numpy as np
import tifffile
from ROIpy.core.components import Node


def stack_metadata_dictionary(
        stack_name: str = None,
        data_type: str = None,
        corners_um: list = None,
        corners_deg: list = None,
        width_pix: int = None,
        height_pix: int = None,
        width_um: float = None,
        height_um: float = None,
        width_deg: float = None,
        height_deg: float = None,
        pix_um_ratio: float = None,
        units_um: str = None,
        units_deg: str = None,
        zoom: float = None,
        zs: list = None,
        z_distance: float = None,
        n_slices: int = None,
        stack_start: float = None,
        stack_end: float = None,
        objective_resolution: float = None,
        pixel_to_ref_transform: np.ndarray = None,
        affine: np.ndarray = None,
        n_channel_available: int = None,
        ch_available_list: list = None,
        ch_active: list = None,
        ch_active_list: list = None,
        n_channels: int = None
) -> dict:
    """
    Constructs a metadata dictionary for a 3D image stack.

    Parameters
    ----------
    stack_name : str, optional
        Identifier or filename of the stack.
    data_type : str, optional
        Type of data (e.g., 'tif', 'npy').
    corners_um : list of float, optional
        Image corner coordinates in micrometers.
    corners_deg : list of float, optional
        Image corner coordinates in degrees.
    width_pix : int, optional
        Image width in pixels.
    height_pix : int, optional
        Image height in pixels.
    width_um : float, optional
        Image width in micrometers.
    height_um : float, optional
        Image height in micrometers.
    width_deg : float, optional
        Image width in degrees.
    height_deg : float, optional
        Image height in degrees.
    pix_um_ratio : float, optional
        Pixel-to-micron scaling factor.
    units_um : str, optional
        Units used for micrometer-based dimensions.
    units_deg : str, optional
        Units used for degree-based dimensions.
    zoom : float, optional
        Zoom factor used during acquisition.
    zs : list of float, optional
        Z-positions of individual slices.
    z_distance : float, optional
        Distance between consecutive z-slices.
    n_slices : int, optional
        Number of z-slices in the stack.
    stack_start : float, optional
        Start time of stack acquisition.
    stack_end : float, optional
        End time of stack acquisition.
    objective_resolution : float, optional
        Optical resolution of the objective in micrometers.
    pixel_to_ref_transform : np.ndarray, optional
        Transformation matrix from pixel to reference coordinates.
    affine : np.ndarray, optional
        Affine transformation matrix for spatial mapping.
    n_channel_available : int, optional
        Total number of available imaging channels.
    ch_available_list : list of int, optional
        List of all available channel indices.
    ch_active : list of int, optional
        Currently active channel indices.
    ch_active_list : list of int, optional
        Redundant/alternative list of active channel indices.
    n_channels : int, optional
        Number of active channels.

    Returns
    -------
    dict
        Dictionary containing all provided metadata fields.
    """
    return locals()


def parse_stack_metadata(
        image_name: str | Path
) -> dict:

    with tifffile.TiffFile(image_name) as tif:
        scanimage_metadata = tif.scanimage_metadata

    framedata = scanimage_metadata['FrameData']
    roigroups = scanimage_metadata['RoiGroups']

    stack_name = framedata['SI.hScan2D.logFileStem']
    data_type = framedata['SI.hScan2D.channelsDataType']
    corners_um = framedata['SI.hRoiManager.imagingFovUm']
    corners_deg = framedata['SI.hRoiManager.imagingFovDeg']
    width_pix = framedata['SI.hRoiManager.pixelsPerLine']
    height_pix = framedata['SI.hRoiManager.linesPerFrame']

    width_um = np.abs(
        min(corners_um[0])
        - max(corners_um[1]))
    height_um = np.abs(
        min(corners_um[2])
        + max(corners_um[3]))
    width_deg = np.abs(
        min(corners_deg[0])
        - max(corners_deg[1]))
    height_deg = np.abs(
        min(corners_deg[2])
        + max(corners_deg[3]))

    pix_um_ratio = width_pix / width_um
    units_um = 'µm'
    units_deg = 'deg'
    zoom = framedata['SI.hRoiManager.scanZoomFactor']
    zs = framedata['SI.hStackManager.zs']

    # To deal with eventual averaging stack planes
    if len(zs) != len(set(zs)):
        zs = list(set(zs))

    z_distance = np.abs(np.diff(zs)[0])
    n_slices = framedata['SI.hStackManager.actualNumSlices']
    stack_start = framedata['SI.hStackManager.stackZStartPos']
    stack_end = framedata['SI.hStackManager.stackZEndPos']

    objective_resolution = framedata['SI.objectiveResolution']

    pixel_to_ref_transform = np.array(
        roigroups['imagingRoiGroup']['rois']
                 ['scanfields']['pixelToRefTransform'])
    affine = np.array(
        roigroups['imagingRoiGroup']['rois']
                 ['scanfields']['affine'])

    n_channel_available = (
        framedata['SI.hChannels.channelsAvailable'])
    ch_available_list = np.arange(n_channel_available)
    ch_active = (
        [framedata['SI.hChannels.channelsActive']]
        if isinstance(framedata['SI.hChannels.channelsActive'], int)
        else framedata['SI.hChannels.channelsActive'])

    ch_active_list = [
        True if (ch + 1) in ch_active else False
        for ch in ch_available_list]

    n_channels = (
        1 if isinstance(ch_active, int)
        else len(ch_active))
    
    metadata_dictionary = dict(
        stack_name=stack_name,
        data_type=data_type,
        corners_um=corners_um,
        corners_deg=corners_deg,
        width_pix=width_pix,
        height_pix=height_pix,
        width_um=width_um,
        height_um=height_um,
        width_deg=width_deg,
        height_deg=height_deg,
        pix_um_ratio=pix_um_ratio,
        units_um=units_um,
        units_deg=units_deg,
        zoom=zoom,
        zs=zs,
        z_distance=z_distance,
        n_slices=n_slices,
        stack_start=stack_start,
        stack_end=stack_end,
        objective_resolution=objective_resolution,
        pixel_to_ref_transform=pixel_to_ref_transform,
        affine=affine,
        n_channel_available=n_channel_available,
        ch_available_list=ch_available_list,
        ch_active=ch_active,
        ch_active_list=ch_active_list,
        n_channels=n_channels
    )

    return stack_metadata_dictionary(**metadata_dictionary)


def parse_swc(
        filename: str,
        metadata: dict,
) -> list:
    """
    Parse an SWC file and generate a list of Node instances.
    Only tested for .swc files generated by SNT plugin in ImageJ.

    Parameters
    ----------
    filename : str
        Path to the SWC file containing the neuronal morphology data.
    metadata : dict
        Dictionary containing metadata required for parsing the SWC file.
        Expected keys:
        - "objective_resolution": float
        - "zs": list of float
        - "pixel_to_ref_transform": np.ndarray

    Returns
    -------
    list
        List of Node instances representing the parsed morphology.
    """

    objective_resolution = metadata["objective_resolution"]
    zs = metadata["zs"]
    pixel_to_ref_transform = metadata["pixel_to_ref_transform"]

    nodes = []
    x_voxel_separation, y_voxel_separation = 1., 1.

    with open(filename, 'r') as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            if line.startswith('#'):

                if "Voxel separation" in line:
                    voxel_info = line.split(':', 1)[1].strip()
                    x, y, z = map(float, voxel_info.split(','))
                    x_voxel_separation = x
                    y_voxel_separation = y
                    z_voxel_separation = z

                continue  # skip other comment lines

            fields = line.split()

            # Create individual Node instances
            node = Node(
                obj_res=objective_resolution,
                _id=fields[0],
                _type=fields[1],
                x=fields[2],
                y=fields[3],
                z_ind=fields[4],
                zs=zs,
                radius=fields[5],
                parent_id=fields[6],
                matrix=pixel_to_ref_transform,
                voxel_separation_x=x_voxel_separation,
                voxel_separation_y=y_voxel_separation,
                voxel_separation_z=z_voxel_separation)
            nodes.append(node)

    # Compute parent node
    for node in nodes:
        parent_id = node.parent_id
        if parent_id != -1:  # Skip root node
            parent_node = next(n for n in nodes if n._id == parent_id)
            parent_node.children.append(node.id)

    # Update is_fork attribute for each node based on children count
    for node in nodes:
        node.is_fork = len(node.children) > 1

    return nodes


def is_new_branch(
        node: object,
        previous_node: object
) -> bool:

    return (
        node.parent_id != previous_node.id or
        node.parent_id is None)


def split_neurite(
        input_data
) -> list:
    """
    Divide a neuronal structure into sections (neurites).

    A neurite is defined as a section delimited by:
    - Soma and an end point
    - Forking point and an end point

    Parameters
    ----------
    input_data : NodeBundle
        Morphology structure containing nodes to split into neurites.

    Returns
    -------
    list
        A list of lists, where each inner list contains nodes representing
        a single neurite section.

    Example
    -------
    >>> neurite_sections = split_neurite(node_bundle)
    >>> print(f"Number of neurites: {len(neurite_sections)}")
    """

    sections = []
    current_section = []

    for node_n, node in enumerate(input_data):

        if node._type == 1:
            if current_section:
                sections.append(current_section)
            current_section = []
            continue  # skip soma

        elif node_n == len(input_data) - 1:  # last node
            current_section.append(node)
            sections.append(current_section)

        else:
            if input_data[node_n + 1].parent_id == node._id:
                current_section.append(node)
            else:
                current_section.append(node)
                sections.append(current_section)
                current_section = []

    return sections


def assign_branch_degree_and_id(input_data: object) -> None:
    """
    Assign branch degrees and unique branch IDs to nodes
    in the neuronal morphology.

    Parameters
    ----------
    input_data : NodeBundle
        Morphology structure containing nodes.

    Returns
    -------
    NodeBundle
        The input NodeBundle with updated branch_degree and branch_id.

    Updates
    -------
    - Each node's branch_degree is updated to reflect its hierarchical level.
    - Each node's branch_id is updated to uniquely identify its neurite.
    """

    neurites = split_neurite(input_data)

    branch_degree = 1

    soma_node_id = input_data[0].id

    already_classified_nodes = set()

    # Start with the first-degree branches
    # Group all neurites whose first node's parent is the soma or soma itself
    # Get their indices
    current_degree_branches = [
        n for n, neurite in enumerate(neurites)
        if neurite[0].parent_id == soma_node_id
        or neurite[0].id == soma_node_id]

    # Loop to assign in-place branch degrees and IDs iteratively
    while current_degree_branches:

        for neurite_n in current_degree_branches:

            for node in neurites[neurite_n]:
                original_node = next(
                    n for n in input_data if n.id == node.id)

                original_node.branch_degree = branch_degree

        already_classified_nodes.update({
            node.id for neurite_n in current_degree_branches
            for node in neurites[neurite_n]})

        fork_nodes = {
            node.id for neurite_n in current_degree_branches
            for node in neurites[neurite_n] if node.is_fork}

        next_degree_branches = [
            n for n, neurite in enumerate(neurites)
            if neurite[0].parent_id in fork_nodes
            and neurite[0].id not in already_classified_nodes]

        current_degree_branches = next_degree_branches
        branch_degree += 1

    # Assign branch IDs
    for neurite_n, neurite in enumerate(neurites):
        for node in neurite:
            original_node = next(
                n for n in input_data if n.id == node.id)
            original_node.branch_id = neurite_n
