import sys
import os
import ctypes
from redmine_helper import RedmineHelperService


def is_admin():
    """Check if the script is running with admin privileges"""
    try:
        # For Windows
        if os.name == 'nt':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        # For Linux/Mac
        else:
            return os.geteuid() == 0
    except:
        return False


if __name__ == "__main__":
    # Check for admin/root privileges
    if not is_admin():
        print("Warning: This application may need administrator privileges to register global hotkeys.")
        print("Consider rerunning the application as administrator.")

    # Check if the script should run as service or show UI directly
    service_mode = len(sys.argv) > 1 and sys.argv[1] == '--service'

    try:
        service = RedmineHelperService()
        if not service_mode:
            service.helper.show()
        sys.exit(service.run())
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        input("Press Enter to exit...")  # Keep console window open to see the error
        sys.exit(1)