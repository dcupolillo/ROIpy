""" Created on Thu Jul 27 15:25:49 2023
    @author: dcupolillo """

import ROIpy as rp
import matplotlib.pyplot as plt
from neuronpath.path import neuronpath
from github_project import GitRepository

paths = neuronpath('240724', 2)

# generate the structures Objects
stack = rp.Stack(paths)
morph = rp.Morphology(paths)
sf = rp.Scanfields(paths)

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

# Publish to github
repo = GitRepository("ROIpy")  # Initialize a new repository
repo.add_all()  # Add all files and commit
repo.commit("Update morphology and Scanfields with saving to h5 methods")
repo.push('main')  # Push changes to the remote repository to the main branch

