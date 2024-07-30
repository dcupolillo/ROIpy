from .core.structures import Stack, Morphology, Scanfields
from .GUI.gui import main
from .core.utils.utils import get_filename
from .github import (
    publish_to_github, setup_https_authentication, update_to_github)


try:
    with open("VERSION", "r") as version_file:
        __version__ = version_file.read().strip()
except FileNotFoundError:
    # Set a default version if the VERSION file is not found
    __version__ = "unknown"