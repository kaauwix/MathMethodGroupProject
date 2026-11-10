
# MainWindow.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget,
    QSizePolicy
)
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Решение задач оптимизации")
        self.setMinimumSize(1100, 750)
        self.resize(1500, 950)

        self.navigation_buttons = []

        self.create_interface()

    # =========================
    # СОЗДАНИЕ ГЛАВНОГО ОКНА
    # =========================

    def create_interface(self):

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)

        # Боковое меню
        sidebar = self.create_sidebar()

        # Рабочая область
        content = self.create_content()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content, 1)

    # =========================
    # БОКОВОЕ МЕНЮ
    # =========================

    def create_sidebar(self):

        sidebar = QFrame()
        sidebar.setObjectName("card")
        sidebar.setFixedWidth(270)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 20)
        layout.setSpacing(12)

        title = QLabel("OPTIMIZATION")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 21px;
            font-weight: bold;
            color: #CB6892;
            padding: 10px;
        """)

        subtitle = QLabel("Математические методы")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("subtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(25)

        menu_title = QLabel("МЕНЮ")
        menu_title.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: #947783;
            padding-left: 10px;
        """)

        layout.addWidget(menu_title)

        # Кнопки разделов
        sections = [
            "Симплекс-метод",
            "Одновременный поиск",
            "Проверка оптимальности",
            "Транспортная задача"
        ]

        for index, section in enumerate(sections):

            button = QPushButton(section)
            button.setObjectName("navigationButton")
            button.setCheckable(True)
            button.setMinimumHeight(55)
            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )

            button.clicked.connect(
                lambda checked, i=index: self.change_page(i)
            )

            layout.addWidget(button)
            self.navigation_buttons.append(button)

        layout.addStretch()

        footer = QLabel("Решение задач оптимизации")
        footer.setAlignment(Qt.AlignCenter)
        footer.setObjectName("subtitle")

        layout.addWidget(footer)

        return sidebar

    # =========================
    # РАБОЧАЯ ОБЛАСТЬ
    # =========================

    def create_content(self):

        content = QWidget()

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Верхняя панель
        header = QFrame()
        header.setObjectName("card")
        header.setFixedHeight(75)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 10, 22, 10)

        self.page_title = QLabel("Симплекс-метод")
        self.page_title.setObjectName("title")

        header_layout.addWidget(self.page_title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Страницы приложения
        self.pages = QStackedWidget()

        self.pages.addWidget(
            self.create_placeholder(
                "Симплекс-метод",
                "Автоматический выбор метода решения задачи."
            )
        )

        self.pages.addWidget(
            self.create_placeholder(
                "Одновременный поиск",
                "Совместное решение прямым и двойственным симплекс-методами."
            )
        )

        self.pages.addWidget(
            self.create_placeholder(
                "Проверка оптимальности",
                "Проверка заданного пользователем плана на оптимальность."
            )
        )

        self.pages.addWidget(
            self.create_placeholder(
                "Транспортная задача",
                "Построение и оптимизация транспортного плана."
            )
        )

        layout.addWidget(self.pages, 1)

        # При запуске активен первый раздел
        self.change_page(0)

        return content

    # =========================
    # ВРЕМЕННАЯ СТРАНИЦА
    # =========================

    def create_placeholder(self, title, description):

        page = QFrame()
        page.setObjectName("card")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 23px;
            font-weight: bold;
            color: #CB6892;
        """)

        description_label = QLabel(description)
        description_label.setObjectName("subtitle")
        description_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()

        return page

    # =========================
    # ПЕРЕКЛЮЧЕНИЕ РАЗДЕЛОВ
    # =========================

    def change_page(self, index):

        self.pages.setCurrentIndex(index)

        titles = [
            "Симплекс-метод",
            "Одновременный поиск",
            "Проверка оптимальности",
            "Транспортная задача"
        ]

        self.page_title.setText(titles[index])

        for i, button in enumerate(self.navigation_buttons):
            button.setChecked(i == index)
