# ROIpy
 
## Description

ROIpy is a python package for Region of Interest (ROI) semi-automatic
generation and placement for neuroimaging of neuronal dendrites of
individual neurons :microscope::brain:.
It provides a tool for defining, managing, visualizing and analyzing dendritic ROIs.

Designed to interact with [Vidrio ScanImage software](https://vidriotechnologies.com/).

## Installation

Simply copy the folder "ROIpy" within your project folder :file_folder:.
Ensure the folder is in your system path.

```
import sys
sys.path.append('path/to/ROIpy')
```

## Features

`ROIpy` is composed of 3 main hierarchically-organized structures:

1. `Stack`: Represents a stack of images of a given neuron, initializing several parameters.
2. `Morphology`: Represents the digitized and structured anatomy of a dendritic arborization.
3. `Scanfields`: Represents the rotated rectangular ROIs that encapsulate the entire dendritic tree region.

`Morphology` and `Scanfields` are further composed of **bundles** which in turn are
formed by individual **components**. Each strucures handles metadata, indexing, and
plotting methods for visual inspection.


### Stack

The `Stack` class initializes with the path to a `.tif` image file (xyz, single channel) generated with **ScanImage**,
and loads the image data along with its **ScanImage** metadata.
The image should include a number of stacked images (z layers) including as many dendrites
as possible, recorded in the channel of the used morphological filler/marker.
`Stack` is the initial building block of the digitized dendritic structures.

**Example Usage:**
```
import ROIpy as rp

# Initialize a stack of neuron images
stack = rp.Stack('path/to/image.tif')

# Plot the stack image
stack.plot(cmap='viridis', norm=(100, 2000))
```

![Example of a stack](descr_images/stack.png)

### Morphology

The `Morphology` class inherits from `Stack` and represents the neuronal
morphology data. Consitutes the structure upon which rectangular ROIs are
defined and placed. It takes a `.swc` file as input.

A `Morphology` object includes a series of `NodeBudle`:

1. `neuron`: the structure of the overall neuron, which includes all the others.
2. `apical`: the apical dendritic compartment.
3. `basal`: the basal dendritic compartment.
4. `soma`: the cell body of the neuron.

Each `NodeBundle` is composed of a series of `Node` components, defining the
features of every individual point within the structure.

**Example Usage:**
```
# Initialize the morphology with image and tracing files
morph = rp.Morphology('path/to/image.tif', 'path/to/tracing.swc')

# Plot the morphology
morph.plot(morph.neuron, show_nodes=True, cmap='jet', linewidth=1)
```

![Example of a morph neuron](descr_images/morph.png)

### Scanfields

The `Scanfields` class inherits from `Morphology` and manages the creation of rotated rectangular scanfields for imaging. It uses various imaging parameters to generate the ROIs.
Refers to **Scanimage** `scanimage.mroi.scanfield.fields.RotatedRectangle` objects. Generates and saves :floppy_disk: 
a number of single-plane json-formatted  `.roi` files corresponding to the different z layers to be provided to **ScanImage** ROI Editor for multiple ROI (mROI) definition.

Similarly to `Morphology` bundles, a `Scanfield` object includes a series of `ScanfieldBundle`:

1. `neuComp`: The ensemble of dendritic ROIs, covering the whole neuron.
2. `apiComp`: ROIs covering the apical dendritic compartment.
3. `basComp`: ROIs coveing the basal dendritic compartment.

Each `ScanfieldBundle` is a collection of individual `Roi` components, defining the
features of every individual rectangle within the structure.

**Example Usage:**

```
# Initialize the scanfields with image and tracing files
sf = rp.Scanfields('path/to/image.tif', 'path/to/tracing.swc')

# Plot the scanfields
sf.plot(sf.neuComp, edgecolor='red')
```

![Example of a neuronal scanfield](descr_images/sf.png)