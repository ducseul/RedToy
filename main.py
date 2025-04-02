import sys
from redmine_helper import RedmineHelperService

if __name__ == "__main__":
    # Check if the script should run as service or show UI directly
    service_mode = len(sys.argv) > 1 and sys.argv[1] == '--service'

    service = RedmineHelperService()
    if not service_mode:
        service.helper.show()
    sys.exit(service.run())