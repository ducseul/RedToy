import sys
import os
import ctypes
from redmine_helper_service import RedmineHelperService

def is_admin():
    try:
        if os.name == 'nt':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False

if __name__ == "__main__":
    if not is_admin():
        print("Warning: This application may need administrator privileges to register global hotkeys.")
    service = RedmineHelperService()
    if not (len(sys.argv) > 1 and sys.argv[1] == '--service'):
        service.helper.show()
    sys.exit(service.run())
