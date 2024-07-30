""" Created on Wed Feb 14 18:55:52 2024
    @author: dcupolillo """

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import dataplotter as dp
import ROIpy as rp

dataframe_filename = Path('Y:\\Vincenzo\\summary.csv')

dataframe = pd.read_csv(
    dataframe_filename,
    sep=',')

filenames = [name for name in dataframe['filename']]


saving_path = Path('Y:\\dcupolillo\\Neurotalk')

# %% Dendritic length plot

dendritic_length = dp.DataPlotter(
    figsize=(1.7, 3),
    font_size=12,
    y_lims=(0, 4000),
    y_label='Total dendritic length (mm)',
    y_ticks=([0, 1000, 2000, 3000, 4000]),
    y_pad=18,
    y_tick_labels=([0, 1, 2, 3, 4])
)

dendritic_length.box_plot(
    data=dataframe,
    x=None,
    y='tot_length',
    box_width=0.3,
    color='#808080')

dendritic_length.strip_plot(
    data=dataframe,
    x=None,
    y='tot_length',
    linewidth=1.5,
    edgecolor='#808080',
    fillcolor='none',
    jitter=0,
    strip_offset=0.3)

dendritic_length.display_mean(
    data=dataframe,
    x=None,
    y='tot_length',
    offset=0.3,
    width=0.1,
    linewidth=3,
    color='black')

# dendritic_length.save_figure(
#     saving_path / 'dendritic_length.png',
#     dpi=600)

# %% Dendritic compartment proportions

dataframe['apical%'] = dataframe['apical_length'] / dataframe['tot_length']
dataframe['basal%'] = dataframe['basal_length'] / dataframe['tot_length']

plot_data = dataframe[['filename', 'apical%', 'basal%']]

dendritic_proportions = dp.DataPlotter(
    figsize=(2.5, 3),
    font_size=12,
    y_lims=(0, 1),
    y_label='Dendritic compartments proportion',
    x_tick_labels=[],
    # x_ticks=([n for n in range(9)]),
    # x_tick_labels=([str(n) for n in range(9)])
    # y_ticks=([0, 20000, 40000, 60000, 80000, 100000]),
    # y_tick_labels=([0, 0.02, 0.04, 0.06, 0.08, 0.1])
)


dendritic_proportions.bar_plot(
    data=plot_data,
    x='filename',
    y='basal%',
    color='#B95B46'
)

dendritic_proportions.bar_plot(
    data=plot_data,
    x='filename',
    y='apical%',
    bottom=plot_data['basal%'],
    color='#46A4B9',
    alpha=0.8,
)

plt.axhline(
    0.5,
    linewidth=1.5,
    color='gray',
    ls='dotted',
    clip_on=False)


# dendritic_proportions.save_figure(
#     saving_path / 'dendritic_proportions.png',
#     dpi=600)

# %% N of z planes

z_planes = dp.DataPlotter(
    figsize=(1.7, 3),
    y_pad=15,
    font_size=12,
    y_lims=(30, 60),
    y_label='Z planes',
    # y_ticks=([0, 20000, 40000, 60000, 80000, 100000]),
    # y_tick_labels=([0, 0.02, 0.04, 0.06, 0.08, 0.1])
)

z_planes.box_plot(
    data=dataframe,
    x=None,
    y='n_z_planes',
    box_width=0.3,
    color='#808080')

z_planes.strip_plot(
    data=dataframe,
    x=None,
    y='n_z_planes',
    linewidth=1.5,
    edgecolor='#808080',
    fillcolor='none',
    jitter=0,
    strip_offset=0.3)

z_planes.display_mean(
    data=dataframe,
    x=None,
    y='n_z_planes',
    offset=0.3,
    width=0.1,
    linewidth=3,
    color='black')

# z_planes.save_figure(
#     saving_path / 'z_planes.png',
#     dpi=600)

# %% Hull area plot

hull_area = dp.DataPlotter(
    figsize=(1.7, 3),
    font_size=12,
    y_lims=(0, 80000),
    y_label='Hull area (mm2)',
    y_ticks=([0, 20000, 40000, 60000, 80000, 100000]),
    y_tick_labels=([0, 0.02, 0.04, 0.06, 0.08, 0.1])
)

hull_area.box_plot(
    data=dataframe,
    x=None,
    y='hull_area',
    box_width=0.3,
    color='#808080')

hull_area.strip_plot(
    data=dataframe,
    x=None,
    y='hull_area',
    linewidth=1.5,
    edgecolor='#808080',
    fillcolor='none',
    jitter=0,
    strip_offset=0.3)

hull_area.display_mean(
    data=dataframe,
    x=None,
    y='hull_area',
    offset=0.3,
    width=0.1,
    linewidth=3,
    color='black')

# hull_area.save_figure(
#     saving_path / 'hull_area.png',
#     dpi=600)

# %% Number of neurites plot

n_neurites = dp.DataPlotter(
    figsize=(1.5, 3),
    font_size=12,
    y_lims=(0, 40),
    y_label='Number of neurites',
    y_ticks=([0, 10, 20, 30, 40]),
)

n_neurites.box_plot(
    data=dataframe,
    x=None,
    y='n_neurites',
    box_width=0.3,
    color='#808080')

n_neurites.strip_plot(
    data=dataframe,
    x=None,
    y='n_neurites',
    linewidth=1.5,
    edgecolor='#808080',
    fillcolor='none',
    jitter=0,
    strip_offset=0.3)

n_neurites.display_mean(
    data=dataframe,
    x=None,
    y='n_neurites',
    offset=0.3,
    width=0.1,
    linewidth=3,
    color='black')

# n_neurites.save_figure(
#     saving_path / 'n_neurites.png',
#     dpi=600)

# %% Plot mean n rois per scanfield z

mean_n_rois = dp.DataPlotter(
    figsize=(1.5, 3),
    font_size=12,
    y_lims=(0, 10.),
    y_label='Mean number of ROI / scanfield',
    # y_ticks=([0, 10, 20, 30, 40]),
)

mean_n_rois.box_plot(
    data=dataframe,
    x=None,
    y='mean_n_roi_scanfields',
    box_width=0.3,
    color='#808080')

mean_n_rois.strip_plot(
    data=dataframe,
    x=None,
    y='mean_n_roi_scanfields',
    linewidth=1.5,
    edgecolor='#808080',
    fillcolor='none',
    jitter=0,
    strip_offset=0.3)

mean_n_rois.display_mean(
    data=dataframe,
    x=None,
    y='mean_n_roi_scanfields',
    offset=0.3,
    width=0.1,
    linewidth=3,
    color='black')

# mean_n_rois.save_figure(
#     saving_path / 'mean_n_rois.png',
#     dpi=600)

# %% Overall scanned area

scanned_area = dp.DataPlotter(
    figsize=(1.5, 3),
    font_size=12,
    y_lims=(0, 30000),
    y_label='Total scanned area (µm²) x 10³',
    y_ticks=([0, 5000, 10000, 15000, 20000, 25000, 30000]),
    # y_pad=15,
    y_tick_labels=([0, 5, 10, 15, 20, 25, 30])
)

scanned_area.box_plot(
    data=dataframe,
    x=None,
    y='tot_scanned_area',
    box_width=0.3,
    color='#808080')

scanned_area.strip_plot(
    data=dataframe,
    x=None,
    y='tot_scanned_area',
    linewidth=1.5,
    edgecolor='#808080',
    fillcolor='none',
    jitter=0,
    strip_offset=0.3)

scanned_area.display_mean(
    data=dataframe,
    x=None,
    y='tot_scanned_area',
    offset=0.3,
    width=0.1,
    linewidth=3,
    color='black')

# scanned_area.save_figure(
#     saving_path / 'scanned_area.png',
#     dpi=600)

# %% Plot neuronal skeletons

skeletons = dp.ElectrophyPlotter(
    figsize=(6, 6),
    grid=(3, 3),
    y_label=''
)

i = 0

for row in range(3):
    for column in range(3):

        date, cell_n = filenames[i].split('_cell_')

        image_name = Path('Y:\\Vincenzo',
                          date,
                          f'cell_{cell_n}',
                          f'{date}_cell{cell_n}_stack_00001.tif')
        swc_name = Path('Y:\\Vincenzo',
                        date,
                        f'cell_{cell_n}',
                        f'{date}_cell{cell_n}_stack_00001.swc')

        morph = rp.Morphology(image_name, swc_name)
        morph.plot(morph.neuron, ax=skeletons[row, column])

        skeletons._format_ax(ax=skeletons[row, column])

        i += 1

# skeletons.save_figure(
#     saving_path / 'skeletons.png',
#     dpi=600)

# %% Example Hull area

main_folder = Path('Y:\\Vincenzo')
date = '240130'
cell_n = '0001'

swc_filename = rp.get_filename(main_folder, date, cell_n, 'swc')
image_filename = rp.get_filename(main_folder, date, cell_n, 'tif')

morph = rp.Morphology(image_filename, swc_filename)

hull_area_tracing = dp.ElectrophyPlotter(
    figsize=(3, 3),
    y_label=''
)

morph.plot(
    morph.neuron,
    ax=hull_area_tracing.ax)

morph.neuron.hull(
    ax=hull_area_tracing.ax,
    facecolor='none',
    linecolor='#B95B46',
    terminal_point_color='#46A4B9')

hull_area_tracing._format_ax(ax=hull_area_tracing.ax)

# hull_area_tracing.save_figure(
#     saving_path / 'hull_area_tracing.png',
#     dpi=600)

# %% Sholl analysis example

sholl_df_apical = pd.DataFrame()
sholl_df_basal = pd.DataFrame()

for name in filenames:

    date, cell_n = name.split('_cell_')

    image_name = Path('Y:\\Vincenzo',
                      date,
                      f'cell{cell_n}',
                      f'{date}_cell{cell_n}_stack_00001.tif')
    swc_name = Path('Y:\\Vincenzo',
                    date,
                    f'cell{cell_n}',
                    f'{date}_cell{cell_n}_stack_00001.swc')

    morph = rp.Morphology(image_name, swc_name)
    sholl_apical, sholl_basal, sholl_radii = morph.neuron.sholl(
        radius_step=20,
        n_radii=20,
        intersection_color='#B95B46',
        circle_linewidth=0.5,
        size=150
    )
    df_apical = pd.DataFrame([sholl_apical], columns=sholl_radii, index=[name])
    df_basal = pd.DataFrame([sholl_basal], columns=sholl_radii, index=[name])
    # Append to respective DataFrames
    sholl_df_apical = pd.concat([sholl_df_apical, df_apical])
    sholl_df_basal = pd.concat([sholl_df_basal, df_basal])

for sholl_df in [sholl_df_apical, sholl_df_basal]:
    sholl_df.reset_index(inplace=True)
    sholl_df.rename(columns={'index': 'filename'}, inplace=True)

melted_dfs = []
for sholl_df, adjust_radii in zip(
        [sholl_df_apical, sholl_df_basal], [False, True]):
    melted_df = sholl_df.melt(
        id_vars='filename',
        var_name='Sholl Radius',
        value_name='Intersection Count')
    if adjust_radii:
        melted_df['Sholl Radius'] = -melted_df['Sholl Radius'].astype(int)
    else:
        melted_df['Sholl Radius'] = melted_df['Sholl Radius'].astype(int)
    melted_dfs.append(melted_df)

# Combine the melted DataFrames
melted_df_combined = pd.concat(melted_dfs)

mean_values = (
    melted_df_combined.groupby(
        'Sholl Radius')['Intersection Count'].mean().reset_index())
sem_values = (
    melted_df_combined.groupby(
        'Sholl Radius')['Intersection Count'].sem().reset_index())

CI_low = (mean_values['Intersection Count'] - 1.96
          * sem_values['Intersection Count'])
CI_high = (mean_values['Intersection Count'] + 1.96
           * sem_values['Intersection Count'])


sholl_lines = dp.DataPlotter(
    figsize=(7, 4),
    font_size=24,
    y_label='Intesection count',
    x_label='Radial distance from soma (µm)',
    hidden_axis=['top', 'right'],
    hide_xticks=False,
    x_lims=(-250, 350),
    y_lims=(0, 15),
    x_ticks=np.arange(-250, 400, 100)
)

sholl_lines.line_plot(
    data=melted_df_combined,
    x='Sholl Radius',
    y='Intersection Count',
    hue='filename',
    color='#B95B46',
    legend=None,
    markers='',
    linewidth=0.8,
    alpha=0.5,
    clip_on=True
)

sholl_lines.plot_data(
    x=mean_values['Sholl Radius'],
    y=mean_values['Intersection Count'],
    color='black',
    linewidth=2)

sholl_lines.confidence_interval(
    mean_values['Sholl Radius'],
    mean_values['Intersection Count'],
    CI_low,
    CI_high,
    fill_color='#46A4B9',
    alpha=0.5,
    clip_on=True)

# sholl_lines.save_figure(
#     saving_path / 'sholl_lines.png',
#     dpi=600)

# sholl_lines.save_figure(
#     Path(r'Y:\SynEmo\figures4poster\sholl_apical_basal.png'),
#     dpi=1000)

# %% plot skeleton and scanfield

date, cell_n = filenames[5].split('_cell_')

image_name = Path('Y:\\Vincenzo',
                  date,
                  f'cell_{cell_n}',
                  f'{date}_cell{cell_n}_stack_00001.tif')
swc_name = Path('Y:\\Vincenzo',
                date,
                f'cell_{cell_n}',
                f'{date}_cell{cell_n}_stack_00001.swc')

stack = rp.Stack(image_name)
morph = rp.Morphology(image_name, swc_name)
sf = rp.Scanfields(image_name, swc_name)

create_roi = dp.ElectrophyPlotter(
    figsize=(10, 4),
    grid=(1, 3),
    y_label='',
)

morph.plot(
    morph.neuron,
    ax=create_roi[0],
    axis_lims=morph.corners_um,
    color='black')

create_roi.plot_data(
    x=np.arange(100, 200),
    y=np.repeat(100, 100),
    row=1,
    col=0,
    color='black',
    linewidth=3)

morph.plot(
    morph.neuron,
    ax=create_roi[1],
    axis_lims=morph.corners_um,
    color='black')
sf.plot(
    sf.neuComp[13],
    ax=create_roi[1],
    axis_lims=morph.corners_um,
    edgecolor='red',
    linewidth=2)
sf.plot(
    sf.neuComp,
    ax=create_roi[2],
    axis_lims=morph.corners_um,
    edgecolor='red')

create_roi._format_ax(ax=create_roi[0])
create_roi._format_ax(ax=create_roi[1])
create_roi._format_ax(ax=create_roi[2])
create_roi[0].set_aspect('equal')
create_roi[1].set_aspect('equal')
create_roi[2].set_aspect('equal')

# create_roi.save_figure(
#     saving_path / 'create_roi.png',
#     dpi=600)

# %%

apical_basal_plot = dp.ElectrophyPlotter(
    figsize=(3, 3),
    grid=(1, 1),
    y_label='')

morph.plot(
    morph.apical,
    ax=apical_basal_plot.axes,
    axis_lims=morph.corners_um,
    color='#46A4B9')

morph.plot(
    morph.basal,
    ax=apical_basal_plot.axes,
    axis_lims=morph.corners_um,
    color='#B95B46')

apical_basal_plot._format_ax(ax=apical_basal_plot.axes)
apical_basal_plot.axes.set_aspect('equal')

# %%

date, cell_n = filenames[1].split('_cell_')

image_name = Path('Y:\\Vincenzo',
                  date,
                  f'cell_{cell_n}',
                  f'{date}_cell{cell_n}_stack_00001.tif')
swc_name = Path('Y:\\Vincenzo',
                date,
                f'cell_{cell_n}',
                f'{date}_cell{cell_n}_stack_00001.swc')

stack = rp.Stack(image_name)
morph = rp.Morphology(image_name, swc_name)
sf = rp.Scanfields(image_name, swc_name)

neuron_plot = dp.ElectrophyPlotter(
    figsize=(4, 4),
    grid=(1, 1),
    y_label='',
)

morph.plot(
    morph.neuron,
    ax=neuron_plot.axes,
    axis_lims=morph.corners_um,
    color='black')

sf.plot(
    sf.neuComp[20][1],
    ax=neuron_plot.axes,
    axis_lims=morph.corners_um,
    edgecolor='red',
    linewidth=2)

sf.plot(
    sf.neuComp[21][2],
    ax=neuron_plot.axes,
    axis_lims=morph.corners_um,
    edgecolor='red',
    linewidth=2)

sf.plot(
    sf.neuComp[21][3],
    ax=neuron_plot.axes,
    axis_lims=morph.corners_um,
    edgecolor='red',
    linewidth=2)

neuron_plot._format_ax(ax=neuron_plot.axes)
neuron_plot.axes.set_aspect('equal')

neuron_plot.plot_data(
    x=np.arange(-100, -50),
    y=np.repeat(40, 50),
    row=0,
    col=0,
    color='black',
    linewidth=3)