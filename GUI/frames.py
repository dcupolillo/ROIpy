""" Created on Tue Nov  7 10:03:57 2023
    @author: dcupolillo """

import os
from PyQt5.QtWidgets import (QMainWindow, QFrame, QLabel, QGridLayout,
                             QPushButton, QFileDialog, QLineEdit,
                             QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal


from ROIpy.core.structures import Stack, Morphology, Scanfields
from ROIpy.assets.palette import dim
from ROIpy.GUI.guiStyles import darkMode, icon
from neuronpath.path import neuronpath


class LoadFiles(QFrame):

    paths = None

    files_name = pyqtSignal(object)
    structures = pyqtSignal(Stack, Morphology, Scanfields)
    update_progress_signal = pyqtSignal()

    generate_button_clicked = pyqtSignal()

    def __init__(
            self,
            parent: QMainWindow,
    ) -> None:
        """
        Frame where initial swc and tif files are loaded.

        Parameters
        ----------
        parent : QMainWindow
            The main window.

        Returns
        -------
        None
        """

        super().__init__(parent)

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.setStyleSheet(darkMode.frame)

        # Add widgets
        title = QLabel("Load")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(darkMode.title)
        self.layout.addWidget(title, 0, 0, 1, 3)

        # first row
        path_label = QLabel('Select a path: ')
        path_label.setAlignment(Qt.AlignVCenter)
        path_label.setStyleSheet(darkMode.label)
        self.layout.addWidget(path_label, 1, 0, 1, 1)

        path_entry = QLabel()
        path_entry.setWordWrap(False)
        path_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        path_entry.setStyleSheet(darkMode.entry)
        path_entry.setFixedWidth(350)
        self.layout.addWidget(path_entry, 1, 1, 1, 1)

        path_button = QPushButton(' Choose')
        path_button.setStyleSheet(darkMode.button +
                                  f'''QPushButton:hover {{
                                  background-color: {dim.hovering.hex};}}''')
        path_button.setIcon(QIcon(icon.folder))
        self.layout.addWidget(path_button, 1, 2, 1, 1)
        path_button.clicked.connect(lambda: self.choose_file(path_entry))

        self.generate_button = QPushButton(' Generate')
        self.generate_button.setStyleSheet(
            darkMode.green_button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        self.generate_button.setIcon(QIcon(icon.next))
        self.layout.addWidget(self.generate_button, 2, 2)
        self.generate_button.clicked.connect(
            lambda: self.generate())
        self.generate_button.setEnabled(False)

    def choose_file(
        self,
        label: QLabel
    ) -> None:
        """
        Opens a dialog to select a folder and searches
        for a .tif and a .swc file within it.
        Updates the label with the folder path.
        Stores the filenames of the found files.
        Runs the file loaded check.

        Parameters
        ----------
        label : QLabel
            Label widget to update with the folder path.

        Returns
        -------
        None
        """

        folder_name = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.ReadOnly
        )

        if folder_name:
            label.setText(folder_name)
            label.setStyleSheet(darkMode.entry)

            # Store the folder name
            self.folder_name = folder_name

            # Split the folder path into its components
            path_parts = os.path.normpath(folder_name).split(os.sep)

            # Store the last and second-to-last components
            self.cell_n = int(''.join(filter(str.isdigit, path_parts[-1])))
            self.date = str(path_parts[-2])

            self.paths = neuronpath(
                date=self.date,
                neuron_number=self.cell_n,
                home='C:\\Users\\vregio',
                user='Desktop')

            # Initialize variables to store file paths
            self.tif_filename = self.paths.stackpath
            self.swc_filename = self.paths.tracepath

            # Search for .tif and .swc files in the selected folder
            for root, dirs, files in os.walk(folder_name):
                for file in files:
                    if file.endswith('.tif'):
                        self.tif_filename = os.path.join(root, file)
                    elif file.endswith('.swc'):
                        self.swc_filename = os.path.join(root, file)

                # Stop searching if both files are found
                if self.tif_filename and self.swc_filename:
                    break

            self.are_files_loaded()

    def are_files_loaded(
            self
    ) -> None:
        """
        Check if both files are loaded
        """

        if self.paths:
            self.generate_button.setEnabled(True)
            self.files_name.emit(self.paths)

    def generate(self) -> None:
        """
        Creates the core Structures of ROIpy.
        Emit a signal to Main Window.
        Enables the structure buttons in the structure frame.

        Parameters
        ----------
        tif : str
            filename of the stack.
        swc : str
            filename of the tracing.

        Returns
        -------
        None
        """
        stack = Stack(self.paths)
        morph = Morphology(self.paths)
        sf = Scanfields(self.paths)

        self.structures.emit(stack, morph, sf)
        self.generate_button_clicked.emit()

        msg = QMessageBox()
        msg.setWindowTitle("Success")
        msg.setText("DONE!")
        msg.setIcon(QMessageBox.Information)
        msg.addButton(QMessageBox.Ok)
        msg.exec_()


class ScanParameters(QFrame):

    change_plot = pyqtSignal()
    change_roi_file = pyqtSignal(Scanfields)

    def __init__(
            self,
            parent: QMainWindow
    ) -> None:
        """
        Frame with Scanfield parameters.

        Parameters
        ----------
        parent : TYPE
            DESCRIPTION.

        Returns
        -------
        None

        """

        super().__init__(parent)

        self.stack = None
        self.morph = None
        self.sf = None

        layout = QGridLayout()
        self.setLayout(layout)

        self.setStyleSheet(darkMode.frame)

        # Add widgets
        title = QLabel("Scan Parameters\n")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(darkMode.title)
        layout.addWidget(title, 0, 0, 1, 4)

        frame_rate_label = QLabel('Frame Rate (Hz): ')
        frame_rate_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        frame_rate_label.setStyleSheet(darkMode.label)
        layout.addWidget(frame_rate_label, 1, 0, 1, 1)

        self.frame_rate_entry = QLineEdit()
        self.frame_rate_entry.setStyleSheet(darkMode.line_edit)
        self.frame_rate_entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.frame_rate_entry.setEnabled(False)
        layout.addWidget(self.frame_rate_entry, 1, 1, 1, 1)

        wavelength_label = QLabel('Wavelength (nm): ')
        wavelength_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        wavelength_label.setStyleSheet(darkMode.label)
        layout.addWidget(wavelength_label, 1, 2, 1, 1)

        self.wavelength_entry = QLineEdit()
        self.wavelength_entry.setStyleSheet(darkMode.line_edit)
        self.wavelength_entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.wavelength_entry.setEnabled(False)
        layout.addWidget(self.wavelength_entry, 1, 3, 1, 1)

        dwell_time_label = QLabel('Dwell time (s): ')
        dwell_time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dwell_time_label.setStyleSheet(darkMode.label)
        layout.addWidget(dwell_time_label, 2, 0, 1, 1)

        self.dwell_time_entry = QLineEdit()
        self.dwell_time_entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.dwell_time_entry.setStyleSheet(darkMode.line_edit)
        self.dwell_time_entry.setEnabled(False)
        layout.addWidget(self.dwell_time_entry, 2, 1, 1, 1)

        pixel_bin_factor_label = QLabel('Pixel bin factor: ')
        pixel_bin_factor_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pixel_bin_factor_label.setStyleSheet(darkMode.label)
        layout.addWidget(pixel_bin_factor_label, 2, 2, 1, 1)

        self.pixel_bin_factor_entry = QLineEdit()
        self.pixel_bin_factor_entry.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter)
        self.pixel_bin_factor_entry.setStyleSheet(darkMode.line_edit)
        self.pixel_bin_factor_entry.setEnabled(False)
        layout.addWidget(self.pixel_bin_factor_entry, 2, 3, 1, 1)

        sample_rate_label = QLabel('Sampling rate (Hz): ')
        sample_rate_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        sample_rate_label.setStyleSheet(darkMode.label)
        layout.addWidget(sample_rate_label, 3, 0, 1, 1)

        self.sample_rate_entry = QLineEdit()
        self.sample_rate_entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.sample_rate_entry.setStyleSheet(darkMode.line_edit)
        self.sample_rate_entry.setEnabled(False)
        layout.addWidget(self.sample_rate_entry, 3, 1, 1, 1)

        fill_fraction_label = QLabel('Fill fraction: ')
        fill_fraction_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        fill_fraction_label.setStyleSheet(darkMode.label)
        layout.addWidget(fill_fraction_label, 3, 2, 1, 1)

        self.fill_fraction_entry = QLineEdit()
        self.fill_fraction_entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.fill_fraction_entry.setStyleSheet(darkMode.line_edit)
        self.fill_fraction_entry.setEnabled(False)
        layout.addWidget(self.fill_fraction_entry, 3, 3, 1, 1)

        fly_to_line_label = QLabel('Fly to line (s): ')
        fly_to_line_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        fly_to_line_label.setStyleSheet(darkMode.label)
        layout.addWidget(fly_to_line_label, 4, 0, 1, 1)

        self.fly_to_line_entry = QLineEdit()
        self.fly_to_line_entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.fly_to_line_entry.setStyleSheet(darkMode.line_edit)
        self.fly_to_line_entry.setEnabled(False)
        layout.addWidget(self.fly_to_line_entry, 4, 1, 1, 1)

        flyback_label = QLabel('Frame flyback (s): ')
        flyback_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flyback_label.setStyleSheet(darkMode.label)
        layout.addWidget(flyback_label, 4, 2, 1, 1)

        self.flyback_entry = QLineEdit()
        self.flyback_entry.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.flyback_entry.setStyleSheet(darkMode.line_edit)
        self.flyback_entry.setEnabled(False)
        layout.addWidget(self.flyback_entry, 4, 3, 1, 1)

        elongating_factor_label = QLabel('Elongating factor :')
        elongating_factor_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        elongating_factor_label.setStyleSheet(darkMode.label)
        layout.addWidget(elongating_factor_label, 5, 0, 1, 1)

        self.elongating_factor_entry = QLineEdit()
        self.elongating_factor_entry.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter)
        self.elongating_factor_entry.setStyleSheet(darkMode.line_edit)
        self.elongating_factor_entry.setEnabled(False)
        layout.addWidget(self.elongating_factor_entry, 5, 1, 1, 1)

        dim_ratio_threshold_label = QLabel('Dimension Ratio Threshold: ')
        dim_ratio_threshold_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dim_ratio_threshold_label.setStyleSheet(darkMode.label)
        layout.addWidget(dim_ratio_threshold_label, 5, 2, 1, 1)

        self.dim_ratio_threshold_entry = QLineEdit()
        self.dim_ratio_threshold_entry.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter)
        self.dim_ratio_threshold_entry.setStyleSheet(darkMode.line_edit)
        self.dim_ratio_threshold_entry.setEnabled(False)
        layout.addWidget(self.dim_ratio_threshold_entry, 5, 3, 1, 1)

        filtering_radius_label = QLabel('Radius Threshold (µm): ')
        filtering_radius_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        filtering_radius_label.setStyleSheet(darkMode.label)
        layout.addWidget(filtering_radius_label, 6, 0, 1, 1)

        self.filtering_radius_entry = QLineEdit()
        self.filtering_radius_entry.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter)
        self.filtering_radius_entry.setStyleSheet(darkMode.line_edit)
        self.filtering_radius_entry.setEnabled(False)
        layout.addWidget(self.filtering_radius_entry, 6, 1, 1, 1)

        self.update_scanfield_button = QPushButton('Update')
        self.update_scanfield_button.setStyleSheet(
            darkMode.green_button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        self.update_scanfield_button.setIcon(QIcon(icon.next))
        layout.addWidget(self.update_scanfield_button, 6, 3, 1, 1)
        self.update_scanfield_button.clicked.connect(self.update_scanfields)
        self.update_scanfield_button.setEnabled(False)

        self.get_scanfield()

    def get_structures(
            self,
            stack: Stack,
            morph: Morphology,
            sf: Scanfields
    ) -> None:
        """
        Run when signal received from Generate button.
        Generates the main structures.

        Parameters
        ----------
        stack : Stack
            DESCRIPTION.
        morph : Morphology
            DESCRIPTION.
        sf : Scanfield
            DESCRIPTION.

        Returns
        -------
        None

        """

        self.stack = stack
        self.morph = morph
        self.sf = sf

    def get_scanfield(
            self
    ) -> None:
        """
        Collects Scanfield Parameters.
        """

        if self.sf:
            entries = [self.frame_rate_entry,
                       self.wavelength_entry,
                       self.dwell_time_entry,
                       self.pixel_bin_factor_entry,
                       self.sample_rate_entry,
                       self.fill_fraction_entry,
                       self.fly_to_line_entry,
                       self.flyback_entry,
                       self.elongating_factor_entry,
                       self.dim_ratio_threshold_entry,
                       self.filtering_radius_entry]

            for entry in entries:
                entry.setEnabled(True)

            self.frame_rate_entry.setText(str(self.sf.desired_framerate))
            self.wavelength_entry.setText(str(self.sf.wavelength))
            self.dwell_time_entry.setText(str(self.sf.dwell_time))
            self.pixel_bin_factor_entry.setText(str(self.sf.pixel_bin_factor))
            self.sample_rate_entry.setText(str(self.sf.sampling_rate))
            self.fill_fraction_entry.setText(str(self.sf.fill_fraction))
            self.fly_to_line_entry.setText(str(self.sf.fly_to_line))
            self.flyback_entry.setText(str(self.sf.frame_flyback))
            self.elongating_factor_entry.setText(
                str(self.sf.elongating_factor))
            self.dim_ratio_threshold_entry.setText(
                str(self.sf.dim_ratio_threshold))
            self.filtering_radius_entry.setText(
                str(self.sf.filtering_radius))

            self.update_scanfield_button.setEnabled(True)

    def update_scanfields(
            self
    ) -> None:
        """
        Collects Scanfield Parameters.
        """

        frame_rate = int(self.frame_rate_entry.text())
        elongating_factor = float(self.elongating_factor_entry.text())
        dim_ratio_threshold = float(self.dim_ratio_threshold_entry.text())
        wavelength = int(self.wavelength_entry.text())
        fill_fraction = float(self.fill_fraction_entry.text())
        frame_flyback = float(self.flyback_entry.text())
        fly_to_line = float(self.fly_to_line_entry.text())
        sampling_rate = float(self.sample_rate_entry.text())
        pixel_bin_factor = int(self.pixel_bin_factor_entry.text())
        string = self.filtering_radius_entry.text()
        filtering_radius = tuple(map(float, string.strip('()').split(', ')))

        numerical_aperture = 0.8
        overlap_threshold = 0.90

        if (frame_rate != self.sf.desired_framerate or
                elongating_factor != self.sf.elongating_factor or
                dim_ratio_threshold != self.sf.dim_ratio_threshold or
                wavelength != self.sf.wavelength or
                fill_fraction != self.sf.fill_fraction or
                frame_flyback != self.sf.frame_flyback or
                fly_to_line != self.sf.fly_to_line or
                sampling_rate != self.sf.sampling_rate or
                pixel_bin_factor != self.sf.pixel_bin_factor or
                filtering_radius != self.sf.filtering_radius):

            self.sf = Scanfields(
                self.stack.paths,
                frame_rate,
                elongating_factor,
                dim_ratio_threshold,
                overlap_threshold,
                wavelength,
                fill_fraction,
                frame_flyback,
                fly_to_line,
                numerical_aperture,
                sampling_rate,
                self.sf.sampling_rate_ctl,
                pixel_bin_factor,
                filtering_radius,
                self.sf.framerate_delta_threshold)

            self.change_plot.emit()  # TODO
            self.change_roi_file.emit(self.sf)

            msg = QMessageBox()
            msg.setWindowTitle("Success")
            msg.setText("Roi files updated!")
            msg.setIcon(QMessageBox.Information)
            msg.addButton(QMessageBox.Ok)
            msg.exec_()


class SaveFiles(QFrame):

    def __init__(
            self,
            parent: QMainWindow,
            folder_name: str
    ) -> None:
        """
        Frame of saving file

        Parameters
        ----------
        parent : QMainWindow
            The main window
        folder_name : str
            destination folder

        Returns
        -------
        None

        """
        super().__init__(parent)

        layout = QGridLayout()
        self.setLayout(layout)

        self.setStyleSheet(darkMode.frame)

        self.folder_name = folder_name
        self.destination_folder = None
        self.to_save = None

        # Add widgets
        title = QLabel("Save\n")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(darkMode.title)
        layout.addWidget(title, 0, 0, 1, 3)

        destination_label = QLabel('Save to: ')
        destination_label.setAlignment(Qt.AlignVCenter)
        destination_label.setStyleSheet(darkMode.label)
        layout.addWidget(destination_label, 1, 0, 1, 1)

        save_entry = QLabel()
        save_entry.setWordWrap(False)
        save_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        save_entry.setStyleSheet(darkMode.entry)
        save_entry.setFixedWidth(350)
        layout.addWidget(save_entry, 1, 1, 1, 1)

        destination_button = QPushButton(' Choose')
        destination_button.setStyleSheet(
            darkMode.button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        destination_button.setIcon(QIcon(icon.folder))
        layout.addWidget(destination_button, 1, 2, 1, 1)
        destination_button.clicked.connect(
            lambda: self.select_destination(save_entry))

        self.save_button = QPushButton(' Save')
        self.save_button.setStyleSheet(
            darkMode.green_button +
            f'''QPushButton:hover {{
            background-color: {dim.hovering.hex};}}''')
        self.save_button.setIcon(QIcon(icon.save))
        layout.addWidget(self.save_button, 2, 2, 1, 1)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(lambda: self.save_roi_files())

    def get_structures(
            self,
            stack: Stack,
            morph: Morphology,
            sf: Scanfields
    ) -> None:

        self.stack = stack
        self.morph = morph
        self.sf = sf

    def update_scanfield(
            self,
            sf: Scanfields
    ) -> None:

        self.sf = sf
        self.save_button.setEnabled(True)

    def select_destination(
            self,
            label: QLabel
    ) -> None:

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        folder_dialog = QFileDialog.getExistingDirectory(
            self,
            "Select a Folder",
            self.folder_name,
            options=options)

        if folder_dialog:
            self.destination_folder = folder_dialog

        label.setText(folder_dialog)

    def which_scanfield_to_save(
            self,
            struct_type: str
    ) -> None:

        self.to_save = struct_type
        self.save_button.setEnabled(True)

    def save_roi_files(
            self
    ) -> None:

        if not self.destination_folder:
            error_msg = QMessageBox()
            error_msg.setWindowTitle("Error")
            error_msg.setText(
                "Please specify the destination folder for saving the files.")
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.addButton(QMessageBox.Ok)
            error_msg.exec_()
            return

        if not self.to_save:
            error_msg = QMessageBox()
            error_msg.setWindowTitle("Error")
            error_msg.setText(
                "Please specify the specific structure"
                "to save by plotting it.")
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.addButton(QMessageBox.Ok)
            error_msg.exec_()
            return

        if self.to_save == 'neuron':
            self.sf.save(self.sf.neuComp,
                         self.destination_folder,
                         self.to_save)
        elif self.to_save == 'apical':
            self.sf.save(self.sf.apiComp,
                         self.destination_folder,
                         self.to_save)
        elif self.to_save == 'basal':
            self.sf.save(self.sf.basComp,
                         self.destination_folder,
                         self.to_save)

        msg = QMessageBox()
        msg.setWindowTitle("Success")
        msg.setText("Roi files saved!")
        msg.setIcon(QMessageBox.Information)
        msg.addButton(QMessageBox.Ok)
        msg.exec_()
