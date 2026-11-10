# SimplexPage.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QSpinBox, QTableWidget, QTableWidgetItem,
    QGroupBox, QScrollArea, QMessageBox,
    QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from MethodSelection import solve_problem


class SimplexPage(QWidget):

    def __init__(self):
        super().__init__()

        self.result = None
        self.steps = []
        self.current_step = 0

        self.init_ui()

    # -------------------------------------------------
    # СОЗДАНИЕ ИНТЕРФЕЙСА
    # -------------------------------------------------

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(18)

        # Область прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("Решение задачи линейного программирования")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 34px; font-weight: bold; color: #CB6892;"
        )

        layout.addWidget(title)

        # Ввод целевой функции
        objective_group = QGroupBox("Целевая функция")
        objective_layout = QGridLayout(objective_group)

        objective_layout.addWidget(
            QLabel("Тип задачи:"), 0, 0
        )

        self.objective_combo = QComboBox()
        self.objective_combo.addItems([
            "Максимум",
            "Минимум"
        ])

        objective_layout.addWidget(
            self.objective_combo, 0, 1
        )

        objective_layout.addWidget(
            QLabel("Коэффициенты функции:"), 1, 0
        )

        self.objective_input = QLineEdit()
        self.objective_input.setPlaceholderText(
            "Например: 3, 2"
        )

        objective_layout.addWidget(
            self.objective_input, 1, 1
        )

        layout.addWidget(objective_group)

        # Размерность задачи
        dimensions_group = QGroupBox("Размерность задачи")
        dimensions_layout = QHBoxLayout(dimensions_group)

        dimensions_layout.addWidget(
            QLabel("Количество переменных:")
        )

        self.variables_spin = QSpinBox()
        self.variables_spin.setRange(1, 20)
        self.variables_spin.setValue(2)

        dimensions_layout.addWidget(self.variables_spin)

        dimensions_layout.addWidget(
            QLabel("Количество ограничений:")
        )

        self.constraints_spin = QSpinBox()
        self.constraints_spin.setRange(1, 30)
        self.constraints_spin.setValue(2)

        dimensions_layout.addWidget(self.constraints_spin)

        layout.addWidget(dimensions_group)

        # Таблица ограничений
        constraints_group = QGroupBox("Ограничения")
        constraints_layout = QVBoxLayout(constraints_group)

        self.constraints_table = QTableWidget()
        constraints_layout.addWidget(self.constraints_table)

        layout.addWidget(constraints_group)

        self.variables_spin.valueChanged.connect(
            self.rebuild_constraints_table
        )

        self.constraints_spin.valueChanged.connect(
            self.rebuild_constraints_table
        )

        self.rebuild_constraints_table()

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        self.solve_button = QPushButton("Решить задачу")
        self.clear_button = QPushButton("Очистить")

        self.solve_button.clicked.connect(self.solve)
        self.clear_button.clicked.connect(self.clear)

        buttons_layout.addWidget(self.solve_button)
        buttons_layout.addWidget(self.clear_button)

        layout.addLayout(buttons_layout)

        # Результат
        result_group = QGroupBox("Ход решения")
        result_layout = QVBoxLayout(result_group)

        self.step_label = QLabel("Решение ещё не запущено")
        self.step_label.setAlignment(Qt.AlignCenter)

        result_layout.addWidget(self.step_label)

        self.step_content = QWidget()
        self.step_content_layout = QVBoxLayout(self.step_content)

        result_layout.addWidget(self.step_content)

        # Переключение шагов
        navigation_layout = QHBoxLayout()

        self.previous_button = QPushButton("Предыдущий шаг")
        self.next_button = QPushButton("Следующий шаг")

        self.previous_button.clicked.connect(
            self.previous_step
        )

        self.next_button.clicked.connect(
            self.next_step
        )

        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)

        navigation_layout.addWidget(self.previous_button)
        navigation_layout.addWidget(self.next_button)

        result_layout.addLayout(navigation_layout)

        # Итог
        self.final_result = QLabel(
            "Здесь появится итоговый результат."
        )
        self.final_result.setWordWrap(True)
        self.final_result.setAlignment(Qt.AlignCenter)

        result_layout.addWidget(self.final_result)

        layout.addWidget(result_group)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    # -------------------------------------------------
    # ПОСТРОЕНИЕ ТАБЛИЦЫ ОГРАНИЧЕНИЙ
    # -------------------------------------------------

    
    
    def rebuild_constraints_table(self):
        old_values = []

        if self.constraints_table.rowCount() > 0:
            old_variables = self.constraints_table.columnCount() - 2

            for i in range(self.constraints_table.rowCount()):
                row = []

                # Считываем только коэффициенты
                for j in range(old_variables):
                    item = self.constraints_table.item(i, j)
                    row.append(item.text() if item else "")

                # Отдельно считываем знак
                sign_widget = self.constraints_table.cellWidget(
                    i, old_variables
                )

                sign = sign_widget.currentText() if sign_widget else "<="

                # Отдельно считываем правую часть
                free_item = self.constraints_table.item(
                    i, old_variables + 1
                )

                free_value = free_item.text() if free_item else ""

                old_values.append({
                    "coefficients": row,
                    "sign": sign,
                    "free_value": free_value
                })

        variables = self.variables_spin.value()
        constraints = self.constraints_spin.value()

        self.constraints_table.clear()
        self.constraints_table.setColumnCount(variables + 2)
        self.constraints_table.setRowCount(constraints)

        headers = [f"x{i + 1}" for i in range(variables)]
        headers.extend(["Знак", "Правая часть"])

        self.constraints_table.setHorizontalHeaderLabels(headers)

        for i in range(constraints):
            old_row = old_values[i] if i < len(old_values) else None

            # Коэффициенты переменных
            for j in range(variables):
                value = ""

                if old_row and j < len(old_row["coefficients"]):
                    value = old_row["coefficients"][j]

                self.constraints_table.setItem(
                    i, j, QTableWidgetItem(value)
                )

            # Выпадающий список знаков
            sign_combo = QComboBox()
            sign_combo.addItems(["<=", ">=", "="])

            if old_row:
                sign_combo.setCurrentText(old_row["sign"])

            self.constraints_table.setCellWidget(
                i, variables, sign_combo
            )

            # Правая часть
            free_value = old_row["free_value"] if old_row else ""

            self.constraints_table.setItem(
                i, variables + 1,
                QTableWidgetItem(free_value)
            )

        header = self.constraints_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        header.setSectionResizeMode(variables, QHeaderView.Fixed)
        header.setSectionResizeMode(variables + 1, QHeaderView.Fixed)

        self.constraints_table.setColumnWidth(variables, 110)
        self.constraints_table.setColumnWidth(variables + 1, 200)

        self.constraints_table.setMinimumWidth(
            variables * 130 + 110 + 200 + 60
        )

        self.constraints_table.verticalHeader().setDefaultSectionSize(65)

        self.constraints_table.setMinimumHeight(
            max(150, constraints * 65 + 60)
        )



    # -------------------------------------------------
    # ПОЛУЧЕНИЕ ЧИСЕЛ
    # -------------------------------------------------

    @staticmethod
    def parse_number(value):
        return float(value.strip().replace(",", "."))

    # -------------------------------------------------
    # СЧИТЫВАНИЕ ЗАДАЧИ
    # -------------------------------------------------

    def read_problem(self):
        variables = self.variables_spin.value()
        constraints = self.constraints_spin.value()

        c_text = self.objective_input.text().split(",")

        if len(c_text) != variables:
            raise ValueError(
                f"В целевой функции должно быть {variables} коэффициентов."
            )

        c = [
            self.parse_number(value)
            for value in c_text
        ]

        A = []
        b = []
        signs = []

        for i in range(constraints):
            row = []

            for j in range(variables):
                item = self.constraints_table.item(i, j)

                if item is None or not item.text().strip():
                    raise ValueError(
                        f"Не заполнен коэффициент x{j + 1} "
                        f"в ограничении №{i + 1}."
                    )

                row.append(self.parse_number(item.text()))

            sign_combo = self.constraints_table.cellWidget(
                i, variables
            )

            sign = sign_combo.currentText()

            free_item = self.constraints_table.item(
                i, variables + 1
            )

            if free_item is None or not free_item.text().strip():
                raise ValueError(
                    f"Не заполнена правая часть ограничения №{i + 1}."
                )

            free_value = self.parse_number(free_item.text())

            A.append(row)
            b.append(free_value)
            signs.append(sign)

        objective = (
            "max"
            if self.objective_combo.currentIndex() == 0
            else "min"
        )

        return c, A, b, signs, objective

    # -------------------------------------------------
    # ЗАПУСК РЕШЕНИЯ
    # -------------------------------------------------

    def solve(self):
        try:
            c, A, b, signs, objective = self.read_problem()

            self.result = solve_problem(
                c, A, b, signs, objective
            )

            self.steps = self.result.get("steps", [])
            self.current_step = 0

            if not self.steps:
                self.steps = [{
                    "type": "text",
                    "title": "Результат",
                    "description": self.result.get(
                        "message", "Решение завершено."
                    )
                }]

            self.show_step()

            status = self.result.get("status", "unknown")
            message = self.result.get("message", "")

            solution = self.result.get("solution")
            objective_value = self.result.get("objective_value")

            if solution is not None:
                variables_text = ", ".join(
                    f"x{i + 1} = {value:.5f}"
                    for i, value in enumerate(solution)
                )

                result_text = (
                    f"Статус: {status}\n"
                    f"{variables_text}\n"
                    f"Значение целевой функции: {objective_value}\n"
                    f"{message}"
                )
            else:
                result_text = (
                    f"Статус: {status}\n"
                    f"{message}"
                )

            self.final_result.setText(result_text)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка",
                str(error)
            )

    # -------------------------------------------------
    # ОТОБРАЖЕНИЕ ТЕКУЩЕГО ШАГА
    # -------------------------------------------------

    def clear_step_content(self):
        while self.step_content_layout.count():
            item = self.step_content_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def show_step(self):
        if not self.steps:
            return

        self.clear_step_content()

        step = self.steps[self.current_step]

        self.step_label.setText(
            f"Шаг {self.current_step + 1} из {len(self.steps)}"
        )

        title = QLabel(step.get("title", "Этап решения"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: #CB6892;"
        )

        self.step_content_layout.addWidget(title)

        description = QLabel(
            step.get("description", "")
        )

        description.setWordWrap(True)

        self.step_content_layout.addWidget(description)

        if step.get("type") == "table":
            self.show_table(step)

        self.previous_button.setEnabled(
            self.current_step > 0
        )

        self.next_button.setEnabled(
            self.current_step < len(self.steps) - 1
        )

    # -------------------------------------------------
    # ОТОБРАЖЕНИЕ СИМПЛЕКСНОЙ ТАБЛИЦЫ
    # -------------------------------------------------

    def show_table(self, step):
        tableau = step["tableau"]
        basis_names = step["basis_names"]
        variable_names = step["variable_names"]
        cb = step["cb"]
        zj = step["zj"]
        deltas = step["deltas"]

        m = len(tableau)
        n = len(variable_names)

        table = QTableWidget(m + 2, n + 3)

        headers = ["Базис", "Cb"]
        headers.extend(variable_names)
        headers.append("b")

        table.setHorizontalHeaderLabels(headers)

        # Строки базиса
        for i in range(m):
            table.setItem(
                i, 0,
                QTableWidgetItem(basis_names[i])
            )

            table.setItem(
                i, 1,
                QTableWidgetItem(f"{cb[i]:.4f}")
            )

            for j in range(n):
                table.setItem(
                    i, j + 2,
                    QTableWidgetItem(f"{tableau[i][j]:.4f}")
                )

            table.setItem(
                i, n + 2,
                QTableWidgetItem(f"{tableau[i][-1]:.4f}")
            )

        # Строка Zj
        zj_row = m

        table.setItem(
            zj_row, 0,
            QTableWidgetItem("Zj")
        )

        for j in range(n):
            table.setItem(
                zj_row, j + 2,
                QTableWidgetItem(f"{zj[j]:.4f}")
            )

        # Строка Delta
        delta_row = m + 1

        table.setItem(
            delta_row, 0,
            QTableWidgetItem("Δj")
        )

        for j in range(n):
            table.setItem(
                delta_row, j + 2,
                QTableWidgetItem(f"{deltas[j]:.4f}")
            )

        # Выделение строк оценок
        for j in range(n + 2):
            for row in (zj_row, delta_row):
                item = table.item(row, j)

                if item is None:
                    item = QTableWidgetItem("")
                    table.setItem(row, j, item)

                item.setBackground(
                    Qt.GlobalColor.lightGray
                )

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        table.verticalHeader().setVisible(False)

        table.setMinimumHeight(
            min(600, (m + 2) * 65 + 60)
        )

        self.step_content_layout.addWidget(table)

        # Информация о разрешающем элементе
        pivot = step.get("pivot")

        if pivot:
            pivot_label = QLabel(
                f"Разрешающий элемент: {pivot}"
            )
            pivot_label.setWordWrap(True)

            self.step_content_layout.addWidget(
                pivot_label
            )

    # -------------------------------------------------
    # ПЕРЕКЛЮЧЕНИЕ ШАГОВ
    # -------------------------------------------------

    def previous_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()

    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.show_step()

    # -------------------------------------------------
    # ОЧИСТКА
    # -------------------------------------------------

    def clear(self):
        self.objective_input.clear()

        self.variables_spin.setValue(2)
        self.constraints_spin.setValue(2)

        self.rebuild_constraints_table()

        self.result = None
        self.steps = []
        self.current_step = 0

        self.clear_step_content()

        self.step_label.setText(
            "Решение ещё не запущено"
        )

        self.final_result.setText(
            "Здесь появится итоговый результат."
        )

        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)