""" Created on Tue Aug 27 15:18:40 2024
    @author: dcupolillo """

import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget, QMessageBox

from ROIpy.GUIv2.load_frame import LoadFiles
from ROIpy.GUIv2.plot_structures_controller import StructureFrame
from ROIpy.GUIv2.scan_parameters import ScanParameters
from ROIpy.GUIv2.save_files import SaveFiles
from ROIpy.GUIv2.canvas import Canvas


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        """ Main Window with Frames for each functionality."""

        QMainWindow.__init__(self)

        self.paths = None

        self.central_widget = QWidget(self)
        self.layout = QGridLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)
        self.setWindowTitle('ROIpy')

        # add all the frames
        self.load_files = LoadFiles(self)
        self.layout.addWidget(self.load_files, 0, 0, 1, 1)

        self.structure_frame = StructureFrame(self)
        self.layout.addWidget(self.structure_frame, 1, 0, 1, 1)

        self.canvas = Canvas(self)
        self.layout.addWidget(self.canvas, 0, 1, 6, 6)

        self.scan_parameters = ScanParameters(self)
        self.layout.addWidget(self.scan_parameters, 2, 0, 1, 1)

        self.save_files = SaveFiles(self)
        self.layout.addWidget(self.save_files, 3, 0, 1, 1)

        # connect the signals
        self.load_files.paths_signal.connect(
            lambda paths: setattr(self, 'paths', paths))

        self.load_files.generate_button_clicked.connect(
            self.structure_frame.activate_buttons)

        self.load_files.structures_signal.connect(
            self.canvas.get_structures)

        self.structure_frame.morph_plotted.connect(self.canvas.plot_morph)
        self.structure_frame.clear_morph.connect(self.canvas.clear_morph)
        self.structure_frame.sf_plotted.connect(self.canvas.plot_scanfield)
        self.structure_frame.clear_sf.connect(self.canvas.clear_scanfield)
        self.structure_frame.max_proj_activated.connect(
            self.canvas.activate_max_proj)
        self.structure_frame.max_proj_disabled.connect(
            self.canvas.disable_max_proj)

        self.load_files.structures_signal.connect(
            self.scan_parameters.get_structures)

        self.load_files.generate_button_clicked.connect(
            self.scan_parameters.get_scanfield)

        self.load_files.paths_signal.connect(
            lambda paths: self.save_files.select_destination(paths))

        self.canvas.which_scanfield_signal.connect(
            self.save_files.which_scanfield_to_save)

        self.load_files.structures_signal.connect(
            self.save_files.get_structures)

        # self.scan_parameters.change_roi_file.connect(
        #     self.save_files.update_scanfield)

    def closeEvent(self, event):
        """Handle the close event triggered by the top corner X button."""
        reply = QMessageBox.question(
            self, 'Quit Application',
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            QtWidgets.QApplication.quit()
        else:
            event.ignore()


def run_app():
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()

    app.setQuitOnLastWindowClosed(True)

    roipy_window = MainWindow()
    roipy_window.show()

    if not QtWidgets.QApplication.instance():
        sys.exit(app.exec_())
    else:
        app.exec_()
