""" Created on Fri Jan 26 15:52:11 2024
    @author: dcupolillo """

import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QDialog,
                             QComboBox, QFileDialog)
from PyQt5.QtGui import QIntValidator, QDoubleValidator

from ROIpy.metadata_creator.entries import (ACSF_recipes,
                                            cutting_recipes,
                                            intra_recipes,
                                            drug_list,
                                            intra_indicators)

filename = 'metadata_template.json'


class DrugsDialog(QDialog):

    def __init__(
            self,
            drugs: list
    ) -> None:

        super().__init__()
        self.initUI(drugs)

    def initUI(
            self,
            drugs: list
    ) -> None:

        self.setWindowTitle('Add Drugs')

        self.grid = QGridLayout()
        self.drug_widgets = []

        self.grid.addWidget(QLabel('Drug:'), 0, 0)
        self.grid.addWidget(QLabel('Concentration [µM]:'), 1, 0)

        for i, drug_name in enumerate(drugs):
            combo_box = QComboBox()
            combo_box.addItems(['None'] + drugs)
            concentration_edit = QLineEdit()
            concentration_edit.setValidator(QDoubleValidator())
            concentration_edit.setEnabled(False)

            combo_box.currentIndexChanged.connect(
                lambda index, line_edit=concentration_edit, combo=combo_box:
                self.update_line_edit_state(line_edit, combo)
            )

            self.grid.addWidget(combo_box, 0, i + 1)
            self.grid.addWidget(concentration_edit, 1, i + 1)
            self.drug_widgets.append((combo_box, concentration_edit))

        self.ok_button = QPushButton('OK', self)
        self.ok_button.clicked.connect(self.accept)
        self.grid.addWidget(self.ok_button, 2, len(drugs))

        self.setLayout(self.grid)

    def update_line_edit_state(
            self,
            line_edit: QLineEdit,
            combo_box: QComboBox
    ) -> None:

        if combo_box.currentText() == 'None':
            line_edit.setDisabled(True)
        else:
            line_edit.setEnabled(True)

    def get_data(self) -> list:
        return [{
            "Name": widget[0].currentText(),
            "Concentration": widget[1].text()}
            for widget in self.drug_widgets
            if widget[0].currentText() != "None"
        ]


class ACSFDialog(QDialog):

    def __init__(
            self
    ) -> None:

        super().__init__()
        self.drugs_data = None
        self.initUI()

    def initUI(
            self
    ) -> None:

        grid = QGridLayout()

        self.setWindowTitle('ACSF Data')

        self.type_combo_box = QComboBox(self)
        self.type_combo_box.addItems(ACSF_recipes)
        grid.addWidget(QLabel('Recipe:'), 0, 0)
        grid.addWidget(self.type_combo_box, 0, 1)

        self.osmolality_edit = QLineEdit(self)
        self.osmolality_edit.setValidator(QIntValidator())
        grid.addWidget(QLabel('Osmolality [mOsm/Kg]:'), 1, 0)
        grid.addWidget(self.osmolality_edit, 1, 1)

        self.ph_edit = QLineEdit(self)
        self.ph_edit.setValidator(QDoubleValidator(0.00, 14.00, 2))
        grid.addWidget(QLabel('pH:'), 2, 0)
        grid.addWidget(self.ph_edit, 2, 1)

        self.add_drugs_button = QPushButton('Add Drugs', self)
        self.add_drugs_button.clicked.connect(self.open_drugs_dialog)
        grid.addWidget(self.add_drugs_button, 3, 1)

        self.ok_button = QPushButton('OK', self)
        self.ok_button.clicked.connect(self.accept)
        grid.addWidget(self.ok_button, 4, 1)

        self.setLayout(grid)

    def get_data(
            self
    ) -> dict:
        return {
            "Recipe": self.type_combo_box.currentText(),
            "Osmolality": self.osmolality_edit.text(),
            "pH": self.ph_edit.text(),
            "Drugs": self.drugs_data
        }

    def accept(
            self
    ) -> None:

        self.data = self.get_data()
        super().accept()

    def open_drugs_dialog(
            self
    ) -> None:

        drugs_dialog = DrugsDialog(drug_list)

        if drugs_dialog.exec_():
            self.drugs_data = drugs_dialog.get_data()


class CuttingDialog(QDialog):

    def __init__(
            self
    ) -> None:

        super().__init__()
        self.drugs_data = None
        self.initUI()

    def initUI(
            self
    ) -> None:

        grid = QGridLayout()

        self.setWindowTitle('Cutting Data')

        self.type_combo_box = QComboBox(self)
        self.type_combo_box.addItems(cutting_recipes)
        grid.addWidget(QLabel('Recipe:'), 0, 0)
        grid.addWidget(self.type_combo_box, 0, 1)

        self.osmolality_edit = QLineEdit(self)
        self.osmolality_edit.setValidator(QIntValidator())
        grid.addWidget(QLabel('Osmolality [mOsm/Kg]:'), 1, 0)
        grid.addWidget(self.osmolality_edit, 1, 1)

        self.ph_edit = QLineEdit(self)
        self.ph_edit.setValidator(QDoubleValidator(0.00, 14.00, 2))
        grid.addWidget(QLabel('pH:'), 2, 0)
        grid.addWidget(self.ph_edit, 2, 1)

        self.add_drugs_button = QPushButton('Add Drugs', self)
        self.add_drugs_button.clicked.connect(self.open_drugs_dialog)
        grid.addWidget(self.add_drugs_button, 3, 1)

        self.ok_button = QPushButton('OK', self)
        self.ok_button.clicked.connect(self.accept)
        grid.addWidget(self.ok_button, 4, 1)

        self.setLayout(grid)

    def get_data(
            self
    ) -> dict:
        return {
            "Recipe": self.type_combo_box.currentText(),
            "Osmolality": self.osmolality_edit.text(),
            "pH": self.ph_edit.text(),
            "Drugs": self.drugs_data
        }

    def open_drugs_dialog(
            self
    ) -> None:

        drugs_dialog = DrugsDialog(drug_list)

        if drugs_dialog.exec_():
            self.drugs_data = drugs_dialog.get_data()


class IntracellularDialog(QDialog):

    def __init__(
            self
    ) -> None:

        super().__init__()
        self.drugs_data = None
        self.initUI()

    def initUI(
            self
    ) -> None:

        grid = QGridLayout()

        self.setWindowTitle('Intracellular Data')

        self.type_combo_box = QComboBox(self)
        self.type_combo_box.addItems(intra_recipes)
        grid.addWidget(QLabel('Recipe:'), 0, 0)
        grid.addWidget(self.type_combo_box, 0, 1)

        self.osmolality_edit = QLineEdit(self)
        self.osmolality_edit.setValidator(QIntValidator())
        grid.addWidget(QLabel('Osmolality [mOsm/Kg]:'), 1, 0)
        grid.addWidget(self.osmolality_edit, 1, 1)

        self.ph_edit = QLineEdit(self)
        self.ph_edit.setValidator(QDoubleValidator(0.00, 14.00, 2))
        grid.addWidget(QLabel('pH:'), 2, 0)
        grid.addWidget(self.ph_edit, 2, 1)

        self.add_drugs_button = QPushButton('Add Drugs', self)
        self.add_drugs_button.clicked.connect(self.open_drugs_dialog)
        grid.addWidget(self.add_drugs_button, 3, 1)

        self.ok_button = QPushButton('OK', self)
        self.ok_button.clicked.connect(self.accept)
        grid.addWidget(self.ok_button, 4, 1)

        self.setLayout(grid)

    def get_data(
            self
    ) -> dict:
        return {
            "Recipe": self.type_combo_box.currentText(),
            "Osmolality": self.osmolality_edit.text(),
            "pH": self.ph_edit.text(),
            "Drugs": self.drugs_data
        }

    def open_drugs_dialog(
            self
    ) -> None:

        drugs_dialog = DrugsDialog(intra_indicators)

        if drugs_dialog.exec_():
            self.drugs_data = drugs_dialog.get_data()


class StimulationDialog(QDialog):

    def __init__(
            self
    ) -> None:

        super().__init__()
        self.initUI()

    def initUI(
            self
    ) -> None:

        grid = QGridLayout()

        self.setWindowTitle('Stimulation Data')

        self.extracellular_stim_button = QPushButton(
            'Extracellular Stim.', self)
        self.extracellular_stim_button.setCheckable(True)
        self.extracellular_stim_button.toggled.connect(
            self.toggle_extracellular_fields)
        self.optogenetic_stim_button = QPushButton(
            'Optogenetic Stim.', self)
        self.optogenetic_stim_button.setCheckable(True)
        self.optogenetic_stim_button.toggled.connect(
            self.toggle_optogenetic_fields)

        # Fields for Extracellular Stim
        self.extracellular_bundle_edit = QLineEdit(self)
        self.extracellular_stim_freq_edit = QLineEdit(self)
        self.extracellular_num_pulses_edit = QLineEdit(self)
        self.extracellular_pulse_freq_edit = QLineEdit(self)

        # Fields for Optogenetic Stim
        self.optogenetic_bundle_edit = QLineEdit(self)
        self.optogenetic_stim_freq_edit = QLineEdit(self)
        self.optogenetic_num_pulses_edit = QLineEdit(self)
        self.optogenetic_pulse_freq_edit = QLineEdit(self)

        self.set_extracellular_fields_enabled(False)
        self.set_optogenetic_fields_enabled(False)

        # Add widgets to the grid
        grid.addWidget(self.extracellular_stim_button, 0, 1)
        grid.addWidget(self.optogenetic_stim_button, 0, 2)
        grid.addWidget(QLabel('Bundle:'), 1, 0)
        grid.addWidget(self.extracellular_bundle_edit, 1, 1)
        grid.addWidget(self.optogenetic_bundle_edit, 1, 2)
        grid.addWidget(QLabel('Stim Freq [Hz]:'), 2, 0)
        grid.addWidget(self.extracellular_stim_freq_edit, 2, 1)
        grid.addWidget(self.optogenetic_stim_freq_edit, 2, 2)
        grid.addWidget(QLabel('Number of Pulses:'), 3, 0)
        grid.addWidget(self.extracellular_num_pulses_edit, 3, 1)
        grid.addWidget(self.optogenetic_num_pulses_edit, 3, 2)
        grid.addWidget(QLabel('Pulse Frequency [Hz]:'), 4, 0)
        grid.addWidget(self.extracellular_pulse_freq_edit, 4, 1)
        grid.addWidget(self.optogenetic_pulse_freq_edit, 4, 2)
        self.extracellular_pulse_freq_edit.setDisabled(True)
        self.optogenetic_pulse_freq_edit.setDisabled(True)

        self.setLayout(grid)
        self.setWindowTitle('Stimulation Data')

        # Apply validators
        self.extracellular_stim_freq_edit.setValidator(QDoubleValidator())
        self.extracellular_num_pulses_edit.setValidator(QIntValidator())
        self.extracellular_pulse_freq_edit.setValidator(QDoubleValidator())

        self.optogenetic_stim_freq_edit.setValidator(QDoubleValidator())
        self.optogenetic_num_pulses_edit.setValidator(QIntValidator())
        self.optogenetic_pulse_freq_edit.setValidator(QDoubleValidator())

        # Connect number of pulses edits to update function
        self.extracellular_num_pulses_edit.textChanged.connect(
            self.update_extracellular_pulse_freq)
        self.optogenetic_num_pulses_edit.textChanged.connect(
            self.update_optogenetic_pulse_freq)

        self.ok_button = QPushButton('OK', self)
        self.ok_button.clicked.connect(self.accept)
        grid.addWidget(self.ok_button, 5, 2)

    def toggle_extracellular_fields(
            self,
            checked
    ) -> None:

        self.set_extracellular_fields_enabled(checked)

    def toggle_optogenetic_fields(
            self,
            checked
    ) -> None:

        self.set_optogenetic_fields_enabled(checked)

    def set_extracellular_fields_enabled(
            self,
            enabled
    ) -> None:

        self.extracellular_bundle_edit.setEnabled(enabled)
        self.extracellular_stim_freq_edit.setEnabled(enabled)
        self.extracellular_num_pulses_edit.setEnabled(enabled)
        self.update_extracellular_pulse_freq()

    def set_optogenetic_fields_enabled(
            self,
            enabled
    ) -> None:

        self.optogenetic_bundle_edit.setEnabled(enabled)
        self.optogenetic_stim_freq_edit.setEnabled(enabled)
        self.optogenetic_num_pulses_edit.setEnabled(enabled)
        self.update_optogenetic_pulse_freq()

    def update_extracellular_pulse_freq(
            self
    ) -> None:

        num_pulses = self.extracellular_num_pulses_edit.text()

        if num_pulses and int(num_pulses) > 1:
            self.extracellular_pulse_freq_edit.setEnabled(True)

        else:
            self.extracellular_pulse_freq_edit.setDisabled(True)

    def update_optogenetic_pulse_freq(
            self
    ) -> None:

        num_pulses = self.optogenetic_num_pulses_edit.text()

        if num_pulses and int(num_pulses) > 1:
            self.optogenetic_pulse_freq_edit.setEnabled(True)

        else:
            self.optogenetic_pulse_freq_edit.setDisabled(True)

    def get_data(
            self
    ) -> dict:

        data = {
            "Type": [],
            "Bundle": [],
            "Stim Freq [Hz]": [],
            "Number of Pulses": [],
            "Pulse Frequency [Hz]": []
        }

        # Check if Extracellular Stim button is toggled
        if self.extracellular_stim_button.isChecked():
            data["Type"].append("Extracellular")
            data["Bundle"].append(
                self.extracellular_bundle_edit.text())
            data["Stim Freq [Hz]"].append(
                self.extracellular_stim_freq_edit.text())
            data["Number of Pulses"].append(
                self.extracellular_num_pulses_edit.text())
            data["Pulse Frequency [Hz]"].append(
                self.extracellular_pulse_freq_edit.text())

        # Check if Optogenetic Stim button is toggled
        if self.optogenetic_stim_button.isChecked():
            data["Type"].append("Optogenetic")
            data["Bundle"].append(
                self.optogenetic_bundle_edit.text())
            data["Stim Freq [Hz]"].append(
                self.optogenetic_stim_freq_edit.text())
            data["Number of Pulses"].append(
                self.optogenetic_num_pulses_edit.text())
            data["Pulse Frequency [Hz]"].append(
                self.optogenetic_pulse_freq_edit.text())

        return data


class DataEntry(QWidget):

    def __init__(
            self
    ) -> None:

        super().__init__()

        self.acsf_data = {}
        self.cutting_data = {}
        self.intracellular_data = {}
        self.stimulation_data = {}

        self.initUI()
        self.check_fields()

    def initUI(
            self
    ) -> None:

        layout = QGridLayout()

        self.date_edit = QLineEdit(self)
        self.date_edit.setText(datetime.now().strftime("%y%m%d"))
        self.date_edit.setReadOnly(True)
        self.date_edit.textChanged.connect(self.check_fields)

        self.neuron_id_edit = QLineEdit(self)
        self.neuron_id_edit.setValidator(QIntValidator())
        self.neuron_id_edit.textChanged.connect(self.format_neuron_id)

        self.mouse_id_edit = QLineEdit(self)

        self.genotype_edit = QLineEdit(self)

        layout.addWidget(QLabel('Date:'), 0, 0)
        layout.addWidget(self.date_edit, 0, 1)
        layout.addWidget(QLabel('Neuron ID:'), 1, 0)
        layout.addWidget(self.neuron_id_edit, 1, 1)
        layout.addWidget(QLabel('Mouse ID:'), 2, 0)
        layout.addWidget(self.mouse_id_edit, 2, 1)
        layout.addWidget(QLabel('Mouse Genotype:'), 3, 0)
        layout.addWidget(self.genotype_edit, 3, 1)
        layout.addWidget(QLabel('ACSF:'), 4, 0)
        layout.addWidget(QLabel('Cutting:'), 5, 0)
        layout.addWidget(QLabel('Intra:'), 6, 0)
        layout.addWidget(QLabel('Stimulation:'), 7, 0)

        self.acsf_button = QPushButton('Edit ACSF', self)
        self.acsf_button.clicked.connect(self.open_ACSF_dialog)
        layout.addWidget(self.acsf_button, 4, 1)

        self.cutting_button = QPushButton('Edit Cutting', self)
        self.cutting_button.clicked.connect(self.open_cutting_dialog)
        layout.addWidget(self.cutting_button, 5, 1)

        self.intra_button = QPushButton('Edit Intra', self)
        self.intra_button.clicked.connect(self.open_intra_dialog)
        layout.addWidget(self.intra_button, 6, 1)

        self.stimulation_button = QPushButton('Edit Stim', self)
        self.stimulation_button.clicked.connect(self.open_stim_dialog)
        layout.addWidget(self.stimulation_button, 7, 1)

        self.save_button = QPushButton('Save Data', self)
        self.save_button.clicked.connect(self.save_data)
        self.update_button_style()
        self.save_button.setDisabled(True)
        layout.addWidget(self.save_button, 8, 1)

        self.setLayout(layout)
        self.setWindowTitle('Data Entry Form')

    def format_neuron_id(
            self
    ) -> None:

        neuron_id = self.neuron_id_edit.text()
        if neuron_id.isdigit():
            neuron_id = int(neuron_id)
            # Formats the ID with leading zeros
            formatted_id = f"{neuron_id:04d}"
            self.neuron_id_edit.setText(formatted_id)
        self.check_fields()

    def update_button_style(
            self
    ) -> None:

        if self.save_button.isEnabled():
            self.save_button.setStyleSheet("QPushButton {"
                                           "background-color: green; "
                                           "color: white; "
                                           # "border-radius: 5px; "
                                           "padding: 6px; "
                                           "font-weight: bold;"
                                           "}"
                                           "QPushButton:disabled {"
                                           "background-color: gray; "
                                           "color: darkgray;"
                                           "}")
        else:
            self.save_button.setStyleSheet("QPushButton:disabled {"
                                           "background-color: gray; "
                                           "color: darkgray;"
                                           "}")

    def check_fields(
            self
    ) -> None:

        if self.date_edit.text() and self.neuron_id_edit.text():
            self.save_button.setEnabled(True)

        else:
            self.save_button.setDisabled(True)

    def open_ACSF_dialog(
            self
    ) -> None:

        dialog = ACSFDialog()
        if dialog.exec_():
            self.acsf_data = dialog.get_data()

    def open_cutting_dialog(
            self
    ) -> None:

        dialog = CuttingDialog()
        if dialog.exec_():
            self.cutting_data = dialog.get_data()

    def open_intra_dialog(
            self
    ) -> None:

        dialog = IntracellularDialog()
        if dialog.exec_():
            self.intracellular_data = dialog.get_data()

    def open_stim_dialog(
            self
    ) -> None:

        dialog = StimulationDialog()
        if dialog.exec_():
            self.stimulation_data = dialog.get_data()

    def save_data(
            self
    ) -> None:

        options = QFileDialog.Options()

        default_filename = os.path.join(
            os.getcwd(),
            f'{self.date_edit.text()}_cell{self.neuron_id_edit.text()}')

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save File", default_filename,
            "JSON Files (*.json)", options=options)

        if filename:
            data = {
                "Date": self.date_edit.text(),
                "NeuronID": self.neuron_id_edit.text(),
                "MouseID": self.mouse_id_edit.text(),
                "Genotype": self.genotype_edit.text(),
                "ACSF": {

                    "Osmolality": self.acsf_data.get("Osmolality", ""),
                    "pH": self.acsf_data.get("pH", ""),
                    "Drugs": self.acsf_data.get("Drugs", [])
                },
                "Cutting": {
                    "Osmolality": self.cutting_data.get("Osmolality", ""),
                    "pH": self.cutting_data.get("pH", ""),
                    "Drugs": self.cutting_data.get("Drugs", [])
                },
                "Intracellular": {
                    "Type": self.intracellular_data.get("Recipe", ""),
                    "Osmolality": self.intracellular_data.get(
                        "Osmolality", ""),
                    "pH": self.intracellular_data.get("pH", ""),
                    "Drugs": self.intracellular_data.get("Drugs", [])
                },
                "Stimulation": {
                    "Type": self.stimulation_data.get("Type", ""),
                    "Axons": self.stimulation_data.get("Bundle", ""),
                    "Frequency [Hz]": self.stimulation_data.get(
                        "Stim Freq [Hz]", ""),
                    "Number of Pulse": self.stimulation_data.get(
                        "Number of Pulses", ""),
                    "Pulse Frequency [Hz]": self.stimulation_data.get(
                        "Pulse Frequency [Hz]", "")
                }
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)

            print("Data saved to", filename)

            print(data)


def main():
    app = QApplication(sys.argv)
    ex = DataEntry()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
