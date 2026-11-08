from AuxiliaryFun import (
    add_text_step, add_table_step, normalize_problem, find_initial_basis,
    calculate_deltas, pivot_operation, build_tableau, make_result, EPSILON
)


def artificial_basis_simplex(c, A, b, signs, objective="max", max_iterations=1000):
    """
    Решает задачу ЛП методом искусственного базиса.
    Возвращает результат в формате make_result.
    """
    # 1. Приведение к канонической форме
    problem = normalize_problem(c, A, b, signs, objective)
    steps = problem["steps"]
    original_count = problem["original_variables_count"]
    objective_factor = problem["objective_factor"]

    work_c = problem["c"][:]
    work_A = [row[:] for row in problem["A"]]
    work_b = problem["b"][:]
    variable_names = problem["variable_names"][:]

    # 2. Проверка: вдруг базис уже есть
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

    # 3. Добавление искусственных переменных
    n = len(work_c)
    m = len(work_A)
    artificial_indices = []

    for i in range(m):
        # Проверяем, есть ли в строке i единичный столбец
        has_unit = False
        for j in range(len(work_A[i])):
            if abs(work_A[i][j] - 1.0) <= EPSILON:
                # проверяем, что в остальных строках этой колонки нули
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

    # 4. Вспомогательная целевая функция F = -sum(w)
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

    # 5. Итерации вспомогательной задачи
    for iteration in range(1, max_iterations + 1):
        deltas = calculate_deltas(tableau, c_art, basis)
        negative = [j for j, d in enumerate(deltas) if d < -EPSILON and j not in basis]

        if not negative:
            break  # вспомогательная задача решена

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

    # 6. Анализ результата
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

    # 7. Вывод искусственных переменных из базиса
    # Если искусственная переменная осталась в базисе, выводим её
    changed = True
    while changed:
        changed = False
        for i, basic_idx in enumerate(basis):
            if basic_idx in artificial_indices:
                # Ищем ненулевой элемент в строке i среди x-столбцов (не искусственных)
                candidate = None
                for j in range(len(work_c)):
                    if j not in artificial_indices and abs(tableau[i][j]) > EPSILON:
                        candidate = j
                        break
                
                if candidate is not None:
                    # Делаем жорданово преобразование, чтобы вывести w
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
                    # Если строка нулевая, просто удаляем её из таблицы
                    add_text_step(
                        steps, "Удаление лишней строки",
                        f"Строка с {variable_names[basic_idx]} содержит только нули при x_j. Удаляем её."
                    )
                    tableau.pop(i)
                    basis.pop(i)
                    changed = True
                    break

    # 8. Убираем все оставшиеся искусственные столбцы
    # Делаем это один раз в конце, чтобы не путаться с индексами
    if artificial_indices:
        # Удаляем столбцы в обратном порядке (с конца), чтобы индексы не съезжали
        for idx in sorted(artificial_indices, reverse=True):
            for row in tableau:
                row.pop(idx)
            variable_names.pop(idx)
            work_c.pop(idx)
        # Обнуляем список искусственных индексов, так как мы их удалили
        artificial_indices = []

    # 9. Пересчёт оценок по исходной целевой функции
    # Восстанавливаем c для x-переменных (исходные + дополнительные)
    c_original = problem["c"][:]
    # Если после удаления строк длина c_original не совпадает - дополняем нулями
    while len(c_original) < len(work_c):
        c_original.append(0.0)
    c_original = c_original[:len(work_c)]

    # Пересчитываем таблицу под новый базис (если строки удалялись - уже готово)
    add_text_step(steps, "Переход к исходной задаче",
                  "Искусственные переменные выведены. Дальше решаем прямой симплекс-метод.")
    add_table_step(steps, tableau, basis, variable_names, c_original,
                   "Начальная таблица исходной задачи")

    # 10. Запуск прямого симплекс-метода
    from PrimalSimplex import primal_simplex
    # но primal_simplex сам нормализует задачу, поэтому проще продолжить здесь
    for iteration in range(1, max_iterations + 1):
        deltas = calculate_deltas(tableau, c_original, basis)
        negative = [j for j, d in enumerate(deltas) if d < -EPSILON and j not in basis]
        if not negative:
            solution = [0.0] * len(c_original)
            for i, j in enumerate(basis):
                solution[j] = tableau[i][-1]
            original_solution = solution[:original_count]
            obj = sum(problem["original_c"][j] * original_solution[j]
                      for j in range(original_count))
            add_text_step(steps, "Оптимум найден",
                          "Все Delta_j >= 0. Оптимальное решение найдено.",
                          {"solution": original_solution, "objective_value": obj})
            return make_result("optimal", "Оптимальное решение найдено.",
                               steps, solution=original_solution,
                               objective_value=obj, tableau=tableau,
                               basis=basis, deltas=deltas, problem=problem)

        pivot_col = min(negative, key=lambda j: deltas[j])
        ratios = []
        for i in range(len(tableau)):
            coef = tableau[i][pivot_col]
            if coef > EPSILON:
                ratios.append((tableau[i][-1] / coef, i))
        if not ratios:
            message = "Целевая функция не ограничена сверху."
            add_text_step(steps, "Проверка ограниченности", message)
            return make_result("unbounded", message, steps,
                               tableau=tableau, basis=basis,
                               deltas=deltas, problem=problem)
        _, pivot_row = min(ratios, key=lambda item: (item[0], basis[item[1]]))
        pivot_info = {
            "row": pivot_row, "column": pivot_col,
            "value": tableau[pivot_row][pivot_col],
            "entering_variable": variable_names[pivot_col],
            "leaving_variable": variable_names[basis[pivot_row]]
        }
        add_text_step(steps, "Выбор разрешающего элемента",
                      f"Входит {variable_names[pivot_col]}, выходит {variable_names[basis[pivot_row]]}.",
                      pivot_info)
        pivot_operation(tableau, pivot_row, pivot_col)
        basis[pivot_row] = pivot_col
        add_table_step(steps, tableau, basis, variable_names, c_original,
                       f"Итерация {iteration} прямого симплекс-метода",
                       pivot=pivot_info)

    return make_result("iteration_limit", "Превышено число итераций.",
                       steps, tableau=tableau, basis=basis,
                       deltas=calculate_deltas(tableau, c_original, basis),
                       problem=problem)