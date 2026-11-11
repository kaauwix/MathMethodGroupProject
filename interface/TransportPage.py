from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QSplitter, QMessageBox, QTextEdit, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from TransportSolver import solve_transport


class TransportPage(QWidget):
    def __init__(self):
        super().__init__()
        self.m = 2 
        self.n = 2 
        self.current_res = None 
        self.init_ui()
        self.load_example()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ==========================================
        # БЛОК 1: НАСТРОЙКА РАЗМЕРНОСТИ
        # ==========================================
        size_group = QGroupBox("Размерность задачи")
        size_layout = QHBoxLayout()

        size_layout.addWidget(QLabel("Поставщики (A):"))
        self.spin_m = QSpinBox()
        self.spin_m.setRange(1, 10)
        self.spin_m.setValue(self.m)
        self.spin_m.valueChanged.connect(self.rebuild_input_table)
        size_layout.addWidget(self.spin_m)

        size_layout.addWidget(QLabel("Потребители (B):"))
        self.spin_n = QSpinBox()
        self.spin_n.setRange(1, 10)
        self.spin_n.setValue(self.n)
        self.spin_n.valueChanged.connect(self.rebuild_input_table)
        size_layout.addWidget(self.spin_n)

        size_group.setLayout(size_layout)
        main_layout.addWidget(size_group)

        # ==========================================
        # БЛОК 2: СПЛИТТЕР
        # ==========================================
        splitter = QSplitter(Qt.Vertical)

        # --- Таблица ввода ---
        self.input_table = QTableWidget()
        self.input_table.setAlternatingRowColors(True)
        self.input_table.setFont(QFont("Arial", 14))
        
        # Исправляем баг невидимого текста при редактировании
        self.input_table.setStyleSheet("""
            QTableWidget {
                selection-background-color: #F4D6E3;
                selection-color: #49333D;
            }
        """)
        
        splitter.addWidget(self.input_table)

        # --- Нижняя часть ---
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        controls_layout = QHBoxLayout()
        self.method_combo = QComboBox()
        self.method_combo.addItem("Метод наименьшей стоимости", "least_cost")
        self.method_combo.addItem("Метод северо-западного угла", "nw")
        
        controls_layout.addWidget(QLabel("Начальный план:"))
        controls_layout.addWidget(self.method_combo)
        
        solve_btn = QPushButton("РЕШИТЬ")
        solve_btn.setObjectName("solveButton")
        solve_btn.setMinimumHeight(40)
        solve_btn.clicked.connect(self.on_solve)
        controls_layout.addWidget(solve_btn)
        
        self.toggle_info_btn = QPushButton("Показать/Скрыть подробности шага")
        self.toggle_info_btn.setStyleSheet("background-color: #F4D6E3; color: #49333D; border: 1px solid #EBC6D7; border-radius: 5px; padding: 5px;")
        self.toggle_info_btn.clicked.connect(self.toggle_info_visibility)
        controls_layout.addWidget(self.toggle_info_btn)
        
        bottom_layout.addLayout(controls_layout)

        # Предупреждение о фиктивном узле
        self.dummy_label = QLabel("")
        self.dummy_label.setStyleSheet("color: #d97706; font-weight: bold; font-size: 14px; padding: 5px;")
        self.dummy_label.setVisible(False)
        bottom_layout.addWidget(self.dummy_label)

        iter_layout = QHBoxLayout()
        self.iter_combo = QComboBox()
        self.iter_combo.currentIndexChanged.connect(self.display_iteration)
        iter_layout.addWidget(QLabel("<b>Выберите итерацию:</b>"))
        iter_layout.addWidget(self.iter_combo)
        iter_layout.addStretch()
        bottom_layout.addLayout(iter_layout)

        # --- Таблица вывода (результат) ---
        self.output_table = QTableWidget()
        self.output_table.setFont(QFont("Arial", 14)) 
        self.output_table.setEditTriggers(QTableWidget.NoEditTriggers) 
        self.output_table.setAlternatingRowColors(True)
        self.output_table.verticalHeader().setDefaultSectionSize(65) 
        bottom_layout.addWidget(self.output_table)

        # --- Текстовый вывод (скрываемый) ---
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.setFont(QFont("Arial", 14)) 
        self.info_text.setStyleSheet("background-color: #FFF8FB; border: 1px solid #EBC6D7; padding: 5px;")
        self.info_text.setVisible(False) 
        bottom_layout.addWidget(self.info_text)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([200, 600]) 
        main_layout.addWidget(splitter, 1)

        self.rebuild_input_table()

    # ------------------------------------------------------------------
    def load_example(self):
        self.spin_m.setValue(2)
        self.spin_n.setValue(2)
        self.rebuild_input_table()

        costs = [
            [4.0, 1.0],
            [2.0, 3.0],
        ]
        a = [30.0, 20.0]
        b = [20.0, 30.0]

        for i in range(self.m):
            for j in range(self.n):
                self.input_table.item(i, j).setText(self._fmt(costs[i][j]))
            self.input_table.item(i, self.n).setText(self._fmt(a[i]))

        for j in range(self.n):
            self.input_table.item(self.m, j).setText(self._fmt(b[j]))

    @staticmethod
    def _fmt(v):
        if float(v).is_integer():
            return str(int(v))
        return str(v)

    # ------------------------------------------------------------------
    def toggle_info_visibility(self):
        self.info_text.setVisible(not self.info_text.isVisible())

    def rebuild_input_table(self):
        self.m = self.spin_m.value()
        self.n = self.spin_n.value()

        self.input_table.setRowCount(self.m + 1)
        self.input_table.setColumnCount(self.n + 1)

        headers_h = [f"B{j+1}" for j in range(self.n)] + ["Запас"]
        self.input_table.setHorizontalHeaderLabels(headers_h)
        headers_v = [f"A{i+1}" for i in range(self.m)] + ["Потребность"]
        self.input_table.setVerticalHeaderLabels(headers_v)

        for i in range(self.m + 1):
            for j in range(self.n + 1):
                item = QTableWidgetItem()
                if i == self.m and j == self.n:
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setBackground(QColor("#EBC6D7")) 
                else:
                    item.setText("0")
                    item.setTextAlignment(Qt.AlignCenter)
                    if i == self.m or j == self.n:
                        item.setBackground(QColor("#F4D6E3")) 
                self.input_table.setItem(i, j, item)

        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.input_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def on_solve(self):
        try:
            c_matrix = [[float(self.input_table.item(i, j).text()) for j in range(self.n)] for i in range(self.m)]
            a = [float(self.input_table.item(i, self.n).text()) for i in range(self.m)]
            b = [float(self.input_table.item(self.m, j).text()) for j in range(self.n)]
            method = self.method_combo.currentData()

            self.current_res = solve_transport(c_matrix, a, b, init_method=method)

            # Показываем предупреждение, если был добавлен фиктивный узел
            if self.current_res.get("dummy_info"):
                self.dummy_label.setText(f"⚠ {self.current_res['dummy_info']}")
                self.dummy_label.setVisible(True)
            else:
                self.dummy_label.setVisible(False)

            self.iter_combo.blockSignals(True)
            self.iter_combo.clear()
            for idx in range(len(self.current_res["iterations"])):
                self.iter_combo.addItem(f"Итерация {idx}")
            self.iter_combo.setCurrentIndex(len(self.current_res["iterations"]) - 1)
            self.iter_combo.blockSignals(False)
            
            self.display_iteration(self.iter_combo.currentIndex())

        except ValueError:
            QMessageBox.warning(self, "Ошибка ввода", "Убедитесь, что все ячейки заполнены числами!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка решения", f"Произошла ошибка:\n{str(e)}")

    def make_custom_cell(self, cost, val, is_basic):
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        
        lbl_top = QLabel(str(cost))
        lbl_top.setAlignment(Qt.AlignRight | Qt.AlignTop)
        lbl_top.setStyleSheet("font-weight: bold; color: #49333D; font-size: 14px;")
        layout.addWidget(lbl_top, 0, 0)
        
        val_str = f"{val:g}" if val > 1e-9 else "0"
        color_bottom = "#CB6892"
        font_weight = "bold" if is_basic else "normal"
        
        lbl_bottom = QLabel(val_str)
        lbl_bottom.setAlignment(Qt.AlignCenter)
        lbl_bottom.setStyleSheet(f"color: {color_bottom}; font-weight: {font_weight}; font-size: 15px;")
        layout.addWidget(lbl_bottom, 1, 0)
        
        return widget

    def display_iteration(self, index):
        if not self.current_res or index < 0 or index >= len(self.current_res["iterations"]):
            return

        try:
            state = self.current_res["iterations"][index]
            m = self.current_res["m"]
            n = self.current_res["n"]
            c = self.current_res["c"]
            a = self.current_res["a"]
            b = self.current_res["b"]
            
            x = state["x"]
            basic = state["basic"]
            u = state.get("u")
            v = state.get("v")

            self.output_table.setRowCount(m + 2)
            self.output_table.setColumnCount(n + 2)

            headers_h = [f"B{j+1}" for j in range(n)] + ["Запас", "u_i"]
            self.output_table.setHorizontalHeaderLabels(headers_h)
            headers_v = [f"A{i+1}" for i in range(m)] + ["Спрос", "v_j"]
            self.output_table.setVerticalHeaderLabels(headers_v)

            for i in range(m + 2):
                for j in range(n + 2):
                    
                    if i == m + 1 and j == n + 1:
                        self.output_table.setItem(i, j, QTableWidgetItem(""))
                        continue
                    
                    if j == n + 1 and i < m:
                        val = f"{u[i]:g}" if (u and i < len(u) and u[i] is not None) else ""
                        item = QTableWidgetItem(val)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.output_table.setItem(i, j, item)
                        continue
                    
                    if i == m + 1 and j < n:
                        val = f"{v[j]:g}" if (v and j < len(v) and v[j] is not None) else ""
                        item = QTableWidgetItem(val)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.output_table.setItem(i, j, item)
                        continue
                    
                    if j == n and i < m:
                        item = QTableWidgetItem(f"{a[i]:g}")
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QColor("#F4D6E3"))
                        self.output_table.setItem(i, j, item)
                        continue
                    
                    if i == m and j < n:
                        item = QTableWidgetItem(f"{b[j]:g}")
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QColor("#F4D6E3"))
                        self.output_table.setItem(i, j, item)
                        continue
                    
                    if i < m and j < n:
                        cost = c[i][j]
                        val = x[i][j]
                        is_basic = (i, j) in basic
                        
                        widget = self.make_custom_cell(cost, val, is_basic)
                        self.output_table.setCellWidget(i, j, widget)

            header = self.output_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            header.setSectionResizeMode(n + 1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(n, QHeaderView.ResizeToContents)
            self.output_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

            z_val = sum(c[i][j] * x[i][j] for i in range(m) for j in range(n))
            info_text = f"<b>Стоимость перевозок (Z):</b> {z_val:.2f}<br>"
            
            if not state.get("enter"):
                info_text += "<b>Статус:</b> <span style='color:green;'>План ОПТИМАЛЬНЫЙ ✓</span>. Все оценки (дельта) >= 0."
            else:
                enter = state["enter"]
                leave = state["leave"]
                theta = state["theta"]
                info_text += f"<b>Действие:</b> Входит A{enter[0]+1}-B{enter[1]+1}, Выходит A{leave[0]+1}-B{leave[1]+1}.<br>"
                info_text += f"<b>Объем перераспределения (θ):</b> {theta:g}"
                
            self.info_text.setHtml(info_text)
            
        except Exception as e:
            self.info_text.setText(f"Ошибка отрисовки итерации: {str(e)}")