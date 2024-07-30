""" Created on Wed May 29 18:31:42 2024
    @author: dcupolillo """

import tensorflow as tf
import numpy as np
from tracing.data_augmentation import augment_image_and_mask


def data_generator(
        images: np.ndarray,
        masks: np.ndarray,
        batch_size: int
) -> tf.data.Dataset:
    """
    Create a data generator for training
    with data augmentation using albumentations.
    """

    dataset = tf.data.Dataset.from_tensor_slices((images, masks))

    def _augment(image, mask):
        aug_img, aug_mask = tf.numpy_function(
            func=augment_image_and_mask,
            inp=[image, mask],
            Tout=[tf.float32, tf.float32])
        aug_img.set_shape((1024, 1024, 1))
        aug_mask.set_shape((1024, 1024, 1))

        return aug_img, aug_mask

    dataset = dataset.map(
        lambda x, y: (tf.cast(x, tf.float32), tf.cast(y, tf.float32)))
    dataset = dataset.map(
        _augment, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    dataset = dataset.batch(batch_size)
    dataset = dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)

    return dataset
