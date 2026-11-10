#Метод искусственного базиса
from AuxiliaryFun import add_text_step, add_table_step, find_initial_basis, calculate_deltas, pivot_operation, build_tableau, make_result, EPSILON

def artificial_basis_prepared(problem, max_iterations=1000):
    steps = problem["steps"]
    work_A = [row[:] for row in problem["A"]]
    work_b = problem["b"][:]
    variable_names = problem["variable_names"][:]
    work_c = problem["c"][:]

    # 1. Делаем свободные члены неотрицательными
    changed_rows = []
    for i in range(len(work_b)):
        if work_b[i] < -EPSILON:
            work_A[i] = [-value for value in work_A[i]]
            work_b[i] *= -1
            changed_rows.append(i + 1)

    if changed_rows:
        add_text_step(steps, "Преобразование ограничений", f"Строки {changed_rows} умножены на -1, чтобы свободные члены стали неотрицательными.")

    # 2. Определяем строки, в которых нет единичного базисного столбца
    unit_rows = set()
    for j in range(len(work_A[0])):
        ones = [i for i in range(len(work_A)) if abs(work_A[i][j] - 1.0) <= EPSILON]
        if len(ones) != 1:
            continue
        row_index = ones[0]
        if all(abs(work_A[i][j]) <= EPSILON for i in range(len(work_A)) if i != row_index):
            unit_rows.add(row_index)

    missing_rows = [i for i in range(len(work_A)) if i not in unit_rows]

    # 3. Добавляем искусственные переменные
    artificial_indices = []
    for row_index in missing_rows:
        for i in range(len(work_A)):
            work_A[i].append(1.0 if i == row_index else 0.0)
        work_c.append(0.0)
        variable_names.append(f"w{len(artificial_indices) + 1}")
        artificial_indices.append(len(work_c) - 1)

    basis = find_initial_basis(work_A)
    if basis is None:
        message = "Не удалось сформировать начальный базис для метода искусственного базиса."
        return make_result("basis_error", message, steps, problem=problem)

    # 4. Формируем вспомогательную целевую функцию
    c_art = [0.0] * len(work_c)
    for index in artificial_indices:
        c_art[index] = -1.0

    tableau = build_tableau(work_A, work_b)
    add_text_step(steps, "Вспомогательная задача", f"Добавлены искусственные переменные: {[variable_names[i] for i in artificial_indices]}. Решаем F = -sum(w) -> max.")
    add_table_step(steps, tableau, basis, variable_names, c_art, "Начальная таблица вспомогательной задачи")

    # 5. Первая фаза: минимизируем сумму искусственных переменных
    phase_one_finished = False
    for iteration in range(1, max_iterations + 1):
        deltas = calculate_deltas(tableau, c_art, basis)
        candidates = [j for j, delta in enumerate(deltas) if delta < -EPSILON and j not in basis]

        if not candidates:
            phase_one_finished = True
            break

        pivot_column = min(candidates, key=lambda j: deltas[j])
        ratios = []
        for i, row in enumerate(tableau):
            coefficient = row[pivot_column]
            if coefficient > EPSILON:
                ratios.append((row[-1] / coefficient, i))

        if not ratios:
            message = "Не удалось выполнить вспомогательную задачу."
            return make_result("phase_one_failed", message, steps, tableau=tableau, basis=basis, deltas=deltas, problem=problem)

        _, pivot_row = min(ratios, key=lambda item: (item[0], basis[item[1]]))
        pivot_info = {
            "row": pivot_row, "column": pivot_column, "value": tableau[pivot_row][pivot_column],
            "entering_variable": variable_names[pivot_column], "leaving_variable": variable_names[basis[pivot_row]]
        }

        add_text_step(steps, "Выбор разрешающего элемента", f"Входит {variable_names[pivot_column]}, выходит {variable_names[basis[pivot_row]]}.", pivot_info)
        pivot_operation(tableau, pivot_row, pivot_column)
        basis[pivot_row] = pivot_column
        add_table_step(steps, tableau, basis, variable_names, c_art, f"Таблица вспомогательной задачи после итерации {iteration}", pivot=pivot_info)

    if not phase_one_finished:
        message = "Достигнуто максимальное количество итераций первой фазы."
        return make_result("iteration_limit", message, steps, tableau=tableau, basis=basis, deltas=calculate_deltas(tableau, c_art, basis), problem=problem)

    # 6. Проверяем результат первой фазы
    F_value = sum(c_art[basis[i]] * tableau[i][-1] for i in range(len(basis)))
    add_text_step(steps, "Результат вспомогательной задачи", f"Получено F = {F_value}.")

    if F_value < -EPSILON:
        message = "Вспомогательная задача дала отрицательное значение F. Система ограничений несовместна."
        add_text_step(steps, "Вывод", message)
        return make_result("infeasible", message, steps, tableau=tableau, basis=basis, deltas=calculate_deltas(tableau, c_art, basis), problem=problem)

    # 7. Удаляем искусственные переменные из базиса
    i = 0
    while i < len(basis):
        if basis[i] not in artificial_indices:
            i += 1
            continue

        candidate = next((j for j in range(len(work_c)) if j not in artificial_indices and abs(tableau[i][j]) > EPSILON), None)

        if candidate is not None:
            pivot_info = {
                "row": i, "column": candidate, "value": tableau[i][candidate],
                "entering_variable": variable_names[candidate], "leaving_variable": variable_names[basis[i]]
            }
            add_text_step(steps, "Удаление искусственной переменной", f"Вводим {variable_names[candidate]} вместо {variable_names[basis[i]]}.", pivot_info)
            pivot_operation(tableau, i, candidate)
            basis[i] = candidate
            add_table_step(steps, tableau, basis, variable_names, problem["c"] + [0.0] * len(artificial_indices), "Таблица после удаления искусственной переменной", pivot=pivot_info)
            i += 1

        elif abs(tableau[i][-1]) <= EPSILON:
            add_text_step(steps, "Удаление лишнего ограничения", "Строка не содержит коэффициентов исходных переменных и имеет нулую правую часть. Удаляем её.")
            tableau.pop(i)
            basis.pop(i)

        else:
            message = "Не удалось удалить искусственную переменную из базиса."
            return make_result("basis_error", message, steps, tableau=tableau, basis=basis, problem=problem)

    # 8. Удаляем искусственные столбцы
    for index in sorted(artificial_indices, reverse=True):
        for row in tableau:
            row.pop(index)
        variable_names.pop(index)
        work_c.pop(index)

    # 9. Переходим к исходной целевой функции
    add_text_step(steps, "Переход к исходной задаче", "Искусственные переменные удалены. Продолжаем решение прямым симплекс-методом.")
    add_table_step(steps, tableau, basis, variable_names, problem["c"], "Начальная таблица исходной задачи")

    # 10. Вторая фаза
    from PrimalSimplex import primal_simplex_prepared
    return primal_simplex_prepared(problem, tableau, basis, max_iterations)