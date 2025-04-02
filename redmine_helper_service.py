from PyQt5 import QtCore, QtWidgets
import sys
from redmine_main_window import RedmineMainWindow

class RedmineHelperService:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.helper = RedmineMainWindow()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.process_events)
        self.timer.start(500)

    def process_events(self):
        QtWidgets.QApplication.processEvents()

    def run(self):
        return self.app.exec_()
