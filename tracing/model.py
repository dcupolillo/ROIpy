""" Created on Wed May 29 14:51:19 2024
    @author: dcupolillo """

from typing import Tuple
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, Concatenate, MaxPool2D, UpSampling2D, BatchNormalization, Activation, Add


def convlayer(
        x,
        filters: int,
        activation: str,
        name: str,
        residual=None,
        use_batchnorm: bool = True
) -> tf.keras.layers.Layer:
    """Convolutional layer with normalization and residual connection."""
    x = Conv2D(filters, 3, padding='same', use_bias=False, name=name)(x)

    if use_batchnorm:
        x = BatchNormalization(name=name+"_BN")(x)

    if residual is not None:
        x = Add(name=name+"_residual_connection")([residual, x])

    x = Activation(activation, name=name+"_activation")(x)
    return x


def identity(
        x,
        filters: int,
        name: str
) -> tf.keras.layers.Layer:
    """Identity layer for residual layers."""
    return Conv2D(filters, 1, padding='same', use_bias=False, name=name)(x)


def decoder(
        x,
        filters: int,
        layers: int,
        to_concat: list,
        name: str,
        activation: str
) -> tf.keras.layers.Layer:
    """Decoder for neural network."""
    for i in range(layers):
        x = UpSampling2D()(x)
        x = Concatenate()([x, to_concat.pop()])
        x = convlayer(
            x,
            filters * 2**(layers-1-i), activation,
            f"{name}_dec_layer{layers-i}_conv1")
        x = convlayer(
            x,
            filters * 2**(layers-1-i), activation,
            f"{name}_dec_layer{layers-i}_conv2")

    x = Conv2D(1, 1, padding='same', name=name, activation='sigmoid')(x)
    return x


def unet_model(
        input_shape: Tuple[int, int, int],
        filters: int = 32,
        layers: int = 4,
        activation: str = "swish"
) -> Model:
    """
    U-Net TensorFlow Keras Model with residual connections
    and batch normalization.
    """

    to_concat = []
    model_input = Input(input_shape, name="input")
    x = model_input

    for i in range(layers):
        residual = identity(x, filters * 2**i, f"enc_layer{i}_identity")
        x = convlayer(
            x,
            filters * 2**i, activation,
            f"enc_layer{i}_conv1")
        x = convlayer(
            x,
            filters * 2**i, activation,
            residual=residual, name=f"enc_layer{i}_conv2")

        to_concat.append(x)
        x = MaxPool2D()(x)

    x = convlayer(x, filters * 2**(i+1), activation, "latent_conv")

    output = decoder(x, filters, layers, to_concat, "output", activation)

    return Model(model_input, output)
