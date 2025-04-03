from PyQt5 import QtWidgets, QtGui, QtCore
import webbrowser
import os
import requests
import tempfile
import subprocess


class IssueDetailsDialog(QtWidgets.QDialog):
    def __init__(self, parent, redmine, issue, font_size, redmine_url, api_key):
        super().__init__(parent, QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
        self.setWindowTitle(f'Issue #{issue.id}')
        self.resize(1080, 620)
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
        info_layout = QtWidgets.QGridLayout()

        def make_labeled_value(label, value, bold=True, font_size_offset=0):
            text = f"<b>{label}</b> {value}" if bold else f"{label} {value}"
            lbl = QtWidgets.QLabel(text)
            font = lbl.font()
            font.setPointSize(self.font_size + font_size_offset)
            lbl.setFont(font)
            return lbl

        # Custom clickable QLabel
        class ClickableLabel(QtWidgets.QLabel):
            clicked = QtCore.pyqtSignal()

            def mouseReleaseEvent(self, event):
                if event.button() == QtCore.Qt.LeftButton:
                    self.clicked.emit()

        # Row 0: Issue title (clickable)
        title_label = ClickableLabel(f"<b>Issue #{self.issue.id}:</b> {self.issue.subject}")
        title_label.setTextFormat(QtCore.Qt.RichText)
        font = title_label.font()
        font.setPointSize(self.font_size)
        title_label.setFont(font)

        title_wrapper = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout(title_wrapper)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.addWidget(title_label)

        # Row 1: Status + Priority
        self.row1_widget = QtWidgets.QWidget()
        row1_layout = QtWidgets.QHBoxLayout(self.row1_widget)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.addWidget(make_labeled_value("Status:", self.issue.status.name, font_size_offset=-1))
        row1_layout.addWidget(make_labeled_value("Priority:", self.issue.priority.name, font_size_offset=-1))
        self.row1_widget.setVisible(False)

        # Row 2: Created + Updated
        self.row2_widget = QtWidgets.QWidget()
        row2_layout = QtWidgets.QHBoxLayout(self.row2_widget)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.addWidget(make_labeled_value("Created:", self.issue.created_on, font_size_offset=-1))
        row2_layout.addWidget(make_labeled_value("Updated:", self.issue.updated_on, font_size_offset=-1))
        self.row2_widget.setVisible(False)

        # Toggle rows on click
        def toggle_rows():
            visible = not self.row1_widget.isVisible()
            self.row1_widget.setVisible(visible)
            self.row2_widget.setVisible(visible)

        title_label.clicked.connect(toggle_rows)

        info_layout.addWidget(title_wrapper, 0, 0, 1, 2)
        info_layout.addWidget(self.row1_widget, 1, 0, 1, 2)
        info_layout.addWidget(self.row2_widget, 2, 0, 1, 2)

        # Row 3: Description
        desc_text = QtWidgets.QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setPlainText(self.issue.description)
        font = desc_text.font()
        font.setPointSize(self.font_size)
        desc_text.setFont(font)

        details_layout.addLayout(info_layout)
        details_layout.addWidget(desc_text)

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
                                old_status = self.statuses.get(int(detail.get('old_value', '0')),
                                                               f"Status #{detail.get('old_value')}")
                                new_status = self.statuses.get(int(detail.get('new_value', '0')),
                                                               f"Status #{detail.get('new_value')}")
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
                if hasattr(journal, 'details') and journal.details:
                    changes_added = False
                    changes_layout = QtWidgets.QVBoxLayout()

                    for detail in journal.details:
                        if detail.get('name') != 'status_id':
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

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

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