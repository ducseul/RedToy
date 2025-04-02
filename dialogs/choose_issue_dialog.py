from PyQt5 import QtWidgets, QtGui
import webbrowser

class ChooseIssueDialog(QtWidgets.QDialog):
    def __init__(self, parent, redmine, font_size, redmine_url):
        super().__init__(parent)
        self.selected_issue = None
        self.redmine_url = redmine_url

        self.setWindowTitle('Choose Issue')
        self.resize(1080, 600)
        layout = QtWidgets.QVBoxLayout()

        issues = redmine.issue.filter(assigned_to_id='me', status_id='open')
        self.issues = issues

        search_layout = QtWidgets.QHBoxLayout()
        search_layout.addWidget(QtWidgets.QLabel("Search (Alt+F):"))
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Filter issues by ID or subject...")
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        self.issues_table = QtWidgets.QTableWidget()
        self.issues_table.setColumnCount(4)
        self.issues_table.setHorizontalHeaderLabels(['ID', 'Subject', 'Status', 'Priority'])
        self.issues_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.issues_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.issues_table.setFont(QtGui.QFont('', font_size))
        layout.addWidget(self.issues_table)

        self.populate_table(issues)
        self.search_edit.textChanged.connect(self.filter_issues)

        button_layout = QtWidgets.QHBoxLayout()
        select_button = QtWidgets.QPushButton('Select as current (Alt+S)')
        select_button.setShortcut('Alt+S')
        select_button.clicked.connect(self.select_issue)
        button_layout.addWidget(select_button)

        open_button = QtWidgets.QPushButton('Open in browser (Alt+B)')
        open_button.setShortcut('Alt+B')
        open_button.clicked.connect(self.open_in_browser)
        button_layout.addWidget(open_button)

        cancel_button = QtWidgets.QPushButton('Cancel (Esc)')
        cancel_button.setShortcut('Esc')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+F"), self, self.search_edit.setFocus)
        QtWidgets.QShortcut(QtGui.QKeySequence("Return"), self.issues_table, self.select_issue)
        QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), self, self.reject)
        self.issues_table.cellDoubleClicked.connect(lambda row, col: self.select_issue())

        self.setLayout(layout)

    def populate_table(self, issues):
        self.issues_table.setRowCount(len(issues))
        for row, issue in enumerate(issues):
            self.issues_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(issue.id)))
            self.issues_table.setItem(row, 1, QtWidgets.QTableWidgetItem(issue.subject))
            self.issues_table.setItem(row, 2, QtWidgets.QTableWidgetItem(issue.status.name))
            self.issues_table.setItem(row, 3, QtWidgets.QTableWidgetItem(issue.priority.name))

    def filter_issues(self):
        text = self.search_edit.text().lower()
        filtered = [i for i in self.issues if text in str(i.id).lower() or text in i.subject.lower() or text in i.status.name.lower() or text in i.priority.name.lower()]
        self.populate_table(filtered)

    def select_issue(self):
        selected = self.issues_table.selectionModel().selectedRows()
        if selected:
            issue_id = int(self.issues_table.item(selected[0].row(), 0).text())
            for issue in self.issues:
                if issue.id == issue_id:
                    self.selected_issue = issue
                    self.accept()
                    return
        QtWidgets.QMessageBox.warning(self, 'No selection', 'Please select an issue.')

    def open_in_browser(self):
        selected = self.issues_table.selectionModel().selectedRows()
        if selected:
            issue_id = int(self.issues_table.item(selected[0].row(), 0).text())
            webbrowser.open(f"{self.redmine_url}/issues/{issue_id}")
        else:
            QtWidgets.QMessageBox.warning(self, 'No selection', 'Please select an issue.')
