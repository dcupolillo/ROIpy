""" Created on Tue Nov  7 16:11:05 2023
    @author: dcupolillo """

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (QMainWindow, QGridLayout, QSlider,
                             QFrame, QPushButton, QLabel,
                             QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from ROIpy.assets.palette import dim
from ROIpy.GUI.guiStyles import darkMode, icon


class ImageView(pg.ImageView):

    def __init__(
            self,
            parent,
            *args,
            **kwargs
    ) -> None:
        """
        ImageView custom class to expand actions
        interact with mouse press event

        Parameters
        ----------
        parent :
            DESCRIPTION.
        *args : TYPE
            DESCRIPTION.
        **kwargs : TYPE
            DESCRIPTION.

        Returns
        -------
        None

        """
        super().__init__(*args, **kwargs)

        # Set ImageView to be at least 50% of the entire window
        image_window_ratio = 0.6
        min_width = parent.window_width * image_window_ratio
        min_height = parent.window_height * image_window_ratio
        self.setMinimumWidth(int(min_width))
        self.setMinimumHeight(int(min_height))

        # Create lateral histogram
        self.getHistogramWidget().setFixedWidth(80)

        # Hide default Roi and Menu buttons
        self.ui.roiBtn.setVisible(False)
        self.ui.menuBtn.setVisible(False)


class Canvas(QFrame):

    which_scanfield_signal = pyqtSignal(str)

    def __init__(
            self,
            parent: QMainWindow,
            structures: pyqtSignal,
            structure_frame: QFrame
    ) -> None:
        """
        Defines the canvas were images and plot are displayed.

        Parameters
        ----------
        parent : QMainWindow
            DESCRIPTION.
        structures : pyqtSignal
            DESCRIPTION.
        structure_frame : QFrame
            DESCRIPTION.

        Returns
        -------
        None

        """

        super().__init__(parent)

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setStyleSheet(darkMode.frame)

        self.init_variables()
        self.add_sliders()

        # structures signal received
        structure_frame.morph_plotted.connect(self.plot_morph)
        structure_frame.clear_morph.connect(self.clear_morph)
        structure_frame.sf_plotted.connect(self.plot_scanfield)
        structure_frame.clear_sf.connect(self.clear_scanfield)
        structure_frame.max_proj_activated.connect(self.activate_max_proj)
        structure_frame.max_proj_disabled.connect(self.disable_max_proj)

        self.add_image_view(parent)

    def init_variables(
            self
    ) -> None:
        """
        Initialize some variables.
        """

        self.stack = None
        self.morph = None
        self.sf = None

        self.is_multichannel: bool = False
        self.normalization_settings: tuple = None
        self.is_z_slider: bool = False

        self.plot_morph_data = None
        self.is_morph_plot: bool = False
        self.which_morph_plot: str = None
        self.is_scanfield_plot: bool = False
        self.which_scanfield_plot: str = None
        self.is_max_proj_active: bool = False

        self.rects: list = []

        self.channel_list = ['Fluo5F', 'Alexa 594', None, None]

    def add_image_view(
            self,
            parent: QMainWindow
    ) -> None:
        """
        Add the custom imageView and the axis.
        Connect the intensity histogram with handle_histogram function

        Parameters
        ----------
        parent : QMainWindow
            DESCRIPTION.

        Returns
        -------
        None

        """

        self.imv = ImageView(parent, view=pg.PlotItem())

        self.imv.getView().showGrid(True, True)
        self.layout.addWidget(self.imv, 0, 0, 1, 3)

        self.imv.getHistogramWidget().region.sigRegionChanged.connect(
            self.handle_histogram)

    def handle_structure_signal(
            self,
            stack,
            morph,
            sf
    ) -> None:
        """
        Executed when the structures signal is emitted.
        Get the main structure objects.

        Parameters
        ----------
        stack : Stack
            DESCRIPTION.
        morph : Morphology
            DESCRIPTION.
        sf : Scanfields
            DESCRIPTION.

        Returns
        -------
        None

        """

        self.stack = stack
        self.morph = morph
        self.sf = sf

        # Initialize the image
        self.set_stack()

    def set_stack(
            self
    ) -> None:
        """
        When the PyQt signal is received,
        enables the Z slider and channel slider
        If image has 4 dimensions (slices, channels width, height),
        then enables also the channel slider

        Returns
        -------
        None

        """

        self.z_slider.setEnabled(True)
        self.z_slider.setRange(0, self.stack.n_slices - 1)
        self.is_z_slider = True

        if len(self.stack.image.shape) == 4:

            # if channel dimension is detected set the image at the 0 channel
            self.is_multichannel = True
            self.imv.setImage(self.stack.image[0, 0, :, :].T,
                              pos=(-self.stack.width_um / 2,
                                   -self.stack.height_um / 2),
                              scale=(1 / self.stack.pix_um_ratio,
                                     1 / self.stack.pix_um_ratio))
        else:
            # if no channel dimension is detected, set fixed value at channel
            self.imv.setImage(self.stack.image[0, :, :].T,
                              pos=(-self.stack.width_um / 2,
                                   -self.stack.height_um / 2),
                              scale=(1 / self.stack.pix_um_ratio,
                                     1 / self.stack.pix_um_ratio))

        # Keep the histogram range fixed
        self.imv.getHistogramWidget().setHistogramRange(np.iinfo(np.int16).min,
                                                        np.iinfo(np.int16).max)

    def add_sliders(
            self
    ) -> None:
        """
        Create the Z-slider and Channel-slider, initially disabled.
        """

        z_slider_label = QLabel('Z Slice')
        z_slider_label.setStyleSheet(darkMode.label)
        z_slider_label.setFixedWidth(60)
        self.layout.addWidget(z_slider_label, 1, 0, 1, 1)

        self.z_slider = QSlider(Qt.Horizontal)
        self.z_slider.setEnabled(False)
        self.z_slider.setStyleSheet(darkMode.slider)
        self.layout.addWidget(self.z_slider, 1, 1, 1, 1)

        self.z_slide_selected = QLabel('0', self)
        self.z_slide_selected.setStyleSheet(darkMode.label)
        self.z_slide_selected.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.z_slide_selected, 1, 2, 1, 1)

        # Connect slider signals to update the displayed image
        self.z_slider.valueChanged.connect(self.update_image)

    def handle_histogram(
            self
    ) -> None:
        """
        Get the current normalization settings from the HistogramWidget
        and updates normalization_settings.
        """

        region = self.imv.getHistogramWidget().region.getRegion()
        min_value, max_value = region[0], region[1]

        self.normalization_settings = (min_value, max_value)

    def update_image(
            self
    ) -> None:
        """
        Checks for the selected Z, selected channels,
        selected range of intensity
        and updates the displayed image
        (zoom in and out is blocked with autoRange = False).
        """

        layer = self.z_slider.value()
        channel = 1

        self.z_slide_selected.setText(f"{self.stack.zs[layer]} µm")

        if self.is_multichannel:
            if self.is_max_proj_active:
                image_to_display = np.max(self.stack.image[:, channel, :, :],
                                          axis=0).T

            else:
                image_to_display = self.stack.image[layer, channel, :, :].T

        else:
            if self.is_max_proj_active:
                image_to_display = np.max(self.stack.image, axis=0).T
            else:
                image_to_display = self.stack.image[layer, :, :].T

        # If normalization range is changed, updates it
        if self.normalization_settings:
            min_value, max_value = self.normalization_settings
            self.imv.setImage(image_to_display, autoRange=False,
                              levels=(min_value, max_value),
                              pos=(-self.stack.width_um / 2,
                                   -self.stack.height_um / 2),
                              scale=(1 / self.stack.pix_um_ratio,
                                     1 / self.stack.pix_um_ratio))

        else:
            self.imv.setImage(image_to_display, autoRange=False,
                              pos=(-self.stack.width_um / 2,
                                   -self.stack.height_um / 2),
                              scale=(1 / self.stack.pix_um_ratio,
                                     1 / self.stack.pix_um_ratio))

        # Keep the histogram range fixed
        self.imv.getHistogramWidget().setHistogramRange(np.iinfo(np.int16).min,
                                                        np.iinfo(np.int16).max)

        # if morph is plotted, keep it when updating image
        if self.is_morph_plot:
            self.plot_morph_data.clear()
            self.plot_morph(self.which_morph_plot)

        # if sf is plotted, keep it when updating image
        if self.is_scanfield_plot:
            for roi_rect in self.rects:
                self.imv.removeItem(roi_rect)
            self.rects = []

            self.plot_scanfield(self.which_scanfield_plot)

    def plot_morph(
            self,
            struct_type: str
    ) -> None:
        """
        Plots the morphology structure on the canvas.

        Parameters
        ----------
        struct_type : TYPE
            DESCRIPTION.

        Returns
        -------
        None

        """

        if struct_type == 'neuron':
            struct = self.morph.neuron
            self.which_morph_plot = struct_type

        if struct_type == 'apical':
            struct = self.morph.apical
            self.which_morph_plot = struct_type

        if struct_type == 'basal':
            struct = self.morph.basal
            self.which_morph_plot = struct_type

        if self.is_max_proj_active:
            x = [node.x for node in struct]
            y = [node.y for node in struct]

        else:
            x = [node.x for node in struct
                 if int(node.z_ind) == self.z_slider.value()]
            y = [node.y for node in struct
                 if int(node.z_ind) == self.z_slider.value()]

        self.plot_morph_data = pg.PlotDataItem(x, y, symbol='o', pen=None)

        self.imv.addItem(self.plot_morph_data)
        self.is_morph_plot = True

    def clear_morph(
            self
    ) -> None:

        self.imv.removeItem(self.plot_morph_data)
        self.is_morph_plot = False

    def plot_scanfield(
            self,
            struct_type: str
    ) -> None:
        """
        Plots the scanfield ROIs on the canvas.

        Parameters
        ----------
        struct_type : str
            DESCRIPTION.

        Returns
        -------
        None

        """

        if struct_type == 'neuron':
            struct = self.sf.neuComp
            self.which_scanfield_plot = struct_type
        if struct_type == 'apical':
            struct = self.sf.apiComp
            self.which_scanfield_plot = struct_type
        if struct_type == 'basal':
            struct = self.sf.basComp
            self.which_scanfield_plot = struct_type

        self.which_scanfield_signal.emit(struct_type)

        bottom_rights = []
        sizes = []
        rotations = []
        zs = []

        if self.is_max_proj_active:

            for rect in struct:
                for roi in rect:

                    bottom_rights.append(roi.bottom_right)

                    sizes.append(roi.size_xy)
                    rotations.append(roi.rotation_degrees)
                    zs.append(int(roi.z_ind))

            for bottom_right, size, rotation, z in zip(
                    bottom_rights, sizes, rotations, zs):

                roi_rect = pg.RectROI(pos=(bottom_right[0],
                                           bottom_right[1]),
                                      size=(size[1], size[0]),
                                      angle=rotation,
                                      removable=True,
                                      )

                self.imv.getView().addItem(roi_rect)

                self.rects.append(roi_rect)
        else:

            for rect in struct:
                for roi in rect:
                    if roi.z == self.stack.zs[self.z_slider.value()]:

                        bottom_rights.append(roi.bottom_right)

                        sizes.append(roi.size_xy)
                        rotations.append(roi.rotation_degrees)
                        zs.append(int(roi.z_ind))

            for bottom_right, size, rotation, z in zip(
                    bottom_rights, sizes, rotations, zs):

                if z == self.z_slider.value():

                    roi_rect = pg.RectROI(pos=(bottom_right[0],
                                               bottom_right[1]),
                                          size=(size[1], size[0]),
                                          angle=rotation,
                                          removable=True,
                                          )

                    self.imv.getView().addItem(roi_rect)

                    self.rects.append(roi_rect)

        self.is_scanfield_plot = True

    def clear_scanfield(
            self
    ) -> None:

        for roi_rect in self.rects:
            self.imv.removeItem(roi_rect)
        self.is_scanfield_plot = False

    def activate_max_proj(
            self
    ) -> None:

        if not self.is_max_proj_active:
            self.is_max_proj_active = True
            self.update_image()
            self.z_slider.setEnabled(False)

    def disable_max_proj(
            self
    ) -> None:

        if self.is_max_proj_active:
            self.is_max_proj_active = False
            self.update_image()
            self.z_slider.setEnabled(True)


class StructureFrame(QFrame):

    morph_plotted = pyqtSignal(str)
    clear_morph = pyqtSignal(str)
    sf_plotted = pyqtSignal(str)
    clear_sf = pyqtSignal(str)
    max_proj_activated = pyqtSignal()
    max_proj_disabled = pyqtSignal()

    def __init__(
            self,
            parent: QMainWindow
    ) -> None:
        """
        Frame ...

        Parameters
        ----------
        parent : QMainWindow
            DESCRIPTION.

        Returns
        -------
        None

        """

        super().__init__(parent)

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setStyleSheet(darkMode.frame)

        # Add widgets
        title = QLabel("Plot structures\n")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(darkMode.title)
        self.layout.addWidget(title, 0, 0, 1, 3)

        # Whole Neuron column
        all_dendrites_label = QLabel("All dendrites")
        all_dendrites_label.setAlignment(Qt.AlignCenter)
        all_dendrites_label.setStyleSheet(darkMode.label)
        self.layout.addWidget(all_dendrites_label, 1, 0, 1, 1)

        self.morph_neuron_button = QPushButton('')
        self.morph_neuron_button.setStyleSheet(
            darkMode.button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        self.morph_neuron_button.setIcon(QIcon(icon.neuron))
        self.layout.addWidget(self.morph_neuron_button, 2, 0, 1, 1)
        self.morph_neuron_button.setEnabled(False)
        self.morph_neuron_button.toggled.connect(
            lambda checked: self.plot_morph(checked, 'neuron'))
        self.morph_neuron_button.toggled.connect(
            lambda checked: self.toggle_buttons_morph(
                checked, self.morph_neuron_button))

        spacer_item = QSpacerItem(1, 20,
                                  QSizePolicy.Minimum,
                                  QSizePolicy.Minimum)
        self.layout.addItem(spacer_item, 3, 0, 1, 3)

        self.scanfield_neuron_button = QPushButton('')
        self.scanfield_neuron_button.setStyleSheet(
            darkMode.button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        self.scanfield_neuron_button.setIcon(QIcon(icon.rect))
        self.layout.addWidget(self.scanfield_neuron_button, 4, 0, 1, 1)
        self.scanfield_neuron_button.setEnabled(False)
        self.scanfield_neuron_button.toggled.connect(
            lambda checked: self.plot_scanfield(checked, 'neuron'))
        self.scanfield_neuron_button.toggled.connect(
            lambda checked: self.toggle_buttons_scanfield(
                checked, self.scanfield_neuron_button))

        # Apical Dendrites column
        apical_dendrites_label = QLabel("Apical dendrites")
        apical_dendrites_label.setAlignment(Qt.AlignCenter)
        apical_dendrites_label.setStyleSheet(darkMode.label)
        self.layout.addWidget(apical_dendrites_label, 1, 1, 1, 1)

        self.morph_apical_button = QPushButton('')
        self.morph_apical_button.setStyleSheet(
            darkMode.button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        self.morph_apical_button.setIcon(QIcon(icon.neuron))
        self.layout.addWidget(self.morph_apical_button, 2, 1, 1, 1)
        self.morph_apical_button.setEnabled(False)
        self.morph_apical_button.toggled.connect(
            lambda checked: self.plot_morph(checked, 'apical'))
        self.morph_apical_button.toggled.connect(
            lambda checked: self.toggle_buttons_morph(
                checked, self.morph_apical_button))

        self.scanfield_apical_button = QPushButton('')
        self.scanfield_apical_button.setStyleSheet(
            darkMode.button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering};}}''')
        self.scanfield_apical_button.setIcon(QIcon(icon.rect))
        self.layout.addWidget(self.scanfield_apical_button, 4, 1, 1, 1)
        self.scanfield_apical_button.setEnabled(False)
        self.scanfield_apical_button.toggled.connect(
            lambda checked: self.plot_scanfield(checked, 'apical'))
        self.scanfield_apical_button.toggled.connect(
            lambda checked: self.toggle_buttons_scanfield(
                checked, self.scanfield_apical_button))

        # Basal Dendrites column
        basal_dendrites_label = QLabel("Basal dendrites")
        basal_dendrites_label.setAlignment(Qt.AlignCenter)
        basal_dendrites_label.setStyleSheet(darkMode.label)
        self.layout.addWidget(basal_dendrites_label, 1, 2, 1, 1)

        self.morph_basal_button = QPushButton('')
        self.morph_basal_button.setStyleSheet(
            darkMode.button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        self.morph_basal_button.setIcon(QIcon(icon.neuron))
        self.layout.addWidget(self.morph_basal_button, 2, 2, 1, 1)
        self.morph_basal_button.setEnabled(False)
        self.morph_basal_button.toggled.connect(
            lambda checked: self.plot_morph(checked, 'basal'))
        self.morph_basal_button.toggled.connect(
            lambda checked: self.toggle_buttons_morph(
                checked, self.morph_basal_button))

        self.scanfield_basal_button = QPushButton('')
        self.scanfield_basal_button.setStyleSheet(
            darkMode.button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        self.scanfield_basal_button.setIcon(QIcon(icon.rect))
        self.layout.addWidget(self.scanfield_basal_button, 4, 2, 1, 1)
        self.scanfield_basal_button.setEnabled(False)
        self.scanfield_basal_button.toggled.connect(
            lambda checked: self.plot_scanfield(checked, 'basal'))
        self.scanfield_basal_button.toggled.connect(
            lambda checked: self.toggle_buttons_scanfield(
                checked, self.scanfield_basal_button))

        # Add another spacer
        self.layout.addItem(spacer_item, 5, 0, 1, 3)

        activate_max_proj_label = QLabel("Activate Max Projection")
        activate_max_proj_label.setAlignment(Qt.AlignCenter)
        activate_max_proj_label.setStyleSheet(darkMode.label)
        self.layout.addWidget(activate_max_proj_label, 6, 0, 1, 1)

        self.max_projection_button = QPushButton('')
        self.max_projection_button.setStyleSheet(
            darkMode.green_button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        self.max_projection_button.setIcon(QIcon(icon.max_proj))
        self.layout.addWidget(self.max_projection_button, 7, 0, 1, 1)
        self.max_projection_button.setEnabled(False)
        self.max_projection_button.toggled.connect(
            lambda checked: self.plot_max_proj(checked))

    def activate_buttons(
            self
    ) -> None:

        buttons = [self.morph_neuron_button,
                   self.morph_apical_button,
                   self.morph_basal_button,
                   self.scanfield_neuron_button,
                   self.scanfield_apical_button,
                   self.scanfield_basal_button,
                   self.max_projection_button]

        for button in buttons:

            button.setEnabled(True)
            button.setCheckable(True)

    def toggle_buttons_morph(
            self,
            checked,
            active_button: QPushButton
    ) -> None:

        buttons = [self.morph_neuron_button,
                   self.morph_apical_button,
                   self.morph_basal_button]
        if checked:

            for button in buttons:
                if button != active_button:
                    button.setEnabled(False)
            active_button.setEnabled(True)

        else:
            for button in buttons:
                button.setEnabled(True)

    def toggle_buttons_scanfield(
            self,
            checked,
            active_button: QPushButton
    ) -> None:

        buttons = [self.scanfield_neuron_button,
                   self.scanfield_apical_button,
                   self.scanfield_basal_button]
        if checked:

            for button in buttons:
                if button != active_button:
                    button.setEnabled(False)
            active_button.setEnabled(True)

        else:
            for button in buttons:
                button.setEnabled(True)

    def plot_morph(
            self,
            checked,
            struct_type: str
    ) -> None:

        if struct_type == 'neuron':
            button = self.morph_neuron_button
        elif struct_type == 'apical':
            button = self.morph_apical_button
        elif struct_type == 'basal':
            button = self.morph_basal_button

        if checked:
            self.morph_plotted.emit(struct_type)
            button.setStyleSheet(darkMode.toggled_button)

        else:
            self.clear_morph.emit(struct_type)
            button.setStyleSheet(
                darkMode.button +
                f'''QPushButton:hover {{
                background-color: {dim.hovering.hex};}}''')

    def plot_scanfield(
            self,
            checked,
            struct_type: str
    ) -> None:

        if struct_type == 'neuron':
            button = self.scanfield_neuron_button
        elif struct_type == 'apical':
            button = self.scanfield_apical_button
        elif struct_type == 'basal':
            button = self.scanfield_basal_button

        if checked:
            self.sf_plotted.emit(struct_type)
            button.setStyleSheet(darkMode.toggled_button)

        else:
            self.clear_sf.emit(struct_type)
            button.setStyleSheet(
                darkMode.button +
                f'''QPushButton:hover {{
                background-color: {dim.hovering.hex};}}''')

    def plot_max_proj(
            self,
            checked
    ) -> None:

        if checked:
            self.max_proj_activated.emit()
            self.max_projection_button.setStyleSheet(darkMode.toggled_button)

        else:
            self.max_proj_disabled.emit()
            self.max_projection_button.setStyleSheet(
                darkMode.button +
                f'''QPushButton:hover {{
                background-color: {dim.hovering.hex};}}''')
