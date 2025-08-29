""" Created on Mon May 12 12:38:32 2025
    @author: dcupolillo """


from pathlib import Path
import ROIpy as rp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

folder = Path(r"neuron_allen")

n_files = len(list(folder.iterdir()))
output_filenames = [
    Path(file.stem).with_suffix('.h5') for file in folder.iterdir()]

morph_list = [
    rp.Morphology(file, output_filename=output)
    for file, output in zip(folder.glob("*.swc"), output_filenames)]

fig, axes = plt.subplots(4, 5, figsize=(12, 12))

for n, morph in enumerate(morph_list):

    ax = axes.flat[n]
    morph.plot(
        morph.neuron,
        ax=ax,
        linewidth=0.8,
        color="grey")

    ax.scatter(
        morph.soma.x,
        morph.soma.y,
        color="crimson",
        zorder=2)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    scalebar_length = 100
    scalebar_height = min(ylim)
    scalebar_start = min(xlim)

    ax.plot(
        [scalebar_start, scalebar_start + scalebar_length],
        [scalebar_height, scalebar_height],
        linewidth=1.8,
        color="black",
        clip_on=False)

    ax.set(
        aspect="equal",
        xticks=[], yticks=[]
    )
    ax.spines[:].set_visible(False)


dendritic_lenghts = np.array([morph.neuron.totlen() for morph in morph_list])
n_branches = np.array([morph.neuron.n_branches for morph in morph_list])

