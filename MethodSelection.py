# MethodSelection.py

from AuxiliaryFun import (
    normalize_problem, build_tableau, find_initial_basis,
    determine_method, add_text_step, make_result,
    calculate_deltas, expand_free_variables, collapse_solution, EPSILON
)


def build_dual_tableau(c, A, b, signs, objective, var_types=None):
    """
    Аккуратно собирает таблицу для проверки: подходит ли она для двойственного симплекса.
    """
    n = len(c)
    if var_types is None:
        var_types = ["nonneg"] * n

    original_c = [float(v) for v in c]
    original_A = [[float(v) for v in row] for row in A]
    original_b = [float(v) for v in b]

    # Расширяем свободные переменные
    exp_c, exp_A, mapping, base_names = expand_free_variables(
        original_c, original_A, var_types
    )

    m = len(exp_A)
    work_A = [row[:] for row in exp_A]
    work_b = list(original_b)
    work_signs = list(signs)

    factor = 1.0 if objective == "max" else -1.0
    work_c = [factor * v for v in exp_c]
    names = base_names[:]

    steps = []
    add_text_step(steps, "Подготовка таблицы", "Ищем базис и формируем таблицу для анализа.")

    # 1. Ищем базис в равенствах (=)
    for i in range(m):
        if work_signs[i] == "=":
            if any(abs(val - 1.0) <= EPSILON for val in work_A[i]):
                continue
            if any(abs(val + 1.0) <= EPSILON for val in work_A[i]):
                work_A[i] = [-v for v in work_A[i]]
                work_b[i] = -work_b[i]
                add_text_step(steps, f"Преобразование равенства №{i+1}", "Умножаем строку на -1, чтобы получить базисную переменную (+1).")

    # 2. Добавляем slack переменные для неравенств
    for i in range(m):
        if work_signs[i] == "=":
            continue
            
        for row in work_A:
            row.append(0.0)
        work_c.append(0.0)
        names.append(f"s{i+1}")

        if work_signs[i] == ">=":
            work_A[i][-1] = -1.0
            work_A[i] = [-v for v in work_A[i]]
            work_b[i] = -work_b[i]
        elif work_signs[i] == "<=":
            work_A[i][-1] = 1.0

    # Ищем базис
    basis = find_initial_basis(work_A)
    if basis is None:
        return None

    tableau = build_tableau(work_A, work_b)
    
    problem = {
        "c": work_c, "A": work_A, "b": work_b, "signs": work_signs,
        "variable_names": names, "original_c": original_c, "original_A": original_A,
        "original_b": original_b, "original_variables_count": len(exp_c),
        "original_var_types": var_types[:], "mapping": mapping,
        "objective": objective, "objective_factor": factor, "steps": steps,
    }

    return tableau, basis, work_c, names, problem


def solve_problem(c, A, b, signs, objective="max", max_iterations=1000,
                  force_method=None, var_types=None):

    if var_types is None:
        var_types = ["nonneg"] * len(c)

    # 1. ПРИНУДИТЕЛЬНЫЙ ДВОЙСТВЕННЫЙ
    if force_method == "dual":
        res = build_dual_tableau(c, A, b, signs, objective, var_types=var_types)
        if res is None:
            return make_result("dual_not_applicable", "Не удалось построить базис.", [], problem=None)
        tableau, basis, work_c, names, problem = res
        from DualSimplex import dual_simplex_prepared
        return dual_simplex_prepared(problem, tableau, basis, max_iterations, force=True)

    # 2. ПРИНУДИТЕЛЬНЫЙ МИБ
    if force_method == "mib":
        problem_norm = normalize_problem(c, A, b, signs, objective, var_types=var_types)
        from MIB import artificial_basis_prepared
        return artificial_basis_prepared(problem_norm, max_iterations)

    # 3. БАЗОВАЯ ПОДГОТОВКА ЗАДАЧИ
    problem_norm = normalize_problem(c, A, b, signs, objective, var_types=var_types)
    tableau_norm = build_tableau(problem_norm["A"], problem_norm["b"])
    basis_norm = find_initial_basis(problem_norm["A"])
    
    # Если удалось сразу найти начальный единичный базис, 
    # и все b >= 0 (план допустим), то МЫ СРАЗУ ИДЕМ В ПРЯМОЙ СИМПЛЕКС!
    if basis_norm is not None:
        b_vals = [row[-1] for row in tableau_norm]
        if all(bv >= -EPSILON for bv in b_vals):
            add_text_step(problem_norm["steps"], "Выбор метода", "Начальный план допустим (все b >= 0). Запускаем прямой симплекс-метод.")
            from PrimalSimplex import primal_simplex_prepared
            return primal_simplex_prepared(problem_norm, tableau_norm, basis_norm, max_iterations)

    # 4. ПРОБУЕМ СОБРАТЬ ТАБЛИЦУ ДЛЯ ДВОЙСТВЕННОГО (если прямой не подошел)
    dual_res = build_dual_tableau(c, A, b, signs, objective, var_types=var_types)
    
    if dual_res is not None:
        tableau_d, basis_d, work_c_d, names_d, problem_d = dual_res
        deltas_d = calculate_deltas(tableau_d, work_c_d, basis_d)
        has_neg_b = any(row[-1] < -EPSILON for row in tableau_d)
        has_neg_delta = any(d < -EPSILON for d in deltas_d)

        # Если есть отрицательные b, но дельты >= 0 — предлагаем выбор
        if has_neg_b and not has_neg_delta:
            add_text_step(problem_d["steps"], "Выбор метода", "Все Δ_j ≥ 0, но есть отрицательные b. Доступен двойственный симплекс.")
            
            return {
                "status": "dual_available",
                "message": "Задача двойственно допустима. Выберите метод решения.",
                "steps": problem_d["steps"],
                "solution": None,
                "objective_value": None,
                "tableau": tableau_d,
                "basis": basis_d,
                "problem": problem_d,
                "dual_data": {
                    "status": "dual_available",
                    "message": "Двойственный симплекс применим.",
                    "problem": problem_d,
                    "tableau": tableau_d,
                    "basis": basis_d,
                    "c": work_c_d,
                    "names": names_d,
                },
                "mib_available": True
            }

    # 5. ЕСЛИ НИЧЕГО НЕ ПОДОШЛО — ИДЕМ В МИБ
    add_text_step(problem_norm["steps"], "Выбор метода", "Двойственный симплекс не применим или нет базиса. Запускаем МИБ.")
    from MIB import artificial_basis_prepared
    return artificial_basis_prepared(problem_norm, max_iterations)