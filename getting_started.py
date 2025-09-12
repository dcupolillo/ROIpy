""" Created on Thu Jul 27 15:25:49 2023
    @author: dcupolillo """

import ROIpy as rp
import matplotlib.pyplot as plt
from pathlib import Path

date = "240828"
cell_n = "cell0001"
data_folder = Path(r"Y:\Vincenzo")
neuron_path = Path(rf"{date}\{cell_n}")

stack_filename = Path(
    data_folder / neuron_path / rf"{date}_{cell_n}_stack_00001.tif")
swc_filename = Path(
    data_folder / neuron_path / rf"{date}_{cell_n}_stack_00001.swc")

# generate the structures Objects
stack = rp.Stack(stack_filename)
morph = rp.Morphology(swc_filename, stack)
sf = rp.Scanfields(morph)

# generate individual branches
branch = morph.neuron.get_branch(11)

# plot the stack
rp.plot(stack.image)
rp.plot(stack.image, stack.metadata, cmap='viridis', norm=(100, 2000))

# plot the morphology structure
rp.plot(morph.neuron)
rp.plot(morph.neuron, show_nodes=True, cmap='jet')

# plot the scanfields
rp.plot(sf.neuron)
rp.plot(sf.neuron, sf.metadata, edgecolor='red', cmap='viridis')

# plot them together
fig, ax = plt.subplots()
ax.set_aspect('equal')
rp.plot(stack.image, stack.metadata, ax=ax)
rp.plot(morph.neuron, morph.metadata, ax=ax, color="lime")
rp.plot(sf.neuron, sf.metadata, ax=ax, edgecolor="fuchsia")
plt.show()

# Start the graphical interface
rp.run_app()
