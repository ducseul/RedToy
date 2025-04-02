import os

# Define the folder and files to create
base_folder = '.'
dialogs_folder = os.path.join(base_folder, 'dialogs')
files_to_create = [
    os.path.join(base_folder, '__init__.py'),
    os.path.join(base_folder, 'redmine_helper_service.py'),
    os.path.join(base_folder, 'redmine_main_window.py'),
    os.path.join(dialogs_folder, '__init__.py'),
    os.path.join(dialogs_folder, 'settings_dialog.py'),
    os.path.join(dialogs_folder, 'issue_details_dialog.py'),
    os.path.join(dialogs_folder, 'change_status_dialog.py'),
    os.path.join(dialogs_folder, 'choose_issue_dialog.py'),
]

# Create directories and empty files
for file_path in files_to_create:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        f.write('')  # Initialize empty files

files_to_create
