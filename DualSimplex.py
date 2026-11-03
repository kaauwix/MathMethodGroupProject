# Двойственный симплекс-метод
# Результат содержит список steps со всеми этапами решения

from AuxiliaryFun import (add_text_step, add_table_step, normalize_problem, find_initial_basis, calculate_deltas,
    pivot_operation, build_tableau, make_result, EPSILON)


def dual_simplex(c, A, b, signs, objective="max", max_iterations=1000):
    # Приведение исходной задачи к стандартному виду
    problem = normalize_problem(c, A, b, signs, objective)
    steps = problem["steps"]
    original_count = problem["original_variables_count"]
    objective_factor = problem["objective_factor"]

    work_A = [row[:] for row in problem["original_A"]]
    work_b = problem["original_b"][:]

    # Берём только коэффициенты исходных переменных.
    # Дополнительные переменные добавим самостоятельно ниже.
    work_c = problem["c"][:original_count]

    variable_names = [f"x{i + 1}" for i in range(original_count)]

    for i, sign in enumerate(problem["signs"]):
        if sign == ">=":
            work_A[i] = [-value for value in work_A[i]]
            work_b[i] = -work_b[i]

        if sign in ("<=", ">="):
            for row in work_A:
                row.append(0.0)
            work_A[i][-1] = 1.0
            work_c.append(0.0)
            variable_names.append(f"x{len(variable_names) + 1}")

    add_text_step(
        steps,
        "Подготовка начальной таблицы",
        "Ограничения >= умножены на -1. К неравенствам добавлены дополнительные "
        "переменные со знаком +1. Отрицательные свободные члены сохранены."
    )

    # Формирование начальной симплексной таблицы
    tableau = build_tableau(work_A, work_b)
    basis = find_initial_basis(work_A)

    if basis is None:
        message = (
            "Не удалось сформировать начальный единичный базис. "
            "Для этой задачи требуется метод искусственного базиса."
        )
        add_text_step(
            steps,
            "Формирование начального базиса",
            message
        )
        return make_result(
            "artificial_basis_required",
            message,
            steps,
            tableau=tableau,
            problem=problem
        )

    add_text_step(
        steps,
        "Формирование начального базиса",
        "Начальный единичный базис сформирован.",
        {
            "basis": basis[:],
            "basis_names": [variable_names[j] for j in basis]
        }
    )
    add_table_step(
        steps,
        tableau,
        basis,
        variable_names,
        work_c,
        "Начальная симплексная таблица"
    )

    # Проверка знаков свободных членов и оценок
    deltas = calculate_deltas(tableau, work_c, basis)
    negative_b = [i for i, row in enumerate(tableau) if row[-1] < -EPSILON]
    negative_delta = [j for j, value in enumerate(deltas) if value < -EPSILON]

    # Если одновременно отрицательны b и Delta, выполняем замену переменных
    if negative_b and negative_delta:
        add_text_step(
            steps,
            "Необходимость замены переменных",
            "Есть отрицательные свободные члены и отрицательные оценки. "
            "Для перехода к двойственному симплекс-методу выполняем замену x_j = M_j - y_j."
        )

        # Поиск верхних границ M_j для исходных переменных.
        # Граница выводится из ограничения, в котором все коэффициенты
        # неотрицательны, а свободный член также неотрицателен.
        upper_bounds = [None] * original_count

        for i, sign in enumerate(problem["signs"]):
            row = problem["original_A"][i][:]
            rhs = problem["original_b"][i]

            if sign == ">=":
                row = [-value for value in row]
                rhs = -rhs

            if rhs < -EPSILON or any(value < -EPSILON for value in row):
                continue

            for j, coefficient in enumerate(row):
                if coefficient > EPSILON:
                    bound = max(0.0, rhs) / coefficient
                    if upper_bounds[j] is None or bound < upper_bounds[j]:
                        upper_bounds[j] = bound

        if any(value is None for value in upper_bounds):
            message = (
                "Не удалось найти конечную верхнюю границу для каждой "
                "переменной. Автоматическая замена x_j = M_j - y_j "
                "для этой задачи невозможна."
            )
            add_text_step(
                steps,
                "Замена переменных невозможна",
                message
            )
            return make_result(
                "variable_substitution_failed",
                message,
                steps,
                tableau=tableau,
                basis=basis,
                deltas=deltas,
                problem=problem
            )

        # Преобразование ограничений после подстановки x_j = M_j - y_j
        transformed_A = []
        transformed_b = []
        transformed_signs = []

        for i, sign in enumerate(problem["signs"]):
            row = problem["original_A"][i][:]
            rhs = problem["original_b"][i]

            if sign == ">=":
                row = [-value for value in row]
                rhs = -rhs

            shift = sum(row[j] * upper_bounds[j] for j in range(original_count))
            transformed_A.append([-value for value in row])
            transformed_b.append(rhs - shift)
            transformed_signs.append("=" if sign == "=" else "<=")

        # Добавление ограничений 0 <= y_j <= M_j
        for j in range(original_count):
            row = [0.0] * original_count
            row[j] = 1.0
            transformed_A.append(row)
            transformed_b.append(upper_bounds[j])
            transformed_signs.append("<=")

        # Преобразование целевой функции и сохранение постоянной части
        transformed_c = [-value for value in work_c[:original_count]]
        objective_constant = sum(
            work_c[j] * upper_bounds[j] for j in range(original_count)
        )

        add_text_step(
            steps,
            "Выполнение замены переменных",
            "Подставляем x_j = M_j - y_j. К преобразованной задаче "
            "добавлены ограничения y_j <= M_j.",
            {
                "upper_bounds": upper_bounds[:],
                "substitution": [
                    f"x{j + 1} = {upper_bounds[j]} - y{j + 1}"
                    for j in range(original_count)
                ],
                "transformed_c": transformed_c[:],
                "objective_constant": objective_constant
            }
        )

        # Канонизация преобразованных ограничений
        variable_names = [f"y{j + 1}" for j in range(original_count)]

        for i, sign in enumerate(transformed_signs):
            if sign in ("<=", ">="):
                for row in transformed_A:
                    row.append(0.0)
                transformed_A[i][-1] = 1.0
                transformed_c.append(0.0)
                variable_names.append(f"x{len(variable_names) + 1}")

        work_A = transformed_A
        work_b = transformed_b
        work_c = transformed_c

        add_text_step(
            steps,
            "Канонический вид преобразованной задачи",
            "К ограничениям добавлены дополнительные переменные. "
            "Формируем новую симплексную таблицу."
        )

        tableau = build_tableau(work_A, work_b)
        basis = find_initial_basis(work_A)

        if basis is None:
            message = (
                "После замены переменных не удалось сформировать "
                "единичный базис. Требуется метод искусственного базиса."
            )
            add_text_step(
                steps,
                "Формирование нового базиса",
                message
            )
            return make_result(
                "artificial_basis_required",
                message,
                steps,
                tableau=tableau,
                problem=problem
            )

        add_text_step(
            steps,
            "Формирование нового базиса",
            "После замены переменных начальный единичный базис сформирован.",
            {
                "basis": basis[:],
                "basis_names": [variable_names[j] for j in basis]
            }
        )
        add_table_step(
            steps,
            tableau,
            basis,
            variable_names,
            work_c,
            "Начальная таблица после замены переменных"
        )

        deltas = calculate_deltas(tableau, work_c, basis)
        if any(value < -EPSILON for value in deltas):
            message = (
                "После замены переменных остались отрицательные оценки. "
                "Двойственный симплекс-метод применить нельзя."
            )
            add_text_step(
                steps,
                "Проверка преобразованной таблицы",
                message
            )
            return make_result(
                "dual_simplex_not_applicable",
                message,
                steps,
                tableau=tableau,
                basis=basis,
                deltas=deltas,
                problem=problem
            )

        if not any(row[-1] < -EPSILON for row in tableau):
            message = (
                "После замены переменных все свободные члены стали "
                "неотрицательными. Полученная таблица не требует "
                "двойственного симплекс-метода."
            )
            add_text_step(
                steps,
                "Проверка преобразованной таблицы",
                message
            )
            return make_result(
                "dual_simplex_not_applicable",
                message,
                steps,
                tableau=tableau,
                basis=basis,
                deltas=deltas,
                problem=problem
            )

        substituted = True
    else:
        substituted = False

    # Проверка условий применения двойственного симплекс-метода
    deltas = calculate_deltas(tableau, work_c, basis)
    if any(value < -EPSILON for value in deltas):
        message = (
            "Есть отрицательные оценки Delta_j, но нет отрицательных "
            "свободных членов для перехода к двойственному симплекс-методу. "
            "Рекомендуется прямой симплекс-метод."
        )
        add_text_step(
            steps,
            "Проверка условий метода",
            message
        )
        return make_result(
            "primal_simplex_recommended",
            message,
            steps,
            tableau=tableau,
            basis=basis,
            deltas=deltas,
            problem=problem
        )

    add_text_step(
        steps,
        "Начало двойственного симплекс-метода",
        "Все оценки Delta_j неотрицательны. Выполняем итерации, "
        "пока не исчезнут отрицательные свободные члены."
    )

    # Выполнение итераций двойственного симплекс-метода
    for iteration in range(1, max_iterations + 1):
        deltas = calculate_deltas(tableau, work_c, basis)
        negative_b = [i for i, row in enumerate(tableau) if row[-1] < -EPSILON]

        # Если все свободные члены неотрицательны, найден оптимум
        if not negative_b:
            solution = [0.0] * len(work_c)
            for i, basic_column in enumerate(basis):
                solution[basic_column] = tableau[i][-1]

            if substituted:
                y_solution = solution[:original_count]
                original_solution = [
                    upper_bounds[j] - y_solution[j]
                    for j in range(original_count)
                ]
                transformed_value = (
                    objective_constant
                    + sum(work_c[j] * solution[j] for j in range(len(work_c)))
                )
                objective_value = transformed_value * objective_factor

                add_text_step(
                    steps,
                    "Возвращение к исходным переменным",
                    "Восстанавливаем исходные значения по формуле x_j = M_j - y_j.",
                    {
                        "transformed_solution": y_solution[:],
                        "upper_bounds": upper_bounds[:],
                        "solution": original_solution[:]
                    }
                )
            else:
                original_solution = solution[:original_count]
                objective_value = sum(
                    problem["original_c"][j] * original_solution[j]
                    for j in range(original_count)
                )

            add_text_step(
                steps,
                "Получение оптимального решения",
                "Все свободные члены и оценки неотрицательны. "
                "Оптимальное решение найдено.",
                {
                    "solution": original_solution[:],
                    "objective_value": objective_value
                }
            )

            return make_result(
                "optimal",
                "Оптимальное решение найдено.",
                steps,
                solution=original_solution,
                objective_value=objective_value,
                tableau=tableau,
                basis=basis,
                deltas=deltas,
                problem=problem
            )

        # Выбор разрешающей строки
        pivot_row = min(negative_b, key=lambda i: tableau[i][-1])
        add_text_step(
            steps,
            "Выбор разрешающей строки",
            f"Выбираем строку с наиболее отрицательным свободным членом "
            f"b = {tableau[pivot_row][-1]}."
        )

        # Выбор разрешающего столбца по минимальному отношению Delta_j / (-a_ij)
        ratios = []
        for j, delta in enumerate(deltas):
            if j in basis:
                continue

            coefficient = tableau[pivot_row][j]
            if coefficient < -EPSILON:
                ratio = delta / (-coefficient)
                if ratio >= -EPSILON:
                    ratios.append((max(0.0, ratio), j))

        if not ratios:
            message = (
                "В разрешающей строке нет отрицательных коэффициентов. "
                "Задача не имеет допустимого решения."
            )
            add_text_step(
                steps,
                "Проверка разрешающего столбца",
                message
            )
            return make_result(
                "infeasible",
                message,
                steps,
                tableau=tableau,
                basis=basis,
                deltas=deltas,
                problem=problem
            )

        _, pivot_column = min(ratios, key=lambda item: (item[0], item[1]))

        # Сохранение информации о разрешающем элементе
        old_variable = variable_names[basis[pivot_row]]
        new_variable = variable_names[pivot_column]
        pivot_info = {
            "row": pivot_row,
            "column": pivot_column,
            "value": tableau[pivot_row][pivot_column],
            "entering_variable": new_variable,
            "leaving_variable": old_variable
        }

        add_text_step(
            steps,
            "Выбор разрешающего элемента",
            f"Переменная {new_variable} входит в базис, "
            f"переменная {old_variable} выходит из базиса.",
            pivot_info
        )

        # Пересчёт таблицы и сохранение нового базиса
        pivot_operation(tableau, pivot_row, pivot_column)
        basis[pivot_row] = pivot_column
        add_table_step(
            steps,
            tableau,
            basis,
            variable_names,
            work_c,
            f"Симплексная таблица после преобразования №{iteration}",
            pivot=pivot_info
        )

        # Проверка сохранения двойственной допустимости
        deltas = calculate_deltas(tableau, work_c, basis)
        if any(value < -EPSILON for value in deltas):
            message = (
                "После преобразования появились отрицательные оценки. "
                "Условие двойственной допустимости нарушено."
            )
            add_text_step(
                steps,
                "Проверка двойственной допустимости",
                message
            )
            return make_result(
                "dual_feasibility_lost",
                message,
                steps,
                tableau=tableau,
                basis=basis,
                deltas=deltas,
                problem=problem
            )

    # Остановка при достижении максимального количества итераций
    message = "Превышено максимальное количество итераций."
    add_text_step(
        steps,
        "Остановка алгоритма",
        message
    )
    return make_result(
        "iteration_limit",
        message,
        steps,
        tableau=tableau,
        basis=basis,
        deltas=calculate_deltas(tableau, work_c, basis),
        problem=problem
    )