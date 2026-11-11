from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt
from optimal import check_optimality


class OptimalityPage(QWidget):
    def __init__(self):
        super().__init__()
        self.n_vars = 2
        self.m_cons = 2

        self.var_inputs = []
        self.cons_inputs = []
        self.cons_signs = []
        self.cons_b_inputs = []

        self.init_ui()
        self.load_example()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # --- Размерность ---
        size_group = QGroupBox("Размерность задачи")
        size_layout = QHBoxLayout()

        size_layout.addWidget(QLabel("Количество переменных (x):"))
        self.n_vars_spin = QSpinBox()
        self.n_vars_spin.setRange(1, 10)
        self.n_vars_spin.setValue(self.n_vars)
        self.n_vars_spin.valueChanged.connect(self.rebuild_ui)
        size_layout.addWidget(self.n_vars_spin)

        size_layout.addWidget(QLabel("Количество ограничений:"))
        self.m_cons_spin = QSpinBox()
        self.m_cons_spin.setRange(1, 10)
        self.m_cons_spin.setValue(self.m_cons)
        self.m_cons_spin.valueChanged.connect(self.rebuild_ui)
        size_layout.addWidget(self.m_cons_spin)
        size_layout.addStretch()

        size_group.setLayout(size_layout)
        main_layout.addWidget(size_group)

        # --- Контейнер ввода (без QScrollArea) ---
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)
        main_layout.addWidget(self.scroll_content, 1)

        # --- Результат ---
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setMaximumHeight(250)
        main_layout.addWidget(QLabel("<b>Результат проверки:</b>"))
        main_layout.addWidget(self.result_output)

        self.rebuild_ui()

    # ------------------------------------------------------------------
    def rebuild_ui(self):
        self.n_vars = self.n_vars_spin.value()
        self.m_cons = self.m_cons_spin.value()

        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.var_inputs.clear()
        self.cons_inputs.clear()
        self.cons_signs.clear()
        self.cons_b_inputs.clear()

        # --- Целевая функция ---
        obj_group = QGroupBox("Целевая функция")
        obj_layout = QHBoxLayout()
        obj_layout.setAlignment(Qt.AlignLeft)

        self.obj_combo = QComboBox()
        self.obj_combo.addItems(["max", "min"])
        obj_layout.addWidget(QLabel("f(x) ="))
        obj_layout.addWidget(self.obj_combo)
        obj_layout.addWidget(QLabel(":"))

        for i in range(self.n_vars):
            if i > 0:
                obj_layout.addWidget(QLabel("+"))

            inp = QLineEdit()
            inp.setFixedWidth(60)
            inp.setAlignment(Qt.AlignCenter)
            inp.setText("0")
            self.var_inputs.append(inp)
            obj_layout.addWidget(inp)

            lbl = QLabel(f"x<sub>{i+1}</sub>")
            lbl.setStyleSheet("font-size: 20px;")
            obj_layout.addWidget(lbl)

        obj_layout.addStretch()
        obj_group.setLayout(obj_layout)
        self.scroll_layout.addWidget(obj_group)

        # --- Ограничения ---
        cons_group = QGroupBox("Ограничения")
        cons_layout = QVBoxLayout()

        for i in range(self.m_cons):
            row_layout = QHBoxLayout()
            row_layout.setAlignment(Qt.AlignLeft)

            for j in range(self.n_vars):
                if j > 0:
                    row_layout.addWidget(QLabel("+"))

                inp = QLineEdit()
                inp.setFixedWidth(60)
                inp.setAlignment(Qt.AlignCenter)
                inp.setText("0")
                self.cons_inputs.append(inp)
                row_layout.addWidget(inp)

                lbl = QLabel(f"x<sub>{j+1}</sub>")
                lbl.setStyleSheet("font-size: 20px;")
                row_layout.addWidget(lbl)

            sign_combo = QComboBox()
            sign_combo.addItems(["<=", ">=", "="])
            sign_combo.setFixedWidth(60)
            self.cons_signs.append(sign_combo)
            row_layout.addWidget(sign_combo)

            b_inp = QLineEdit()
            b_inp.setFixedWidth(60)
            b_inp.setAlignment(Qt.AlignCenter)
            b_inp.setText("0")
            self.cons_b_inputs.append(b_inp)
            row_layout.addWidget(b_inp)

            row_layout.addStretch()
            cons_layout.addLayout(row_layout)

        cons_group.setLayout(cons_layout)
        self.scroll_layout.addWidget(cons_group)

        # --- Проверяемый план ---
        plan_group = QGroupBox("Проверяемый план x")
        plan_layout = QHBoxLayout()
        self.plan_input = QLineEdit()
        self.plan_input.setPlaceholderText(
            "Например: 2, 2 (через запятую)"
        )
        plan_layout.addWidget(QLabel("Значения переменных:"))
        plan_layout.addWidget(self.plan_input)
        plan_group.setLayout(plan_layout)
        self.scroll_layout.addWidget(plan_group)

        check_btn = QPushButton("ПРОВЕРИТЬ ПЛАН")
        check_btn.setObjectName("solveButton")
        check_btn.setMinimumHeight(50)
        check_btn.clicked.connect(self.on_check)
        self.scroll_layout.addWidget(check_btn)
        self.scroll_layout.addStretch()

    # ------------------------------------------------------------------
    def load_example(self):
        self.n_vars_spin.setValue(2)
        self.m_cons_spin.setValue(2)
        self.rebuild_ui()

        self.obj_combo.setCurrentText("max")
        self.var_inputs[0].setText("3")
        self.var_inputs[1].setText("2")

        constraints = [
            ([1.0, 1.0], "<=", 4.0),
            ([2.0, 1.0], "<=", 6.0),
        ]

        for i, (coeffs, sign, rhs) in enumerate(constraints):
            for j in range(self.n_vars):
                self.cons_inputs[i * self.n_vars + j].setText(
                    self._fmt(coeffs[j])
                )
            self.cons_signs[i].setCurrentText(sign)
            self.cons_b_inputs[i].setText(self._fmt(rhs))

        # Оптимальное решение этой задачи — (2, 2)
        self.plan_input.setText("2, 2")

    @staticmethod
    def _fmt(v):
        if float(v).is_integer():
            return str(int(v))
        return str(v)

    # ------------------------------------------------------------------
    def on_check(self):
        try:
            c = [float(inp.text()) for inp in self.var_inputs]
            A = []
            for i in range(self.m_cons):
                row = [float(self.cons_inputs[i * self.n_vars + j].text())
                       for j in range(self.n_vars)]
                A.append(row)
            b = [float(inp.text()) for inp in self.cons_b_inputs]
            signs = [combo.currentText() for combo in self.cons_signs]

            plan_text = self.plan_input.text().replace(' ', '')
            x = [float(val) for val in plan_text.split(',')]

            if len(x) != self.n_vars:
                raise ValueError(
                    f"В плане должно быть ровно {self.n_vars} чисел."
                )

            result = check_optimality(c, A, b, x, signs)

            self.result_output.clear()
            status = result.get('status')

            if status == 'optimal':
                self.result_output.append(
                    "<span style='color:green; font-size:16px;'>"
                    "<b>✔ План ОПТИМАЛЕН</b></span>"
                )
            elif status == 'not_feasible':
                self.result_output.append(
                    "<span style='color:red; font-size:16px;'>"
                    "<b>✘ План НЕДОПУСТИМ</b></span>"
                )
            else:
                self.result_output.append(
                    "<span style='color:red; font-size:16px;'>"
                    "<b>✘ План НЕ ОПТИМАЛЕН</b></span>"
                )

            self.result_output.append(
                f"<b>Сообщение:</b> {result.get('message')}"
            )

            if result.get('y') is not None:
                y_str = ", ".join([f"{v:g}" for v in result['y']])
                self.result_output.append(
                    f"<b>Двойственные оценки (y):</b> {y_str}"
                )

        except ValueError as e:
            self.result_output.setText(
                f"<span style='color:red;'>Ошибка ввода: {e}</span>"
            )
        except Exception as e:
            self.result_output.setText(
                f"<span style='color:red;'>Ошибка проверки: {e}</span>"
            )