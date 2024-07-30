""" Created on Wed Feb 14 16:48:30 2024
    @author: dcupolillo """

from pathlib import Path
import json
import numpy as np
import pandas as pd
import ROIpy as rp

dataset_folder = Path('Y:\\Vincenzo')
filename_list_file = Path('neuron_ids.json')
filename_list_path = dataset_folder / filename_list_file


with filename_list_path.open(mode='r') as file:
    data = json.load(file)

filename_list = data['neuron_ids']

tot_length = [None] * len(filename_list)
apical_length = [None] * len(filename_list)
basal_length = [None] * len(filename_list)
hull_area = [None] * len(filename_list)
n_neurites = [None] * len(filename_list)
n_roi_scanfield = [None] * len(filename_list)
z_distances = [None] * len(filename_list)
tot_scanned_area = [None] * len(filename_list)
n_z_planes = [None] * len(filename_list)

for i, neuron_id in enumerate(filename_list):

    date, cell_number = neuron_id.split('_cell_')
    path = (dataset_folder / date / f'cell_{cell_number}' / f'{date}_neuron')

    swc_filename = (dataset_folder / date / f'cell_{cell_number}' /
                    f'{date}_cell{cell_number}_stack_00001.swc')
    image_filename = (dataset_folder / date / f'cell_{cell_number}' /
                      f'{date}_cell{cell_number}_stack_00001.tif')

    morph = rp.Morphology(image_filename, swc_filename)
    sf = rp.Scanfields(image_filename, swc_filename)

    tot_length[i] = morph.neuron.totlen()
    apical_length[i] = morph.apical.totlen()
    basal_length[i] = morph.basal.totlen()
    hull_area[i] = morph.neuron.hull()
    n_neurites[i] = len(morph.neuron.neurite)

    n_roi_scanfield[i] = np.mean(sf.neuComp.shape[1])
    z_distances[i] = morph.z_distance
    tot_scanned_area[i] = sf.neuComp.area
    n_z_planes[i] = len(morph.zs)

dataframe_dict = {
        'filename': filename_list,
        'tot_length': tot_length,
        'apical_length': apical_length,
        'basal_length': basal_length,
        'hull_area': hull_area,
        'n_neurites': n_neurites,
        'mean_n_roi_scanfields': n_roi_scanfield,
        'z_distance': z_distances,
        'tot_scanned_area': tot_scanned_area,
        'n_z_planes': n_z_planes
}

dataframe = pd.DataFrame(dataframe_dict)

output_summary_filename = Path('summary.csv')

dataframe.to_csv(
    dataset_folder / output_summary_filename,
    index=False,
    sep=',')
