from .core.structures import Stack, Morphology, Scanfields
from .GUI.gui import main
from .core.utils.utils import get_filename
from .github import GitRepository


try:
    with open("VERSION", "r") as version_file:
        __version__ = version_file.read().strip()
except FileNotFoundError:
    # Set a default version if the VERSION file is not found
    __version__ = "unknown"