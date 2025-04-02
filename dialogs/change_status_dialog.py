from PyQt5 import QtWidgets, QtGui

class ChangeStatusDialog(QtWidgets.QDialog):
    def __init__(self, parent, redmine, issue, font_size):
        super().__init__(parent)
        self.redmine = redmine
        self.issue = redmine.issue.get(issue.id)
        self.updated_issue = None

        self.setWindowTitle('Change Issue Status')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel(f'Current status: {self.issue.status.name}'))
        layout.addWidget(QtWidgets.QLabel('Select new status (Alt+S to focus):'))

        self.status_combo = QtWidgets.QComboBox()
        self.status_map = {}

        for status in redmine.issue_status.all():
            if status.id != self.issue.status.id:
                self.status_combo.addItem(status.name, status.id)
                self.status_map[status.name] = status.id

        layout.addWidget(self.status_combo)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_status)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+S"), self, self.status_combo.setFocus)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, self.accept)

        self.setLayout(layout)

    def save_status(self):
        selected_id = self.status_combo.currentData()
        if selected_id:
            self.redmine.issue.update(self.issue.id, status_id=selected_id)
            self.updated_issue = self.redmine.issue.get(self.issue.id)
            QtWidgets.QMessageBox.information(self, 'Status Updated', f'Status updated to {self.updated_issue.status.name}')
            self.accept()