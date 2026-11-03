#Прямой симплекс метод
#Результат содержит список steps со всеми этапами решения

from AuxiliaryFun import (add_text_step, add_table_step, normalize_problem, find_initial_basis, 
    calculate_deltas, determine_method, pivot_operation, build_tableau, EPSILON)

def primal_simplex(c, A, b, signs, objective="max", max_iterations=1000):
    #Приведение задачи к каноническому виду
    problem = normalize_problem(c, A, b, signs, objective)
    c = problem["c"]
    A = problem["A"]
    b = problem["b"]
    variable_names = problem["variable_names"]
    original_variables_count = problem["original_variables_count"]
    objective_factor = problem["objective_factor"]
    steps = problem["steps"]

    #Формирование начальной симплексной таблицы
    tableau = build_tableau(A, b)
    basis = find_initial_basis(A)

    #Проверка наличия начального базиса
    if basis is None:
        add_text_step(
            steps,
            "Формирование начального базиса",
            "Не удалось сформировать единичный базис. Для дальнейшего решения необходим метод искусственного базиса."
        )
        return {
            "status": "artificial_basis_required",
            "message": "Используется метод искусственного базиса.",
            "solution": None,
            "objective_value": None,
            "steps": steps,
            "problem": problem
        }

    #Сохранение информации о сформированном базисе
    add_text_step(
        steps,
        "Формирование начального базиса",
        "Начальный базис успешно сформирован.",
        {
            "basis": basis[:],
            "basis_names": [variable_names[index] for index in basis]
        }
    )

    #Проверка возможности применения прямого симплекс-метода
    add_table_step(steps, tableau, basis, variable_names, c, "Начальная симплексная таблица")
    method_info = determine_method(tableau, c, basis)
    add_text_step(
        steps,
        "Проверка возможности применения метода",
        method_info["message"],
        method_info
    )

    #Если начальная таблица не подходит для прямого симплекс-метода, завершаем работу
    #Если таблица уже оптимальна, продолжаем выполнение для получения решения
    if method_info["method"] not in ("primal_simplex", "optimal"):
        return {
            "status": method_info["method"],
            "message": method_info["message"],
            "solution": None,
            "objective_value": None,
            "tableau": [row[:] for row in tableau],
            "basis": basis[:],
            "steps": steps,
            "problem": problem
        }

    #Начало выполнения прямого симплекс-метода
    add_text_step(
        steps,
        "Начало прямого симплекс-метода",
        "Начальное базисное решение допустимо. Начинаем проверку критерия оптимальности."
    )

    #Выполнение итераций симплекс-метода
    for iteration_number in range(1, max_iterations + 1):
        #Вычисление оценок по формуле Delta_j = Z_j - C_j
        deltas = calculate_deltas(tableau, c, basis)

        #Проверка критерия оптимальности
        #Для задачи на максимум оптимум достигнут, если все Delta_j >= 0
        negative_columns = [
            j for j, delta in enumerate(deltas)
            if delta < -EPSILON and j not in basis
        ]

        if not negative_columns:
            #Восстановление значений всех переменных из итогового базисного решения
            solution = [0.0] * len(c)

            for i, basic_index in enumerate(basis):
                solution[basic_index] = tableau[i][-1]

            #Получение значений только исходных переменных
            original_solution = solution[:original_variables_count]

            #Вычисление значения целевой функции
            transformed_value = sum(
                c[j] * solution[j]
                for j in range(len(c))
            )

            #Восстановление значения исходной целевой функции
            objective_value = transformed_value * objective_factor

            add_text_step(
                steps,
                "Проверка критерия оптимальности",
                "Все оценки Delta_j >= 0. Следовательно, найдено оптимальное решение."
            )

            add_text_step(
                steps,
                "Получение оптимального решения",
                "Выписываем значения исходных переменных из итогового базисного решения.",
                {
                    "solution": original_solution[:],
                    "all_variables": solution[:],
                    "objective_value": objective_value
                }
            )

            return {
                "status": "optimal",
                "message": "Оптимальное решение найдено.",
                "solution": original_solution,
                "all_variables": solution,
                "objective_value": objective_value,
                "steps": steps,
                "basis": basis[:],
                "tableau": [row[:] for row in tableau],
                "deltas": deltas[:],
                "problem": problem
            }

        #Выбор разрешающего столбца
        #Выбираем столбец с наиболее отрицательной оценкой Delta_j
        pivot_column = min(
            negative_columns,
            key=lambda j: deltas[j]
        )

        #Выбор разрешающей строки
        #Рассматриваем только положительные коэффициенты разрешающего столбца
        ratios = []

        for i in range(len(tableau)):
            coefficient = tableau[i][pivot_column]

            if coefficient > EPSILON:
                ratio = tableau[i][-1] / coefficient

                #Учитываем только неотрицательные отношения
                if ratio >= -EPSILON:
                    ratios.append((max(0.0, ratio), i))

        #Проверка неограниченности целевой функции
        if not ratios:
            add_text_step(
                steps,
                "Проверка ограниченности",
                "В разрешающем столбце нет положительных элементов. Целевая функция не ограничена сверху."
            )

            return {
                "status": "unbounded",
                "message": "Целевая функция не ограничена.",
                "solution": None,
                "objective_value": None,
                "steps": steps,
                "tableau": [row[:] for row in tableau],
                "basis": basis[:],
                "deltas": deltas[:],
                "problem": problem
            }

        #Выбор строки с минимальным неотрицательным отношением
        _, pivot_row = min(
            ratios,
            key=lambda item: (item[0], basis[item[1]])
        )

        #Сохранение информации о разрешающем элементе
        old_variable = variable_names[basis[pivot_row]]
        new_variable = variable_names[pivot_column]
        pivot_value = tableau[pivot_row][pivot_column]

        pivot_info = {
            "row": pivot_row,
            "column": pivot_column,
            "value": pivot_value,
            "entering_variable": new_variable,
            "leaving_variable": old_variable
        }

        add_text_step(
            steps,
            "Выбор разрешающего элемента",
            f"Переменная {new_variable} входит в базис, переменная {old_variable} выходит из базиса.",
            pivot_info
        )

        #Преобразование симплексной таблицы методом Жордана — Гаусса
        pivot_operation(tableau, pivot_row, pivot_column)

        #Обновление состава базиса
        basis[pivot_row] = pivot_column

        #Сохранение новой симплексной таблицы в списке этапов решения
        add_table_step(
            steps,
            tableau,
            basis,
            variable_names,
            c,
            f"Симплексная таблица после преобразования №{iteration_number}",
            pivot=pivot_info
        )

    #Превышено допустимое количество итераций
    add_text_step(
        steps,
        "Остановка алгоритма",
        "Достигнуто максимальное количество итераций."
    )

    return {
        "status": "iteration_limit",
        "message": "Превышено максимальное количество итераций.",
        "solution": None,
        "objective_value": None,
        "steps": steps,
        "tableau": [row[:] for row in tableau],
        "basis": basis[:],
        "deltas": calculate_deltas(tableau, c, basis),
        "problem": problem
    }
