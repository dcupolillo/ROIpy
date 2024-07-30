""" Created on Wed May 29 14:23:07 2024
    @author: dcupolillo """

import albumentations as A
import cv2
import numpy as np
from typing import Tuple


def get_augmenter() -> A.Compose:
    """
    Defines used augmentations.

    Returns:
        albumentations.Compose: Augmentation pipeline.
    """
    aug = A.Compose([
        A.RandomBrightnessContrast(p=0.25),
        A.Rotate(limit=10, border_mode=cv2.BORDER_REFLECT, p=0.5),
        A.RandomRotate90(p=0.5),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.Blur(p=0.2),
        A.GaussNoise(p=0.5)
    ], p=1)

    return aug


def augment_image_and_mask(
        image: np.ndarray,
        mask: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply augmentations to an image and its corresponding mask.

    Args:
        image (numpy.ndarray): Input image.
        mask (numpy.ndarray): Corresponding mask.

    Returns:
        tuple: Augmented image and mask.
    """

    augmentations = get_augmenter()
    augmented = augmentations(
        image=image,
        mask=mask
    )

    return augmented['image'], augmented['mask']
