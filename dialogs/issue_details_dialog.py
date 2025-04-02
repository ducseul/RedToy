from PyQt5 import QtWidgets, QtGui
import webbrowser

class IssueDetailsDialog(QtWidgets.QDialog):
    def __init__(self, parent, redmine, issue, font_size, redmine_url):
        super().__init__(parent)
        self.setWindowTitle(f'Issue #{issue.id}')
        self.resize(1080, 600)

        layout = QtWidgets.QVBoxLayout()

        issue = redmine.issue.get(issue.id)

        details = f"""
Issue #{issue.id}: {issue.subject}
Status: {issue.status.name}
Priority: {issue.priority.name}
Assigned to: {getattr(issue, 'assigned_to', 'Unassigned')}
Created: {issue.created_on}
Updated: {issue.updated_on}

Description:
{issue.description}
        """

        text_edit = QtWidgets.QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(details)
        font = text_edit.font()
        font.setPointSize(font_size)
        text_edit.setFont(font)

        layout.addWidget(text_edit)

        button_layout = QtWidgets.QHBoxLayout()
        web_button = QtWidgets.QPushButton('Open in browser (Alt+B)')
        web_button.setShortcut('Alt+B')
        web_button.clicked.connect(lambda: webbrowser.open(f"{redmine_url}/issues/{issue.id}"))

        close_button = QtWidgets.QPushButton('Close (Esc)')
        close_button.setShortcut('Esc')
        close_button.clicked.connect(self.accept)

        button_layout.addWidget(web_button)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.accept)

        self.setLayout(layout)