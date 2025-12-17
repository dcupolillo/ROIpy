""" Created on Thu Oct 12 13:18:03 2023
    @author: dcupolillo """

import json


def save_to_json(
    node_bundle: object,
    json_filename: str,
) -> None:
    """
    Save NodeBundle data to a JSON file.

    This function serializes key properties of a NodeBundle, such as the total
    number of nodes, total neurite length, convex hull volume, and branch count,
    and saves them in a JSON file.

    Parameters
    ----------
    node_bundle : NodeBundle
        The NodeBundle instance to be saved.
    json_name : str
        The name or path of the JSON file to save the data.

    Returns
    -------
    None

    Example
    -------
    >>> save_to_json(node_bundle, 'output/nodes.json')
    """
    # Ensure the file has a .json extension
    if not json_filename.lower().endswith('.json'):
        json_filename += '.json'

    # Prepare data to save
    data_to_save = {
        'neuron_id': None,  # Placeholder for neuron ID (can be updated)
        'num_nodes': len(node_bundle),
        'tot_len': node_bundle.totlen(),
        'hull_volume': node_bundle.hull(show_plot=False),
        'num_branches': len(node_bundle.neurite),
    }

    # Save data to the JSON file
    with open(json_filename, 'w') as json_file:
        json.dump(data_to_save, json_file, indent=4)
