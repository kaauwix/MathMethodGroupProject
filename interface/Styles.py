
# Styles.py

# =========================
# ЦВЕТОВАЯ ПАЛИТРА
# =========================

BACKGROUND = "#FFF0F6"       # Основной фон
CARD_BACKGROUND = "#FFFFFF"  # Фон карточек
INPUT_BACKGROUND = "#FFF8FB" # Поля ввода

PINK_LIGHT = "#F4D6E3"       # Светло-розовый
PINK_MIDDLE = "#DF83A9"      # Основной розовый
PINK_DARK = "#CB6892"        # Насыщенный розовый

TEXT_DARK = "#49333D"        # Основной текст
TEXT_SECONDARY = "#947783"   # Второстепенный текст

BORDER_COLOR = "#EBC6D7"     # Границы
TABLE_HEADER = "#F4D6E3"     # Заголовки таблиц
TABLE_HIGHLIGHT = "#F8D5E4"  # Выделенные ячейки

SUCCESS_COLOR = "#DCEFE2"
ERROR_COLOR = "#F9DCDD"


# =========================
# ОСНОВНОЕ ОФОРМЛЕНИЕ
# =========================

APP_STYLE = f"""

QWidget {{
    background-color: {BACKGROUND};
    color: {TEXT_DARK};
    font-family: "Arial";
    font-size: 24px;
}}


QMainWindow {{
    background-color: {BACKGROUND};
}}


QLabel {{
    background: transparent;
    color: {TEXT_DARK};
}}


QLabel#title {{
    font-size: 37px;
    font-weight: bold;
    color: {PINK_DARK};
}}


QLabel#subtitle {{
    font-size: 23px;
    color: {TEXT_SECONDARY};
}}


QFrame#card {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 14px;
}}


QGroupBox {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    margin-top: 14px;
    padding: 14px;
    font-weight: bold;
    color: {PINK_DARK};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}}


QPushButton {{
    background-color: {PINK_MIDDLE};
    color: white;
    border: none;
    border-radius: 9px;
    padding: 10px 18px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {PINK_DARK};
}}

QPushButton:pressed {{
    background-color: #B85480;
}}

QPushButton:disabled {{
    background-color: #E8CCD9;
    color: #A58D98;
}}


QPushButton#navigationButton {{
    background-color: {PINK_LIGHT};
    color: {TEXT_DARK};
    text-align: left;
    padding: 14px;
    font-size: 24px;
}}

QPushButton#navigationButton:hover {{
    background-color: #F0C0D5;
}}

QPushButton#navigationButton:checked {{
    background-color: {PINK_DARK};
    color: white;
}}


QPushButton#solveButton {{
    background-color: {PINK_DARK};
    color: white;
    font-size: 25px;
    padding: 13px;
}}


QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {INPUT_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 7px;
    padding: 8px;
    color: {TEXT_DARK};
    selection-background-color: {PINK_MIDDLE};
}}

QLineEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus {{
    border: 2px solid {PINK_MIDDLE};
}}


QComboBox QAbstractItemView {{
    background-color: {CARD_BACKGROUND};
    selection-background-color: {PINK_LIGHT};
    selection-color: {TEXT_DARK};
    border: 1px solid {BORDER_COLOR};
}}


QTableWidget {{
    background-color: {CARD_BACKGROUND};
    alternate-background-color: {INPUT_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    gridline-color: {BORDER_COLOR};
    color: {TEXT_DARK};
    selection-background-color: {PINK_LIGHT};
    selection-color: {TEXT_DARK};
}}

QHeaderView::section {{
    background-color: {TABLE_HEADER};
    color: {PINK_DARK};
    border: none;
    border-right: 1px solid {BORDER_COLOR};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 9px;
    font-weight: bold;
}}

QTableWidget::item {{
    padding: 7px;
}}

QTableWidget::item:selected {{
    background-color: {TABLE_HIGHLIGHT};
}}


QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: {BACKGROUND};
    width: 10px;
    margin: 2px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background-color: {PINK_MIDDLE};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {PINK_DARK};
}}

QScrollBar:horizontal {{
    background-color: {BACKGROUND};
    height: 10px;
    margin: 2px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background-color: {PINK_MIDDLE};
    border-radius: 5px;
    min-width: 30px;
}}

QTextEdit, QPlainTextEdit {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px;
    color: {TEXT_DARK};
}}

"""


# =========================
# ПРИМЕНЕНИЕ СТИЛЕЙ
# =========================

def apply_styles(app):
    app.setStyleSheet(APP_STYLE)
