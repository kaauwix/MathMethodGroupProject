from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


class StepsViewer(QScrollArea):
    """Прокручиваемая область для отображения всех шагов решения."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(12)
        self.setWidget(self.container)

    # ------------------------------------------------------------------
    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_message(self, text):
        self.clear()
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #947783; font-size: 22px; padding: 8px;")
        self.layout.addWidget(lbl)
        self.layout.addStretch()

    def show_steps(self, steps):
        self.clear()
        if not steps:
            self.layout.addWidget(QLabel("<i>Шаги решения отсутствуют.</i>"))
            self.layout.addStretch()
            return

        for step in steps:
            if step["type"] == "text":
                self._add_text_step(step)
            elif step["type"] == "table":
                self._add_table_step(step)

        self.layout.addStretch()

    # ------------------------------------------------------------------
    def _add_text_step(self, step):
        box = QFrame()
        box.setObjectName("card")
        v = QVBoxLayout(box)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        title = QLabel(f"<b>{step['title']}</b>")
        title.setStyleSheet("color: #CB6892; font-size: 26px;")
        title.setWordWrap(True)
        v.addWidget(title)

        desc = QLabel(step.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #49333D; font-size: 22px;")
        v.addWidget(desc)

        data = step.get("data")
        if data:
            extra = QLabel(self._format_data(data))
            extra.setWordWrap(True)
            extra.setStyleSheet("color: #947783; font-size: 20px;")
            v.addWidget(extra)

        self.layout.addWidget(box)

    # ------------------------------------------------------------------
    def _add_table_step(self, step):
        box = QFrame()
        box.setObjectName("card")
        v = QVBoxLayout(box)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(12)

        title = QLabel(f"<b>{step['title']}</b>")
        title.setStyleSheet("color: #CB6892; font-size: 26px;")
        title.setWordWrap(True)
        v.addWidget(title)

        table = self._build_table(step)
        
        # Оборачиваем таблицу в HBox, чтобы она прижималась влево и не растягивалась
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(table)
        h_layout.addStretch() 
        
        v.addLayout(h_layout)

        pivot = step.get("pivot")
        if pivot:
            pivot_text = (
                f"Ведущий элемент: строка {pivot['row'] + 1}, "
                f"столбец {pivot['column'] + 1} "
                f"(входит <b>{pivot.get('entering_variable', '?')}</b>, "
                f"выходит <b>{pivot.get('leaving_variable', '?')}</b>)"
            )
            lbl = QLabel(pivot_text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #947783; font-size: 20px;")
            v.addWidget(lbl)

        self.layout.addWidget(box)

    # ------------------------------------------------------------------
    def _build_table(self, step):
        tableau = step["tableau"]
        names = step["variable_names"]
        basis = step["basis"]
        cb = step["cb"]
        deltas = step["deltas"]
        c_full = step.get("c", [0.0] * len(names))
        pivot = step.get("pivot")

        show_idx = [j for j, name in enumerate(names) if name.startswith("x")]
        n_show = len(show_idx)

        rows = len(tableau)
        total_rows = rows + 2
        cols = 2 + n_show + 1

        # Вычисляем текущее значение целевой функции Z = sum(C_b * b)
        z_value = sum(cb[i] * tableau[i][-1] for i in range(rows))

        table = QTableWidget(total_rows, cols)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(False)
        
        # --- Шрифт: крупный, 28pt ---
        font = QFont("Arial", 28)
        font.setBold(True)
        table.setFont(font)
        table.setStyleSheet("QTableWidget { color: #49333D; border: none; }")

        # --- Гарантированно убираем скроллы ---
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        table.verticalHeader().setVisible(False)

        # --- Заголовки ---
        headers = ["C_b", "Базис"] + [names[j] for j in show_idx] + ["b"]
        table.setHorizontalHeaderLabels(headers)
        
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #F4D6E3;
                color: #CB6892;
                font-weight: bold;
                font-size: 28px;
                padding: 12px;
                border: 1px solid #EBC6D7;
            }
        """)

        # --- Строки базиса ---
        for i in range(rows):
            item = QTableWidgetItem(self._fmt(cb[i]))
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor("#F4D6E3"))
            table.setItem(i, 0, item)

            item = QTableWidgetItem(names[basis[i]])
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor("#F4D6E3"))
            table.setItem(i, 1, item)

            for c_pos, j in enumerate(show_idx):
                item = QTableWidgetItem(self._fmt(tableau[i][j]))
                item.setTextAlignment(Qt.AlignCenter)
                if pivot and j == pivot["column"]:
                    item.setBackground(QColor("#F8D5E4"))
                table.setItem(i, 2 + c_pos, item)

            item = QTableWidgetItem(self._fmt(tableau[i][-1]))
            item.setTextAlignment(Qt.AlignCenter)
            if pivot and i == pivot["row"]:
                item.setBackground(QColor("#F8D5E4"))
            table.setItem(i, 2 + n_show, item)

        # --- Строка c_j ---
        r = rows
        item = QTableWidgetItem("c_j")
        item.setTextAlignment(Qt.AlignCenter)
        item.setBackground(QColor("#EBC6D7"))
        item.setForeground(QColor("#CB6892"))
        table.setItem(r, 1, item)
        
        item_empty_c = QTableWidgetItem("")
        item_empty_c.setBackground(QColor("#EBC6D7"))
        table.setItem(r, 0, item_empty_c)

        for c_pos, j in enumerate(show_idx):
            item = QTableWidgetItem(self._fmt(c_full[j]))
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor("#EBC6D7"))
            table.setItem(r, 2 + c_pos, item)
            
        # Пустая ячейка под b в строке c_j
        item_b_c = QTableWidgetItem("")
        item_b_c.setBackground(QColor("#EBC6D7"))
        table.setItem(r, 2 + n_show, item_b_c)

        # --- Строка Δ_j ---
        r = rows + 1
        item = QTableWidgetItem("Δ_j")
        item.setTextAlignment(Qt.AlignCenter)
        item.setBackground(QColor("#EBC6D7"))
        item.setForeground(QColor("#CB6892"))
        table.setItem(r, 1, item)
        
        item_empty_d = QTableWidgetItem("")
        item_empty_d.setBackground(QColor("#EBC6D7"))
        table.setItem(r, 0, item_empty_d)

        for c_pos, j in enumerate(show_idx):
            item = QTableWidgetItem(self._fmt(deltas[j]))
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor("#EBC6D7"))
            table.setItem(r, 2 + c_pos, item)

        # --- ВЫВОДИМ f = ... ПОД СТОЛБЦОМ b ---
        item_z = QTableWidgetItem(f"f = {self._fmt(z_value)}")
        item_z.setTextAlignment(Qt.AlignCenter)
        item_z.setBackground(QColor("#EBC6D7"))
        item_z.setForeground(QColor("#49333D"))
        table.setItem(r, 2 + n_show, item_z)

        # --- Размеры: увеличены под 28pt ---
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        
        for c in range(cols):
            table.setColumnWidth(c, 150)        # было 105
        for r in range(total_rows):
            table.setRowHeight(r, 78)           # было 52

        # --- Вычисляем итоговый размер и задаем его ---
        header_h = table.horizontalHeader().height()
        total_h = sum(table.rowHeight(i) for i in range(total_rows))
        total_w = sum(table.columnWidth(c) for c in range(cols))

        table.setFixedHeight(header_h + total_h + 2)
        table.setFixedWidth(total_w + 2)

        return table

    # ------------------------------------------------------------------
    @staticmethod
    def _fmt(v):
        if abs(v) < 1e-9:
            return "0"
        return f"{v:.4g}"

    @staticmethod
    def _format_data(data):
        if isinstance(data, dict):
            parts = []
            for k, v in data.items():
                if isinstance(v, (list, tuple)):
                    inner = ", ".join(
                        StepsViewer._fmt(x) if isinstance(x, (int, float)) else str(x)
                        for x in v
                    )
                    parts.append(f"{k}: [{inner}]")
                elif isinstance(v, (int, float)):
                    parts.append(f"{k}: {StepsViewer._fmt(v)}")
                else:
                    parts.append(f"{k}: {v}")
            return " | ".join(parts)
        return str(data)