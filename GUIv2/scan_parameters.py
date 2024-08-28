""" Created on Tue Aug 27 15:47:53 2024
    @author: dcupolillo """


from PyQt5.QtWidgets import (QMainWindow, QFrame, QLabel, QGridLayout,
                             QPushButton, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from ROIpy.core.structures import Stack, Morphology, Scanfields


class ScanParameters(QFrame):

    change_plot = pyqtSignal()
    change_roi_file = pyqtSignal(Scanfields)

    def __init__(self, parent: QMainWindow) -> None:
        """Frame with Scanfield parameters."""

        super().__init__(parent)

        self.stack = None
        self.morph = None
        self.sf = None

        layout = QGridLayout()
        self.setLayout(layout)

        # Add widgets
        title = QLabel("Scan Parameters\n")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 4)

        # Entries
        labels_and_attributes = [
            ("Desired Framerate [Hz]", "desired_framerate", 0, False),
            ("Elongating Factor", "elongating_factor", 1, False),
            ("Dim Ratio Threshold", "dim_ratio_threshold", 2, False),
            ("Overlap Threshold", "overlap_threshold", 3, False),
            ("Wavelength [nm]", "wavelength", 4, False),
            ("Fill Fraction", "fill_fraction", 5, False),
            ("Frame Flyback [s]", "frame_flyback", 6, False),
            ("Fly to Line [s]", "fly_to_line", 7, False),
            ("Numerical Aperture", "numerical_aperture", 8, True),
            ("Sampling Rate [Hz]", "sampling_rate", 9, False),
            ("Sampling Rate Control [Hz]", "sampling_rate_ctl", 10, True),
            ("Pixel Bin Factor", "pixel_bin_factor", 11, False),
            ("Dwell Time [s]", "dwell_time", 12, False),
            ("Filtering Radius", "filtering_radius", 13, False),
            ("Framerate Delta Threshold", "framerate_delta_threshold",
             14, False),
        ]

        self.entries = {}

        for text, attribute, row, read_only in labels_and_attributes:
            # Determine column based on row parity (odd/even)
            col_label = 0 if row % 2 == 0 else 2
            col_entry = col_label + 1

            label = QLabel(text)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(label, (row // 2) + 1, col_label, 1, 1)

            entry = QLineEdit()
            entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            entry.setEnabled(False)

            if read_only:
                entry.setReadOnly(True)

            layout.addWidget(entry, (row // 2) + 1, col_entry, 1, 1)

            # Use the attribute name as the key
            self.entries[attribute] = entry

        self.update_scanfield_button = QPushButton('Update')
        layout.addWidget(
            self.update_scanfield_button,
            len(labels_and_attributes) // 2 + 1, 3, 1, 1)
        self.update_scanfield_button.clicked.connect(self.update_scanfields)
        self.update_scanfield_button.setEnabled(False)

        self.get_scanfield()

    def get_structures(
            self,
            stack: Stack,
            morph: Morphology,
            sf: Scanfields
    ) -> None:
        """Receive structures from the Generate button signal."""

        self.stack = stack
        self.morph = morph
        self.sf = sf

    def get_scanfield(self) -> None:
        """Populates entries with Scanfield parameters."""

        if self.sf:
            for key, entry in self.entries.items():
                entry.setEnabled(True)
                entry.setText(str(getattr(self.sf, key, "")))

            self.update_scanfield_button.setEnabled(True)

    def update_scanfields(self) -> None:
        """Updates Scanfield parameters based on user input."""

        updated_fields = {
            'desired_framerate': int(self.entries['frame'].text()),
            'elongating_factor': float(self.entries['elongating'].text()),
            'dim_ratio_threshold': float(self.entries['dimension'].text()),
            'wavelength': int(self.entries['wavelength'].text()),
            'fill_fraction': float(self.entries['fill'].text()),
            'frame_flyback': float(self.entries['frame'].text()),
            'fly_to_line': float(self.entries['fly'].text()),
            'sampling_rate': float(self.entries['sampling'].text()),
            'pixel_bin_factor': int(self.entries['pixel'].text()),
            'filtering_radius': tuple(map(float, self.entries['radius'].text().strip('()').split(', ')))
        }

        numerical_aperture = 0.8
        overlap_threshold = 0.90

        # Check if any values have changed and update if necessary
        if any(getattr(self.sf, key) != value
               for key, value in updated_fields.items()):
            self.sf = Scanfields(
                self.stack.paths, **updated_fields,
                overlap_threshold=overlap_threshold,
                numerical_aperture=numerical_aperture,
                sampling_rate_ctl=self.sf.sampling_rate_ctl,
                framerate_delta_threshold=self.sf.framerate_delta_threshold)

            self.change_plot.emit()
            self.change_roi_file.emit(self.sf)

            QMessageBox.information(self, "Success", "Roi files updated!")
