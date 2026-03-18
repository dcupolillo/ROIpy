"""
ROIpy is a package for region of interest (ROI) creation
compatible with ScanImage.
"""

__version__ = "0.1.0"

from .core.structures import Stack, Morphology, Scanfields
from .GUIv2.main import run_app

# Import plot submodule
from .plot.plot import plot, animate

from .analysis import stats

import sys
from pathlib import Path


def _info():
    """display information about the ROIpy package."""
    import platform
    import numpy
    print("==== ROIpy Information ====\n")
    print("Python", sys.version)
    print("System:", platform.system(), platform.release())
    print("numpy version:", numpy.__version__)
    print("ROIpy version:", __version__)
    print("ROIpy path:", Path(__file__).parent.resolve())
    print("\n")


def showInfo():
    _info()


def help():
    """launch the ROIpy project page in a browser."""
    import webbrowser
    webbrowser.open(
        "http://github.com/dcupolillo/ROIpy/tree/GUI_new_version", new=2)
    
__all__ = [
    "Stack",
    "Morphology",
    "Scanfields",
    "run_app",
    "plot",
    "animate",
    "stats",
    "showInfo",
    "help"
]
