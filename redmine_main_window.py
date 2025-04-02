import os
import configparser
import webbrowser

from PyQt5 import QtWidgets, QtCore, QtGui
from redminelib import Redmine
from redminelib.exceptions import AuthError
import keyboard

from dialogs.settings_dialog import SettingsDialog
from dialogs.issue_details_dialog import IssueDetailsDialog
from dialogs.change_status_dialog import ChangeStatusDialog
from dialogs.choose_issue_dialog import ChooseIssueDialog

class RedmineMainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.cfg')
        self.current_issue = None
        self.redmine = None
        self.hotkey = None
        self.font_size = 10
        self.load_config()
        self.init_redmine()
        self.init_ui()
        self.apply_font_size()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        QtCore.QTimer.singleShot(1000, self.register_hotkey)
        self.manually_hidden = False

    def load_config(self):
        config = configparser.ConfigParser()
        self.redmine_url = "https://redmine.example.com"
        self.api_key = ""
        self.hotkey = "ctrl+shift+r"
        self.font_size = 10
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            if 'Redmine' in config:
                self.redmine_url = config['Redmine'].get('url', self.redmine_url)
                self.api_key = config['Redmine'].get('api_key', self.api_key)
            if 'Settings' in config:
                self.hotkey = config['Settings'].get('hotkey', self.hotkey)
                self.font_size = config['Settings'].getint('font_size', self.font_size)
        else:
            config['Redmine'] = {'url': self.redmine_url, 'api_key': self.api_key}
            config['Settings'] = {'hotkey': self.hotkey, 'font_size': str(self.font_size)}
            with open(self.config_file, 'w') as f:
                config.write(f)
            print(f"Default configuration file created at {self.config_file}")

    def save_config(self):
        config = configparser.ConfigParser()
        config['Redmine'] = {'url': self.redmine_url, 'api_key': self.api_key}
        config['Settings'] = {'hotkey': self.hotkey, 'font_size': str(self.font_size)}
        with open(self.config_file, 'w') as f:
            config.write(f)

    def init_redmine(self):
        try:
            if not self.api_key:
                print("API key not set.")
                return None
            self.redmine = Redmine(self.redmine_url, key=self.api_key)
            self.current_user = self.redmine.user.get('current')
            print(f"Connected to Redmine as {self.current_user.firstname} {self.current_user.lastname}")
            return True
        except AuthError:
            print("Authentication failed.")
            return False
        except Exception as e:
            print(f"Failed to connect: {str(e)}")
            return False

    def init_ui(self):
        self.setWindowTitle('Redmine Helper')
        self.resize(650, 350)
        self.setMinimumSize(650, 350)
        layout = QtWidgets.QVBoxLayout()

        self.view_button = QtWidgets.QPushButton('1. View current issue details (1)')
        self.view_button.setShortcut('1')
        self.view_button.clicked.connect(self.view_issue_details)
        self.view_button.setEnabled(False)
        layout.addWidget(self.view_button)

        self.status_button = QtWidgets.QPushButton('2. Change issue status (2)')
        self.status_button.setShortcut('2')
        self.status_button.clicked.connect(self.change_issue_status)
        self.status_button.setEnabled(False)
        layout.addWidget(self.status_button)

        self.choose_button = QtWidgets.QPushButton('3. Choose issue to work on (3)')
        self.choose_button.setShortcut('3')
        self.choose_button.clicked.connect(self.choose_issue)
        layout.addWidget(self.choose_button)

        self.settings_button = QtWidgets.QPushButton('4. Settings (4)')
        self.settings_button.setShortcut('4')
        self.settings_button.clicked.connect(self.show_settings)
        layout.addWidget(self.settings_button)

        self.status_label = QtWidgets.QLabel(f'Connected as {self.current_user.firstname} {self.current_user.lastname}' if self.redmine else 'Not connected')
        layout.addWidget(self.status_label)

        self.issue_label = QtWidgets.QLabel('No issue selected')
        layout.addWidget(self.issue_label)

        self.hotkey_label = QtWidgets.QLabel(f'Press {self.hotkey} to toggle this window, Alt+H to hide')
        layout.addWidget(self.hotkey_label)

        self.hide_button = QtWidgets.QPushButton('Hide Window (Alt+H)')
        self.hide_button.setShortcut('Alt+H')
        self.hide_button.clicked.connect(self.hide_window)
        layout.addWidget(self.hide_button)

        QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), self, self.hide_window)

        self.setLayout(layout)

    def hide_window(self):
        self.manually_hidden = True
        self.hide()

    def closeEvent(self, event):
        event.ignore()
        self.hide_window()

    def apply_font_size(self):
        font = QtGui.QFont()
        font.setPointSize(self.font_size)
        self.setFont(font)
        QtWidgets.QApplication.setFont(font)


    def register_hotkey(self):
        """Register global hotkey for showing the application"""
        try:
            # keyboard.remove_all_hotkeys()
            # Register the new hotkey with a direct reference to toggle_window
            keyboard.add_hotkey(self.hotkey, self.toggle_window)
            print(f"Hotkey registered: {self.hotkey}")

            # Update the label
            if hasattr(self, 'hotkey_label'):
                self.hotkey_label.setText(f'Press {self.hotkey} to toggle this window, Alt+H to hide')

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, 'Hotkey Error',
                f"Failed to register hotkey: {str(e)}"
            )


    def toggle_window(self):
        if self.isVisible():
            self.hide_window()
        else:
            self.manually_hidden = False
            self.show()
            self.raise_()
            self.activateWindow()

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.font_size = dialog.font_size
            self.hotkey = dialog.hotkey
            self.apply_font_size()
            self.register_hotkey()
            self.save_config()
            self.hotkey_label.setText(f'Press {self.hotkey} to toggle this window, Alt+H to hide')

    def view_issue_details(self):
        if not self.current_issue:
            QtWidgets.QMessageBox.warning(self, 'No issue', 'No issue is currently selected.')
            return
        dialog = IssueDetailsDialog(self, self.redmine, self.current_issue, self.font_size, self.redmine_url)
        dialog.exec_()

    def change_issue_status(self):
        if not self.current_issue:
            QtWidgets.QMessageBox.warning(self, 'No issue', 'No issue is currently selected.')
            return
        dialog = ChangeStatusDialog(self, self.redmine, self.current_issue, self.font_size)
        if dialog.exec_():
            self.current_issue = dialog.updated_issue
            self.issue_label.setText(f'Working on #{self.current_issue.id}: {self.current_issue.subject}')

    def choose_issue(self):
        dialog = ChooseIssueDialog(self, self.redmine, self.font_size, self.redmine_url)
        if dialog.exec_():
            self.current_issue = dialog.selected_issue
            self.issue_label.setText(f'Working on #{self.current_issue.id}: {self.current_issue.subject}')
            self.view_button.setEnabled(True)
            self.status_button.setEnabled(True)
