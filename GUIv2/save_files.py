""" Created on Tue Aug 27 15:56:23 2024
    @author: dcupolillo """

from PyQt5.QtWidgets import (
    QMainWindow, QFrame, QGridLayout, QPushButton, QMessageBox)
from ROIpy.core.structures import Stack, Morphology, Scanfields


class SaveFiles(QFrame):

    def __init__(self, parent: QMainWindow) -> None:
        """ Frame of saving file. """

        super().__init__(parent)

        layout = QGridLayout()
        self.setLayout(layout)

        self.to_save = None

        self.save_button = QPushButton('Save .roi files')
        layout.addWidget(self.save_button, 0, 0, 1, 1)
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

    def update_scanfield(self, sf: Scanfields) -> None:

        self.sf = sf
        self.save_button.setEnabled(True)

    def select_destination(self, paths) -> None:

        self.destination_folder = paths

    def which_scanfield_to_save(self, struct_type: str) -> None:
        if struct_type:
            self.to_save = struct_type
            self.save_button.setEnabled(True)
        else:
            self.to_save = None
            self.save_button.setEnabled(False)

    def save_roi_files(self) -> None:

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

        # save Roi Files
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
