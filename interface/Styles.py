# Styles.py

from PyQt5.QtGui import QFont


BACKGROUND = "#FFF0F6"
PANEL = "#FFF8FB"
PINK = "#DF83A9"
DARK_PINK = "#CB6892"
LIGHT_PINK = "#F9D5E4"
WHITE = "#FFFFFF"
TEXT = "#292329"
BORDER = "#E8A8C2"


def apply_styles(app):
    app.setFont(QFont("Arial", 30))

    app.setStyleSheet(f"""
        QWidget {{
            background-color: {BACKGROUND};
            color: {TEXT};
            font-family: Arial;
            font-size: 30px;
        }}

        QMainWindow {{
            background-color: {BACKGROUND};
        }}

        QPushButton {{
            background-color: {PINK};
            color: {WHITE};
            border: none;
            border-radius: 14px;
            padding: 14px 24px;
            font-size: 30px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {DARK_PINK};
        }}

        QPushButton:disabled {{
            background-color: #D9C2CC;
            color: #777777;
        }}

        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {WHITE};
            border: 2px solid {BORDER};
            border-radius: 10px;
            padding: 10px;
            min-height: 45px;
            font-size: 30px;
        }}

        QTextEdit, QPlainTextEdit {{
            background-color: {WHITE};
            border: 2px solid {BORDER};
            border-radius: 10px;
            padding: 12px;
            font-size: 30px;
        }}

        QTableWidget {{
            background-color: {WHITE};
            alternate-background-color: {PANEL};
            gridline-color: {BORDER};
            border: 2px solid {BORDER};
            border-radius: 10px;
            font-size: 30px;
        }}

        QHeaderView::section {{
            background-color: {LIGHT_PINK};
            color: {TEXT};
            padding: 10px;
            border: 1px solid {BORDER};
            font-size: 30px;
            font-weight: bold;
        }}

        QLabel {{
            font-size: 30px;
        }}

        QGroupBox {{
            background-color: {PANEL};
            border: 2px solid {BORDER};
            border-radius: 14px;
            margin-top: 20px;
            padding: 15px;
            font-size: 30px;
            font-weight: bold;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px;
        }}

        QScrollArea {{
            border: none;
            background-color: {BACKGROUND};
        }}

        QScrollBar:vertical {{
            background-color: {LIGHT_PINK};
            width: 18px;
            border-radius: 8px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {PINK};
            border-radius: 8px;
            min-height: 35px;
        }}
    """)