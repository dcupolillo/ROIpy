import numpy as np
from pathlib import Path
import cv2
from typing import Tuple


def load_images(
        image_dir: Path,
        mask_dir: Path,
        target_size: Tuple[int, int]
) -> Tuple[np.ndarray, np.ndarray]:
    """Load images and masks from the specified directories."""

    image_paths = sorted(image_dir.glob('*.tif'))
    mask_paths = sorted(mask_dir.glob('*.tif'))

    images = []
    masks = []

    for img_path, mask_path in zip(image_paths, mask_paths):
        image = cv2.imread(
            str(img_path), cv2.IMREAD_UNCHANGED).astype(np.int16)
        mask = cv2.imread(
            str(mask_path), cv2.IMREAD_UNCHANGED).astype(np.int16)

        image = cv2.resize(image, target_size)
        mask = cv2.resize(mask, target_size)

        images.append(image)
        masks.append(mask)

    return np.array(images), np.array(masks)


def resize_images(
        images: np.ndarray,
        target_size: Tuple[int, int]
) -> np.ndarray:
    """
    Resize images to a target size.

    Parameters:
    images (np.ndarray): Array of images to resize.
    target_size (Tuple[int, int]): Desired size of the output images.

    Returns:
    np.ndarray: Array of resized images.
    """

    resized_images = np.array(
        [cv2.resize(image, target_size) for image in images])

    return resized_images
