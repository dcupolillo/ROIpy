""" Created on Wed May 29 16:23:48 2024
    @author: dcupolillo """

import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, CSVLogger, LearningRateScheduler
from tracing.model import unet_model
from tracing.data_generator import data_generator
from sklearn.model_selection import train_test_split
from typing import Tuple
import numpy as np


def schedule(epoch, lr):
    """Learning rate schedule function."""
    if epoch < 15:
        return lr
    else:
        return lr * tf.math.exp(-0.1)


def train_unet(
        images: np.ndarray,
        masks: np.ndarray,
        input_shape: Tuple[int, int, int, int],
        batch_size: int,
        epochs: int,
        filters: int = 32,
        layers: int = 4,
        activation: str = "swish"
) -> tf.keras.Model:
    """Train U-Net model."""
    # Reshape images and masks for the model
    images = images[..., np.newaxis]  # Add channel dimension for 3D data
    masks = masks[..., np.newaxis]

    # Normalize images
    images = images / np.max(images)

    # Split data into training and validation sets
    X_train, X_val, y_train, y_val = train_test_split(
        images, masks, test_size=0.2, random_state=42)

    # Create data generators
    train_dataset = data_generator(X_train, y_train, batch_size)
    val_dataset = data_generator(X_val, y_val, batch_size)

    # Initialize model
    model = unet_model(input_shape, filters, layers, activation)
    model.summary()

    # Compile model
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy'])

    # Set up callbacks
    checkpoint = ModelCheckpoint(
        'unet_model.h5', save_best_only=True, monitor='val_loss', mode='min')
    early_stop = EarlyStopping(
        monitor='val_loss', patience=10, restore_best_weights=True)
    csv_logger = CSVLogger('training.log', append=True)
    lr_scheduler = LearningRateScheduler(schedule)

    # Train the model
    model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=epochs,
        callbacks=[checkpoint, csv_logger, lr_scheduler, early_stop])

    return model
