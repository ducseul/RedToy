from PyQt5 import QtWidgets, QtGui, QtCore
import webbrowser
import os
import requests
import tempfile
import subprocess


class IssueDetailsDialog(QtWidgets.QDialog):
    def __init__(self, parent, redmine, issue, font_size, redmine_url, api_key):
        super().__init__(parent)
        self.setWindowTitle(f'Issue #{issue.id}')
        self.resize(1080, 600)
        self.redmine = redmine
        self.issue_id = issue.id
        self.redmine_url = redmine_url
        self.api_key = api_key
        self.font_size = font_size
        self.temp_files = []  # Track temporary files for cleanup

        # Get the full issue details
        self.issue = redmine.issue.get(issue.id, include=['attachments', 'journals', 'status'])

        # Try to get all statuses to show names instead of IDs
        self.statuses = {}
        try:
            # Try the issue_status endpoint instead of status
            for status in redmine.issue_status.all():
                self.statuses[status.id] = status.name
        except Exception as e:
            print(f"Failed to retrieve statuses: {e}")
            # If we can't get statuses, try to at least get the current issue's status
            if hasattr(self.issue, 'status'):
                self.statuses[self.issue.status.id] = self.issue.status.name

        self.setup_ui()

    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout()

        # Create tab widget for organization
        tab_widget = QtWidgets.QTabWidget()

        # Issue details tab
        details_tab = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout()
        details_tab.setLayout(details_layout)

        # Issue details
        details = f"""
Issue #{self.issue.id}: {self.issue.subject}
Status: {self.issue.status.name}
Priority: {self.issue.priority.name}
Assigned to: {getattr(self.issue, 'assigned_to', 'Unassigned')}
Created: {self.issue.created_on}
Updated: {self.issue.updated_on}

Description:
{self.issue.description}
        """

        text_edit = QtWidgets.QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(details)
        font = text_edit.font()
        font.setPointSize(self.font_size)
        text_edit.setFont(font)
        details_layout.addWidget(text_edit)

        # Notes/journals tab
        notes_tab = QtWidgets.QWidget()
        notes_layout = QtWidgets.QVBoxLayout()
        notes_tab.setLayout(notes_layout)

        notes_scroll = QtWidgets.QScrollArea()
        notes_scroll.setWidgetResizable(True)
        notes_widget = QtWidgets.QWidget()
        notes_content_layout = QtWidgets.QVBoxLayout()
        notes_widget.setLayout(notes_content_layout)

        # Add each journal/note
        if hasattr(self.issue, 'journals'):
            for journal in reversed(self.issue.journals):
                note_frame = QtWidgets.QFrame()
                note_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
                note_frame.setFrameShadow(QtWidgets.QFrame.Raised)
                note_layout = QtWidgets.QVBoxLayout()

                # Header with author, date, and status change if present
                author = getattr(journal, 'user', 'Unknown')
                header_text = f"<b>{author}</b> - {journal.created_on}"

                # Add status change info directly in the header if present
                if hasattr(journal, 'details') and journal.details:
                    for detail in journal.details:
                        if detail.get('name') == 'status_id':
                            try:
                                # Convert string status IDs to integers before lookup
                                old_status_id = int(detail.get('old_value', '0'))
                                new_status_id = int(detail.get('new_value', '0'))

                                # Use the converted integers to look up status names
                                old_status = self.statuses.get(old_status_id, f"Status #{old_status_id}")
                                new_status = self.statuses.get(new_status_id, f"Status #{new_status_id}")

                                header_text += f" - Status: {old_status} → {new_status}"
                            except (ValueError, TypeError):
                                # Fallback if conversion fails
                                header_text += f" - Status: {detail.get('old_value', 'Unknown')} → {detail.get('new_value', 'Unknown')}"
                            break

                header = QtWidgets.QLabel(header_text)
                note_layout.addWidget(header)

                # Note content as italic text without scrollbars
                if hasattr(journal, 'notes') and journal.notes:
                    notes_label = QtWidgets.QLabel()

                    # Format the text with italics and preserve line breaks
                    formatted_notes = journal.notes.replace('\n', '<br>')
                    notes_label.setText(f"<i>{formatted_notes}</i>")
                    notes_label.setWordWrap(True)
                    notes_label.setTextFormat(QtCore.Qt.RichText)

                    # Set the font size
                    font = notes_label.font()
                    font.setPointSize(self.font_size)
                    notes_label.setFont(font)

                    note_layout.addWidget(notes_label)

                # Display other changes (not status which is already in the header)
                changes_added = False
                if hasattr(journal, 'details') and journal.details:
                    changes_layout = QtWidgets.QVBoxLayout()

                    for detail in journal.details:
                        if detail.get('name') != 'status_id':  # Skip status changes as they're in the header
                            if not changes_added:
                                changes = QtWidgets.QLabel("<b>Changes:</b>")
                                changes_layout.addWidget(changes)
                                changes_added = True

                            change_text = f"• {detail.get('name', 'Unknown')}: {detail.get('old_value', '')} → {detail.get('new_value', '')}"
                            change = QtWidgets.QLabel(change_text)
                            changes_layout.addWidget(change)

                    if changes_added:
                        note_layout.addLayout(changes_layout)

                note_frame.setLayout(note_layout)
                notes_content_layout.addWidget(note_frame)
                notes_content_layout.addSpacing(10)
        else:
            no_notes = QtWidgets.QLabel("No notes available for this issue.")
            notes_content_layout.addWidget(no_notes)

        notes_content_layout.addStretch()
        notes_scroll.setWidget(notes_widget)
        notes_layout.addWidget(notes_scroll)

        # Attachments tab
        attachments_tab = QtWidgets.QWidget()
        attachments_layout = QtWidgets.QVBoxLayout()
        attachments_tab.setLayout(attachments_layout)

        if hasattr(self.issue, 'attachments') and self.issue.attachments:
            attachments_table = QtWidgets.QTableWidget()
            attachments_table.setColumnCount(5)
            attachments_table.setHorizontalHeaderLabels(["Filename", "Size", "Author", "Created", "Actions"])
            attachments_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            attachments_table.setRowCount(len(self.issue.attachments))

            row = 0
            for attachment in self.issue.attachments:
                # Filename
                attachments_table.setItem(row, 0, QtWidgets.QTableWidgetItem(attachment.filename))

                # Size (format nicely)
                size = self.format_size(attachment.filesize)
                attachments_table.setItem(row, 1, QtWidgets.QTableWidgetItem(size))

                # Author
                author = getattr(attachment, 'author', 'Unknown')
                attachments_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(author)))

                # Created date
                attachments_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(attachment.created_on)))

                # Actions button
                actions_widget = QtWidgets.QWidget()
                actions_layout = QtWidgets.QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)

                view_button = QtWidgets.QPushButton("View")
                view_button.clicked.connect(lambda checked, a=attachment: self.view_attachment(a))

                save_button = QtWidgets.QPushButton("Save")
                save_button.clicked.connect(lambda checked, a=attachment: self.save_attachment(a))

                actions_layout.addWidget(view_button)
                actions_layout.addWidget(save_button)

                attachments_table.setCellWidget(row, 4, actions_widget)
                row += 1

            attachments_layout.addWidget(attachments_table)
        else:
            no_attachments = QtWidgets.QLabel("No attachments available for this issue.")
            attachments_layout.addWidget(no_attachments)

        # Add tabs to widget
        tab_widget.addTab(details_tab, "Details")
        tab_widget.addTab(notes_tab, "Notes")
        tab_widget.addTab(attachments_tab, "Attachments")

        main_layout.addWidget(tab_widget)

        # Bottom buttons
        button_layout = QtWidgets.QHBoxLayout()
        web_button = QtWidgets.QPushButton('Open in browser (Alt+B)')
        web_button.setShortcut('Alt+B')
        web_button.clicked.connect(lambda: webbrowser.open(f"{self.redmine_url}/issues/{self.issue_id}"))

        close_button = QtWidgets.QPushButton('Close (Esc)')
        close_button.setShortcut('Esc')
        close_button.clicked.connect(self.accept)

        button_layout.addWidget(web_button)
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)

        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.accept)

        self.setLayout(main_layout)

    def format_size(self, size_bytes):
        # Format file size in human-readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def view_attachment(self, attachment):
        # Download and open the attachment
        try:
            # Create a direct URL to the attachment
            url = f"{self.redmine_url}/attachments/download/{attachment.id}/{attachment.filename}"

            # Setup headers for API key authentication
            headers = {}

            # Add API key to headers if available
            if self.api_key:
                headers['X-Redmine-API-Key'] = self.api_key

            # Download the attachment using requests with API key
            response = requests.get(
                url,
                headers=headers,
                stream=True,
                verify=True  # Set to False if you have SSL certificate issues
            )

            if response.status_code == 200:
                # Create temp file with correct extension
                suffix = os.path.splitext(attachment.filename)[1]
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                self.temp_files.append(temp_file.name)  # Track for cleanup

                # Write content to temp file
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.close()

                # Open with default application
                if os.name == 'nt':  # Windows
                    os.startfile(temp_file.name)
                elif os.name == 'posix':  # Linux/Mac
                    subprocess.call(('xdg-open', temp_file.name))
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Download Failed",
                    f"Failed to download attachment: HTTP {response.status_code}\n{response.text[:200]}"
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error viewing attachment: {str(e)}")

    # Also update the save_attachment method similarly:
    def save_attachment(self, attachment):
        try:
            # Show save dialog
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Attachment", attachment.filename, "All Files (*.*)"
            )

            if file_path:
                # Create a direct URL to the attachment
                url = f"{self.redmine_url}/attachments/download/{attachment.id}/{attachment.filename}"

                # Setup headers for API key authentication
                headers = {}

                # Try to get API key from redmine object
                if self.api_key:
                    headers['X-Redmine-API-Key'] = self.api_key

                # Download the attachment
                response = requests.get(
                    url,
                    headers=headers,
                    stream=True,
                    verify=True  # Set to False if you have SSL certificate issues
                )

                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    QtWidgets.QMessageBox.information(self, "Success", "Attachment saved successfully!")
                else:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Download Failed",
                        f"Failed to download attachment: HTTP {response.status_code}\n{response.text[:200]}"
                    )
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error saving attachment: {str(e)}")

    def closeEvent(self, event):
        # Clean up any temporary files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        event.accept()