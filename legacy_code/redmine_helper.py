import configparser
import os
import sys
import webbrowser

import keyboard
from PyQt5 import QtWidgets, QtCore, QtGui
from redminelib import Redmine
from redminelib.exceptions import AuthError


class RedmineHelperService:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.helper = RedmineHelper()

        # Use a lower frequency timer to reduce CPU usage
        # 500ms is enough for hotkey responsiveness without causing lag
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.process_events)
        self.timer.start(500)

    def process_events(self):
        # Process pending events but avoid excessive CPU usage
        QtWidgets.QApplication.processEvents()

    def run(self):
        # Run the application without showing the UI initially
        # It will show up when the hotkey is pressed
        return self.app.exec_()


class RedmineHelper(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.cfg')
        self.current_issue = None
        self.redmine = None
        self.hotkey = None
        self.font_size = 10  # Default font size
        self.load_config()
        self.init_redmine()
        self.init_ui()
        self.apply_font_size()

        # Set window flags to stay on top but allow normal window behavior
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # Use a single-shot timer to register the hotkey after the app is fully initialized
        QtCore.QTimer.singleShot(1000, self.register_hotkey)

        # Create a flag to track visibility state
        self.manually_hidden = False

    def load_config(self):
        """Load configuration from config file"""
        config = configparser.ConfigParser()

        # Default configuration
        self.redmine_url = "https://redmine.example.com"
        self.api_key = ""
        self.hotkey = "ctrl+shift+r"
        self.font_size = 10

        # Try to load from config file
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            if 'Redmine' in config:
                self.redmine_url = config['Redmine'].get('url', self.redmine_url)
                self.api_key = config['Redmine'].get('api_key', self.api_key)
            if 'Settings' in config:
                self.hotkey = config['Settings'].get('hotkey', self.hotkey)
                self.font_size = config['Settings'].getint('font_size', self.font_size)
        else:
            # Create default config
            config['Redmine'] = {
                'url': self.redmine_url,
                'api_key': self.api_key
            }
            config['Settings'] = {
                'hotkey': self.hotkey,
                'font_size': str(self.font_size)
            }
            with open(self.config_file, 'w') as f:
                config.write(f)
            print(f"Default configuration file created at {self.config_file}")
            print("Please edit it to add your Redmine URL and API key.")

    def save_config(self):
        """Save current configuration to config file"""
        config = configparser.ConfigParser()

        config['Redmine'] = {
            'url': self.redmine_url,
            'api_key': self.api_key
        }
        config['Settings'] = {
            'hotkey': self.hotkey,
            'font_size': str(self.font_size)
        }

        with open(self.config_file, 'w') as f:
            config.write(f)
        print(f"Configuration saved to {self.config_file}")

    def init_redmine(self):
        """Initialize Redmine connection"""
        try:
            if not self.api_key:
                print("API key not set. Please edit the config file.")
                return None

            self.redmine = Redmine(self.redmine_url, key=self.api_key)
            # Test connection by getting current user
            self.current_user = self.redmine.user.get('current')
            print(f"Connected to Redmine as {self.current_user.firstname} {self.current_user.lastname}")
            return True
        except AuthError:
            print("Authentication failed. Please check your API key.")
            return False
        except Exception as e:
            print(f"Failed to connect to Redmine: {str(e)}")
            return False

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle('Redmine Helper')
        self.resize(650, 350)
        # Set a minimum size to prevent UI glitches
        self.setMinimumSize(650, 350)

        layout = QtWidgets.QVBoxLayout()

        # Option 1: View issue details
        self.view_button = QtWidgets.QPushButton('1. View current issue details (1)')
        self.view_button.setShortcut('1')
        self.view_button.clicked.connect(self.view_issue_details)
        self.view_button.setEnabled(self.current_issue is not None)
        layout.addWidget(self.view_button)

        # Option 2: Change issue status
        self.status_button = QtWidgets.QPushButton('2. Change issue status (2)')
        self.status_button.setShortcut('2')
        self.status_button.clicked.connect(self.change_issue_status)
        self.status_button.setEnabled(self.current_issue is not None)
        layout.addWidget(self.status_button)

        # Option 3: Choose issue to work on
        self.choose_button = QtWidgets.QPushButton('3. Choose issue to work on (3)')
        self.choose_button.setShortcut('3')
        self.choose_button.clicked.connect(self.choose_issue)
        layout.addWidget(self.choose_button)

        # Option 4: Settings
        self.settings_button = QtWidgets.QPushButton('4. Settings (4)')
        self.settings_button.setShortcut('4')
        self.settings_button.clicked.connect(self.show_settings)
        layout.addWidget(self.settings_button)

        # Status bar
        self.status_label = QtWidgets.QLabel('Not connected to Redmine')
        if self.redmine:
            self.status_label.setText(f'Connected as {self.current_user.firstname} {self.current_user.lastname}')
        layout.addWidget(self.status_label)

        # Current issue info
        self.issue_label = QtWidgets.QLabel('No issue selected')
        if self.current_issue:
            self.issue_label.setText(f'Working on #{self.current_issue.id}: {self.current_issue.subject}')
        layout.addWidget(self.issue_label)

        # Add keyboard shortcut info
        self.hotkey_label = QtWidgets.QLabel(f'Press {self.hotkey} to toggle this window, Alt+H to hide')
        layout.addWidget(self.hotkey_label)

        # Add a hide button with shortcut
        self.hide_button = QtWidgets.QPushButton('Hide Window (Alt+H)')
        self.hide_button.setShortcut('Alt+H')
        self.hide_button.clicked.connect(self.hide_window)
        layout.addWidget(self.hide_button)

        self.setLayout(layout)

        # Add global shortcuts for the entire window
        QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), self, self.hide_window)

    def hide_window(self):
        """Hide the window when button is clicked"""
        self.manually_hidden = True
        self.hide()
        print("Window hidden - press hotkey to show")

    def closeEvent(self, event):
        """Override close event to hide instead of close"""
        # Hide the window instead of closing it
        event.ignore()
        self.manually_hidden = True
        self.hide()
        print("Window hidden on close - press hotkey to show")

    def apply_font_size(self):
        """Apply the configured font size to the application"""
        font = QtGui.QFont()
        font.setPointSize(self.font_size)
        self.setFont(font)
        QtWidgets.QApplication.setFont(font)
        print(f"Font size set to {self.font_size}")

    def register_hotkey(self):
        """Register global hotkey for showing the application"""
        try:
            # First try to unregister any existing hotkey
            try:
                keyboard.remove_all_hotkeys()
            except:
                pass

            # Register the new hotkey with a direct reference to toggle_window
            keyboard.add_hotkey(self.hotkey, self.toggle_window)
            print(f"Hotkey registered: {self.hotkey}")

            # Update the label
            if hasattr(self, 'hotkey_label'):
                self.hotkey_label.setText(f'Press {self.hotkey} to toggle this window, Alt+H to hide')

        except Exception as e:
            print(f"Failed to register hotkey: {str(e)}")
            QtWidgets.QMessageBox.warning(
                self, 'Hotkey Error',
                f"Failed to register hotkey: {str(e)}\n\nTry running the application as administrator."
            )

    def toggle_window(self):
        """Toggle window visibility when hotkey is pressed"""
        print("Hotkey pressed - toggling visibility")

        if self.isVisible():
            print("Window is visible - hiding")
            self.manually_hidden = True
            self.hide()
        else:
            print("Window is hidden - showing")
            self.manually_hidden = False
            self.show()
            self.raise_()  # Bring window to front
            self.activateWindow()  # Set as active window

    def show_settings(self):
        """Show settings dialog"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Settings')
        dialog.resize(360, 250)

        layout = QtWidgets.QVBoxLayout()

        # Font size settings
        font_layout = QtWidgets.QHBoxLayout()
        font_layout.addWidget(QtWidgets.QLabel('Font Size (Alt+F):'))

        font_spin = QtWidgets.QSpinBox()
        font_spin.setMinimum(8)
        font_spin.setMaximum(24)
        font_spin.setValue(self.font_size)
        font_layout.addWidget(font_spin)

        layout.addLayout(font_layout)

        # Hotkey settings
        hotkey_layout = QtWidgets.QHBoxLayout()
        hotkey_layout.addWidget(QtWidgets.QLabel('Hotkey (Alt+K):'))

        hotkey_edit = QtWidgets.QLineEdit(self.hotkey)
        hotkey_layout.addWidget(hotkey_edit)

        layout.addLayout(hotkey_layout)

        # Test hotkey button
        test_button = QtWidgets.QPushButton('Test Hotkey (Alt+T)')
        test_button.setShortcut('Alt+T')
        test_button.clicked.connect(lambda: self.test_hotkey(hotkey_edit.text()))
        layout.addWidget(test_button)

        # Preview label
        preview_label = QtWidgets.QLabel('This is a font size preview')
        preview_font = QtGui.QFont()
        preview_font.setPointSize(font_spin.value())
        preview_label.setFont(preview_font)
        layout.addWidget(preview_label)

        # Update preview when font size changes
        font_spin.valueChanged.connect(lambda size: self.update_preview(preview_label, size))

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(lambda: self.save_settings(font_spin.value(), hotkey_edit.text(), dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Set keyboard shortcuts for the dialog
        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+F"), dialog, font_spin.setFocus)
        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+K"), dialog, hotkey_edit.setFocus)
        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+S"), dialog, dialog.accept)
        QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), dialog, dialog.reject)

        dialog.setLayout(layout)
        dialog.exec_()

    def test_hotkey(self, hotkey):
        """Test if a hotkey can be registered"""
        try:
            # Try to register the hotkey temporarily
            temp_fn = lambda: print("Test hotkey pressed")
            keyboard.add_hotkey(hotkey, temp_fn)
            QtWidgets.QMessageBox.information(
                self, 'Hotkey Test',
                f"Hotkey '{hotkey}' registered successfully!\n\nPress OK to remove the test hotkey."
            )
            keyboard.remove_hotkey(hotkey)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, 'Hotkey Test Failed',
                f"Failed to register hotkey: {str(e)}\n\nTry another key combination."
            )

    def update_preview(self, label, size):
        """Update the font size preview"""
        font = QtGui.QFont()
        font.setPointSize(size)
        label.setFont(font)

    def save_settings(self, font_size, hotkey, dialog):
        """Save settings and apply changes"""
        # Update settings
        self.font_size = font_size
        old_hotkey = self.hotkey
        self.hotkey = hotkey

        # Apply font size
        self.apply_font_size()

        # Update hotkey if it changed
        if old_hotkey != self.hotkey:
            try:
                # Register the new hotkey
                self.register_hotkey()
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, 'Hotkey Error',
                    f"Failed to register new hotkey: {str(e)}\nReverting to previous hotkey."
                )
                self.hotkey = old_hotkey
                self.register_hotkey()

        # Save to config file
        self.save_config()

        dialog.accept()

    def view_issue_details(self):
        """View details of current issue"""
        if not self.current_issue:
            QtWidgets.QMessageBox.warning(self, 'No issue selected', 'No issue is currently selected.')
            return

        try:
            # Refresh issue data
            issue = self.redmine.issue.get(self.current_issue.id)

            details = f"""
Issue #{issue.id}: {issue.subject}
Status: {issue.status.name}
Priority: {issue.priority.name}
Assigned to: {issue.assigned_to.name if hasattr(issue, 'assigned_to') else 'Unassigned'}
Created: {issue.created_on}
Updated: {issue.updated_on}

Description:
{issue.description}
            """

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(f'Issue #{issue.id}')
            dialog.resize(800, 600)

            layout = QtWidgets.QVBoxLayout()

            text_edit = QtWidgets.QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(details)

            # Apply current font size to text edit
            font = text_edit.font()
            font.setPointSize(self.font_size)
            text_edit.setFont(font)

            layout.addWidget(text_edit)

            button_layout = QtWidgets.QHBoxLayout()

            web_button = QtWidgets.QPushButton('Open in browser (Alt+B)')
            web_button.setShortcut('Alt+B')
            web_button.clicked.connect(lambda: webbrowser.open(f"{self.redmine_url}/issues/{issue.id}"))
            button_layout.addWidget(web_button)

            close_button = QtWidgets.QPushButton('Close (Esc)')
            close_button.setShortcut('Esc')
            close_button.clicked.connect(dialog.accept)
            button_layout.addWidget(close_button)

            layout.addLayout(button_layout)
            dialog.setLayout(layout)

            # Additional keyboard shortcuts
            QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), dialog, dialog.accept)

            dialog.exec_()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Failed to get issue details: {str(e)}')

    def change_issue_status(self):
        """Change the status of the current issue"""
        if not self.current_issue:
            QtWidgets.QMessageBox.warning(self, 'No issue selected', 'No issue is currently selected.')
            return

        try:
            # Refresh issue data
            issue = self.redmine.issue.get(self.current_issue.id)

            # Get available statuses for the current issue
            status_list = []
            for status in self.redmine.issue_status.all():
                status_list.append(status)

            # Create dialog for status selection
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle('Change Issue Status')

            layout = QtWidgets.QVBoxLayout()

            layout.addWidget(QtWidgets.QLabel(f'Current status: {issue.status.name}'))
            layout.addWidget(QtWidgets.QLabel('Select new status (Alt+S to focus):'))

            status_combo = QtWidgets.QComboBox()
            for status in status_list:
                if status.id != issue.status.id:  # Don't show current status
                    status_combo.addItem(status.name, status.id)
            layout.addWidget(status_combo)

            button_box = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
            )
            ok_button = button_box.button(QtWidgets.QDialogButtonBox.Ok)
            cancel_button = button_box.button(QtWidgets.QDialogButtonBox.Cancel)

            ok_button.setText("Save (Alt+Enter)")
            ok_button.setShortcut("Alt+Return")
            cancel_button.setText("Cancel (Esc)")
            cancel_button.setShortcut("Esc")

            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            dialog.setLayout(layout)

            # Additional shortcuts
            QtWidgets.QShortcut(QtGui.QKeySequence("Alt+S"), dialog, status_combo.setFocus)
            QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), dialog, dialog.accept)

            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                if status_combo.currentIndex() >= 0:
                    new_status_id = status_combo.currentData()
                    self.redmine.issue.update(issue.id, status_id=new_status_id)
                    QtWidgets.QMessageBox.information(
                        self, 'Status Updated',
                        f'Issue #{issue.id} status has been updated.'
                    )
                    # Refresh the issue
                    self.current_issue = self.redmine.issue.get(issue.id)
                    self.issue_label.setText(f'Working on #{self.current_issue.id}: {self.current_issue.subject}')

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Failed to change issue status: {str(e)}')

    def choose_issue(self):
        """Choose an issue to work on from assigned issues"""
        try:
            # Get issues assigned to current user
            issues = self.redmine.issue.filter(assigned_to_id='me', status_id='open')

            if not issues:
                QtWidgets.QMessageBox.information(self, 'No issues', 'No open issues are assigned to you.')
                return

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle('Choose Issue')
            dialog.resize(1080, 600)

            layout = QtWidgets.QVBoxLayout()

            # Add search filter
            search_layout = QtWidgets.QHBoxLayout()
            search_layout.addWidget(QtWidgets.QLabel("Search (Alt+F):"))
            search_edit = QtWidgets.QLineEdit()
            search_edit.setPlaceholderText("Filter issues by ID or subject...")
            search_layout.addWidget(search_edit)
            layout.addLayout(search_layout)

            issues_table = QtWidgets.QTableWidget()
            issues_table.setColumnCount(4)
            issues_table.setHorizontalHeaderLabels(['ID', 'Subject', 'Status', 'Priority'])
            issues_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            issues_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

            # Set column widths
            issues_table.setColumnWidth(0, 50)  # ID
            issues_table.setColumnWidth(1, 700)  # Subject
            issues_table.setColumnWidth(2, 100)  # Status
            issues_table.setColumnWidth(3, 100)  # Priority

            # Apply current font size to table
            font = issues_table.font()
            font.setPointSize(self.font_size)
            issues_table.setFont(font)

            # Store all issues for filtering
            self.all_issues = []

            row = 0
            issues_table.setRowCount(len(issues))
            for issue in issues:
                issues_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(issue.id)))
                issues_table.setItem(row, 1, QtWidgets.QTableWidgetItem(issue.subject))
                issues_table.setItem(row, 2, QtWidgets.QTableWidgetItem(issue.status.name))
                issues_table.setItem(row, 3, QtWidgets.QTableWidgetItem(issue.priority.name))
                self.all_issues.append(issue)
                row += 1

            # Connect search filter
            search_edit.textChanged.connect(lambda text: self.filter_issues(text, issues_table, issues))

            layout.addWidget(issues_table)

            button_layout = QtWidgets.QHBoxLayout()

            select_button = QtWidgets.QPushButton('Select as current (Alt+S)')
            select_button.setShortcut('Alt+S')
            select_button.clicked.connect(lambda: self.select_issue(issues_table, issues, dialog))
            button_layout.addWidget(select_button)

            open_button = QtWidgets.QPushButton('Open in browser (Alt+B)')
            open_button.setShortcut('Alt+B')
            open_button.clicked.connect(lambda: self.open_issue_in_browser(issues_table, issues))
            button_layout.addWidget(open_button)

            cancel_button = QtWidgets.QPushButton('Cancel (Esc)')
            cancel_button.setShortcut('Esc')
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)

            layout.addLayout(button_layout)
            dialog.setLayout(layout)

            # Add more keyboard shortcuts
            QtWidgets.QShortcut(QtGui.QKeySequence("Alt+F"), dialog, search_edit.setFocus)
            QtWidgets.QShortcut(QtGui.QKeySequence("Return"), issues_table,
                                lambda: self.select_issue(issues_table, issues, dialog))
            QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), dialog, dialog.reject)

            # Double click to select
            issues_table.cellDoubleClicked.connect(
                lambda row, col: self.select_issue(issues_table, issues, dialog))

            dialog.exec_()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Failed to get issues: {str(e)}')

    def filter_issues(self, text, table, issues):
        """Filter issues in the table by text"""
        text = text.lower()

        # Clear the table
        table.setRowCount(0)

        # Find matching issues
        filtered_issues = []
        for issue in issues:
            if (text in str(issue.id).lower() or
                    text in issue.subject.lower() or
                    text in issue.status.name.lower() or
                    text in issue.priority.name.lower()):
                filtered_issues.append(issue)

        # Repopulate the table
        table.setRowCount(len(filtered_issues))
        for row, issue in enumerate(filtered_issues):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(issue.id)))
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(issue.subject))
            table.setItem(row, 2, QtWidgets.QTableWidgetItem(issue.status.name))
            table.setItem(row, 3, QtWidgets.QTableWidgetItem(issue.priority.name))

    def select_issue(self, table, issues, dialog):
        """Select an issue as current from the table"""
        selected_rows = table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            issue_id = int(table.item(row, 0).text())
            for issue in issues:
                if issue.id == issue_id:
                    self.current_issue = issue
                    self.issue_label.setText(f'Working on #{issue.id}: {issue.subject}')
                    self.view_button.setEnabled(True)
                    self.status_button.setEnabled(True)
                    dialog.accept()
                    return

        QtWidgets.QMessageBox.warning(self, 'No selection', 'Please select an issue from the list.')

    def open_issue_in_browser(self, table, issues):
        """Open selected issue in web browser"""
        selected_rows = table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            issue_id = int(table.item(row, 0).text())
            webbrowser.open(f"{self.redmine_url}/issues/{issue_id}")
        else:
            QtWidgets.QMessageBox.warning(self, 'No selection', 'Please select an issue from the list.')