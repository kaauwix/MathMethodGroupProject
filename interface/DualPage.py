from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QComboBox, QScrollArea,
    QFrame, QSpinBox, QTabWidget
)
from PyQt5.QtCore import Qt
from SolveLP import solve_primal_and_dual
from interface.StepViewers import StepsViewer


class DualPage(QWidget):
    def __init__(self):
        super().__init__()
        self.n_vars = 2
        self.m_cons = 2

        self.var_inputs = []
        self.cons_inputs = []
        self.cons_signs = []
        self.cons_b_inputs = []

        self.init_ui()

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

        size_group.setLayout(size_layout)
        main_layout.addWidget(size_group)

        # --- Прокрутка ввода ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)

        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, 1)

        # --- Вкладки результата ---
        self.results_tabs = QTabWidget()

        self.tab_primal = QTextEdit()
        self.tab_primal.setReadOnly(True)
        self.results_tabs.addTab(self.tab_primal, "Прямая задача")

        self.tab_dual = QTextEdit()
        self.tab_dual.setReadOnly(True)
        self.results_tabs.addTab(self.tab_dual, "Двойственная")

        self.tab_form = QTextEdit()
        self.tab_form.setReadOnly(True)
        self.results_tabs.addTab(self.tab_form, "Формулировка")

        self.tab_steps_primal = StepsViewer()
        self.results_tabs.addTab(self.tab_steps_primal, "Шаги прямой")

        self.tab_steps_dual = StepsViewer()
        self.results_tabs.addTab(self.tab_steps_dual, "Шаги двойственной")

        main_layout.addWidget(self.results_tabs, 1)

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

        solve_btn = QPushButton("РЕШИТЬ ПРЯМУЮ И ДВОЙСТВЕННУЮ")
        solve_btn.setObjectName("solveButton")
        solve_btn.setMinimumHeight(50)
        solve_btn.clicked.connect(self.on_solve)
        self.scroll_layout.addWidget(solve_btn)
        self.scroll_layout.addStretch()

    # ------------------------------------------------------------------
    def on_solve(self):
        try:
            c = [float(inp.text()) for inp in self.var_inputs]
            objective = self.obj_combo.currentText()

            A = []
            for i in range(self.m_cons):
                row = [float(self.cons_inputs[i * self.n_vars + j].text())
                       for j in range(self.n_vars)]
                A.append(row)

            b = [float(inp.text()) for inp in self.cons_b_inputs]
            signs = [combo.currentText() for combo in self.cons_signs]

            res = solve_primal_and_dual(c, A, b, signs, objective)

            # --- Прямая ---
            self.tab_primal.clear()
            p = res["primal"]
            self.tab_primal.append(f"<b>Статус:</b> {p['status']}")
            self.tab_primal.append(f"<b>Сообщение:</b> {p['message']}")
            if p.get('solution'):
                self.tab_primal.append(f"<b>Решение:</b> {p['solution']}")
                self.tab_primal.append(
                    f"<b>Значение f(x):</b> {p['objective_value']}"
                )

            # --- Двойственная ---
            self.tab_dual.clear()
            d = res.get("dual")
            if d:
                self.tab_dual.append(f"<b>Статус:</b> {d['status']}")
                self.tab_dual.append(f"<b>Сообщение:</b> {d['message']}")
                self.tab_dual.append(f"<b>Решение (y):</b> {d['solution']}")
                self.tab_dual.append(
                    f"<b>Значение g(y):</b> {d['objective_value']}"
                )

                if p["status"] == "optimal":
                    diff = abs(p['objective_value'] - d['objective_value'])
                    if diff < 1e-6:
                        self.tab_dual.append(
                            "<br><span style='color:green;'>"
                            "<b>✔ Теорема двойственности выполнена: f(x) = g(y)</b>"
                            "</span>"
                        )
                    else:
                        self.tab_dual.append(
                            "<br><span style='color:red;'>"
                            "<b>✘ Ошибка: f(x) ≠ g(y)</b>"
                            "</span>"
                        )
            else:
                self.tab_dual.setText(
                    "Двойственная задача не может быть решена "
                    "(прямая задача не имеет оптимального решения)."
                )

            # --- Формулировка ---
            self.tab_form.clear()
            form = res.get("dual_formulation")
            if form:
                self.tab_form.append("<b>Двойственная задача:</b>")
                self.tab_form.append(
                    f"g(y) = {form['c']} * y -> {form['objective']}"
                )
                self.tab_form.append("Матрица A^T:")
                for row in form['A']:
                    self.tab_form.append(f"  {row}")
                self.tab_form.append(f"Правые части (c): {form['b']}")
                self.tab_form.append(f"Знаки: {form['signs']}")
                self.tab_form.append("y >= 0")
            else:
                self.tab_form.setText(
                    "Явная формулировка недоступна "
                    "(есть смешанные знаки ограничений или равенства)."
                )

            # --- Шаги прямой ---
            self.tab_steps_primal.show_steps(p.get("steps", []))

            # --- Шаги двойственной ---
            if d and d.get("steps"):
                self.tab_steps_dual.show_steps(d["steps"])
            else:
                self.tab_steps_dual.show_message(
                    "Двойственная задача решалась неявно — решение извлечено "
                    "из финальной таблицы прямой задачи. Отдельных шагов нет."
                )

        except ValueError:
            self.tab_primal.setText(
                "<span style='color:red;'>Ошибка ввода: проверьте числа!</span>"
            )
            self.tab_dual.clear()
            self.tab_form.clear()
            self.tab_steps_primal.clear()
            self.tab_steps_dual.clear()
        except Exception as e:
            self.tab_primal.setText(
                f"<span style='color:red;'>Ошибка: {e}</span>"
            )
            self.tab_dual.clear()
            self.tab_form.clear()
            self.tab_steps_primal.clear()
            self.tab_steps_dual.clear()