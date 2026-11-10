#Двойственный симплекс
from AuxiliaryFun import add_text_step, add_table_step, calculate_deltas, pivot_operation, recover_solution, make_result, EPSILON

def dual_simplex_prepared(problem, tableau, basis, max_iterations=1000):
    """
    Решает уже подготовленную задачу двойственным симплекс-методом.
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

    # Сохраняем начальную таблицу.
    add_table_step(steps, tableau, basis, names, c, "Начальная симплексная таблица")

    # Проверяем условия применения двойственного метода.
    deltas = calculate_deltas(tableau, c, basis)

    if any(delta < -EPSILON for delta in deltas):
        message = "Есть отрицательные оценки Delta_j. Двойственный симплекс-метод применить нельзя."
        add_text_step(steps, "Проверка условий метода", message)
        return make_result("dual_simplex_not_applicable", message, steps, tableau=tableau, basis=basis, deltas=deltas, problem=problem)

    if not any(row[-1] < -EPSILON for row in tableau):
        message = "Все свободные члены неотрицательны. Двойственный симплекс-метод не требуется."
        add_text_step(steps, "Проверка условий метода", message)
        return make_result("dual_simplex_not_applicable", message, steps, tableau=tableau, basis=basis, deltas=deltas, problem=problem)

    add_text_step(steps, "Начало двойственного симплекс-метода", "Все оценки Delta_j неотрицательны, но имеются отрицательные свободные члены. Начинаем итерации.")

    # ОСНОВНОЙ ЦИКЛ ИТЕРАЦИЙ
    for iteration in range(1, max_iterations + 1):

        deltas = calculate_deltas(tableau, c, basis)

        # 1. Ищем отрицательные свободные члены.
        negative_b = [i for i, row in enumerate(tableau) if row[-1] < -EPSILON]

        # 2. Проверяем допустимость решения.
        if not negative_b:
            add_text_step(steps, "Проверка допустимости решения", "Все свободные члены b_i неотрицательны. Допустимый оптимальный план найден.")

            # Восстанавливаем значения переменных.
            all_values = recover_solution(tableau, basis, len(c))
            # Оставляем только исходные переменные.
            solution = all_values[:original_count]
            # Вычисляем значение исходной целевой функции.
            objective_value = sum(original_c[j] * solution[j] for j in range(original_count))

            add_text_step(
                steps, "Получение оптимального решения", "Выписываем значения исходных переменных и вычисляем значение целевой функции.",
                {"solution": solution[:], "objective_value": objective_value}
            )

            return make_result("optimal", "Оптимальное решение найдено.", steps,
                solution, objective_value, tableau, basis, deltas, problem, all_variables=all_values)

        # 3. Выбираем ведущую строку. Берём строку с наиболее отрицательным b.
        pivot_row = min(negative_b, key=lambda i: tableau[i][-1])
        add_text_step(steps, "Выбор ведущей строки", f"Выбираем строку {pivot_row + 1}, так как её свободный член b = {tableau[pivot_row][-1]:.6g} является наиболее отрицательным.")

        # 4. Выбираем ведущий столбец. Учитываем только отрицательные коэффициенты в выбранной строке.
        ratios = []
        for j, delta in enumerate(deltas):
            # Базисные столбцы не рассматриваем.
            if j in basis:
                continue
            coefficient = tableau[pivot_row][j]
            if coefficient < -EPSILON:
                ratio = delta / (-coefficient)
                ratios.append((ratio, j))
                add_text_step(steps, f"Расчёт отношения для столбца {names[j]}", f"theta = {delta:.6g} / ({-coefficient:.6g}) = {ratio:.6g}.")
            else:
                add_text_step(steps, f"Проверка столбца {names[j]}", f"Коэффициент {coefficient:.6g} не является отрицательным. Столбец не участвует в выборе ведущего.")

        # 5. Проверяем возможность продолжения.
        if not ratios:
            message = "В выбранной строке нет отрицательных коэффициентов. Допустимое решение получить невозможно."
            add_text_step(steps, "Проверка ведущего столбца", message)
            return make_result("infeasible", message, steps, tableau=tableau, basis=basis, deltas=deltas, problem=problem)

        # Выбираем минимальное неотрицательное отношение.
        _, pivot_column = min(ratios, key=lambda item: (item[0], item[1]))

        # 6. Определяем ведущий элемент.
        pivot_value = tableau[pivot_row][pivot_column]
        leaving_variable = names[basis[pivot_row]]
        entering_variable = names[pivot_column]
        pivot_info = {
            "row": pivot_row, "column": pivot_column, "value": pivot_value,
            "entering_variable": entering_variable, "leaving_variable": leaving_variable
        }

        add_text_step(
            steps, "Выбор ведущего элемента",
            f"Выбираем столбец {entering_variable} с минимальным отношением. Ведущий элемент равен {pivot_value:.6g}. "
            f"Переменная {entering_variable} входит в базис, а {leaving_variable} выходит из базиса.",
            pivot_info
        )

        # 7. Пересчитываем таблицу.
        add_text_step(steps, "Пересчёт симплексной таблицы", "Ведущую строку делим на ведущий элемент. Остальные элементы пересчитываем по правилу прямоугольника.")
        pivot_operation(tableau, pivot_row, pivot_column)

        # 8. Обновляем базис.
        basis[pivot_row] = pivot_column
        add_text_step(steps, "Обновление базиса", f"Новый базис: {', '.join(names[index] for index in basis)}.")

        # 9. Сохраняем новую таблицу.
        add_table_step(steps, tableau, basis, names, c, f"Таблица после итерации {iteration}", pivot_info)

        # 10. Проверяем сохранение двойственной допустимости.
        deltas = calculate_deltas(tableau, c, basis)
        if any(delta < -EPSILON for delta in deltas):
            message = "После преобразования появились отрицательные оценки. Условие двойственной допустимости нарушено."
            add_text_step(steps, "Проверка двойственной допустимости", message)
            return make_result("dual_feasibility_lost", message, steps, tableau=tableau, basis=basis, deltas=deltas, problem=problem)

    # ПРЕВЫШЕНО КОЛИЧЕСТВО ИТЕРАЦИЙ
    message = "Превышено максимальное количество итераций."
    add_text_step(steps, "Остановка алгоритма", message)
    return make_result("iteration_limit", message, steps, tableau=tableau, basis=basis, deltas=calculate_deltas(tableau, c, basis), problem=problem)