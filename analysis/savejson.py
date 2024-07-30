""" Created on Thu Oct 12 13:18:03 2023
    @author: dcupolillo """

import json


def save_to_json(
        node_bundle,
        json_name: str
) -> None:
    """
    Save data to a JSON file.

    Parameters
    ----------
    node_bundle : NodeBundle
        The data to be saved.
    json_name : str
        The name of the JSON file to save.

    Returns
    -------
    None

    """

    if not json_name.lower().endswith('.json'):
        json_name += '.json'

    data_to_save = {
        'neuron_id': None,
        'num_nodes': len(node_bundle),
        'tot_len': node_bundle.totlen,
        'hull_area': node_bundle.hullarea,
        'num_branches': len(node_bundle.neurite),
    }

    with open(json_name, 'w') as json_file:
        json.dump(data_to_save, json_file, indent=4)
