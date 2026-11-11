from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QComboBox,
    QSpinBox, QTabWidget
)
from PyQt5.QtCore import Qt
from MethodSelection import solve_problem
from interface.StepViewers import StepsViewer


class SimplexPage(QWidget):
    def __init__(self):
        super().__init__()
        self.n_vars = 4
        self.m_cons = 3

        self.var_inputs = []
        self.var_type_combos = []
        self.cons_inputs = []
        self.cons_signs = []
        self.cons_b_inputs = []

        self.dual_btn = None
        self.mib_btn = None

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
        
        # 0 — блок ввода не растягивается на пустоту
        main_layout.addWidget(self.scroll_content, 0)

        # --- Вкладки результата ---
        self.result_tabs = QTabWidget()

        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_tabs.addTab(self.result_output, "Результат")

        self.steps_viewer = StepsViewer()
        self.result_tabs.addTab(self.steps_viewer, "Шаги решения")

        main_layout.addWidget(QLabel("<b>Результат решения:</b>"))
        
        # 1 — результаты занимают всё оставшееся место
        main_layout.addWidget(self.result_tabs, 1)

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
        self.var_type_combos.clear()
        self.cons_inputs.clear()
        self.cons_signs.clear()
        self.cons_b_inputs.clear()
        self.dual_btn = None
        self.mib_btn = None

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

            # тип переменной
            type_combo = QComboBox()
            type_combo.addItem("≥ 0", "nonneg")
            type_combo.addItem("свободная", "free")
            type_combo.setFixedWidth(110)
            self.var_type_combos.append(type_combo)
            obj_layout.addWidget(type_combo)

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

        # --- Кнопки ---
        solve_btn = QPushButton("РЕШИТЬ ЗАДАЧУ")
        solve_btn.setObjectName("solveButton")
        solve_btn.setMinimumHeight(50)
        solve_btn.clicked.connect(self.on_solve)
        self.scroll_layout.addWidget(solve_btn)

        # Кнопка «двойственным симплексом» — появляется только когда
        # solve_problem вернул «доступен» (dual_available / dual_available_force)
        self.dual_btn = QPushButton("РЕШИТЬ ДВОЙСТВЕННЫМ СИМПЛЕКСОМ")
        self.dual_btn.setObjectName("solveButton")
        self.dual_btn.setMinimumHeight(48)
        self.dual_btn.setVisible(False)
        self.dual_btn.clicked.connect(
            lambda: self.on_solve(force_method="dual")
        )
        self.scroll_layout.addWidget(self.dual_btn)

        # Кнопка «всё равно МИБ» — альтернатива
        self.mib_btn = QPushButton("ВСЁ РАВНО РЕШИТЬ МИБ")
        self.mib_btn.setStyleSheet(
            "background-color: #F4D6E3; color: #49333D; "
            "border: 1px solid #EBC6D7; border-radius: 9px; padding: 10px;"
        )
        self.mib_btn.setMinimumHeight(42)
        self.mib_btn.setVisible(False)
        self.mib_btn.clicked.connect(
            lambda: self.on_solve(force_method="mib")
        )
        self.scroll_layout.addWidget(self.mib_btn)

    # ------------------------------------------------------------------
    def load_example(self):
        # Задача с вашего скриншота
        self.n_vars_spin.setValue(4)
        self.m_cons_spin.setValue(3)
        self.rebuild_ui()

        self.obj_combo.setCurrentText("max")
        
        # Целевая функция: 0x1 + 1x2 - 3x3 + 0x4
        self.var_inputs[0].setText("0")
        self.var_inputs[1].setText("1")
        self.var_inputs[2].setText("-3")
        self.var_inputs[3].setText("0")

        # Ограничения
        constraints = [
            ([0.0, 1.0, 0.0, 1.0], "=", 3.0),
            ([4.0, 0.0, 2.0, 0.0], ">=", 7.0),
            ([4.0, 0.0, 1.0, 0.0], ">=", 5.0),
        ]

        for i, (coeffs, sign, rhs) in enumerate(constraints):
            for j in range(self.n_vars):
                self.cons_inputs[i * self.n_vars + j].setText(
                    self._fmt(coeffs[j])
                )
            self.cons_signs[i].setCurrentText(sign)
            self.cons_b_inputs[i].setText(self._fmt(rhs))

    @staticmethod
    def _fmt(v):
        if float(v).is_integer():
            return str(int(v))
        return str(v)

    # ------------------------------------------------------------------
    def on_solve(self, force_method=None):
        try:
            c = [float(inp.text()) for inp in self.var_inputs]
            objective = self.obj_combo.currentText()
            var_types = [combo.currentData() for combo in self.var_type_combos]

            A = []
            for i in range(self.m_cons):
                row = [float(self.cons_inputs[i * self.n_vars + j].text())
                       for j in range(self.n_vars)]
                A.append(row)

            b = [float(inp.text()) for inp in self.cons_b_inputs]
            signs = [combo.currentText() for combo in self.cons_signs]

            result = solve_problem(
                c, A, b, signs, objective,
                force_method=force_method,
                var_types=var_types
            )

            # --- Специальный случай: доступен двойственный (и/или МИБ) ---
            if result.get("status") in ("dual_available", "dual_available_force"):
                self._show_dual_offer(result)
                return

            self._hide_dual_offer()
            self._show_result(result)

        except ValueError:
            self._hide_dual_offer()
            self.result_output.setText(
                "<span style='color:red; font-size: 18px;'>"
                "Ошибка ввода: убедитесь, что все поля заполнены числами!"
                "</span>"
            )
            self.steps_viewer.clear()
        except Exception as e:
            self._hide_dual_offer()
            self.result_output.setText(
                f"<span style='color:red; font-size: 18px;'>"
                f"Ошибка решения: {e}"
                f"</span>"
            )
            self.steps_viewer.clear()

    # ------------------------------------------------------------------
    def _show_dual_offer(self, result):
        self.result_output.clear()
        status = result.get("status")
        
        if status == "dual_available_force":
            self.result_output.append(
                "<span style='color:#d97706; font-size: 18px;'>"
                "<b>Внимание!</b> Задача имеет b &lt; 0, но также есть Δ &lt; 0.<br><br>"
                "Двойственный симплекс в классическом виде не применим, "
                "но вы можете <b>попробовать</b> запустить его принудительно. "
                "Если алгоритм не сойдётся — используйте <b>МИБ</b>."
                "</span>"
            )
        else:
            self.result_output.append(
                "<span style='color:#49333D; font-size: 18px;'>"
                "<b>Задача двойственно допустима!</b><br><br>"
                "Все Δ_j ≥ 0 и есть b_i &lt; 0. Доступны <b>два пути</b>:<br>"
                "• <b>Двойственный симплекс</b> — без искусственных переменных (рекомендуется).<br>"
                "• <b>МИБ</b> — метод искусственного базиса.<br><br>"
                "Выберите кнопку ниже."
                "</span>"
            )
            
        self.steps_viewer.show_steps(result.get("steps", []))

        if self.dual_btn:
            self.dual_btn.setVisible(True)
        if self.mib_btn:
            self.mib_btn.setVisible(True)

    def _hide_dual_offer(self):
        if self.dual_btn:
            self.dual_btn.setVisible(False)
        if self.mib_btn:
            self.mib_btn.setVisible(False)

    def _show_result(self, result):
        self.result_output.clear()
        
        # Увеличенный шрифт для всего блока результата
        self.result_output.append(
            f"<div style='font-size: 18px;'>"
            f"<b>Статус:</b> {result.get('status')}<br>"
            f"<b>Сообщение:</b> {result.get('message')}<br>"
        )

        if result.get("solution") is not None:
            sol_str = ", ".join([f"{x:g}" for x in result["solution"]])
            self.result_output.append(
                f"<b>Решение (x):</b> {sol_str}<br>"
            )
            obj_val = result.get("objective_value")
            if obj_val is not None:
                self.result_output.append(
                    f"<b>Значение функции (f):</b> {obj_val:g}<br>"
                )
        else:
            self.result_output.append(
                "<span style='color:red;'>Оптимальное решение не найдено.</span>"
            )
        
        self.result_output.append("</div>")

        self.steps_viewer.show_steps(result.get("steps", []))