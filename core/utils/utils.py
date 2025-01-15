""" Created on Mon Nov  6 10:29:44 2023
    @author: dcupolillo """

from pathlib import Path
import numpy as np
import tifffile
from ROIpy.core.components import Node


def get_filename(
        main_folder: str,
        date: str,
        cell_number: str,
        file_type: str
) -> str:

    if file_type == 'swc' or file_type == 'tif':
        return Path(main_folder,
                    date,
                    f'cell_{cell_number}',
                    f'{date}_cell{cell_number}_stack_00001.{file_type}')
    elif file_type == 'abf':
        return Path(main_folder,
                    date,
                    f'cell_{cell_number}',
                    f'20{date[:2]}_{date[2:4]}_{date[4:]}_0001.{file_type}')
    else:
        raise ValueError('f{file_type} not a valid input.')


def parse_stack_metadata(
        image_name: str
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
    width_um = np.abs(min(corners_um[0])
                      - max(corners_um[1]))
    height_um = np.abs(min(corners_um[2])
                       + max(corners_um[3]))
    width_deg = np.abs(min(corners_deg[0])
                       - max(corners_deg[1]))
    height_deg = np.abs(min(corners_deg[2])
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

    n_channel_available = framedata['SI.hChannels.channelsAvailable']
    ch_available_list = np.arange(n_channel_available)
    ch_active = ([framedata['SI.hChannels.channelsActive']]
                 if isinstance(
        framedata['SI.hChannels.channelsActive'], int)
        else framedata['SI.hChannels.channelsActive'])

    ch_active_list = [True if (n+1) in ch_active else False
                      for i, n in enumerate(ch_available_list)]

    n_channels = (1 if isinstance(ch_active, int)
                  else len(ch_active))

    return {
        'stack_name': stack_name,
        'data_type': data_type,
        'corners_um': corners_um,
        'corners_deg': corners_deg,
        'width_pix': width_pix,
        'height_pix': height_pix,
        'width_um': width_um,
        'height_um': height_um,
        'width_deg': width_deg,
        'height_deg': height_deg,
        'pix_um_ratio': pix_um_ratio,
        'units_um': units_um,
        'units_deg': units_deg,
        'zoom': zoom,
        'zs': zs,
        'z_distance': z_distance,
        'n_slices': n_slices,
        'stack_start': stack_start,
        'stack_end': stack_end,
        'objective_resolution': objective_resolution,
        'pixel_to_ref_transform': pixel_to_ref_transform,
        'affine': affine,
        'n_channel_available': n_channel_available,
        'ch_available_list': ch_available_list,
        'ch_active': ch_active,
        'ch_active_list': ch_active_list,
        'n_channels': n_channels
    }


def parse_swc(
        filename: str,
        objective_resolution: float,
        zs: list,
        pixel_to_ref_transform: list or np.ndarray
) -> list:
    """
    Read the swc file, extract the data and generates a list of Node instances

    Parameters
    ----------
    filename : str
        file name of the tracing file.
    objective_resolution : float
        of the used objective, stored in the image metadata.
    zs : list
        a list with all Z slice positions.
    pixel_to_ref_transform : list or np.ndarray
        transformation matrix stored in the image metadata.

    Returns
    -------
    list
        list of Node instances.

    """

    nodes = []

    with open(filename, 'r') as f:
        for n_line, line in enumerate(f):
            if line.startswith('#'):
                if n_line == 4:
                    field = line.strip().split()
                    x_voxel_separation = float(field[4][:-1])
                    y_voxel_separation = float(field[5][:-1])
                continue  # skip comment lines

            fields = line.strip().split()

            # Create individual Node instances
            node = Node(
                objective_resolution,
                fields[0],
                fields[1],
                fields[2],
                fields[3],
                fields[4],
                zs,
                fields[5],
                fields[6],
                pixel_to_ref_transform,
                x_voxel_separation,
                y_voxel_separation)
            nodes.append(node)

    # Compute parent node
    for node in nodes:
        parent_id = node.parent_id
        if parent_id != -1:  # Skip root node
            parent_node = next(n for n in nodes if n._id == parent_id)
            parent_node.children.append(node._id)

    # Update is_fork attribute for each node based on children count
    for node in nodes:
        node.is_fork = len(node.children) > 1

    return nodes


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

    for i, node in enumerate(input_data):

        if node._type == 'soma':
            if current_section:
                sections.append(current_section)
            current_section = []
            continue  # skip soma

        elif i == len(input_data) - 1:  # last node
            current_section.append(node)
            sections.append(current_section)

        else:
            if input_data[i+1].parent_id == node._id:
                current_section.append(node)
            else:
                current_section.append(node)
                sections.append(current_section)
                current_section = []

    return sections


def assign_branch_degree(input_data):

    neurites = split_neurite(input_data)

    branch_degree = 1

    already_classified_nodes = set()

    # Start with the first-degree branches
    current_degree_branches = [
        n for n, neurite in enumerate(neurites)
        if neurite[0].parent_id == 1]

    # Loop to assign branch degrees iteratively
    while current_degree_branches:

        for i in current_degree_branches:
            for node in neurites[i]:
                node.branch_degree = branch_degree

        already_classified_nodes.update({
            node._id for i in current_degree_branches
            for node in neurites[i]})

        fork_nodes = {
            node._id for i in current_degree_branches
            for node in neurites[i] if node.is_fork}

        next_degree_branches = [
            n for n, neurite in enumerate(neurites)
            if neurite[0].parent_id in fork_nodes
            and neurite[0]._id not in already_classified_nodes]

        current_degree_branches = next_degree_branches
        branch_degree += 1
