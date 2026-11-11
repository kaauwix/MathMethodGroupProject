from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QComboBox, QScrollArea,
    QFrame, QSpinBox, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt
from MethodSelection import solve_problem

class SimplexPage(QWidget):
    def __init__(self):
        super().__init__()
        self.n_vars = 2  # По умолчанию 2 переменные
        self.m_cons = 2  # По умолчанию 2 ограничения
        
        self.var_inputs = []      # Для коэффициентов целевой функции
        self.cons_inputs = []     # Для коэффициентов ограничений
        self.cons_signs = []      # Для знаков ограничений
        self.cons_b_inputs = []   # Для правых частей (b)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # ==========================================
        # БЛОК 1: НАСТРОЙКА РАЗМЕРНОСТИ
        # ==========================================
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

        # ==========================================
        # БЛОК 2: ПРОКРУЧИВАЕМАЯ ОБЛАСТЬ ДЛЯ ВВОДА
        # ==========================================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)
        
        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, 1) # 1 - чтобы занимало всё свободное место

        # ==========================================
        # БЛОК 3: РЕЗУЛЬТАТ
        # ==========================================
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setMaximumHeight(200)
        main_layout.addWidget(QLabel("<b>Результат решения:</b>"))
        main_layout.addWidget(self.result_output)

        # Первичная отрисовка
        self.rebuild_ui()

    def rebuild_ui(self):
        """Перерисовывает поля ввода при изменении размерности"""
        self.n_vars = self.n_vars_spin.value()
        self.m_cons = self.m_cons_spin.value()

        # Очищаем старые виджеты
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.var_inputs.clear()
        self.cons_inputs.clear()
        self.cons_signs.clear()
        self.cons_b_inputs.clear()

        # --- Блок целевой функции ---
        obj_group = QGroupBox("Целевая функция")
        obj_layout = QHBoxLayout()
        obj_layout.setAlignment(Qt.AlignLeft)

        self.obj_combo = QComboBox()
        self.obj_combo.addItems(["max", "min"])
        obj_layout.addWidget(QLabel("f(x) ="))
        obj_layout.addWidget(self.obj_combo)
        obj_layout.addWidget(QLabel(":")) # Просто для вида

        for i in range(self.n_vars):
            if i > 0:
                obj_layout.addWidget(QLabel("+"))
            
            inp = QLineEdit()
            inp.setFixedWidth(60)
            inp.setAlignment(Qt.AlignCenter)
            inp.setText("0")
            self.var_inputs.append(inp)
            obj_layout.addWidget(inp)
            
            # Красивая метка x_1, x_2
            lbl = QLabel(f"x<sub>{i+1}</sub>")
            lbl.setStyleSheet("font-size: 20px;")
            obj_layout.addWidget(lbl)

        obj_layout.addStretch()
        obj_group.setLayout(obj_layout)
        self.scroll_layout.addWidget(obj_group)

        # --- Блок ограничений ---
        cons_group = QGroupBox("Ограничения")
        cons_layout = QVBoxLayout()

        for i in range(self.m_cons):
            row_layout = QHBoxLayout()
            row_layout.setAlignment(Qt.AlignLeft)
            row_signs = []
            row_b = None

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

            # Выбор знака
            sign_combo = QComboBox()
            sign_combo.addItems(["<=", ">=", "="])
            sign_combo.setFixedWidth(60)
            self.cons_signs.append(sign_combo)
            row_layout.addWidget(sign_combo)

            # Правая часть
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

        # Кнопка "Решить"
        solve_btn = QPushButton("РЕШИТЬ ЗАДАЧУ")
        solve_btn.setObjectName("solveButton")
        solve_btn.setMinimumHeight(50)
        solve_btn.clicked.connect(self.on_solve)
        self.scroll_layout.addWidget(solve_btn)
        self.scroll_layout.addStretch()

    def on_solve(self):
        try:
            # 1. Собираем целевую функцию
            c = [float(inp.text()) for inp in self.var_inputs]
            objective = self.obj_combo.currentText()

            # 2. Собираем ограничения
            A = []
            for i in range(self.m_cons):
                # Берем нужный кусок из плоского списка cons_inputs
                row = [float(self.cons_inputs[i * self.n_vars + j].text()) for j in range(self.n_vars)]
                A.append(row)

            b = [float(inp.text()) for inp in self.cons_b_inputs]
            signs = [combo.currentText() for combo in self.cons_signs]

            # 3. Вызываем решатель
            result = solve_problem(c, A, b, signs, objective)

            # 4. Выводим результат
            self.result_output.clear()
            self.result_output.append(f"<b>Статус:</b> {result.get('status')}")
            self.result_output.append(f"<b>Сообщение:</b> {result.get('message')}")
            
            if result.get('solution') is not None:
                self.result_output.append(f"<b>Решение:</b> {result['solution']}")
                self.result_output.append(f"<b>Значение функции:</b> {result['objective_value']}")
                
        except ValueError as e:
            self.result_output.setText(f"<span style='color:red;'>Ошибка ввода: убедитесь, что все поля заполнены числами!</span>")
        except Exception as e:
            self.result_output.setText(f"<span style='color:red;'>Ошибка решения: {e}</span>")