from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel
)

from PyQt5.QtCore import Qt

from SimplexPage import SimplexPage
from TransportPage import TransportPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Решение задач оптимизации")
        self.resize(1600, 1000)
        self.setMinimumSize(1100, 750)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)

        title = QLabel("Решение задач оптимизации")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #CB6892;
            padding: 10px;
        """)

        main_layout.addWidget(title)

        navigation_layout = QHBoxLayout()
        navigation_layout.setSpacing(20)

        self.simplex_button = QPushButton("Симплекс-метод")
        self.transport_button = QPushButton("Транспортная задача")

        self.simplex_button.clicked.connect(
            lambda: self.change_page(0)
        )

        self.transport_button.clicked.connect(
            lambda: self.change_page(1)
        )

        navigation_layout.addWidget(self.simplex_button)
        navigation_layout.addWidget(self.transport_button)

        main_layout.addLayout(navigation_layout)

        self.pages = QStackedWidget()

        self.simplex_page = SimplexPage()
        self.transport_page = TransportPage()

        self.pages.addWidget(self.simplex_page)
        self.pages.addWidget(self.transport_page)

        main_layout.addWidget(self.pages)

        self.change_page(0)

    def change_page(self, index):
        self.pages.setCurrentIndex(index)

        if index == 0:
            self.simplex_button.setStyleSheet(
                "background-color: #CB6892;"
            )
            self.transport_button.setStyleSheet(
                "background-color: #DF83A9;"
            )
        else:
            self.simplex_button.setStyleSheet(
                "background-color: #DF83A9;"
            )
            self.transport_button.setStyleSheet(
                "background-color: #CB6892;"
            )