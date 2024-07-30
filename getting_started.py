""" Created on Thu Jul 27 15:25:49 2023
    @author: dcupolillo """

import ROIpy as rp
import matplotlib.pyplot as plt
from neuronpath.path import neuronpath

paths = neuronpath('240123', 1)

# generate the structures Objects
stack = rp.Stack(paths.stackpath)
morph = rp.Morphology(paths.stackpath, paths.tracepath)
sf = rp.Scanfields(paths.stackpath, paths.tracepath)

# plot the stack
stack.plot()
stack.plot(cmap='viridis', norm=(100, 2000))

# plot the morphology structure
morph.plot(morph.neuron)
morph.plot(morph.neuron, show_nodes=True, cmap='jet', linewidth=1)

# plot the scanfields
sf.plot(sf.neuComp)
sf.plot(sf.neuComp, edgecolor='red', cmap='viridis')

# plot them together
fig, ax = plt.subplots()
ax.set_aspect('equal')
stack.plot(ax=ax)
morph.plot(morph.neuron, ax=ax)
sf.plot(sf.neuComp, ax=ax)

# Start the graphical interface
rp.main()



sf.create_roi(sf.neuComp)