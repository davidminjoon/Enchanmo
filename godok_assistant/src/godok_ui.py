import sys

from PyQt5.QtWidgets import QApplication, QMainWindow


class GodokAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GodokAssistant()


