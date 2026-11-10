# Двойственный симплекс-метод
# Применяется, когда базис двойственно допустим (Delta >= 0), но в столбце свободных членов есть отрицательные значения.

from AuxiliaryFun import (calculate_deltas, pivot_operation, add_text_step, add_table_step, recover_solution, make_result, EPSILON)

def dual_simplex_prepared(problem, tableau, basis, max_iterations=1000):
    steps = problem["steps"]
    c = problem["c"]
    names = problem["variable_names"]

    add_text_step(steps, "Начало двойственного симплекс-метода", "Проверяем двойственную допустимость: все Delta_j должны быть неотрицательны.")
    
    for iteration in range(1, max_iterations + 1):
        deltas = calculate_deltas(tableau, c, basis)

        if any(d < -EPSILON for d in deltas):
            return make_result("dual_simplex_not_applicable",
                               "Двойственная допустимость нарушена: есть отрицательные оценки.",
                               steps, tableau=tableau, basis=basis,
                               deltas=deltas, problem=problem)
        
        negative_rows = [i for i, row in enumerate(tableau) if row[-1] < -EPSILON]
        if not negative_rows:
            values = recover_solution(tableau, basis, len(c))
            x = values[:problem["original_variables_count"]]
            obj = sum(problem["original_c"][j] * x[j] for j in range(len(x)))

            add_text_step(steps, "Допустимый план получен",
                          "Все свободные члены неотрицательны, а оценки неотрицательны.")
            
            return make_result("optimal", "Оптимальное решение найдено двойственным симплекс-методом.",
                               steps, x, obj, tableau, basis, deltas, problem, all_variables=values)
        
        pivot_row = min(negative_rows, key=lambda i: tableau[i][-1])
        candidates = []
        
        for j in range(len(c)):
            if j in basis or tableau[pivot_row][j] >= -EPSILON:
                continue
            ratio = deltas[j] / (-tableau[pivot_row][j])
            candidates.append((ratio, j))
        if not candidates:
            return make_result("infeasible",
                               "В выбранной строке нет допустимого разрешающего столбца. Задача несовместна.",
                               steps, tableau=tableau, basis=basis,
                               deltas=deltas, problem=problem)
        _, pivot_col = min(candidates, key=lambda item: (item[0], item[1]))
        info = {"row": pivot_row, "column": pivot_col,
                "value": tableau[pivot_row][pivot_col],
                "entering_variable": names[pivot_col],
                "leaving_variable": names[basis[pivot_row]]}
        add_text_step(steps, "Выбор разрешающего элемента",
                      f"Входит {names[pivot_col]}, выходит {names[basis[pivot_row]]}.", info)
        pivot_operation(tableau, pivot_row, pivot_col)
        basis[pivot_row] = pivot_col
        add_table_step(steps, tableau, basis, names, c,
                       f"Двойственный симплекс-метод: итерация {iteration}", info)
    return make_result("iteration_limit", "Превышено максимальное количество итераций.",
                       steps, tableau=tableau, basis=basis,
                       deltas=calculate_deltas(tableau, c, basis), problem=problem)
