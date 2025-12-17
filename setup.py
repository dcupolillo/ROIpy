from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long_description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="ROIpy",
    version="0.1.0",
    description="Python package for ROI semi-automatic generation and placement for functional imaging of neuronal dendrites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="dcupolillo",
    author_email="",
    url="https://github.com/dcupolillo/ROIpy",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.23.5",
        "pandas>=1.5.3",
        "matplotlib>=3.8.2",
        "pyqt>=5.15.10",
        "pyqtgraph>=0.13.3",
        "tifffile>=2024.2.12",
        "h5py>=3.10.0",
        "flammkuchen",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Visualization",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="roi imaging neuron dendrite scanimage",
)
