from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


class StepsViewer(QScrollArea):
    """Прокручиваемая область для отображения всех шагов решения."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

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
        lbl.setStyleSheet("color: #947783; font-size: 15px; padding: 8px;")
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
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(6)

        title = QLabel(f"<b>{step['title']}</b>")
        title.setStyleSheet("color: #CB6892; font-size: 17px;")
        title.setWordWrap(True)
        v.addWidget(title)

        desc = QLabel(step.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #49333D; font-size: 15px;")
        v.addWidget(desc)

        data = step.get("data")
        if data:
            extra = QLabel(self._format_data(data))
            extra.setWordWrap(True)
            extra.setStyleSheet("color: #947783; font-size: 14px;")
            v.addWidget(extra)

        self.layout.addWidget(box)

    # ------------------------------------------------------------------
    def _add_table_step(self, step):
        box = QFrame()
        box.setObjectName("card")
        v = QVBoxLayout(box)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(8)

        title = QLabel(f"<b>{step['title']}</b>")
        title.setStyleSheet("color: #CB6892; font-size: 17px;")
        title.setWordWrap(True)
        v.addWidget(title)

        table = self._build_table(step)
        v.addWidget(table)

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
            lbl.setStyleSheet("color: #947783; font-size: 14px;")
            v.addWidget(lbl)

        self.layout.addWidget(box)

    # ------------------------------------------------------------------
    def _build_table(self, step):
        tableau = step["tableau"]
        names = step["variable_names"]
        basis = step["basis"]
        cb = step["cb"]
        deltas = step["deltas"]
        c_full = step.get("c", [0.0] * len(names))   # полный вектор c_j
        pivot = step.get("pivot")

        # --- Скрываем столбцы s1, s2, ... (доп. переменные) ---
        # Оставляем только x1..xn. Если решите вернуть s — просто
        # замените условие ниже на `return True`.
        show_idx = [j for j, name in enumerate(names) if name.startswith("x")]
        n_show = len(show_idx)

        rows = len(tableau)

        # --- Колонки: C_b | Базис | x1..xn | b ---
        cols = 2 + n_show + 1
        table = QTableWidget(rows + 2, cols)   # + c_j + Δ_j
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setFont(QFont("Arial", 12))

        headers = ["C_b", "Базис"] + [names[j] for j in show_idx] + ["b"]
        table.setHorizontalHeaderLabels(headers)

        vheaders = [f"A{i + 1}" for i in range(rows)] + ["c_j", "Δ_j"]
        table.setVerticalHeaderLabels(vheaders)

        # --- Строки базиса ---
        for i in range(rows):
            # C_b
            item = QTableWidgetItem(self._fmt(cb[i]))
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor("#F4D6E3"))
            table.setItem(i, 0, item)

            # Базис
            item = QTableWidgetItem(names[basis[i]])
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor("#F4D6E3"))
            table.setItem(i, 1, item)

            # Коэффициенты (только для show_idx)
            for c_pos, j in enumerate(show_idx):
                item = QTableWidgetItem(self._fmt(tableau[i][j]))
                item.setTextAlignment(Qt.AlignCenter)
                if pivot and j == pivot["column"]:
                    item.setBackground(QColor("#F8D5E4"))
                table.setItem(i, 2 + c_pos, item)

            # b
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
        table.setItem(r, 1, item)

        for c_pos, j in enumerate(show_idx):
            item = QTableWidgetItem(self._fmt(c_full[j]))
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor("#EBC6D7"))
            table.setItem(r, 2 + c_pos, item)

        # --- Строка Δ_j ---
        r = rows + 1
        item = QTableWidgetItem("Δ_j")
        item.setTextAlignment(Qt.AlignCenter)
        item.setBackground(QColor("#EBC6D7"))
        table.setItem(r, 1, item)

        for c_pos, j in enumerate(show_idx):
            item = QTableWidgetItem(self._fmt(deltas[j]))
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor("#EBC6D7"))
            table.setItem(r, 2 + c_pos, item)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setMinimumHeight(32 * (rows + 2) + 8)

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