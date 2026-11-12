from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QComboBox, QSpinBox, 
    QCheckBox, QSplitter, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from optimal import check_optimality


class OptimalityPage(QWidget):
    def __init__(self):
        super().__init__()
        self.n_vars = 2
        self.m_cons = 3

        self.var_inputs = []
        self.var_free_checks = [] 
        self.cons_inputs = []
        self.cons_signs = []
        self.cons_b_inputs = []

        self.init_ui()
        self.load_preset_example(0) # Загружаем первый пример при старте

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Выбор шаблона ---
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("<b>Выберите пример:</b>"))
        self.preset_combo = QComboBox()
        
        # ДОБАВЛЕН НОВЫЙ ПРИМЕР СЮДА
        self.preset_combo.addItem("Задача из ДЗ №4")
        self.preset_combo.addItem("Задача из лекции (Оптимальный)")
        self.preset_combo.addItem("Задача на минимум (НЕ оптимальный)")
        self.preset_combo.addItem("Задача со свободной переменной")
        
        self.preset_combo.currentIndexChanged.connect(self.load_preset_example)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        main_layout.addLayout(preset_layout)

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

        # --- СПЛИТТЕР (Ввод + Результат) ---
        splitter = QSplitter(Qt.Vertical)

        # Верхняя часть: Ввод (в скролле)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)
        scroll.setWidget(self.scroll_content)
        
        splitter.addWidget(scroll)

        # Нижняя часть: Результат
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.setContentsMargins(0, 0, 0, 0)
        
        result_layout.addWidget(QLabel("<b>Результат проверки:</b>"))
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        result_layout.addWidget(self.result_output)

        splitter.addWidget(result_widget)
        splitter.setSizes([400, 300]) 

        main_layout.addWidget(splitter, 1)

        self.rebuild_ui()

    def rebuild_ui(self):
        self.n_vars = self.n_vars_spin.value()
        self.m_cons = self.m_cons_spin.value()

        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.var_inputs.clear()
        self.var_free_checks.clear()
        self.cons_inputs.clear()
        self.cons_signs.clear()
        self.cons_b_inputs.clear()

        # --- Целевая функция (ДВЕ СТРОКИ) ---
        obj_group = QGroupBox("Целевая функция")
        obj_main_layout = QVBoxLayout()

        # Строка 1: Сама функция
        func_row = QHBoxLayout()
        func_row.setAlignment(Qt.AlignLeft)

        self.obj_combo = QComboBox()
        self.obj_combo.addItems(["max", "min"])
        func_row.addWidget(QLabel("f(x) ="))
        func_row.addWidget(self.obj_combo)
        func_row.addWidget(QLabel(":"))

        for i in range(self.n_vars):
            if i > 0:
                func_row.addWidget(QLabel("+"))

            inp = QLineEdit()
            inp.setFixedWidth(60)
            inp.setAlignment(Qt.AlignCenter)
            inp.setText("0")
            self.var_inputs.append(inp)
            func_row.addWidget(inp)

            lbl = QLabel(f"x<sub>{i+1}</sub>")
            lbl.setStyleSheet("font-size: 20px;")
            func_row.addWidget(lbl)

        func_row.addStretch()
        obj_main_layout.addLayout(func_row)

        # Строка 2: Галочки (под функцией)
        check_row = QHBoxLayout()
        check_row.setAlignment(Qt.AlignLeft)
        check_row.addWidget(QLabel("<i>Ограничения на переменные:</i>"))
        
        for i in range(self.n_vars):
            spacer = QLabel(f"x<sub>{i+1}</sub>:")
            check_row.addWidget(spacer)
            
            chk = QCheckBox("≥ 0")
            chk.setChecked(True)
            self.var_free_checks.append(chk)
            check_row.addWidget(chk)
            
            if i < self.n_vars - 1:
                check_row.addSpacing(30)

        check_row.addStretch()
        obj_main_layout.addLayout(check_row)
        
        obj_group.setLayout(obj_main_layout)
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

        # --- План ---
        plan_group = QGroupBox("Проверяемый план x")
        plan_layout = QHBoxLayout()
        self.plan_input = QLineEdit()
        self.plan_input.setPlaceholderText("Например: 4, 4")
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
    def load_preset_example(self, index):
        if index == 0:
            # НОВЫЙ ПРИМЕР (со скриншота)
            self.n_vars_spin.setValue(2)
            self.m_cons_spin.setValue(3)
            self.rebuild_ui()

            self.obj_combo.setCurrentText("max")
            self.var_inputs[0].setText("-1")
            self.var_inputs[1].setText("3")
            
            for chk in self.var_free_checks:
                chk.setChecked(True)

            constraints = [
                (3.0, 4.0, "<=", 12.0),
                (-1.0, 1.0, "<=", 3.0),
                (1.0, -1.0, "<=", 1.0),
            ]
            self.plan_input.setText("0, 3")

        elif index == 1:
            # Задача из лекции
            self.n_vars_spin.setValue(2)
            self.m_cons_spin.setValue(3)
            self.rebuild_ui()

            self.obj_combo.setCurrentText("max")
            self.var_inputs[0].setText("-1")
            self.var_inputs[1].setText("2")
            
            for chk in self.var_free_checks:
                chk.setChecked(True)

            constraints = [
                (1.0, -3.0, "<=", 3.0),
                (-1.0, 1.0, "<=", 1.0),
                (-1.0, 2.0, "<=", 4.0),
            ]
            self.plan_input.setText("4, 4")

        elif index == 2:
            # Задача на минимум
            self.n_vars_spin.setValue(2)
            self.m_cons_spin.setValue(2)
            self.rebuild_ui()

            self.obj_combo.setCurrentText("min")
            self.var_inputs[0].setText("2")
            self.var_inputs[1].setText("3")

            for chk in self.var_free_checks:
                chk.setChecked(True)

            constraints = [
                (1.0, 2.0, ">=", 4.0),
                (3.0, 1.0, ">=", 6.0),
            ]
            self.plan_input.setText("2, 1")

        elif index == 3:
            # Задача со свободной переменной
            self.n_vars_spin.setValue(2)
            self.m_cons_spin.setValue(2)
            self.rebuild_ui()

            self.obj_combo.setCurrentText("max")
            self.var_inputs[0].setText("1")
            self.var_inputs[1].setText("1")

            self.var_free_checks[0].setChecked(False)
            self.var_free_checks[1].setChecked(True)

            constraints = [
                (1.0, 1.0, "<=", 4.0),
                (1.0, -1.0, "<=", 2.0),
            ]
            self.plan_input.setText("1, 3")
        else:
            return

        # Заполняем ограничения
        for i, (c1, c2, sign, rhs) in enumerate(constraints):
            self.cons_inputs[i * self.n_vars + 0].setText(self._fmt(c1))
            self.cons_inputs[i * self.n_vars + 1].setText(self._fmt(c2))
            self.cons_signs[i].setCurrentText(sign)
            self.cons_b_inputs[i].setText(self._fmt(rhs))

    @staticmethod
    def _fmt(v):
        if float(v).is_integer():
            return str(int(v))
        return str(v)

    def on_check(self):
        try:
            c = [float(inp.text()) for inp in self.var_inputs]
            
            var_types = ["nonneg" if chk.isChecked() else "free" for chk in self.var_free_checks]

            A = []
            for i in range(self.m_cons):
                row = [float(self.cons_inputs[i * self.n_vars + j].text()) for j in range(self.n_vars)]
                A.append(row)
            b = [float(inp.text()) for inp in self.cons_b_inputs]
            signs = [combo.currentText() for combo in self.cons_signs]

            plan_text = self.plan_input.text().replace(' ', '')
            x = [float(val) for val in plan_text.split(',')]

            if len(x) != self.n_vars:
                raise ValueError(f"В плане должно быть ровно {self.n_vars} чисел.")

            result = check_optimality(c, A, b, x, signs, var_types=var_types)

            self.result_output.clear()
            status = result.get('status')

            if status == 'optimal':
                self.result_output.append("<span style='color:green; font-size:16px;'><b>✔ План ОПТИМАЛЕН</b></span>")
            elif status == 'not_feasible':
                self.result_output.append("<span style='color:red; font-size:16px;'><b>✘ План НЕДОПУСТИМ</b></span>")
            else:
                self.result_output.append("<span style='color:red; font-size:16px;'><b>✘ План НЕ ОПТИМАЛЕН</b></span>")

            self.result_output.append(f"<b>Сообщение:</b> {result.get('message')}")

            if result.get('y') is not None:
                y_str = ", ".join([f"{v:g}" for v in result['y']])
                self.result_output.append(f"<b>Двойственные оценки (y):</b> {y_str}")

            if "steps" in result:
                self.result_output.append("<hr><b>Пошаговый ход решения:</b>")
                for step in result["steps"]:
                    self.result_output.append(f"<br><b>{step['title']}:</b>")
                    self.result_output.append(f"{step['description']}")

        except ValueError as e:
            self.result_output.setText(f"<span style='color:red;'>Ошибка ввода: {e}</span>")
        except Exception as e:
            self.result_output.setText(f"<span style='color:red;'>Ошибка проверки: {e}</span>")