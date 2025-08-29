""" Created on Tue Aug 27 15:22:29 2024
    @author: dcupolillo """

from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QFrame, QLabel, QGridLayout,
    QPushButton, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from ROIpy.core.structures import Stack, Morphology, Scanfields


class LoadFiles(QFrame):

    paths_signal = pyqtSignal(Path)
    structures_signal = pyqtSignal(Stack, Morphology, Scanfields)
    generate_button_clicked = pyqtSignal()

    def __init__(self, parent: QMainWindow) -> None:
        """ Frame where path is loaded. """

        super().__init__(parent)

        self.date = None
        self.cell_n = None

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Add widgets
        title = QLabel("Load")
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title, 0, 0, 1, 3)

        # first row
        self.path_entry = QLabel()
        self.path_entry.setWordWrap(False)
        self.path_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.layout.addWidget(QLabel('Select a path: '), 1, 0, 1, 1)
        self.layout.addWidget(self.path_entry, 1, 1, 1, 1)

        path_button = QPushButton('Choose')
        self.layout.addWidget(path_button, 1, 2, 1, 1)
        path_button.clicked.connect(self.choose_file)

        self.generate_button = QPushButton('Generate')
        self.layout.addWidget(self.generate_button, 2, 2)
        self.generate_button.clicked.connect(
            lambda: self.generate())
        self.generate_button.setEnabled(False)

    def choose_file(self) -> None:
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

        self.folder_name = Path(folder_name)

        if self.folder_name:
            self.path_entry.setText(folder_name)

            # Split the folder path into its components
            path_parts = self.folder_name.parts

            # Store the last and second-to-last components
            self.cell_n = int(''.join(filter(str.isdigit, path_parts[-1])))
            self.date = str(path_parts[-2])

            self.are_files_loaded()

    def are_files_loaded(self) -> None:

        if self.date and self.cell_n:
            self.generate_button.setEnabled(True)
            self.paths_signal.emit(self.folder_name)

    def generate(self) -> None:
        """
        Creates the core Structures of ROIpy.
        Emit a signal to Main Window.
        Enables the structure buttons in the structure frame.
        """
        for file in self.folder_name.iterdir():
            if file.suffix in ['.tif', '.tiff']:
                stack_filename = file
            elif file.suffix == ".swc":
                swc_filename = file
            else:
                pass

        stack = Stack(stack_filename)
        morph = Morphology(swc_filename, stack)
        sf = Scanfields(morph)

        self.structures_signal.emit(stack, morph, sf)
        self.generate_button_clicked.emit()

        QMessageBox.information(self, "Success", "DONE!")
