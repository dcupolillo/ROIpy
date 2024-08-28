""" Created on Tue Aug 27 16:25:15 2024
    @author: dcupolillo """

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QMainWindow, QGridLayout, QSlider,
                             QFrame, QLabel)


class CustomToggleButton(QPushButton):

    def __init__(self, text, parent=None) -> None:

        super().__init__(parent)
        self.setCheckable(True)
        self.setText(text)


class MorphButton(CustomToggleButton):

    def __init__(self, text, parent=None) -> None:
        super().__init__(text, parent)


class ScanfieldButton(CustomToggleButton):

    def __init__(self, text, parent=None) -> None:
        super().__init__(text, parent)


class StructureFrame(QFrame):

    morph_plotted = pyqtSignal(str)
    clear_morph = pyqtSignal()
    sf_plotted = pyqtSignal(str)
    clear_sf = pyqtSignal()
    max_proj_activated = pyqtSignal()
    max_proj_disabled = pyqtSignal()

    def __init__(self, parent: QMainWindow) -> None:

        super().__init__(parent)

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        title = QLabel("Plot structures\n")
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title, 0, 0, 1, 3)

        self.morph_neuron_button = MorphButton(
            "Plot all dendrites", parent=self)
        self.layout.addWidget(self.morph_neuron_button, 2, 0, 1, 1)
        self.morph_neuron_button.toggled.connect(
            lambda checked: self.toggle_morph_exclusivity(
                checked, self.morph_neuron_button, 'neuron'))

        self.morph_apical_button = MorphButton(
            "Plot apical dendrites", parent=self)
        self.layout.addWidget(self.morph_apical_button, 2, 1, 1, 1)
        self.morph_apical_button.toggled.connect(
            lambda checked: self.toggle_morph_exclusivity(
                checked, self.morph_apical_button, 'apical'))

        self.morph_basal_button = MorphButton(
            "Plot basal dendrites", parent=self)
        self.layout.addWidget(self.morph_basal_button, 2, 2, 1, 1)
        self.morph_basal_button.toggled.connect(
            lambda checked: self.toggle_morph_exclusivity(
                checked, self.morph_basal_button, 'basal'))

        # Scanfield buttons
        self.scanfield_neuron_button = ScanfieldButton(
            "Plot all ROIs", parent=self)
        self.layout.addWidget(self.scanfield_neuron_button, 3, 0, 1, 1)
        self.scanfield_neuron_button.toggled.connect(
            lambda checked: self.toggle_sf_exclusivity(
                checked, self.scanfield_neuron_button, 'neuron'))

        self.scanfield_apical_button = ScanfieldButton(
            "Plot apical ROIs", parent=self)
        self.layout.addWidget(self.scanfield_apical_button, 3, 1, 1, 1)
        self.scanfield_apical_button.toggled.connect(
            lambda checked: self.toggle_sf_exclusivity(
                checked, self.scanfield_apical_button, 'apical'))

        self.scanfield_basal_button = ScanfieldButton(
            "Plot basal ROIs", parent=self)
        self.layout.addWidget(self.scanfield_basal_button, 3, 2, 1, 1)
        self.scanfield_basal_button.toggled.connect(
            lambda checked: self.toggle_sf_exclusivity(
                checked, self.scanfield_basal_button, 'basal'))

        # Max Projection Button
        self.max_projection_button = CustomToggleButton(
            "Activate Max Projection", parent=self)
        self.layout.addWidget(self.max_projection_button, 4, 0, 1, 3)
        self.max_projection_button.toggled.connect(self.toggle_max_proj)

        # Initially disable all buttons
        self.disable_buttons()

    def disable_buttons(self) -> None:
        """Disable all buttons initially."""
        buttons = [
            self.morph_neuron_button,
            self.morph_apical_button,
            self.morph_basal_button,
            self.scanfield_neuron_button,
            self.scanfield_apical_button,
            self.scanfield_basal_button,
            self.max_projection_button
        ]

        for button in buttons:
            button.setEnabled(False)

    def activate_buttons(self) -> None:
        # Simplified activation of buttons
        buttons = [
            self.morph_neuron_button,
            self.morph_apical_button,
            self.morph_basal_button,
            self.scanfield_neuron_button,
            self.scanfield_apical_button,
            self.scanfield_basal_button,
            self.max_projection_button]

        for button in buttons:
            button.setEnabled(True)
            button.setCheckable(True)

    def toggle_morph_exclusivity(self, checked, active_button, struct_type):

        buttons = [
            self.morph_neuron_button,
            self.morph_apical_button,
            self.morph_basal_button]

        if checked:
            for button in buttons:
                if button != active_button:
                    button.setChecked(False)
                    self.clear_morph.emit()
            self.morph_plotted.emit(struct_type)
        else:
            self.clear_morph.emit()

    def toggle_sf_exclusivity(self, checked, active_button, struct_type):

        buttons = [
            self.scanfield_neuron_button,
            self.scanfield_apical_button,
            self.scanfield_basal_button]

        if checked:
            for button in buttons:
                if button != active_button:
                    button.setChecked(False)
                    self.clear_sf.emit()
            self.sf_plotted.emit(struct_type)
        else:
            if not any(button.isChecked() for button in buttons):
                self.clear_sf.emit()

    def toggle_max_proj(self, checked):
        if checked:
            self.max_proj_activated.emit()
        else:
            self.max_proj_disabled.emit()
