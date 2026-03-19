""" Created on Tue Aug 27 16:49:49 2024
    @author: dcupolillo """

from __future__ import annotations
from ROIpy.core.structures import Stack, Morphology, Scanfields
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QMainWindow, QFrame, QGridLayout, QLabel, QSlider, QWidget, QVBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal


class ImageView(pg.ImageView):

    def __init__(
            self,
            parent: QMainWindow,
            *args,
            **kwargs
    ) -> None:
        """
        Custom ImageView that initializes with a fixed size and hides the
        ROI and menu buttons.
        
        Parameters
        ----------
        parent : QMainWindow
            The parent window to which this ImageView belongs.
        *args
            Additional positional arguments passed to the base ImageView class.
        **kwargs
            Additional keyword arguments passed to the base ImageView class.
        """
        super().__init__(*args, **kwargs)

        # Set ImageView size relative to the parent window
        image_window_ratio = 1.5
        window_width = parent.width()
        window_height = parent.height()
        base_size = min(window_width, window_height) * image_window_ratio

        # Apply the square size
        self.setMinimumWidth(int(base_size))
        self.setMinimumHeight(int(base_size))
        self.setMaximumWidth(int(base_size))
        self.setMaximumHeight(int(base_size))

        # Customize ImageView
        self.getHistogramWidget().setFixedWidth(80)
        self.ui.roiBtn.setVisible(False)
        self.ui.menuBtn.setVisible(False)


class CustomSlider(QWidget):

    def __init__(
            self,
            tick_values: list = None,
            orientation: Qt.Orientation = Qt.Horizontal,
            parent: QWidget = None
    ) -> None:
        """
        Custom slider widget that includes a label to display the current value
        and supports custom tick values.
        
        Parameters
        ----------
        tick_values : list, optional
            A list of values to be used as ticks on the slider. If None, a default
            range of 0-100 will be used.
        orientation : Qt.Orientation, optional
            The orientation of the slider (Qt.Horizontal or Qt.Vertical). Default is
            Qt.Horizontal.
        parent : QWidget, optional
            The parent widget for this slider. Default is None.
            """

        super().__init__(parent)

        # Layout for the slider and its labels
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Create the slider itself
        self.slider = QSlider(orientation, self)
        self.slider.setTickPosition(QSlider.TicksBelow)
        layout.addWidget(self.slider)

        # Set the tick values and map them to the slider's range
        if tick_values:
            self.set_tick_values(tick_values)
        else:
            self.slider.setRange(0, 100)  # Default range

        # Add a label to display the current value
        self.value_label = QLabel('0', self)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        # Connect the slider's value change to update the value label
        self.slider.valueChanged.connect(self.update_value_label)

    def set_tick_values(self, tick_values: list) -> None:
        """Set tick values and adjust the slider range accordingly."""

        self.tick_values = tick_values
        self.slider.setRange(0, len(tick_values) - 1)
        self.slider.setTickInterval(1)
        self.slider.setSingleStep(1)

    def update_value_label(self):
        """Update the label displaying the current slider value."""

        value = self.slider.value()
        if hasattr(self, 'tick_values'):
            self.value_label.setText(str(self.tick_values[value]))
        else:
            self.value_label.setText(str(value))

    def set_label_text(self, text: str) -> None:
        """Set the label text."""
        self.label.setText(text)

    def set_slider_value(self, value: int) -> None:
        """Set the slider's value based on the tick list."""
        if hasattr(self, 'tick_values'):
            if value in self.tick_values:
                index = self.tick_values.index(value)
                self.slider.setValue(index)
        else:
            self.slider.setValue(value)

    def get_slider(self) -> QSlider:
        """Get the underlying QSlider object."""
        return self.slider


class Canvas(QFrame):

    which_scanfield_signal = pyqtSignal(str)

    def __init__(self, parent: QMainWindow) -> None:
        """
        Canvas class that manages the display of images, morphology, and scanfield
        ROIs. It includes an ImageView for displaying images and sliders for
        navigating through Z-planes and channels.
        
        Parameters
        ----------
        parent : QMainWindow
            The parent window to which this canvas belongs.
        """

        super().__init__(parent)

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.stack = None
        self.morph = None
        self.sf = None
        self.is_multichannel = False
        self.normalization_settings = None
        self.is_z_slider = False
        self.plot_morph_data = None
        self.is_morph_plot = False
        self.which_morph_plot = None
        self.is_scanfield_plot = False
        self.which_scanfield_plot = None
        self.is_max_proj_active = False
        self.rects = []

        self.add_image_view(parent)

    def add_image_view(self, parent: QMainWindow) -> None:
        """Add custom ImageView to the layout."""

        self.imv = ImageView(parent, view=pg.PlotItem())
        self.imv.getView().showGrid(True, True)
        self.layout.addWidget(self.imv, 0, 0, 1, 3)
        self.imv.getHistogramWidget().region.sigRegionChanged.connect(
            self.handle_histogram)

    def add_slider(self) -> None:
        """Create the Z-slider using the CustomSlider class."""

        self.z_slider = CustomSlider(orientation=Qt.Horizontal)
        self.layout.addWidget(self.z_slider, 1, 0, 1, 3)
        self.z_slider.slider.valueChanged.connect(self.update_image)

        # The color slider will only be enabled if the image is multichannel
        self.color_slider = CustomSlider(orientation=Qt.Horizontal)
        self.layout.addWidget(self.color_slider, 2, 0, 1, 3)
        self.color_slider.setVisible(False)
        self.color_slider.slider.valueChanged.connect(self.update_image)

    def get_structures(
            self,
            stack: Stack,
            morph: Morphology,
            sf: Scanfields
    ) -> None:
        """Handle the received structure signal and initialize the stack."""

        self.stack = stack
        self.morph = morph
        self.sf = sf
        self.set_stack()

    def set_stack(self) -> None:
        """Initialize the image stack and enable the Z slider."""

        self.add_slider()
        self.z_slider.slider.setEnabled(True)
        self.z_slider.set_tick_values(self.stack.zs)
        self.z_slider.set_slider_value(0)
        self.is_z_slider = True

        if len(self.stack.image.shape) == 4:
            self.is_multichannel = True
            self.color_slider.setEnabled(True)
            self.color_slider.setVisible(True)
            self.color_slider.setRange(0, self.stack.image.shape[1] - 1)
            self.color_slider.set_slider_value(0)
            self.imv.setImage(
                self.stack.image[0, 0, :, :].T,
                pos=(-self.stack.width_um / 2, -self.stack.height_um / 2),
                scale=(1 / self.stack.pix_um_ratio,
                       1 / self.stack.pix_um_ratio))
        else:
            self.imv.setImage(
                self.stack.image[0, :, :].T,
                pos=(-self.stack.width_um / 2, -self.stack.height_um / 2),
                scale=(1 / self.stack.pix_um_ratio,
                       1 / self.stack.pix_um_ratio))

        self.imv.getHistogramWidget().setHistogramRange(
            np.iinfo(np.int16).min, np.iinfo(np.int16).max)

    def handle_histogram(self) -> None:
        """Update normalization settings based on histogram changes."""

        region = self.imv.getHistogramWidget().region.getRegion()
        self.normalization_settings = (region[0], region[1])

    def update_image(self) -> None:
        """Update the displayed image based on slider and other settings."""

        layer = self.z_slider.slider.value()
        self.z_slider.value_label.setText(f"{self.stack.zs[layer]} µm")

        if self.is_multichannel:
            channel = self.color_slider.slider.value()
            image_to_display = (
                np.max(self.stack.image[:, channel, :, :], axis=0).T
                if self.is_max_proj_active
                else self.stack.image[layer, channel, :, :].T)
        else:
            image_to_display = (
                np.max(self.stack.image, axis=0).T
                if self.is_max_proj_active
                else self.stack.image[layer, :, :].T)

        self.imv.setImage(
            image_to_display, autoRange=False,
            levels=self.normalization_settings,
            pos=(-self.stack.width_um / 2, -self.stack.height_um / 2),
            scale=(1 / self.stack.pix_um_ratio, 1 / self.stack.pix_um_ratio))

        if self.is_morph_plot:
            self.plot_morph_data.clear()
            self.plot_morph(self.which_morph_plot)

        if self.is_scanfield_plot:
            self.clear_scanfield()
            self.plot_scanfield(self.which_scanfield_plot)

    def plot_morph(self, struct_type: str) -> None:
        """Plot morphology structure on the canvas."""

        struct_map = {
            'neuron': self.morph.neuron,
            'apical': self.morph.apical,
            'basal': self.morph.basal
        }

        struct = struct_map.get(struct_type)

        if struct:
            self.which_morph_plot = struct_type
            x = [node.x
                 for node in struct
                 if self.is_max_proj_active
                 or int(node.z_ind) == self.z_slider.slider.value()]
            y = [node.y
                 for node in struct
                 if self.is_max_proj_active
                 or int(node.z_ind) == self.z_slider.slider.value()]

            self.plot_morph_data = pg.PlotDataItem(
                x, y,
                symbol='o',
                pen=None,
                symbolBrush='m')

            self.imv.addItem(self.plot_morph_data)
            self.is_morph_plot = True

    def clear_morph(self) -> None:
        """Clear the morphology plot from the canvas."""

        self.imv.removeItem(self.plot_morph_data)
        self.is_morph_plot = False

    def plot_scanfield(self, struct_type: str) -> None:
        """Plot the scanfield ROIs on the canvas."""

        struct_map = {
            'neuron': self.sf.neuron,
            'apical': self.sf.apical,
            'basal': self.sf.basal
        }

        struct = struct_map.get(struct_type)

        if struct:
            self.which_scanfield_plot = struct_type
            self.clear_scanfield()  # Clear previous ROIs

            for rect in struct:
                for roi in rect:
                    if (self.is_max_proj_active or
                            int(roi.z_ind) == self.z_slider.slider.value()):

                        roi_rect = pg.RectROI(
                            pos=roi.bottom_right,
                            size=roi.size_xy[::-1],
                            angle=roi.rotation_degrees,
                            removable=True,
                            pen=pg.mkPen(color='green', width=2))

                        tooltip_text = "\n".join(
                            f"{attr.lstrip('_')}: {getattr(roi, attr)}"
                            for attr in dir(roi)
                            if not attr.startswith("__")
                            and not callable(getattr(roi, attr))
                        )

                        roi_rect.setToolTip(tooltip_text)

                        self.imv.getView().addItem(roi_rect)
                        self.rects.append(roi_rect)
            self.is_scanfield_plot = True
            self.which_scanfield_signal.emit(struct_type)

    def clear_scanfield(self) -> None:
        """Clear the scanfield ROIs from the canvas."""

        for roi_rect in self.rects:
            self.imv.removeItem(roi_rect)
        self.rects = []
        self.is_scanfield_plot = False
        self.which_scanfield_signal.emit("")

    def activate_max_proj(self) -> None:
        """Activate max projection mode and disable the Z-slider."""

        if not self.is_max_proj_active:
            self.is_max_proj_active = True
            self.update_image()
            self.z_slider.slider.setEnabled(False)

    def disable_max_proj(self) -> None:
        """Disable max projection mode and enable the Z-slider."""

        if self.is_max_proj_active:
            self.is_max_proj_active = False
            self.update_image()
            self.z_slider.slider.setEnabled(True)
