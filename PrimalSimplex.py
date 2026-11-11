#Прямой симплекс
from AuxiliaryFun import add_text_step, add_table_step, normalize_problem, find_initial_basis, calculate_deltas, determine_method, pivot_operation, build_tableau, recover_solution, make_result, EPSILON

def primal_simplex_prepared(problem, tableau, basis, max_iterations=1000):
    """
    Решает уже подготовленную задачу прямым симплекс-методом.
    problem — нормализованная задача;
    tableau — начальная симплексная таблица;
    basis — начальный базис;
    max_iterations — максимальное количество итераций.
    """
    c = problem["c"]
    names = problem["variable_names"]
    steps = problem["steps"]
    original_count = problem["original_variables_count"]
    original_c = problem["original_c"]

    # Сохраняем начальную симплексную таблицу.
    add_table_step(steps, tableau, basis, names, c, "Начальная симплексная таблица")

    # Проверяем возможность применения прямого симплекс-метода.
    method_info = determine_method(tableau, c, basis)
    add_text_step(steps, "Проверка начального плана", method_info["message"])

    if method_info["method"] not in ("primal_simplex", "optimal"):
        return make_result(
            method_info["method"], method_info["message"], steps,
            tableau=tableau, basis=basis, deltas=calculate_deltas(tableau, c, basis), problem=problem
        )

    add_text_step(steps, "Начало прямого симплекс-метода", "Начальный план допустим. Переходим к проверке критерия оптимальности.")

    # ОСНОВНОЙ ЦИКЛ ИТЕРАЦИЙ
    for iteration in range(1, max_iterations + 1):

        # 1. Вычисляем оценки Delta_j = Z_j - C_j.
        deltas = calculate_deltas(tableau, c, basis)
        add_text_step(steps, f"Итерация {iteration}. Вычисление оценок", "Вычисляем оценки всех столбцов по формуле Delta_j = Z_j - C_j.")

        # 2. Проверяем критерий оптимальности. Для задачи на максимум все оценки должны быть >= 0.
        negative_columns = [j for j, delta in enumerate(deltas) if delta < -EPSILON and j not in basis]

        if not negative_columns:
            add_text_step(steps, "Проверка критерия оптимальности", "Все оценки Delta_j неотрицательны. Оптимальное решение найдено.")

            # Восстанавливаем значения всех переменных.
            all_values = recover_solution(tableau, basis, len(c))
            # Оставляем только исходные переменные x1, x2, ...
            solution = all_values[:original_count]
            # Вычисляем значение исходной целевой функции.
            objective_value = sum(original_c[j] * solution[j] for j in range(original_count))

            add_text_step(steps, "Итоговое решение", "Выписываем значения исходных переменных и вычисляем значение целевой функции.",
                {"solution": solution[:], "objective_value": objective_value})

            return make_result("optimal", "Оптимальное решение найдено.", steps,
                solution, objective_value, tableau, basis, deltas, problem, all_variables=all_values)

        # 3. Выбираем ведущий столбец.
        # Берём столбец с наиболее отрицательной оценкой.
        pivot_column = min(negative_columns, key=lambda j: deltas[j])
        entering_variable = names[pivot_column]

        add_text_step(steps, "Выбор ведущего столбца", f"Выбираем столбец {entering_variable}, так как его оценка Delta = {deltas[pivot_column]:.6g} является наиболее отрицательной.")

        # 4. Выбираем ведущую строку.
        # Используем правило минимального положительного отношения:
        # theta_i = b_i / a_ij, если a_ij > 0.
        ratios = []
        for i, row in enumerate(tableau):
            coefficient = row[pivot_column]
            free_member = row[-1]
            if coefficient > EPSILON:
                ratio = max(0.0, free_member) / coefficient
                ratios.append((ratio, i))
                add_text_step(steps, f"Расчёт отношения для строки {i + 1}", f"theta = {max(0.0, free_member):.6g} / {coefficient:.6g} = {ratio:.6g}.")
            else:
                add_text_step(steps, f"Проверка строки {i + 1}", f"Коэффициент {coefficient:.6g} не является положительным. Строка не участвует в выборе ведущей строки.")

        # 5. Проверяем ограниченность целевой функции.
        if not ratios:
            message = "В ведущем столбце нет положительных элементов. Целевая функция не ограничена сверху."
            add_text_step(steps, "Проверка ограниченности", message)
            return make_result("unbounded", "Целевая функция не ограничена.", steps,
                tableau=tableau, basis=basis, deltas=deltas, problem=problem)

        # Выбираем строку с минимальным отношением.
        _, pivot_row = min(ratios, key=lambda item: (item[0], basis[item[1]]))

        # 6. Определяем ведущий элемент.
        pivot_value = tableau[pivot_row][pivot_column]
        leaving_variable = names[basis[pivot_row]]
        pivot_info = {"row": pivot_row, "column": pivot_column, "value": pivot_value,
            "entering_variable": entering_variable, "leaving_variable": leaving_variable
        }

        add_text_step(
            steps, "Выбор ведущего элемента",
            f"Ведущий элемент находится на пересечении строки {pivot_row + 1} и столбца {entering_variable}. "
            f"Его значение: {pivot_value:.6g}. Переменная {entering_variable} входит в базис, а {leaving_variable} выходит из базиса.",
            pivot_info
        )

        # 7. Пересчитываем симплексную таблицу.
        add_text_step(steps, "Пересчёт симплексной таблицы", "Ведущую строку делим на ведущий элемент. Остальные элементы пересчитываем по правилу прямоугольника.")
        pivot_operation(tableau, pivot_row, pivot_column)

        # 8. Обновляем базис.
        basis[pivot_row] = pivot_column
        add_text_step(steps, "Обновление базиса", f"Новый базисный состав: {', '.join(names[index] for index in basis)}.")

        # 9. Сохраняем новую таблицу.
        add_table_step(steps, tableau, basis, names, c, f"Таблица после итерации {iteration}", pivot_info)

    # ПРЕВЫШЕНО КОЛИЧЕСТВО ИТЕРАЦИЙ
    message = "Превышено максимальное количество итераций."
    add_text_step(steps, "Остановка алгоритма", message)
    return make_result("iteration_limit", message, steps,
        tableau=tableau, basis=basis, deltas=calculate_deltas(tableau, c, basis), problem=problem)