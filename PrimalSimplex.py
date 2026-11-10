# Прямой симплекс-метод
# Все итерации метода находятся в этом файле.
# Результат содержит список steps со всеми этапами решения.

from AuxiliaryFun import (add_text_step, add_table_step, calculate_deltas, recover_solution, pivot_operation, make_result, EPSILON)

# Прямой симплекс-метод для уже подготовленной задачи.
def primal_simplex_prepared(problem, tableau, basis, max_iterations=1000):

    steps = problem["steps"]
    c = problem["c"]
    names = problem["variable_names"]

    add_text_step(steps, "Начало прямого симплекс-метода", "Начальное базисное решение допустимо. Используем оценки Delta_j = Z_j - C_j.")

    # Основной цикл прямого симплекс-метода.
    for iteration in range(1, max_iterations + 1):

        # 1. Вычисление оценок всех переменных.
        deltas = calculate_deltas(tableau, c, basis)

        # 2. Выбор разрешающего столбца.
        # Для задачи максимизации выбираем отрицательную оценку.
        entering = [j for j, delta in enumerate(deltas) if delta < -EPSILON and j not in basis]

        # Если отрицательных оценок нет, решение оптимально.
        if not entering:
            status = "optimal"
            break

        pivot_col = min(entering, key=lambda j: deltas[j])

        # 3. Выбор разрешающей строки.
        # Используем правило минимального положительного отношения.
        ratios = []
        for i in range(len(tableau)):
            coefficient = tableau[i][pivot_col]
            free_member = tableau[i][-1]
            if coefficient > EPSILON:
                ratio = free_member / coefficient
                if ratio >= -EPSILON:
                    ratios.append((max(0.0, ratio), i))

        # Если разрешающей строки нет, целевая функция не ограничена.
        if not ratios:
            status = "unbounded"
            break

        # При равенстве отношений выбираем строку с меньшим индексом базисной переменной.
        _, pivot_row = min(ratios, key=lambda item: (item[0], basis[item[1]]))

        # 4. Сохранение информации о разрешающем элементе.
        pivot_info = {
            "row": pivot_row,
            "column": pivot_col,
            "value": tableau[pivot_row][pivot_col],
            "entering_variable": names[pivot_col],
            "leaving_variable": names[basis[pivot_row]]
        }

        add_text_step(steps, "Выбор разрешающего элемента", f"Входит переменная {names[pivot_col]}, выходит переменная {names[basis[pivot_row]]}.", pivot_info)

        # 5. Преобразование симплексной таблицы методом Жордана — Гаусса.
        pivot_operation(tableau, pivot_row, pivot_col)

        # 6. Обновление базиса.
        basis[pivot_row] = pivot_col

        # 7. Сохранение новой симплексной таблицы.
        add_table_step(steps, tableau, basis, names, c, f"Прямой симплекс-метод: итерация {iteration}", pivot_info)

    else:
        # Достигнуто максимальное количество итераций.
        status = "iteration_limit"
        deltas = calculate_deltas(tableau, c, basis)

    # Обработка найденного оптимального решения.
    if status == "optimal":
        # Восстановление значений всех переменных.
        all_values = recover_solution(tableau, basis, len(c))
        # Выделение исходных переменных.
        x = all_values[:problem["original_variables_count"]]
        # Вычисление исходной целевой функции.
        value = sum(problem["original_c"][j] * x[j] for j in range(len(x)))
        add_text_step(steps, "Получение оптимального решения", "Восстанавливаем исходные переменные и вычисляем значение исходной целевой функции.", {"solution": x[:], "objective_value": value})
        return make_result("optimal", "Оптимальное решение найдено.", steps, x, value, tableau, basis, deltas, problem, all_variables=all_values)

    # Обработка случаев, когда оптимальное решение не найдено.
    if status == "unbounded":
        message = "Целевая функция не ограничена."
    else:
        message = "Превышено максимальное количество итераций."

    return make_result(status, message, steps, tableau=tableau, basis=basis, deltas=deltas, problem=problem)