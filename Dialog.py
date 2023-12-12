from PyQt5.uic import loadUiType
from os import path
from PyQt5 import QtCore as qtc
from PyQt5.QtWidgets import QDialogButtonBox, QFileDialog, QMessageBox

FORM_CLASS_DIALOG, _ = loadUiType(path.join(path.dirname(__file__), "dialog.ui"))


class Dialog(QDialogButtonBox, FORM_CLASS_DIALOG):
    submitClicked = qtc.pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        QDialogButtonBox.__init__(self, parent=None)
        self.setupUi(self)
        self.setWindowTitle("open signal")
        self.browse.clicked.connect(self.browse_window)

    def browse_window(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "open wave file", "Data/", "WAV Files (*.WAV)")
        if file_path != '':
            self.show_path.setText(file_path)
        else:
            QMessageBox.warning(self, "Error", "failed to add file")

    def accept(self):
        if self.show_path.text() == '':
            QMessageBox.warning(self, "Error", "you have not choose file")
        else:
            chosen_radio_button = None
            for mode_index in reversed(range(self.radio_button_horizontalLayout.count())):
                chosen_radio_button = self.radio_button_horizontalLayout.itemAt(mode_index).widget()
                if chosen_radio_button.isChecked():
                    break
            self.submitClicked.emit(self.show_path.text(), chosen_radio_button.text())
            self.close()

    def reject(self):
        self.close()
