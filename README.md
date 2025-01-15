# ROIpy

## Description

**ROIpy** is a python package for ROI (Region of Interest) semi-automatic generation and placement for functional imaging of neuronal dendrites of individual neurons :microscope::brain:. It provides a tool for defining, managing and visualizing dendritic ROIs. In addition, provides a benchmark for analyzing morphological data such as dendritic structure.

Designed to interface with [Vidrio ScanImage software](https://vidriotechnologies.com/).

### ScanImage setup

ROIpy is designed to facilitate scanning along dendritic arborization. In Scanimage, it works for **Linear Scan - Frame scan** configuration (_Galvo-Galvo_). ROIpy is developed to overcome the inherent 2D limitation of arbitrary scanning, by generating a set of discrete planes populated with scattered rectangular ROIs spanning the depth of the neuron.

It outputs `.roi` files which can be loaded and are interpreted by ScanImage **mROI Editor Window**.

### Dendrite tracing

Tested to work with `.swc` files generated with ImageJ Fiji plugin [Simple Neurite Tracer (SNT)](https://imagej.net/plugins/snt/). `.swc` files generated with different softwares are not tested and may raise errors. Common labels are **apical dendrite** or **basal dendrite** or **soma**.

## Installation

#### Option 1: Install via Git Clone

Clone the repository and install it locally:

```git
git clone https://github.com/dcupolillo/ROIpy.git
```

#### Option 2: Manual copy

Simply copy the folder "ROIpy" within your project folder :file_folder:. Ensure the folder is in your system path.

```python
import sys
sys.path.append("path/to/ROIpy")
```

## Features

`ROIpy` is composed of 3 main structures: **Stack**, **Morphology**, **Scanfields**. Morphology and Scanfields are further composed of **bundles** which in turn are formed by individual **components**. Each strucures handles metadata, indexing, and plotting methods for visual inspection.

#### Stack

Represents a stack of images of a given neuron, which includes all dendrites within its depth.
The initial Stack is acquired from Scanimage. Each z-layer defines the discrete planes where ROIs will be placed on. The stack is necessary to outline the dendritic structure using SNT.

#### Morphology

Object defining the digitized structural anatomy of a dendritic arborization drawn using SNT. This object is necessary to drive the placement of dendritic rectangular ROIs. A morphology object can also be used to run morphological analysis of dendritic structure.

#### Scanfields

Represents the rotated rectangular ROIs that encapsulate the entire dendritic tree region.

## Dependency on Neuronpath

`ROIpy` objects initialization depends on the custom dataset handler `Neuronpath` (find repository [here](https://github.com/dcupolillo/neuronpath)).

**Example Usage:**

```python
from neuronpath.path import neuronpath
paths = neuronpath("date_string", cell_number)

# date_string: str (in the format YYMMDD i.e. "240505")
# cell_number: int (i.e. 1)
```

### Stack

The `Stack` class initializes with the path to a `.tif` image file (xyz, single channel, shape = [z, x, y]) generated with **ScanImage**, and loads the image data along with its **ScanImage** metadata. The image should include a number of stacked images (z layers) including as many dendrites as possible, recorded in the channel of the used morphological filler/marker. `Stack` is the initial building block of the digitized dendritic structures.

**Example Usage:**

```python
import ROIpy as rp

# Initialize a stack of neuron images
stack = rp.Stack(paths)

# Plot the stack image
stack.plot(cmap="viridis", norm=(100, 2000))
```

![Example of a stack](assets/stack.png)

### Morphology

The `Morphology` class inherits from `Stack` and represents the neuronal morphology data. Consitutes the structure upon which rectangular ROIs are defined and placed. It takes a `.swc` file as input.

A `Morphology` object includes a series of `NodeBudle`:

1. `neuron`: the structure of the overall neuron, which includes all the others.
2. `apical`: the apical dendritic compartment.
3. `basal`: the basal dendritic compartment.
4. `soma`: the cell body of the neuron.

Each `NodeBundle` is composed of a series of `Node` components, defining the features of every individual point within the structure.

**Example Usage:**

```python
# Initialize the morphology with image and tracing files
morph = rp.Morphology(paths)

# Plot the morphology
morph.plot(morph.neuron, show_nodes=True, cmap="jet", linewidth=1)
```

![Example of a morph neuron](assets/morph.png)

### Scanfields

The `Scanfields` class inherits from `Morphology` and manages the creation of rotated rectangular scanfields for imaging. It uses various imaging parameters to generate the ROIs. Refers to **Scanimage** `scanimage.mroi.scanfield.fields.RotatedRectangle` objects. Generates and saves :floppy_disk: a number of single-plane json-formatted `.roi` files corresponding to the different z layers to be provided to **ScanImage** ROI Editor for multiple ROI (mROI) definition.

Similarly to `Morphology` bundles, a `Scanfield` object includes a series of `ScanfieldBundle`:

1. `neuComp`: The ensemble of dendritic ROIs, covering the whole neuron.
2. `apiComp`: ROIs covering the apical dendritic compartment.
3. `basComp`: ROIs coveing the basal dendritic compartment.

Each `ScanfieldBundle` is a collection of individual `Roi` components, defining the features of every individual rectangle within the structure.

**Example Usage:**

```python
# Initialize the scanfields with image and tracing files
sf = rp.Scanfields(paths)

# Plot the scanfields
sf.plot(sf.neuComp, edgecolor="red")
```

![Example of a neuronal scanfield](assets/sf.png)
