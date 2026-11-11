#Метод искусственного базиса

from AuxiliaryFun import ( add_text_step, add_table_step, find_initial_basis,
    calculate_deltas, pivot_operation, build_tableau, make_result, EPSILON)

def artificial_basis_prepared(problem, max_iterations=1000):
    """
    Выполняет метод искусственного базиса для уже нормализованной задачи.
    Этапы метода, проверка вспомогательной задачи и удаление искусственных
    переменных остаются такими же, как в исходной реализации.
    """
    steps = problem["steps"]
    original_count = problem["original_variables_count"]
    objective_factor = problem["objective_factor"]

    work_c = problem["c"][:]
    work_A = [row[:] for row in problem["A"]]
    work_b = problem["b"][:]
    variable_names = problem["variable_names"][:]

    # 1. Проверка на базис
    basis = find_initial_basis(work_A)
    if basis is not None:
        add_text_step(
            steps, "Проверка базиса",
            "Единичный базис уже присутствует. Метод искусственного базиса не нужен."
        )
        return make_result(
            "basis_exists",
            "Единичный базис уже есть, используйте прямой симплекс-метод.",
            steps, problem=problem
        )

    # 2. Добавляем искусственные переменные
    n = len(work_c)
    m = len(work_A)
    artificial_indices = []

    for i in range(m):
        has_unit = False
        for j in range(len(work_A[i])):
            if abs(work_A[i][j] - 1.0) <= EPSILON:
                if all(abs(work_A[k][j]) <= EPSILON for k in range(m) if k != i):
                    has_unit = True
                    break
        if not has_unit:
            for row in work_A:
                row.append(0.0)
            work_A[i][-1] = 1.0
            work_c.append(0.0)
            variable_names.append(f"w{len(artificial_indices) + 1}")
            artificial_indices.append(len(variable_names) - 1)

    # 3. Вспомогательная целевая функция F
    c_art = [0.0] * len(work_c)
    for idx in artificial_indices:
        c_art[idx] = -1.0

    tableau = build_tableau(work_A, work_b)
    basis = find_initial_basis(work_A)

    add_text_step(
        steps, "Вспомогательная задача",
        f"Введены искусственные переменные: {[variable_names[i] for i in artificial_indices]}. "
        "Решаем задачу F = -sum(w) -> max."
    )
    add_table_step(steps, tableau, basis, variable_names, c_art,
                   "Начальная таблица вспомогательной задачи")

    # 4. Итерации вспомогательной задачи
    for iteration in range(1, max_iterations + 1):
        deltas = calculate_deltas(tableau, c_art, basis)
        negative = [j for j, d in enumerate(deltas) if d < -EPSILON and j not in basis]

        if not negative:
            break 

        pivot_col = min(negative, key=lambda j: deltas[j])
        ratios = []
        for i in range(len(tableau)):
            coef = tableau[i][pivot_col]
            if coef > EPSILON:
                ratios.append((tableau[i][-1] / coef, i))

        if not ratios:
            message = "Вспомогательная задача не ограничена. Система ограничений противоречива."
            add_text_step(steps, "Проверка ограниченности", message)
            return make_result("infeasible", message, steps,
                               tableau=tableau, basis=basis,
                               deltas=deltas, problem=problem)

        _, pivot_row = min(ratios, key=lambda item: (item[0], basis[item[1]]))
        pivot_info = {
            "row": pivot_row,
            "column": pivot_col,
            "value": tableau[pivot_row][pivot_col],
            "entering_variable": variable_names[pivot_col],
            "leaving_variable": variable_names[basis[pivot_row]]
        }
        add_text_step(
            steps, "Выбор разрешающего элемента",
            f"Входит {variable_names[pivot_col]}, выходит {variable_names[basis[pivot_row]]}.",
            pivot_info
        )
        pivot_operation(tableau, pivot_row, pivot_col)
        basis[pivot_row] = pivot_col
        add_table_step(steps, tableau, basis, variable_names, c_art,
                       f"Таблица вспомогательной задачи после итерации {iteration}",
                       pivot=pivot_info)

    # 5. Анализ результата
    F_value = sum(c_art[j] * tableau[i][-1] for i, j in enumerate(basis))
    add_text_step(steps, "Результат вспомогательной задачи",
                  f"max F = {F_value}.")

    if F_value < -EPSILON:
        message = "max F < 0. Система ограничений противоречива, задача не имеет допустимых решений."
        add_text_step(steps, "Вывод", message)
        return make_result("infeasible", message, steps,
                           tableau=tableau, basis=basis,
                           deltas=calculate_deltas(tableau, c_art, basis),
                           problem=problem)

    # 6. Вывод искусственных переменных из базиса
    changed = True
    while changed:
        changed = False
        for i, basic_idx in enumerate(basis):
            if basic_idx in artificial_indices:
                candidate = None
                for j in range(len(work_c)):
                    if j not in artificial_indices and abs(tableau[i][j]) > EPSILON:
                        candidate = j
                        break
                
                if candidate is not None:
                    pivot_info = {
                        "row": i, "column": candidate,
                        "value": tableau[i][candidate],
                        "entering_variable": variable_names[candidate],
                        "leaving_variable": variable_names[basic_idx]
                    }
                    add_text_step(
                        steps, "Вывод искусственной переменной",
                        f"Выводим {variable_names[basic_idx]} из базиса, вводим {variable_names[candidate]}.",
                        pivot_info
                    )
                    pivot_operation(tableau, i, candidate)
                    basis[i] = candidate
                    add_table_step(steps, tableau, basis, variable_names, c_art,
                                   "Таблица после вывода искусственной переменной")
                    changed = True
                    break
                else:
                    add_text_step(
                        steps, "Удаление лишней строки",
                        f"Строка с {variable_names[basic_idx]} содержит только нули при x_j. Удаляем её."
                    )
                    tableau.pop(i)
                    basis.pop(i)
                    changed = True
                    break

    # 7. Убираем все оставшиеся искусственные столбцы
    if artificial_indices:
        for idx in sorted(artificial_indices, reverse=True):
            for row in tableau:
                row.pop(idx)
            variable_names.pop(idx)
            work_c.pop(idx)
        artificial_indices = []

    # 8. Пересчёт оценок по исходной целевой функции
    c_original = problem["c"][:]
    while len(c_original) < len(work_c):
        c_original.append(0.0)
    c_original = c_original[:len(work_c)]

    add_text_step(steps, "Переход к исходной задаче",
                  "Искусственные переменные выведены. Дальше решаем прямой симплекс-метод.")
    add_table_step(steps, tableau, basis, variable_names, c_original,
                   "Начальная таблица исходной задачи")

    # 9. Запуск прямого симплекс-метода
    from PrimalSimplex import primal_simplex_prepared

    return primal_simplex_prepared(problem, tableau, basis, max_iterations)