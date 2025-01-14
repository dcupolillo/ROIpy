""" Created on Thu Oct 12 13:18:03 2023
    @author: dcupolillo """

import json


def save_to_json(
        node_bundle,
        json_filename: str
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
    """

    if not json_filename.lower().endswith('.json'):
        json_filename += '.json'

    data_to_save = {
        'neuron_id': None,
        'num_nodes': len(node_bundle),
        'tot_len': node_bundle.totlen,
        'hull_area': node_bundle.hullarea,
        'num_branches': len(node_bundle.neurite),
    }

    with open(json_filename, 'w') as json_file:
        json.dump(data_to_save, json_file, indent=4)
