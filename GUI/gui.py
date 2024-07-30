""" Created on Tue Nov  7 10:03:57 2023
    @author: dcupolillo """

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget

import ROIpy as rp
from ROIpy.GUI.frames import LoadFiles, ScanParameters, SaveFiles
from ROIpy.GUI.canvas import Canvas, StructureFrame
from ROIpy.GUI.guiStyles import darkMode


class MainWindow(QMainWindow):

    def __init__(
            self
    ) -> None:
        """
        Main Window with Frames for each functionality.

        Returns
        -------
        None

        """

        super().__init__()

        self.init_variables()
        self.window_geometry()
        self.init_window()
        self.add_frames()

    def init_variables(
            self
    ) -> None:

        self.tif_filename = None
        self.swc_filename = None
        self.folder_name = None

    def window_geometry(
            self
    ) -> None:
        """
        Defines window geometry as specified in gui_styles.style
        """

        self.window_height = darkMode.window_size[0]
        self.window_width = darkMode.window_size[1]
        self.window_left_offset = darkMode.window_offset[0]
        self.window_top_offset = darkMode.window_offset[1]

        self.central_widget = QWidget(self)
        self.layout = QGridLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

    def init_window(
            self
    ) -> None:
        """
        Set the graphical properties of the window.
        """

        self.setStyleSheet(darkMode.window)
        self.setWindowTitle(f'ROIpy - {rp.__version__}')
        self.setGeometry(self.window_left_offset, self.window_top_offset,
                         self.window_width, self.window_height)

    def add_frames(
            self
    ) -> None:
        """
        Add the individual frames.
        Manages the signals.

        Returns
        -------
        None

        """

        # Load files frame and receive file names signal
        self.load_files = LoadFiles(self)
        self.load_files.files_name.connect(
            lambda tif_filename, swc_filename, folder_name:
                setattr(self, 'tif_filename', tif_filename) or
                setattr(self, 'swc_filename', swc_filename) or
                setattr(self, 'folder_name', folder_name))

        self.layout.addWidget(self.load_files, 0, 0, 1, 1)

        # Structure Buttons Frame and receive signal
        self.structure_frame = StructureFrame(self)
        self.load_files.generate_button_clicked.connect(
            self.structure_frame.activate_buttons)
        self.layout.addWidget(self.structure_frame, 1, 0, 1, 1)

        # Canvas
        self.canvas = Canvas(self,
                             self.load_files.structures,
                             self.structure_frame)
        self.layout.addWidget(self.canvas, 0, 1, 4, 2)

        # Scan parameters
        self.scan_parameters = ScanParameters(self)
        self.load_files.structures.connect(self.scan_parameters.get_structures)
        self.load_files.generate_button_clicked.connect(
            self.scan_parameters.get_scanfield)
        self.layout.addWidget(self.scan_parameters, 2, 0, 1, 1)

        # Save
        self.save_files = SaveFiles(self, self.folder_name)
        self.canvas.which_scanfield_signal.connect(
            self.save_files.which_scanfield_to_save)
        self.load_files.structures.connect(self.save_files.get_structures)
        self.scan_parameters.change_roi_file.connect(
            self.save_files.update_scanfield)
        self.layout.addWidget(self.save_files, 3, 0, 1, 1)


def main():
    app = QApplication([])

    roipy_window = MainWindow()

    roipy_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
