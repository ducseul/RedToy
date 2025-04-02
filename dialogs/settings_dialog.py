from PyQt5 import QtWidgets, QtGui
import keyboard

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.resize(360, 250)

        self.font_size = parent.font_size
        self.hotkey = parent.hotkey

        layout = QtWidgets.QVBoxLayout()

        # Font size
        font_layout = QtWidgets.QHBoxLayout()
        font_layout.addWidget(QtWidgets.QLabel('Font Size (Alt+F):'))

        self.font_spin = QtWidgets.QSpinBox()
        self.font_spin.setMinimum(8)
        self.font_spin.setMaximum(24)
        self.font_spin.setValue(self.font_size)
        font_layout.addWidget(self.font_spin)

        layout.addLayout(font_layout)

        # Hotkey input
        hotkey_layout = QtWidgets.QHBoxLayout()
        hotkey_layout.addWidget(QtWidgets.QLabel('Hotkey (Alt+K):'))

        self.hotkey_edit = QtWidgets.QLineEdit(self.hotkey)
        hotkey_layout.addWidget(self.hotkey_edit)

        layout.addLayout(hotkey_layout)

        # Test hotkey
        test_button = QtWidgets.QPushButton('Test Hotkey (Alt+T)')
        test_button.setShortcut('Alt+T')
        test_button.clicked.connect(self.test_hotkey)
        layout.addWidget(test_button)

        # Preview
        self.preview_label = QtWidgets.QLabel('This is a font size preview')
        preview_font = QtGui.QFont()
        preview_font.setPointSize(self.font_size)
        self.preview_label.setFont(preview_font)
        layout.addWidget(self.preview_label)

        self.font_spin.valueChanged.connect(self.update_preview)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accepted)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+F"), self, self.font_spin.setFocus)
        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+K"), self, self.hotkey_edit.setFocus)
        QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), self, self.reject)

        self.setLayout(layout)

    def update_preview(self):
        font = QtGui.QFont()
        font.setPointSize(self.font_spin.value())
        self.preview_label.setFont(font)

    def test_hotkey(self):
        hotkey = self.hotkey_edit.text()
        try:
            keyboard.add_hotkey(hotkey, lambda: print("Test hotkey pressed"))
            QtWidgets.QMessageBox.information(self, 'Hotkey Test', f"Hotkey '{hotkey}' registered successfully!")
            keyboard.remove_hotkey(hotkey)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Hotkey Test Failed', str(e))

    def accepted(self):
        self.font_size = self.font_spin.value()
        self.hotkey = self.hotkey_edit.text()
        self.accept()