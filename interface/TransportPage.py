# TransportPage.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QSpinBox, QTableWidget, QTableWidgetItem,
    QGroupBox, QScrollArea, QMessageBox,
    QHeaderView
)

from PyQt5.QtCore import Qt

from TransportSolver import solve_transport


class TransportPage(QWidget):

    def __init__(self):
        super().__init__()

        self.result = None
        self.iterations = []
        self.current_step = 0

        self.init_ui()

    # -------------------------------------------------
    # СОЗДАНИЕ ИНТЕРФЕЙСА
    # -------------------------------------------------

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(18)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("Решение транспортной задачи")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #CB6892;
            padding: 10px;
        """)

        layout.addWidget(title)

        # Размерность задачи
        dimensions_group = QGroupBox("Размерность транспортной задачи")
        dimensions_layout = QHBoxLayout(dimensions_group)

        dimensions_layout.addWidget(
            QLabel("Поставщики:")
        )

        self.suppliers_spin = QSpinBox()
        self.suppliers_spin.setRange(1, 15)
        self.suppliers_spin.setValue(2)

        dimensions_layout.addWidget(self.suppliers_spin)

        dimensions_layout.addWidget(
            QLabel("Потребители:")
        )

        self.consumers_spin = QSpinBox()
        self.consumers_spin.setRange(1, 15)
        self.consumers_spin.setValue(2)

        dimensions_layout.addWidget(self.consumers_spin)

        layout.addWidget(dimensions_group)

        # Начальный метод
        method_group = QGroupBox("Метод построения начального плана")
        method_layout = QHBoxLayout(method_group)

        self.method_combo = QComboBox()
        self.method_combo.addItem(
            "Метод минимальной стоимости",
            "least_cost"
        )
        self.method_combo.addItem(
            "Метод северо-западного угла",
            "nw"
        )

        method_layout.addWidget(self.method_combo)

        layout.addWidget(method_group)

        # Транспортная таблица
        table_group = QGroupBox("Исходные данные")
        table_layout = QVBoxLayout(table_group)

        explanation = QLabel(
            "Введите тарифы перевозок, запасы поставщиков "
            "и потребности потребителей."
        )
        explanation.setWordWrap(True)

        table_layout.addWidget(explanation)

        self.transport_table = QTableWidget()
        table_layout.addWidget(self.transport_table)

        layout.addWidget(table_group)

        self.suppliers_spin.valueChanged.connect(
            self.rebuild_table
        )

        self.consumers_spin.valueChanged.connect(
            self.rebuild_table
        )

        self.rebuild_table()

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.solve_button = QPushButton("Решить задачу")
        self.clear_button = QPushButton("Очистить")

        self.solve_button.clicked.connect(self.solve)
        self.clear_button.clicked.connect(self.clear)

        buttons_layout.addWidget(self.solve_button)
        buttons_layout.addWidget(self.clear_button)

        layout.addLayout(buttons_layout)

        # Результаты
        result_group = QGroupBox("Ход решения")
        result_layout = QVBoxLayout(result_group)

        self.step_label = QLabel(
            "Решение ещё не запущено."
        )
        self.step_label.setAlignment(Qt.AlignCenter)

        result_layout.addWidget(self.step_label)

        self.step_description = QLabel("")
        self.step_description.setWordWrap(True)

        result_layout.addWidget(self.step_description)

        self.iteration_table = QTableWidget()
        result_layout.addWidget(self.iteration_table)

        self.iteration_info = QLabel("")
        self.iteration_info.setWordWrap(True)

        result_layout.addWidget(self.iteration_info)

        # Навигация
        navigation_layout = QHBoxLayout()

        self.previous_button = QPushButton("Предыдущая итерация")
        self.next_button = QPushButton("Следующая итерация")

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

        # Итоговый ответ
        self.final_result = QLabel(
            "Здесь появится итоговый план перевозок."
        )
        self.final_result.setWordWrap(True)
        self.final_result.setAlignment(Qt.AlignCenter)

        result_layout.addWidget(self.final_result)

        layout.addWidget(result_group)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    # -------------------------------------------------
    # ПОСТРОЕНИЕ ИСХОДНОЙ ТРАНСПОРТНОЙ ТАБЛИЦЫ
    # -------------------------------------------------

    def rebuild_table(self):
        old_values = []

        if hasattr(self, "transport_table"):
            for i in range(self.transport_table.rowCount()):
                row = []

                for j in range(self.transport_table.columnCount()):
                    item = self.transport_table.item(i, j)

                    row.append(
                        item.text() if item else ""
                    )

                old_values.append(row)

        m = self.suppliers_spin.value()
        n = self.consumers_spin.value()

        # Последняя строка — потребности.
        # Последний столбец — запасы.
        self.transport_table.setRowCount(m + 1)
        self.transport_table.setColumnCount(n + 1)

        headers = [
            f"B{j + 1}" for j in range(n)
        ]

        headers.append("Запасы")

        self.transport_table.setHorizontalHeaderLabels(
            headers
        )

        vertical_headers = [
            f"A{i + 1}" for i in range(m)
        ]

        vertical_headers.append("Потребности")

        self.transport_table.setVerticalHeaderLabels(
            vertical_headers
        )

        for i in range(m + 1):
            for j in range(n + 1):

                value = ""

                if (
                    i < len(old_values)
                    and j < len(old_values[i])
                ):
                    value = old_values[i][j]

                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)

                self.transport_table.setItem(
                    i, j, item
                )

        self.transport_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.transport_table.verticalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.transport_table.setMinimumHeight(
            (m + 1) * 75 + 60
        )

    # -------------------------------------------------
    # ПРЕОБРАЗОВАНИЕ ВВЕДЁННЫХ ЧИСЕЛ
    # -------------------------------------------------

    @staticmethod
    def parse_number(value):
        return float(
            value.strip().replace(",", ".")
        )

    # -------------------------------------------------
    # СЧИТЫВАНИЕ ИСХОДНОЙ ЗАДАЧИ
    # -------------------------------------------------

    def read_problem(self):
        m = self.suppliers_spin.value()
        n = self.consumers_spin.value()

        c = []
        a = []
        b = []

        # Тарифы и запасы
        for i in range(m):
            row = []

            for j in range(n):
                item = self.transport_table.item(i, j)

                if item is None or not item.text().strip():
                    raise ValueError(
                        f"Не указан тариф перевозки "
                        f"от поставщика A{i + 1} "
                        f"потребителю B{j + 1}."
                    )

                value = self.parse_number(item.text())

                if value < 0:
                    raise ValueError(
                        "Тарифы не могут быть отрицательными."
                    )

                row.append(value)

            supply_item = self.transport_table.item(i, n)

            if (
                supply_item is None
                or not supply_item.text().strip()
            ):
                raise ValueError(
                    f"Не указан запас поставщика A{i + 1}."
                )

            supply = self.parse_number(
                supply_item.text()
            )

            if supply < 0:
                raise ValueError(
                    "Запасы не могут быть отрицательными."
                )

            c.append(row)
            a.append(supply)

        # Потребности
        for j in range(n):
            demand_item = self.transport_table.item(m, j)

            if (
                demand_item is None
                or not demand_item.text().strip()
            ):
                raise ValueError(
                    f"Не указана потребность B{j + 1}."
                )

            demand = self.parse_number(
                demand_item.text()
            )

            if demand < 0:
                raise ValueError(
                    "Потребности не могут быть отрицательными."
                )

            b.append(demand)

        return c, a, b

    # -------------------------------------------------
    # ЗАПУСК РЕШЕНИЯ
    # -------------------------------------------------

    def solve(self):
        try:
            c, a, b = self.read_problem()

            init_method = self.method_combo.currentData()

            self.result = solve_transport(
                c,
                a,
                b,
                init_method=init_method
            )

            self.iterations = self.result["iterations"]
            self.current_step = 0

            if not self.iterations:
                raise ValueError(
                    "Алгоритм не вернул итерации."
                )

            # Информация о балансировке
            dummy_info = self.result.get("dummy_info")

            if dummy_info:
                self.step_description.setText(
                    "Для балансировки задачи автоматически "
                    "добавлен фиктивный участник:\n"
                    + dummy_info
                )
            else:
                self.step_description.setText(
                    "Транспортная задача сбалансирована. "
                    "Дополнительные строки и столбцы не требуются."
                )

            self.show_step()
            self.show_final_result()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка",
                str(error)
            )

    # -------------------------------------------------
    # ОТОБРАЖЕНИЕ ИТЕРАЦИИ
    # -------------------------------------------------

    def show_step(self):
        if not self.iterations or self.result is None:
            return

        state = self.iterations[self.current_step]

        c = self.result["c"]
        a = self.result["a"]
        b = self.result["b"]

        x = state["x"]
        basic = state["basic"]

        m = len(c)
        n = len(c[0])

        self.step_label.setText(
            f"Итерация {self.current_step + 1} "
            f"из {len(self.iterations)}"
        )

        # Создаём таблицу
        self.iteration_table.clear()

        self.iteration_table.setRowCount(m + 1)
        self.iteration_table.setColumnCount(n + 1)

        headers = [
            f"B{j + 1}" for j in range(n)
        ]

        headers.append("Запасы")

        self.iteration_table.setHorizontalHeaderLabels(
            headers
        )

        vertical_headers = [
            f"A{i + 1}" for i in range(m)
        ]

        vertical_headers.append("Потребности")

        self.iteration_table.setVerticalHeaderLabels(
            vertical_headers
        )

        # Ячейки транспортной таблицы
        for i in range(m):
            for j in range(n):

                cost = c[i][j]
                shipment = x[i][j]

                cell_text = (
                    f"Тариф: {cost:g}\n"
                    f"Перевозка: {shipment:g}"
                )

                # Оценка для небазисной клетки
                if state["u"] is not None and state["v"] is not None:
                    if (i, j) not in basic:
                        delta = (
                            cost
                            - state["u"][i]
                            - state["v"][j]
                        )

                        cell_text += (
                            f"\nΔ = {delta:.4f}"
                        )

                # Обозначение базисной клетки
                if (i, j) in basic:
                    cell_text += "\nБазисная"

                item = QTableWidgetItem(cell_text)
                item.setTextAlignment(Qt.AlignCenter)

                self.iteration_table.setItem(
                    i, j, item
                )

            # Запасы
            supply_item = QTableWidgetItem(
                f"{a[i]:g}"
            )

            supply_item.setTextAlignment(Qt.AlignCenter)

            self.iteration_table.setItem(
                i, n, supply_item
            )

        # Потребности
        for j in range(n):
            demand_item = QTableWidgetItem(
                f"{b[j]:g}"
            )

            demand_item.setTextAlignment(Qt.AlignCenter)

            self.iteration_table.setItem(
                m, j, demand_item
            )

        # Последняя ячейка
        self.iteration_table.setItem(
            m, n,
            QTableWidgetItem("—")
        )

        # Размеры таблицы
        self.iteration_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.iteration_table.verticalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.iteration_table.verticalHeader().setVisible(True)

        self.iteration_table.setMinimumHeight(
            (m + 1) * 115 + 60
        )

        # Потенциалы
        u = state["u"]
        v = state["v"]

        info = ""

        if u is not None and v is not None:
            info += (
                "Потенциалы поставщиков:\n"
                + ", ".join(
                    f"u{i + 1} = {value:.4f}"
                    for i, value in enumerate(u)
                )
                + "\n\nПотенциалы потребителей:\n"
                + ", ".join(
                    f"v{j + 1} = {value:.4f}"
                    for j, value in enumerate(v)
                )
            )

        # Входящая клетка и цикл
        enter = state["enter"]

        if enter is not None:
            info += (
                f"\n\nВводимая клетка: "
                f"A{enter[0] + 1} → B{enter[1] + 1}"
            )

        cycle = state["cycle"]
        signs = state["signs"]

        if cycle:
            cycle_text = []

            for cell, sign in zip(cycle, signs):
                cycle_text.append(
                    f"{sign} A{cell[0] + 1} → B{cell[1] + 1}"
                )

            info += (
                "\n\nЦикл перераспределения:\n"
                + "  ".join(cycle_text)
            )

            info += (
                f"\n\nθ = {state['theta']:g}"
            )

            leave = state["leave"]

            if leave is not None:
                info += (
                    f"\nВыбывающая клетка: "
                    f"A{leave[0] + 1} → B{leave[1] + 1}"
                )

        else:
            info += (
                "\n\nОтрицательных оценок нет. "
                "Получен оптимальный план."
            )

        self.iteration_info.setText(info)

        self.previous_button.setEnabled(
            self.current_step > 0
        )

        self.next_button.setEnabled(
            self.current_step < len(self.iterations) - 1
        )

    # -------------------------------------------------
    # ИТОГОВЫЙ РЕЗУЛЬТАТ
    # -------------------------------------------------

    def show_final_result(self):
        if self.result is None:
            return

        x = self.result["x"]
        z = self.result["Z"]

        lines = [
            "ОПТИМАЛЬНЫЙ ПЛАН ПЕРЕВОЗОК",
            ""
        ]

        for i, row in enumerate(x):
            for j, value in enumerate(row):
                if value > 1e-9:
                    lines.append(
                        f"A{i + 1} → B{j + 1}: {value:g}"
                    )

        lines.append("")
        lines.append(
            f"Минимальная стоимость перевозок: {z:g}"
        )

        self.final_result.setText(
            "\n".join(lines)
        )

    # -------------------------------------------------
    # ПЕРЕКЛЮЧЕНИЕ ИТЕРАЦИЙ
    # -------------------------------------------------

    def previous_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()

    def next_step(self):
        if self.current_step < len(self.iterations) - 1:
            self.current_step += 1
            self.show_step()

    # -------------------------------------------------
    # ОЧИСТКА
    # -------------------------------------------------

    def clear(self):
        self.suppliers_spin.setValue(2)
        self.consumers_spin.setValue(2)

        self.method_combo.setCurrentIndex(0)

        self.rebuild_table()

        self.result = None
        self.iterations = []
        self.current_step = 0

        self.iteration_table.clear()
        self.iteration_table.setRowCount(0)
        self.iteration_table.setColumnCount(0)

        self.step_label.setText(
            "Решение ещё не запущено."
        )

        self.step_description.clear()
        self.iteration_info.clear()

        self.final_result.setText(
            "Здесь появится итоговый план перевозок."
        )

        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)